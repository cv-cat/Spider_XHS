from typing import Dict, Optional, List, Tuple
from datetime import datetime
import threading
from models.cookie import CookieInfo, CookieStatus
from loguru import logger


class CookieManager:
    """内存Cookie管理器"""
    
    def __init__(self):
        # 存储结构: {cookie_key: {"cookie_str": str, "info": CookieInfo}}
        self._cookies: Dict[str, Dict] = {}
        self._lock = threading.RLock()  # 使用可重入锁保证线程安全
    
    def _generate_cookie_key(self, user_id: Optional[str], platform: str) -> str:
        """生成Cookie的唯一键"""
        if user_id:
            return f"{platform}:{user_id}"
        else:
            return f"{platform}:default"
    
    def set_cookie(self, cookie_str: str, user_id: Optional[str] = None, 
                   platform: str = "xhs_pc", description: Optional[str] = None) -> Tuple[bool, str]:
        """
        设置Cookie
        
        Args:
            cookie_str: Cookie字符串
            user_id: 用户ID（可选）
            platform: 平台类型
            description: Cookie描述
            
        Returns:
            (success, message)
        """
        with self._lock:
            try:
                cookie_key = self._generate_cookie_key(user_id, platform)
                
                # 创建Cookie信息
                cookie_info = CookieInfo(
                    user_id=user_id,
                    platform=platform,
                    status=CookieStatus.ACTIVE,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    description=description
                )
                
                # 存储Cookie
                self._cookies[cookie_key] = {
                    "cookie_str": cookie_str,
                    "info": cookie_info
                }
                
                logger.info(f"Cookie设置成功: {cookie_key}")
                return True, "Cookie设置成功"
                
            except Exception as e:
                logger.error(f"设置Cookie失败: {str(e)}")
                return False, f"设置Cookie失败: {str(e)}"
    
    def get_cookie(self, user_id: Optional[str] = None, platform: str = "xhs_pc") -> Optional[str]:
        """
        获取Cookie字符串
        
        Args:
            user_id: 用户ID（可选）
            platform: 平台类型
            
        Returns:
            Cookie字符串或None
        """
        with self._lock:
            try:
                cookie_key = self._generate_cookie_key(user_id, platform)
                
                if cookie_key in self._cookies:
                    cookie_data = self._cookies[cookie_key]
                    
                    # 更新最后使用时间
                    cookie_data["info"].last_used = datetime.now()
                    
                    logger.info(f"Cookie获取成功: {cookie_key}")
                    return cookie_data["cookie_str"]
                    
                return None
                
            except Exception as e:
                logger.error(f"获取Cookie失败: {str(e)}")
                return None
    
    def delete_cookie(self, user_id: Optional[str] = None, platform: Optional[str] = None) -> Tuple[bool, str, int]:
        """
        删除Cookie
        
        Args:
            user_id: 用户ID（可选，如果不提供则删除所有）
            platform: 平台类型（可选）
            
        Returns:
            (success, message, deleted_count)
        """
        with self._lock:
            try:
                deleted_count = 0
                
                if user_id is not None and platform is not None:
                    # 删除指定用户的指定平台Cookie
                    cookie_key = self._generate_cookie_key(user_id, platform)
                    if cookie_key in self._cookies:
                        del self._cookies[cookie_key]
                        deleted_count = 1
                        logger.info(f"Cookie删除成功: {cookie_key}")
                
                elif user_id is not None:
                    # 删除指定用户的所有平台Cookie
                    keys_to_delete = [key for key in self._cookies.keys() 
                                    if key.endswith(f":{user_id}")]
                    for key in keys_to_delete:
                        del self._cookies[key]
                        deleted_count += 1
                    logger.info(f"用户 {user_id} 的所有Cookie删除成功，共删除 {deleted_count} 个")
                
                elif platform is not None:
                    # 删除指定平台的所有Cookie
                    keys_to_delete = [key for key in self._cookies.keys() 
                                    if key.startswith(f"{platform}:")]
                    for key in keys_to_delete:
                        del self._cookies[key]
                        deleted_count += 1
                    logger.info(f"平台 {platform} 的所有Cookie删除成功，共删除 {deleted_count} 个")
                
                else:
                    # 删除所有Cookie
                    deleted_count = len(self._cookies)
                    self._cookies.clear()
                    logger.info(f"所有Cookie删除成功，共删除 {deleted_count} 个")
                
                if deleted_count > 0:
                    return True, f"成功删除 {deleted_count} 个Cookie", deleted_count
                else:
                    return False, "没有找到匹配的Cookie", 0
                    
            except Exception as e:
                logger.error(f"删除Cookie失败: {str(e)}")
                return False, f"删除Cookie失败: {str(e)}", 0
    
    def get_all_cookies_info(self) -> Dict[str, CookieInfo]:
        """
        获取所有Cookie的信息（不包含Cookie字符串）
        
        Returns:
            Cookie信息字典
        """
        with self._lock:
            try:
                result = {}
                for key, cookie_data in self._cookies.items():
                    result[key] = cookie_data["info"]
                return result
                
            except Exception as e:
                logger.error(f"获取Cookie信息失败: {str(e)}")
                return {}
    
    def get_cookie_count(self) -> int:
        """获取Cookie总数"""
        with self._lock:
            return len(self._cookies)
    
    def is_cookie_exists(self, user_id: Optional[str] = None, platform: str = "xhs_pc") -> bool:
        """检查Cookie是否存在"""
        with self._lock:
            cookie_key = self._generate_cookie_key(user_id, platform)
            return cookie_key in self._cookies
    
    def update_cookie_status(self, user_id: Optional[str], platform: str, 
                           status: CookieStatus) -> Tuple[bool, str]:
        """
        更新Cookie状态
        
        Args:
            user_id: 用户ID
            platform: 平台类型
            status: 新状态
            
        Returns:
            (success, message)
        """
        with self._lock:
            try:
                cookie_key = self._generate_cookie_key(user_id, platform)
                
                if cookie_key in self._cookies:
                    self._cookies[cookie_key]["info"].status = status
                    self._cookies[cookie_key]["info"].updated_at = datetime.now()
                    
                    logger.info(f"Cookie状态更新成功: {cookie_key} -> {status}")
                    return True, "Cookie状态更新成功"
                else:
                    return False, "Cookie不存在"
                    
            except Exception as e:
                logger.error(f"更新Cookie状态失败: {str(e)}")
                return False, f"更新Cookie状态失败: {str(e)}"


# 创建全局Cookie管理器实例
cookie_manager = CookieManager() 