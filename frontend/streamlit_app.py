import json
import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("XIANXIA_API_BASE", "http://127.0.0.1:8000").rstrip("/")
MAX_CHAT_LOG = 200

INTENT_LABELS = {
    "roleplay": "🗡️ 角色扮演",
    "skill_qa": "📖 功法问答",
    "explore": "🗺️ 探索",
    "cultivate": "🧘 修炼",
    "rest": "🌙 调息",
    "use_item": "🎒 使用物品",
    "status_query": "📊 状态查询",
}

QUICK_COMMANDS = [
    ("🗺️ 探索周围", "探索一下周围有什么"),
    ("📊 查看属性", "查看自身属性"),
    ("⚔️ 修炼", "我要开始修炼"),
    ("🌙 调息", "先调息片刻"),
]


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=120.0, trust_env=False)


def _api_get(path: str, **kwargs):
    try:
        with _client() as c:
            r = c.get(path, **kwargs)
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        st.error("无法连接后端 API，请确认 uvicorn 已启动。")
        return None
    except httpx.HTTPStatusError as exc:
        st.error(f"API 错误 ({exc.response.status_code}): {exc.response.text[:300]}")
        return None


def _api_post(path: str, **kwargs):
    try:
        with _client() as c:
            r = c.post(path, **kwargs)
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        st.error("无法连接后端 API，请确认 uvicorn 已启动。")
        return None
    except httpx.HTTPStatusError as exc:
        st.error(f"API 错误 ({exc.response.status_code}): {exc.response.text[:300]}")
        return None


def _fetch_character(user_id: str, character_id: int):
    return _api_get(f"/api/v1/characters/{character_id}", params={"user_id": user_id})


def _send_message(user_id: str, character_id: int, message: str):
    """Send message via SSE stream, return (full_text, intent, context)."""
    body = {
        "user_id": user_id,
        "character_id": character_id,
        "message": message,
        "stream": True,
    }
    full = ""
    intent = ""
    context = ""
    try:
        with _client() as c, c.stream("POST", "/api/v1/chat/stream", json=body) as stream:
            stream.raise_for_status()
            for line in stream.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                raw = line.removeprefix("data:").strip()
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if obj.get("error"):
                    st.error(f"后端错误：{obj['error']}")
                    return full, intent, context
                if obj.get("done"):
                    intent = obj.get("current_intent", "")
                    context = obj.get("retrieved_context", "")
                    continue
                tok = obj.get("token")
                if tok:
                    full += tok
    except httpx.ConnectError:
        st.error("无法连接后端 API，请确认 uvicorn 已启动。")
    except httpx.HTTPStatusError as exc:
        st.error(f"API 错误 ({exc.response.status_code}): {exc.response.text[:300]}")
    except httpx.ReadTimeout:
        st.error("请求超时，请稍后重试。")
    return full, intent, context


# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="修仙 Agent", layout="wide")
st.title("修仙 AI Agent")
st.caption("创建角色、与引导灵对话 · 意图路由自动识别 · 功法问答 / 探索 / 状态查询")

if "user_id" not in st.session_state:
    st.session_state.user_id = "demo-xianren-001"
if "character_id" not in st.session_state:
    st.session_state.character_id = None
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "pending_cmd" not in st.session_state:
    st.session_state.pending_cmd = None

# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.subheader("身份")
    st.session_state.user_id = st.text_input("user_id", value=st.session_state.user_id)
    st.divider()

    st.subheader("角色")
    chars_data = _api_get("/api/v1/characters/", params={"user_id": st.session_state.user_id})
    chars = chars_data if isinstance(chars_data, list) else []
    options = {f"{x['name']}（{x['sect']} · id={x['id']}）": x["id"] for x in chars}
    if options:
        label = st.selectbox("选择角色", list(options.keys()))
        st.session_state.character_id = options[label]
    else:
        st.info("暂无角色，请在下方创建。")

    st.divider()
    st.subheader("创建新角色")
    name = st.text_input("道号", placeholder="如：云游子")
    sect = st.text_input("门派", placeholder="如：太清宗")
    spirit_root = st.text_input("灵根", placeholder="如：水木双灵根")
    if st.button("创建角色", type="primary"):
        if not (name and sect and spirit_root):
            st.warning("请填写道号、门派、灵根。")
        else:
            payload = {
                "user_id": st.session_state.user_id,
                "name": name,
                "sect": sect,
                "spirit_root": spirit_root,
            }
            result = _api_post("/api/v1/characters/", json=payload)
            if result:
                st.success("角色已立册入库。")
                st.session_state.character_id = result["id"]
                st.rerun()

# ── Main area ───────────────────────────────────────────────────────────────

col_chat, col_info = st.columns([2, 1])

with col_chat:
    st.subheader("对话")

    for turn in st.session_state.chat_log:
        with st.chat_message(turn["role"]):
            intent_tag = turn.get("intent", "")
            if turn["role"] == "assistant" and intent_tag:
                badge = INTENT_LABELS.get(intent_tag, f"🏷️ {intent_tag}")
                st.caption(badge)
            st.markdown(turn["content"])

    # Quick command buttons
    if st.session_state.character_id:
        cols = st.columns(len(QUICK_COMMANDS))
        for i, (btn_label, cmd_text) in enumerate(QUICK_COMMANDS):
            if cols[i].button(btn_label, key=f"qcmd_{i}", use_container_width=True):
                st.session_state.pending_cmd = cmd_text
                st.rerun()

    prompt = st.chat_input("向本座问法、问路、问劫数……")

    # Use pending quick command if no manual input
    if not prompt and st.session_state.pending_cmd:
        prompt = st.session_state.pending_cmd
        st.session_state.pending_cmd = None

    if prompt and st.session_state.character_id:
        stream_status = st.status("本座推演中……", expanded=False)
        full, intent, context = _send_message(
            st.session_state.user_id,
            st.session_state.character_id,
            prompt,
        )
        stream_status.update(label="推演已毕", state="complete", expanded=False)

        if full:
            st.session_state.chat_log.append({"role": "user", "content": prompt})
            st.session_state.chat_log.append(
                {
                    "role": "assistant",
                    "content": full,
                    "intent": intent,
                }
            )
            st.session_state.last_intent = intent
            st.session_state.last_ctx = context
            if len(st.session_state.chat_log) > MAX_CHAT_LOG:
                st.session_state.chat_log = st.session_state.chat_log[-MAX_CHAT_LOG:]
            st.rerun()
    elif prompt:
        st.warning("请先在侧栏创建或选择角色。")

# ── Right panel: character card + metadata ──────────────────────────────────

with col_info:
    if st.session_state.character_id:
        char_data = _fetch_character(st.session_state.user_id, st.session_state.character_id)
        if char_data:
            inventory = "、".join(char_data.get("inventory") or []) or "空"
            recent_events = char_data.get("event_log") or []
            st.subheader("角色面板")
            st.markdown(f"""
| | |
|---|---|
| **道号** | {char_data["name"]} |
| **门派** | {char_data["sect"]} |
| **灵根** | {char_data["spirit_root"]} |
| **境界** | {char_data["realm"]} |
| **修为** | {char_data["exp"]} |
| **位置** | {char_data.get("location", "青云镇")} |
| **背包** | {inventory} |
""")
            if recent_events:
                with st.expander("近事", expanded=False):
                    for item in recent_events[-5:]:
                        st.write(f"- {item}")
        st.divider()

    st.subheader("会话状态")
    last_intent = st.session_state.get("last_intent", "")
    if last_intent:
        badge = INTENT_LABELS.get(last_intent, last_intent)
        st.markdown(f"**当前意图**：{badge}")
    else:
        st.write("当前意图：未知")

    st.write(f"对话轮次：{len(st.session_state.chat_log) // 2}")

    if st.session_state.get("last_ctx"):
        with st.expander("检索到的典籍片段"):
            st.text(st.session_state.get("last_ctx")[:2000])
