#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义小红书搜索脚本
搜索"漫剧"和"AI仿真人剧"
"""

import json
import os
import sys
import time
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import handle_note_info

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class CustomXhsSearcher:
    def __init__(self):
        self.xhs_apis = XHS_Apis()
        self.results = []

    def search(self, query: str, require_num: int, cookies_str: str, proxies=None):
        """
        搜索关键词并返回笔记信息
        :param query: 搜索关键词
        :param require_num: 需要的笔记数量
        :param cookies_str: cookies字符串
        :param proxies: 代理设置
        :return: 笔记列表
        """
        try:
            # sort_type_choice: 0 综合, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            # note_type: 0 不限, 1 视频, 2 普通
            # note_time: 0 不限, 1 一天内, 2 一周内, 3 半年内
            sort_type_choice = 0
            note_type = 0
            note_time = 0
            note_range = 0
            pos_distance = 0

            logger.info(f'开始搜索: {query}, 数量: {require_num}')

            success, msg, notes = self.xhs_apis.search_some_note(
                query, require_num, cookies_str,
                sort_type_choice, note_type, note_time,
                note_range, pos_distance, geo=None, proxies=proxies
            )

            if success:
                # 过滤笔记类型
                notes = [note for note in notes if note.get('model_type') == 'note']

                logger.info(f'搜索成功，找到 {len(notes)} 条笔记')

                # 处理每条笔记
                for note in notes:
                    try:
                        note_info = handle_note_info(note)
                        note_info['query'] = query
                        note_info['platform'] = 'xiaohongshu'

                        # 添加URL
                        note_id = note.get('id', '')
                        xsec_token = note.get('xsec_token', '')
                        note_info['url'] = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"

                        self.results.append(note_info)

                        logger.info(f"  - {note_info['title'][:30]}... ({note_info['liked_count']} likes)")

                    except Exception as e:
                        logger.warning(f'处理笔记失败: {e}')
                        continue

                return notes
            else:
                logger.error(f'搜索失败: {msg}')
                return []

        except Exception as e:
            logger.error(f'搜索异常: {e}')
            return []

    def save_results(self, output_file: str):
        """保存搜索结果到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            logger.info(f'结果已保存到: {output_file}')
            return True
        except Exception as e:
            logger.error(f'保存结果失败: {e}')
            return False


def main():
    logger.remove()  # 移除默认处理器
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    logger.info("=" * 60)
    logger.info("小红书自定义搜索脚本")
    logger.info("=" * 60)

    # 初始化
    cookies_str, base_path = init()
    searcher = CustomXhsSearcher()

    # 搜索关键词
    queries = [
        ('漫剧', 50),
        ('AI仿真人剧', 50)
    ]

    all_results = []

    for query, num in queries:
        logger.info(f'\n搜索关键词: {query}')
        notes = searcher.search(query, num, cookies_str)
        all_results.extend(notes)

    # 保存结果
    if searcher.results:
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)

        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f'spider_xhs_results_{timestamp}.json')

        if searcher.save_results(output_file):
            logger.info(f'\n{"=" * 60}')
            logger.info(f'搜索完成！总共收集到 {len(searcher.results)} 条笔记')
            logger.info(f'结果文件: {output_file}')
            logger.info(f'{"=" * 60}')
            return 0
        else:
            logger.error('保存结果失败')
            return 1
    else:
        logger.error('没有搜索到任何笔记')
        return 1


if __name__ == '__main__':
    sys.exit(main())
