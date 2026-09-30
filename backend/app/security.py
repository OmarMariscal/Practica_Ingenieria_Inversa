import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app import config

_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, digest = stored.split("$")
        candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), **_SCRYPT)
        return hmac.compare_digest(candidate.hex(), digest)
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.TOKEN_TTL_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, config.SECRET_KEY, algorithm="HS256")


def read_token(token: str) -> int | None:
    try:
        return int(jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
