import logging
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from app.agent.prompts import SUMMARY_MERGE_TEMPLATE, render_system_prompt
from app.agent.state import AgentState
from app.core.config import settings
from app.memory.layered import (
    count_turns,
    format_turn_for_summary,
    load_layered_session,
    messages_token_count,
    pop_oldest_turn,
    save_layered_session,
)
from app.memory.long_term import load_character_profile
from app.rag.retriever import retrieve_context_text

logger = logging.getLogger("app.agent")


def _last_human_text(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return str(m.content)
        if getattr(m, "type", None) == "human":
            return str(m.content)
    return ""


def _last_turn_as_dicts(messages: list) -> Optional[tuple[dict, dict]]:
    last_ai = ""
    last_human = ""
    for m in reversed(messages):
        if not last_ai and (
            isinstance(m, AIMessage) or getattr(m, "type", None) == "ai"
        ):
            last_ai = str(m.content)
            continue
        if last_ai and (
            isinstance(m, HumanMessage) or getattr(m, "type", None) == "human"
        ):
            last_human = str(m.content)
            break
    if last_human and last_ai:
        return (
            {"role": "user", "content": last_human},
            {"role": "assistant", "content": last_ai},
        )
    return None


def _infer_intent(user_text: str) -> str:
    keys = ("功法", "修炼", "剑法", "诀", "术", "筑基", "金丹", "炼气", "逆天", "太清", "典籍")
    if any(k in user_text for k in keys):
        return "skill_qa"
    return "roleplay"


def retrieve_context(state: AgentState) -> dict:
    q = _last_human_text(state["messages"])
    intent = _infer_intent(q)
    ctx = retrieve_context_text(q) if intent == "skill_qa" else ""
    return {"current_intent": intent, "retrieved_context": ctx}


def _llm() -> ChatOpenAI:
    key = settings.openai_api_key
    if not key or len(key) < 10:
        raise RuntimeError("OPENAI_API_KEY is not set; cannot call the language model.")
    kwargs: dict = {
        "api_key": key,
        "model": settings.openai_model,
        "temperature": 0.75,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def _merge_older_turn_into_summary(llm: ChatOpenAI, old_summary: str, dialog_excerpt: str) -> str:
    max_chars = settings.memory_summary_max_chars
    old_block = old_summary.strip() or "（无）"
    text = SUMMARY_MERGE_TEMPLATE.format(
        old_summary=old_block,
        dialog_excerpt=dialog_excerpt,
        max_chars=max_chars,
    )
    comp = llm.bind(temperature=0.2, max_tokens=min(1024, max_chars + 128))
    resp = comp.invoke([HumanMessage(content=text)])
    out = str(getattr(resp, "content", "")).strip()
    if len(out) > max_chars:
        out = out[:max_chars]
    return out


def _should_compress(recent: list[dict]) -> bool:
    if count_turns(recent) > settings.memory_recent_turns_max:
        return True
    return messages_token_count(recent) > settings.memory_max_tokens


def fold_recent_until_cap(llm: ChatOpenAI, summary: str, recent: list[dict]) -> tuple[str, list[dict]]:
    recent = list(recent)
    s = summary
    while _should_compress(recent):
        folded_blocks: list[str] = []
        work = recent
        while _should_compress(work):
            turn, rest = pop_oldest_turn(work)
            if not turn:
                break
            folded_blocks.append(format_turn_for_summary(turn))
            work = rest
        if not folded_blocks:
            break
        excerpt = "\n\n---\n\n".join(folded_blocks)
        try:
            s = _merge_older_turn_into_summary(llm, s, excerpt)
        except Exception:
            logger.exception("Summary merge failed; folding without LLM merge")
            s = (s + "\n" + excerpt).strip()[: settings.memory_summary_max_chars]
        recent = work
        break
    return s, recent


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
        conversation_summary=state["conversation_summary"] or "",
    )
    return [SystemMessage(content=system_text), *state["messages"]]


async def generate_response(state: AgentState, config: RunnableConfig) -> dict:
    llm = _llm()
    prompt_messages = build_system_and_llm_messages(state, config)
    chunks: list[str] = []
    async for chunk in llm.astream(prompt_messages, config=config):
        c = getattr(chunk, "content", None)
        if c:
            chunks.append(c)
    return {"messages": [AIMessage(content="".join(chunks))]}


def save_memory(state: AgentState) -> dict:
    pair = _last_turn_as_dicts(state["messages"])
    if not pair:
        logger.warning("save_memory: could not extract last turn, skip persist")
        return {}
    user_msg, assistant_msg = pair
    uid = state["user_id"]
    cid = state["character_id"]
    summary, recent = load_layered_session(uid, cid)
    recent = list(recent)
    recent.append(user_msg)
    recent.append(assistant_msg)
    try:
        llm = _llm()
        summary, recent = fold_recent_until_cap(llm, summary, recent)
        save_layered_session(uid, cid, summary, recent)
    except Exception:
        logger.exception("Failed to persist layered session")
        raise
    return {}
