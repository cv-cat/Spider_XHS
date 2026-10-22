"""Fetch the server-issued ``window._dsl`` anchor for an explicit Web appId."""

from __future__ import annotations

import re
import threading
import time
from typing import Optional


_GETDSS_RE = re.compile(r"function\s+getdss\s*\(\s*\)\s*\{\s*return\s+'(\d+)'")
_TTL = 300


class DsFetcher:
    def __init__(
        self,
        app_id: str,
        *,
        referer: str,
        ttl: int = _TTL,
    ) -> None:
        self.app_id = str(app_id)
        self.referer = str(referer)
        self._ttl = int(ttl)
        self._value: Optional[str] = None
        self._program: Optional[str] = None
        self._fetched_at = 0.0
        self._lock = threading.Lock()

    @property
    def url(self) -> str:
        return f'https://as.xiaohongshu.com/api/sec/v1/ds?appId={self.app_id}'

    def get(self, proxies: Optional[dict] = None, force: bool = False) -> str:
        return self.get_bundle(proxies=proxies, force=force)[0]

    def get_bundle(
        self,
        proxies: Optional[dict] = None,
        force: bool = False,
        http_client=None,
    ) -> tuple[str, str]:
        """Return the server anchor and its DS program from one cached fetch."""
        now = time.time()
        if (
            not force
            and self._value
            and self._program
            and now - self._fetched_at < self._ttl
        ):
            return self._value, self._program
        with self._lock:
            now = time.time()
            if (
                not force
                and self._value
                and self._program
                and now - self._fetched_at < self._ttl
            ):
                return self._value, self._program
            try:
                value, program = self._fetch(
                    proxies=proxies,
                    http_client=http_client,
                )
                self._value = value
                self._program = program
                self._fetched_at = now
                return value, program
            except Exception as exc:
                if self._value and self._program:
                    return self._value, self._program
                raise RuntimeError(
                    f'ds fetch failed for appId={self.app_id}: {exc}'
                ) from exc

    def _fetch(
        self,
        proxies: Optional[dict] = None,
        http_client=None,
    ) -> tuple[str, str]:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/155.0.0.0 Safari/537.36'
            ),
            'Referer': self.referer,
            'Accept': '*/*',
        }
        if http_client is None:
            import requests

            response = requests.get(
                self.url,
                headers=headers,
                proxies=proxies,
                timeout=8,
            )
        else:
            response = http_client.get(
                self.url,
                headers=headers,
                proxies=proxies,
                timeout=8,
            )
        response.raise_for_status()
        match = _GETDSS_RE.search(response.text)
        if not match:
            raise ValueError('ds response does not contain getdss()')
        if '_dsf' not in response.text and '__$c' not in response.text:
            raise ValueError('ds response does not contain the DS runtime program')
        return match.group(1), response.text

    def peek(self) -> Optional[str]:
        return self._value

    def peek_program(self) -> Optional[str]:
        return self._program


__all__ = ['DsFetcher']
