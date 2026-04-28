import json
import os

import execjs

from xhs_utils.xhs_util import generate_x_b3_traceid, generate_xray_traceid, splice_str

_STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))


def _compile_static_js(filename):
    with open(os.path.join(_STATIC_DIR, filename), 'r', encoding='utf-8') as f:
        return execjs.compile(f.read())


_JS_CACHE = {}


def _get_static_js(filename):
    if filename not in _JS_CACHE:
        _JS_CACHE[filename] = _compile_static_js(filename)
    return _JS_CACHE[filename]


class LazyStaticJS:
    def __init__(self, filename):
        self.filename = filename

    def call(self, *args):
        return _get_static_js(self.filename).call(*args)

    def eval(self, *args):
        return _get_static_js(self.filename).eval(*args)


signature_js = LazyStaticJS('xhs_creator_signature.js')
sign_js = LazyStaticJS('xhs_creator_sign.js')

def generate_xs(a1, api, data=''):
    ret = _get_static_js('xhs_creator_260411.js').call('get_request_headers_params', api, data, a1)
    xs, xt = ret['xs'], ret['xt']
    if data:
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return xs, xt, data

def generate_xs_xs_common(a1, api, data=''):
    ret = _get_static_js('xhs_creator_260411.js').call('get_request_headers_params', api, data, a1)

    xs, xt, xs_common = ret['xs'], ret['xt'], ret['xs_common']
    return xs, xt, xs_common

def generate_xsc(a1, api, data=''):
    xs, xt, xs_common = generate_xs_xs_common(a1, api, data)
    x_b3_traceid = generate_x_b3_traceid()
    headers = {}
    headers['x-s'] = xs
    headers['x-t'] = str(xt)
    headers['x-s-common'] = xs_common
    headers['x-b3-traceid'] = x_b3_traceid
    headers['x-xray-traceid'] = generate_xray_traceid()
    return headers

# scene: image/video
def get_fileIds_params(scene):
    return {
        "biz_name": "spectrum",
        "scene": scene,
        "file_count": "1",
        "version": "1",
        "source": "web"
    }

def get_search_location_headers():
    return  {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization": "",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://creator.xiaohongshu.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://creator.xiaohongshu.com/",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "x-b3-traceid": "",
        "x-s": "",
        # "x-s-common": "2UQAPsHC+aIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PjhFHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQM89PjNsQh+sHCH0Z1+Aq1PsHVHdWMH0ijP/DMPnPl8fGh+fpV+/HlJom34dHl87zi4/86GAbjPnbj8fbMJ9rEwnWMPeZIPeHhP0LUwsHVHdW9H0ijHjIj2eqjwjHjNsQhwsHCHDDAwoQH8B4AyfRI8FS98g+Dpd4daLP3JFSb/BMsn0pSPM87nrldzSzQ2bPAGdb7zgQB8nph8emSy9E0cgk+zSS1qgzianYt8Lzs/LzN4gzaa/+NqMS6qS4HLozoqfQnPbZEp98QyaRSp9P98pSl4oSzcgmca/P78nTTL08z/brManD9q9z18np/8db8aob7JeQl4epsPrzsagW3Lr4ryaRA4gz3agYDq7YM47HFqgzkanYMGLSbP9LA/bGIa/+nprSe+9LI4gzVPDbrJg+P4fprLFTALMm7+LSb4d+kpdzt/7b7wrQM498cqBzSpr8g/FSh+bzQygL9nSm7qSmM4epQ4flY/BQdqA+l4oYQ2BpAPp87arS34nMQyFSE8nkdqMD6pMzd8/4SL7bF8aRr+7+rG7mkqBpD8pSUzozQcA8Szb87PDSb/d+/qgzVJfl/4LExpdzQ4fRSy7bFP9+y+7+nJAzdaLp/2LSiz/zzwgbMagYiJdbCwB4QyFSfJ7b7yFSenSqh8e+A8BlO8p8c4A+Q4DbSPB8d8ncIngSQy/pAPFMHp/QM4rbQyLTAynz98nTy/fpLLocFJDbO8p4c4FpQ4fTP20m98p+M4MQIwLbAL7b7LrDAL7QQ2rLM/op749bl4UTU8nSjqgQO8pSx87+3qgzdanTD8pSdPBphp9QhanYdq98+8gP9yf+VanTm8/+c4bzQygQDLgb7a0YM4eSQPA8SPMmFpDSk/fLlLozVanDM8n8n4FbH4gz+z7b72rDALppQcFpSafbccL4VN7+kqgz+anYn4rSk8np84g4lcDS3womp+d+DyfH9anSc2gbc4sTTLo4/ag8O8gYc4bpF/LTAPnI9qM8jzpmQzLkA2B4OqAbl4r4Ppd4Yag8m8nkn498QyLkSpemr2LS9N9p/8DESpM8FPFDA+9pnqgqAwrQ8qDSiasTQcA8A2rS68/GE4fpDqDRAnpm7aDSbwsRQcM8V/b87GFDAnf8QyLESP9l/ygS6+fp84g46anTPqB+l49TUp94AL9pDq98n4bYALo41agYiJrSi2dkjpdc3cdpFGLSe4dPlan4S8dpFwBMc4BzQzpPFJ7pFPrDAqfMsyS46anSdq9G7P7+LGaRApdb7+gzl4BlQzpzTanV7qM8M4BTQzLbS8DMI2rS9t9+yJrMzagG3aFS9cnpDpdzGJ7pFPFEn4sRQcAWAaLP7qMzmcnLlLoq9qBQn/LSezdzopdzjJp8FPrS9+bYQynTEa/+g4DS3/9prq0+ApDMLLSmM4FTQcF49Jdp7/9Qn4M4Qz/pSn/m8+LShG9SPJFTSpb87y7kM4rRy2f+sq9QVaLSi/LkPqg4TanT6q98jqfMQy9QocS874DSkJoSzqgzftMm7GFSkysRQ4S+aag8I+7QM47SQzgm7anW7q7Yl4AmSJombaLpUJFSi8BpfN9pA8Sm7cLS9L/4Qc9Yi+rz84DSbJnS1ndQ3agGAq9krJ9pgLo4saLp6qM8l4rTQzL4caLpw8/mM4rQQyrMSJ7p7yDSb4dPA8aTtJM8FpUTc4omQcFbS+dbFJFSi8g+/89T3anYt8pSI+gPApdzw4Amdq9Sl4FRszd8APpmFPrShcg+n2DkA+dbFajHVHdWEH0iTP/LM+AH9+/PIPaIj2erIH0iINsQhP/rjwjQ1J7QTGnIjKc==",
        "x-s-common": "",
        "x-t": "",
        # "x-xray-traceid": "cc428472e3e116d000ea48806dce1d78"
    }
def get_common_headers():
    return  {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "accept": "application/json, text/plain, */*",
        "Host": "edith.xiaohongshu.com",
        "pragma": "no-cache",
        "cache-control": "no-cache",
        "sec-ch-ua-platform": "\"Windows\"",
        "authorization": "",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "x-t": "",
        "x-s": "",
        "x-s-common": "",
        "x-b3-traceid": "",
        "x-xray-traceid": "",
        "origin": "https://creator.xiaohongshu.com",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://creator.xiaohongshu.com/",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "priority": "u=1, i"
    }


def get_upload_media_headers(message, signature, token):
    return {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization": f"q-sign-algorithm=sha1&q-ak=null&q-sign-time={message}&q-key-time={message}&q-header-list=content-length;host&q-url-param-list=&q-signature={signature}",
        "cache-control": "",
        "content-type": "",
        "origin": "https://creator.xiaohongshu.com",
        "pragma": "no-cache",
        "referer": "https://creator.xiaohongshu.com/",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "x-cos-security-token": token,
    }

def get_post_note_headers():
    return {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "authorization": "",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://creator.xiaohongshu.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://creator.xiaohongshu.com/",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
    "x-b3-traceid": generate_x_b3_traceid(),
    "x-s": "",
    "x-s-common": "",
    "x-t": "",
    "x-rap-param": "",
    "x-xray-traceid": generate_xray_traceid(),
}

def get_query_transcode_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization": "",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://creator.xiaohongshu.com",
        "priority": "u=1, i",
        "referer": "https://creator.xiaohongshu.com/",
        "sec-ch-ua": "\"Chromium\";v=\"124\", \"Microsoft Edge\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "x-b3-traceid": "",
        "x-s": "",
        "x-s-common": "",
        "x-t": "",
    }

def get_encryption_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization": "",
        "cache-control": "no-cache",
        "origin": "https://creator.xiaohongshu.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://creator.xiaohongshu.com/",
        "sec-ch-ua": "\"Chromium\";v=\"130\", \"Microsoft Edge\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    }

def get_post_note_image_data(title, desc, postTime, post_loc, privacy_type, fileInfos):
    if postTime is None:
        business_binds = "{\"version\":1,\"noteId\":0,\"bizType\":0,\"noteOrderBind\":{},\"notePostTiming\":{},\"noteCollectionBind\":{\"id\":\"\"},\"noteSketchCollectionBind\":{\"id\":\"\"},\"coProduceBind\":{\"enable\":true},\"noteCopyBind\":{\"copyable\":true},\"interactionPermissionBind\":{\"commentPermission\":0},\"optionRelationList\":[]}"
    else:
        # 13位时间戳
        business_binds = f"{{\"version\":1,\"noteId\":0,\"bizType\":13,\"noteOrderBind\":{{}},\"notePostTiming\":{{\"postTime\":\"{postTime}\"}},\"noteCollectionBind\":{{\"id\":\"\"}}}}"
    images = []
    for fileInfo in fileInfos:
        fileIds = fileInfo['fileIds']
        # 数字int
        width = fileInfo['width']
        height = fileInfo['height']
        images.append({
            "file_id": f"spectrum/{fileIds}",
            "width": width,
            "height": height,
            "metadata": {
                "source": -1
            },
            "stickers": {
                "version": 2,
                "floating": []
            },
            "extra_info_json": json.dumps({
                "mimeType": fileInfo.get("mime_type", "image/png"),
                "image_metadata": {
                    "bg_color": "",
                    "origin_size": fileInfo.get("file_size", 0) / 1024
                }
            }, separators=(',', ':'), ensure_ascii=False)
        })
    contextJson = json.dumps({
        "recommend_title": {
            "recommend_title_id": "",
            "is_use": 3,
            "used_index": -1
        },
        "recommendTitle": [],
        "recommend_topics": {
            "used": []
        }
    }, separators=(',', ':'), ensure_ascii=False)
    return {
        "common": {
            "type": "normal",
            "title": title,
            "note_id": "",
            "desc": desc,
            "source": "{\"type\":\"web\",\"ids\":\"\",\"extraInfo\":\"{\\\"subType\\\":\\\"official\\\",\\\"systemId\\\":\\\"web\\\"}\"}",
            "business_binds": business_binds,
            "ats": [],
            "hash_tag": [],
            "post_loc": post_loc,
            "privacy_info": {
                "op_type": 1,
                "type": privacy_type,
                "user_ids": []
            },
            "goods_info": {},
            "biz_relations": [],
            "capa_trace_info": {
                "contextJson": contextJson
            }
        },
        "image_info": {
            "images": images
        },
        "video_info": None
    }

def get_loc_data(keyword):
    return {
        "latitude": 31.161327166987615,
        "longitude": 121.45301809352632,
        "keyword": keyword,
        "page": 1,
        "size": 50,
        "source": "WEB",
        "type": 3
    }


def get_post_note_video_data(title, desc, postTime, post_loc, privacy_type, fileInfo, coverInfo, metadata=None):
    if postTime is None:
        business_binds = "{\"version\":1,\"noteId\":0,\"bizType\":0,\"noteOrderBind\":{},\"notePostTiming\":{},\"noteCollectionBind\":{\"id\":\"\"},\"noteSketchCollectionBind\":{\"id\":\"\"},\"coProduceBind\":{\"enable\":true},\"noteCopyBind\":{\"copyable\":true},\"interactionPermissionBind\":{\"commentPermission\":0},\"optionRelationList\":[]}"
    else:
        # 13位时间戳
        business_binds = f"{{\"version\":1,\"noteId\":0,\"bizType\":13,\"noteOrderBind\":{{}},\"notePostTiming\":{{\"postTime\":\"{postTime}\"}},\"noteCollectionBind\":{{\"id\":\"\"}}}}"
    metadata = metadata or {}
    video_meta = metadata.get("video") or {
        "bitrate": None,
        "colour_primaries": "BT.709",
        "duration": 0,
        "format": "AVC",
        "frame_rate": 0,
        "height": fileInfo.get("height") or 0,
        "matrix_coefficients": "BT.709",
        "rotation": 0,
        "transfer_characteristics": "BT.709",
        "width": fileInfo.get("width") or 0
    }
    audio_meta = metadata.get("audio") or {
        "bitrate": None,
        "channels": 2,
        "duration": video_meta.get("duration", 0),
        "format": "AAC",
        "sampling_rate": 48000
    }
    duration_seconds = round((video_meta.get("duration") or 0) / 1000, 3)
    video_file_id = f"spectrum/{fileInfo['fileIds']}"
    cover_file_id = f"spectrum/{coverInfo['fileIds']}"
    return {
        "common": {
            "type": "video",
            "title": title,
            "note_id": "",
            "desc": desc,
            "source": "{\"type\":\"web\",\"ids\":\"\",\"extraInfo\":\"{\\\"subType\\\":\\\"official\\\",\\\"systemId\\\":\\\"web\\\"}\"}",
            "business_binds": business_binds,
            "ats": [],
            "hash_tag": [],
            "post_loc": post_loc,
            "privacy_info": {
                "op_type": 1,
                "type": privacy_type,
                "user_ids": []
            },
            "goods_info": {},
            "biz_relations": [],
            "capa_trace_info": {
                "contextJson": "{\"recommend_title\":{\"recommend_title_id\":\"\",\"is_use\":3,\"used_index\":-1},\"recommendTitle\":[],\"recommend_topics\":{\"used\":[]}}"
            },
        },
        "image_info": None,
        "video_info": {
            "fileid": video_file_id,
            "file_id": video_file_id,
            "format_width": video_meta.get("width") or fileInfo.get("width") or 0,
            "format_height": video_meta.get("height") or fileInfo.get("height") or 0,
            "video_preview_type": "",
            "composite_metadata": {
                "video": video_meta,
                "audio": audio_meta
            },
            "timelines": [],
            "cover": {
                "fileid": cover_file_id,
                "file_id": cover_file_id,
                "height": coverInfo.get("height") or video_meta.get("height") or 0,
                "width": coverInfo.get("width") or video_meta.get("width") or 0,
                "frame": {
                    "ts": 0,
                    "is_user_select": False,
                    "is_upload": False
                },
                "stickers": {
                    "version": 2,
                    "neptune": []
                },
                "fonts": [],
                "extra_info_json": "{}"
            },
            "chapters": [],
            "chapter_sync_text": False,
            "segments": {
                "count": 1,
                "need_slice": False,
                "items": [
                    {
                        "mute": 0,
                        "speed": 1,
                        "start": 0,
                        "duration": duration_seconds,
                        "transcoded": 0,
                        "media_source": 1,
                        "original_metadata": {
                            "video": video_meta,
                            "audio": audio_meta
                        }
                    }
                ]
            },
            "entrance": "web"
        }
    }
