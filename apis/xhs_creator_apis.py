import json
import os
import tempfile
import time

import cv2
import numpy as np
import requests
from loguru import logger
from xhs_utils.cookie_util import trans_cookies
from xhs_utils.http_util import REQUEST_TIMEOUT
from xhs_utils.xhs_creator_util import get_upload_media_headers, get_post_note_headers, \
    get_loc_data, signature_js, get_fileIds_params, get_query_transcode_headers, \
    get_encryption_headers, sign_js, get_post_note_video_data, get_post_note_image_data, get_common_headers, \
    generate_xsc, generate_xs_xs_common, get_search_location_headers
from xhs_utils.xhs_util import splice_str, generate_x_rap_param


class XHS_Creator_Apis():
    def __init__(self):
        self.base_url = "https://creator.xiaohongshu.com"
        self.upload_url = "https://ros-upload.xiaohongshu.com"
        self.edith_url = "https://edith.xiaohongshu.com"
        self.xhs_web_url = "https://www.xiaohongshu.com"

    def get_topic(self, keyword, cookies):
        try:
            api = "/web_api/sns/v1/search/topic"
            data = {
                "keyword": keyword,
                "suggest_topic_request": {
                    "title": "",
                    "desc": f"#{keyword}"
                },
                "page": {
                    "page_size": 20,
                    "page": 1
                }
            }
            headers = get_common_headers()
            headers.update(generate_xsc(cookies['a1'], api, data))
            if data:
                data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            response = requests.post(self.edith_url + api, headers=headers, cookies=cookies, data=data.encode('utf-8'), timeout=REQUEST_TIMEOUT)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            res_json = None
            success, msg = False, str(e)
        return success, msg, res_json

    def get_location_info(self, keyword, cookies):
        try:
            data = get_loc_data(keyword)
            api = "/web_api/sns/v1/local/poi/creator/search"
            headers = get_search_location_headers()
            h = generate_xsc(cookies['a1'], api, data)
            headers.update(h)
            if data:
                data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            response = requests.post(self.edith_url + api, headers=headers, cookies=cookies, data=data.encode('utf-8'), timeout=REQUEST_TIMEOUT)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            res_json = None
            success, msg = False, str(e)
        return success, msg, res_json

    # media_type: image or video
    def get_fileIds(self, media_type, cookies):
        try:
            api = "/api/media/v1/upload/creator/permit"
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "authorization": "",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://creator.xiaohongshu.com/publish/publish?source=official&from=menu&target=image",
                "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                "x-b3-traceid": "",
                "x-xray-traceid": "",
                "x-s": "",
                "x-s-common": "",
                "x-t": ""
            }
            params = get_fileIds_params(media_type)
            splice_api = splice_str(api, params)

            headers.update(generate_xsc(cookies['a1'], splice_api))
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
            res_json = response.json()
            success, msg = res_json["success"], '获取fileIds成功'
        except Exception as e:
            return False, str(e), (None, None)
        return success, msg, (res_json, headers['x-t'])


    def upload_media(self, path_or_file, media_type, cookies):
        res = {
            "fileIds": '',
            "width": '',
            "height": '',
            "video_id": ''
        }
        try:
            success, msg, (data, xt) = self.get_fileIds(media_type, cookies)
            if not success:
                raise Exception(msg)
            data = data['data']['uploadTempPermits'][0]
            upload_host = data.get('uploadAddr') or self.upload_url.replace('https://', '')
            upload_url = upload_host if upload_host.startswith('http') else f"https://{upload_host}"
            fileIds, expireTime, token = data['fileIds'][0].split('/')[-1], data['expireTime'], data['token']
            res['fileIds'] = fileIds
            xt, expireTime = str(xt)[:10], str(expireTime)[:10]
            message = f"{xt};{expireTime}"
            if media_type == "image":
                width, height, file, file_size = self.get_file_info(path_or_file, media_type="image")
                res['width'] = width
                res['height'] = height
                res['file_size'] = file_size
                res['mime_type'] = "image/png"
            else:
                file, file_size = self.get_file_info(path_or_file, media_type="video")
                res['file_size'] = file_size
            signature = signature_js.call('getSignature', message, fileIds, file_size, upload_host)
            headers = get_upload_media_headers(message, signature, token)
            api = f"/spectrum/{fileIds}"
            response = requests.put(upload_url + api, headers=headers, data=file, cookies=cookies, timeout=REQUEST_TIMEOUT)
            if media_type == "video":
                res['video_id'] = response.headers['X-Ros-Video-Id']
        except Exception as e:
            return False, str(e), None
        return True, "上传成功", res

    def query_transcode(self, video_id, cookies):
        res_json = None
        success, msg = False, ''
        try:
            api = "/web_api/sns/capa/postgw/query_transcode"
            headers = get_query_transcode_headers()
            params = {
                "video_id": str(video_id),
                "need_transcode": "false",
                "resource_type": "0",
            }
            splice_api = splice_str(api, params)
            headers.update(generate_xsc(cookies['a1'], splice_api))
            response = requests.get(self.edith_url + splice_api, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
            res_json = response.json()
            success = res_json["success"]
            if 'msg' in res_json:
                msg = res_json['msg']
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, res_json

    def encryption(self, file_id, cookies):
        res_json = None
        success, msg = False, ''
        try:
            api = "/web_api/sns/v5/creator/file/encryption"
            headers = get_encryption_headers()
            params = {
                "file_id": file_id,
                "type": "image",
                "ts": str(int(time.time() * 1000)),
                "sign": ""
            }
            sign = sign_js.call('urlSing', file_id)
            params['sign'] = sign
            splice_api = splice_str(api, params)
            headers.update(generate_xsc(cookies['a1'], splice_api))
            response = requests.get(self.xhs_web_url + splice_api, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success, msg = False, str(e)
        return success, msg, res_json


    def post_note(self, noteInfo, cookies_str):
        post_api = "/web_api/sns/v2/note"
        headers = get_post_note_headers()
        cookies = trans_cookies(cookies_str)
        title = noteInfo['title']
        desc = noteInfo['desc']
        postTime = noteInfo['postTime']
        location = noteInfo['location']
        type = noteInfo['type']
        media_type = noteInfo['media_type']

        if location is not None:
            success, msg, location_info = self.get_location_info(location, cookies)
            if not success:
                raise Exception(msg)
            if len(location_info['data']['poi_list']) == 0:
                raise Exception('未找到该地点')
            location = location_info['data']['poi_list'][0]
            post_loc = {
                "name": location['name'],
                "subname": location['full_address'],
                "poi_id": location['poi_id'],
                "poi_type": location['poi_type'],
            }
        else:
            post_loc = {}
        if media_type == 'video':
            video = noteInfo['video']
            cover, metadata = self.extract_video_cover_and_metadata(video)
            success, msg, fileInfo = self.upload_media(video, media_type, cookies)
            if not success:
                raise Exception(msg)
            success, msg, coverInfo = self.upload_media(cover, 'image', cookies)
            if not success:
                raise Exception(msg)
            for _ in range(20):
                success, msg, res = self.query_transcode(fileInfo['video_id'], cookies)
                if not success:
                    raise Exception(msg)
                data_info = res.get('data') or {}
                if data_info.get('hasFirstFrame') is True or data_info.get('status') in (2, 'success', 'SUCCESS') or not data_info:
                    break
                time.sleep(3)
            data = get_post_note_video_data(title, desc, postTime, post_loc, type, fileInfo, coverInfo, metadata)
        else:
            fileInfos = []
            images = noteInfo['images']
            for image in images:
                success, msg, fileInfo = self.upload_media(image, media_type, cookies)
                if not success:
                    raise Exception(msg)
                fileInfos.append(fileInfo)
            data = get_post_note_image_data(title, desc, postTime, post_loc, type, fileInfos)
        topics = noteInfo['topics']
        for topic in topics:
            success, msg, res_json = self.get_topic(topic, cookies)
            if not success:
                raise Exception(msg)
            if len(res_json['data']['topic_info_dtos']) == 0:
                raise Exception(f'未找到话题{topic}')
            insert_topic = res_json['data']['topic_info_dtos'][0]
            insert_topic = {
                "id": insert_topic['id'],
                "link": insert_topic['link'],
                "name": insert_topic['name'],
                "type": 'topic'
            }
            data['common']['hash_tag'].append(insert_topic)
            data['common']['desc'] += f" #{insert_topic['name']}[话题]# "

        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        xs, xt, xs_common = generate_xs_xs_common(cookies['a1'], post_api, data)
        headers['x-s'], headers['x-t'], headers['x-s-common'] = xs, str(xt), xs_common
        headers['x-rap-param'] = generate_x_rap_param(post_api, data)

        response = requests.post(self.edith_url + post_api, headers=headers, data=data.encode('utf-8'), cookies=cookies, timeout=REQUEST_TIMEOUT)
        res_json = response.json()
        success, msg = res_json["success"], res_json["msg"]
        return success, msg, res_json

    def get_file_info(self, file, media_type="image"):
        file_size = len(file)
        if media_type == "image":
            size = cv2.imdecode(np.frombuffer(file, np.uint8), cv2.IMREAD_COLOR).shape
            w, h = size[1], size[0]
            if w > 2 * h:
                h = int(w / 2)
            return w, h, file, file_size
        else:
            return file, file_size

    def extract_video_cover_and_metadata(self, video):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
                f.write(video)
                temp_path = f.name

            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise ValueError("video decode failed")

            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            duration_ms = int(frame_count / fps * 1000) if fps else 0
            success, frame = cap.read()
            cap.release()
            if not success:
                raise ValueError("video cover frame decode failed")

            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                raise ValueError("video cover encode failed")

            metadata = {
                "video": {
                    "bitrate": None,
                    "colour_primaries": "BT.709",
                    "duration": duration_ms,
                    "format": "AVC",
                    "frame_rate": round(fps, 3) if fps else 0,
                    "height": height,
                    "matrix_coefficients": "BT.709",
                    "rotation": 0,
                    "transfer_characteristics": "BT.709",
                    "width": width
                },
                "audio": {
                    "bitrate": None,
                    "channels": 2,
                    "duration": duration_ms,
                    "format": "AAC",
                    "sampling_rate": 48000
                }
            }
            return encoded.tobytes(), metadata
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


    # # page: 页数
    # # time: 最近几天的时间
    # def get_publish_note_info(self, page: int, time: int, cookies_str):
    #     success = False
    #     msg = '成功'
    #     res_json = None
    #     try:
    #         api = "/api/galaxy/creator/data/note_stats/new"
    #         headers = get_common_headers()
    #         cookies = trans_cookies(cookies_str)
    #         xs, xt, _ = generate_xs(cookies['a1'], '/api/galaxy/creator/data/note_stats/new', '')
    #         headers['x-s'], headers['x-t'] = xs, str(xt)
    #         headers['x-b3-traceid'] = generate_x_b3_traceid()
    #         params = {
    #             "page": str(page),
    #             "page_size": "12",
    #             "sort_by": "time",
    #             "note_type": "0",
    #             "time": str(time),
    #             "is_recent": "false"
    #         }
    #         response = requests.get(self.base_url + api, headers=headers, cookies=cookies, params=params)
    #         res_json = response.json()
    #         success = res_json["success"]
    #     except Exception as e:
    #         success, msg = False, str(e)
    #     return success, msg, res_json
    #
    #
    # # 获取全部的发布信息
    # def get_all_publish_note_info(self, cookies_str):
    #     page = 1
    #     time = 7
    #     success, msg, res_json = self.get_publish_note_info(page, time, cookies_str)
    #     if not success:
    #         return False, msg, None
    #     notes = res_json['data']['note_infos']
    #     total = res_json['data']['total']
    #     while len(notes) < total:
    #         page += 1
    #         success, msg, res_json = self.get_publish_note_info(page, time, cookies_str)
    #         if not success:
    #             return False, msg, None
    #         notes += res_json['data']['note_infos']
    #     return True, '成功', notes

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
            params = {
                "tab": '0',
            }
            if page:
                params["page"] = str(page)
            splice_api = splice_str(api, params)
            headers.update(generate_xsc(cookies['a1'], splice_api))
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
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
            logger.debug(f'{success}, {msg}, {res_json}')
            if not success:
                return False, msg, notes
            notes += res_json['data']['notes']
            page = res_json['data']['page']
            if page == -1:
                break
        return True, '成功', notes


if __name__ == '__main__':
    xhs_creator_apis = XHS_Creator_Apis()
    # 创作者平台 https://creator.xiaohongshu.com/login 的cookie
    cookies_str = r''
    noteInfos = [
        {
            # 标题
            "title": "21121121212",
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
            "title": "test2",
            "desc": "dwadawd20240815",
            "postTime": None,
            "location": '河海大学',
            "topics": ["北京"],
            # "topics": [],
            "type": 1,
            "media_type": "video",
            "video": open(r"D:\data\Videos\2024-05-02 21-14-45.mkv", 'rb').read(),
        }
    ]
    for noteInfo in noteInfos:
        success, msg, info = xhs_creator_apis.post_note(noteInfo, cookies_str)
        logger.debug(f'{success}, {msg}, {info}')
        logger.debug('========')

    # topics = ["雀魂", "麻将"]
    # cookies = trans_cookies(cookies_str)
    # for topic in topics:
    #     success, msg, res_json = xhs_creator_apis.get_topic(topic, cookies)
    #     print(success, msg, res_json)
