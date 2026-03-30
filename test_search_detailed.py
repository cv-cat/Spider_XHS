#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细测试小红书搜索API
"""

import json
import os
import sys
import requests
from loguru import logger

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xhs_utils.cookie_util import trans_cookies
from xhs_utils.common_util import load_env
from xhs_utils.xhs_util import (
    generate_request_params,
    generate_x_b3_traceid,
    get_request_headers_template
)

def test_search_detailed():
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    logger.info("=" * 60)
    logger.info("详细测试小红书搜索API")
    logger.info("=" * 60)

    cookies_str = load_env() or ''

    # 转换cookies
    cookies_dict = trans_cookies(cookies_str)
    logger.info(f"\nCookies加载成功，共 {len(cookies_dict)} 个")
    logger.info(f"a1: {cookies_dict.get('a1', 'N/A')[:30]}...")

    # API参数
    api = "/api/sns/web/v1/search/notes"
    query = "漫剧"
    page = 1

    data = {
        "keyword": query,
        "page": page,
        "page_size": 20,
        "search_id": generate_x_b3_traceid(21),
        "sort": "general",
        "note_type": 0,
        "ext_flags": [],
        "filters": [
            {
                "tags": ["general"],
                "type": "sort_type"
            },
            {
                "tags": ["不限"],
                "type": "filter_note_type"
            },
            {
                "tags": ["不限"],
                "type": "filter_note_time"
            },
            {
                "tags": ["不限"],
                "type": "filter_note_range"
            },
            {
                "tags": ["不限"],
                "type": "filter_pos_distance"
            }
        ],
        "geo": "",
        "image_formats": ["jpg", "webp", "avif"]
    }

    logger.info(f"\nAPI: {api}")
    logger.info(f"Query: {query}")

    # 生成请求参数
    logger.info("\n生成请求参数...")
    try:
        headers, cookies, trans_data = generate_request_params(cookies_str, api, data, 'POST')

        logger.info("✅ 请求参数生成成功")
        logger.info(f"Headers (前500字符): {json.dumps(headers, indent=2)[:500]}")
        logger.info(f"Data (前500字符): {str(trans_data)[:500]}")

    except Exception as e:
        logger.error(f"❌ 请求参数生成失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

    # 发送请求
    base_url = "https://edith.xiaohongshu.com"
    logger.info(f"\n发送请求到: {base_url}{api}")

    try:
        response = requests.post(
            base_url + api,
            headers=headers,
            data=trans_data.encode('utf-8'),
            cookies=cookies
        )

        logger.info(f"响应状态码: {response.status_code}")

        # 检查响应
        if response.status_code == 200:
            try:
                res_json = response.json()
                logger.info("✅ JSON响应解析成功")
                logger.info(f"Response keys: {list(res_json.keys())}")

                if "success" in res_json:
                    success = res_json.get("success", False)
                    msg = res_json.get("msg", "")
                    logger.info(f"Success: {success}")
                    logger.info(f"Message: {msg}")

                    if success and "data" in res_json:
                        data = res_json["data"]
                        logger.info(f"Data keys: {list(data.keys())}")

                        if "items" in data:
                            items = data["items"]
                            logger.info(f"✅ 找到 {len(items)} 条笔记")

                            for i, item in enumerate(items[:3]):  # 只显示前3条
                                item_type = item.get("model_type", "unknown")
                                if item_type == "note":
                                    note_id = item.get("id", "unknown")
                                    logger.info(f"  [{i+1}] 笔记ID: {note_id}")
                                else:
                                    logger.info(f"  [{i+1}] 类型: {item_type}")
                        else:
                            logger.warning("⚠️  data中没有items字段")
                            logger.info(f"data内容: {json.dumps(data, indent=2)[:500]}")
                    else:
                        logger.warning("⚠️  API返回失败或无data字段")
                else:
                    logger.warning("⚠️  响应中没有success字段")
            except Exception as e:
                logger.error(f"❌ JSON解析失败: {e}")
                logger.info(f"响应内容 (前500字符): {response.text[:500]}")
        else:
            logger.error(f"❌ HTTP请求失败: {response.status_code}")
            logger.info(f"响应内容: {response.text[:500]}")

        return 0

    except Exception as e:
        logger.error(f"❌ 请求发送失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(test_search_detailed())
