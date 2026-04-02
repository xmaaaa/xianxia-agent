from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.agent.graph import get_agent_graph
from app.agent.nodes import retrieve_context, save_memory, stream_llm_tokens
from app.agent.state import AgentState
from app.db.session import SessionLocal, get_db
from app.memory.short_term import get_session_messages
from app.models.character import Character
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


def _require_character(db: Session, character_id: int, user_id: str) -> Character:
    row = db.get(Character, character_id)
    if row is None or row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return row


def _redis_to_lc_messages(rows: list[dict]) -> list[Union[HumanMessage, AIMessage]]:
    out: list[Union[HumanMessage, AIMessage]] = []
    for m in rows:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=str(content)))
        elif role == "assistant":
            out.append(AIMessage(content=str(content)))
    return out


def _build_initial_state(req: ChatRequest) -> AgentState:
    prior = get_session_messages(req.user_id, req.character_id)
    base = _redis_to_lc_messages(prior)
    base.append(HumanMessage(content=req.message))
    return AgentState(
        user_id=req.user_id,
        character_id=req.character_id,
        messages=base,
        current_intent="",
        retrieved_context="",
    )


@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    if req.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use POST /chat/stream with the same body for streaming.",
        )
    _require_character(db, req.character_id, req.user_id)
    graph = get_agent_graph()
    state = _build_initial_state(req)
    config = {"configurable": {"db": db}}
    result = graph.invoke(state, config=config)
    last = result["messages"][-1]
    reply = str(getattr(last, "content", ""))
    return ChatResponse(
        reply=reply,
        retrieved_context=result.get("retrieved_context", ""),
        current_intent=result.get("current_intent", ""),
    )


def _sse_token_stream(req: ChatRequest, db: Session) -> Iterator[bytes]:
    _require_character(db, req.character_id, req.user_id)
    state0 = _build_initial_state(req)
    r1 = retrieve_context(state0)
    merged: AgentState = {
        "user_id": state0["user_id"],
        "character_id": state0["character_id"],
        "messages": state0["messages"],
        "current_intent": r1["current_intent"],
        "retrieved_context": r1["retrieved_context"],
    }
    config = {"configurable": {"db": db}}
    pieces: list[str] = []
    for token in stream_llm_tokens(merged, config):
        pieces.append(token)
        payload = json.dumps({"token": token}, ensure_ascii=False)
        yield f"data: {payload}\n\n".encode("utf-8")
    full = "".join(pieces)
    final: AgentState = {
        "user_id": merged["user_id"],
        "character_id": merged["character_id"],
        "messages": [*merged["messages"], AIMessage(content=full)],
        "current_intent": merged["current_intent"],
        "retrieved_context": merged["retrieved_context"],
    }
    save_memory(final)
    meta = json.dumps(
        {
            "done": True,
            "current_intent": merged["current_intent"],
            "retrieved_context": merged["retrieved_context"],
        },
        ensure_ascii=False,
    )
    yield f"data: {meta}\n\n".encode("utf-8")


def _sse_with_db(req: ChatRequest):
    db = SessionLocal()
    try:
        yield from _sse_token_stream(req, db)
    finally:
        db.close()


@router.post("/stream")
def chat_stream(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _sse_with_db(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
