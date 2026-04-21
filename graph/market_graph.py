from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import MarketState
from agents.data_agent import data_agent
from agents.analysis_agent import analysis_agent
from agents.opportunity_agent import opportunity_agent
from agents.report_agent import report_agent


def _should_continue_after_data(state: MarketState) -> str:
    """Si el DataAgent falló de forma crítica, terminamos el flujo."""
    if state.get("nodo_error"):
        return "end_with_error"
    if not state.get("raw_prices"):
        return "end_with_error"
    return "continue"


def _error_node(state: MarketState) -> MarketState:
    """Nodo final de error: genera un reporte mínimo con el problema."""
    error = state.get("nodo_error", "Error desconocido")
    return {
        **state,
        "report": f"❌ El análisis no pudo completarse.\nError: {error}\n\nVerificá tu conexión o los servicios externos.",
        "opportunities": [],
    }


def build_market_graph():
    """
    Construye y compila el grafo LangGraph del sistema multi-agente.

    Flujo:
        data_agent → analysis_agent → opportunity_agent → report_agent → END
                    ↘ (error) → error_node → END
    """
    memory = MemorySaver()

    graph = StateGraph(MarketState)

    # Registrar nodos
    graph.add_node("data_agent", data_agent)
    graph.add_node("analysis_agent", analysis_agent)
    graph.add_node("opportunity_agent", opportunity_agent)
    graph.add_node("report_agent", report_agent)
    graph.add_node("error_node", _error_node)

    # Entry point
    graph.set_entry_point("data_agent")

    # Flujo condicional post data_agent
    graph.add_conditional_edges(
        "data_agent",
        _should_continue_after_data,
        {
            "continue": "analysis_agent",
            "end_with_error": "error_node",
        },
    )

    # Flujo lineal
    graph.add_edge("analysis_agent", "opportunity_agent")
    graph.add_edge("opportunity_agent", "report_agent")
    graph.add_edge("report_agent", END)
    graph.add_edge("error_node", END)

    return graph.compile(checkpointer=memory)


# Instancia global del grafo compilado
market_graph = build_market_graph()