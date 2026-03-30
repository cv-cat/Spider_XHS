#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试cookies和JS签名
"""

import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xhs_utils.common_util import load_env

cookies_str = load_env() or ''

print("=" * 60)
print("测试Cookies和JS签名")
print("=" * 60)

print(f"\nCookie字符串 (前200字符):")
print(cookies_str[:200])

try:
    from xhs_utils.cookie_util import trans_cookies

    cookies_dict = trans_cookies(cookies_str)

    print(f"\n转换后的Cookies字典:")
    for key, value in cookies_dict.items():
        print(f"  {key}: {value[:50]}...")

    # 检查a1
    if 'a1' in cookies_dict:
        print(f"\n✅ a1存在: {cookies_dict['a1'][:30]}...")
    else:
        print(f"\n❌ a1不存在！")

    # 测试JS签名生成
    print("\n测试JS签名生成...")
    from xhs_utils.xhs_util import generate_xs_xs_common

    a1 = cookies_dict.get('a1', '')
    api = "/api/sns/web/v1/search/notes"
    data = {"keyword": "漫剧"}

    try:
        xs, xt, xs_common = generate_xs_xs_common(a1, api, json.dumps(data, ensure_ascii=False), 'POST')

        print(f"✅ JS签名生成成功:")
        print(f"  X-s: {xs[:50]}...")
        print(f"  X-t: {xt if isinstance(xt, str) else xt}...")
        print(f"  X-s-common: {xs_common[:50]}...")

    except Exception as e:
        print(f"❌ JS签名生成失败: {e}")
        import traceback
        print(traceback.format_exc())

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    print(traceback.format_exc())
