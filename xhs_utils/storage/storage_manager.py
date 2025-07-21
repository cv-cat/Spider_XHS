from typing import List, Dict, Any, Union
from loguru import logger
from . import StorageStrategy
from .excel_storage import ExcelStorage
from .file_storage import FileStorage
from .postgres_storage import PostgresStorage
from config.storage_config import  STORAGE_OPTIONS
from config.config import Config
import asyncio

class StorageManager:
    """存储管理器，用于管理多个存储策略"""
    
    def __init__(self):
        self.strategies: Dict[str, StorageStrategy] = {}
        
    def add_strategy(self, name: str, strategy: StorageStrategy):
        """添加存储策略"""
        self.strategies[name] = strategy
        
    def remove_strategy(self, name: str):
        """移除存储策略"""
        if name in self.strategies:
            del self.strategies[name]
            
    def _normalize_storage_options(self, storage_options: Union[str, dict, None] = None) -> dict:
        """
        规范化存储选项
        :param storage_options: 存储选项，可以是：
            - None: 使用默认选项
            - dict: 新的选项格式 {'save_choice': ['file', 'excel'], 'save_image': True, 'save_video': True}
        :return: 规范化后的存储选项字典
        """
        if storage_options is None:
            return STORAGE_OPTIONS.copy()
            
        if isinstance(storage_options, dict):
            options = STORAGE_OPTIONS.copy()
            options.update(storage_options)
            return options
            
        raise ValueError(f'不支持的存储选项类型: {type(storage_options)}')
            
    async def save_notes(self, notes: list, storage_options: Union[str, dict, None] = None, **kwargs):
        """
        使用指定的存储策略保存笔记列表
        :param notes: 笔记列表
        :param storage_options: 存储选项，可以是字符串（向后兼容）或字典（新格式）
        :param kwargs: 传递给存储策略的参数
        """
        if not notes:
            return
            
        options = self._normalize_storage_options(storage_options)
        strategy_names = options['save_choice']
        
        # 只使用已启用的存储策略
        strategy_names = [name for name in strategy_names 
                    if name in self.strategies]
                    
        for name in strategy_names:
            try:
                await self.strategies[name].save_notes(notes, **kwargs)
            except Exception as e:
                logger.error(f'使用存储策略 {name} 保存笔记列表失败: {str(e)}')
                    
    async def save_note_media(self, note_info: dict, storage_options: Union[str, dict, None] = None, **kwargs):
        """
        使用指定的存储策略保存笔记媒体文件
        :param note_info: 笔记信息
        :param storage_options: 存储选项，可以是字符串（向后兼容）或字典（新格式）
        :param kwargs: 传递给存储策略的参数
        """
        if not note_info:
            return
            
        options = self._normalize_storage_options(storage_options)
        strategy_names = options['save_choice']
            
        # 只使用已启用的存储策略
        strategy_names = [name for name in strategy_names 
                            if name in self.strategies]
    
        for name in strategy_names:
            try:
                await self.strategies[name].save_note_media(note_info, **kwargs)
            except Exception as e:
                logger.error(f'使用存储策略 {name} 保存笔记媒体文件失败: {str(e)}')
                    
    @classmethod
    def create_default(cls) -> 'StorageManager':
        """
        创建默认的存储管理器，根据配置文件初始化
        :return: 配置好的存储管理器
        """
        manager = cls()
        
        enabled_strategies = STORAGE_OPTIONS.get('save_choice', [])
        
        # 添加Excel存储策略
        if 'excel' in enabled_strategies:
            excel_config = Config.get_excel_config()
            manager.add_strategy('excel', ExcelStorage(excel_config['path']))
            
        # 添加文件存储策略
        if 'file' in enabled_strategies:
            file_config = Config.get_file_config()
            manager.add_strategy('file', FileStorage(file_config['path']))
            
        # 添加PostgreSQL存储策略
        if 'postgresql' in enabled_strategies:
            postgresql_config = Config.get_postgresql_config()
            manager.add_strategy('postgresql', PostgresStorage(postgresql_config))
            
        return manager
        
    def init_storage(self):
        """初始化所有存储策略"""
        for strategy in self.strategies.values():
            strategy.init_storage()
            
    def close(self):
        """关闭所有存储策略"""
        for strategy in self.strategies.values():
            try:
                strategy.close()
            except Exception as e:
                logger.error(f"关闭存储策略失败: {str(e)}") 