"""密码安全处理（隔离在本模块，其他模块不得自行实现哈希逻辑）。

方案：secrets 生成随机盐 + hashlib.pbkdf2_hmac 派生哈希 + hmac.compare_digest 定时比较。
明文密码既不落盘也不进日志。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from backend_zhang import config


def generate_salt() -> str:
    """生成随机盐值（十六进制字符串）。"""
    return secrets.token_hex(config.SALT_BYTES)


def hash_password(password: str, salt: str) -> str:
    """使用 PBKDF2-HMAC 派生密码哈希。"""
    derived = hashlib.pbkdf2_hmac(
        config.PBKDF2_ALGORITHM,
        str(password).encode("utf-8"),
        str(salt).encode("utf-8"),
        config.PBKDF2_ITERATIONS,
    )
    return derived.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """校验密码是否匹配已保存的哈希（定时安全比较）。"""
    if not salt or not expected_hash:
        return False
    actual = hash_password(password, salt)
    return hmac.compare_digest(actual, str(expected_hash))
