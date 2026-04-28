import os
import time
import random
import hashlib
import binascii
import json

import execjs
import requests
from loguru import logger
from dotenv import load_dotenv

from xhs_utils.http_util import REQUEST_TIMEOUT
from xhs_utils.xhs_creator_util import generate_xsc

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
_WEBSECTIGA_ENV_PATH = os.path.join(_STATIC_DIR, 'xhs_websectiga_env.js')

_A1_CHARSET = 'abcdefghijklmnopqrstuvwxyz1234567890'
_AS_URL = 'https://as.xiaohongshu.com'


def load_env():
    load_dotenv()
    cookies_str = os.getenv('COOKIES')
    return cookies_str


def init():
    media_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../datas/media_datas'))
    excel_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../datas/excel_datas'))
    for base_path in [media_base_path, excel_base_path]:
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            logger.info(f'创建目录 {base_path}')
    cookies_str = load_env()
    base_path = {
        'media': media_base_path,
        'excel': excel_base_path,
    }
    return cookies_str, base_path


def generate_a1():
    ts_hex = hex(int(time.time() * 1000))[2:]
    random_str = ''.join(random.choices(_A1_CHARSET, k=30))
    a_part = ts_hex + random_str + '5' + '0' + '000'
    crc = binascii.crc32(a_part.encode()) & 0xFFFFFFFF
    return (a_part + str(crc))[:52]


def generate_web_id(a1):
    return hashlib.md5(a1.encode()).hexdigest()


def _load_websectiga_env():
    try:
        return open(_WEBSECTIGA_ENV_PATH, 'r', encoding='utf-8').read()
    except FileNotFoundError:
        return None


def fetch_sec_cookies(cookies, headers):
    sec_poison_id = None
    websectiga = None

    api = '/api/sec/v1/scripting'
    data = {"callFrom": "web", "callback": "seccallback"}
    h = dict(headers)
    h['content-type'] = 'application/json;charset=UTF-8'
    sign_h = generate_xsc(cookies['a1'], api, data)
    h.update(sign_h)
    data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    try:
        resp = requests.post(
            _AS_URL + api,
            headers=h,
            cookies=cookies,
            data=data_str.encode('utf-8'),
            timeout=REQUEST_TIMEOUT
        )
        res = resp.json()
        sec_poison_id = res.get('data', {}).get('secPoisonId')
        jsvmp_code = res.get('data', {}).get('data', '')
        if jsvmp_code:
            env = _load_websectiga_env()
            if env:
                try:
                    js_code = env + '\n' + jsvmp_code + '\nvar __result = _websectiga_result;'
                    ctx = execjs.compile(js_code)
                    websectiga = ctx.eval('__result') or None
                except Exception as e:
                    logger.debug(f'websectiga jsvmp execution failed: {e}')
    except Exception as e:
        logger.debug(f'fetch sec cookies failed: {e}')
    return sec_poison_id, websectiga


def fetch_gid(cookies, headers):
    api = '/api/sec/v1/shield/webprofile'
    data = {
        "platform": "Windows",
        "sdkVersion": "4.3.5",
        "svn": "2",
        "profileData": ""
    }
    h = dict(headers)
    h['content-type'] = 'application/json'
    sign_h = generate_xsc(cookies['a1'], api, data)
    h.update(sign_h)
    data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    try:
        resp = requests.post(
            _AS_URL + api,
            headers=h,
            cookies=cookies,
            data=data_str.encode('utf-8'),
            timeout=REQUEST_TIMEOUT
        )
        for key, value in resp.cookies.items():
            cookies[key] = value
        if 'gid' in cookies:
            return cookies['gid']
    except Exception as e:
        logger.debug(f'fetch gid failed: {e}')
    return None
