import json
from threading import Thread

import aiohttp
import asyncio

import qrcode

from xhs_utils.xhs_util import generate_headers, splice_str
from playwright.async_api import async_playwright


class XHSLoginApi:
    def __init__(self):
        self.base_url = "https://edith.xiaohongshu.com"
        self.home_url = 'https://www.xiaohongshu.com/explore'
        self.generate_qrcode_api = '/api/sns/web/v1/login/qrcode/create'

    # 生成初始cookies
    async def xhsCheckInitCookies(self, page):
        while True:
            cookies = dict()
            page_cookies = await page.context.cookies()
            for cookie in page_cookies:
                cookies[cookie['name']] = cookie['value']
            if "webId" in cookies and "a1" in cookies and "gid" in cookies:
                break
            await asyncio.sleep(1)
        if 'web_session' in cookies:
            del cookies['web_session']
        return cookies

    async def xhsGenerateInitCookies(self, headless=True):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ],
            )
            page = await browser.new_page()
            await page.goto(self.home_url)
            cookies = await self.xhsCheckInitCookies(page)
            await browser.close()
            return cookies

    # 手机验证码登录
    async def xhsGeneratePhoneVerificationCode(self, phone_num, cookies):
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
                    print(res)
                    success, msg = res['success'], res['msg']
        except Exception as e:
            success, msg = False, str(e)
        return success, msg

    async def xhsCheckPhoneVerificationCode(self, phone_num, code, cookies):
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

    async def xhsPhoneVerificationCodeLogin(self, mobile_token, phone, cookies):
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
                    cookies_str = ''
                    for key in cookies:
                        cookies_str += f'{key}={cookies[key]}; '
                    cookies_str = cookies_str[:-2]
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, cookies_str

    # 二维码扫描登录
    async def xhsGenerateQRcode(self, cookies):
        try:
            data = {
                "qr_type": 1
            }
            headers, data = generate_headers(cookies['a1'], self.generate_qrcode_api, data)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url + self.generate_qrcode_api, headers=headers, cookies=cookies, data=data) as response:
                    res = await response.json()
                    qr_id, code, verify_url = res['data']['qr_id'], res['data']['code'], res["data"]["url"]
                    success, msg = res['success'], res['msg']
        except Exception as e:
            return False, str(e), {
                "cookies": cookies,
                "qr_id": None,
                "code": None,
                "verify_url": None
            }
        return success, msg, {
            "cookies": cookies,
            "qr_id": qr_id,
            "code": code,
            "verify_url": verify_url
        }

    async def xhsCheckQRCodeLogin(self, qr_id, code, cookies):
        cookies_str = None
        try:
            check_api = f"/api/sns/web/v1/login/qrcode/status?qr_id={qr_id}&code={code}"
            headers, _ = generate_headers(cookies['a1'], check_api)
            headers['x-login-mode'] = ""
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url + check_api, headers=headers, cookies=cookies) as response:
                    res = await response.json()
                    success, msg = res['success'], res['msg']
                    code_status = res['data']['code_status']
                    if code_status == 0:
                        msg = "请扫描二维码"
                    elif code_status == 1:
                        msg = "请确认登录"
                    elif code_status == 2:
                        cookies['web_session'] = res['data']['login_info']['session']
                        cookies_str = ''
                        for key in cookies:
                            cookies_str += f'{key}={cookies[key]}; '
                        cookies_str = cookies_str[:-2]
                    elif code_status == 3:
                        msg = "二维码已失效"
                        raise Exception(msg)
                    else:
                        msg = "未知code_status"
                        raise Exception(msg)
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, {
            'cookies_str': cookies_str,
            'res': res
        }
    def generateQrcode(self, verify_url):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.show()

    async def qrcodeMain(self):
        cookies = await self.xhsGenerateInitCookies()
        success, msg, qrcode_dict = await self.xhsGenerateQRcode(cookies)
        qrcode_thread = Thread(target=self.generateQrcode, args=(qrcode_dict['verify_url'],))
        qrcode_thread.start()
        # asyncio.create_task(asyncio.to_thread(self.generateQrcode, qrcode_dict['verify_url']))
        while True:
            success, msg, res = await self.xhsCheckQRCodeLogin(qrcode_dict['qr_id'], qrcode_dict['code'], qrcode_dict['cookies'])
            print(success, msg, res)
            print(res['cookies_str'])
            await asyncio.sleep(1)

    async def phoneMain(self):
        cookies = await self.xhsGenerateInitCookies()
        phone_num = ""
        success, msg = await self.xhsGeneratePhoneVerificationCode(phone_num, cookies)
        print(success, msg)
        code = input("请输入验证码：")
        success, msg, mobile_token = await self.xhsCheckPhoneVerificationCode(phone_num, code, cookies)
        print(success, msg, mobile_token)
        success, msg, cookies_str = await self.xhsPhoneVerificationCodeLogin(mobile_token, phone_num, cookies)
        print(success, msg, cookies_str)

if __name__ == '__main__':
    login_util = XHSLoginApi()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(login_util.qrcodeMain())
    # loop.run_until_complete(login_util.phoneMain())