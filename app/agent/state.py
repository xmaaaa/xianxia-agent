from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    user_id: str
    character_id: int
    messages: Annotated[list[AnyMessage], add_messages]
    current_intent: str
    retrieved_context: str
