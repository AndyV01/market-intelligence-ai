import time

_cache = {}

def get_cached(key):
    data = _cache.get(key)
    if not data:
        return None

    value, expire_at = data

    if expire_at and time.time() > expire_at:
        del _cache[key]
        return None

    return value


def set_cache(key, value, ex: int = 60):
    expire_at = time.time() + ex if ex else None
    _cache[key] = (value, expire_at)