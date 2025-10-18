from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./reader.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BookSource(Base):
    __tablename__ = "book_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String)
    search_url = Column(String)
    book_url_pattern = Column(String)
    chapter_url_pattern = Column(String)
    content_selector = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    description = Column(Text)
    cover_url = Column(String)
    source_id = Column(Integer, ForeignKey("book_sources.id"))
    source_url = Column(String)
    total_chapters = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    source = relationship("BookSource")
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
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    current_chapter = Column(Integer, default=1)
    reading_position = Column(Integer, default=0)
    last_read_at = Column(DateTime, default=datetime.utcnow)

class Excerpt(Base):
    __tablename__ = "excerpts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    content = Column(Text)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    book = relationship("Book")
    chapter = relationship("Chapter")

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    content = Column(Text)
    keywords = Column(Text)  # JSON格式存储关键词列表
    tags = Column(Text)  # JSON格式存储标签列表
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class Rewrite(Base):
    __tablename__ = "rewrites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    original_content = Column(Text)
    rewritten_content = Column(Text)
    position = Column(Integer)  # 在章节中的位置
    type = Column(String)  # 'rewrite' 或 'insert'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    book = relationship("Book")
    chapter = relationship("Chapter")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()