from typing import Dict, Optional, Any
import json
from datetime import datetime
from loguru import logger
from .config import PostgresConfig
from .client import PostgresClient

class PostgresManager:
    """PostgreSQL管理器类"""
    
    def __init__(self, config: PostgresConfig):
        self.config = config
        self.client = PostgresClient(config)
        
    async def init_tables(self):
        """初始化数据库表"""
        # 创建笔记表
        await self.client.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.client.table_name('notes')} (
                id SERIAL PRIMARY KEY,
                note_id VARCHAR(50) UNIQUE NOT NULL,
                note_url TEXT,
                note_type VARCHAR(20),
                user_id VARCHAR(50),
                home_url TEXT,
                nickname VARCHAR(100),
                avatar TEXT,
                title TEXT,
                description TEXT,
                liked_count INTEGER,
                collected_count INTEGER,
                comment_count INTEGER,
                share_count INTEGER,
                video_cover TEXT,
                video_url TEXT,
                image_urls JSONB,
                tags JSONB,
                upload_time TIMESTAMP,
                ip_location VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建媒体文件表
        await self.client.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.client.table_name('media_files')} (
                id SERIAL PRIMARY KEY,
                note_id VARCHAR(50) REFERENCES {self.client.table_name('notes')}(note_id),
                file_type VARCHAR(10),
                file_url TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.info("数据库表初始化完成")
        
    async def save_note(self, note_info: dict) -> bool:
        """
        保存笔记信息
        :param note_info: 笔记信息字典
        :return: 是否保存成功
        """
        try:
            # 转换上传时间
            upload_time = datetime.fromisoformat(note_info['upload_time']) if note_info.get('upload_time') else None
            
            # 插入笔记信息
            query = f"""
                INSERT INTO {self.client.table_name('notes')} (
                    note_id, note_url, note_type, user_id, home_url, nickname,
                    avatar, title, description, liked_count, collected_count,
                    comment_count, share_count, video_cover, video_url,
                    image_urls, tags, upload_time, ip_location,status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20
                )
                ON CONFLICT (note_id) DO UPDATE SET
                    note_url = EXCLUDED.note_url,
                    note_type = EXCLUDED.note_type,
                    user_id = EXCLUDED.user_id,
                    home_url = EXCLUDED.home_url,
                    nickname = EXCLUDED.nickname,
                    avatar = EXCLUDED.avatar,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    liked_count = EXCLUDED.liked_count,
                    collected_count = EXCLUDED.collected_count,
                    comment_count = EXCLUDED.comment_count,
                    share_count = EXCLUDED.share_count,
                    video_cover = EXCLUDED.video_cover,
                    video_url = EXCLUDED.video_url,
                    image_urls = EXCLUDED.image_urls,
                    tags = EXCLUDED.tags,
                    upload_time = EXCLUDED.upload_time,
                    ip_location = EXCLUDED.ip_location,
                    status = EXCLUDED.status
            """
            
            await self.client.execute(
                query,
                note_info['note_id'],
                note_info.get('note_url'),
                note_info.get('note_type'),
                note_info.get('user_id'),
                note_info.get('home_url'),
                note_info.get('nickname'),
                note_info.get('avatar'),
                note_info.get('title'),
                note_info.get('desc'),
                note_info.get('liked_count'),
                note_info.get('collected_count'),
                note_info.get('comment_count'),
                note_info.get('share_count'),
                note_info.get('video_cover'),
                note_info.get('video_addr'),
                json.dumps(note_info.get('image_list', [])),
                json.dumps(note_info.get('tags', [])),
                upload_time,
                note_info.get('ip_location'),
                1
            )
            
            logger.info(f"笔记保存成功: {note_info['note_id']}")
            return True
        except Exception as e:
            logger.error(f"笔记保存失败: {note_info['note_id']}, 错误: {str(e)}")
            return False
            
    async def save_media_file(self, note_id: str, file_type: str, file_url: str, file_path: str) -> bool:
        """
        保存媒体文件信息
        :param note_id: 笔记ID
        :param file_type: 文件类型（image/video）
        :param file_url: 文件URL
        :param file_path: 文件保存路径
        :return: 是否保存成功
        """
        try:
            query = f"""
                INSERT INTO {self.client.table_name('media_files')} (
                    note_id, file_type, file_url, file_path
                ) VALUES ($1, $2, $3, $4)
            """
            
            await self.client.execute(query, note_id, file_type, file_url, file_path)
            logger.info(f"媒体文件信息保存成功: {note_id} - {file_type}")
            return True
        except Exception as e:
            logger.error(f"媒体文件信息保存失败: {note_id} - {file_type}, 错误: {str(e)}")
            return False
            
    async def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        获取笔记信息
        :param note_id: 笔记ID
        :return: 笔记信息字典
        """
        try:
            query = f"""
                SELECT * FROM {self.client.table_name('notes')}
                WHERE note_id = $1
            """
            
            row = await self.client.fetchrow(query, note_id)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"获取笔记信息失败: {note_id}, 错误: {str(e)}")
            return None
            
    async def get_note_media_files(self, note_id: str) -> list:
        """
        获取笔记的媒体文件信息
        :param note_id: 笔记ID
        :return: 媒体文件信息列表
        """
        try:
            query = f"""
                SELECT * FROM {self.client.table_name('media_files')}
                WHERE note_id = $1
                ORDER BY created_at
            """
            
            rows = await self.client.fetch(query, note_id)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取笔记媒体文件信息失败: {note_id}, 错误: {str(e)}")
            return [] 