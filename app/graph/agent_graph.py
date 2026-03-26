from typing import Any, Dict, Optional, TypedDict
from langgraph.graph import StateGraph, END

from app.agents.verification_agent import run_verification_agent
from app.agents.identity_agent import run_identity_agent
from app.agents.matching_agent import run_matching_agent
from app.agents.decision_agent import run_decision_agent


# ─────────────────────────────────────────────────────────────
# Shared Agent State
# ─────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    request: Any                      # VerificationRequest (Pydantic model)
    ocr_result: Optional[Dict]        # Output from verification_agent (OCR + fraud)
    identity_result: Optional[Dict]   # Output from identity_agent (match scores)
    matching_result: Optional[Dict]   # Output from matching_agent (logic results)
    final_result: Optional[Dict]      # Output from decision_agent (verdict)


# ─────────────────────────────────────────────────────────────
# Build and Compile the Graph
# ─────────────────────────────────────────────────────────────

def build_verification_graph():
    """
    Constructs the LangGraph pipeline:
        verification_agent → identity_agent → matching_agent → END
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("verification_agent", run_verification_agent)
    graph.add_node("identity_agent", run_identity_agent)
    graph.add_node("matching_agent", run_matching_agent)
    graph.add_node("decision_agent", run_decision_agent)

    # Wire edges
    graph.set_entry_point("verification_agent")
    graph.add_edge("verification_agent", "identity_agent")
    graph.add_edge("identity_agent", "matching_agent")
    graph.add_edge("matching_agent", "decision_agent")
    graph.add_edge("decision_agent", END)

    return graph.compile()


# Singleton compiled graph — import this in the route
verification_graph = build_verification_graph()
