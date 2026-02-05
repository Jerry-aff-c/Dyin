# -*- encoding: utf-8 -*-
"""
用户数据存储

为每个用户提供独立的 SQLite 数据库，存储监控数据和视频信息。
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

from ..models import UserConfig


class UserDatabase:
    """用户专属SQLite数据库"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.conn = None
        try:
            user_dir = UserConfig.get_user_data_dir(user_id)
            db_path = os.path.join(user_dir, 'monitor_data.db')
            
            # 确保目录存在
            os.makedirs(user_dir, exist_ok=True)
            
            # 使用绝对路径，避免路径问题
            db_path = os.path.abspath(db_path)
            
            # 尝试连接数据库
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.init_tables()
        except Exception as e:
            # 无法创建数据库，设置conn为None
            print(f"创建数据库失败: {e}")
            pass
    
    def init_tables(self):
        """初始化用户数据表"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # 关注账号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS following_accounts (
                account_id TEXT PRIMARY KEY,
                sec_uid TEXT NOT NULL,
                nickname TEXT,
                follower_count INTEGER,
                last_updated TIMESTAMP,
                is_monitoring BOOLEAN DEFAULT 1
            )
        ''')
        
        # 视频数据表
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
                hourly_likes INTEGER DEFAULT 0,  # 近一小时点赞增量
                FOREIGN KEY (account_id) REFERENCES following_accounts (account_id)
            )
        ''')
        
        # 点赞历史表（用于计算小时增量）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS like_history (
                video_id TEXT,
                like_count INTEGER,
                recorded_at TIMESTAMP,
                PRIMARY KEY (video_id, recorded_at)
            )
        ''')
        
        self.conn.commit()
    
    def save_account(self, account_id: str, sec_uid: str, nickname: str, follower_count: int):
        """保存关注账号信息"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO following_accounts 
            (account_id, sec_uid, nickname, follower_count, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (account_id, sec_uid, nickname, follower_count, datetime.now()))
        
        self.conn.commit()
    
    def save_video_data(self, account_id: str, videos: List[Dict[str, Any]]):
        """保存视频数据并计算增量"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # 确保表存在（在多线程环境下可能需要重新检查）
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS like_history (
                video_id TEXT,
                like_count INTEGER,
                recorded_at TIMESTAMP,
                PRIMARY KEY (video_id, recorded_at)
            )
        ''')
        
        self.conn.commit()
        
        for video in videos:
            # 检查是否已存在
            cursor.execute(
                "SELECT like_count FROM videos WHERE video_id = ?",
                (video['id'],)
            )
            existing = cursor.fetchone()
            
            # 保存点赞历史
            cursor.execute(
                '''INSERT INTO like_history (video_id, like_count, recorded_at) 
                   VALUES (?, ?, ?)''',
                (video['id'], video['digg_count'], datetime.now())
            )
            
            # 计算近一小时点赞增量
            hour_ago = datetime.now().timestamp() - 3600
            cursor.execute('''
                SELECT like_count FROM like_history 
                WHERE video_id = ? AND recorded_at >= datetime(?, 'unixepoch')
                ORDER BY recorded_at ASC LIMIT 1
            ''', (video['id'], hour_ago))
            
            hour_ago_likes = cursor.fetchone()
            hourly_inc = 0
            if hour_ago_likes:
                hourly_inc = video['digg_count'] - hour_ago_likes[0]
            
            # 插入或更新视频数据
            if existing:
                cursor.execute('''
                    UPDATE videos SET 
                        like_count = ?,
                        collect_count = ?,
                        comment_count = ?,
                        share_count = ?,
                        hourly_likes = ?,
                        collected_at = CURRENT_TIMESTAMP
                    WHERE video_id = ?
                ''', (
                    video['digg_count'],
                    video['collect_count'],
                    video['comment_count'],
                    video['share_count'],
                    hourly_inc,
                    video['id']
                ))
            else:
                # 获取视频播放地址
                video_url = video.get('download_addr', '')
                
                cursor.execute('''
                    INSERT INTO videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video['id'],
                    account_id,
                    video['desc'],
                    video['time'],
                    video['digg_count'],
                    video['collect_count'],
                    video['comment_count'],
                    video['share_count'],
                    video['cover'],
                    video_url,
                    datetime.now(),
                    hourly_inc
                ))
        
        self.conn.commit()
    
    def get_monitoring_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取监控数据"""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT v.video_id, v.account_id, v.description, v.create_time, 
                       v.like_count, v.collect_count, v.comment_count, v.share_count, 
                       v.cover_url, v.video_url, v.hourly_likes, 
                       a.nickname as account_name, a.follower_count
                FROM videos v
                JOIN following_accounts a ON v.account_id = a.account_id
                ORDER BY v.hourly_likes DESC, v.like_count DESC
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'key': row[0],
                    'video_id': row[0],
                    'account_id': row[1],
                    'video_desc': row[2],
                    'create_time': row[3],
                    'total_likes': row[4],
                    'collect_count': row[5],
                    'comment_count': row[6],
                    'share_count': row[7],
                    'cover_url': row[8],
                    'video_url': row[9],
                    'hourly_likes': row[10],
                    'account_name': row[11],
                    'follower_count': row[12]
                })
            
            return results
        except Exception as e:
            # 表不存在或其他错误，返回空列表
            print(f"获取监控数据失败: {e}")
            return []
    
    def get_following_count(self) -> int:
        """获取关注账号数量"""
        if not self.conn:
            return 0
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM following_accounts WHERE is_monitoring = 1')
        return cursor.fetchone()[0]
    
    def get_last_update_time(self) -> str:
        """获取最后更新时间"""
        if not self.conn:
            return datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT MAX(collected_at) FROM videos
        ''')
        result = cursor.fetchone()[0]
        return result or datetime.now().isoformat()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()