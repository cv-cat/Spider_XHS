import os
import openpyxl
import aiofiles
from loguru import logger
from . import StorageStrategy
from ..data_util import norm_text

class ExcelStorage(StorageStrategy):
    """Excel存储策略"""
    
    def __init__(self, base_path):
        self.base_path = base_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            
    async def save_notes(self, notes: list, **kwargs):
        """
        保存笔记列表到Excel
        :param notes: 笔记列表
        :param kwargs: 
            - filename: Excel文件名（不含扩展名）
        """
        if not notes:
            return
            
        filename = kwargs.get('filename', 'notes')
        file_path = os.path.abspath(os.path.join(self.base_path, f'{filename}.xlsx'))
        
        wb = openpyxl.Workbook()
        ws = wb.active
        
        # 设置表头
        headers = ['笔记id', '笔记url', '笔记类型', '用户id', '用户主页url', '昵称', 
                  '头像url', '标题', '描述', '点赞数量', '收藏数量', '评论数量', 
                  '分享数量', '视频封面url', '视频地址url', '图片地址url列表', 
                  '标签', '上传时间', 'ip归属地']
        ws.append(headers)
        
        # 写入数据
        for note in notes:
            row_data = [
                note.get('note_id', ''),
                note.get('note_url', ''),
                note.get('note_type', ''),
                note.get('user_id', ''),
                note.get('home_url', ''),
                note.get('nickname', ''),
                note.get('avatar', ''),
                note.get('title', ''),
                note.get('desc', ''),
                note.get('liked_count', ''),
                note.get('collected_count', ''),
                note.get('comment_count', ''),
                note.get('share_count', ''),
                note.get('video_cover', ''),
                note.get('video_addr', ''),
                str(note.get('image_list', [])),
                str(note.get('tags', [])),
                note.get('upload_time', ''),
                note.get('ip_location', '')
            ]
            ws.append([norm_text(str(v)) for v in row_data])
            
        wb.save(file_path)
        logger.info(f'数据已保存至Excel文件: {file_path}')
        
    async def save_note_media(self, note_info: dict, **kwargs):
        """Excel存储策略不需要实现媒体文件保存"""
        pass
        
    async def close(self):
        """关闭存储策略"""
        pass 