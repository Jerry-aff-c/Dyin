#!/usr/bin/env python3
"""
授权码生成器 - 用于生成带有ECDSA数字签名的授权码

使用方法:
1. 首先运行此脚本生成密钥对（仅需执行一次）
2. 使用生成的私钥生成授权码
3. 将公钥硬编码到 backend/auth/license_manager.py 中
"""

import json
import base64
from datetime import datetime, timedelta
from ecdsa import SigningKey, VerifyingKey, NIST256p
import os

class LicenseGenerator:
    """授权码生成器"""
    
    def __init__(self, private_key_path='private_key.pem', public_key_path='public_key.pem'):
        """初始化授权码生成器"""
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.sk = None
        self.vk = None
    
    def generate_keypair(self):
        """生成密钥对"""
        print("生成密钥对...")
        sk = SigningKey.generate(curve=NIST256p)
        vk = sk.get_verifying_key()
        
        # 保存密钥
        with open(self.private_key_path, 'wb') as f:
            f.write(sk.to_pem())
        
        with open(self.public_key_path, 'wb') as f:
            f.write(vk.to_pem())
        
        # 生成公钥的十六进制表示（用于硬编码到代码中）
        public_key_hex = vk.to_string().hex()
        print(f"公钥（十六进制）: {public_key_hex}")
        print(f"私钥已保存到: {self.private_key_path}")
        print(f"公钥已保存到: {self.public_key_path}")
        
        return sk, vk
    
    def load_keypair(self):
        """加载密钥对"""
        if not os.path.exists(self.private_key_path):
            print(f"私钥文件不存在: {self.private_key_path}")
            print("请先运行 generate_keypair() 生成密钥对")
            return False
        
        with open(self.private_key_path, 'rb') as f:
            self.sk = SigningKey.from_pem(f.read())
        
        self.vk = self.sk.get_verifying_key()
        print("密钥对加载成功")
        return True
    
    def generate_license(self, license_type='professional', days=365):
        """生成授权码
        
        Args:
            license_type: 授权类型 (trial/professional/enterprise)
            days: 授权天数
            
        Returns:
            str: 授权码
        """
        if not self.sk:
            if not self.load_keypair():
                return None
        
        # 计算过期时间
        expiry_date = datetime.now() + timedelta(days=days)
        
        # 授权数据
        license_data = {
            "data": {
                "type": license_type,
                "expiry": expiry_date.isoformat(),
                "serial": self._generate_serial(),
                "issued_at": datetime.now().isoformat()
            }
        }
        
        # 生成签名
        data_str = json.dumps(license_data['data'], sort_keys=True)
        signature = self.sk.sign(data_str.encode('utf-8'))
        
        # 添加签名到授权数据
        license_data['sig'] = base64.b64encode(signature).decode('utf-8')
        
        # 生成最终授权码
        license_key = base64.b64encode(
            json.dumps(license_data).encode('utf-8')
        ).decode('utf-8')
        
        print(f"授权码生成成功:")
        print(f"类型: {license_type}")
        print(f"过期时间: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"授权码: {license_key}")
        
        return license_key
    
    def _generate_serial(self):
        """生成序列号"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    
    def verify_license(self, license_key):
        """验证授权码
        
        Args:
            license_key: 授权码
            
        Returns:
            dict: 验证结果
        """
        try:
            # 解码授权码
            decoded = base64.b64decode(license_key).decode('utf-8')
            license_data = json.loads(decoded)
            
            # 分离数据和签名
            data_str = json.dumps(license_data['data'], sort_keys=True)
            signature = base64.b64decode(license_data['sig'])
            
            # 验证签名
            if not self.vk.verify(signature, data_str.encode('utf-8')):
                return {"valid": False, "error": "签名验证失败"}
            
            # 检查过期时间
            expiry_date = datetime.fromisoformat(license_data['data']['expiry'])
            if expiry_date < datetime.now():
                return {"valid": False, "error": "授权已过期"}
            
            return {
                "valid": True,
                "type": license_data['data']['type'],
                "expiry": expiry_date,
                "serial": license_data['data']['serial']
            }
            
        except Exception as e:
            return {"valid": False, "error": f"验证失败: {str(e)}"}

def main():
    """主函数"""
    generator = LicenseGenerator()
    
    while True:
        print("\n=== 授权码生成器 ===")
        print("1. 生成密钥对")
        print("2. 生成试用授权码 (7天)")
        print("3. 生成专业版授权码 (365天)")
        print("4. 生成企业版授权码 (730天)")
        print("5. 退出")
        
        choice = input("请选择操作: ")
        
        if choice == '1':
            generator.generate_keypair()
        elif choice == '2':
            generator.generate_license('trial', 7)
        elif choice == '3':
            generator.generate_license('professional', 365)
        elif choice == '4':
            generator.generate_license('enterprise', 730)
        elif choice == '5':
            break
        else:
            print("无效的选择，请重新输入")

if __name__ == '__main__':
    main()
