import json
from one import OneNote
from xhs_utils.xhs_util import *

class Search:
    def __init__(self):
        self.search_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
        self.headers = get_headers()
        self.params = get_params()
        self.oneNote = OneNote()
        self.cookies = self.oneNote.cookies

    def get_search_note(self, query, number):
        data = get_search_data()
        api = '/api/sns/web/v1/search/notes'
        data = json.dumps(data, separators=(',', ':'))
        data = re.sub(r'"keyword":".*?"', f'"keyword":"{query}"', data)
        page = 0
        note_ids = []
        while len(note_ids) < number:
            page += 1
            data = re.sub(r'"page":".*?"', f'"page":"{page}"', data)
            ret = js.call('get_xs', api, data, self.cookies['a1'])
            self.headers['x-s'], self.headers['x-t'] = ret['X-s'], str(ret['X-t'])
            response = requests.post(self.search_url, headers=self.headers, cookies=self.cookies, data=data.encode('utf-8'))
            res = response.json()
            if not res['data']['has_more']:
                print(f'搜索结果数量为 {len(note_ids)}, 不足 {number}')
                break
            items = res['data']['items']
            for note in items:
                note_id = note['id']
                note_ids.append(note_id)
                if len(note_ids) >= number:
                    break
        return note_ids

    def handle_note_info(self, query, number, need_cover=False):
        data = get_search_data()
        api = '/api/sns/web/v1/search/notes'
        data = json.dumps(data, separators=(',', ':'))
        data = re.sub(r'"keyword":".*?"', f'"keyword":"{query}"', data)
        page = 0
        index = 0
        while index < number:
            page += 1
            data = re.sub(r'"page":".*?"', f'"page":"{page}"', data)
            ret = js.call('get_xs', api, data, self.cookies['a1'])
            self.headers['x-s'], self.headers['x-t'] = ret['X-s'], str(ret['X-t'])
            response = requests.post(self.search_url, headers=self.headers, cookies=self.cookies, data=data.encode('utf-8'))
            res = response.json()
            if not res['data']['has_more']:
                print(f'搜索结果数量为 {index}, 不足 {number}')
                break
            items = res['data']['items']
            for note in items:
                index += 1
                self.oneNote.save_one_note_info(self.oneNote.detail_url + note['id'], need_cover, '', 'datas_search')

                if index >= number:
                    break
        print(f'搜索结果全部下载完成，共 {index} 个笔记')


def main():
    search = Search()
    query = '你好'
    # 搜索的数量（前多少个）
    number = 22
    search.handle_note_info(query, number, need_cover=True)


if __name__ == '__main__':
    main()