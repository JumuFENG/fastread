from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, ReadingProgress, User, Book
from routers.auth import get_current_user
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.book_id == book_id
    ).first()
    
    if not progress:
        # 创建新的阅读进度
        progress = ReadingProgress(
            user_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.book_id == book_id
    ).first()
    
    if not progress:
        progress = ReadingProgress(
            user_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history = db.query(ReadingProgress, Book).join(Book).filter(
        ReadingProgress.user_id == current_user.id
    ).order_by(ReadingProgress.last_read_at.desc()).all()
    
    result = []
    for progress, book in history:
        result.append({
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_url": book.cover_url
            },
            "progress": {
                "current_chapter": progress.current_chapter,
                "reading_position": progress.reading_position,
                "last_read_at": progress.last_read_at
            }
        })
    
    return result