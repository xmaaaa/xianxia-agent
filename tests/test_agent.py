from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

from app.agent.nodes import (
    _keyword_classify,
    _llm_classify,
    apply_game_delta,
    classify_intent,
    prepare_explore,
    prepare_game_action,
    prepare_roleplay,
    prepare_skill_qa,
)
from app.agent.prompts import render_system_prompt
from app.agent.state import AgentState
from app.models.character import Character

# ── keyword classification ──────────────────────────────────────────────────


def test_keyword_classify_skill_qa():
    assert _keyword_classify("太清剑法要如何修炼？") == "skill_qa"
    assert _keyword_classify("逆天诀的境界要求是什么？") == "skill_qa"
    assert _keyword_classify("炼气术入门") == "skill_qa"


def test_keyword_classify_explore():
    assert _keyword_classify("带我去探索秘境") == "explore"
    assert _keyword_classify("我想进入那个洞府") == "explore"
    assert _keyword_classify("查看周围有什么") == "explore"


def test_keyword_classify_status():
    assert _keyword_classify("查看自身属性") == "status_query"
    assert _keyword_classify("我现在是什么境界") == "status_query"
    assert _keyword_classify("打开面板") == "status_query"


def test_keyword_classify_game_actions():
    assert _keyword_classify("我要开始修炼") == "cultivate"
    assert _keyword_classify("先调息片刻") == "rest"
    assert _keyword_classify("服用凝气草") == "use_item"


def test_keyword_classify_returns_none_for_ambiguous():
    assert _keyword_classify("今日天气不错") is None
    assert _keyword_classify("你好") is None


# ── LLM fallback classification ─────────────────────────────────────────────


def test_llm_classify_parses_valid_intent():
    mock_llm = MagicMock()
    fake_resp = MagicMock()
    fake_resp.content = "roleplay"
    mock_llm.bind.return_value = mock_llm
    mock_llm.invoke.return_value = fake_resp
    assert _llm_classify("你好", mock_llm) == "roleplay"


def test_llm_classify_defaults_to_roleplay_on_garbage():
    mock_llm = MagicMock()
    fake_resp = MagicMock()
    fake_resp.content = "unknown_intent_xyz"
    mock_llm.bind.return_value = mock_llm
    mock_llm.invoke.return_value = fake_resp
    assert _llm_classify("你好", mock_llm) == "roleplay"


# ── classify_intent node ────────────────────────────────────────────────────


def test_classify_intent_keyword_hit():
    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="带我探索秘境")],
        "conversation_summary": "",
        "current_intent": "",
        "retrieved_context": "",
    }
    out = classify_intent(state)
    assert out["current_intent"] == "explore"


@patch("app.agent.nodes._llm")
def test_classify_intent_llm_fallback(mock_llm_fn):
    fake_resp = MagicMock()
    fake_resp.content = "roleplay"
    instance = MagicMock()
    instance.bind.return_value = instance
    instance.invoke.return_value = fake_resp
    mock_llm_fn.return_value = instance

    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="你好呀")],
        "conversation_summary": "",
        "current_intent": "",
        "retrieved_context": "",
    }
    out = classify_intent(state)
    assert out["current_intent"] == "roleplay"
    mock_llm_fn.assert_called_once()


# ── prepare nodes ───────────────────────────────────────────────────────────


def test_prepare_roleplay_returns_empty_context():
    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="你好")],
        "conversation_summary": "",
        "current_intent": "roleplay",
        "retrieved_context": "",
    }
    assert prepare_roleplay(state) == {"retrieved_context": ""}


@patch("app.agent.nodes.retrieve_context_text", return_value="[mock] 逆天诀摘录")
def test_prepare_skill_qa_calls_rag(_mock_rt):
    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="逆天诀有何要求？")],
        "conversation_summary": "",
        "current_intent": "skill_qa",
        "retrieved_context": "",
    }
    out = prepare_skill_qa(state)
    assert "逆天诀" in out["retrieved_context"]
    _mock_rt.assert_called_once()


def test_prepare_explore_returns_action_context():
    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="探索秘境")],
        "conversation_summary": "",
        "current_intent": "explore",
        "retrieved_context": "",
    }
    out = prepare_explore(state)
    assert "本次行动" in out["retrieved_context"]
    assert out["game_delta"]["type"] == "explore"
    assert out["game_delta"]["exp_delta"] > 0


def test_prepare_game_action_uses_character_state(db_session):
    row = Character(
        user_id="u1",
        name="云游子",
        sect="太清宗",
        spirit_root="水木双灵根",
        exp=15,
        inventory=["凝气草"],
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    state: AgentState = {
        "user_id": "u1",
        "character_id": row.id,
        "messages": [HumanMessage(content="开始修炼")],
        "conversation_summary": "",
        "current_intent": "cultivate",
        "retrieved_context": "",
    }
    out = prepare_game_action(state, {"configurable": {"db": db_session}})

    assert out["game_delta"]["type"] == "cultivate"
    assert out["game_delta"]["realm"] == "炼气中期"
    assert "境界变化：炼气中期" in out["retrieved_context"]


def test_apply_game_delta_updates_character(db_session):
    row = Character(
        user_id="u1",
        name="云游子",
        sect="太清宗",
        spirit_root="水木双灵根",
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    state: AgentState = {
        "user_id": "u1",
        "character_id": row.id,
        "messages": [HumanMessage(content="探索秘境")],
        "conversation_summary": "",
        "current_intent": "explore",
        "retrieved_context": "",
        "game_delta": {
            "type": "explore",
            "exp_delta": 7,
            "location": "废弃洞府",
            "items_add": ["残破玉简"],
            "event": "在废弃洞府发现残破玉简。",
        },
    }
    apply_game_delta(state, {"configurable": {"db": db_session}})
    db_session.refresh(row)

    assert row.exp == 7
    assert row.location == "废弃洞府"
    assert row.inventory == ["残破玉简"]
    assert row.event_log == ["在废弃洞府发现残破玉简。"]


def test_apply_game_delta_handles_breakthrough_and_item_removal(db_session):
    row = Character(
        user_id="u1",
        name="云游子",
        sect="太清宗",
        spirit_root="水木双灵根",
        exp=18,
        inventory=["凝气草", "残破玉简"],
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    state: AgentState = {
        "user_id": "u1",
        "character_id": row.id,
        "messages": [HumanMessage(content="服用凝气草")],
        "conversation_summary": "",
        "current_intent": "use_item",
        "retrieved_context": "",
        "game_delta": {
            "type": "use_item",
            "exp_delta": 5,
            "items_remove": ["凝气草"],
            "realm": "炼气中期",
            "event": "使用凝气草后，灵气入体。",
        },
    }
    apply_game_delta(state, {"configurable": {"db": db_session}})
    db_session.refresh(row)

    assert row.exp == 23
    assert row.realm == "炼气中期"
    assert row.inventory == ["残破玉简"]
    assert row.event_log == ["使用凝气草后，灵气入体。"]


# ── render_system_prompt ────────────────────────────────────────────────────


def test_render_system_prompt_includes_profile_and_rag():
    text = render_system_prompt("测试修士档案", "测试典籍摘录", "skill_qa")
    assert "本座" in text
    assert "测试修士档案" in text
    assert "测试典籍摘录" in text


def test_render_system_prompt_defaults_when_empty():
    text = render_system_prompt("", "", "")
    assert "无名散修" in text
    assert "暂无检索" in text
    assert "暂无往事提要" in text
    assert "未分类" in text


def test_render_system_prompt_includes_conversation_summary():
    text = render_system_prompt("档案", "摘录", "roleplay", conversation_summary="曾论剑于东海。")
    assert "曾论剑于东海" in text


def test_render_system_prompt_includes_intent_hint():
    text = render_system_prompt("档案", "", "explore", intent_hint="探索模式补充指令")
    assert "探索模式补充指令" in text
