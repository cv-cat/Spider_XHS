import json
import os
import asyncio
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import handle_note_info
from xhs_utils.storage.storage_manager import StorageManager
from config.storage_config import STORAGE_OPTIONS

# 配置日志输出
logger.add("logs/spider_{time}.log", rotation="500 MB", encoding="utf-8", enqueue=True, retention="10 days")

class Data_Spider():
    def __init__(self):
        self.xhs_apis = XHS_Apis()
        self.storage_manager = StorageManager.create_default()

    def spider_note(self, note_url: str, cookies_str: str, proxies=None):
        """
        爬取一个笔记的信息
        :param note_url:
        :param cookies_str:
        :return:
        """
        note_info = None
        try:
            success, msg, note_info = self.xhs_apis.get_note_info(note_url, cookies_str, proxies)
            if success:
                note_info = note_info['data']['items'][0]
                note_info['url'] = note_url
                note_info = handle_note_info(note_info)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取笔记信息 {note_url}: {success}, msg: {msg}')
        return success, msg, note_info

    async def spider_some_note(self, notes: list, cookies_str: str,  storage_options: dict = None, excel_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes: 笔记URL列表
        :param cookies_str: cookies字符串
        :param storage_options: 存储选项字典，格式如：
            {
                'save_choice': ['file', 'excel'],  # 使用的存储策略列表
                'save_image': True,  # 是否保存图片
                'save_video': True   # 是否保存视频
            }
        :param excel_name: Excel文件名（不含扩展名）
        :param proxies: 代理设置
        """
        if 'excel' in (storage_options or {}).get('save_choice', []) and excel_name == '':
            raise ValueError('使用Excel存储时，excel_name 不能为空')
            
        note_list = []
        for note_url in notes:
            success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
            if not success:
                logger.error(f'爬取失败，停止继续爬取。失败原因: {msg}')
                break
                
            if note_info is not None:
                note_list.append(note_info)
                logger.info(f'成功爬取笔记: {note_info["note_id"]}')
        
                # 保存数据
                await self.storage_manager.save_notes(note_list, storage_options, filename=excel_name)
                
                # 如果需要保存媒体文件
                if storage_options and (storage_options['save_image'] or storage_options['save_video']):
                    for note_info in note_list:
                        await self.storage_manager.save_note_media(note_info, storage_options)
            
        logger.info(f'成功爬取 {len(note_list)} 个笔记')
        
        return True, "success", note_list

    async def spider_some_search_note(self, query: str, require_num: int, cookies_str: str, storage_options: dict, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo: dict = None, proxies=None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param storage_manager 存储管理器
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            返回搜索的结果
        """
        note_list = []
        success = False
        msg = ""
        excel_name = query  # 初始化excel_name
        
        try:
            success, msg, notes = self.xhs_apis.search_some_note(query, require_num, cookies_str, sort_type_choice, note_type, note_time, note_range, pos_distance, geo, proxies)
            if success:
                notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
                for note in notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_list.append(note_url)
                if note_list:  # 只有在有笔记时才调用spider_some_note
                    return await self.spider_some_note(note_list, cookies_str, storage_options, excel_name, proxies)
        except Exception as e:
            success = False
            msg = str(e)
            
        logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return False, msg, note_list

async def main():
    """
    此文件为爬虫的入口文件，可以直接运行
    apis/xhs_pc_apis.py 为爬虫的api文件，包含小红书的全部数据接口，可以继续封装
    apis/xhs_creator_apis.py 为小红书创作者中心的api文件
    感谢star和follow
    """
    cookies_str, _ = init()  # 不再使用base_path
    data_spider = Data_Spider()

    # 3 搜索指定关键词的笔记
    # queries = [
    #     "杭州 博物馆", 
    #     "杭州 音乐会 活动",
    #     "杭州 展览 活动",
    #     "杭州 读书会 活动",]
    # query_num = 10
    # sort_type_choice = 0  # 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
    # note_type = 2 # 0 不限, 1 视频笔记, 2 普通笔记
    # note_time = 2  # 0 不限, 1 一天内, 2 一周内天, 3 半年内
    # note_range = 2  # 0 不限, 1 已看过, 2 未看过, 3 已关注
    # pos_distance = 0  # 0 不限, 1 同城, 2 附近 指定这个1或2必须要指定 geo

    queries = [
        "杭州 饭店 地道 本地人",]
        # "杭州 必去 景点",]
    query_num = 10
    sort_type_choice = 0  # 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
    note_type = 2 # 0 不限, 1 视频笔记, 2 普通笔记
    note_time = 3  # 0 不限, 1 一天内, 2 一周内天, 3 半年内
    note_range = 0  # 0 不限, 1 已看过, 2 未看过, 3 已关注
    pos_distance = 0  # 0 不限, 1 同城, 2 附近 指定这个1或2必须要指定 geo
    # geo = {
    #     # 经纬度
    #     "latitude": 39.9725,
    #     "longitude": 116.4207
    # }
    # 使用默认存储选项
    for query in queries:
        await data_spider.spider_some_search_note(query, query_num, cookies_str, STORAGE_OPTIONS, sort_type_choice, note_type, note_time, note_range, pos_distance, geo=None)

if __name__ == '__main__':
    asyncio.run(main())

