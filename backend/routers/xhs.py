from fastapi import APIRouter, HTTPException, status
from typing import Optional, Any
from models.error import ErrorResponse
from models.xhs import UserResponse
from services.cookie_manager import cookie_manager
from apis.xhs_pc_apis import XHS_Apis
from loguru import logger

# 创建XHS_Apis实例
xhs_apis = XHS_Apis()

# 创建API路由
router = APIRouter(prefix="/xhs", tags=["小红书API"])

# 定义统一的Cookie获取函数
def get_cookie_str(user_id: Optional[str], platform: str = "xhs_pc") -> str:
    """
    从Cookie管理器获取Cookie字符串
    
    - **user_id**: 用户ID（可选）
    - **platform**: 平台类型（默认为xhs_pc）
    
    如果Cookie不存在，则抛出401异常
    """
    cookie_str = cookie_manager.get_cookie(user_id=user_id, platform=platform)
    if not cookie_str:
        logger.warning(f"用户 {user_id} 的Cookie不存在")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cookie不存在，请先设置Cookie"
        )
    return cookie_str


@router.get("/user/me/v1", summary="获取用户信息V1")
async def get_self_info_v1(user_id: Optional[str] = None) -> Any:
    """
    获取当前登录用户的信息（V1版本）
    - **user_id**: 用户ID（可选），用于从Cookie管理器获取Cookie
    
    如果`user_id`未提供，将使用默认Cookie
    """
    try:
        cookie_str = get_cookie_str(user_id)
        
        # 调用小红书API
        success, msg, data = xhs_apis.get_user_self_info(cookies_str=cookie_str)
        
        if not success:
            logger.error(f"小红书API调用失败: {msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"小红书API调用失败: {msg}"
            )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.get("/user/me", response_model=UserResponse, responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse},
})
async def get_self_info_v2(user_id: Optional[str] = None):
    """
    获取当前登录用户的信息(V2版本)
    - **user_id**: 用户ID(可选), 用于从Cookie管理器获取Cookie
    
    如果`user_id`未提供, 将使用默认Cookie
    """
    cookie_str = cookie_manager.get_cookie(user_id=user_id)
    if not cookie_str or len(cookie_str) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cookie不存在, 请先设置Cookie"
        )
    success, msg, data = xhs_apis.get_user_self_info2(cookies_str=cookie_str)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"小红书API调用失败: {msg}"
        )
    return data