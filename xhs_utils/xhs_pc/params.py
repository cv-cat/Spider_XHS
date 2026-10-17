import json
import math
import os
import random
import time
import uuid
from urllib.parse import urlencode

from xhs_utils.cookie_util import trans_cookies
from xhs_utils.xhs_core.http import ordered_wire_headers


PC_LOGIN_ACCEPT_LANGUAGE = 'zh-CN,zh;q=0.9'
PC_BUSINESS_ACCEPT_LANGUAGE = 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6'
PC_SEC_CH_UA = (
    '"Google Chrome";v="155", "Chromium";v="155", '
    '"Not(A:Brand";v="24"'
)

PC_CURRENT_BROWSER_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'
)

PC_NAVIGATION_HEADER_ORDER = (
    'upgrade-insecure-requests', 'user-agent', 'sec-ch-ua',
    'sec-ch-ua-mobile', 'sec-ch-ua-platform', 'accept', 'accept-encoding',
    'accept-language', 'cookie', 'priority', 'sec-fetch-dest',
    'sec-fetch-mode', 'sec-fetch-site', 'sec-fetch-user',
)
PC_HONEYPOT_HEADER_ORDER = (
    'sec-ch-ua-platform', 'referer', 'user-agent', 'accept', 'sec-ch-ua',
    'content-type', 'sec-ch-ua-mobile', 'accept-encoding', 'accept-language',
    'cookie', 'origin', 'priority', 'sec-fetch-dest', 'sec-fetch-mode',
    'sec-fetch-site',
)
PC_SECURITY_HEADER_ORDER = (
    'sec-ch-ua-platform', 'referer', 'sec-ch-ua', 'sec-ch-ua-mobile',
    'x-t', 'x-s-common', 'user-agent', 'accept', 'content-type', 'x-s',
    'accept-encoding', 'accept-language', 'cookie', 'origin', 'priority',
    'sec-fetch-dest', 'sec-fetch-mode', 'sec-fetch-site',
)
PC_SEM_HEADER_ORDER = (
    'sec-ch-ua-platform', 'referer', 'sec-ch-ua', 'sec-ch-ua-mobile',
    'x-t', 'x-s-common', 'user-agent', 'accept', 'x-s', 'accept-encoding',
    'accept-language', 'origin', 'priority', 'sec-fetch-dest',
    'sec-fetch-mode', 'sec-fetch-site',
)
PC_SIGNED_POST_HEADER_ORDER = (
    'sec-ch-ua-platform', 'referer', 'sec-ch-ua', 'x-xray-traceid',
    'sec-ch-ua-mobile', 'x-t', 'x-b3-traceid', 'x-s-common',
    'user-agent', 'accept', 'content-type', 'x-s', 'accept-encoding',
    'accept-language', 'cookie', 'origin', 'priority', 'sec-fetch-dest',
    'sec-fetch-mode', 'sec-fetch-site',
)
PC_SIGNED_GET_HEADER_ORDER = (
    'sec-ch-ua-platform', 'referer', 'sec-ch-ua', 'x-xray-traceid',
    'sec-ch-ua-mobile', 'x-t', 'x-b3-traceid', 'x-s-common',
    'user-agent', 'accept', 'x-s', 'accept-encoding', 'accept-language',
    'cookie', 'origin', 'priority', 'sec-fetch-dest', 'sec-fetch-mode',
    'sec-fetch-site',
)
PC_BUSINESS_SIGNED_POST_HEADER_ORDER = (
    'referer', 'x-xray-traceid', 'x-t', 'x-b3-traceid', 'x-s-common',
    'user-agent', 'accept', 'content-type', 'x-s', 'accept-encoding',
    'accept-language', 'cookie', 'origin', 'priority', 'sec-fetch-dest',
    'sec-fetch-mode', 'sec-fetch-site',
)
PC_BUSINESS_SIGNED_GET_HEADER_ORDER = (
    'referer', 'x-xray-traceid', 'x-t', 'x-b3-traceid', 'x-s-common',
    'user-agent', 'accept', 'x-s', 'accept-encoding', 'accept-language',
    'cookie', 'origin', 'priority', 'sec-fetch-dest', 'sec-fetch-mode',
    'sec-fetch-site',
)
PC_BUSINESS_CDEVICE_GET_HEADER_ORDER = (
    'referer', 'x-xray-traceid', 'c_device_id', 'x-t', 'x-b3-traceid',
    'x-s-common', 'user-agent', 'accept', 'x-s', 'accept-encoding',
    'accept-language', 'cookie', 'origin', 'priority', 'sec-fetch-dest',
    'sec-fetch-mode', 'sec-fetch-site',
)
PC_LIVE_POST_HEADER_ORDER = (
    'referer', 'xy-common-params', 'x-t', 'x-s-common',
    'x-ratelimit-meta', 'accept', 'content-type', 'x-s', 'user-agent',
    'accept-encoding', 'accept-language', 'cookie', 'origin', 'priority',
    'sec-fetch-dest', 'sec-fetch-mode', 'sec-fetch-site',
)
PC_LIVE_GET_HEADER_ORDER = (
    'referer', 'xy-common-params', 'x-t', 'x-s-common',
    'x-ratelimit-meta', 'accept', 'x-s', 'user-agent', 'accept-encoding',
    'accept-language', 'cookie', 'origin', 'priority', 'sec-fetch-dest',
    'sec-fetch-mode', 'sec-fetch-site',
)
PC_RAP_POST_HEADER_ORDER = (
    'referer', 'x-xray-traceid', 'x-t', 'x-b3-traceid', 'x-s-common',
    'x-rap-param', 'accept', 'content-type', 'x-s', 'user-agent',
    'accept-encoding', 'accept-language', 'cookie', 'origin', 'priority',
    'sec-fetch-dest', 'sec-fetch-mode', 'sec-fetch-site',
)
PC_XY_RAP_POST_HEADER_ORDER = (
    # Chrome's homefeed/feed requests place the sharding header first.
    'xy-direction', 'referer', 'x-xray-traceid', 'x-t', 'x-b3-traceid',
    'x-s-common', 'x-rap-param', 'accept', 'content-type', 'x-s',
    'user-agent', 'accept-encoding', 'accept-language', 'cookie', 'origin',
    'priority', 'sec-fetch-dest', 'sec-fetch-mode', 'sec-fetch-site',
)
PC_RAP_GET_HEADER_ORDER = (
    'referer', 'x-xray-traceid', 'x-t', 'x-b3-traceid', 'x-s-common',
    'x-rap-param', 'user-agent', 'accept', 'x-s', 'accept-encoding',
    'accept-language', 'cookie', 'origin', 'priority', 'sec-fetch-dest',
    'sec-fetch-mode', 'sec-fetch-site',
)


def resolve_mns_tier(api: str, fingerprint_ready: bool = True) -> str:
    """按接口解析 mnsv2 档位（实测规律见 ``state.PcDeviceProfile``）。

    - fingerprint/webprofile 已就绪：全部请求（含 scripting）→ mns0301
    - 未就绪的反爬安全域（/api/sec/v1/*、/api/redcaptcha/*、sem_sdk）→ mns0201
    - 未就绪的内容接口 → mns0101

    生产路径应优先由 PcDeviceProfile.resolve_mns_tier() 结合会话状态选择。
    """
    a = str(api or '')
    if fingerprint_ready:
        return '0301'
    if '/api/sec/v1/' in a or '/api/redcaptcha/' in a or 'sem_sdk' in a:
        return '0201'
    return '0101'


def generate_x_b3_traceid(len=16):
    x_b3_traceid = ""
    for t in range(len):
        x_b3_traceid += "abcdef0123456789"[math.floor(16 * random.random())]
    return x_b3_traceid

_BASE36_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"

def _int_to_base36(value):
    if value == 0:
        return "0"
    result = ""
    while value:
        value, remainder = divmod(value, 36)
        result = _BASE36_CHARS[remainder] + result
    return result

def generate_search_id(root_search_id=None):
    if root_search_id:
        return root_search_id
    timestamp_ms = int(time.time() * 1000)
    random_part = math.ceil(0x7ffffffe * random.random())
    return _int_to_base36((timestamp_ms << 64) + random_part)

def generate_search_request_id():
    timestamp_ms = int(time.time() * 1000)
    random_part = math.ceil(0x7ffffffe * random.random())
    return f"{random_part}-{timestamp_ms}"


def generate_search_session_id():
    """Current `/v2/search/notes` session_id is a UUIDv4.

    This is distinct from the legacy numeric `request_id` used by user search.
    """
    return str(uuid.uuid4())


def generate_xs(
    a1, api, data='', method='POST', *, cookie='', tier=None,
    sign_context=None,
):
    """Generate X-s/X-t for endpoints that do not send X-S-Common.

    蒲公英等接口只携带 X-s/X-t，因此不应伪造 b1 或 dsl_pair。MNS 环境和
    会话计数仍必须由 PcDeviceProfile.next_sign_context() 显式提供。
    """
    del method  # method does not participate in the current browser signer
    if not cookie or 'a1=' not in cookie:
        raise ValueError('generate_xs: cookie 须含 a1')
    if not sign_context:
        raise ValueError('generate_xs: sign_context 必传')
    from .runtime import run_signer

    resolved_tier = tier or sign_context.get('tier') or resolve_mns_tier(api)
    result = run_signer(
        api,
        data,
        a1=a1,
        cookie=cookie,
        b1='',
        dsl_pair='',
        tier=resolved_tier,
        sign_context=sign_context,
    )
    if not result or not result.get('xs'):
        raise RuntimeError(f'JS X-s 生成失败（档位 mns{resolved_tier}_）')
    return result['xs'], result.get('xt') or str(int(time.time() * 1000))

def generate_xs_xs_common(
    a1, api, data='', method='POST', b1=None, dsl_pair=None, cookie='', tier=None,
    sign_context=None,
):
    """
    生成 X-s / X-t / X-S-Common。算法唯一实现位于 ``js/``，Python 只负责调用。
    不加载任何 VM / 混淆 bundle。必须显式传入 cookie（含 a1）、b1、dsl_pair。
    浏览器登录冷链的 b1 是空字符串，因此只禁止 ``None``，不禁止 ``''``。
    sign_context 由 PcDeviceProfile.next_sign_context() 生成，包含会话与环境动态字段。
    """
    if not cookie or 'a1=' not in cookie:
        raise ValueError('generate_xs_xs_common: cookie(document.cookie 含 a1) 必传')
    if b1 is None:
        raise ValueError('generate_xs_xs_common: b1 必须显式传入（允许空字符串）')
    if not dsl_pair or ';' not in str(dsl_pair):
        raise ValueError('generate_xs_xs_common: dsl_pair 必传，格式 dsllt;_dsl')

    from .runtime import run_signer
    if not sign_context:
        raise ValueError('generate_xs_xs_common: sign_context 必传（PcDeviceProfile 会话状态）')
    tier = tier or sign_context.get('tier') or resolve_mns_tier(api)
    node_ret = run_signer(
        api, data, a1=a1, cookie=cookie, b1=b1, dsl_pair=dsl_pair, tier=tier,
        sign_context=sign_context,
    )
    if not node_ret or not node_ret.get('xs'):
        raise RuntimeError(
            f'JS mnsv2 签名失败或未达到硬门禁（档位 mns{tier}_，无短签/静态兜底）'
        )
    xs = node_ret['xs']
    xt = node_ret.get('xt') or str(int(time.time() * 1000))
    xs_common = node_ret.get('xs_common')
    if not xs_common:
        raise RuntimeError('JS X-S-Common 生成失败（缺 b1/dsl_pair 或运行时异常）')
    return xs, xt, xs_common

_xray_seq = [int(random.random() * 0x7fffff)]

def generate_xray_traceid():
    """本地生成 x-xray-traceid（还原自 xhs_xray.js traceId）：
    hex16((now_ms<<23)|seq) + hex16(random64)。追踪头，不参与签名校验。"""
    now_ms = int(time.time() * 1000)
    _xray_seq[0] = (_xray_seq[0] + 1) & 0x7fffff
    part1 = format(((now_ms << 23) | _xray_seq[0]) & 0xffffffffffffffff, 'x').rjust(16, '0')
    rnd = (random.getrandbits(32) << 32) | random.getrandbits(32)
    part2 = format(rnd, 'x').rjust(16, '0')
    return part1 + part2

_RAP_CLI = os.path.join(os.path.dirname(__file__), 'js', 'rap_cli.js')

def generate_x_rap_param(api, data, app_id=None, fingerprint_hex: str = ''):
    """生成 x-rap-param；算法唯一实现位于 ``js/rap.js``。

    Python 仅做输入序列化、Node 调用和输出门禁：
      - Xorkeyverifyvalue = xxHash32([mask], 0)
      - RequestHash       = xxHash32(url + body, 0)
      - 随机 ASCII         = alphabet36[byte % 36] (nonce/xorKey/uuidStr)
      - 加密层             = AES-128-ECB(自研S-box, 固定密钥"kqI1DTcwKX90ZtAy") + gzip + XOR + 信封
      - 指纹 ~219B         = 采集模板（同 mns envConst/envFpTail 思路，一次采集永久用）
    2026-07-16 实发验证：homefeed 逐字节对齐浏览器（273/273 字节）。
    """
    import subprocess as _sp
    import json as _json
    body = data if isinstance(data, str) else _json.dumps(data or {}, ensure_ascii=False)
    argv = ['node', _RAP_CLI, api, body]
    if app_id:
        argv.append(app_id)
    elif fingerprint_hex:
        argv.append('')
    if fingerprint_hex:
        argv.append(fingerprint_hex)
    try:
        r = _sp.run(
            argv, capture_output=True, text=True,
            cwd=os.path.dirname(_RAP_CLI), timeout=30,
        )
        out = (r.stdout or '').strip()
        if out and out.startswith('ByQ'):
            return out
    except (OSError, _sp.TimeoutExpired):
        pass
    raise RuntimeError('JS x-rap-param 生成失败')

def get_common_headers():
    return {
        'upgrade-insecure-requests': '1',
        'user-agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/155.0.0.0 Safari/537.36'
        ),
        'sec-ch-ua': PC_SEC_CH_UA,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,'
            'image/avif,image/webp,image/apng,*/*;q=0.8,'
            'application/signed-exchange;v=b3;q=0.7'
        ),
        'accept-language': PC_LOGIN_ACCEPT_LANGUAGE,
        'priority': 'u=0, i',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
    }
def generate_xy_direction(user_id: str) -> int:
    """
    PC 端 xy-direction = murmurHash3_32(userId, 151488) % 100 + 1
    结果会缓存到 localStorage.xhs_sharding_key
    """
    if not user_id:
        return 0
    return murmur_hash3_32(user_id, 151488) % 100 + 1


def _string_to_utf8_bytes(s: str):
    return list(s.encode('utf-8'))


def murmur_hash3_32(key: str, seed: int = 0) -> int:
    """对齐小红书 index.bundle 中的 murmurHash3_32"""
    data = _string_to_utf8_bytes(key)
    length = len(data)
    h = seed & 0xffffffff
    nblocks = length // 4

    for i in range(nblocks):
        k = (data[4*i]
             | (data[4*i+1] << 8)
             | (data[4*i+2] << 16)
             | (data[4*i+3] << 24)) & 0xffffffff
        k = (k * 0xcc9e2d51) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * 0x1b873593) & 0xffffffff
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = (h * 5 + 0xe6546b64) & 0xffffffff

    tail_index = 4 * nblocks
    k = 0
    rem = length % 4
    if rem == 3:
        k ^= data[tail_index + 2] << 16
    if rem >= 2:
        k ^= data[tail_index + 1] << 8
    if rem >= 1:
        k ^= data[tail_index]
        k = (k * 0xcc9e2d51) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * 0x1b873593) & 0xffffffff
        h ^= k

    h ^= length
    h ^= (h >> 16)
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= (h >> 13)
    h = (h * 0xc2b2ae35) & 0xffffffff
    h ^= (h >> 16)
    return h


def get_request_headers_template(
    sign_context=None,
    *,
    method='POST',
    accept_language=PC_BUSINESS_ACCEPT_LANGUAGE,
    has_body=None,
    include_client_hints=True,
    include_trace_headers=True,
):
    context = sign_context or {}
    user_agent = context.get(
        'userAgent',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36',
    )
    headers = {
        'referer': 'https://www.xiaohongshu.com/',
        'x-t': '',
        'x-s-common': '',
        'user-agent': user_agent,
        'accept': 'application/json, text/plain, */*',
        'x-s': '',
        'accept-language': str(accept_language),
        'origin': 'https://www.xiaohongshu.com',
        'priority': 'u=1, i',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
    }
    if include_trace_headers:
        headers['x-xray-traceid'] = generate_xray_traceid()
        headers['x-b3-traceid'] = ''
    if include_client_hints:
        headers['sec-ch-ua-platform'] = '"Windows"'
        headers['sec-ch-ua'] = context.get('secChUa', PC_SEC_CH_UA)
        headers['sec-ch-ua-mobile'] = '?0'
    if has_body is None:
        has_body = str(method).upper() != 'GET'
    if has_body:
        headers['content-type'] = 'application/json;charset=UTF-8'
    return headers


def build_pc_navigation_headers(headers, cookies=None):
    return ordered_wire_headers(
        headers,
        order=PC_NAVIGATION_HEADER_ORDER,
        cookies=cookies,
        optional=('cookie',),
    )


def build_pc_login_headers(headers, cookies=None, *, kind='post'):
    if kind == 'honeypot':
        order = PC_HONEYPOT_HEADER_ORDER
    elif kind == 'security':
        order = PC_SECURITY_HEADER_ORDER
    elif kind == 'sem':
        order = PC_SEM_HEADER_ORDER
    elif kind == 'get':
        order = PC_SIGNED_GET_HEADER_ORDER
    elif kind == 'get-login-mode':
        order = (
            'sec-ch-ua-platform', 'x-login-mode',
        ) + PC_SIGNED_GET_HEADER_ORDER[1:]
    else:
        order = PC_SIGNED_POST_HEADER_ORDER
    if 'content-type' not in {str(key).lower() for key in headers}:
        order = tuple(key for key in order if key != 'content-type')
    return ordered_wire_headers(headers, order=order, cookies=cookies)


def build_pc_business_headers(headers, cookies, *, api, method='POST'):
    upper_method = str(method).upper()
    has_rap = 'x-rap-param' in {str(key).lower() for key in headers}
    has_xy = 'xy-direction' in {str(key).lower() for key in headers}
    has_client_hints = 'sec-ch-ua-platform' in {str(key).lower() for key in headers}
    has_device_header = 'c_device_id' in {str(key).lower() for key in headers}
    if not has_client_hints and has_device_header:
        order = PC_BUSINESS_CDEVICE_GET_HEADER_ORDER
    elif not has_client_hints and has_xy:
        order = PC_XY_RAP_POST_HEADER_ORDER
    elif not has_client_hints and has_rap and upper_method == 'GET':
        order = PC_RAP_GET_HEADER_ORDER
    elif not has_client_hints and has_rap:
        order = PC_RAP_POST_HEADER_ORDER
    elif not has_client_hints and not has_rap and not has_xy:
        order = (
            PC_BUSINESS_SIGNED_GET_HEADER_ORDER
            if upper_method == 'GET'
            else PC_BUSINESS_SIGNED_POST_HEADER_ORDER
        )
    elif has_xy:
        order = PC_XY_RAP_POST_HEADER_ORDER
    elif has_rap and upper_method == 'GET':
        order = PC_RAP_GET_HEADER_ORDER
    elif has_rap:
        order = PC_RAP_POST_HEADER_ORDER
    elif upper_method == 'GET':
        order = PC_SIGNED_GET_HEADER_ORDER
    else:
        order = PC_SIGNED_POST_HEADER_ORDER
    if 'content-type' not in {str(key).lower() for key in headers}:
        order = tuple(key for key in order if key != 'content-type')
    # Message-page bootstrap captures include these cache controls in this
    # exact relative position.
    lower_keys = {str(key).lower() for key in headers}
    order = list(order)
    if 'cache-control' in lower_keys and 'cache-control' not in order:
        anchor = order.index('cookie') if 'cookie' in order else order.index('origin')
        order.insert(anchor, 'cache-control')
    if 'pragma' in lower_keys and 'pragma' not in order:
        anchor = order.index('priority') if 'priority' in order else len(order)
        order.insert(anchor, 'pragma')
    return ordered_wire_headers(
        headers,
        order=tuple(order),
        cookies=cookies,
    )


def build_pc_live_headers(headers, cookies, *, method='POST'):
    """Build the separate live-room header contract captured in Chrome.

    Live-room requests currently omit client-hint and trace headers.  The
    live page places ``xy-common-params`` immediately after the referer and
    ``x-ratelimit-meta`` before ``accept``.
    """
    order = PC_LIVE_GET_HEADER_ORDER if str(method).upper() == 'GET' else PC_LIVE_POST_HEADER_ORDER
    if 'content-type' not in {str(key).lower() for key in headers}:
        order = tuple(key for key in order if key != 'content-type')
    return ordered_wire_headers(
        headers,
        order=order,
        cookies=cookies,
        optional=('xy-common-params', 'x-ratelimit-meta'),
    )

def generate_headers(
    a1, api, data='', method='POST', user_id: str = '', cookie: str = '',
    b1=None, dsl_pair=None, with_xy_direction: bool = False,
    tier=None, sign_context=None,
    include_client_hints=True, include_trace_headers=True,
):
    # user_id 用于可选 xy-direction；签名材料仍强制在 generate_xs_xs_common / generate_request_params 校验
    xs, xt, xs_common = generate_xs_xs_common(
        a1, api, data, method, b1=b1, dsl_pair=dsl_pair, cookie=cookie, tier=tier,
        sign_context=sign_context,
    )
    x_b3_traceid = generate_x_b3_traceid()
    headers = get_request_headers_template(
        sign_context,
        method=method,
        has_body=data not in ('', None),
        include_client_hints=include_client_hints,
        include_trace_headers=include_trace_headers,
    )
    headers['x-s'] = xs
    headers['x-t'] = str(xt)
    headers['x-s-common'] = xs_common
    headers['x-b3-traceid'] = x_b3_traceid
    # 浏览器实抓：仅 homefeed / feed 带 xy-direction
    if with_xy_direction:
        if not user_id:
            raise ValueError('generate_headers: 该接口需要 xy-direction，user_id 必传')
        headers['xy-direction'] = str(generate_xy_direction(user_id))
    if data == '' or data is None:
        data = ''
    elif isinstance(data, str):
        data = data
    else:
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return headers, data

def generate_request_params(
    cookies_str, api, data='', method='POST', user_id: str = '', b1=None,
    dsl_pair=None, doc_cookie: str = '', with_xy_direction: bool = False,
    tier=None, sign_context=None,
    include_client_hints=True, include_trace_headers=True,
):
    # Network Cookie 已含 a1 时可直接复用，不必再传一份 document.cookie
    sign_cookie = doc_cookie or cookies_str
    if not sign_cookie or 'a1=' not in sign_cookie:
        raise ValueError('generate_request_params: cookies 须含 a1（Network Cookie 或 document.cookie）')
    if b1 is None:
        raise ValueError('generate_request_params: b1 必须显式传入（允许空字符串）')
    if not dsl_pair or ';' not in str(dsl_pair):
        raise ValueError('generate_request_params: dsl_pair 必传')
    # user_id 仅在需要 xy-direction 时强制；其余接口可后置 bootstrap
    if with_xy_direction and not user_id:
        raise ValueError('generate_request_params: 该接口需要 xy-direction，user_id 必传')
    cookies = trans_cookies(cookies_str)
    if 'a1' not in cookies:
        raise ValueError('generate_request_params: cookies_str 须含 a1')
    a1 = cookies['a1']
    headers, data = generate_headers(
        a1, api, data, method, user_id=user_id,
        cookie=sign_cookie, b1=b1, dsl_pair=dsl_pair,
        with_xy_direction=with_xy_direction, tier=tier, sign_context=sign_context,
        include_client_hints=include_client_hints,
        include_trace_headers=include_trace_headers,
    )
    return headers, cookies, data

def splice_str(api, params):
    return api + '?' + urlencode(
        {key: '' if value is None else value for key, value in params.items()},
        doseq=True
    )


__all__ = [
    'resolve_mns_tier',
    'generate_x_b3_traceid',
    'generate_search_id',
    'generate_search_request_id',
    'generate_search_session_id',
    'generate_xs',
    'generate_xs_xs_common',
    'generate_xray_traceid',
    'generate_x_rap_param',
    'get_common_headers',
    'PC_LOGIN_ACCEPT_LANGUAGE',
    'PC_BUSINESS_ACCEPT_LANGUAGE',
    'PC_SEC_CH_UA',
    'PC_CURRENT_BROWSER_UA',
    'build_pc_navigation_headers',
    'build_pc_login_headers',
    'build_pc_business_headers',
    'build_pc_live_headers',
    'generate_xy_direction',
    'murmur_hash3_32',
    'get_request_headers_template',
    'generate_headers',
    'generate_request_params',
    'splice_str',
]
