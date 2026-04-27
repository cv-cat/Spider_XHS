import json
import time
import random
import hashlib
import binascii
import os

import execjs
import requests
import qrcode

from xhs_utils.xhs_creator_util import generate_xsc, generate_xs, splice_str

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
_WEBSECTIGA_ENV_PATH = os.path.join(_STATIC_DIR, 'xhs_websectiga_env.js')


def _load_websectiga_env():
    try:
        return open(_WEBSECTIGA_ENV_PATH, 'r', encoding='utf-8').read()
    except FileNotFoundError:
        return None

CHARSET = 'abcdefghijklmnopqrstuvwxyz1234567890'


class XHSCreatorLoginApi:
    def __init__(self):
        self.customer_url = "https://customer.xiaohongshu.com"
        self.creator_url = "https://creator.xiaohongshu.com"
        self.as_url = "https://as.xiaohongshu.com"

    @staticmethod
    def _generate_a1():
        ts_hex = hex(int(time.time() * 1000))[2:]
        random_str = ''.join(random.choices(CHARSET, k=30))
        platform_code = '5'
        a_part = ts_hex + random_str + platform_code + '0' + '000'
        crc = binascii.crc32(a_part.encode()) & 0xFFFFFFFF
        return (a_part + str(crc))[:52]

    @staticmethod
    def _generate_web_id(a1):
        return hashlib.md5(a1.encode()).hexdigest()

    def _get_gid(self, cookies):
        api = '/api/sec/v1/shield/webprofile'
        data = {
            "platform": "Windows",
            "sdkVersion": "4.3.5",
            "svn": "2",
            "profileData": ""
        }
        headers = self._get_request_headers()
        headers['content-type'] = 'application/json'
        sign_h = generate_xsc(cookies['a1'], api, data)
        headers.update(sign_h)
        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        try:
            resp = requests.post(
                self.as_url + api,
                headers=headers,
                cookies=cookies,
                data=data_str.encode('utf-8')
            )
            for key, value in resp.cookies.items():
                cookies[key] = value
            if 'gid' in cookies:
                return cookies['gid']
        except Exception:
            pass
        return None

    def _get_websectiga(self, cookies):
        api = '/api/sec/v1/scripting'
        data = {"callFrom": "web", "callback": "seccallback"}
        headers = self._get_request_headers()
        headers['content-type'] = 'application/json;charset=UTF-8'
        sign_h = generate_xsc(cookies['a1'], api, data)
        headers.update(sign_h)
        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        sec_poison_id = None
        websectiga = None
        try:
            resp = requests.post(
                self.as_url + api,
                headers=headers,
                cookies=cookies,
                data=data_str.encode('utf-8')
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
                        websectiga = ctx.eval('__result')
                        if not websectiga:
                            websectiga = None
                    except Exception:
                        pass
        except Exception:
            pass
        return sec_poison_id, websectiga

    def generate_init_cookies(self):
        ts = int(time.time() * 1000)
        a1 = self._generate_a1()
        web_id = self._generate_web_id(a1)
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
            allow_redirects=False
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        sec_poison_id, websectiga = self._get_websectiga(cookies)
        if sec_poison_id:
            cookies['sec_poison_id'] = sec_poison_id

        gid = self._get_gid(cookies)
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
            data=data_str.encode('utf-8')
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

    def check_qrcode_status(self, qr_id, cookies):
        api = '/api/cas/customer/web/qr-code'
        params = {
            'service': 'https://creator.xiaohongshu.com',
            'qr_code_id': qr_id,
            'source': ''
        }
        splice_api = splice_str(api, params)

        headers = self._get_request_headers()
        sign_h = generate_xsc(cookies['a1'], api)
        headers.update(sign_h)

        resp = requests.get(
            self.customer_url + splice_api,
            headers=headers,
            cookies=cookies
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        status = res['data']['status']
        ticket = res['data'].get('ticket')

        status_map = {
            1: (True, '验证成功'),
            2: (False, '请扫描二维码'),
            3: (False, '请确认登录'),
            -1: (False, '二维码已过期'),
        }
        success, msg = status_map.get(status, (False, f'未知状态: {status}'))
        return success, msg, {'cookies': cookies, 'ticket': ticket}

    def login_step1(self, ticket, cookies):
        api = '/sso/customer_login'
        data = {
            "ticket": ticket,
            "login_service": "https://creator.xiaohongshu.com",
            "subsystem_alias": "creator",
            "set_global_domain": True
        }

        headers = self._get_request_headers()
        headers['content-type'] = 'application/json;charset=UTF-8'
        sign_h = generate_xsc(cookies['a1'], api, data)
        headers.update(sign_h)

        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        resp = requests.post(
            self.creator_url + api,
            headers=headers,
            cookies=cookies,
            data=data_str.encode('utf-8')
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        return res.get('success', False), res.get('msg', ''), {
            'cookies': cookies,
            'userInfo': res
        }

    def login_step2(self, cookies):
        api = '/api/galaxy/user/cas/login'

        headers = self._get_request_headers()
        sign_h = generate_xsc(cookies['a1'], api)
        headers.update(sign_h)

        resp = requests.post(
            self.creator_url + api,
            headers=headers,
            cookies=cookies
        )
        for key, value in resp.cookies.items():
            cookies[key] = value

        res = resp.json()
        return res.get('success', False), res.get('msg', ''), cookies

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
            data=data_str.encode('utf-8')
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
            data=data_str.encode('utf-8')
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
        print('[1/4] 正在生成初始cookies...')
        cookies = self.generate_init_cookies()
        print(f'  a1={cookies["a1"]}')

        print('[2/4] 正在获取二维码...')
        success, msg, qr_data = self.generate_qrcode(cookies)
        if not success:
            print(f'  失败: {msg}')
            return None
        cookies = qr_data['cookies']

        print('  请使用小红书APP扫描以下二维码:')
        if show_in_terminal:
            self.show_qrcode_terminal(qr_data['qr_url'])
        else:
            self.show_qrcode_image(qr_data['qr_url'])

        print('[3/4] 等待扫码...')
        while True:
            success, msg, result = self.check_qrcode_status(qr_data['qr_id'], cookies)
            cookies = result['cookies']

            if success:
                print(f'  {msg}')
                ticket = result['ticket']
                break
            if msg == '二维码已过期':
                print(f'  {msg}')
                return None
            time.sleep(3)

        print('[4/4] 正在完成登录...')
        if ticket:
            success, msg, result = self.login_step1(ticket, cookies)
            if not success:
                print(f'  step1失败: {msg}')
                return None
            cookies = result['cookies']

            success, msg, cookies = self.login_step2(cookies)
            if not success:
                print(f'  step2失败: {msg}')
                return None

        cookies_str = self.cookies_to_str(cookies)
        print(f'\n登录成功!\ncookies:\n{cookies_str}')
        return cookies_str

    def phone_login(self):
        print('[1/4] 正在生成初始cookies...')
        cookies = self.generate_init_cookies()
        print(f'  a1={cookies["a1"]}')

        phone = input('请输入手机号: ')
        print('[2/4] 正在发送验证码...')
        success, msg, _ = self.send_phone_code(phone, cookies)
        if not success:
            print(f'  发送失败: {msg}')
            return None
        print('  验证码已发送')

        code = input('请输入验证码: ')
        print('[3/4] 正在验证...')
        success, msg, result = self.login_by_phone(phone, code, cookies)
        if not success:
            print(f'  验证失败: {msg}')
            return None
        cookies = result['cookies']

        print('[4/4] 正在完成登录...')
        success, msg, cookies = self.login_step2(cookies)
        if not success:
            print(f'  登录失败: {msg}')
            return None

        cookies_str = self.cookies_to_str(cookies)
        print(f'\n登录成功!\ncookies:\n{cookies_str}')
        return cookies_str


if __name__ == '__main__':
    login_api = XHSCreatorLoginApi()
    login_api.qrcode_login(show_in_terminal=True)
