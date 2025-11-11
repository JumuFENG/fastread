from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, Book, Chapter
from pydantic import BaseModel
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import re
from parsers.parser_loader import get_parser_for_source, get_parser_for_url

router = APIRouter()

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    source_url: str
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
    source_id: str
    source_url: str

def get_parser_for_book(book: Book):
    if book.source_id and isinstance(book.source_id, str):
        return get_parser_for_source(book.source_id)
    return get_parser_for_url(book.source_url, {})

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

@router.post("/{book_id}/update")
async def update_book_chapters(book_id: int, db: Session = Depends(get_db)):
    """
    更新书籍章节列表
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 更新章节列表
    try:
        parser = get_parser_for_book(book)
        chapters = await parser.update_chapter_list(book.source_url, book.total_chapters)
        existing_chapter_numbers = {c.chapter_number for c in db.query(Chapter).filter(Chapter.book_id == book_id).all()}
        new_chapters = []
        for ch in chapters:
            if ch.chapter_number not in existing_chapter_numbers:
                new_chapter = Chapter(
                    book_id=book_id,
                    title=ch.title,
                    content=None,
                    chapter_number=ch.chapter_number,
                    source_url=ch.url,
                    is_cached=False
                )
                db.add(new_chapter)
                new_chapters.append(new_chapter)

        book.total_chapters = len(existing_chapter_numbers) + len(new_chapters)
        book.updated_at = datetime.utcnow()

        db.commit()

        return {
            "message": f"书籍信息和章节列表已更新，新增章节数: {len(new_chapters)}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节列表更新失败: {str(e)}")

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

        parser = get_parser_for_book(book)
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
