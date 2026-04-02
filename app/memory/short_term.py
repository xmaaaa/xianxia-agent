import json
from typing import Any

import redis

from app.core.config import settings


def _client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def session_key(user_id: str, character_id: int) -> str:
    return f"xianxia:chat:{user_id}:{character_id}"


def get_session_messages(user_id: str, character_id: int) -> list[dict[str, Any]]:
    r = _client()
    raw = r.get(session_key(user_id, character_id))
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def set_session_messages(
    user_id: str,
    character_id: int,
    messages: list[dict[str, Any]],
    ttl_seconds: int = 86400 * 7,
) -> None:
    r = _client()
    key = session_key(user_id, character_id)
    r.setex(key, ttl_seconds, json.dumps(messages, ensure_ascii=False))


def append_turn(
    user_id: str,
    character_id: int,
    user_text: str,
    assistant_text: str,
    ttl_seconds: int = 86400 * 7,
) -> list[dict[str, Any]]:
    history = get_session_messages(user_id, character_id)
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": assistant_text})
    set_session_messages(user_id, character_id, history, ttl_seconds=ttl_seconds)
    return history


def clear_session(user_id: str, character_id: int) -> None:
    r = _client()
    r.delete(session_key(user_id, character_id))
