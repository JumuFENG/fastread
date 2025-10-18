from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, Excerpt, User
from routers.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class ExcerptCreate(BaseModel):
    book_id: int
    chapter_id: int
    content: str
    note: Optional[str] = None

class ExcerptResponse(BaseModel):
    id: int
    book_id: int
    chapter_id: int
    content: str
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExcerptUpdate(BaseModel):
    content: Optional[str] = None
    note: Optional[str] = None

@router.post("/", response_model=ExcerptResponse)
async def create_excerpt(
    excerpt: ExcerptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建摘录"""
    db_excerpt = Excerpt(
        user_id=current_user.id,
        book_id=excerpt.book_id,
        chapter_id=excerpt.chapter_id,
        content=excerpt.content,
        note=excerpt.note
    )
    
    db.add(db_excerpt)
    db.commit()
    db.refresh(db_excerpt)
    
    return db_excerpt

@router.get("/", response_model=List[ExcerptResponse])
async def get_excerpts(
    book_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的摘录列表"""
    query = db.query(Excerpt).filter(Excerpt.user_id == current_user.id)
    
    if book_id:
        query = query.filter(Excerpt.book_id == book_id)
    
    excerpts = query.order_by(Excerpt.created_at.desc()).all()
    return excerpts

@router.get("/{excerpt_id}", response_model=ExcerptResponse)
async def get_excerpt(
    excerpt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个摘录"""
    excerpt = db.query(Excerpt).filter(
        Excerpt.id == excerpt_id,
        Excerpt.user_id == current_user.id
    ).first()
    
    if not excerpt:
        raise HTTPException(status_code=404, detail="摘录不存在")
    
    return excerpt

@router.put("/{excerpt_id}", response_model=ExcerptResponse)
async def update_excerpt(
    excerpt_id: int,
    excerpt_update: ExcerptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新摘录"""
    excerpt = db.query(Excerpt).filter(
        Excerpt.id == excerpt_id,
        Excerpt.user_id == current_user.id
    ).first()
    
    if not excerpt:
        raise HTTPException(status_code=404, detail="摘录不存在")
    
    if excerpt_update.content is not None:
        excerpt.content = excerpt_update.content
    if excerpt_update.note is not None:
        excerpt.note = excerpt_update.note
    
    db.commit()
    db.refresh(excerpt)
    
    return excerpt

@router.delete("/{excerpt_id}")
async def delete_excerpt(
    excerpt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除摘录"""
    excerpt = db.query(Excerpt).filter(
        Excerpt.id == excerpt_id,
        Excerpt.user_id == current_user.id
    ).first()
    
    if not excerpt:
        raise HTTPException(status_code=404, detail="摘录不存在")
    
    db.delete(excerpt)
    db.commit()
    
    return {"message": "摘录删除成功"}