# -*- encoding: utf-8 -*-
"""
修复数据库表结构
"""

import sqlite3
import os

db_path = "e:\\抖音监控\\监控系统\\douyin-main\\temp_data\\users\\default\\monitor_data.db"

print("=" * 80)
print("修复数据库表结构")
print("=" * 80)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查现有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\n现有表: {[t[0] for t in tables]}")

# 创建videos表
print("\n创建videos表...")
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            account_id TEXT,
            description TEXT,
            create_time INTEGER,
            like_count INTEGER,
            collect_count INTEGER,
            comment_count INTEGER,
            share_count INTEGER,
            cover_url TEXT,
            video_url TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hourly_likes INTEGER DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES following_accounts (account_id)
        )
    ''')
    print("✓ videos表创建成功")
except Exception as e:
    print(f"✗ 创建videos表失败: {e}")

# 创建like_history表
print("\n创建like_history表...")
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS like_history (
            video_id TEXT,
            like_count INTEGER,
            recorded_at TIMESTAMP,
            PRIMARY KEY (video_id, recorded_at)
        )
    ''')
    print("✓ like_history表创建成功")
except Exception as e:
    print(f"✗ 创建like_history表失败: {e}")

# 检查创建后的表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\n更新后的表: {[t[0] for t in tables]}")

conn.commit()
conn.close()

print("\n" + "=" * 80)
print("数据库修复完成")
print("=" * 80)