from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import MarketState
from agents.data_agent import data_agent
from agents.analysis_agent import analysis_agent
from agents.opportunity_agent import opportunity_agent
from agents.report_agent import report_agent
from agents.portfolio_optimizer_agent import portfolio_optimizer_agent
from agents.asset_allocator import asset_allocator_agent
from agents.macro_data_agent import macro_data_agent

# ── CONDITIONS ─────────────────────────────

def _should_continue_after_data(state: MarketState) -> str:
    if state.get("nodo_error"):
        return "end_with_error"
    if not state.get("raw_prices"):
        return "end_with_error"
    return "continue"


def _should_continue_after_optimizer(state: MarketState) -> str:
    if state.get("nodo_error"):
        return "end_with_error"
    return "continue"


# ── ERROR NODE ─────────────────────────────

def _error_node(state: MarketState) -> MarketState:
    error = state.get("nodo_error", "Error desconocido")
    return {
        **state,
        "report": f"❌ El análisis no pudo completarse.\nError: {error}",
        "opportunities": [],
    }


# ── GRAPH ─────────────────────────────

def build_market_graph():
    memory = MemorySaver()
    graph = StateGraph(MarketState)

    graph.add_node("data_agent", data_agent)
    graph.add_node("analysis_agent", analysis_agent)
    graph.add_node("opportunity_agent", opportunity_agent)
    graph.add_node("portfolio_optimizer_agent", portfolio_optimizer_agent)
    graph.add_node("report_agent", report_agent)
    graph.add_node("error_node", _error_node)
    graph.add_node("asset_allocator_agent", asset_allocator_agent)
    graph.add_node("macro_data_agent", macro_data_agent)

    graph.set_entry_point("data_agent")

    # 🔹 DATA → ANALYSIS
    graph.add_conditional_edges(
        "data_agent",
        _should_continue_after_data,
        {
            "continue": "macro_data_agent",
            "end_with_error": "error_node",
        },
    )

    # 🔹 FLOW NORMAL
    graph.add_edge("macro_data_agent", "analysis_agent")
    graph.add_edge("analysis_agent", "opportunity_agent")
    graph.add_edge("opportunity_agent", "asset_allocator_agent")
    graph.add_edge("asset_allocator_agent", "portfolio_optimizer_agent")

    # 🔹 OPTIMIZER → REPORT (CONDICIONAL)
    graph.add_conditional_edges(
        "portfolio_optimizer_agent",
        _should_continue_after_optimizer,
        {
            "continue": "report_agent",
            "end_with_error": "error_node",
        },
    )

    # 🔹 FINAL
    graph.add_edge("report_agent", END)
    graph.add_edge("error_node", END)

    return graph.compile(checkpointer=memory)


market_graph = build_market_graph()