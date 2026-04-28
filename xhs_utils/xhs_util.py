import json
import math
import os
import random
import time
from urllib.parse import urlencode

import execjs
from xhs_utils.cookie_util import trans_cookies

_STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))


def _compile_static_js(filename):
    with open(os.path.join(_STATIC_DIR, filename), 'r', encoding='utf-8') as f:
        return execjs.compile(f.read())


_JS_CACHE = {}


def _get_static_js(filename):
    if filename not in _JS_CACHE:
        _JS_CACHE[filename] = _compile_static_js(filename)
    return _JS_CACHE[filename]

def generate_x_b3_traceid(len=16):
    x_b3_traceid = ""
    for t in range(len):
        x_b3_traceid += "abcdef0123456789"[math.floor(16 * random.random())]
    return x_b3_traceid

_BASE36_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"

def _int_to_base36(value):
    if value == 0:
        return "0"
    result = ""
    while value:
        value, remainder = divmod(value, 36)
        result = _BASE36_CHARS[remainder] + result
    return result

def generate_search_id(root_search_id=None):
    if root_search_id:
        return root_search_id
    timestamp_ms = int(time.time() * 1000)
    random_part = math.ceil(0x7ffffffe * random.random())
    return _int_to_base36((timestamp_ms << 64) + random_part)

def generate_search_request_id():
    timestamp_ms = int(time.time() * 1000)
    random_part = math.ceil(0x7ffffffe * random.random())
    return f"{random_part}-{timestamp_ms}"

def generate_xs_xs_common(a1, api, data='', method='POST'):
    ret = _get_static_js('xhs_main_260411.js').call('get_request_headers_params', api, data, a1, method)
    xs, xt, xs_common = ret['xs'], ret['xt'], ret['xs_common']
    return xs, xt, xs_common

def generate_xs(a1, api, data=''):
    ret = _get_static_js('xhs_main_260411.js').call('get_xs', api, data, a1)
    xs, xt = ret['X-s'], ret['X-t']
    return xs, xt

def generate_xray_traceid():
    return _get_static_js('xhs_xray.js').call('traceId')

def generate_x_rap_param(api, data, app_id=None):
    if isinstance(data, (dict, list)):
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return _get_static_js('xhs_rap.js').call('generate_x_rap_param', api, data or '', app_id)

def get_common_headers():
    return {
        "authority": "www.xiaohongshu.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
def get_request_headers_template():
    return {
        "authority": "edith.xiaohongshu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.xiaohongshu.com",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "x-b3-traceid": "",
        "x-mns": "unload",
        "x-s": "",
        "x-s-common": "",
        "x-t": "",
        "x-xray-traceid": generate_xray_traceid()
    }

def generate_headers(a1, api, data='', method='POST'):
    xs, xt, xs_common = generate_xs_xs_common(a1, api, data, method)
    x_b3_traceid = generate_x_b3_traceid()
    headers = get_request_headers_template()
    headers['x-s'] = xs
    headers['x-t'] = str(xt)
    headers['x-s-common'] = xs_common
    headers['x-b3-traceid'] = x_b3_traceid
    if data:
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return headers, data

def generate_request_params(cookies_str, api, data='', method='POST'):
    cookies = trans_cookies(cookies_str)
    a1 = cookies['a1']
    headers, data = generate_headers(a1, api, data, method)
    return headers, cookies, data

def splice_str(api, params):
    return api + '?' + urlencode(
        {key: '' if value is None else value for key, value in params.items()},
        doseq=True
    )

if __name__ == '__main__':
    print(generate_search_id())
