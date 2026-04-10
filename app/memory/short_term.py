import redis

from app.core.config import settings


def _client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def session_key(user_id: str, character_id: int) -> str:
    return f"xianxia:chat:{user_id}:{character_id}"


def clear_session(user_id: str, character_id: int) -> None:
    r = _client()
    r.delete(session_key(user_id, character_id))
