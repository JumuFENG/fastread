from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, ReadingProgress, Book
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ReadingProgressResponse(BaseModel):
    book_id: int
    current_chapter: int
    reading_position: int
    last_read_at: datetime
    
    class Config:
        from_attributes = True

class UpdateProgress(BaseModel):
    current_chapter: int
    reading_position: int = 0

@router.get("/progress/{book_id}", response_model=ReadingProgressResponse)
async def get_reading_progress(
    book_id: int,
    db: Session = Depends(get_db)
):
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.book_id == book_id
    ).first()
    
    if not progress:
        # 创建新的阅读进度
        progress = ReadingProgress(
            book_id=book_id,
            current_chapter=1,
            reading_position=0
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return progress

@router.put("/progress/{book_id}")
async def update_reading_progress(
    book_id: int,
    progress_data: UpdateProgress,
    db: Session = Depends(get_db)
):
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.book_id == book_id
    ).first()
    
    if not progress:
        progress = ReadingProgress(
            book_id=book_id
        )
        db.add(progress)
    
    progress.current_chapter = progress_data.current_chapter
    progress.reading_position = progress_data.reading_position
    progress.last_read_at = datetime.utcnow()
    
    db.commit()
    return {"message": "阅读进度更新成功"}

@router.get("/history")
async def get_reading_history(
    db: Session = Depends(get_db)
):
    history = db.query(ReadingProgress, Book).join(Book).order_by(ReadingProgress.last_read_at.desc()).all()
    
    result = []
    for progress, book in history:
        result.append({
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_url": book.cover_url,
                "total_chapters": book.total_chapters
            },
            "progress": {
                "current_chapter": progress.current_chapter,
                "reading_position": progress.reading_position,
                "last_read_at": progress.last_read_at
            }
        })
    
    return result