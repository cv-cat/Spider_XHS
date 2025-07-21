"""
Rate limiter configuration settings
"""

"""配置管理模块"""
import os
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    @staticmethod
    def get_rate_limiter_config() -> Dict[str, Any]:
        """获取速率限制的配置"""
        return {
            # 在时间窗口内允许的最大请求数
            'max_requests': int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '2')),
            
            # 时间窗口大小(秒)
            'time_window': int(os.getenv('RATE_LIMIT_TIME_WINDOW', '1')),
            
            # 随机延迟的最小值(秒)
            'min_delay': float(os.getenv('RATE_LIMIT_MIN_DELAY', '0.5')),
            
            # 随机延迟的最大值(秒)
            'max_delay': float(os.getenv('RATE_LIMIT_MAX_DELAY', '2.0')),
            'enabled': os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
        }
    
    @staticmethod
    def get_storage_options() -> Dict[str, Any]:
        """获取存储相关的配置"""
        return {
            # 存储策略选择
            'save_choice': os.getenv('STORAGE_CHOICES', 'file,excel').split(','),
            # 媒体文件存储选项
            'save_image': os.getenv('SAVE_IMAGE', 'true').lower() == 'true',
            'save_video': os.getenv('SAVE_VIDEO', 'true').lower() == 'true',
        }
    
    @staticmethod
    def get_excel_config() -> Dict[str, str]:
        """获取Excel存储的配置"""
        return {
            'path': os.getenv('EXCEL_STORAGE_PATH', 'data/excel')
        }
    
    @staticmethod
    def get_file_config() -> Dict[str, str]:
        """获取文件存储的配置"""
        return {
            'path': os.getenv('FILE_STORAGE_PATH', 'data/media')
        }
    
    @staticmethod
    def get_postgresql_config() -> Dict[str, Any]:
        """获取PostgreSQL的配置"""
        return {
            'host': os.getenv('PG_HOST', 'localhost'),
            'port': int(os.getenv('PG_PORT', '5432')),
            'database': os.getenv('PG_DATABASE', 'xhs_spider'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASSWORD', 'postgres'),
            'min_connections': int(os.getenv('PG_MIN_CONNECTIONS', '1')),
            'max_connections': int(os.getenv('PG_MAX_CONNECTIONS', '10')),
            'connection_timeout': int(os.getenv('PG_CONNECTION_TIMEOUT', '30')),
        } 