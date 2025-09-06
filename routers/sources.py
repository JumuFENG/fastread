from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from database import get_db, BookSource, Book, Chapter
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import asyncio
from parsers.parser_loader import get_parser_for_source, get_parser_for_url

router = APIRouter()

class BookSourceResponse(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    
    class Config:
        from_attributes = True

class BookSourceCreate(BaseModel):
    name: str
    url: str
    search_url: str
    book_url_pattern: str
    chapter_url_pattern: str
    content_selector: str

class SearchResult(BaseModel):
    title: str
    author: str
    description: str
    source_url: str
    cover_url: str = None

@router.get("/parsers")
async def list_available_parsers():
    """列出所有可用的解析器"""
    from parsers.parser_loader import parser_loader
    parsers = parser_loader.list_available_parsers()
    return {
        "available_parsers": parsers,
        "total_count": len(parsers),
        "base_parser": "BaseBookSourceParser (默认)",
        "note": "扩展解析器来自sources文件夹"
    }

@router.post("/parsers/reload")
async def reload_parsers():
    """重新加载所有解析器"""
    from parsers.parser_loader import parser_loader
    parser_loader.reload_parsers()
    parsers = parser_loader.list_available_parsers()
    return {
        "message": "扩展解析器重新加载成功",
        "available_parsers": parsers,
        "total_count": len(parsers)
    }

@router.get("/", response_model=List[BookSourceResponse])
async def get_book_sources(db: Session = Depends(get_db)):
    sources = db.query(BookSource).filter(BookSource.is_active == True).all()
    return sources

@router.post("/", response_model=BookSourceResponse)
async def create_book_source(source: BookSourceCreate, db: Session = Depends(get_db)):
    db_source = BookSource(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.get("/{source_id}/search")
async def search_books(source_id: int, keyword: str, db: Session = Depends(get_db)):
    source = db.query(BookSource).filter(BookSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="书源不存在")
    
    try:
        # 构建书源配置
        source_config = {
            'name': source.name,
            'url': source.url,
            'search_url': source.search_url,
            'book_url_pattern': source.book_url_pattern,
            'chapter_url_pattern': source.chapter_url_pattern,
            'content_selector': source.content_selector
        }
        
        # 获取对应的解析器
        parser = get_parser_for_source(source.name, source_config)
        
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

@router.get("/{source_id}", response_model=BookSourceResponse)
async def get_book_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(BookSource).filter(BookSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="书源不存在")
    return source

@router.put("/{source_id}", response_model=BookSourceResponse)
async def update_book_source(source_id: int, source: BookSourceCreate, db: Session = Depends(get_db)):
    db_source = db.query(BookSource).filter(BookSource.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="书源不存在")
    
    for key, value in source.dict().items():
        setattr(db_source, key, value)
    
    db.commit()
    db.refresh(db_source)
    return db_source

@router.delete("/{source_id}")
async def delete_book_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(BookSource).filter(BookSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="书源不存在")
    
    db.delete(source)
    db.commit()
    return {"message": "书源删除成功"}

@router.post("/{source_id}/toggle")
async def toggle_book_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(BookSource).filter(BookSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="书源不存在")
    
    source.is_active = not source.is_active
    db.commit()
    return {"message": "书源状态更新成功", "is_active": source.is_active}

@router.post("/{source_id}/test")
async def test_book_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(BookSource).filter(BookSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="书源不存在")
    
    try:
        # 测试搜索功能
        async with httpx.AsyncClient() as client:
            test_url = source.search_url.format(keyword="测试")
            response = await client.get(test_url, timeout=10)
            response.raise_for_status()
            
            return {
                "success": True,
                "message": "书源测试成功",
                "status_code": response.status_code,
                "response_size": len(response.text)
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"书源测试失败: {str(e)}"
        }

class DetectSourceRequest(BaseModel):
    book_url: str

@router.post("/detect")
async def detect_book_source(request: DetectSourceRequest, db: Session = Depends(get_db)):
    """根据URL自动检测匹配的书源"""
    try:
        # 验证请求数据
        if not request.book_url:
            raise HTTPException(status_code=422, detail="book_url是必需的")
        
        from urllib.parse import urlparse
        parsed_url = urlparse(request.book_url)
        hostname = parsed_url.hostname
        
        if not hostname:
            raise HTTPException(status_code=422, detail="无效的URL格式")
        
        # 查找匹配的书源
        sources = db.query(BookSource).filter(BookSource.is_active == True).all()
        
        # 精确匹配
        for source in sources:
            if source.url and hostname in source.url:
                return {
                    "source_id": source.id,
                    "source_name": source.name,
                    "match_type": "exact"
                }
        
        # 模糊匹配
        domain = hostname.replace('www.', '').split('.')[0]
        for source in sources:
            if (source.name.lower().find(domain) != -1 or 
                (source.url and source.url.lower().find(domain) != -1)):
                return {
                    "source_id": source.id,
                    "source_name": source.name,
                    "match_type": "fuzzy"
                }
        
        return {"message": "未找到匹配的书源"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"检测书源API错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

class ImportBookRequest(BaseModel):
    source_id: int
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
        
        source = db.query(BookSource).filter(BookSource.id == request.source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="书源不存在")
        
        # 检查书籍是否已存在
        existing_book = db.query(Book).filter(Book.source_url == request.book_url).first()
        if existing_book:
            return {"message": "书籍已存在", "book_id": existing_book.id}
        
        # 后台任务导入书籍
        background_tasks.add_task(import_book_task, source, request.book_url, db)
        
        return {"message": "开始导入书籍，请稍后查看"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"导入书籍API错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

async def import_book_task(source: BookSource, book_url: str, db_session: Session):
    # 创建新的数据库会话，避免会话冲突
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        print(f"开始导入书籍: {book_url}")
        
        # 构建书源配置
        source_config = {
            'name': source.name,
            'url': source.url,
            'search_url': source.search_url,
            'book_url_pattern': source.book_url_pattern,
            'chapter_url_pattern': source.chapter_url_pattern,
            'content_selector': source.content_selector
        }
        
        # 获取对应的解析器
        parser = get_parser_for_url(book_url, source_config)
        
        # 获取书籍信息
        print(f"正在获取书籍信息...")
        book_info = await parser.get_book_info(book_url)
        if not book_info:
            raise Exception("无法获取书籍信息")
        
        print(f"解析到书籍信息: 标题={book_info.title}, 作者={book_info.author}")
        
        # 创建书籍记录
        book = Book(
            title=book_info.title,
            author=book_info.author,
            description=book_info.description,
            cover_url=book_info.cover_url,
            source_id=source.id,
            source_url=book_url
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        
        print(f"书籍记录创建成功，ID: {book.id}")
        
        # 获取章节列表
        print(f"正在获取章节列表...")
        chapter_infos = await parser.get_chapter_list(book_url)
        print(f"找到 {len(chapter_infos)} 个章节")
        
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
                    print(f"已添加 {chapters_added} 章节...")
                    
            except Exception as e:
                print(f"添加章节失败: {chapter_info.title}, 错误: {e}")
                continue
        
        # 最终提交
        db.commit()
        
        # 更新书籍章节数
        book.total_chapters = chapters_added
        db.commit()
        
        print(f"书籍导入成功: {book_info.title}, 共 {chapters_added} 章")
        
    except Exception as e:
        print(f"导入书籍失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

# 旧的解析函数已移至解析器类中