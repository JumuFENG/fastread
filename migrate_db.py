#!/usr/bin/env python3
"""
数据库迁移脚本
添加新的字段到现有数据库
"""

import sqlite3
from database import engine, Base
from sqlalchemy import text

def migrate_database():
    """迁移数据库，添加新字段"""
    
    # 创建所有表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    # 连接到SQLite数据库
    conn = sqlite3.connect('reader.db')
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
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def check_database_schema():
    """检查数据库结构"""
    conn = sqlite3.connect('reader.db')
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
    conn = sqlite3.connect('reader.db')
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {name}")
    conn.commit()
    conn.close()

def recreate_table(name):
    """重新创建表"""
    conn = sqlite3.connect('reader.db')
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


if __name__ == "__main__":
    print("检查当前数据库结构...")
    check_database_schema()
    