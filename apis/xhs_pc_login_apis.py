import json
import time
import random
import uuid

import aiohttp
import asyncio
import requests

import qrcode
from loguru import logger

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.xhs_util import generate_headers, generate_xs_xs_common, splice_str
from xhs_utils.common_util import generate_a1, generate_web_id


class XHSLoginApi:
    def __init__(self):
        self.base_url = "https://edith.xiaohongshu.com"
        self.as_url = "https://as.xiaohongshu.com"
        self.home_url = 'https://www.xiaohongshu.com/explore'
        self.generate_qrcode_api = '/api/sns/web/v1/login/qrcode/create'
        self.check_qrcode_api = '/api/qrcode/userinfo'

    # 生成初始cookies
    @staticmethod
    def _get_sec_headers():
        return {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json;charset=UTF-8',
            'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'origin': 'https://www.xiaohongshu.com',
            'referer': 'https://www.xiaohongshu.com/',
        }

    def _fetch_sec_cookies(self, cookies):
        api = '/api/sec/v1/scripting'
        data = {"callFrom": "web", "callback": "", "type": "ds", "appId": "xhs-pc-web"}

        xs, xt, xs_common = generate_xs_xs_common(cookies['a1'], api, data)
        headers = self._get_sec_headers()
        headers['x-s'] = xs
        headers['x-t'] = str(xt)
        headers['x-s-common'] = xs_common

        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        try:
            resp = requests.post(
                self.as_url + api,
                headers=headers, cookies=cookies,
                data=data_str.encode('utf-8')
            )
            res = resp.json()
            return res.get('data', {}).get('secPoisonId')
        except Exception:
            return None

    def _fetch_gid(self, cookies):
        api = '/api/sec/v1/shield/webprofile'
        data = {"platform": "Windows", "sdkVersion": "4.3.5", "svn": "2", "profileData": ""}

        xs, xt, xs_common = generate_xs_xs_common(cookies['a1'], api, data)
        headers = self._get_sec_headers()
        headers['x-s'] = xs
        headers['x-t'] = str(xt)
        headers['x-s-common'] = xs_common

        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        try:
            resp = requests.post(
                self.as_url + api,
                headers=headers, cookies=cookies,
                data=data_str.encode('utf-8')
            )
            for key, value in resp.cookies.items():
                cookies[key] = value
            return cookies.get('gid')
        except Exception:
            return None

    def generate_init_cookies(self):
        ts = int(time.time() * 1000)
        a1 = generate_a1()
        web_id = generate_web_id(a1)
        cookies = {
            'abRequestId': str(uuid.uuid4()),
            'ets': str(ts),
            'webBuild': '6.7.4',
            'xsecappid': 'xhs-pc-web',
            'loadts': str(ts + random.randint(50, 200)),
            'a1': a1,
            'webId': web_id,
        }

        sec_poison_id = self._fetch_sec_cookies(cookies)
        if sec_poison_id:
            cookies['sec_poison_id'] = sec_poison_id

        gid = self._fetch_gid(cookies)
        if gid:
            cookies['gid'] = gid

        return cookies

    # 手机验证码登录
    async def send_phone_code(self, phone_num, cookies):
        try:
            api = "/api/sns/web/v2/login/send_code"
            params = {
                "phone": phone_num,
                "zone": "86",
                "type": "login"
            }
            splice_api = splice_str(api, params)
            headers, _ = generate_headers(cookies['a1'], splice_api)
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url + splice_api, headers=headers, cookies=cookies) as response:
                    res = await response.json()
                    logger.debug(res)
                    success, msg = res['success'], res['msg']
        except Exception as e:
            success, msg = False, str(e)
        return success, msg

    async def check_phone_code(self, phone_num, code, cookies):
        mobile_token = None
        try:
            api = "/api/sns/web/v1/login/check_code"
            params = {
                "phone": phone_num,
                "zone": "86",
                "code": code
            }
            splice_api = splice_str(api, params)
            headers, _ = generate_headers(cookies['a1'], splice_api)
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url + splice_api, headers=headers, cookies=cookies) as response:
                    res = await response.json()
                    success, msg = res['success'], res['msg']
                    mobile_token = res['data']['mobile_token']
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, mobile_token

    async def login_by_phone(self, mobile_token, phone, cookies):
        cookies_str = None
        try:
            api = "/api/sns/web/v2/login/code"
            data = {
                "mobile_token": mobile_token,
                "zone": "86",
                "phone": phone
            }
            headers, data = generate_headers(cookies['a1'], api, data)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url + api, headers=headers, cookies=cookies, data=data) as response:
                    res = await response.json()
                    success, msg = res['success'], res['msg']
                    cookies['web_session'] = res['data']['session']
                    cookies_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, cookies_str

    # 二维码扫描登录
    def generate_qrcode(self, cookies):
        try:
            data = {"qr_type": 1}
            headers, data = generate_headers(cookies['a1'], self.generate_qrcode_api, data)
            response = requests.post(
                self.base_url + self.generate_qrcode_api,
                headers=headers, cookies=cookies, data=data
            )
            res = response.json()
            qr_id, code, verify_url = res['data']['qr_id'], res['data']['code'], res["data"]["url"]
            success, msg = res['success'], res['msg']
        except Exception as e:
            return False, str(e), None
        return success, msg, {
            "cookies": cookies,
            "qr_id": qr_id,
            "code": code,
            "verify_url": verify_url
        }

    def check_qrcode_status(self, qr_id, code, cookies):
        code_status = -1
        try:
            data = {"qrId": qr_id, "code": code}
            headers, data = generate_headers(cookies['a1'], self.check_qrcode_api, data)
            response = requests.post(
                self.base_url + self.check_qrcode_api,
                headers=headers, cookies=cookies, data=data
            )
            res = response.json()
            code_status = res['data']['codeStatus']
            if code_status == 2:
                if 'web_session' in response.cookies:
                    cookies['web_session'] = response.cookies['web_session']
                elif 'loginInfo' in res.get('data', {}):
                    cookies['web_session'] = res['data']['loginInfo']['session']
        except Exception as e:
            logger.error(f'轮询异常: {e}')

        status_map = {
            0: (False, '请扫描二维码'),
            1: (False, '请确认登录'),
            2: (True, '验证成功'),
            3: (False, '二维码已过期'),
        }
        success, msg = status_map.get(code_status, (False, f'未知codeStatus: {code_status}'))
        return success, msg, cookies

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
        logger.info('[1/3] 正在生成初始cookies...')
        cookies = self.generate_init_cookies()
        logger.info(f'a1={cookies["a1"]}')

        logger.info('[2/3] 正在获取二维码...')
        success, msg, qr_data = self.generate_qrcode(cookies)
        if not success:
            logger.error(f'获取二维码失败: {msg}')
            return None
        cookies = qr_data['cookies']

        logger.info('请使用小红书APP扫描以下二维码:')
        if show_in_terminal:
            self.show_qrcode_terminal(qr_data['verify_url'])
        else:
            self.show_qrcode_image(qr_data['verify_url'])

        logger.info('[3/3] 等待扫码...')
        while True:
            success, msg, cookies = self.check_qrcode_status(
                qr_data['qr_id'], qr_data['code'], cookies
            )
            if success:
                logger.info(msg)
                break
            if msg == '二维码已过期':
                logger.error(msg)
                return None
            time.sleep(2)

        cookies_str = self.cookies_to_str(cookies)
        logger.success(f'登录成功!\ncookies:\n{cookies_str}')
        return cookies_str

    async def phone_login(self):
        cookies = self.generate_init_cookies()
        phone_num = input("请输入手机号：")

        logger.info('正在发送验证码...')
        success, msg = await self.send_phone_code(phone_num, cookies)
        if not success:
            logger.error(f'发送失败: {msg}')
            return None
        logger.info('验证码已发送')

        code = input("请输入验证码：")
        success, msg, mobile_token = await self.check_phone_code(phone_num, code, cookies)
        if not success:
            logger.error(f'验证失败: {msg}')
            return None

        success, msg, cookies_str = await self.login_by_phone(mobile_token, phone_num, cookies)
        if not success:
            logger.error(f'登录失败: {msg}')
            return None

        logger.success(f'登录成功!\ncookies:\n{cookies_str}')
        return cookies_str


if __name__ == '__main__':
    login_api = XHSLoginApi()
    cookies_str = login_api.qrcode_login(show_in_terminal=True)
    xhs_apis = XHS_Apis()
    # 获取用户信息
    user_url = 'https://www.xiaohongshu.com/user/profile/67a332a2000000000d008358?xsec_token=ABTf9yz4cLHhTycIlksF0jOi1yIZgfcaQ6IXNNGdKJ8xg=&xsec_source=pc_feed'
    success, msg, user_info = xhs_apis.get_user_info('67a332a2000000000d008358', cookies_str)
    logger.info(f'获取用户信息结果 {json.dumps(user_info, ensure_ascii=False)}: {success}, msg: {msg}')
