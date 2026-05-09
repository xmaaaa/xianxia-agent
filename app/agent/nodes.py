import logging
from hashlib import sha1
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from app.agent.prompts import (
    EXPLORE_HINT,
    INTENT_CLASSIFY_TEMPLATE,
    STATUS_QUERY_HINT,
    SUMMARY_MERGE_TEMPLATE,
    VALID_INTENTS,
    render_system_prompt,
)
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
from app.models.character import Character
from app.rag.retriever import retrieve_context_text

logger = logging.getLogger("app.agent")

_EXPLORE_SCENES: tuple[dict, ...] = (
    {
        "location": "青云镇外竹林",
        "exp_delta": 6,
        "item": "凝气草",
        "event": "在青云镇外竹林采得凝气草，丹田受灵气一洗。",
    },
    {
        "location": "寒潭石径",
        "exp_delta": 8,
        "item": "寒潭水珠",
        "event": "沿寒潭石径探查，收起一枚寒潭水珠。",
    },
    {
        "location": "废弃洞府",
        "exp_delta": 10,
        "item": "残破玉简",
        "event": "在废弃洞府发现残破玉简，隐约记下一缕古意。",
    },
)

_KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "skill_qa",
        (
            "功法",
            "修炼",
            "剑法",
            "诀",
            "术",
            "筑基",
            "金丹",
            "炼气",
            "逆天",
            "太清",
            "典籍",
            "丹方",
            "药理",
        ),
    ),
    (
        "explore",
        ("探索", "秘境", "进入", "查看周围", "环顾", "四周", "走进", "前往", "地图", "洞府"),
    ),
    (
        "status_query",
        ("属性", "境界", "修为", "状态", "背包", "装备", "面板", "我的信息", "查看自身"),
    ),
]


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
        if not last_ai and (isinstance(m, AIMessage) or getattr(m, "type", None) == "ai"):
            last_ai = str(m.content)
            continue
        if last_ai and (isinstance(m, HumanMessage) or getattr(m, "type", None) == "human"):
            last_human = str(m.content)
            break
    if last_human and last_ai:
        return (
            {"role": "user", "content": last_human},
            {"role": "assistant", "content": last_ai},
        )
    return None


def _keyword_classify(user_text: str) -> Optional[str]:
    for intent, keywords in _KEYWORD_RULES:
        if any(k in user_text for k in keywords):
            return intent
    return None


def _llm_classify(user_text: str, llm: ChatOpenAI) -> str:
    prompt = INTENT_CLASSIFY_TEMPLATE.format(user_text=user_text)
    comp = llm.bind(temperature=0.0, max_tokens=20)
    resp = comp.invoke([HumanMessage(content=prompt)])
    raw = str(getattr(resp, "content", "")).strip().lower()
    for v in VALID_INTENTS:
        if v in raw:
            return v
    return "roleplay"


def classify_intent(state: AgentState) -> dict:
    q = _last_human_text(state["messages"])
    intent = _keyword_classify(q)
    if intent is None:
        try:
            intent = _llm_classify(q, _llm())
        except Exception:
            logger.exception("LLM intent classification failed, defaulting to roleplay")
            intent = "roleplay"
    return {"current_intent": intent}


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


# ── Prepare nodes (one per intent) ──────────────────────────────────────────


def prepare_roleplay(state: AgentState) -> dict:
    return {"retrieved_context": ""}


def prepare_skill_qa(state: AgentState) -> dict:
    q = _last_human_text(state["messages"])
    ctx = retrieve_context_text(q)
    return {"retrieved_context": ctx}


def prepare_explore(state: AgentState) -> dict:
    q = _last_human_text(state["messages"])
    seed = f"{state['user_id']}:{state['character_id']}:{q}"
    idx = int(sha1(seed.encode("utf-8")).hexdigest(), 16) % len(_EXPLORE_SCENES)
    scene = _EXPLORE_SCENES[idx]
    game_delta = {
        "type": "explore",
        "exp_delta": scene["exp_delta"],
        "location": scene["location"],
        "items_add": [scene["item"]],
        "event": scene["event"],
    }
    ctx = (
        "本次探索将产生以下可落账结果：\n"
        f"- 地点：{game_delta['location']}\n"
        f"- 修为增加：{game_delta['exp_delta']}\n"
        f"- 获得物品：{scene['item']}\n"
        f"- 事件：{game_delta['event']}"
    )
    return {"retrieved_context": ctx, "game_delta": game_delta}


def prepare_status_query(state: AgentState, config: RunnableConfig) -> dict:
    configurable = config.get("configurable") or {}
    db = configurable.get("db")
    if db is None:
        return {"retrieved_context": ""}
    cid = state["character_id"]
    profile = load_character_profile(db, cid)
    return {"retrieved_context": profile or ""}


# ── Shared: build prompt, generate, save ────────────────────────────────────


def _intent_hint(intent: str, retrieved_context: str) -> str:
    if intent == "explore":
        return EXPLORE_HINT
    if intent == "status_query":
        return STATUS_QUERY_HINT.format(status_data=retrieved_context or "（无法读取属性。）")
    return ""


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


def fold_recent_until_cap(
    llm: ChatOpenAI, summary: str, recent: list[dict]
) -> tuple[str, list[dict]]:
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
    intent = state["current_intent"] or ""
    hint = _intent_hint(intent, state["retrieved_context"])
    system_text = render_system_prompt(
        profile,
        state["retrieved_context"],
        intent,
        conversation_summary=state["conversation_summary"] or "",
        intent_hint=hint,
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


def apply_game_delta(state: AgentState, config: RunnableConfig) -> dict:
    delta = state.get("game_delta") or {}
    if not delta:
        return {}

    configurable = config.get("configurable") or {}
    db = configurable.get("db")
    if db is None:
        raise ValueError("RunnableConfig must include configurable['db'] (SQLAlchemy Session).")

    row = db.get(Character, state["character_id"])
    if row is None or row.user_id != state["user_id"]:
        logger.warning("apply_game_delta: character not found or not owned")
        return {}

    exp_delta = int(delta.get("exp_delta") or 0)
    if exp_delta:
        row.exp = max(0, row.exp + exp_delta)

    location = str(delta.get("location") or "").strip()
    if location:
        row.location = location

    items = [str(x).strip() for x in delta.get("items_add", []) if str(x).strip()]
    if items:
        row.inventory = [*(row.inventory or []), *items]

    event = str(delta.get("event") or "").strip()
    if event:
        row.event_log = [*(row.event_log or []), event][-20:]

    db.commit()
    return {}


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
