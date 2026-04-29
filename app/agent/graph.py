from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    apply_game_delta,
    classify_intent,
    generate_response,
    prepare_explore,
    prepare_roleplay,
    prepare_skill_qa,
    prepare_status_query,
    save_memory,
)
from app.agent.state import AgentState

_PREPARE_NODES = {
    "roleplay": "prepare_roleplay",
    "skill_qa": "prepare_skill_qa",
    "explore": "prepare_explore",
    "status_query": "prepare_status_query",
}


def _build_graph():
    g = StateGraph(AgentState)

    g.add_node("classify_intent", classify_intent)
    g.add_node("prepare_roleplay", prepare_roleplay)
    g.add_node("prepare_skill_qa", prepare_skill_qa)
    g.add_node("prepare_explore", prepare_explore)
    g.add_node("prepare_status_query", prepare_status_query)
    g.add_node("generate_response", generate_response)
    g.add_node("apply_game_delta", apply_game_delta)
    g.add_node("save_memory", save_memory)

    g.add_edge(START, "classify_intent")
    g.add_conditional_edges(
        "classify_intent",
        lambda s: s["current_intent"],
        _PREPARE_NODES,
    )
    for node in _PREPARE_NODES.values():
        g.add_edge(node, "generate_response")
    g.add_edge("generate_response", "apply_game_delta")
    g.add_edge("apply_game_delta", "save_memory")
    g.add_edge("save_memory", END)

    return g.compile()


@lru_cache
def get_agent_graph():
    return _build_graph()
