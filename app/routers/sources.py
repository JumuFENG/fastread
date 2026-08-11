from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Union
from app.database import get_db, Book, Chapter
from pydantic import BaseModel
import json
import httpx
from app.parsers.parser_loader import BaseBookSourceParser, get_parser_for_source, get_parser_for_url
from app.parsers.parser_loader import delete_parser, list_available_parsers
from app.lofig import logger

router = APIRouter()

class BookSourceResponse(BaseModel):
    id: int|str
    name: str
    url: str
    searchable: bool = True
    can_delete: bool = False

def parser_to_booksource(parser: BaseBookSourceParser) -> BookSourceResponse:
    return {
        "id": parser.get_parser_name()[0],
        "name": parser.get_parser_name()[-1],
        "url": parser.base_url,
        "searchable": bool(parser.search_url),
        "can_delete": parser.__class__.__name__ == "BaseBookSourceParser"
    }

class BookSourceCreate(BaseModel):
    name: str
    sourcejson: dict

class SearchResult(BaseModel):
    title: str
    author: str
    description: str
    source_url: str
    cover_url: str = None

@router.post("/parsers/reload")
async def reload_parsers():
    """重新加载所有解析器"""
    from app.parsers.parser_loader import parser_loader
    parser_loader.reload_parsers()
    parsers = parser_loader.list_available_parsers()
    return {
        "message": "扩展解析器重新加载成功",
        "available_parsers": [parser_to_booksource(parser) for parser in parsers],
        "total_count": len(parsers)
    }

@router.get("/", response_model=List[BookSourceResponse])
async def get_book_sources():
    parsers = list_available_parsers()
    return [parser_to_booksource(parser) for parser in parsers]

@router.post("/", response_model=BookSourceResponse)
async def create_book_source(source: BookSourceCreate):
    parser = get_parser_for_source(source.name, source.sourcejson)
    return parser_to_booksource(parser)

@router.get("/{source_id}/search")
async def search_books(source_id: int|str, keyword: str, db: Session = Depends(get_db)):

    try:
        # 获取对应的解析器
        parser = get_parser_for_source(source_id)

        # 使用解析器搜索
        search_results = await parser.search_books(keyword, limit=10)

        # 转换为API响应格式
        results = []
        for result in search_results:
            results.append(SearchResult(
                title=result.title,
                author=result.author,
                description=result.description,
                source_url=result.source_url,
                cover_url=result.cover_url
            ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/{source_id}", response_model=BookSourceCreate)
async def get_book_source(source_id: int|str):
    parser = get_parser_for_source(source_id)
    if not parser:
        raise HTTPException(status_code=404, detail="书源不存在")
    return {
        "name": parser.get_parser_name()[-1],
        "sourcejson": parser.source_config if hasattr(parser, 'source_config') else parser.cfg_template
    }

@router.put("/{source_id}", response_model=BookSourceResponse)
async def update_book_source(source: BookSourceCreate):
    return create_book_source(source)

@router.delete("/{source_id}")
async def delete_book_source(source_id: int|str):
    try:
        delete_parser(source_id)
        return {"message": "书源删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除书源失败: {str(e)}")

@router.post("/{source_id}/test")
async def test_book_source(source_id: str):
    parser = get_parser_for_source(source_id)
    try:
        if parser.search_url:
            books = await parser.search_books('三寸人间')
            if books and len(books) > 0:
                return {
                    "success": True,
                    "message": "测试成功"
                }
        else:
            response = await httpx.AsyncClient().get(parser.base_url)
            response.raise_for_status()
            if response.text:
                return {
                    "success": True,
                    "message": "书源测试成功"
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试书源失败: {str(e)}")
        return {
            "success": False,
            "message": f"书源测试失败: {str(e)}"
        }
    return {
        "success": False,
        "message": "书源测试失败"
    }

class DetectSourceRequest(BaseModel):
    book_url: str

@router.post("/detect", response_model=BookSourceResponse)
async def detect_book_source(request: DetectSourceRequest):
    """根据URL自动检测匹配的书源"""
    try:
        # 验证请求数据
        if not request.book_url:
            raise HTTPException(status_code=422, detail="book_url是必需的")

        parser = get_parser_for_url(request.book_url, {})
        return parser_to_booksource(parser)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检测书源API错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

class ImportBookRequest(BaseModel):
    source_id: Union[int, str]
    book_url: str

@router.post("/import")
async def import_book(
    request: ImportBookRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        # 验证请求数据
        if not request.source_id or not request.book_url:
            raise HTTPException(status_code=422, detail="source_id和book_url都是必需的")

        # 验证URL格式
        from urllib.parse import urlparse
        parsed_url = urlparse(request.book_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=422, detail="无效的URL格式")

        # 检查书籍是否已存在
        existing_book = db.query(Book).filter(Book.source_url == request.book_url).first()
        if existing_book:
            return {"message": "书籍已存在", "book_id": existing_book.id}

        # 后台任务导入书籍
        background_tasks.add_task(import_book_task, request)

        return {"message": "开始导入书籍，请稍后查看"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入书籍API错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

async def import_book_task(ibook: ImportBookRequest):
    # 创建新的数据库会话，避免会话冲突
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        book_url = ibook.book_url
        logger.info(f"开始导入书籍: {book_url}")

        # 获取对应的解析器
        parser = get_parser_for_source(ibook.source_id) or get_parser_for_url(book_url)

        # 获取书籍信息
        logger.info(f"正在获取书籍信息...")
        book_info = await parser.get_book_info(book_url)
        if not book_info:
            raise Exception("无法获取书籍信息")

        logger.info(f"解析到书籍信息: 标题={book_info.title}, 作者={book_info.author}")

        # 创建书籍记录
        book = Book(
            title=book_info.title,
            author=book_info.author,
            description=book_info.description,
            cover_url=book_info.cover_url,
            source_url=book_url,
            source_id=ibook.source_id
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        logger.info(f"书籍记录创建成功，ID: {book.id}")

        # 获取章节列表
        logger.info(f"正在获取章节列表...")
        chapter_infos = await parser.get_chapter_list(book_url)
        logger.info(f"找到 {len(chapter_infos)} 个章节")

        chapters_added = 0
        for chapter_info in chapter_infos:
            try:
                # 只保存章节信息，不获取内容
                chapter = Chapter(
                    book_id=book.id,
                    title=chapter_info.title,
                    content=None,  # 不预先获取内容
                    chapter_number=chapter_info.chapter_number or (chapters_added + 1),
                    source_url=chapter_info.url,
                    is_cached=False
                )
                db.add(chapter)
                chapters_added += 1

                # 每50章提交一次
                if chapters_added % 50 == 0:
                    db.commit()
                    logger.info(f"已添加 {chapters_added} 章节...")

            except Exception as e:
                logger.warning(f"添加章节失败: {chapter_info.title}, 错误: {e}")
                continue

        # 最终提交
        db.commit()

        # 更新书籍章节数
        book.total_chapters = chapters_added
        db.commit()

        logger.info(f"书籍导入成功: {book_info.title}, 共 {chapters_added} 章")

    except Exception as e:
        logger.error(f"导入书籍失败: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()

