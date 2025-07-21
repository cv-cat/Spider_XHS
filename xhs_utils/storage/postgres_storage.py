import os
import openpyxl
from loguru import logger
from . import StorageStrategy
from ..data_util import norm_text
from datetime import datetime
from pkg.core.pg import PostgresConfig, PostgresManager

class PostgresStorage(StorageStrategy):
    """PostgreSQL存储策略"""
    
    def __init__(self, config_dict: dict):
        """
        初始化PostgreSQL存储策略
        :param config_dict: PostgreSQL配置字典，包含以下字段：
            - host: 主机地址
            - port: 端口号
            - database: 数据库名
            - user: 用户名
            - password: 密码
        """
        self.config = PostgresConfig.from_dict(config_dict)
        self.manager = PostgresManager(self.config)
        
    async def init_storage(self):
        """初始化存储（创建必要的表）"""
        try:
            await self.manager.init_tables()
            logger.info("PostgreSQL存储初始化完成")
        except Exception as e:
            logger.error(f"PostgreSQL存储初始化失败: {str(e)}")
            raise
            
    async def save_notes(self, notes: list, **kwargs):
        """
        保存笔记列表到PostgreSQL
        :param notes: 笔记列表
        :param kwargs: 额外参数（未使用）
        """
        if not notes:
            return
            
        success_count = 0
        for note in notes:
            try:
                # 转换上传时间格式
                if 'upload_time' in note and note['upload_time']:
                    try:
                        # 尝试解析不同的时间格式
                        upload_time = datetime.fromisoformat(note['upload_time'])
                        note['upload_time'] = upload_time.isoformat()
                    except (ValueError, TypeError):
                        note['upload_time'] = None
                
                # 保存笔记
                success = await self.manager.save_note(note)
                if success:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"保存笔记失败 {note.get('note_id', 'unknown')}: {str(e)}")
                
        logger.info(f"成功保存 {success_count}/{len(notes)} 条笔记到PostgreSQL")
            
    async def save_note_media(self, note_info: dict, **kwargs):
       pass
            
    async def close(self):
        """关闭数据库连接"""
        try:
            await self.manager.client.disconnect()
            logger.info("PostgreSQL连接已关闭")
        except Exception as e:
            logger.error(f"关闭PostgreSQL连接失败: {str(e)}") 