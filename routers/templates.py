from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, Template, User
from routers.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import re

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    content: str
    keywords: List[str]
    tags: List[str]
    description: Optional[str] = None

class TemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    keywords: List[str]
    tags: List[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None

class TemplateApply(BaseModel):
    template_id: int
    keyword_values: dict  # 关键词对应的值

@router.post("/", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建模板"""
    # 验证模板内容中是否包含所有关键词
    for keyword in template.keywords:
        if f"{{{keyword}}}" not in template.content:
            raise HTTPException(
                status_code=400, 
                detail=f"模板内容中缺少关键词: {keyword}"
            )
    
    db_template = Template(
        user_id=current_user.id,
        name=template.name,
        content=template.content,
        keywords=json.dumps(template.keywords, ensure_ascii=False),
        tags=json.dumps(template.tags, ensure_ascii=False),
        description=template.description
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # 转换JSON字段
    db_template.keywords = json.loads(db_template.keywords)
    db_template.tags = json.loads(db_template.tags)
    
    return db_template

@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的模板列表"""
    templates = db.query(Template).filter(Template.user_id == current_user.id).all()
    
    # 转换JSON字段并过滤标签
    result = []
    for template in templates:
        template.keywords = json.loads(template.keywords)
        template.tags = json.loads(template.tags)
        
        if tag and tag not in template.tags:
            continue
            
        result.append(template)
    
    return result

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 转换JSON字段
    template.keywords = json.loads(template.keywords)
    template.tags = json.loads(template.tags)
    
    return template

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template_update.name is not None:
        template.name = template_update.name
    if template_update.content is not None:
        template.content = template_update.content
    if template_update.keywords is not None:
        template.keywords = json.dumps(template_update.keywords, ensure_ascii=False)
    if template_update.tags is not None:
        template.tags = json.dumps(template_update.tags, ensure_ascii=False)
    if template_update.description is not None:
        template.description = template_update.description
    
    template.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(template)
    
    # 转换JSON字段
    template.keywords = json.loads(template.keywords)
    template.tags = json.loads(template.tags)
    
    return template

@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    db.delete(template)
    db.commit()
    
    return {"message": "模板删除成功"}

