# -*- encoding: utf-8 -*-
"""
监控API路由

提供监控相关的API接口，支持状态查询、任务控制和数据获取。
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any
import asyncio

from ..models import UserConfig
from ..auth.license_manager import LicenseManager
from ..monitor.scheduler import monitoring_manager
from ..settings import settings

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


# 依赖注入：获取当前用户配置
async def get_current_user(request: Request) -> UserConfig:
    """从请求中获取用户ID并加载配置"""
    # 从请求头或cookie中获取用户ID
    user_id = request.headers.get('X-User-ID') or request.cookies.get('user_id')
    
    # 如果没有用户ID，使用默认用户ID
    if not user_id:
        user_id = "default"
    
    user_config = UserConfig(user_id)
    
    # 检查授权状态
    if not user_config.has_valid_access():
        # 检查试用期
        if not LicenseManager.check_trial_period(user_config):
            raise HTTPException(status_code=403, detail="授权已过期")
    
    return user_config


@router.get("/status")
async def get_monitor_status(user: UserConfig = Depends(get_current_user)):
    """获取监控状态"""
    scheduler = monitoring_manager.get_scheduler(user.user_id)
    state = scheduler.get_monitoring_state()
    
    return {
        "sec_user_id": user.sec_user_id,
        "monitoring": state["is_running"],
        "last_update": state["last_update"],
        "accounts_count": state["following_count"],
        "user_id": user.user_id
    }


@router.post("/start")
async def start_monitoring(
    request_data: dict,
    user: UserConfig = Depends(get_current_user)
):
    """开始监控任务 - 重用原项目爬虫"""
    # 从请求体中获取sec_user_id（如果提供）
    sec_user_id = request_data.get("sec_user_id", "")
    if sec_user_id:
        user.sec_user_id = sec_user_id
        user.save()
    
    if not user.sec_user_id:
        raise HTTPException(status_code=400, detail="请先设置抖音sec_user_id")
    
    # 获取cookie，如果请求中没有提供，则从配置文件获取
    cookie = request_data.get("cookie", "")
    if not cookie:
        cookie = settings.get("cookie", "").strip()
    
    # 启动后台任务
    asyncio.create_task(
        monitoring_manager.get_scheduler(user.user_id).run_monitoring_task(cookie)
    )
    
    return {
        "message": "监控任务已启动",
        "user_id": user.user_id,
        "sec_user_id": user.sec_user_id
    }


@router.post("/stop")
async def stop_monitoring(user: UserConfig = Depends(get_current_user)):
    """停止监控任务"""
    monitoring_manager.stop_task(user.user_id)
    return {
        "message": "监控任务已停止",
        "user_id": user.user_id
    }


@router.get("/data")
async def get_monitoring_data(
    limit: int = 100,
    user: UserConfig = Depends(get_current_user)
):
    """获取监控数据"""
    scheduler = monitoring_manager.get_scheduler(user.user_id)
    data = scheduler.get_monitoring_data(limit)
    
    return {
        "data": data,
        "total": len(data),
        "user_id": user.user_id
    }


@router.post("/set-sec-user-id")
async def set_sec_user_id(
    request_data: dict,
    user: UserConfig = Depends(get_current_user)
):
    """设置抖音sec_user_id"""
    sec_user_id = request_data.get("sec_user_id", "")
    if not sec_user_id:
        raise HTTPException(status_code=400, detail="sec_user_id不能为空")
    
    user.sec_user_id = sec_user_id
    user.save()
    
    return {
        "message": "sec_user_id设置成功",
        "sec_user_id": sec_user_id,
        "user_id": user.user_id
    }


@router.post("/auth/activate")
async def activate_license(
    request_data: dict,
    user: UserConfig = Depends(get_current_user)
):
    """激活授权码"""
    license_key = request_data.get("license_key", "")
    if not license_key:
        raise HTTPException(status_code=400, detail="授权码不能为空")
    
    # 激活授权
    result = LicenseManager.activate_license(user, license_key)
    
    if not result['valid']:
        raise HTTPException(status_code=400, detail=result.get('error', '授权码无效'))
    
    return result


@router.get("/auth/status")
async def get_auth_status(user: UserConfig = Depends(get_current_user)):
    """获取授权状态"""
    # 检查试用期
    is_trial_active = user.is_trial_active()
    
    # 检查授权状态
    is_license_valid = user.is_license_valid()
    
    # 计算剩余时间
    remaining_days = 0
    if is_trial_active:
        from datetime import timedelta
        trial_end = user.trial_start_time + timedelta(hours=24)
        remaining_days = (trial_end - user.created_at).days
    elif is_license_valid:
        from datetime import timedelta
        remaining_days = (user.license_expiry - user.created_at).days
    
    return {
        "is_trial_active": is_trial_active,
        "is_license_valid": is_license_valid,
        "has_valid_access": user.has_valid_access(),
        "remaining_days": remaining_days,
        "user_id": user.user_id
    }
