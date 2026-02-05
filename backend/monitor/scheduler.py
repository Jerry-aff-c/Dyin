# -*- encoding: utf-8 -*-
"""
监控调度器

负责管理监控任务，重用原项目爬虫功能，支持定时采集和并行处理。
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from ..lib.douyin.crawler import Douyin
from ..storage.user_db import UserDatabase
from ..models import UserConfig


class MonitoringScheduler:
    """监控调度器 - 重用原项目爬虫"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_config = UserConfig(user_id)
        self.user_db = None  # 延迟初始化数据库连接
        self.executor = ThreadPoolExecutor(max_workers=5)  # 并行采集
        self.is_running = False
        self.last_update_time = datetime.now()
    
    def _get_db(self):
        """获取数据库连接（延迟初始化）"""
        if self.user_db is None:
            self.user_db = UserDatabase(self.user_id)
        return self.user_db
    
    async def init_crawler(self, sec_user_id: str, cookie: str = "") -> Douyin:
        """初始化爬虫 - 重用原项目代码"""
        # 创建爬虫实例
        crawler = Douyin(
            target=sec_user_id,
            type="post",
            limit=20,  # 每个账号最多采集20个视频
            cookie=cookie
        )
        return crawler
    
    async def monitor_following(self, sec_user_id: str, cookie: str = ""):
        """监控用户关注列表"""
        logger.info(f"[{self.user_id}] 开始监控关注列表...")
        
        try:
            # 1. 获取关注列表
            following_crawler = Douyin(
                target=sec_user_id,
                type="following",
                limit=0,  # 不设限制，获取所有关注账号
                cookie=cookie
            )
            
            # 同步运行关注列表采集
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, following_crawler.run)
            
            following_list = following_crawler.results
            logger.info(f"[{self.user_id}] 共关注 {len(following_list)} 个账号")
            
            # 2. 并行采集每个账号的视频
            tasks = []
            for account in following_list:  # 处理所有关注账号
                account_sec_uid = account.get('sec_uid')
                account_name = account.get('nickname', 'Unknown')
                
                if account_sec_uid:
                    # 尝试保存账号信息
                    try:
                        self._get_db().save_account(
                            account_id=account_sec_uid,
                            sec_uid=account_sec_uid,
                            nickname=account_name,
                            follower_count=account.get('follower_count', 0)
                        )
                    except Exception as e:
                        logger.warning(f"[{self.user_id}] 保存账号信息失败: {e}")
                    
                    # 创建采集任务
                    task = self.executor.submit(
                        self.fetch_account_videos,
                        account_sec_uid,
                        account_name,
                        cookie
                    )
                    tasks.append(task)
            
            # 3. 处理结果
            for future in as_completed(tasks, timeout=600):  # 10分钟超时
                try:
                    account_id, videos = future.result()
                    if videos:
                        logger.info(f"[{self.user_id}] 账号 {account_id} 采集到 {len(videos)} 个视频")
                except Exception as e:
                    logger.error(f"[{self.user_id}] 采集失败: {e}")
            
            self.last_update_time = datetime.now()
            logger.info(f"[{self.user_id}] 关注列表监控完成")
            
        except Exception as e:
            logger.error(f"[{self.user_id}] 监控任务失败: {e}")
    
    def fetch_account_videos(self, account_sec_uid: str, account_name: str, cookie: str = "") -> tuple:
        """获取账号最近视频 - 重用原项目方法"""
        try:
            # 创建爬虫实例（不使用回调函数，直接处理数据）
            crawler = Douyin(
                target=account_sec_uid,
                type="post",
                limit=10,  # 每个账号最多10个视频
                cookie=cookie
            )
            
            # 运行采集
            crawler.run()
            
            # 过滤近3天的视频
            three_days_ago = datetime.now() - timedelta(days=3)
            recent_videos = []
            
            for video in crawler.results:
                video_time = video.get('time')
                if video_time:
                    video_datetime = datetime.fromtimestamp(video_time)
                    if video_datetime > three_days_ago:
                        recent_videos.append(video)
            
            # 保存视频数据
            if recent_videos:
                try:
                    self._get_db().save_video_data(account_sec_uid, recent_videos)
                except Exception as e:
                    logger.warning(f"[{self.user_id}] 保存视频数据失败: {e}")
            
            return account_sec_uid, recent_videos
            
        except Exception as e:
            logger.error(f"[{self.user_id}] 采集账号 {account_name} 失败: {e}")
            return account_sec_uid, []
    
    async def run_monitoring_task(self, cookie: str = ""):
        """运行监控任务"""
        self.is_running = True
        
        try:
            # 重新加载用户配置，确保获取最新的sec_user_id
            self.user_config = UserConfig(self.user_id)
            
            if not self.user_config.sec_user_id:
                logger.error(f"[{self.user_id}] 未设置抖音sec_user_id")
                self.is_running = False
                return
            
            # 开始监控
            await self.monitor_following(self.user_config.sec_user_id, cookie)
            
        finally:
            self.is_running = False
    
    def get_monitoring_state(self) -> Dict:
        """获取监控状态"""
        return {
            "is_running": self.is_running,
            "last_update": self.last_update_time.isoformat(),
            "following_count": self._get_db().get_following_count(),
            "user_id": self.user_id
        }
    
    def stop(self):
        """停止监控"""
        self.is_running = False
        # 关闭线程池
        self.executor.shutdown(wait=False)
        logger.info(f"[{self.user_id}] 监控已停止")
    
    def get_monitoring_data(self, limit: int = 100) -> List[Dict]:
        """获取监控数据"""
        return self._get_db().get_monitoring_data(limit)


# 全局监控任务管理器
class MonitoringTaskManager:
    """监控任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, MonitoringScheduler] = {}
    
    def get_scheduler(self, user_id: str) -> MonitoringScheduler:
        """获取用户的监控调度器"""
        if user_id not in self.tasks:
            self.tasks[user_id] = MonitoringScheduler(user_id)
        return self.tasks[user_id]
    
    async def start_task(self, user_id: str, cookie: str = ""):
        """开始监控任务"""
        scheduler = self.get_scheduler(user_id)
        await scheduler.run_monitoring_task(cookie)
    
    def stop_task(self, user_id: str):
        """停止监控任务"""
        if user_id in self.tasks:
            self.tasks[user_id].stop()
            del self.tasks[user_id]
    
    def get_task_state(self, user_id: str) -> Dict:
        """获取任务状态"""
        if user_id in self.tasks:
            return self.tasks[user_id].get_monitoring_state()
        return {
            "is_running": False,
            "last_update": datetime.now().isoformat(),
            "following_count": 0,
            "user_id": user_id
        }


# 全局实例
monitoring_manager = MonitoringTaskManager()