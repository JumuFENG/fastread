from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database import get_db, User, ReadingProgress, Book
from routers.auth import get_current_user

router = APIRouter()

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserDetailResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    books_count: int
    reading_progress_count: int
    
    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None

# 检查是否为管理员
def check_admin(current_user: User = Depends(get_current_user)):
    # 简单的管理员检查：用户名为admin或administrator
    if current_user.username not in ['admin', 'administrator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表（需要管理员权限）"""
    query = db.query(User)
    
    # 搜索功能
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.username.like(search_pattern)) | 
            (User.email.like(search_pattern))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    current_user: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """获取用户详情（需要管理员权限）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 统计用户的书籍数量
    books_count = db.query(func.count(ReadingProgress.book_id.distinct())).filter(
        ReadingProgress.user_id == user_id
    ).scalar() or 0
    
    # 统计阅读进度数量
    reading_progress_count = db.query(func.count(ReadingProgress.id)).filter(
        ReadingProgress.user_id == user_id
    ).scalar() or 0
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "books_count": books_count,
        "reading_progress_count": reading_progress_count
    }

@router.get("/{user_id}/reading-progress")
async def get_user_reading_progress(
    user_id: int,
    current_user: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """获取用户的阅读进度"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取用户的阅读进度
    progress_list = db.query(ReadingProgress, Book).join(
        Book, ReadingProgress.book_id == Book.id
    ).filter(
        ReadingProgress.user_id == user_id
    ).order_by(
        ReadingProgress.last_read_at.desc()
    ).limit(10).all()
    
    return [
        {
            "book_id": progress.book_id,
            "book_title": book.title,
            "current_chapter": progress.current_chapter,
            "last_read_at": progress.last_read_at
        }
        for progress, book in progress_list
    ]

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    current_user: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """更新用户信息（需要管理员权限）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许禁用自己
    if user.id == current_user.id and user_update.is_active is False:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """删除用户（需要管理员权限）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    
    db.delete(user)
    db.commit()
    return {"message": "用户删除成功"}

@router.get("/stats/summary")
async def get_users_stats(
    current_user: User = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """获取用户统计信息"""
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # 最近7天注册的用户
    from datetime import timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = db.query(func.count(User.id)).filter(
        User.created_at >= seven_days_ago
    ).scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "recent_users": recent_users
    }
