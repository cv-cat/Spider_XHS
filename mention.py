from xhs_utils.xhs_util import *

class Mention:
    def __init__(self):
        self.headers = get_headers()
        self.cookies = check_cookies()
        self.params = {
            "num": "20",
            "cursor": ""
        }

    def get_all_mentions(self):
        has_more = True
        while has_more:
            api_base = "/api/sns/web/v1/you/mentions"
            # 拼接参数
            api = f"{api_base}?num={self.params['num']}&cursor={self.params['cursor']}"
            ret = js.call('get_xs', api, '', self.cookies['a1'])
            self.headers['x-s'], self.headers['x-t'] = ret['X-s'], str(ret['X-t'])
            url = "https://edith.xiaohongshu.com/api/sns/web/v1/you/mentions"
            response = requests.get(url, headers=self.headers, cookies=self.cookies, params=self.params)
            res = response.json()
            message = res['data']['message_list']
            has_more = res['data']['has_more']
            self.params['cursor'] = res['data']['cursor']
            for msg in message:
                print(f'内容 content: {msg["comment_info"]["content"]}')
                print(f'谁@的 user_id: {msg["user_info"]["userid"]}')
                print(f'@的谁 user_id: {msg["item_info"]["user_info"]["userid"]}')
                print(f'@的视频 id: {msg["item_info"]["id"]}')
                print(f'@我的时间 time: {msg["time"]}')
                print(
                    '-------------------------------------------------------------------------------------------------')

def main():
    mention = Mention()
    mention.get_all_mentions()

if __name__ == '__main__':
    main()
# {
#     "item_info": {
#         "type": "note_info",
#         "id": "65053aac000000001e02cfc3",
#         "image": "http://ci.xiaohongshu.com/1040g00830p2pl0kb46005o1gm6d085tr4b0n0s8?imageView2/2/w/1080/format/jpg",
#         "image_info": {
#             "url": "http://ci.xiaohongshu.com/1040g00830p2pl0kb46005o1gm6d085tr4b0n0s8?imageView2/2/w/1080/format/jpg",
#             "width": 1440,
#             "height": 2560
#         },
#         "illegal_info": {
#             "status": 0,
#             "desc": "",
#             "illegal_status": "NORMAL"
#         },
#         "link": "xhsdiscover://item/discovery.65053aac000000001e02cfc3?type=normal&sourceID=notifications&feedType=single&anchorCommentId=6513fe3e000000001a0102fe&authorId=6030b19a00000000010017bb",
#         "user_info": {
#             "userid": "6030b19a00000000010017bb",
#             "nickname": "越南网红胖大海。",
#             "image": "https://sns-avatar-qc.xhscdn.com/avatar/6492b81ad7ca2f223fb6a3ab.jpg?imageView2/2/w/120/format/jpg",
#             "red_official_verify_type": 0
#         },
#         "status": 0
#     },
#     "track_type": "8",
#     "id": "283977337",
#     "type": "mention/comment",
#     "title": "在评论中@了你",
#     "score": 283977337,
#     "user_info": {
#         "nickname": "tan90°",
#         "image": "https://sns-avatar-qc.xhscdn.com/avatar/62b587e00000000019029b80.jpg?imageView2/2/w/120/format/jpg",
#         "red_official_verify_type": 0,
#         "indicator": "你的好友",
#         "userid": "62b587e00000000019029b80"
#     },
#     "time": 1695809087,
#     "comment_info": {
#         "status": 0,
#         "liked": false,
#         "like_count": 0,
#         "id": "6513fe3e000000001a0102fe",
#         "content": "@誠",
#         "illegal_info": {
#             "desc": "",
#             "illegal_status": "NORMAL",
#             "status": 0
#         }
#     },
#     "liked": false,
#     "time_flag": 0
# },