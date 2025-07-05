from fastapi import APIRouter, HTTPException, status
from typing import Optional
from models.cookie import (
    CookieSetRequest, 
    CookieSetResponse,
    CookieDeleteResponse,
    CookieStatusResponse,
    HealthCheckResponse
)
from services.cookie_manager import cookie_manager
from loguru import logger

router = APIRouter(prefix="/api/v1/cookie", tags=["Cookie管理"])


@router.post("/set", response_model=CookieSetResponse, summary="设置Cookie") 
async def set_cookie(request: CookieSetRequest):
    """
    设置Cookie
    
    - **cookies**: Cookie字符串（必填）
    - **user_id**: 用户ID（可选，如果不提供则使用默认用户）
    - **platform**: 平台类型（默认为xhs_pc）
    - **description**: Cookie描述（可选）
    """
    try:
        # 验证Cookie字符串不为空
        if not request.cookies.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cookie字符串不能为空"
            )
        
        # 调用Cookie管理器设置Cookie
        success, message = cookie_manager.set_cookie(
            cookie_str=request.cookies,
            user_id=request.user_id,
            platform=request.platform,
            description=request.description
        )
        
        if success:
            logger.info(f"Cookie设置成功 - user_id: {request.user_id}, platform: {request.platform}")
            return CookieSetResponse(
                user_id=request.user_id,
                platform=request.platform,
                cookie_key=f"{request.platform}:{request.user_id or 'default'}",
                message=message
            )
        else:
            logger.error(f"Cookie设置失败 - {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置Cookie异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置Cookie失败: {str(e)}"
        )


@router.delete("", response_model=CookieDeleteResponse, summary="删除Cookie")
async def delete_cookie(
    user_id: Optional[str] = None,
    platform: Optional[str] = None
):
    """
    删除Cookie
    
    - **user_id**: 用户ID（可选，如果不提供则删除所有用户的Cookie）
    - **platform**: 平台类型（可选，如果不提供则删除所有平台的Cookie）
    
    **删除逻辑：**
    - 如果同时提供user_id和platform，删除指定用户的指定平台Cookie
    - 如果只提供user_id，删除该用户的所有平台Cookie
    - 如果只提供platform，删除该平台的所有用户Cookie
    - 如果都不提供，删除所有Cookie
    """
    try:
        # 调用Cookie管理器删除Cookie
        success, message, deleted_count = cookie_manager.delete_cookie(
            user_id=user_id,
            platform=platform
        )
        
        logger.info(f"Cookie删除操作 - user_id: {user_id}, platform: {platform}, 删除数量: {deleted_count}")
        
        return CookieDeleteResponse(
            deleted_count=deleted_count,
            user_id=user_id,
            platform=platform,
            message=message
        )
            
    except Exception as e:
        logger.error(f"删除Cookie异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Cookie失败: {str(e)}"
        )


@router.get("/status", response_model=CookieStatusResponse, summary="检查Cookie状态")
async def get_cookie_status(
    user_id: Optional[str] = None,
    platform: Optional[str] = None
):
    """
    检查Cookie状态
    
    - **user_id**: 用户ID（可选，如果不提供则返回所有用户的Cookie状态）
    - **platform**: 平台类型（可选，如果不提供则返回所有平台的Cookie状态）
    
    **查询逻辑：**
    - 如果同时提供user_id和platform，返回指定用户的指定平台Cookie状态
    - 如果只提供user_id，返回该用户的所有平台Cookie状态
    - 如果只提供platform，返回该平台的所有用户Cookie状态
    - 如果都不提供，返回所有Cookie状态
    """
    try:
        # 获取所有Cookie信息
        all_cookies_info = cookie_manager.get_all_cookies_info()
        
        # 根据查询条件过滤结果
        filtered_cookies = {}
        
        for cookie_key, cookie_info in all_cookies_info.items():
            # 解析cookie_key格式: platform:user_id
            parts = cookie_key.split(":", 1)
            if len(parts) != 2:
                continue
                
            cookie_platform, cookie_user_id = parts
            # 处理默认用户的情况
            if cookie_user_id == "default":
                cookie_user_id = None
            
            # 应用过滤条件
            if user_id is not None and cookie_user_id != user_id:
                continue
            if platform is not None and cookie_platform != platform:
                continue
                
            filtered_cookies[cookie_key] = cookie_info
        
        total_count = len(filtered_cookies)
        
        logger.info(f"Cookie状态查询成功 - user_id: {user_id}, platform: {platform}, 总数: {total_count}")
        
        return CookieStatusResponse(
            cookies=filtered_cookies,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"获取Cookie状态异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Cookie状态失败: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse, summary="健康检查")
async def health_check():
    try:
        total_count = cookie_manager.get_cookie_count()
        return HealthCheckResponse(
            service="cookie_manager",
            status="healthy",
            total_cookies=total_count
        )
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        ) 