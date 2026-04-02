from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import generate_response, retrieve_context, save_memory
from app.agent.state import AgentState


def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("retrieve_context", retrieve_context)
    g.add_node("generate_response", generate_response)
    g.add_node("save_memory", save_memory)
    g.add_edge(START, "retrieve_context")
    g.add_edge("retrieve_context", "generate_response")
    g.add_edge("generate_response", "save_memory")
    g.add_edge("save_memory", END)
    return g.compile()


@lru_cache
def get_agent_graph():
    return _build_graph()
