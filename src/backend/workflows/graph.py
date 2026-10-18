"""The executable case graph. State/checkpoints contain JSON, not live clients."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from backend.contracts.services import ServiceUnavailable
from backend.workflows.evidence_nodes import PipelineNodes


class CaseState(TypedDict, total=False):
    context: dict
    message: str
    instruction: str
    expected_revision: int
    parent_result_id: str | None
    pack_id: str | None
    result_id: str
    round: int
    clarification_round: int
    tools_used: int
    interpretation: dict
    questions: list[dict]
    query: dict
    db_research: dict
    web_research: dict
    research: dict
    batch: dict
    claims: dict
    claim_evidence: list[dict]
    assessment: dict
    pack: dict
    draft_error: bool


def build_graph(store, reasoning, backbone, web, checkpointer, tracer=None):
    nodes = PipelineNodes(store, reasoning, backbone, web, tracer)
    graph = StateGraph(CaseState)
    policy = RetryPolicy(initial_interval=.2, max_interval=1, max_attempts=2, retry_on=ServiceUnavailable)
    mapping = {"interpret": nodes.interpret, "ask_clarification": nodes.questions, "clarify": nodes.clarify,
        "plan": nodes.plan, "retrieve": nodes.retrieve, "web_search": nodes.web_research, "merge": nodes.merge,
        "extract": nodes.extract, "persist_candidates": nodes.persist_candidates, "assess": nodes.assess,
        "propose_pack": nodes.propose_pack, "load_pack": nodes.load_pack, "draft": nodes.draft,
        "reject_draft": nodes.reject_draft}
    for name, function in mapping.items():
        graph.add_node(name, function, retry_policy=policy)
    graph.add_conditional_edges(START, lambda s: "load_pack" if s.get("pack_id") else "interpret")
    graph.add_conditional_edges("interpret", lambda s: "ask_clarification" if s["interpretation"]["blocking_questions"] else "plan")
    graph.add_edge("ask_clarification", "clarify")
    graph.add_edge("clarify", "interpret")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("plan", "web_search")
    graph.add_edge(["retrieve", "web_search"], "merge")
    graph.add_edge("merge", "extract")
    graph.add_edge("extract", "persist_candidates")
    graph.add_edge("persist_candidates", "assess")
    graph.add_conditional_edges("assess", lambda s: "plan" if s["assessment"]["gaps"] and
        not any(a["status"] == "supported" for a in s["assessment"]["assessments"]) and
        s["round"] < s["context"]["max_research_rounds"] else "propose_pack")
    graph.add_edge("propose_pack", "draft")
    graph.add_edge("load_pack", "draft")
    # A wording-only edit cannot silently turn into browsing/new factual work.
    graph.add_conditional_edges("draft", lambda s: END if not s["draft_error"] else (
        "plan" if s["round"] > 0 and s["round"] < s["context"]["max_research_rounds"] else "reject_draft"))
    return graph.compile(checkpointer=checkpointer)
