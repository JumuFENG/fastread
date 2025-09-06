from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, Book, Chapter, BookSource
from pydantic import BaseModel
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import re
from parsers.parser_loader import get_parser_for_source

router = APIRouter()

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    description: str
    cover_url: Optional[str]
    total_chapters: int
    is_completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChapterResponse(BaseModel):
    id: int
    title: str
    chapter_number: int
    source_url: Optional[str] = None
    is_cached: bool = False
    
    class Config:
        from_attributes = True

class BookCreate(BaseModel):
    title: str
    author: str
    description: str
    cover_url: Optional[str] = None
    source_id: int
    source_url: str

@router.get("/", response_model=List[BookResponse])
async def get_books(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Book)
    if search:
        query = query.filter(Book.title.contains(search))
    books = query.offset(skip).limit(limit).all()
    return books

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return book

@router.get("/{book_id}/chapters", response_model=List[ChapterResponse])
async def get_book_chapters(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    chapters = db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()
    return chapters

@router.get("/{book_id}/chapters/{chapter_number}")
async def get_chapter_content(book_id: int, chapter_number: int, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number == chapter_number
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 如果章节内容未缓存，实时获取
    if not chapter.is_cached or not chapter.content:
        try:
            content = await fetch_chapter_content_realtime(chapter, db)
            return {
                "id": chapter.id,
                "title": chapter.title,
                "content": content,
                "chapter_number": chapter.chapter_number,
                "is_cached": chapter.is_cached
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取章节内容失败: {str(e)}")
    
    return {
        "id": chapter.id,
        "title": chapter.title,
        "content": chapter.content,
        "chapter_number": chapter.chapter_number,
        "is_cached": chapter.is_cached
    }

@router.post("/", response_model=BookResponse)
async def create_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.delete("/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    db.delete(book)
    db.commit()
    return {"message": "书籍删除成功"}
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

async def fetch_chapter_content_realtime(chapter: Chapter, db: Session) -> str:
    """实时获取章节内容"""
    try:
        print(f"开始获取章节内容: {chapter.title} (ID: {chapter.id})")
        print(f"章节URL: {chapter.source_url}")
        
        # 获取书籍和书源信息
        book = db.query(Book).filter(Book.id == chapter.book_id).first()
        if not book:
            raise Exception("书籍信息不存在")
        
        print(f"书籍信息: {book.title} (源ID: {book.source_id})")
        
        source = db.query(BookSource).filter(BookSource.id == book.source_id).first()
        if not source:
            raise Exception("书源信息不存在")
        
        print(f"书源信息: {source.name}")
        
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
        
        # 使用解析器获取章节内容
        content = await parser.get_chapter_content(chapter.source_url)
        
        if not content:
            raise Exception("解析器无法提取章节内容")
        
        print(f"解析器成功提取内容，长度: {len(content)}")
        
        # 可选：缓存内容到数据库（如果需要）
        cache_content = len(content) < 50000  # 只缓存较小的章节
        if cache_content:
            chapter.content = content
            chapter.is_cached = True
            chapter.cached_at = datetime.utcnow()
            db.commit()
        
        return content
        
    except Exception as e:
        raise Exception(f"获取章节内容失败: {str(e)}")

def clean_chapter_content(raw_content: str) -> str:
    """清理章节内容"""
    if not raw_content:
        return ""
    
    # 移除多余的空白字符
    content = raw_content.strip()
    
    # 移除常见的广告和无关内容
    ad_patterns = [
        r'.*?广告.*?',
        r'.*?推荐.*?',
        r'.*?点击.*?',
        r'.*?下载.*?',
        r'.*?APP.*?',
        r'.*?网站.*?',
        r'.*?更新.*?',
        r'.*?最新章节.*?',
    ]
    
    for pattern in ad_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # 规范化段落
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 5:  # 过滤太短的行
            cleaned_lines.append(line)
    
    # 重新组合内容
    content = '\n\n'.join(cleaned_lines)
    
    return content

# 添加章节预加载功能
@router.post("/{book_id}/chapters/{chapter_number}/preload")
async def preload_chapter_content(book_id: int, chapter_number: int, db: Session = Depends(get_db)):
    """预加载章节内容"""
    chapter = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number == chapter_number
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    if chapter.is_cached and chapter.content:
        return {"message": "章节已缓存", "cached": True}
    
    try:
        content = await fetch_chapter_content_realtime(chapter, db)
        return {
            "message": "章节预加载成功",
            "cached": True,
            "content_length": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预加载失败: {str(e)}")

# 批量预加载章节
@router.post("/{book_id}/chapters/batch-preload")
async def batch_preload_chapters(
    book_id: int, 
    start_chapter: int = 1, 
    count: int = 5,
    db: Session = Depends(get_db)
):
    """批量预加载章节内容"""
    chapters = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number >= start_chapter,
        Chapter.chapter_number < start_chapter + count
    ).all()
    
    if not chapters:
        raise HTTPException(status_code=404, detail="没有找到章节")
    
    results = []
    for chapter in chapters:
        try:
            if not chapter.is_cached or not chapter.content:
                content = await fetch_chapter_content_realtime(chapter, db)
                results.append({
                    "chapter_number": chapter.chapter_number,
                    "title": chapter.title,
                    "status": "success",
                    "content_length": len(content)
                })
            else:
                results.append({
                    "chapter_number": chapter.chapter_number,
                    "title": chapter.title,
                    "status": "already_cached"
                })
        except Exception as e:
            results.append({
                "chapter_number": chapter.chapter_number,
                "title": chapter.title,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "message": f"批量预加载完成",
        "total": len(chapters),
        "results": results
    }
# 调试章节内容获取
@router.get("/debug/{book_id}/chapters/{chapter_number}")
async def debug_chapter_content(book_id: int, chapter_number: int, db: Session = Depends(get_db)):
    """调试章节内容获取"""
    chapter = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number == chapter_number
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    try:
        # 获取书籍和书源信息
        book = db.query(Book).filter(Book.id == chapter.book_id).first()
        source = db.query(BookSource).filter(BookSource.id == book.source_id).first()
        
        # 获取页面内容进行分析
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = await client.get(chapter.source_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 分析页面结构
            analysis = {
                "chapter_info": {
                    "id": chapter.id,
                    "title": chapter.title,
                    "url": chapter.source_url,
                    "chapter_number": chapter.chapter_number
                },
                "book_info": {
                    "title": book.title,
                    "author": book.author
                },
                "source_info": {
                    "name": source.name,
                    "content_selector": source.content_selector
                },
                "page_analysis": {
                    "status_code": response.status_code,
                    "page_title": soup.find('title').text if soup.find('title') else None,
                    "page_size": len(response.text),
                    "has_content_div": bool(soup.find('div', class_='content')),
                    "has_text_div": bool(soup.find('div', class_='text')),
                    "has_chaptercontent_id": bool(soup.find(id='chaptercontent')),
                    "paragraph_count": len(soup.find_all('p')),
                    "div_count": len(soup.find_all('div'))
                },
                "selector_test": {}
            }
            
            # 测试各种选择器
            test_selectors = [
                '.content', '#content', '.chapter-content', '.text',
                '.novel-content', '.read-content', '.chapter_content',
                '.txt', '.chapter-txt', '#chaptercontent'
            ]
            
            if source.content_selector:
                test_selectors = [s.strip() for s in source.content_selector.split(',')] + test_selectors
            
            for selector in test_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text().strip()
                        analysis["selector_test"][selector] = {
                            "found": True,
                            "text_length": len(text),
                            "preview": text[:200] + "..." if len(text) > 200 else text
                        }
                    else:
                        analysis["selector_test"][selector] = {"found": False}
                except Exception as e:
                    analysis["selector_test"][selector] = {"error": str(e)}
            
            return analysis
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调试失败: {str(e)}")