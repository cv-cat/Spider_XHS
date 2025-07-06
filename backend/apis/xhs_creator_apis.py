import requests
from xhs_utils.cookie_util import trans_cookies
from xhs_utils.xhs_creator_util import get_common_headers, generate_xs
from xhs_utils.xhs_util import generate_x_b3_traceid


class XHS_Creator_Apis():
    def __init__(self):
        self.base_url = "https://creator.xiaohongshu.com"


    # page: 页数
    # time: 最近几天的时间
    def get_publish_note_info(self, page, cookies_str):
        success = False
        msg = '成功'
        res_json = None
        try:
            api = "/api/galaxy/creator/note/user/posted"
            headers = get_common_headers()
            cookies = trans_cookies(cookies_str)
            xs, xt, _ = generate_xs(cookies['a1'], api, '')
            headers['x-s'], headers['x-t'] = xs, str(xt)
            headers['x-b3-traceid'] = generate_x_b3_traceid()
            params = {
                "tab": '0',
            }
            if page:
                params["page"] = str(page)
            response = requests.get(self.base_url + api, headers=headers, cookies=cookies, params=params)
            res_json = response.json()
            success = res_json["success"]
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, res_json


    # 获取全部的发布信息
    def get_all_publish_note_info(self, cookies_str):
        page = None
        notes = []
        while True:
            success, msg, res_json = self.get_publish_note_info(page, cookies_str)
            print(success, msg, res_json)
            if not success:
                return False, msg, notes
            notes += res_json['data']['notes']
            page = res_json['data']['page']
            if page == -1:
                break
        return True, '成功', notes


if __name__ == '__main__':
    xhs_creator_apis = XHS_Creator_Apis()
