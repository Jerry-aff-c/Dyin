# -*- encoding: utf-8 -*-
"""
检查数据库状态
"""

import sqlite3
import os

db_path = "e:\\抖音监控\\监控系统\\douyin-main\\temp_data\\users\\default\\monitor_data.db"

print("=" * 80)
print("检查数据库状态")
print("=" * 80)

# 检查数据库文件是否存在
if os.path.exists(db_path):
    print(f"\n✓ 数据库文件存在: {db_path}")
    print(f"  文件大小: {os.path.getsize(db_path)} 字节")
else:
    print(f"\n✗ 数据库文件不存在: {db_path}")
    exit(1)

# 连接数据库
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("✓ 数据库连接成功")
except Exception as e:
    print(f"✗ 数据库连接失败: {e}")
    exit(1)

# 检查表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\n现有表: {[t[0] for t in tables]}")

# 检查每个表的结构
for table in tables:
    table_name = table[0]
    print(f"\n{table_name} 表结构:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

# 检查数据
print("\n数据统计:")
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  - {table_name}: {count} 条记录")

conn.close()

print("\n" + "=" * 80)
print("检查完成")
print("=" * 80)