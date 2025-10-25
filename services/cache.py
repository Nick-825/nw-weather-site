import time
from functools import wraps

def ttl_cache(ttl_seconds=600):
    def decorator(fn):
        cache = {"value": None, "ts": 0}
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = time.time()
            if cache["value"] is None or now - cache["ts"] > ttl_seconds:
                cache["value"] = fn(*args, **kwargs)
                cache["ts"] = now
            return cache["value"]
        return wrapper
    return decorator
