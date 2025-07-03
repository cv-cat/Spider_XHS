import json
import os
import time

from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import handle_note_info,handle_comment_info,handle_comment_info_sub, download_note, download_note_index, save_to_xlsx


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
        logger.info(f'爬取笔记信息 {note_url}: {success}, msg: {msg}')
        return success, msg, note_info

    def spider_comment(self, note_url: str, cookies_str: str, proxies=None):
        """
        爬取一个笔记的信息
        :param note_url:
        :param cookies_str:
        :return:
        """
        comment_note = None
        comment_display = ''
        try:
            success, msg, note_all_comment = self.xhs_apis.get_note_all_comment(note_url, cookies_str)
            logger.info(f'获取笔记评论结果 {json.dumps(note_all_comment, ensure_ascii=False)}: {success}, msg: {msg}')
            if success:
                comment_note, comment_display = handle_comment_info_sub(note_all_comment)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取笔记信息 {note_url}: {success}, msg: {msg}')
        return success, msg, comment_note, comment_display

    def spider_some_note(self, notes: list, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes:
        :param cookies_str:
        :param base_path:
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        if save_choice == 'content' and excel_name != '':
            content_name = excel_name
        note_list = []
        for note_url in notes:
            success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
            if note_info is not None and success:
                note_list.append(note_info)
        for note_info in note_list:
            if save_choice == 'all' or 'media' in save_choice:
                download_note(note_info, base_path['media'], save_choice)
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(note_list, file_path)

    def spider_some_note_by_download(self, notes: list, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes:
        :param cookies_str:
        :param base_path:
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        if save_choice == 'content' and excel_name != '':
            content_name = excel_name
        note_list = []
        index = 0
        for note_url in notes:
            index += 1
            try:
                # Add delay between requests to avoid being blocked
                time.sleep(4)  # 1 second delay, adjust as needed

                success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
                time.sleep(4)  # 4 second delay, adjust as needed
                success, msg, comment_note, comment_display = self.spider_comment(note_url, cookies_str, proxies)
                if note_info is not None and success:
                    info = f'第{index}个笔记, '
                    note_list.append(note_info)
                    try:
                        if save_choice == 'all' or 'media' in save_choice:
                            download_note_index(note_info, base_path['media'], save_choice,comment_note, comment_display, info, index)
                    except Exception as e:
                        print(f"Error downloading media for note {index}: {str(e)}")

                    try:
                        if save_choice == 'all' or save_choice == 'content' or 'content' in save_choice:
                            download_note_index(note_info, base_path['content'], save_choice, info, index)
                    except Exception as e:
                        print(f"Error downloading content for note {index}: {str(e)}")

            except Exception as e:
                print(f"Error processing note {index} ({note_url}): {str(e)}")
                continue  # Continue to next note even if this one fails

            if save_choice == 'all' or save_choice == 'excel':
                try:
                    file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
                    save_to_xlsx(note_list, file_path)
                except Exception as e:
                    print(f"Error saving to Excel: {str(e)}")


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
            success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, cookies_str, proxies)
            if success:
                logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
                for simple_note_info in all_note_info:
                    note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel' or save_choice == 'content':
                excel_name = user_url.split('/')[-1].split('?')[0]
            self.spider_some_note_by_download(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取用户所有视频 {user_url}: {success}, msg: {msg}')
        return note_list, success, msg

    def spider_some_search_note(self, query: str, require_num: int, cookies_str: str, base_path: dict, save_choice: str, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo: dict = None,  excel_name: str = '', proxies=None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param base_path 保存路径
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            返回搜索的结果
        """
        note_list = []
        try:
            success, msg, notes = self.xhs_apis.search_some_note(query, require_num, cookies_str, sort_type_choice, note_type, note_time, note_range, pos_distance, geo, proxies)
            if success:
                notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
                for note in notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = query
            self.spider_some_note_by_download(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return note_list, success, msg

    def userHome(self, url_list, cookies_str: str, base_path: dict, save_choice: str,):
        # url_list = [
        #     'https://www.xiaohongshu.com/user/profile/6185ce66000000001000705b',
        #     'https://www.xiaohongshu.com/user/profile/6034d6f20000000001006fbb',
        # ]
        for user_url in url_list:
            try:
                self.spider_user_all_note(user_url, cookies_str, base_path, 'content')
            except:
                print(f'用户 {user_url} 查询失败')

if __name__ == '__main__':
    """
        此文件为爬虫的入口文件，可以直接运行
        apis/xhs_pc_apis.py 为爬虫的api文件，包含小红书的全部数据接口，可以继续封装
        apis/xhs_creator_apis.py 为小红书创作者中心的api文件
        感谢star和follow
    """

    cookies_str, base_path = init()
    data_spider = Data_Spider()
    """
        save_choice: all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
        save_choice 为 excel 或者 all 时，excel_name 不能为空
        save_choice 为 content时，就是文件夹 保存方式
    """


    # 1 爬取列表的所有笔记信息 笔记链接 如下所示 注意此url会过期！
    # notes = [
    #     r'https://www.xiaohongshu.com/explore/683fe17f0000000023017c6a?xsec_token=ABBr_cMzallQeLyKSRdPk9fwzA0torkbT_ubuQP1ayvKA=&xsec_source=pc_user',
    # ]
    # data_spider.spider_some_note_by_download(notes, cookies_str, base_path, 'all', 'test')

    # 2 爬取用户的所有笔记信息 用户链接 如下所示 注意此url会过期！
    user_url_list = [
        # 'https://www.xiaohongshu.com/user/profile/64c3f392000000002b009e45?xsec_token=AB-GhAToFu07JwNk_AMICHnp7bSTjVz2beVIDBwSyPwvM=&xsec_source=pc_feed',
                     'https://www.xiaohongshu.com/user/profile/658fbc1e0000000022012d90?xsec_token=AB3KOmCoVMCHstjRwG4RbwmUq_K0qE4vqQOo3ke2FLlDM%3D&xsec_source=pc_search',]
    data_spider.userHome(user_url_list, cookies_str, base_path, 'content')

    # # 3 搜索指定关键词的笔记
    # query = "榴莲"
    # query_num = 10
    # sort_type_choice = 0  # 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
    # note_type = 0 # 0 不限, 1 视频笔记, 2 普通笔记
    # note_time = 0  # 0 不限, 1 一天内, 2 一周内天, 3 半年内
    # note_range = 0  # 0 不限, 1 已看过, 2 未看过, 3 已关注
    # pos_distance = 0  # 0 不限, 1 同城, 2 附近 指定这个1或2必须要指定 geo
    # # geo = {
    # #     # 经纬度
    # #     "latitude": 39.9725,
    # #     "longitude": 116.4207
    # # }
    # data_spider.spider_some_search_note(query, query_num, cookies_str, base_path, 'all', sort_type_choice, note_type, note_time, note_range, pos_distance, geo=None)
