#!/usr/bin/env python3
"""
数据库迁移脚本
添加新的字段到现有数据库
"""

import os
import sys
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import *
from app.database import DB_PATH
from sqlalchemy import text

def migrate_database():
    """迁移数据库，添加新字段"""
    
    # 创建所有表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    # 连接到SQLite数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查chapters表是否存在新字段
        cursor.execute("PRAGMA table_info(chapters)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"当前chapters表字段: {columns}")
        
        # 添加新字段（如果不存在）
        if 'is_cached' not in columns:
            print("添加is_cached字段...")
            cursor.execute("ALTER TABLE chapters ADD COLUMN is_cached BOOLEAN DEFAULT 0")
            
        if 'cached_at' not in columns:
            print("添加cached_at字段...")
            cursor.execute("ALTER TABLE chapters ADD COLUMN cached_at DATETIME")
            
        # 更新现有记录
        cursor.execute("""
            UPDATE chapters 
            SET is_cached = CASE 
                WHEN content IS NOT NULL AND content != '' THEN 1 
                ELSE 0 
            END
            WHERE is_cached IS NULL
        """)
        
        conn.commit()
        print("数据库迁移完成！")
        
        # 单用户模式迁移：删除 user_id 列和 users 表
        # SQLite不允许直接删除外键列，需要重建表
        for table in ['reading_progress', 'excerpts', 'templates', 'rewrites', 'sensitive_words']:
            # 处理上次迁移中断遗留的 _old 表
            cursor.execute(f"PRAGMA table_info({table}_old)")
            if cursor.fetchall():
                print(f"发现遗留的{table}_old表，继续迁移...")
                Base.metadata.create_all(bind=engine)
                cursor.execute(f"PRAGMA table_info({table})")
                new_columns = [column[1] for column in cursor.fetchall()]
                old_columns = [column[1] for column in cursor.execute(f"PRAGMA table_info({table}_old)").fetchall()]
                common = [c for c in old_columns if c in new_columns]
                cursor.execute(
                    f"INSERT OR IGNORE INTO {table} ({', '.join(common)}) "
                    f"SELECT {', '.join(common)} FROM {table}_old"
                )
                cursor.execute(f"DROP TABLE {table}_old")
                conn.commit()
                continue
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [column[1] for column in cursor.fetchall()]
            if 'user_id' not in columns:
                continue
            print(f"重建{table}表，删除user_id字段...")
            cursor.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
            # 删除旧表上的索引，避免与新表索引重名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL", (f"{table}_old",))
            for (index_name,) in cursor.fetchall():
                cursor.execute(f"DROP INDEX {index_name}")
            conn.commit()
            Base.metadata.create_all(bind=engine)
            new_columns = [column[1] for column in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            common = [c for c in columns if c in new_columns]
            cursor.execute(
                f"INSERT INTO {table} ({', '.join(common)}) "
                f"SELECT {', '.join(common)} FROM {table}_old"
            )
            cursor.execute(f"DROP TABLE {table}_old")
            conn.commit()
        cursor.execute("DROP TABLE IF EXISTS users")
        conn.commit()
        print("单用户模式迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def check_database_schema():
    """检查数据库结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"数据库表: {[table[0] for table in tables]}")
        
        for table, in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n{table}表结构:")
            for column in columns:
                print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'} {'DEFAULT ' + str(column[4]) if column[4] else ''}")
            
    except Exception as e:
        print(f"检查失败: {e}")
    finally:
        conn.close()

def delete_table(name):
    """删除表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {name}")
    conn.commit()
    conn.close()

def recreate_table(name):
    """重新创建表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if not cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'").fetchone():
        return
    old_values = cursor.execute(f"SELECT * FROM {name}").fetchall()
    columns = [column[1] for column in cursor.execute(f"PRAGMA table_info({name})").fetchall()]
    cursor.execute(f"DROP TABLE IF EXISTS {name}")
    Base.metadata.create_all(bind=engine)
    new_columns = [column[1] for column in cursor.execute(f"PRAGMA table_info({name})").fetchall()]
    new_value = []
    for old_value in old_values:
        new_value.append([old_value[i] for i in range(len(old_value)) if columns[i] in new_columns])
    cursor.executemany(f"INSERT INTO {name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})", new_value)

    conn.commit()
    conn.close()


def check_book_table():
    """检查表是否存在"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    books = db.query(Book).all()
    sources = {1:'biquuge',4:'mddyueshu',5:"crxs",6:"xszj"}
    for b in books:
        print(b.title, b.source_id, b.source_url)
    db.commit()
    db.close()

if __name__ == "__main__":
    print("检查当前数据库结构...")
    check_database_schema()
    