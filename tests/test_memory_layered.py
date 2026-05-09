import json

from app.memory.layered import (
    count_turns,
    dump_stored_session,
    estimate_token_count,
    messages_token_count,
    parse_stored_session,
    pop_oldest_turn,
)


def test_parse_legacy_list_truncates_to_cap(monkeypatch):
    monkeypatch.setattr("app.memory.layered.settings.memory_recent_turns_max", 2)
    raw = json.dumps(
        [{"role": "user", "content": str(i)} for i in range(8)],
        ensure_ascii=False,
    )
    summary, msgs = parse_stored_session(raw)
    assert summary == ""
    assert len(msgs) == 4


def test_parse_v2_roundtrip():
    summary, msgs = parse_stored_session(
        dump_stored_session(
            "提要", [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
        )
    )
    assert summary == "提要"
    assert len(msgs) == 2


def test_count_turns_and_pop():
    msgs = [
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "2"},
        {"role": "user", "content": "3"},
        {"role": "assistant", "content": "4"},
    ]
    assert count_turns(msgs) == 2
    turn, rest = pop_oldest_turn(msgs)
    assert len(turn) == 2
    assert rest[0]["content"] == "3"


def test_estimate_token_count_positive():
    assert estimate_token_count("你好世界") > 0
    assert estimate_token_count("hello world") > 0
    assert estimate_token_count("") >= 0


def test_messages_token_count():
    msgs = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好世界"},
    ]
    total = messages_token_count(msgs)
    assert total > 0
    assert total > estimate_token_count("你好")
