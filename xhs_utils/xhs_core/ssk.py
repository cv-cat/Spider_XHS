"""Web/App 共用的账号 SSK 原语（X25519 + AES-256-GCM）。

溯源与真机验证记录见 ``apis/app/research/ssk.md``（App 9.43.1 的
X25519KeyExchange / AccountSskClient / dcb.a）。登录链在
``apis/xhs_pc_login_apis.py`` 使用；独立成模块是为了不依赖未发布的
``apis/app`` 包。
"""

from __future__ import annotations

import base64
import re
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 公开协议常量（App 9.43.1 X25519KeyExchange）。web 端实测同钥（2026-10-17）。
SERVER_PUBLIC_KEY_9_43_1 = bytes.fromhex(
    "2abd22ca0b02bb78a760935708be24e09bb369843669f235c5bc1cec11fab26f"
)

_CANONICAL_B64_80 = re.compile(r'^[A-Za-z0-9+/]{79}=$')


def generate_private_key() -> bytes:
    """32 随机字节并按 X25519 约定钳位（App Java 实现同款）。"""
    private = bytearray(secrets.token_bytes(32))
    private[0] &= 248
    private[31] = (private[31] & 127) | 64
    return bytes(private)


def public_key(private_key: bytes) -> bytes:
    return X25519PrivateKey.from_private_bytes(private_key).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def public_key_base64(private_key: bytes) -> str:
    """44 字符标准 base64、保留单个填充、无换行（Android NO_WRAP）。"""
    return base64.b64encode(public_key(private_key)).decode("ascii")


def shared_secret(private_key: bytes, peer_public_key: bytes) -> bytes:
    private = X25519PrivateKey.from_private_bytes(private_key)
    peer = X25519PublicKey.from_public_bytes(peer_public_key)
    try:
        shared = private.exchange(peer)
    except ValueError:
        raise ValueError("invalid X25519 peer/shared secret") from None
    if shared == bytes(32):
        raise ValueError("invalid X25519 peer/shared secret")
    return shared


def decrypt_ssk(private_key: bytes, encrypted: bytes, *, server_public_key: bytes) -> bytes:
    """解 nonce[12] || ciphertext[32] || GCM tag[16]；无 AAD、无 KDF。"""
    if len(encrypted) != 60:
        raise ValueError("encrypted 32-byte SSK must contain exactly 60 bytes")
    key = shared_secret(private_key, server_public_key)
    try:
        return AESGCM(key).decrypt(encrypted[:12], encrypted[12:], None)
    except InvalidTag:
        raise ValueError("SSK authentication failed") from None


def decrypt_ssk_base64(private_key: bytes, encrypted_base64: str, *, server_public_key: bytes) -> str:
    """要求规范 80 字符 base64（拒绝换行/非规范填充）。"""
    if not isinstance(encrypted_base64, str) or not _CANONICAL_B64_80.fullmatch(encrypted_base64):
        raise ValueError("encrypted SSK must be canonical 80-char base64")
    ssk = decrypt_ssk(private_key, base64.b64decode(encrypted_base64),
                      server_public_key=server_public_key)
    return base64.b64encode(ssk).decode("ascii")
