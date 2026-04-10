"""分层会话记忆：Redis 中保存「滚动摘要 + 近期原文轮次」。"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings
from app.memory.short_term import session_key

logger = logging.getLogger("app.memory.layered")

LAYERED_VERSION = 2

_tiktoken_encoder = None
_tiktoken_failed = False


def estimate_token_count(text: str) -> int:
    global _tiktoken_encoder, _tiktoken_failed
    if not _tiktoken_failed and _tiktoken_encoder is None:
        try:
            import tiktoken

            _tiktoken_encoder = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            logger.debug("tiktoken unavailable, falling back to char-based estimate")
            _tiktoken_failed = True
    if _tiktoken_encoder is not None:
        return len(_tiktoken_encoder.encode(text))
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return int(cjk * 1.5 + (len(text) - cjk) * 0.25) + 1


def messages_token_count(messages: list[dict[str, Any]]) -> int:
    return sum(estimate_token_count(m.get("content", "")) + 4 for m in messages)


def _redis_client():
    from app.memory.short_term import _client

    return _client()


def _normalize_legacy_list(data: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    """旧版仅存储消息列表时，截断为近期轮次，避免一次加载过长上下文。"""
    flat = [x for x in data if isinstance(x, dict)]
    cap = settings.memory_recent_turns_max * 2
    if len(flat) > cap:
        flat = flat[-cap:]
    return "", flat


def parse_stored_session(raw: str | None) -> tuple[str, list[dict[str, Any]]]:
    """解析 Redis 中的 JSON，返回 (summary, message_dicts)。"""
    if not raw:
        return "", []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return "", []
    if isinstance(data, list):
        return _normalize_legacy_list(data)
    if not isinstance(data, dict):
        return "", []
    summary = data.get("summary") or ""
    if not isinstance(summary, str):
        summary = str(summary)
    messages = data.get("messages")
    if not isinstance(messages, list):
        messages = []
    out: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant"):
            out.append({"role": m["role"], "content": str(m.get("content", ""))})
    return summary, out


def dump_stored_session(summary: str, messages: list[dict[str, Any]]) -> str:
    payload = {
        "v": LAYERED_VERSION,
        "summary": summary.strip(),
        "messages": messages,
    }
    return json.dumps(payload, ensure_ascii=False)


def load_layered_session(user_id: str, character_id: int) -> tuple[str, list[dict[str, Any]]]:
    r = _redis_client()
    raw = r.get(session_key(user_id, character_id))
    return parse_stored_session(raw)


def save_layered_session(
    user_id: str,
    character_id: int,
    summary: str,
    messages: list[dict[str, Any]],
    ttl_seconds: int = 86400 * 7,
) -> None:
    r = _redis_client()
    key = session_key(user_id, character_id)
    r.setex(key, ttl_seconds, dump_stored_session(summary, messages))


def count_turns(messages: list[dict[str, Any]]) -> int:
    n = 0
    i = 0
    while i + 1 < len(messages):
        if messages[i].get("role") == "user" and messages[i + 1].get("role") == "assistant":
            n += 1
            i += 2
            continue
        i += 1
    return n


def pop_oldest_turn(messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """拆出最旧的一轮 (user, assistant)，返回 (turn_pair, remaining)。"""
    if len(messages) >= 2 and messages[0].get("role") == "user" and messages[1].get("role") == "assistant":
        turn = messages[:2]
        rest = messages[2:]
        return turn, rest
    return [], messages


def format_turn_for_summary(turn: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for m in turn:
        role = "修士" if m.get("role") == "user" else "本座"
        lines.append(f"{role}：{m.get('content', '')}")
    return "\n".join(lines)
