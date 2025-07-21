from abc import ABC, abstractmethod

class StorageStrategy(ABC):
    """存储策略基类"""
    
    async def init_storage(self):
        """初始化存储（可选实现）"""
        pass
        
    @abstractmethod
    async def save_notes(self, notes: list, **kwargs):
        """
        保存笔记列表
        :param notes: 笔记列表
        :param kwargs: 额外参数
        """
        pass
        
    @abstractmethod
    async def save_note_media(self, note_info: dict, **kwargs):
        """
        保存笔记的媒体文件
        :param note_info: 笔记信息
        :param kwargs: 额外参数
        """
        pass
        
    async def close(self):
        """关闭存储（可选实现）"""
        pass 