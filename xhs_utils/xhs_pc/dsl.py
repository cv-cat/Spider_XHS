# encoding: utf-8
"""
小红书 ds 接口（sec sdk 时间戳锚点）拉取器。

背景
====
XHS PC web 签名的 X-S-Common.x12 字段结构为 "<dsllt>;<_dsl>"：
  - dsllt = 本地 Date.now()（页面加载覆盖 localStorage.dsllt）
  - _dsl  = 服务端下发的伪时间戳（`window._dsl`）

_dsl 来源逆向确认
================
访问 https://as.xiaohongshu.com/api/sec/v1/ds?appId=xhs-pc-web，
接口返回 JS（obfuscator.io 混淆的 Sabo VMP），前几行明文：

    function getdss() { return '<13位时间戳>'; };
    var _0x341b=[...混淆字符串表...];
    var __$c='<VMP 字节码 hex>';
    glb['_BHjFmfUMEtxhI'](__$c, [,,undefined,Uint8Array,getdss])

VMP 内部把 `getdss()` 返回值直接写入 `window._dsl`。
在 Node V8 sandbox 里跑该 JS，能拿到：
  - window._dsl = "1783929625569"  ← 就是 getdss() 值
  - window._dsn = "a3"              ← 静态字符串
  - window._dsf = <function>        ← 某个签名相关闭包
  - window.__bc = "<字节码 hex>"    ← 内部复制

因此，_dsl 不属于本地算法参数：直接从 ds 接口提取 getdss() 值。

服务端行为
==========
  - cache-control: max-age=300 (5 分钟)
  - 不同 CDN 节点返回不同 getdss() 值（有 3 天前、3 周前等）
  - 服务端并非返回 Date.now()，而是某个"锚点时间戳"

策略
====
  - 首次调 API 前 fetch 一次，缓存到内存
  - 5 分钟内复用（浏览器一致行为）
  - 过期后重新 fetch
  - 失败时用上次值继续（不阻塞签名）
"""
from __future__ import annotations

import re
import time
import threading
from typing import Optional

_GETDSS_RE = re.compile(r"function\s+getdss\s*\(\s*\)\s*\{\s*return\s+'(\d+)'")
_DS_URL = "https://as.xiaohongshu.com/api/sec/v1/ds?appId=xhs-pc-web"
_TTL = 300  # 与服务端 max-age 对齐


class DsFetcher:
    """
    ds 接口 getdss() 值拉取 + 5 分钟内存缓存。

    - 线程安全（单进程内多线程共享 1 份缓存）
    - 缓存策略：命中即返回，未命中或过期则同步 fetch
    - 失败降级：fetch 失败时若有旧值则复用旧值 + 记 warn

    典型用法：
        dsl = get_dsl()
        # dsl_pair = str(int(time.time()*1000)) + ';' + dsl
    """

    def __init__(self, ttl: int = _TTL, url: str = _DS_URL):
        self._ttl = ttl
        self._url = url
        self._value: Optional[str] = None
        self._fetched_at: float = 0.0
        self._lock = threading.Lock()

    def get(
        self,
        proxies: Optional[dict] = None,
        force: bool = False,
        http_client=None,
    ) -> str:
        """
        拿 getdss() 值（=_dsl）。缓存命中直接返回，否则同步 fetch。

        Args:
            proxies: 可选，透传给 HTTP 客户端
            force:   强制刷新（跳过缓存）
            http_client: 可选，复用 Auth 的浏览器传输 Session

        Returns:
            13 位数字字符串
        """
        now = time.time()
        if not force and self._value and now - self._fetched_at < self._ttl:
            return self._value

        with self._lock:
            # 双重检查（多线程下另一线程可能刚 fetch 完）
            now = time.time()
            if not force and self._value and now - self._fetched_at < self._ttl:
                return self._value
            try:
                new_val = self._fetch(
                    proxies=proxies,
                    http_client=http_client,
                )
                self._value = new_val
                self._fetched_at = now
                return new_val
            except Exception as e:
                if self._value:
                    # 失败降级：返回旧值
                    return self._value
                raise RuntimeError(f'ds 接口首次 fetch 失败：{e}') from e

    def _fetch(
        self,
        proxies: Optional[dict] = None,
        http_client=None,
    ) -> str:
        """
        实际发请求 + 正则提 getdss() 值。
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/155.0.0.0 Safari/537.36',
            'Referer': 'https://www.xiaohongshu.com/',
            'Accept': '*/*',
        }
        if http_client is None:
            from .http import PcHttpClient

            client = PcHttpClient(proxies=proxies)
            try:
                r = client.get(
                    self._url,
                    headers=headers,
                    proxies=proxies,
                    timeout=8,
                )
            finally:
                client.close()
        else:
            r = http_client.get(
                self._url,
                headers=headers,
                proxies=proxies,
                timeout=8,
            )
        r.raise_for_status()
        m = _GETDSS_RE.search(r.text)
        if not m:
            raise ValueError('ds 响应未匹配 getdss() 模式')
        return m.group(1)

    def peek(self) -> Optional[str]:
        """不发请求，返回当前缓存值（可能为 None）。"""
        return self._value


# 模块级单例（与浏览器 window._dsl 语义对齐：一次页面一份）
_default = DsFetcher()


def get_dsl(
    proxies: Optional[dict] = None,
    force: bool = False,
    http_client=None,
) -> str:
    """
    模块级快捷接口，多数场景直接用这个。

    示例：
        from xhs_utils.xhs_pc.dsl import get_dsl
        _dsl = get_dsl()
    """
    return _default.get(
        proxies=proxies,
        force=force,
        http_client=http_client,
    )


# _dsn 是静态字符串，不需要拉接口（VMP 直接写入 "a3"）。
# 未来若 XHS 改版可能变，暂 hardcode。
DSN_STATIC = 'a3'
