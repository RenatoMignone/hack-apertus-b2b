"""Interpretation/parallel research graph nodes. All persistence uses a store port."""
import asyncio

from langgraph.types import interrupt

from backend.contracts.data import QueryPlan
from backend.contracts.pipeline import CaseInterpretation
from backend.contracts.services import (BudgetExceeded, InvalidModelOutput, RegisteredResearch,
    ResearchBundle, RunContext, ServiceUnavailable, WebResearchResult)
from backend.workflows.execution import Execution
from backend.workflows.research import merged, public_query, research_tools


class ResearchNodes:
    def __init__(self, store, reasoning, backbone, web, tracer=None):
        self.store, self.reasoning, self.backbone, self.web, self.tracer = store, reasoning, backbone, web, tracer

    def execution(self, state):
        return Execution(self.store, RunContext.model_validate(state["context"]), self.tracer)

    async def interpret(self, state):
        execution = self.execution(state)
        context = execution.context
        if state.get("clarification_round", 0) >= 3:
            raise InvalidModelOutput()
        taxonomy = await execution.call("taxonomy", {}, lambda: self.backbone.taxonomy(context))
        result = await execution.call(f"interpret.{state.get('clarification_round', 0)}", {"message": state["message"]},
            lambda: self.reasoning.interpret(state["message"], taxonomy, context))
        interpretation = CaseInterpretation.model_validate(result)
        if not interpretation.blocking_questions:
            await asyncio.to_thread(self.store.save_interpretation, context.access, context.run_id, interpretation)
        return {"interpretation": result}

    async def questions(self, state):
        context = self.execution(state).context
        interpretation = CaseInterpretation.model_validate(state["interpretation"])
        return await asyncio.to_thread(self.store.ask_questions, context.access, context.run_id,
                                       interpretation.blocking_questions, state["clarification_round"])

    async def clarify(self, state):
        # Nothing with external side effects before interrupt; this node restarts on resume.
        response = interrupt({"questions": state["questions"], "input_id": state["context"]["input_id"]})
        if not isinstance(response, dict) or not response.get("answers"):
            raise InvalidModelOutput()
        return {"message": state["message"] + "\n\nClarification:\n" + "\n".join(
            f"{row['reason']}: {row['message']}" for row in response["answers"]),
            "clarification_round": state["clarification_round"] + 1}

    async def plan(self, state):
        context = self.execution(state).context
        interpretation = CaseInterpretation.model_validate(state["interpretation"])
        round_number = state["round"] + 1
        if round_number > context.max_research_rounds:
            raise BudgetExceeded()
        variants = list(dict.fromkeys(interpretation.search_terms))[:5]
        plan = QueryPlan(original_request=state["message"], run_id=context.run_id, case_id=context.case_id,
            input_revision_id=context.input_id, variants=variants, snapshot_id=context.snapshot_id,
            profile_id=context.profile_id, taxonomy_version_id=context.taxonomy_version_id,
            build_id=context.build_id, embedding_config_hash=context.embedding_config_hash, round_number=round_number)
        return {"query": plan.model_dump(mode="json"), "round": round_number, "draft_error": False}

    async def retrieve(self, state):
        execution = self.execution(state)
        plan = QueryPlan.model_validate(state["query"])
        result = await execution.call(f"retrieve.{state['round']}", state["query"],
                                     lambda: self.backbone.retrieve(plan, execution.context))
        research = ResearchBundle.model_validate(result)
        await asyncio.to_thread(self.store.validate_evidence, execution.context.access, execution.context.run_id, research.evidence)
        return {"db_research": result}

    async def web_research(self, state):
        execution = self.execution(state)
        context = execution.context
        used = state.get("tools_used", 0)
        unavailable = lambda reason: {"web_research": WebResearchResult(status="unavailable", limitations=[reason]).model_dump(mode="json")}
        if context.mode == "offline":
            return unavailable("web_disabled_offline")
        if not self.web:
            return unavailable("web_unconfigured")
        if used + 2 > context.max_tool_calls:
            return unavailable("web_tool_budget_exhausted")
        query = public_query(CaseInterpretation.model_validate(state["interpretation"]))
        if not query:
            return unavailable("no_public_search_terms")
        discover, fetch = research_tools(self.web, context)
        try:
            urls = await execution.call(f"discover.{state['round']}", {"query": query},
                                       lambda: discover.ainvoke({"query": query}))
            # URL selection is constrained before delegating redirect/network safety to C's fetcher.
            from backend.contracts.pipeline import canonical_url
            urls = list(dict.fromkeys(canonical_url(url) for url in urls))[:min(5, context.max_tool_calls - used - 1)]
            used += 1 + len(urls)  # C counts discovery and each fetched page independently.
            result = await execution.call(f"fetch.{state['round']}", {"urls": urls},
                                         lambda: fetch.ainvoke({"urls": urls}))
        except (ServiceUnavailable, BudgetExceeded) as error:
            return {**unavailable("web_tool_budget_exhausted" if isinstance(error, BudgetExceeded) else "web_unavailable"),
                    "tools_used": max(used, state.get("tools_used", 0) + 1)}
        return {"web_research": WebResearchResult.model_validate(result).model_dump(mode="json"), "tools_used": used}

    async def merge(self, state):
        execution = self.execution(state)
        web = WebResearchResult.model_validate(state["web_research"])
        db = ResearchBundle.model_validate(state["db_research"])
        if web.status == "completed":
            data = await execution.call(f"register.{state['round']}", web.model_dump(mode="json"),
                lambda: self.backbone.register_research(web, execution.context))
            registered = RegisteredResearch.model_validate(data)
        else:
            registered = RegisteredResearch(limitations=web.limitations or ["web_source_failure"])
        result = merged(db, registered)
        await asyncio.to_thread(self.store.validate_evidence, execution.context.access, execution.context.run_id, result.evidence)
        return {"research": result.model_dump(mode="json")}
