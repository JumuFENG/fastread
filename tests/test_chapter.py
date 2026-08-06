#!/usr/bin/env python3
"""
测试章节内容获取
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.lofig import Config
Config.db_config()['dbpath'] = 'data/test.db'
import asyncio
from app.database import engine, Base, SessionLocal, Book, Chapter
from app.routers.books import fetch_chapter_content_realtime

Base.metadata.create_all(bind=engine)

async def test_chapter_fetch():
    """测试章节内容获取"""
    db = SessionLocal()
    
    try:
        # 获取第一本书的第一章
        book = db.query(Book).first()
        if not book:
            print("数据库中没有书籍")
            return
        
        print(f"测试书籍: {book.title}")
        
        chapter = db.query(Chapter).filter(Chapter.book_id == book.id).first()
        if not chapter:
            print("书籍没有章节")
            return
        
        print(f"测试章节: {chapter.title}")
        print(f"章节URL: {chapter.source_url}")
                
        # 尝试获取内容
        try:
            content = await fetch_chapter_content_realtime(chapter, db)
            print(f"\n成功获取内容，长度: {len(content)}")
            print(f"内容预览: {content[:200]}...")
        except Exception as e:
            print(f"\n获取内容失败: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        db.close()

async def test_update_chapter_list(book_id):
    """测试更新章节列表"""
    db = SessionLocal()
    
    try:
        # db.query(Chapter).filter(Chapter.book_id == book_id).delete()
        # db.commit()
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            print(f"书籍ID {book_id} 不存在")
            return
        
        
        chapters = db.query(Chapter).filter(Chapter.book_id == book_id).all()
        # 从数据库中删除source_url重复的章节
        unique_urls = set()
        duplicates = []
        for chapter in chapters:
            if chapter.source_url in unique_urls:
                duplicates.append(chapter)
            else:
                unique_urls.add(chapter.source_url)
        for duplicate in duplicates:
            db.delete(duplicate)

        if duplicates or book.total_chapters != len(unique_urls):
            book.total_chapters = len(unique_urls)

        db.commit()

        if duplicates:
            print(f"删除了 {len(duplicates)} 个重复章节")

        # print(f"更新书籍 {book.title} 的章节列表...")
        # 这里假设有一个函数 update_chapter_list(book, db) 可以更新章节列表
        # from routers.books import update_book_chapters
        # updated_count = await update_book_chapters(book_id, db)
        
        # print(f"成功更新了 {updated_count} 个章节")
        
    except Exception as e:
        print(f"更新章节列表失败: {e}")
    finally:
        db.close()
    
if __name__ == "__main__":    
    print("\n开始测试章节内容获取...")
    asyncio.run(test_update_chapter_list(51))