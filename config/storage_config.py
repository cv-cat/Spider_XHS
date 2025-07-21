"""存储配置文件"""
from .config import Config

# 统一的存储配置
STORAGE_OPTIONS = Config.get_storage_options() 