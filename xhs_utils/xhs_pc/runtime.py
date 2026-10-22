# encoding: utf-8
"""Node runtime adapter for the XHS PC JavaScript algorithms.

Shared cryptographic/signature algorithms live under
:mod:`xhs_utils.xhs_core.js`（唯一来源）；本目录仅保留 PC 特有模板
（profile/rap 等）。This module only validates Python inputs, invokes Node,
and validates outputs; it intentionally does not maintain a second Python
implementation.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from typing import Any, Mapping, Optional


_JS_DIR = os.path.join(os.path.dirname(__file__), 'js')
_CORE_JS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'xhs_core', 'js',
)
_B1_JS = os.path.join(_CORE_JS_DIR, 'b1.js')
_SIGN_JS = os.path.join(_CORE_JS_DIR, 'sign.js')
_WEBSECTIGA_CLI = os.path.join(_CORE_JS_DIR, 'websectiga_cli.js')
_PROFILE_JS = os.path.join(_JS_DIR, 'profile.js')
_WEB_SSK_JS = os.path.join(_JS_DIR, 'web_ssk.js')

_TIER_GATE = {
    '0101': ('mns0101_', 205),
    '0201': ('mns0201_', 208),
    '0301': ('mns0301_', 200),
}
_WEBSECTIGA_RE = re.compile(r'^[0-9a-f]{64}$', re.I)
_PROFILE_DATA_RE = re.compile(r'^[0-9a-f]{10000,200000}$', re.I)


def generate_b1(
    options: Optional[Mapping[str, Any]] = None,
    timeout: float = 10.0,
) -> str:
    """Generate b1 from an explicit 19-field browser-state snapshot."""
    if not os.path.isfile(_B1_JS):
        raise RuntimeError(f'b1 algorithm missing: {_B1_JS}')
    payload = json.dumps(dict(options or {}), ensure_ascii=False, separators=(',', ':'))
    try:
        proc = subprocess.run(
            ['node', _B1_JS, '--generate', payload],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_JS_DIR,
            encoding='utf-8',
            errors='replace',
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'b1 runtime failed to start: {exc}') from exc
    if proc.returncode != 0:
        raise RuntimeError(f'b1 runtime failed: {(proc.stderr or proc.stdout).strip()}')
    try:
        value = str(json.loads(proc.stdout.strip())['b1'])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(f'b1 runtime output invalid: {proc.stdout[:300]}') from exc
    if len(value) < 500 or len(value) % 4:
        raise RuntimeError(f'b1 length invalid: {len(value)}')
    return value


def run_signer(
    api: str,
    data: Any = '',
    *,
    a1: str,
    cookie: str,
    b1: Optional[str],
    dsl_pair: str,
    tier: str,
    sign_context: Mapping[str, Any],
    timeout: float = 30.0,
) -> Optional[dict]:
    """Run the JS signing core and enforce the selected MNS tier gate."""
    if not os.path.isfile(_SIGN_JS) or not cookie or 'a1=' not in cookie:
        return None
    if tier not in _TIER_GATE:
        return None
    context = dict(sign_context or {})
    required = ('loadts', 'seq', 'envConst', 'envFpTail', 'webBuild')
    if not all(key in context for key in required):
        return None

    payload = {
        'api': api,
        'data': data,
        'cookie': cookie,
        'a1': a1,
        # Empty b1 is the browser's real cold-login state. ``None`` remains
        # reserved for callers that failed to provide the field explicitly.
        'b1': '' if b1 is None else str(b1),
        'dslPair': dsl_pair,
        'tier': tier,
    }
    for key in (
        'now', 'version', 'loadts', 'seq', 'envConst', 'envFpTail', 'webBuild',
        'signVersion', 'appId', 'platform', 'deviceTag', 'webSsk',
    ):
        if key in context:
            payload[key] = context[key]

    # Windows CreateProcess 命令行约 32K 上限；webprofile 一类大 body
    # （profileData 36K hex）必须走 @file 间接传参，否则 WinError 206。
    arg = json.dumps(payload, ensure_ascii=False)
    sign_arg = arg if len(arg) <= 8000 else None
    tmp_path = None
    if sign_arg is None:
        fd, tmp_path = tempfile.mkstemp(prefix='xhs_sign_', suffix='.json')
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(arg)
        sign_arg = '@' + tmp_path
    try:
        proc = subprocess.run(
            ['node', _SIGN_JS, sign_arg],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_JS_DIR,
            encoding='utf-8',
            errors='replace',
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    if proc.returncode != 0:
        return None

    required_prefix, required_length = _TIER_GATE[tier]
    for line in reversed([
        item.strip() for item in (proc.stdout or '').splitlines() if item.strip()
    ]):
        if not line.startswith('{') or '"x3"' not in line:
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            continue
        x3 = str(result.get('x3') or '')
        if (
            result.get('xs')
            and x3.startswith(required_prefix)
            and len(x3) == required_length
        ):
            result['len'] = len(x3)
            result['prefix'] = x3[:12]
            return result
        return None
    return None


def _run_web_ssk(payload: Mapping[str, Any], timeout: float = 10.0) -> dict:
    if not os.path.isfile(_WEB_SSK_JS):
        raise RuntimeError(f'webSsk helper missing: {_WEB_SSK_JS}')
    try:
        proc = subprocess.run(
            ['node', _WEB_SSK_JS, json.dumps(dict(payload), separators=(',', ':'))],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_JS_DIR,
            encoding='utf-8',
            errors='replace',
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'webSsk helper failed to start: {exc}') from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f'webSsk helper failed: {(proc.stderr or proc.stdout).strip()[:500]}'
        )
    try:
        result = json.loads(proc.stdout.strip())
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(f'webSsk helper output invalid: {proc.stdout[:300]}') from exc
    if not isinstance(result, dict):
        raise RuntimeError('webSsk helper output must be an object')
    return result


def create_web_ssk_handshake(timeout: float = 10.0) -> dict:
    """Generate the ephemeral X25519 keypair used by PC login activation."""
    result = _run_web_ssk({'action': 'create'}, timeout=timeout)
    if not result.get('private_key_base64') or not result.get('client_public_key_base64'):
        raise RuntimeError('webSsk handshake output is missing key material')
    return result


def accept_web_ssk(
    private_key_base64: str,
    encrypted_ssk_base64: str,
    timeout: float = 10.0,
) -> str:
    """Decrypt the activation response SSK with X25519 + AES-256-GCM."""
    result = _run_web_ssk({
        'action': 'accept',
        'private_key_base64': str(private_key_base64),
        'encrypted_ssk_base64': str(encrypted_ssk_base64),
    }, timeout=timeout)
    value = str(result.get('ssk_base64') or '')
    if not value:
        raise RuntimeError('webSsk acceptance returned an empty secret')
    return value


def generate_websectiga(
    scripting_code: str,
    *,
    profile: Optional[Mapping[str, Any]] = None,
    timeout: float = 20.0,
) -> str:
    """Execute a server-issued scripting program and return websectiga."""
    code = str(scripting_code or '')
    if len(code) < 1000:
        raise ValueError('scripting code is empty or truncated')
    if not os.path.isfile(_WEBSECTIGA_CLI):
        raise RuntimeError(f'websectiga runtime missing: {_WEBSECTIGA_CLI}')

    values = dict(profile or {})
    payload = {
        'code': code,
        'userAgent': values.get('userAgent', ''),
        'platform': values.get('platform', 'Win32'),
        'pageUrl': values.get(
            'pageUrl',
            'https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend',
        ),
        'timeoutMs': int(max(1000, timeout * 1000 * 0.75)),
    }
    try:
        proc = subprocess.run(
            ['node', _WEBSECTIGA_CLI],
            input=json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_JS_DIR,
            encoding='utf-8',
            errors='replace',
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'websectiga runtime failed to start: {exc}') from exc
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or '').strip()
        raise RuntimeError(f'websectiga runtime failed: {message[:500]}')

    for line in (proc.stdout or '').splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            continue
        token = str(result.get('websectiga') or '')
        if _WEBSECTIGA_RE.fullmatch(token):
            return token
    raise RuntimeError(f'websectiga runtime output invalid: {(proc.stdout or "")[:300]}')


def generate_profile_data(
    *,
    fields: Optional[Mapping[str, Any]] = None,
    timestamp_ms: Optional[int] = None,
    ets: Optional[int] = None,
    document_cookie: Optional[str] = None,
    time_origin: Optional[float] = None,
    i12_seed: Optional[int] = None,
    telemetry_fi: Optional[int] = None,
    exact_fields: bool = False,
    timeout: float = 10.0,
) -> str:
    """Pure-calculate PC ``profileData`` from explicit fingerprint fields.

    Node only performs deterministic field assembly, UTF-8/Base64 encoding,
    DES-ECB zero-padding encryption and hexadecimal serialization.  It does not
    construct browser objects or execute the original fingerprint SDK.
    """
    if not os.path.isfile(_PROFILE_JS):
        raise RuntimeError(f'profileData algorithm missing: {_PROFILE_JS}')
    payload: dict[str, Any] = {'fields': dict(fields or {})}
    if exact_fields:
        payload['exactFields'] = True
    if timestamp_ms is not None:
        payload['timestampMs'] = int(timestamp_ms)
    if ets is not None:
        payload['ets'] = int(ets)
    if document_cookie is not None:
        payload['documentCookie'] = str(document_cookie)
    if time_origin is not None:
        payload['timeOrigin'] = float(time_origin)
    if i12_seed is not None:
        payload['i12Seed'] = int(i12_seed)
    if telemetry_fi is not None:
        payload['telemetryFi'] = int(telemetry_fi)
    try:
        proc = subprocess.run(
            [
                'node',
                _PROFILE_JS,
                json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_JS_DIR,
            encoding='utf-8',
            errors='replace',
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'profileData runtime failed to start: {exc}') from exc
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or '').strip()
        raise RuntimeError(f'profileData runtime failed: {message[:500]}')

    for line in reversed((proc.stdout or '').splitlines()):
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            continue
        value = str(result.get('profileData') or '')
        if (
            result.get('sdkVersion') == '4.4.3'
            and int(result.get('length') or 0) == len(value)
            and result.get('algorithm') == 'base64-des-ecb-zero-padding-hex'
            and _PROFILE_DATA_RE.fullmatch(value)
        ):
            return value
    raise RuntimeError(f'profileData runtime output invalid: {(proc.stdout or "")[:300]}')


__all__ = [
    'generate_b1',
    'run_signer',
    'generate_websectiga',
    'generate_profile_data',
    'create_web_ssk_handshake',
    'accept_web_ssk',
]

