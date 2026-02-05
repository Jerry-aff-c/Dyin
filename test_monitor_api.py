# -*- encoding: utf-8 -*-
"""
测试监控API功能
"""

import requests
import json
import time

API_BASE_URL = "http://127.0.0.1:8001"

# 配置参数
SEC_USER_ID = "MS4wLjABAAAABF-5EvorTy_tdI7eYmL2Mf0JdDQX6SHUtTkbgsfx13uJHWbiIftkY5Dh6je5brJ4"

# 从配置文件读取cookie
with open('config/settings.json', 'r', encoding='utf-8') as f:
    settings_data = json.load(f)
    COOKIE = settings_data.get('cookie', '').strip()

print("=" * 80)
print("测试监控API功能")
print("=" * 80)

# 1. 获取监控状态
print("\n步骤1：获取监控状态...")
print("-" * 80)
try:
    response = requests.get(f"{API_BASE_URL}/api/monitor/status")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 监控状态: {data}")
    else:
        print(f"✗ 请求失败: {response.text}")
except Exception as e:
    print(f"✗ 请求异常: {e}")

# 2. 启动监控任务
print("\n步骤2：启动监控任务...")
print("-" * 80)
try:
    response = requests.post(
        f"{API_BASE_URL}/api/monitor/start",
        json={
            "sec_user_id": SEC_USER_ID,
            "cookie": COOKIE
        }
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 监控任务已启动: {data}")
    else:
        print(f"✗ 启动失败: {response.text}")
except Exception as e:
    print(f"✗ 请求异常: {e}")

# 3. 等待一段时间让监控任务运行
print("\n步骤3：等待监控任务运行...")
print("-" * 80)
for i in range(10):
    time.sleep(3)
    try:
        response = requests.get(f"{API_BASE_URL}/api/monitor/status")
        if response.status_code == 200:
            data = response.json()
            print(f"[{i+1}/10] 监控状态: {data['monitoring']}, 账户数: {data['accounts_count']}")
        else:
            print(f"[{i+1}/10] 获取状态失败: {response.status_code}")
    except Exception as e:
        print(f"[{i+1}/10] 请求异常: {e}")

# 4. 获取监控数据
print("\n步骤4：获取监控数据...")
print("-" * 80)
try:
    response = requests.get(f"{API_BASE_URL}/api/monitor/data")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 数据条数: {data['total']}")
        if data['data']:
            print(f"✓ 第一条数据: {json.dumps(data['data'][0], indent=2, ensure_ascii=False)}")
        else:
            print("⚠ 暂无监控数据")
    else:
        print(f"✗ 获取数据失败: {response.text}")
except Exception as e:
    print(f"✗ 请求异常: {e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)