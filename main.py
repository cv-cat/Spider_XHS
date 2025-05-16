import os
from loguru import logger
from apis.pc_apis import XHS_Apis
from xhs_utils.common_utils import init
from xhs_utils.data_util import handle_note_info, download_note, save_to_xlsx, save_to_csv
from tqdm import tqdm
from time import sleep
from random import uniform

class Data_Spider():
    def __init__(self):
        self.xhs_apis = XHS_Apis()

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
        logger.info(f'爬取笔记信息 {note_url}: {success}')
        return success, msg, note_info

    def spider_some_note(self, notes: list, cookies_str: str, base_path: dict, save_choice: str, save_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes:
        :param cookies_str:
        :param base_path:
        :return:
        """
        from xhs_utils.xhs_util import sleep_random

        if (save_choice == 'all' or save_choice == 'excel' or save_choice == 'csv') and save_name == '':
            raise ValueError('save_name 不能为空')
        note_list = []
        for note_url in notes:
            sleep_random()
            success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
            if note_info is not None and success:
                note_list.append(note_info)
        for note_info in note_list:
            if save_choice == 'all' or save_choice == 'media':
                download_note(note_info, base_path['media'])

        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{save_name}.xlsx'))
            save_to_xlsx(note_list, file_path)
        elif save_choice == 'csv':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{save_name}.csv'))
            save_to_csv(note_list, file_path)

    def spider_user_all_note(self, user_url: str, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一个用户的所有笔记
        :param user_url:
        :param cookies_str:
        :param base_path:
        :return:
        """
        note_list = []
        try:
            success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, cookies_str, proxies, MAXIMUM_NOTES=60)
            if success:
                logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
                for simple_note_info in tqdm(all_note_info, desc='整理笔记链接'):
                    note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}"
                    note_list.append(note_url)
                    
            # 统一处理保存逻辑
            save_name = user_url.split('/')[-1].split('?')[0]
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, save_name, proxies)
            
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取用户所有视频 {user_url}: {success}, msg: {msg}')
        return note_list, success, msg

    def spider_some_search_note(self, query: str, require_num: int, cookies_str: str, base_path: dict, save_choice: str, sort="general", note_type=0,  excel_name: str = '', proxies=None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param base_path 保存路径
            :param sort 排序方式 general:综合排序, time_descending:时间排序, popularity_descending:热度排序
            :param note_type 笔记类型 0:全部, 1:视频, 2:图文
            返回搜索的结果
        """
        note_list = []
        try:
            success, msg, notes = self.xhs_apis.search_some_note(query, require_num, cookies_str, sort, note_type, proxies)
            if success:
                notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
                for note in notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = query
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return note_list, success, msg

if __name__ == '__main__':
    """
        此文件为爬虫的入口文件，可以直接运行
        apis/pc_apis.py 为爬虫的api文件，包含小红书的全部数据接口，可以继续封装，感谢star和follow
    """

    import time
    time.sleep(5)

    cookies_str, base_path = init()
    data_spider = Data_Spider()
    # save_choice: all: 保存所有的信息, media: 保存视频和图片, excel: 保存到excel
    # save_choice 为 excel 或者 all 时，excel_name 不能为空
    # 1
    notes = [
        r'https://www.xiaohongshu.com/explore/67d7c713000000000900e391?xsec_token=AB1ACxbo5cevHxV_bWibTmK8R1DDz0NnAW1PbFZLABXtE=&xsec_source=pc_user',
    ]
    # data_spider.spider_some_note(notes, cookies_str, base_path, 'all', 'test')

    # 2
    # user_url = 'https://www.xiaohongshu.com/user/profile/67a332a2000000000d008358?xsec_token=ABTf9yz4cLHhTycIlksF0jOi1yIZgfcaQ6IXNNGdKJ8xg=&xsec_source=pc_feed'
    # user_url = 'https://www.xiaohongshu.com/user/profile/5bb370f87d871100012f124a?xsec_token=ABWX915VCi8hbDizp6C0i0yW4X71s7dpUHYIYSIq7UCkY=&xsec_source=pc_feed'
    # user_url = 'https://www.xiaohongshu.com/user/profile/5a8cc0aa11be107fd08dffc5?xsec_token=ABYLB0P1M-TRuepgUcMvKoun4w-OobVbzPUDj69KLfFXc=&xsec_source=pc_feed'
    user_url = 'https://www.xiaohongshu.com/user/profile/64f57d7f00000000040240ab?xsec_token=AB72sECJPN4_Z985HpoOUggnYmuW-HcAuLCEthC32FZBs=&xsec_source=pc_note'
    data_spider.spider_user_all_note(user_url, cookies_str, base_path, 'csv')

    # 3
    # query = "榴莲"
    # query_num = 10
    # sort = "general"
    # note_type = 0
    # data_spider.spider_some_search_note(query, query_num, cookies_str, base_path, 'all', sort, note_type)
