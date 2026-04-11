import json
from threading import Thread

import aiohttp
import asyncio

import qrcode

from apis.xhs_creator_apis import XHS_Creator_Apis
from xhs_utils.xhs_creator_util import generate_xs, splice_str, get_common_headers
from playwright.async_api import async_playwright


class XHSLoginApi:
    def __init__(self):
        self.base_url = "https://customer.xiaohongshu.com"
        self.home_url = 'https://creator.xiaohongshu.com'

    # 生成初始cookies
    async def creatorCheckInitCookies(self, page):
        while True:
            cookies = dict()
            page_cookies = await page.context.cookies()
            for cookie in page_cookies:
                cookies[cookie['name']] = cookie['value']
            if "a1" in cookies and "xsecappid" in cookies and "webId" in cookies and "acw_tc" in cookies and "gid" in cookies and "websectiga" in cookies and "sec_poison_id" in cookies:
                break
            await asyncio.sleep(1)
        return cookies

    async def creatorGenerateInitCookies(self, headless=True):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ],
            )
            page = await browser.new_page()
            await page.goto(self.home_url + '/login')
            cookies = await self.creatorCheckInitCookies(page)
            await browser.close()
            return cookies

    # 手机验证码登录
    async def creatorGeneratePhoneCode(self, phone, cookies):
        res_json = None
        try:
            api = "/api/cas/customer/web/verify-code"
            data = {
                "service": "https://creator.xiaohongshu.com",
                "phone": phone,
                "zone": "86"
            }
            headers = get_common_headers()
            xs, xt, data = generate_xs(cookies['a1'], api, data)
            headers['x-s'], headers['x-t'] = xs, str(xt)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url + api, headers=headers, cookies=cookies, data=data) as response:
                    res_json = await response.json()
                    success, msg = res_json['success'], res_json['msg']
        except Exception as e:
            return False, str(e), res_json
        return success, msg, res_json

    async def creatorLoginByPhone(self, phone, code, cookies):
        res_json = None
        try:
            api = "/api/cas/customer/web/service-ticket"
            data = {
                "service": "https://creator.xiaohongshu.com",
                "zone": "86",
                "phone": phone,
                "verify_code": code,
                "source": "",
                "type": 'phoneVerifyCode'
            }
            headers = get_common_headers()
            xs, xt, data = generate_xs(cookies['a1'], api, data)
            headers['x-s'], headers['x-t'] = xs, str(xt)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url + api, headers=headers, cookies=cookies, data=data) as response:
                    res_json = await response.json()
                    success, msg = res_json['success'], res_json['msg']
                    add_cookies = dict()
                    return_cookies = response.cookies
                    for item in return_cookies.keys():
                        add_cookies[return_cookies[item].key] = return_cookies[item].value
                    cookies.update(add_cookies)
        except Exception as e:
            return False, str(e), res_json
        return success, msg, {
            "cookies": cookies,
            "res_json": res_json
        }

    # 二维码扫描登录
    async def creatorGenerateQRcode(self, cookies):
        try:
            api = '/api/cas/customer/web/qr-code'
            data = {
                "service": "https://creator.xiaohongshu.com"
            }
            headers = get_common_headers()
            xs, xt, data = generate_xs(cookies['a1'], api, data)
            headers['x-s'], headers['x-t'] = xs, str(xt)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url + api, headers=headers, cookies=cookies, data=data) as response:
                    res = await response.json()
                    qr_id, verify_url = res['data']['id'], res["data"]["url"]
                    success, msg = res['success'], res['msg']
        except Exception as e:
            return False, str(e), {
                "cookies": cookies,
                "qr_id": None,
                "verify_url": None
            }
        return success, msg, {
            "cookies": cookies,
            "qr_id": qr_id,
            "verify_url": verify_url
        }

    async def creatorCheckQRCodeLogin(self, qr_id, cookies):
        params = {
            "service": "https://creator.xiaohongshu.com",
            "qr_code_id": qr_id,
            "source": ""
        }
        ticket = None
        try:
            api = f"/api/cas/customer/web/qr-code"
            splice_api = splice_str(api, params)
            headers = get_common_headers()
            xs, xt, _ = generate_xs(cookies['a1'], api)
            headers['x-s'], headers['x-t'] = xs, str(xt)
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url + splice_api, headers=headers, cookies=cookies) as response:
                    res = await response.json()
                    success, msg = res['success'], res['msg']
                    code_status = res['data']['status']
                    if code_status == 1:
                        add_cookies = dict()
                        return_cookies = response.cookies
                        for item in return_cookies.keys():
                            add_cookies[return_cookies[item].key] = return_cookies[item].value
                        cookies.update(add_cookies)
                        ticket = res['data'].get('ticket', None)
                        msg = "验证成功"
                    elif code_status == 2:
                        msg = "请扫描二维码"
                    elif code_status == 3:
                        msg = "请确认登录"
                    elif code_status == -1:
                        msg = "验证码过期"
                        raise Exception(msg)
                    else:
                        msg = "未知错误"
                        raise Exception(msg)
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, {
            'cookies': cookies,
            'ticket': ticket
        }

    async def creatorLoginStep1(self, ticket, cookies):
        api = "/sso/customer_login"
        data = {
            "ticket": ticket,
            "login_service": "https://creator.xiaohongshu.com",
            "subsystem_alias": "creator",
            "set_global_domain": True
        }
        msg = '成功'
        try:
            headers = get_common_headers()
            xs, xt, data = generate_xs(cookies['a1'], api, data)
            headers['x-s'], headers['x-t'] = xs, str(xt)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.home_url + api, headers=headers, cookies=cookies, data=data) as response:
                    res = await response.json()
                    success = res['success']
                    add_cookies = dict()
                    return_cookies = response.cookies
                    for item in return_cookies.keys():
                        add_cookies[return_cookies[item].key] = return_cookies[item].value
                    cookies.update(add_cookies)
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, {
            'cookies': cookies,
            "userInfo": res
        }

    async def creatorLoginStep2(self, cookies):
        api = "/api/galaxy/user/cas/login"
        msg = '成功'
        try:
            headers = get_common_headers()
            xs, xt, _ = generate_xs(cookies['a1'], api)
            headers['x-s'], headers['x-t'] = xs, str(xt)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.home_url + api, headers=headers, cookies=cookies) as response:
                    res = await response.json()
                    success = res['success']
                    add_cookies = dict()
                    return_cookies = response.cookies
                    for item in return_cookies.keys():
                        add_cookies[return_cookies[item].key] = return_cookies[item].value
                    cookies.update(add_cookies)
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, cookies

    def transfer_cookies(self, cookies):
        cookies_str = ""
        for key, value in cookies.items():
            cookies_str += f"{key}={value}; "
        cookies_str = cookies_str[:-2]
        return cookies_str

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
        cookies = await self.creatorGenerateInitCookies()
        print('获取初始cookies')
        success, msg, qrcode_dict = await self.creatorGenerateQRcode(cookies)
        print('获取二维码', success, msg)
        print(qrcode_dict)
        qrcode_thread = Thread(target=self.generateQrcode, args=(qrcode_dict['verify_url'],))
        qrcode_thread.start()
        while True:
            success, msg, res = await self.creatorCheckQRCodeLogin(qrcode_dict['qr_id'], qrcode_dict['cookies'])
            print('检查二维码登录', success, msg)
            print(res)
            if msg == "验证成功":
                cookies = res['cookies']
                ticket = res['ticket']
                break
            await asyncio.sleep(10)

        if ticket is None:
            print('登录成功')
        else:
            print('需要ticket继续认证')
            success, msg, res = await self.creatorLoginStep1(ticket, cookies)
            print('ticket认证第一步', success, msg)
            print(res)
            cookies = res['cookies']
            userInfo = res['userInfo']
            success, msg, cookies = await self.creatorLoginStep2(cookies)
            print('ticket认证第二步', success, msg)
            print(cookies)
            print('登录成功')
        cookies_str = self.transfer_cookies(cookies)
        print(f'cookies_str: {cookies_str}')

    async def phoneMain(self):
        cookies = await self.creatorGenerateInitCookies()
        print('获取初始cookies')
        phone_num = ""
        phone_num = ""
        success, msg, res_json = await self.creatorGeneratePhoneCode(phone_num, cookies)
        print('获取手机验证码', success, msg, res_json)
        code = input("请输入验证码：")
        success, msg, res_json = await self.creatorLoginByPhone(phone_num, code, cookies)
        print('手机验证码登录', success, msg, res_json)
        cookies = res_json['cookies']
        cookies_str = self.transfer_cookies(cookies)
        print(f'cookies_str: {cookies_str}')
        self.test(cookies_str)

    def test(self, cookies_str):
        xhs_creator_apis = XHS_Creator_Apis()
        noteInfos = [
            {
                # 标题
                "title": "我是笨蛋",
                # 描述
                "desc": "我",
                # 13位时间戳 数字类型
                "postTime": None,
                # 设置地点 "河海大学"
                "location": None,
                # 0:公开 1:私密
                "type": 1,
                "topics": ["测试"],
                "media_type": "image",
                # 图片路径 最多15张
                "images": [
                    open(r"D:\Desktop\Data\images\temp\22.jpg", 'rb').read(),
                    open(r"D:\Desktop\Data\images\temp\22.jpg", 'rb').read(),
                ],
            },
        ]
        for noteInfo in noteInfos:
            success, msg, info = xhs_creator_apis.post_note(noteInfo, cookies_str)
            print(success, msg, info)
            print('========')


if __name__ == '__main__':
    login_util = XHSLoginApi()
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(login_util.qrcodeMain())
    loop.run_until_complete(login_util.phoneMain())
