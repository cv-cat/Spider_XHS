import os
import json
import aiohttp
import aiofiles
from loguru import logger
from . import StorageStrategy
from ..data_util import norm_str

class FileStorage(StorageStrategy):
    """文件存储策略"""
    
    def __init__(self, base_path):
        self.base_path = base_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            
    async def save_notes(self, notes: list, **kwargs):
        """保存笔记列表到文件系统"""
        if not notes:
            return
            
        for note in notes:
            await self._save_note_detail(note)
            
    async def save_note_media(self, note_info: dict, **kwargs):
        """
        保存笔记的媒体文件
        :param note_info: 笔记信息
        :param kwargs: 存储选项，包含：
            - save_image: 是否保存图片
            - save_video: 是否保存视频
        """
        if not note_info:
            return
            
        note_id = note_info['note_id']
        title = norm_str(note_info['title'])[:40]
        
        if title.strip() == '':
            title = '无标题'
            
        save_path = os.path.join(self.base_path, f'{title}_{note_id}')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        save_image = kwargs.get('save_image', True)
        save_video = kwargs.get('save_video', True)
        
        # 保存图片
        if save_image and note_info.get('image_list'):
            media_path = os.path.join(save_path, 'images')
            if not os.path.exists(media_path):
                os.makedirs(media_path)
                
            for idx, image_url in enumerate(note_info['image_list']):
                await self._download_media(image_url, os.path.join(media_path, f'image_{idx}.jpg'))
                
        # 保存视频
        if save_video and note_info.get('video_addr'):
            media_path = os.path.join(save_path, 'video')
            if not os.path.exists(media_path):
                os.makedirs(media_path)
                
            # 保存视频封面
            if note_info.get('video_cover'):
                await self._download_media(note_info['video_cover'], os.path.join(media_path, 'cover.jpg'))
                
            # 保存视频文件
            await self._download_media(note_info['video_addr'], os.path.join(media_path, 'video.mp4'))
            
    async def _save_note_detail(self, note: dict):
        """保存笔记详细信息到文本文件"""
        if not note:
            return
            
        note_id = note['note_id']
        title = norm_str(note['title'])[:40]
        
        if title.strip() == '':
            title = '无标题'
            
        save_path = os.path.join(self.base_path, f'{title}_{note_id}')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        # 保存JSON格式
        async with aiofiles.open(os.path.join(save_path, 'info.json'), 'w', encoding='utf-8') as f:
            await f.write(json.dumps(note, ensure_ascii=False, indent=2))
            
        # 保存可读的文本格式
        async with aiofiles.open(os.path.join(save_path, 'detail.txt'), 'w', encoding='utf-8') as f:
            await f.write(f"笔记id: {note['note_id']}\n")
            await f.write(f"笔记url: {note['note_url']}\n")
            await f.write(f"笔记类型: {note['note_type']}\n")
            await f.write(f"用户id: {note['user_id']}\n")
            await f.write(f"用户主页url: {note['home_url']}\n")
            await f.write(f"昵称: {note['nickname']}\n")
            await f.write(f"头像url: {note['avatar']}\n")
            await f.write(f"标题: {note['title']}\n")
            await f.write(f"描述: {note['desc']}\n")
            await f.write(f"点赞数量: {note['liked_count']}\n")
            await f.write(f"收藏数量: {note['collected_count']}\n")
            await f.write(f"评论数量: {note['comment_count']}\n")
            await f.write(f"分享数量: {note['share_count']}\n")
            await f.write(f"视频封面url: {note['video_cover']}\n")
            await f.write(f"视频地址url: {note['video_addr']}\n")
            await f.write(f"图片地址url列表: {note['image_list']}\n")
            await f.write(f"标签: {note['tags']}\n")
            await f.write(f"上传时间: {note['upload_time']}\n")
            await f.write(f"ip归属地: {note['ip_location']}\n")
            
    async def _download_media(self, url: str, save_path: str):
        """下载媒体文件"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(save_path, 'wb') as f:
                            await f.write(await response.read())
                        logger.info(f"媒体文件下载成功: {save_path}")
                    else:
                        logger.error(f"媒体文件下载失败: {url}, 状态码: {response.status}")
        except Exception as e:
            logger.error(f"媒体文件下载失败: {url}, 错误: {str(e)}")
            
    async def close(self):
        """关闭存储策略"""
        pass 