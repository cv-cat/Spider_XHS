import json
import os

import execjs

from xhs_utils.xhs_creator.auth import XHSCreatorAuth
from xhs_utils.xhs_creator.params import (
    generate_request_params,
    generate_xsc as _generate_xsc,
)
_STATIC_DIR = os.path.join(os.path.dirname(__file__), 'xhs_creator', 'js')


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

_CREATOR_RAP_TPL_PATH = os.path.join(_STATIC_DIR, 'rap_fingerprint_creator.json')
_ALPHABET36 = '0123456789abcdefghijklmnopqrstuvwxyz'


def load_creator_rap_fingerprint_hex() -> str:
    """加载 Creator 发布接口的 rap 指纹模板（Uuid 每次随机化）。

    模板来自浏览器 Creator post_note x-rap-param 信封的 AES 解密
    （build 1.19.3，436B）。03ea 段的 16 字符会话 Uuid 每次重新随机，
    避免静态指纹聚类；03eb 槽位由生成侧按 url+body 现算覆写。
    """
    import random
    with open(os.path.abspath(_CREATOR_RAP_TPL_PATH), encoding='utf-8') as fh:
        tpl = json.load(fh)
    raw = bytearray.fromhex(tpl['bodyUnmaskedHex'])
    if raw[:6].hex() != '03ea00000010':
        raise RuntimeError('creator rap fingerprint template 03ea Uuid section not found')
    raw[6:22] = ''.join(random.choice(_ALPHABET36) for _ in range(16)).encode('ascii')
    return raw.hex()

def _require_auth(auth):
    if not isinstance(auth, XHSCreatorAuth):
        raise TypeError(
            'Creator signing now requires XHSCreatorAuth; create it with '
            'from_cookie(), from_qrcode_login(), or from_phone_login()'
        )
    return auth


def generate_xs(auth, api, data=''):
    headers, _, body = generate_request_params(_require_auth(auth), api, data)
    return headers['x-s'], headers['x-t'], body


def generate_xs_xs_common(auth, api, data=''):
    headers, _, _ = generate_request_params(_require_auth(auth), api, data)
    return headers['x-s'], headers['x-t'], headers['x-s-common']


def generate_xsc(auth, api, data=''):
    return _generate_xsc(_require_auth(auth), api, data)

# scene: image/video
def get_fileIds_params(scene):
    return {
        "biz_name": "spectrum",
        "scene": scene,
        "file_count": "1",
        "version": "1",
        "source": "web"
    }

def get_upload_media_headers(message, signature, token, *, user_agent, upload_host=''):
    # 2026-07-25 浏览器实抓（ros-upload-d4 PUT）：accept-encoding 含 zstd、
    # accept-language 为长列表、无 pragma 头；sec-fetch-site 随上传域与
    # creator.xiaohongshu.com 的站点关系变化（xhscdn.com -> cross-site）。
    sec_fetch_site = (
        'cross-site' if 'xhscdn.com' in str(upload_host) else 'same-site'
    )
    return {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6",
        "authorization": f"q-sign-algorithm=sha1&q-ak=null&q-sign-time={message}&q-key-time={message}&q-header-list=content-length;host&q-url-param-list=&q-signature={signature}",
        "cache-control": "",
        "content-type": "",
        "origin": "https://creator.xiaohongshu.com",
        "referer": "https://creator.xiaohongshu.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": sec_fetch_site,
        "user-agent": user_agent,
        "x-cos-security-token": token,
    }

def get_post_note_image_data(title, desc, postTime, post_loc, privacy_type, fileInfos):
    if postTime is None:
        business_binds = "{\"version\":1,\"noteId\":0,\"bizType\":0,\"noteOrderBind\":{},\"notePostTiming\":{},\"noteCollectionBind\":{\"id\":\"\"},\"noteSketchCollectionBind\":{\"id\":\"\"},\"noteCopyBind\":{\"copyable\":false},\"interactionPermissionBind\":{\"commentPermission\":0},\"optionRelationList\":[]}"
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
