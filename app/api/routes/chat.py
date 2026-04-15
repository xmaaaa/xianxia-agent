from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.agent.graph import get_agent_graph
from app.agent.state import AgentState
from app.db.session import SessionLocal, get_db
from app.memory.layered import load_layered_session
from app.models.character import Character
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger("app.api.chat")
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
    summary, prior = load_layered_session(req.user_id, req.character_id)
    base = _redis_to_lc_messages(prior)
    base.append(HumanMessage(content=req.message))
    return AgentState(
        user_id=req.user_id,
        character_id=req.character_id,
        messages=base,
        conversation_summary=summary,
        current_intent="",
        retrieved_context="",
    )


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    if req.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use POST /chat/stream with the same body for streaming.",
        )
    _require_character(db, req.character_id, req.user_id)
    graph = get_agent_graph()
    state = _build_initial_state(req)
    config = {"configurable": {"db": db}}
    result = await graph.ainvoke(state, config=config)
    last = result["messages"][-1]
    reply = str(getattr(last, "content", ""))
    return ChatResponse(
        reply=reply,
        retrieved_context=result.get("retrieved_context", ""),
        current_intent=result.get("current_intent", ""),
    )


def _sse_event(data: dict) -> bytes:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode()


async def _sse_token_stream(req: ChatRequest, db: Session) -> AsyncIterator[bytes]:
    has_tokens = False
    intent = ""
    context = ""
    try:
        _require_character(db, req.character_id, req.user_id)
        graph = get_agent_graph()
        state = _build_initial_state(req)
        config = {"configurable": {"db": db}}

        async for event in graph.astream_events(state, config=config, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node", "")

            if kind == "on_chat_model_stream" and node == "generate_response":
                token = event["data"]["chunk"].content
                if token:
                    has_tokens = True
                    yield _sse_event({"token": token})

            elif kind == "on_chain_end" and node == "classify_intent":
                output = event["data"].get("output", {})
                if isinstance(output, dict):
                    intent = output.get("current_intent", intent)

            elif kind == "on_chain_end" and node.startswith("prepare_"):
                output = event["data"].get("output", {})
                if isinstance(output, dict):
                    context = output.get("retrieved_context", context)

        yield _sse_event({"done": True, "current_intent": intent, "retrieved_context": context})

    except HTTPException as exc:
        yield _sse_event({"error": exc.detail, "status": exc.status_code})
    except Exception as exc:
        if has_tokens:
            logger.exception("Post-generation error (tokens already streamed): %s", exc)
            yield _sse_event({"done": True, "current_intent": intent, "retrieved_context": context})
        else:
            logger.exception("SSE stream error: %s", exc)
            yield _sse_event({"error": f"{type(exc).__name__}: {str(exc)[:300]}", "status": 500})


async def _sse_with_db(req: ChatRequest) -> AsyncIterator[bytes]:
    db = SessionLocal()
    try:
        async for chunk in _sse_token_stream(req, db):
            yield chunk
    finally:
        db.close()


@router.post("/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _sse_with_db(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
