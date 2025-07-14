import requests
from xhs_utils.cookie_util import trans_cookies
from xhs_utils.xhs_creator_util import get_common_headers, generate_xs, splice_str
from xhs_utils.xhs_util import generate_x_b3_traceid


class XHS_Creator_Apis():
    def __init__(self):
        self.base_url = "https://edith.xiaohongshu.com"


    # page: 页数
    # time: 最近几天的时间
    def get_publish_note_info(self, page, cookies_str):
        success = False
        msg = '成功'
        res_json = None

        try:
            api = "/web_api/sns/v5/creator/note/user/posted"
            params = {
                "tab": '0',
            }
            if page >= 0:
                params["page"] = str(page)
            splice_api = splice_str(api, params)
            headers = get_common_headers()
            cookies = trans_cookies(cookies_str)
            xs, xt, _ = generate_xs(cookies['a1'], splice_api, '')
            headers['x-s'], headers['x-t'] = xs, str(xt)
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, verify=False)
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
