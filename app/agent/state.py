from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    user_id: str
    character_id: int
    messages: Annotated[list[AnyMessage], add_messages]
    conversation_summary: str
    current_intent: str
    retrieved_context: str
    game_delta: dict
