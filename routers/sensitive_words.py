from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database import get_db, SensitiveWord
from routers.auth import get_current_user, User

router = APIRouter()

class SensitiveWordCreate(BaseModel):
    book_id: int
    original: str
    replacement: str
    enabled: bool = True

class SensitiveWordUpdate(BaseModel):
    original: str = None
    replacement: str = None
    enabled: bool = None

class SensitiveWordResponse(BaseModel):
    id: int
    book_id: int
    original: str
    replacement: str
    enabled: bool
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[SensitiveWordResponse])
async def get_sensitive_words(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定书籍的敏感词列表"""
    words = db.query(SensitiveWord).filter(
        SensitiveWord.user_id == current_user.id,
        SensitiveWord.book_id == book_id
    ).all()
    return words

@router.post("/", response_model=SensitiveWordResponse)
async def create_sensitive_word(
    word: SensitiveWordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建敏感词"""
    # 检查是否已存在相同的敏感词
    existing = db.query(SensitiveWord).filter(
        SensitiveWord.user_id == current_user.id,
        SensitiveWord.book_id == word.book_id,
        SensitiveWord.original == word.original
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="该敏感词已存在")
    
    db_word = SensitiveWord(
        user_id=current_user.id,
        book_id=word.book_id,
        original=word.original,
        replacement=word.replacement,
        enabled=word.enabled
    )
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word

@router.put("/{word_id}", response_model=SensitiveWordResponse)
async def update_sensitive_word(
    word_id: int,
    word_update: SensitiveWordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新敏感词"""
    db_word = db.query(SensitiveWord).filter(
        SensitiveWord.id == word_id,
        SensitiveWord.user_id == current_user.id
    ).first()
    
    if not db_word:
        raise HTTPException(status_code=404, detail="敏感词不存在")
    
    if word_update.original is not None:
        db_word.original = word_update.original
    if word_update.replacement is not None:
        db_word.replacement = word_update.replacement
    if word_update.enabled is not None:
        db_word.enabled = word_update.enabled
    
    db.commit()
    db.refresh(db_word)
    return db_word

@router.delete("/{word_id}")
async def delete_sensitive_word(
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除敏感词"""
    db_word = db.query(SensitiveWord).filter(
        SensitiveWord.id == word_id,
        SensitiveWord.user_id == current_user.id
    ).first()
    
    if not db_word:
        raise HTTPException(status_code=404, detail="敏感词不存在")
    
    db.delete(db_word)
    db.commit()
    return {"message": "敏感词删除成功"}
