import json
import time
import random

import requests
import qrcode
from loguru import logger

from apis.xhs_creator_apis import XHS_Creator_Apis
from xhs_utils.http_util import REQUEST_TIMEOUT
from xhs_utils.xhs_creator_util import generate_xsc, splice_str
from xhs_utils.common_util import generate_a1, generate_web_id, fetch_sec_cookies, fetch_gid


class XHSCreatorLoginApi:
    def __init__(self):
        self.customer_url = "https://customer.xiaohongshu.com"
        self.creator_url = "https://creator.xiaohongshu.com"

    def generate_init_cookies(self):
        ts = int(time.time() * 1000)
        a1 = generate_a1()
        web_id = generate_web_id(a1)
        cookies = {
            'ets': str(ts),
            'xsecappid': 'ugc',
            'loadts': str(ts + random.randint(50, 200)),
            'a1': a1,
            'webId': web_id,
        }
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'accept-language': 'zh-CN,zh;q=0.9',
        }
        resp = requests.get(
            self.creator_url + '/login',
            headers=headers,
            cookies=cookies,
            allow_redirects=False,
            timeout=REQUEST_TIMEOUT
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        req_headers = self._get_request_headers()

        sec_poison_id, websectiga = fetch_sec_cookies(cookies, req_headers)
        if sec_poison_id:
            cookies['sec_poison_id'] = sec_poison_id

        gid = fetch_gid(cookies, req_headers)
        if gid:
            cookies['gid'] = gid

        if websectiga:
            cookies['websectiga'] = websectiga

        return cookies

    @staticmethod
    def _get_request_headers():
        return {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'origin': 'https://creator.xiaohongshu.com',
            'referer': 'https://creator.xiaohongshu.com/',
            'authorization': '',
        }

    def generate_qrcode(self, cookies):
        api = '/api/cas/customer/web/qr-code'
        data = {"service": "https://creator.xiaohongshu.com"}

        headers = self._get_request_headers()
        headers['content-type'] = 'application/json'
        sign_h = generate_xsc(cookies['a1'], api, data)
        headers.update(sign_h)

        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        resp = requests.post(
            self.customer_url + api,
            headers=headers,
            cookies=cookies,
            data=data_str.encode('utf-8'),
            timeout=REQUEST_TIMEOUT
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        if not res.get('success'):
            return False, res.get('msg', '未知错误'), None

        return True, '成功', {
            'cookies': cookies,
            'qr_id': res['data']['id'],
            'qr_url': res['data']['url'],
        }

    def check_session(self, cookies):
        api = '/api/cas/customer/web/service-ticket'
        data = {"service": "https://creator.xiaohongshu.com", "source": "", "type": "tgt"}

        headers = self._get_request_headers()
        headers['content-type'] = 'application/json'
        sign_h = generate_xsc(cookies['a1'], api, data)
        headers.update(sign_h)

        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        resp = requests.post(
            self.customer_url + api,
            headers=headers,
            cookies=cookies,
            data=data_str.encode('utf-8'),
            timeout=REQUEST_TIMEOUT
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        has_session = res.get('data') is not None
        return has_session, cookies

    def check_qrcode_status(self, qr_id, cookies):
        api = '/api/cas/customer/web/qr-code'
        params = {
            'service': 'https://creator.xiaohongshu.com',
            'qr_code_id': qr_id,
            'source': ''
        }
        splice_api = splice_str(api, params)

        headers = self._get_request_headers()
        sign_h = generate_xsc(cookies['a1'], splice_api)
        headers.update(sign_h)

        resp = requests.get(
            self.customer_url + splice_api,
            headers=headers,
            cookies=cookies,
            timeout=REQUEST_TIMEOUT
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        status = res['data']['status']

        status_map = {
            1: (True, '验证成功'),
            2: (False, '请扫描二维码'),
            3: (False, '请确认登录'),
            -1: (False, '二维码已过期'),
        }
        success, msg = status_map.get(status, (False, f'未知状态: {status}'))
        return success, msg, cookies

    def get_user_info(self, cookies):
        api = '/api/galaxy/user/info'

        headers = self._get_request_headers()
        headers['sec-fetch-site'] = 'same-origin'
        sign_h = generate_xsc(cookies['a1'], api)
        headers.update(sign_h)

        resp = requests.get(
            self.creator_url + api,
            headers=headers,
            cookies=cookies,
            timeout=REQUEST_TIMEOUT
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        return res.get('success', False), res.get('data', {}), cookies

    def send_phone_code(self, phone, cookies, zone='86'):
        api = '/api/cas/customer/web/verify-code'
        data = {
            "service": "https://creator.xiaohongshu.com",
            "phone": phone,
            "zone": zone
        }

        headers = self._get_request_headers()
        headers['content-type'] = 'application/json'
        sign_h = generate_xsc(cookies['a1'], api, data)
        headers.update(sign_h)

        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        resp = requests.post(
            self.customer_url + api,
            headers=headers,
            cookies=cookies,
            data=data_str.encode('utf-8'),
            timeout=REQUEST_TIMEOUT
        )
        res = resp.json()
        return res.get('success', False), res.get('msg', ''), res

    def login_by_phone(self, phone, code, cookies, zone='86'):
        api = '/api/cas/customer/web/service-ticket'
        data = {
            "service": "https://creator.xiaohongshu.com",
            "zone": zone,
            "phone": phone,
            "verify_code": code,
            "source": "",
            "type": "phoneVerifyCode"
        }

        headers = self._get_request_headers()
        headers['content-type'] = 'application/json'
        sign_h = generate_xsc(cookies['a1'], api, data)
        headers.update(sign_h)

        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        resp = requests.post(
            self.customer_url + api,
            headers=headers,
            cookies=cookies,
            data=data_str.encode('utf-8'),
            timeout=REQUEST_TIMEOUT
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        return res.get('success', False), res.get('msg', ''), {
            'cookies': cookies,
            'res_json': res
        }

    @staticmethod
    def cookies_to_str(cookies):
        return '; '.join(f'{k}={v}' for k, v in cookies.items())

    @staticmethod
    def show_qrcode_terminal(url):
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)

    @staticmethod
    def show_qrcode_image(url):
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.show()

    def qrcode_login(self, show_in_terminal=True):
        logger.info('[1/4] 正在生成初始cookies...')
        cookies = self.generate_init_cookies()
        logger.info(f'a1={cookies["a1"]}')

        logger.info('[2/4] 正在获取二维码...')
        has_session, cookies = self.check_session(cookies)
        if has_session:
            logger.info('检测到已有会话，继续获取二维码...')

        success, msg, qr_data = self.generate_qrcode(cookies)
        if not success:
            logger.error(f'获取二维码失败: {msg}')
            return None
        cookies = qr_data['cookies']

        logger.info('请使用小红书APP扫描以下二维码:')
        if show_in_terminal:
            self.show_qrcode_terminal(qr_data['qr_url'])
        else:
            self.show_qrcode_image(qr_data['qr_url'])

        logger.info('[3/4] 等待扫码...')
        while True:
            success, msg, cookies = self.check_qrcode_status(qr_data['qr_id'], cookies)

            if success:
                logger.info(msg)
                break
            if msg == '二维码已过期':
                logger.error(msg)
                return None
            time.sleep(1)

        logger.info('[4/4] 验证登录状态...')
        success, user_info, cookies = self.get_user_info(cookies)
        if success:
            logger.info(f'用户: {user_info.get("userName", "未知")} (RedID: {user_info.get("redId", "未知")})')
        else:
            logger.warning('获取用户信息失败，但cookies可能仍有效')

        cookies_str = self.cookies_to_str(cookies)
        logger.success(f'登录成功!\ncookies:\n{cookies_str}')
        return cookies_str

    def phone_login(self):
        logger.info('[1/4] 正在生成初始cookies...')
        cookies = self.generate_init_cookies()
        logger.info(f'a1={cookies["a1"]}')

        phone = input('请输入手机号: ')
        logger.info('[2/4] 正在发送验证码...')
        success, msg, _ = self.send_phone_code(phone, cookies)
        if not success:
            logger.error(f'发送失败: {msg}')
            return None
        logger.info('验证码已发送')

        code = input('请输入验证码: ')
        logger.info('[3/4] 正在验证...')
        success, msg, result = self.login_by_phone(phone, code, cookies)
        if not success:
            logger.error(f'验证失败: {msg}')
            return None
        cookies = result['cookies']

        logger.info('[4/4] 验证登录状态...')
        success, user_info, cookies = self.get_user_info(cookies)
        if success:
            logger.info(f'用户: {user_info.get("userName", "未知")} (RedID: {user_info.get("redId", "未知")})')

        cookies_str = self.cookies_to_str(cookies)
        logger.success(f'登录成功!\ncookies:\n{cookies_str}')
        return cookies_str


if __name__ == '__main__':
    login_api = XHSCreatorLoginApi()
    # cookies_str = login_api.qrcode_login(show_in_terminal=True)
    cookies_str = login_api.phone_login()
    xhs_creator_apis = XHS_Creator_Apis()
    # 创作者平台 https://creator.xiaohongshu.com/login 的cookie
    noteInfos = [
        {
            # 标题
            "title": "222",
            # 描述
            "desc": "dwadaw最后一把直接神之一手直接立直后第一轮就胡牌了，最近吃点好的，哈哈",
            # 13位时间戳 数字类型
            "postTime": None,
            # 设置地点 "河海大学"
            "location": '南京',
            # 0:公开 1:私密
            "type": 1,
            "media_type": "image",
            # 设置话题
            # "topics": ["雀魂", "麻将"],
            "topics": [],
            # 图片路径 最多15张
            "images": [
                open(r"D:\Desktop\签名\QQ图片20240903150607.jpg", 'rb').read(),
            ],
        },
        {
            "title": "111",
            "desc": "dwadawd20240815",
            "postTime": None,
            "location": '河海大学',
            "topics": ["北京"],
            # "topics": [],
            "type": 1,
            "media_type": "video",
            "video": open(r"D:\Desktop\2026-04-28 13-24-20.mp4", 'rb').read(),
        }
    ]
    for noteInfo in noteInfos:
        success, msg, info = xhs_creator_apis.post_note(noteInfo, cookies_str)
        logger.debug(f'{success}, {msg}, {info}')
        logger.debug('========')
