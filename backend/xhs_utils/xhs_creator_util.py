import json

import execjs

try:
    js = execjs.compile(
        open(r"../static/xhs_creator_xs.js", "r", encoding="utf-8").read()
    )
except:
    js = execjs.compile(open(r"static/xhs_creator_xs.js", "r", encoding="utf-8").read())


def generate_xs(a1, api, data=""):
    ret = js.call("get_request_headers_params", api, data, a1)
    xs, xt = ret["xs"], ret["xt"]
    if data:
        data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    return xs, xt, data


def get_common_headers():
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
        "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
        "x-s": "",
        "x-t": "",
    }


def splice_str(api, params):
    url = api + "?"
    for key, value in params.items():
        if value is None:
            value = ""
        url += key + "=" + value + "&"
    return url[:-1]
