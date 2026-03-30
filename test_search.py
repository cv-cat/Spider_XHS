#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试小红书搜索API
"""

import json
import os
import sys
from loguru import logger

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init

def test_search():
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    logger.info("=" * 60)
    logger.info("测试小红书搜索API")
    logger.info("=" * 60)

    # 初始化
    cookies_str, base_path = init()
    xhs_apis = XHS_Apis()

    # 测试搜索
    query = "漫剧"
    page = 1

    logger.info(f"\n测试搜索: {query}")

    try:
        # 调用search_note方法
        success, msg, res_json = xhs_apis.search_note(query, cookies_str, page)

        logger.info(f"Success: {success}")
        logger.info(f"Message: {msg}")
        logger.info(f"Response keys: {res_json.keys() if res_json else 'None'}")

        if res_json:
            logger.info(f"Response data: {json.dumps(res_json, indent=2, ensure_ascii=False)[:1000]}")

        return 0
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(test_search())
