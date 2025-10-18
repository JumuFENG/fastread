from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, Rewrite, User, Book, Chapter
from routers.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class RewriteCreate(BaseModel):
    book_id: int
    chapter_id: int
    original_content: str
    rewritten_content: str
    position: int
    type: str  # 'rewrite' 或 'insert'

class RewriteResponse(BaseModel):
    id: int
    book_id: int
    chapter_id: int
    original_content: str
    rewritten_content: str
    position: int
    type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class RewriteUpdate(BaseModel):
    rewritten_content: Optional[str] = None
    position: Optional[int] = None

@router.post("/", response_model=RewriteResponse)
async def create_rewrite(
    rewrite: RewriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建重写/插入内容"""
    # 验证书籍和章节是否存在
    book = db.query(Book).filter(Book.id == rewrite.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    chapter = db.query(Chapter).filter(
        Chapter.id == rewrite.chapter_id,
        Chapter.book_id == rewrite.book_id
    ).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    db_rewrite = Rewrite(
        user_id=current_user.id,
        book_id=rewrite.book_id,
        chapter_id=rewrite.chapter_id,
        original_content=rewrite.original_content,
        rewritten_content=rewrite.rewritten_content,
        position=rewrite.position,
        type=rewrite.type
    )
    
    db.add(db_rewrite)
    db.commit()
    db.refresh(db_rewrite)
    
    return db_rewrite

@router.get("/", response_model=List[RewriteResponse])
async def get_rewrites(
    book_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的重写列表"""
    query = db.query(Rewrite).filter(Rewrite.user_id == current_user.id)
    
    if book_id:
        query = query.filter(Rewrite.book_id == book_id)
    if chapter_id:
        query = query.filter(Rewrite.chapter_id == chapter_id)
    
    rewrites = query.order_by(Rewrite.position).all()
    return rewrites

@router.get("/{rewrite_id}", response_model=RewriteResponse)
async def get_rewrite(
    rewrite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个重写"""
    rewrite = db.query(Rewrite).filter(
        Rewrite.id == rewrite_id,
        Rewrite.user_id == current_user.id
    ).first()
    
    if not rewrite:
        raise HTTPException(status_code=404, detail="重写内容不存在")
    
    return rewrite

@router.put("/{rewrite_id}", response_model=RewriteResponse)
async def update_rewrite(
    rewrite_id: int,
    rewrite_update: RewriteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新重写内容"""
    rewrite = db.query(Rewrite).filter(
        Rewrite.id == rewrite_id,
        Rewrite.user_id == current_user.id
    ).first()
    
    if not rewrite:
        raise HTTPException(status_code=404, detail="重写内容不存在")
    
    if rewrite_update.rewritten_content is not None:
        rewrite.rewritten_content = rewrite_update.rewritten_content
    if rewrite_update.position is not None:
        rewrite.position = rewrite_update.position
    
    db.commit()
    db.refresh(rewrite)
    
    return rewrite

@router.delete("/{rewrite_id}")
async def delete_rewrite(
    rewrite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除重写内容"""
    rewrite = db.query(Rewrite).filter(
        Rewrite.id == rewrite_id,
        Rewrite.user_id == current_user.id
    ).first()
    
    if not rewrite:
        raise HTTPException(status_code=404, detail="重写内容不存在")
    
    db.delete(rewrite)
    db.commit()
    
    return {"message": "重写内容删除成功"}

@router.get("/chapter/{chapter_id}/merged")
async def get_merged_chapter_content(
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取合并了重写内容的章节"""
    # 获取原始章节内容
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 获取该章节的所有重写
    rewrites = db.query(Rewrite).filter(
        Rewrite.chapter_id == chapter_id,
        Rewrite.user_id == current_user.id
    ).order_by(Rewrite.position.desc()).all()  # 倒序处理，避免位置偏移
    
    # 合并内容
    merged_content = chapter.content or ""
    
    for rewrite in rewrites:
        if rewrite.type == "rewrite":
            # 替换内容
            if rewrite.original_content in merged_content:
                merged_content = merged_content.replace(
                    rewrite.original_content, 
                    rewrite.rewritten_content, 
                    1  # 只替换第一个匹配
                )
        elif rewrite.type == "insert":
            # 插入内容
            if rewrite.position <= len(merged_content):
                merged_content = (
                    merged_content[:rewrite.position] + 
                    rewrite.rewritten_content + 
                    merged_content[rewrite.position:]
                )
    
    return {
        "chapter_id": chapter_id,
        "original_content": chapter.content,
        "merged_content": merged_content,
        "rewrites_count": len(rewrites)
    }