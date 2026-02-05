# -*- encoding: utf-8 -*-
"""
授权验证管理器

实现离线授权验证功能，使用 ECDSA 数字签名进行安全验证。
"""

import base64
import json
import os
from datetime import datetime
from typing import Dict, Any

from ecdsa import VerifyingKey, NIST256p, BadSignatureError

from ..models import UserConfig


class LicenseManager:
    """离线授权验证管理器"""
    
    # 内置公钥（由你生成并硬编码，对应你的私钥）
    # 注意：实际部署时需要替换为真实的公钥
    PUBLIC_KEY_HEX = "3059301306072a8648ce3d020106082a8648ce3d03010703420004a1f3b8c5e7d9f1a2b4c6d8e0f2a4c6e8d0b2d4f6h8j0l2n4p6r8t0v2x4z6b8d0f2a4c6e8d0b2d4f6h8j0l2n4p6r8t0v2x4z6b8d0f2a4c6e8d0b2d4f6h8j0l2n4p"
    
    @classmethod
    def verify_license(cls, license_key: str) -> Dict[str, Any]:
        """验证授权码并返回解析后的数据"""
        try:
            # 1. Base64解码
            decoded = base64.b64decode(license_key).decode('utf-8')
            license_data = json.loads(decoded)
            
            # 2. 分离数据和签名
            data_str = json.dumps(license_data['data'], sort_keys=True)
            signature = base64.b64decode(license_data['sig'])
            
            # 3. 使用内置公钥验证签名
            vk = VerifyingKey.from_string(bytes.fromhex(cls.PUBLIC_KEY_HEX), curve=NIST256p)
            
            if not vk.verify(signature, data_str.encode('utf-8')):
                return {"valid": False, "error": "签名验证失败"}
            
            # 4. 检查过期时间
            expiry_date = datetime.fromisoformat(license_data['data']['expiry'])
            if expiry_date < datetime.now():
                return {"valid": False, "error": "授权已过期"}
            
            return {
                "valid": True,
                "type": license_data['data']['type'],
                "expiry": expiry_date,
                "serial": license_data['data']['serial']
            }
            
        except BadSignatureError:
            return {"valid": False, "error": "签名验证失败"}
        except json.JSONDecodeError:
            return {"valid": False, "error": "授权码格式错误"}
        except Exception as e:
            return {"valid": False, "error": f"授权码无效: {str(e)}"}
    
    @classmethod
    def check_trial_period(cls, user_config: UserConfig) -> bool:
        """检查试用期状态"""
        if not user_config.trial_start_time:
            # 首次使用，开始试用
            user_config.start_trial()
            return True
        
        # 检查是否超过24小时
        from datetime import timedelta
        trial_end = user_config.trial_start_time + timedelta(hours=24)
        return datetime.now() < trial_end
    
    @classmethod
    def activate_license(cls, user_config: UserConfig, license_key: str) -> Dict[str, Any]:
        """激活授权码"""
        # 验证授权码
        verification_result = cls.verify_license(license_key)
        
        if not verification_result['valid']:
            return verification_result
        
        # 激活授权
        user_config.set_license_key(license_key, verification_result['expiry'])
        
        # 计算剩余天数
        from datetime import timedelta
        remaining_days = (verification_result['expiry'] - datetime.now()).days
        
        return {
            "valid": True,
            "type": verification_result['type'],
            "expiry": verification_result['expiry'].isoformat(),
            "serial": verification_result['serial'],
            "remaining_days": remaining_days
        }
    
    @classmethod
    def get_public_key(cls) -> str:
        """获取公钥"""
        # 尝试从文件加载公钥
        public_key_path = os.path.join(os.path.dirname(__file__), 'public_key.txt')
        if os.path.exists(public_key_path):
            try:
                with open(public_key_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                pass
        
        # 返回默认公钥
        return cls.PUBLIC_KEY_HEX