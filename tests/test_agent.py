from unittest.mock import patch

from langchain_core.messages import HumanMessage

from app.agent.nodes import _infer_intent, retrieve_context
from app.agent.prompts import render_system_prompt
from app.agent.state import AgentState
from app.main import app


def test_infer_intent_skill_keywords():
    assert _infer_intent("太清剑法要如何修炼？") == "skill_qa"
    assert _infer_intent("今日天气不错") == "roleplay"


@patch("app.agent.nodes.retrieve_context_text", return_value="[mock] 逆天诀摘录")
def test_retrieve_context_sets_intent_and_context_keys(_mock_rt):
    state: AgentState = {
        "user_id": "u1",
        "character_id": 1,
        "messages": [HumanMessage(content="逆天诀有何境界要求？")],
        "current_intent": "",
        "retrieved_context": "",
    }
    out = retrieve_context(state)
    assert "current_intent" in out and "retrieved_context" in out
    assert out["current_intent"] == "skill_qa"
    assert "逆天诀" in out["retrieved_context"]


def test_render_system_prompt_includes_profile_and_rag_placeholders():
    text = render_system_prompt("测试修士档案", "测试典籍摘录", "skill_qa")
    assert "本座" in text
    assert "测试修士档案" in text
    assert "测试典籍摘录" in text


def test_health_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
