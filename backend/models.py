# -*- encoding: utf-8 -*-
"""
用户数据模型

扩展原项目数据模型，支持多用户隔离和授权管理。
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional

from .settings import settings


class UserConfig:
    """用户配置模型 - 每个用户独立存储"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id or self.generate_user_id()
        self.sec_user_id = ""  # 用户绑定的抖音sec_uid
        self.license_key = ""  # 授权码
        self.trial_start_time: Optional[datetime] = None  # 试用开始时间
        self.license_expiry: Optional[datetime] = None    # 授权过期时间
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # 加载现有配置（如果存在）
        self._load_existing_config()
    
    def generate_user_id(self) -> str:
        """生成唯一用户ID"""
        return str(uuid.uuid4())[:8]
    
    def _load_existing_config(self):
        """加载现有用户配置"""
        config_path = os.path.join(self.get_user_data_dir(self.user_id), 'user_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.user_id = data.get('user_id', self.user_id)
                self.sec_user_id = data.get('sec_user_id', '')
                self.license_key = data.get('license_key', '')
                
                # 解析时间字段
                if data.get('trial_start_time'):
                    try:
                        self.trial_start_time = datetime.fromisoformat(data['trial_start_time'])
                    except Exception:
                        pass
                
                if data.get('license_expiry'):
                    try:
                        self.license_expiry = datetime.fromisoformat(data['license_expiry'])
                    except Exception:
                        pass
                
                if data.get('created_at'):
                    try:
                        self.created_at = datetime.fromisoformat(data['created_at'])
                    except Exception:
                        pass
                
            except Exception:
                # 配置文件损坏，使用默认值
                pass
    
    def save(self):
        """保存用户配置到独立文件"""
        try:
            user_dir = self.get_user_data_dir(self.user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            config_path = os.path.join(user_dir, 'user_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'user_id': self.user_id,
                    'sec_user_id': self.sec_user_id,
                    'license_key': self.license_key,
                    'trial_start_time': self.trial_start_time.isoformat() if self.trial_start_time else None,
                    'license_expiry': self.license_expiry.isoformat() if self.license_expiry else None,
                    'created_at': self.created_at.isoformat(),
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 无法保存配置，记录错误
            print(f"保存配置失败: {e}")
            pass
    
    @staticmethod
    def get_user_data_dir(user_id: str = None) -> str:
        """获取用户数据目录 - 重用原项目数据目录结构"""
        base_dir = os.path.expanduser('~/.douyin_monitor')  # 与原项目保持一致
        
        # 如果无法访问用户目录，使用项目目录下的临时目录
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir, exist_ok=True)
                # 测试目录是否可写
                test_file = os.path.join(base_dir, 'test_write.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception:
                # 无法创建或写入用户目录，使用项目目录
                base_dir = os.path.join(os.path.dirname(__file__), '..', 'temp_data')
        else:
            # 目录存在，测试是否可写
            try:
                test_file = os.path.join(base_dir, 'test_write.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception:
                # 无法写入用户目录，使用项目目录
                base_dir = os.path.join(os.path.dirname(__file__), '..', 'temp_data')
        
        # 确保基础目录存在
        os.makedirs(base_dir, exist_ok=True)
        
        if user_id:
            user_dir = os.path.join(base_dir, 'users', user_id)
            # 确保用户目录存在
            os.makedirs(user_dir, exist_ok=True)
            return user_dir
        return base_dir
    
    def set_sec_user_id(self, sec_user_id: str):
        """设置抖音sec_user_id"""
        self.sec_user_id = sec_user_id
        self.last_updated = datetime.now()
        self.save()
    
    def set_license_key(self, license_key: str, expiry_date: datetime):
        """设置授权码和过期时间"""
        self.license_key = license_key
        self.license_expiry = expiry_date
        self.last_updated = datetime.now()
        self.save()
    
    def start_trial(self):
        """开始试用期"""
        self.trial_start_time = datetime.now()
        self.last_updated = datetime.now()
        self.save()
    
    def is_trial_active(self) -> bool:
        """检查试用期是否激活"""
        if not self.trial_start_time:
            return False
        # 试用期24小时
        trial_end = self.trial_start_time + timedelta(hours=24)
        return datetime.now() < trial_end
    
    def is_license_valid(self) -> bool:
        """检查授权是否有效"""
        if not self.license_expiry:
            return False
        return datetime.now() < self.license_expiry
    
    def has_valid_access(self) -> bool:
        """检查是否有有效访问权限"""
        return self.is_trial_active() or self.is_license_valid()


# 导入需要的模块
from datetime import timedelta