from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CookieStatus(str, Enum):
    """Cookie状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    INVALID = "invalid"


class CookieSetRequest(BaseModel):
    """设置Cookie的请求模型"""
    cookies: str = Field(..., description="Cookie字符串", min_length=1)
    user_id: Optional[str] = Field(None, description="用户ID（可选）")
    platform: str = Field(default="xhs_pc", description="平台类型")
    description: Optional[str] = Field(None, description="Cookie描述")


class CookieSetResponse(BaseModel):
    """设置Cookie的响应模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    platform: str = Field(..., description="平台类型")
    cookie_key: str = Field(..., description="Cookie键值")
    message: str = Field(..., description="操作消息")


class CookieDeleteResponse(BaseModel):
    """删除Cookie的响应模型"""
    deleted_count: int = Field(..., description="删除的Cookie数量")
    user_id: Optional[str] = Field(None, description="用户ID")
    platform: Optional[str] = Field(None, description="平台类型")
    message: str = Field(..., description="操作消息")


class CookieInfo(BaseModel):
    """Cookie信息模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    platform: str = Field(..., description="平台类型")
    status: CookieStatus = Field(default=CookieStatus.ACTIVE, description="Cookie状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_used: Optional[datetime] = Field(None, description="最后使用时间")
    description: Optional[str] = Field(None, description="Cookie描述")


class CookieStatusResponse(BaseModel):
    """Cookie状态响应模型"""
    cookies: Dict[str, CookieInfo] = Field(..., description="Cookie信息字典")
    total_count: int = Field(..., description="Cookie总数")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    service: str = Field(..., description="服务名称")
    status: str = Field(..., description="服务状态")
    total_cookies: int = Field(..., description="Cookie总数") 