from collections.abc import Iterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from app.agent.prompts import render_system_prompt
from app.agent.state import AgentState
from app.core.config import settings
from app.memory.long_term import load_character_profile
from app.memory.short_term import set_session_messages
from app.rag.retriever import retrieve_context_text


def _last_human_text(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return str(m.content)
        if getattr(m, "type", None) == "human":
            return str(m.content)
    return ""


def _infer_intent(user_text: str) -> str:
    t = user_text
    keys = ("功法", "修炼", "剑法", "诀", "术", "筑基", "金丹", "炼气", "逆天", "太清", "典籍")
    if any(k in t for k in keys):
        return "skill_qa"
    return "roleplay"


def retrieve_context(state: AgentState) -> dict:
    q = _last_human_text(state["messages"])
    intent = _infer_intent(q)
    ctx = retrieve_context_text(q) if intent == "skill_qa" else ""
    return {"current_intent": intent, "retrieved_context": ctx}


def _llm() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set; cannot call the language model.")
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.75,
    )


def build_system_and_llm_messages(state: AgentState, config: RunnableConfig) -> list:
    configurable = config.get("configurable") or {}
    db = configurable.get("db")
    if db is None:
        raise ValueError("RunnableConfig must include configurable['db'] (SQLAlchemy Session).")
    cid = state["character_id"]
    profile = load_character_profile(db, cid) or "无名散修，宗册未录。"
    system_text = render_system_prompt(
        profile,
        state["retrieved_context"],
        state["current_intent"],
    )
    return [SystemMessage(content=system_text), *state["messages"]]


def generate_response(state: AgentState, config: RunnableConfig) -> dict:
    llm = _llm()
    prompt_messages = build_system_and_llm_messages(state, config)
    resp: AIMessage = llm.invoke(prompt_messages)
    return {"messages": [resp]}


def stream_llm_tokens(state: AgentState, config: RunnableConfig) -> Iterator[str]:
    llm = _llm()
    prompt_messages = build_system_and_llm_messages(state, config)
    for chunk in llm.stream(prompt_messages):
        c = getattr(chunk, "content", None)
        if c:
            yield c


def save_memory(state: AgentState) -> dict:
    uid = state["user_id"]
    cid = state["character_id"]
    serialized: list[dict] = []
    for m in state["messages"]:
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            serialized.append({"role": "user", "content": str(m.content)})
        elif isinstance(m, AIMessage) or getattr(m, "type", None) == "ai":
            serialized.append({"role": "assistant", "content": str(m.content)})
    set_session_messages(uid, cid, serialized)
    return {}
