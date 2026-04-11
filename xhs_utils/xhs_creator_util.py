import json
import math
import random

import execjs

try:
    js = execjs.compile(open(r'../static/xhs_creator_260411.js', 'r', encoding='utf-8').read())
except:
    js = execjs.compile(open(r'static/xhs_creator_260411.js', 'r', encoding='utf-8').read())
try:
    signature_js = execjs.compile(open(r'static/xhs_creator_signature.js', 'r', encoding='utf-8').read())
except:
    signature_js = execjs.compile(open(r'../static/xhs_creator_signature.js', 'r', encoding='utf-8').read())

try:
    sign_js = execjs.compile(open(r'../static/xhs_creator_sign.js', 'r', encoding='utf-8').read())
except:
    sign_js = execjs.compile(open(r'static/xhs_creator_sign.js', 'r', encoding='utf-8').read())

def generate_xs(a1, api, data=''):
    ret = js.call('get_request_headers_params', api, data, a1)
    xs, xt = ret['xs'], ret['xt']
    if data:
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return xs, xt, data

def generate_xs_xs_common(a1, api, data=''):
    ret = js.call('get_request_headers_params', api, data, a1)

    xs, xt, xs_common = ret['xs'], ret['xt'], ret['xs_common']
    return xs, xt, xs_common

def generate_x_b3_traceid(len=16):
    x_b3_traceid = ""
    for t in range(len):
        x_b3_traceid += "abcdef0123456789"[math.floor(16 * random.random())]
    return x_b3_traceid
def generate_xsc(a1, api, data=''):
    xs, xt, xs_common = generate_xs_xs_common(a1, api, data)
    x_b3_traceid = generate_x_b3_traceid()
    headers = {}
    headers['x-s'] = xs
    headers['x-t'] = str(xt)
    headers['x-s-common'] = xs_common
    headers['x-b3-traceid'] = x_b3_traceid
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
        "authorization;": "",
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
        "x-b3-traceid": "84241340c1fcb99c",
        "x-s": "XYS_2UQhPsHCH0c1PjhFHjIj2erjwjQM89PjNsQhPjHCHS4kJfz647PjNsQhPUHCHfM1qAZlPebKPbYxwrkFapr3G9Ez8oY0tAm0Lo8Iw/SFLpYoyA+o/0Yzy0Yx+ju3+o4sanG64fkcyMS6aURGPbPEyBpbnD8QzFql4MY6ySbVPrTcGFMDaDTH2LSc89hUGDk6JDTOtMQo4Lz++78kPeSY/f+34n4jy0+s+Dpaqr4PcDV7yb4kL0poJ9MV89c6Gd4YaBbf8FSfLLY7apPhJ/QLP9zP8URHLjHVHdWFH0ijJ9Qx8n+FHdF=",
        # "x-s-common": "2UQAPsHC+aIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PjhFHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQM89PjNsQh+sHCH0Z1+Aq1PsHVHdWMH0ijP/DMPnPl8fGh+fpV+/HlJom34dHl87zi4/86GAbjPnbj8fbMJ9rEwnWMPeZIPeHhP0LUwsHVHdW9H0ijHjIj2eqjwjHjNsQhwsHCHDDAwoQH8B4AyfRI8FS98g+Dpd4daLP3JFSb/BMsn0pSPM87nrldzSzQ2bPAGdb7zgQB8nph8emSy9E0cgk+zSS1qgzianYt8Lzs/LzN4gzaa/+NqMS6qS4HLozoqfQnPbZEp98QyaRSp9P98pSl4oSzcgmca/P78nTTL08z/brManD9q9z18np/8db8aob7JeQl4epsPrzsagW3Lr4ryaRA4gz3agYDq7YM47HFqgzkanYMGLSbP9LA/bGIa/+nprSe+9LI4gzVPDbrJg+P4fprLFTALMm7+LSb4d+kpdzt/7b7wrQM498cqBzSpr8g/FSh+bzQygL9nSm7qSmM4epQ4flY/BQdqA+l4oYQ2BpAPp87arS34nMQyFSE8nkdqMD6pMzd8/4SL7bF8aRr+7+rG7mkqBpD8pSUzozQcA8Szb87PDSb/d+/qgzVJfl/4LExpdzQ4fRSy7bFP9+y+7+nJAzdaLp/2LSiz/zzwgbMagYiJdbCwB4QyFSfJ7b7yFSenSqh8e+A8BlO8p8c4A+Q4DbSPB8d8ncIngSQy/pAPFMHp/QM4rbQyLTAynz98nTy/fpLLocFJDbO8p4c4FpQ4fTP20m98p+M4MQIwLbAL7b7LrDAL7QQ2rLM/op749bl4UTU8nSjqgQO8pSx87+3qgzdanTD8pSdPBphp9QhanYdq98+8gP9yf+VanTm8/+c4bzQygQDLgb7a0YM4eSQPA8SPMmFpDSk/fLlLozVanDM8n8n4FbH4gz+z7b72rDALppQcFpSafbccL4VN7+kqgz+anYn4rSk8np84g4lcDS3womp+d+DyfH9anSc2gbc4sTTLo4/ag8O8gYc4bpF/LTAPnI9qM8jzpmQzLkA2B4OqAbl4r4Ppd4Yag8m8nkn498QyLkSpemr2LS9N9p/8DESpM8FPFDA+9pnqgqAwrQ8qDSiasTQcA8A2rS68/GE4fpDqDRAnpm7aDSbwsRQcM8V/b87GFDAnf8QyLESP9l/ygS6+fp84g46anTPqB+l49TUp94AL9pDq98n4bYALo41agYiJrSi2dkjpdc3cdpFGLSe4dPlan4S8dpFwBMc4BzQzpPFJ7pFPrDAqfMsyS46anSdq9G7P7+LGaRApdb7+gzl4BlQzpzTanV7qM8M4BTQzLbS8DMI2rS9t9+yJrMzagG3aFS9cnpDpdzGJ7pFPFEn4sRQcAWAaLP7qMzmcnLlLoq9qBQn/LSezdzopdzjJp8FPrS9+bYQynTEa/+g4DS3/9prq0+ApDMLLSmM4FTQcF49Jdp7/9Qn4M4Qz/pSn/m8+LShG9SPJFTSpb87y7kM4rRy2f+sq9QVaLSi/LkPqg4TanT6q98jqfMQy9QocS874DSkJoSzqgzftMm7GFSkysRQ4S+aag8I+7QM47SQzgm7anW7q7Yl4AmSJombaLpUJFSi8BpfN9pA8Sm7cLS9L/4Qc9Yi+rz84DSbJnS1ndQ3agGAq9krJ9pgLo4saLp6qM8l4rTQzL4caLpw8/mM4rQQyrMSJ7p7yDSb4dPA8aTtJM8FpUTc4omQcFbS+dbFJFSi8g+/89T3anYt8pSI+gPApdzw4Amdq9Sl4FRszd8APpmFPrShcg+n2DkA+dbFajHVHdWEH0iTP/LM+AH9+/PIPaIj2erIH0iINsQhP/rjwjQ1J7QTGnIjKc==",
        "x-t": "1754578609610",
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
        "authority": f"q-sign-algorithm=sha1&q-ak=null&q-sign-time={message}&q-key-time={message}&q-header-list=content-length&q-url-param-list=&q-signature={signature}",
        "cache-control": "",
        "content-type": "image/jpeg",
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
    "authorization;": "",
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
    "x-b3-traceid": "60ed2f830af78d18",
    "x-s": "XYS_2UQhPsHCH0c1PjhFHjIj2erjwjQM89PjNsQhPjHCHS4kJfz647PjNsQhPUHCHfM1qAZlPebKPbYxwrk74MmHwbSr2rGFaURca9pQyBzOL9z8wrpdyr4749YH4fpH+rYk8bma8Sz/JLpbLfTHPf+jaMr9n/zz+0q7JDpkLrREynkIL0PMyAza/DQewrRBJnb9adkC8D4Ey9bfLDWIpFEr20Yw+biFN74Szfbh/A4sPgY7PFh920zgzDT0GL8NqrHhnbY3PFR1LBQLznhM+p4HPLYOnSW9ajHVHdWFH0ijJ9Qx8n+FHdF=",
    "x-s-common": "2UQAPsHC+aIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PjhFHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQM89PjNsQh+sHCH0Z1+Aq1PsHVHdWMH0ijP/DMPnPl8fGh+fpV+/HlJom34dHl87zi4/86GAbjPnbj8fbMJ9rEwnWMPeZIPeHhP0LUwsHVHdW9H0ijHjIj2eqjwjHjNsQhwsHCHDDAwoQH8B4AyfRI8FS98g+Dpd4daLP3JFSb/BMsn0pSPM87nrldzSzQ2bPAGdb7zgQB8nph8emSy9E0cgk+zSS1qgzianYt8p+1/LzN4gzaa/+NqMS6qS4HLozoqfQnPbZEp98QyaRSp9P98pSl4oSzcgmca/P78nTTL08z/brManD9q9z18np/8db8aob7JeQl4epsPrzsagW3Lr4ryaRA4gz3agYDq7YM47HFqgzkanYMGLSbP9LA/bGIa/+nprSe+9LI4gzVPDbrJg+P4fprLFTALMm7+LSb4d+kpdzt/7b7wrQM498cqBzSpr8g/FSh+bzQygL9nSm7qSmM4epQ4flY/BQdqA+l4oYQ2BpAPp87arS34nMQyFSE8nkdqMD6pMzd8/4SL7bF8aRr+7+rG7mkqBpD8pSUzozQcA8Szb87PDSb/d+/qgzVJfl/4LExpdzQ4fRSy7bFP9+y+7+nJAzdaLp/2LSiz/zz8dbMagYiJdbCwB4QyFSfJ7b7yFSenSqh8e+A8BlO8p8c4A+Q4DbSPB8d8ncIngSQy/pAPFMHp/QM4rbQyLTAynz98nTy/fpLLocFJDbO8p4c4FpQ4fTP20m68nzc4ApIJDbAL7p7tFDAngQQ2rLM/op749bl4UTU8nSjqgQO8pSx87+3qgzdanTD8pSdPBphp9QhanYdq98+8gP9yf+VanTm8/+c4bzQygQDLgb7a0YM4eSQPA8SPMmFpDSk/fLlLozVanDM8n8n4FbH4gz+z7b72rDALppQcFpSafbccL4VN7+kqgz+anYn4rSk8np84gqFqDS3adZ6ad+gqMbDanSo2gbc4sTypd4/ag8O8nTc4bpF/LTAPnI9qM8jzpmQzLkA+DH7qMzM4F4I4g4caL+t8p4n49SQy94S2Bka4FS9+9p/JURS8S8FLFS9a9pnLozTtURoqLS3qbbQ2BRSPMi9qAbm+7PI2jRS8S87qDSb/p+Q4DSkPdbFGFSe/rlQy/mSL9QcL0WEJ9pxqgqhanTcwrTc4rpEcjRSydP68p4M49pNqgz7a/+cPFSiwezTpdzPLgb7qrDAN7+fa/pS8dpF2pkM4rSQznT+2Sm78rSkqpmyN7QPanSSqMSDJ7+fw/4Spob7wrEM4bmQyp4MagG98gYl4oSQz/4SPFSM+FSbzLk6pAzwag8a/FSe89pkLo4b2dbF/Sbc4rRQc7mnagGAqMzyPo+k4gcAzM+oPLS9GAWh4gzo8gbFtFDAyepQPMzPanS/qDS3/d+ncf4AyM+3JBQn4bkQPFSgqob7z7Qn4M+Q4DEAP/mi4rS3nDMPzepAydb7P9pM4B+6JgpCq9ElJrDAq/bUqg4GanV7q9TTqbSQypbpGMmF8DSkwob7LozMq7pFcDSiye4QzgQDa/+IcnRl4F+QyFY3aLp9qM4M4rpPyfMBanYoGFSe+dPIwLkApbm7JrS920+QyrSpN9+r+rShnSptGMZAaLP7qAb//fphpdzlanSmqAbM4ezQyoQcaLpOq98l4AYQcFMQqdp7zrDAP7P9aL86JdbFzSkc4oQQ4fzSyS8FLLS94d+8GDp3anTSq9kyO/FjNsQhwaHCN/PlPePEPAHA+UIj2erIH0iINsQhP/rjwjQ1J7QTGnIjKc==",
    "x-t": "1754583438247",
    "x-xray-traceid": "cc42a949cf700b529db7d62b69c81be0"
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
        "x-sign": "X2d2ea70d804b4f98d20cc70f5643bc26",
    }

def get_encryption_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization;": "",
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
        business_binds = "{\"version\":1,\"noteId\":0,\"bizType\":0,\"noteOrderBind\":{},\"notePostTiming\":{\"postTime\":\"\"},\"noteCollectionBind\":{\"id\":\"\"}}"
        business_binds = "{\"version\":1,\"noteId\":0,\"bizType\":0,\"noteOrderBind\":{},\"notePostTiming\":{},\"noteCollectionBind\":{\"id\":\"\"},\"noteSketchCollectionBind\":{\"id\":\"\"},\"coProduceBind\":{\"enable\":true},\"noteCopyBind\":{\"copyable\":true},\"interactionPermissionBind\":{\"commentPermission\":0},\"optionRelationList\":[]}",
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
            "extra_info_json": "{\"mimeType\":\"image/png\",\"bgColor\":\"\"}"
        })
    contextJson =  "{\"longTextToImage\":{\"imageFileIds\":[]},\"recommend_title\":{\"recommend_title_id\":\"\",\"is_use\":3,\"used_index\":-1},\"recommendTitle\":[],\"recommend_topics\":{\"used\":[]}}"
    contextJson = json.loads(contextJson)
    for i in images:
        contextJson['longTextToImage']['imageFileIds'].append(i['file_id'])

    contextJson = json.dumps(contextJson, separators=(',', ':'), ensure_ascii=False)
    return {
        "common": {
            "type": "normal",
            "title": title,
            "note_id": "",
            "desc": desc,
            "source": "{\"type\":\"web\",\"ids\":\"\",\"extraInfo\":\"{\\\"subType\\\":\\\"\\\",\\\"systemId\\\":\\\"web\\\"}\"}",
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


def get_post_note_video_data(title, desc, postTime, post_loc, privacy_type, fileInfo, firstFrameFileId):
    if postTime is None:
        business_binds = "{\"version\":1,\"noteId\":0,\"bizType\":0,\"noteOrderBind\":{},\"notePostTiming\":{\"postTime\":\"\"},\"noteCollectionBind\":{\"id\":\"\"}}"
    else:
        # 13位时间戳
        business_binds = f"{{\"version\":1,\"noteId\":0,\"bizType\":13,\"noteOrderBind\":{{}},\"notePostTiming\":{{\"postTime\":\"{postTime}\"}},\"noteCollectionBind\":{{\"id\":\"\"}}}}"
    return {
        "common": {
            "type": "video",
            "title": title,
            "note_id": "",
            "desc": desc,
            "source": "{\"type\":\"web\",\"ids\":\"\",\"extraInfo\":\"{\\\"systemId\\\":\\\"web\\\"}\"}",
            "business_binds": business_binds,
            "ats": [],
            "hash_tag": [],
            "post_loc": post_loc,
            "privacy_info": {
                "op_type": 1,
                "type": privacy_type
            }
        },
        "image_info": None,
        "video_info": {
            "file_id": f"spectrum/{fileInfo['fileIds']}",
            "format_width": 2560,
            "format_height": 1600,
            "video_preview_type": "",
            "composite_metadata": {
                "video": {
                    "bitrate": 2499968,
                    "colour_primaries": "BT.709",
                    "duration": 850,
                    "format": "AVC",
                    "frame_rate": 60,
                    "height": 1600,
                    "matrix_coefficients": "BT.709",
                    "rotation": None,
                    "transfer_characteristics": "BT.709",
                    "width": 2560
                },
                "audio": {
                    "bitrate": None,
                    "channels": 2,
                    "duration": 810,
                    "format": "AAC",
                    "sampling_rate": 48000
                }
            },
            "timelines": [],
            "cover": {
                "file_id": firstFrameFileId,
                "height": 1600,
                "width": 2560,
                "frame": {
                    "ts": 0,
                    "is_user_select": False,
                    "is_upload": False
                }
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
                        "duration": 0.85,
                        "transcoded": 0,
                        "media_source": 1,
                        "original_metadata": {
                            "video": {
                                "bitrate": 2499968,
                                "colour_primaries": "BT.709",
                                "duration": 850,
                                "format": "AVC",
                                "frame_rate": 60,
                                "height": 1600,
                                "matrix_coefficients": "BT.709",
                                "rotation": None,
                                "transfer_characteristics": "BT.709",
                                "width": 2560
                            },
                            "audio": {
                                "bitrate": None,
                                "channels": 2,
                                "duration": 810,
                                "format": "AAC",
                                "sampling_rate": 48000
                            }
                        }
                    }
                ]
            },
            "entrance": "web",
            "backup_covers": []
        }
    }
def splice_str(api, params):
    url = api + '?'
    for key, value in params.items():
        if value is None:
            value = ''
        url += key + '=' + value + '&'
    return url[:-1]