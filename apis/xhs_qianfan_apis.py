import json
import requests
from xhs_utils.cookie_util import trans_cookies
from xhs_utils.xhs_qianfan_util import get_qianfan_headers_template, generate_qianfan_data, get_qianfan_userDetail_headers_template

class QianFanAPI:
    def get_all_categories(self, cookies):
        headers = get_qianfan_headers_template()
        url = "https://pgy.xiaohongshu.com/api/draco/distributor-square/distributors-tags"
        params = {
            "types": "content_category,distribution_category,user_design_tag,content_tag"
        }
        response = requests.get(url, headers=headers, cookies=cookies, params=params)
        distribution_category = response.json()["data"]['distributor_tag_map']["distribution_category"]
        return distribution_category

    def choose_categories(self, cookies):
        distribution_category = self.get_all_categories(cookies)
        for first_index, first_category_temp in enumerate(distribution_category):
            print(f'{first_index}: {first_category_temp["first_category"]}')
            for second_index, second_category_temp in enumerate(first_category_temp["second_category"]):
                print(f'---- {second_index}: {second_category_temp}')
        choice = input(
            "请选择您的类目：如果输入-1则为全部类目，输入1-2-4代表整个美妆/个护，服饰鞋包，母婴用品类目，输入1(1,3,4)-2代表美妆/个护类目下的1,3,4子类目和服饰鞋的全部\n")
        return choice, distribution_category

    def get_user_by_page(self, choice, distribution_category, page, cookies):
        headers = get_qianfan_headers_template()
        url = "https://pgy.xiaohongshu.com/api/draco/distributor-square/distributors"
        data = generate_qianfan_data(choice, distribution_category, page)
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        res_json = response.json()
        total = res_json["data"]["total"]
        user_list = res_json["data"]["list"]
        return user_list, total

    def get_some_user(self, choice, distribution_category, num, cookies):
        user_list = []
        page = 1
        while len(user_list) < num:
            user_list_temp, total = self.get_user_by_page(choice, distribution_category, page, cookies)
            user_list.extend(user_list_temp)
            page += 1
            if page > total / 20 + 1:
                break
        if len(user_list) > num:
            user_list = user_list[:num]
        return user_list

    def get_user_detail(self, user_id, cookies):
        headers = get_qianfan_userDetail_headers_template(user_id)
        url = "https://pgy.xiaohongshu.com/api/draco/distributor-square/distributor/detail/overview/v2"
        data = {
            "buyer_id": user_id,
            "date_type": 2
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        return response.json()

    def get_user_cooperation(self, user_id, cookies):
        headers = get_qianfan_userDetail_headers_template(user_id)
        url = "https://pgy.xiaohongshu.com/api/draco/distributor-square/distributor/cooperative/category/v2"
        data = {
            "buyer_id": user_id,
            "first_live_category": "",
            "second_live_category": "",
            "date_type": 2,
            "page": 1,
            "size": 10
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        return response.json()

    def get_user_shop(self, user_id, cookies):
        headers = get_qianfan_userDetail_headers_template(user_id)
        url = "https://pgy.xiaohongshu.com/api/draco/distributor-square/distributor/cooperative/shop/v2"
        data = {
            "buyer_id": "56509e0d9eb5782270a7b5ea",
            "first_live_category": "",
            "second_live_category": "",
            "date_type": 2,
            "page": 1,
            "size": 10
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        return response.json()

    def get_user_item(self, user_id, cookies):
        headers = get_qianfan_userDetail_headers_template(user_id)
        url = "https://pgy.xiaohongshu.com/api/draco/distributor-square/distributor/cooperative/item/v2"
        data = {
            "buyer_id": "56509e0d9eb5782270a7b5ea",
            "first_live_category": "",
            "second_live_category": "",
            "date_type": 2,
            "page": 1,
            "size": 10
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        return response.json()

    def get_user_fans(self, user_id, cookies):
        headers = get_qianfan_userDetail_headers_template(user_id)
        url = "https://pgy.xiaohongshu.com/api/draco/distributor-square/distribuitor/detail/fans"
        params = {
            "distributor_id": user_id,
            "date_type": "2"
        }
        response = requests.get(url, headers=headers, cookies=cookies, params=params)
        return response.json()

if __name__ == '__main__':
    qianfan_api = QianFanAPI()
    # https://pgy.xiaohongshu.com 的cookie
    cookies_str = ''
    cookies = trans_cookies(cookies_str)
    choice, distribution_category = qianfan_api.choose_categories(cookies)
    user_list = qianfan_api.get_some_user(choice, distribution_category, 10, cookies)
    for user in user_list:
        user_id = user["distributor_id"]
        user_detail = qianfan_api.get_user_detail(user_id, cookies)
        user_cooperation = qianfan_api.get_user_cooperation(user_id, cookies)
        user_shop = qianfan_api.get_user_shop(user_id, cookies)
        user_item = qianfan_api.get_user_item(user_id, cookies)
        user_fans = qianfan_api.get_user_fans(user_id, cookies)
        print(user)
        print(user_detail)
        print(user_cooperation)
        print(user_shop)
        print(user_item)
        print(user_fans)
        print(f'url: https://www.xiaohongshu.com/user/profile/{user_id}')
        print(f'qianfan_url: https://pgy.xiaohongshu.com/microapp/distribution/live-blogger-info/{user_id}?source=square')
