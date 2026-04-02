import json
import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("XIANXIA_API_BASE", "http://127.0.0.1:8000").rstrip("/")


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=120.0)


st.set_page_config(page_title="修仙 Agent · MVP", layout="wide")
st.title("修仙 AI Agent · Phase 1")
st.caption("创建角色、与叙事之灵对话；功法问答走本地 RAG（Chroma）。")

if "user_id" not in st.session_state:
    st.session_state.user_id = "demo-xianren-001"
if "character_id" not in st.session_state:
    st.session_state.character_id = None
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

with st.sidebar:
    st.subheader("身份")
    st.session_state.user_id = st.text_input("user_id", value=st.session_state.user_id)
    st.divider()
    st.subheader("角色")
    with _client() as c:
        r = c.get("/api/v1/characters/", params={"user_id": st.session_state.user_id})
        chars = r.json() if r.status_code == 200 else []
    options = {f"{x['name']}（{x['sect']} · id={x['id']}）": x["id"] for x in chars}
    if options:
        label = st.selectbox("选择角色", list(options.keys()))
        st.session_state.character_id = options[label]
    else:
        st.info("暂无角色，请在右侧创建。")

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
            with _client() as c:
                resp = c.post("/api/v1/characters/", json=payload)
            if resp.status_code == 201:
                st.success("角色已立册入库。")
                st.session_state.character_id = resp.json()["id"]
                st.rerun()
            else:
                st.error(resp.text)

col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("对话")
    for turn in st.session_state.chat_log:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    prompt = st.chat_input("向本座问法、问路、问劫数……")
    if prompt and st.session_state.character_id:
        full = ""
        body = {
            "user_id": st.session_state.user_id,
            "character_id": st.session_state.character_id,
            "message": prompt,
            "stream": True,
        }
        status = st.status("本座推演中……", expanded=False)
        with _client() as c:
            with c.stream("POST", "/api/v1/chat/stream", json=body) as stream:
                for line in stream.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line.removeprefix("data:").strip()
                    try:
                        obj = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("done"):
                        st.session_state.last_intent = obj.get("current_intent", "")
                        st.session_state.last_ctx = obj.get("retrieved_context", "")
                        continue
                    tok = obj.get("token")
                    if tok:
                        full += tok
        status.update(label="推演已毕", state="complete", expanded=False)
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        st.session_state.chat_log.append({"role": "assistant", "content": full})
        st.rerun()
    elif prompt:
        st.warning("请先在侧栏创建或选择角色。")

with col_b:
    st.subheader("会话元数据")
    st.write("user_id:", st.session_state.user_id)
    st.write("character_id:", st.session_state.character_id)
    if st.session_state.get("last_intent") is not None:
        st.write("current_intent:", st.session_state.get("last_intent"))
    if st.session_state.get("last_ctx"):
        with st.expander("retrieved_context（节选）"):
            st.text(st.session_state.get("last_ctx")[:2000])
