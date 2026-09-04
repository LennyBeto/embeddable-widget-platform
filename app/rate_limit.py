from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def widget_id_key(request: Request) -> str:
    """Per-widget rate limit key: combine widget id (path param) + client IP.
    This lets us apply BOTH a per-IP and a per-widget ceiling on the same route
    by stacking two @limiter.limit(...) decorators with different key funcs."""
    widget_id = request.path_params.get("widget_id", "unknown")
    return f"widget:{widget_id}"


limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
widget_limiter = Limiter(key_func=widget_id_key, storage_uri=settings.redis_url)
