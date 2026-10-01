import hashlib
import secrets

KEY_PREFIX = "agsk_"


def hash_agent_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_agent_key() -> tuple[str, str]:
    key = KEY_PREFIX + secrets.token_urlsafe(32)
    return key, hash_agent_key(key)