from unittest.mock import patch

from langchain_core.messages import HumanMessage

from app.agent.nodes import _infer_intent, retrieve_context
from app.agent.prompts import render_system_prompt
from app.agent.state import AgentState


def test_infer_intent_skill_keywords():
    assert _infer_intent("太清剑法要如何修炼？") == "skill_qa"
    assert _infer_intent("逆天诀的境界要求是什么？") == "skill_qa"
    assert _infer_intent("炼气术入门") == "skill_qa"
    assert _infer_intent("今日天气不错") == "roleplay"
    assert _infer_intent("带我去探索秘境") == "roleplay"


@patch("app.agent.nodes.retrieve_context_text", return_value="[mock] 逆天诀摘录")
def test_retrieve_context_sets_intent_and_context_keys(_mock_rt):
    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="逆天诀有何境界要求？")],
        "conversation_summary": "",
        "current_intent": "",
        "retrieved_context": "",
    }
    out = retrieve_context(state)
    assert out["current_intent"] == "skill_qa"
    assert "逆天诀" in out["retrieved_context"]


@patch("app.agent.nodes.retrieve_context_text", return_value="")
def test_retrieve_context_roleplay_skips_rag(_mock_rt):
    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="今天天气如何")],
        "conversation_summary": "",
        "current_intent": "",
        "retrieved_context": "",
    }
    out = retrieve_context(state)
    assert out["current_intent"] == "roleplay"
    assert out["retrieved_context"] == ""
    _mock_rt.assert_not_called()


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
