from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from database import get_db, User
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "120"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_at: str  # ISO format datetime string
    remember_me: bool = False

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None, remember_me: bool = False):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 如果选择记住我，token有效期更长
        if remember_me:
            expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # 默认7天
    
    to_encode.update({"exp": expire, "remember_me": remember_me})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 验证用户名格式
    if len(user.username) < 3 or len(user.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度必须在3-20个字符之间")
    
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', user.username):
        raise HTTPException(status_code=400, detail="用户名只能包含字母、数字和下划线")
    
    # 验证密码长度
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6个字符")
    
    # 验证邮箱格式
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_regex, user.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    try:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        access_token, expire_time = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires, remember_me=True
        )
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_at": expire_time.isoformat(),
            "remember_me": True
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

@router.post("/login", response_model=Token)
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """JSON格式的登录接口，支持记住我功能"""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 根据remember_me设置不同的过期时间
    if login_data.remember_me:
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    else:
        access_token_expires = timedelta(days=7)
    
    access_token, expire_time = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires,
        remember_me=login_data.remember_me
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_at": expire_time.isoformat(),
        "remember_me": login_data.remember_me
    }

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2兼容的登录接口"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=7)
    access_token, expire_time = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_at": expire_time.isoformat(),
        "remember_me": False
    }

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """刷新token，延长有效期"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        remember_me: bool = payload.get("remember_me", False)
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token",
            )
        
        # 验证用户是否存在
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
            )
        
        # 创建新token
        if remember_me:
            access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        else:
            access_token_expires = timedelta(days=7)
        
        new_token, expire_time = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires,
            remember_me=remember_me
        )
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_at": expire_time.isoformat(),
            "remember_me": remember_me
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token",
        )