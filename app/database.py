from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pathlib import Path
import os

# 数据库文件路径解析（相对项目根目录的 data 文件夹，可通过 FASTREAD_DB_PATH 覆盖）
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.environ.get("FASTREAD_DB_PATH", str(DATA_DIR / "reader.db")))

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    description = Column(Text)
    cover_url = Column(String)
    source_id = Column(String)
    source_url = Column(String)
    total_chapters = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    chapters = relationship("Chapter", back_populates="book")

class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    title = Column(String)
    content = Column(Text, nullable=True)  # 内容变为可选，实时获取
    chapter_number = Column(Integer)
    source_url = Column(String)
    is_cached = Column(Boolean, default=False)  # 是否已缓存内容
    cached_at = Column(DateTime, nullable=True)  # 缓存时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    book = relationship("Book", back_populates="chapters")

class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    current_chapter = Column(Integer, default=1)
    reading_position = Column(Integer, default=0)
    last_read_at = Column(DateTime, default=datetime.utcnow)

class Excerpt(Base):
    __tablename__ = "excerpts"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    content = Column(Text)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    book = relationship("Book")
    chapter = relationship("Chapter")

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    content = Column(Text)
    keywords = Column(Text)  # JSON格式存储关键词列表
    tags = Column(Text)  # JSON格式存储标签列表
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Rewrite(Base):
    __tablename__ = "rewrites"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    original_content = Column(Text)
    rewritten_content = Column(Text)
    position = Column(Integer)  # 在章节中的位置
    type = Column(String)  # 'rewrite' 或 'insert'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    book = relationship("Book")
    chapter = relationship("Chapter")

class SensitiveWord(Base):
    __tablename__ = "sensitive_words"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    original = Column(String, index=True)
    replacement = Column(String)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    book = relationship("Book")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()