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
    pending_gaps: list[str]
    research_exhausted: bool
    query_history: list[str]
    fetched_urls: list[str]
    web_query: str
    search_observations: list[dict]
    round_started_at: str
    research_deadline_at: str
    reuse_prepared_evidence: bool


def build_graph(store, reasoning, backbone, web, checkpointer, tracer=None, *, memory=None):
    nodes = PipelineNodes(store, reasoning, backbone, web, tracer, memory=memory)
    graph = StateGraph(CaseState)
    policy = RetryPolicy(initial_interval=.2, max_interval=1, max_attempts=2, retry_on=ServiceUnavailable)
    mapping = {"interpret": nodes.interpret, "ask_clarification": nodes.questions, "clarify": nodes.clarify,
        "plan": nodes.plan, "retrieve": nodes.retrieve, "web_search": nodes.web_research, "merge": nodes.merge,
        "extract": nodes.extract, "persist_candidates": nodes.persist_candidates, "assess": nodes.assess,
        "propose_pack": nodes.propose_pack, "freeze_pack": nodes.freeze_pack,
        "load_pack": nodes.load_pack, "draft": nodes.draft,
        "reject_draft": nodes.reject_draft}
    for name, function in mapping.items():
        graph.add_node(name, function, retry_policy=policy)
    graph.add_conditional_edges(START, lambda s: "load_pack" if s.get("pack_id") else "interpret")
    graph.add_conditional_edges("interpret", lambda s: "ask_clarification" if s["interpretation"]["blocking_questions"] else "plan")
    graph.add_edge("ask_clarification", "clarify")
    graph.add_edge("clarify", "interpret")
    graph.add_conditional_edges("plan", lambda s: ("reject_draft" if s.get("draft_error") else "freeze_pack")
        if s.get("research_exhausted") else ["retrieve", "web_search"])
    graph.add_edge(["retrieve", "web_search"], "merge")
    graph.add_conditional_edges("merge", lambda s: (
        "reject_draft" if s.get("pack_id") else "freeze_pack") if s.get("reuse_prepared_evidence") else "extract")
    graph.add_edge("extract", "persist_candidates")
    graph.add_edge("persist_candidates", "assess")
    graph.add_edge("assess", "propose_pack")
    graph.add_conditional_edges("propose_pack", lambda s: "plan" if s.get("pending_gaps") and
        s["round"] < s["context"]["max_research_rounds"] else "freeze_pack")
    graph.add_edge("freeze_pack", "draft")
    graph.add_edge("load_pack", "draft")
    # A wording-only edit cannot silently turn into browsing/new factual work.
    graph.add_conditional_edges("draft", lambda s: END if not s["draft_error"] else (
        "plan" if s["round"] > 0 and s["round"] < s["context"]["max_research_rounds"] else "reject_draft"))
    return graph.compile(checkpointer=checkpointer)
