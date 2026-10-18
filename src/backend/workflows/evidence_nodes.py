"""Extraction, assessment, freeze and draft nodes with explicit factual gates."""
import asyncio
from uuid import UUID

from backend.contracts.pipeline import DraftAssessment, DraftRevision, ReportEvidencePack
from backend.contracts.services import (EvidenceAssessment, EvidenceRecord, EvidenceRejected,
    ExtractionBatch, InvalidModelOutput, PersistedClaims, ResearchBundle)
from backend.workflows.nodes import ResearchNodes


class PipelineNodes(ResearchNodes):
    async def extract(self, state):
        from backend.contracts.pipeline import CaseInterpretation
        execution = self.execution(state)
        interpretation = CaseInterpretation.model_validate(state["interpretation"])
        research = ResearchBundle.model_validate(state["research"])
        raw = await execution.call(f"extract.{state['round']}", {"interpretation": state["interpretation"], "research": state["research"]},
            lambda: self.reasoning.extract(interpretation, research, execution.context))
        batch = ExtractionBatch.model_validate(raw)
        eligible = {record.evidence_id for record in research.evidence}
        if any(not set(item.evidence_ids) <= eligible for item in [*batch.entities, *batch.claims]):
            raise EvidenceRejected()
        return {"batch": raw}

    async def persist_candidates(self, state):
        execution = self.execution(state)
        batch = ExtractionBatch.model_validate(state["batch"])
        raw = await execution.call(f"persist_extraction.{state['round']}", state["batch"],
            lambda: self.backbone.persist_extraction(batch, execution.context))
        claims = PersistedClaims.model_validate(raw)
        if len({c.claim_id for c in claims.claims}) != len(claims.claims) or {c.text for c in claims.claims} != {c.statement for c in batch.claims}:
            raise EvidenceRejected()
        ids = sorted({e for claim in claims.claims for e in claim.evidence_ids}, key=str)
        records = await execution.call(f"evidence.{state['round']}", {"ids": list(map(str, ids))},
            lambda: self.backbone.read_evidence(ids, execution.context))
        evidence = [EvidenceRecord.model_validate(record) for record in records]
        if {e.evidence_id for e in evidence} != set(ids):
            raise EvidenceRejected()
        await asyncio.to_thread(self.store.validate_evidence, execution.context.access, execution.context.run_id, evidence)
        return {"claims": raw, "claim_evidence": records}

    async def assess(self, state):
        execution = self.execution(state)
        claims = PersistedClaims.model_validate(state["claims"])
        evidence = [EvidenceRecord.model_validate(e) for e in state["claim_evidence"]]
        raw = await execution.call(f"assess.{state['round']}", {"claims": state["claims"], "evidence": state["claim_evidence"]},
            lambda: self.reasoning.assess(claims, evidence, execution.context))
        assessed = EvidenceAssessment.model_validate(raw)
        by_id = {item.claim_id: item for item in assessed.assessments}
        if len(by_id) != len(assessed.assessments) or set(by_id) != {c.claim_id for c in claims.claims}:
            raise EvidenceRejected()
        for claim in claims.claims:
            item = by_id[claim.claim_id]
            if item.statement != claim.text or set(item.evidence_ids) != set(claim.evidence_ids):
                raise EvidenceRejected()
        return {"assessment": raw}

    async def propose_pack(self, state):
        from backend.contracts.pipeline import CaseInterpretation
        execution = self.execution(state)
        claims = PersistedClaims.model_validate(state["claims"])
        assessment = EvidenceAssessment.model_validate(state["assessment"])
        research = ResearchBundle.model_validate(state["research"])
        # Supply the canonical remapped support too, never only stale pre-extraction IDs.
        records = {e.evidence_id: e for e in research.evidence}
        records.update({UUID(e["evidence_id"]): EvidenceRecord.model_validate(e) for e in state["claim_evidence"]})
        research = research.model_copy(update={"evidence": list(records.values())})
        raw = await execution.call(f"propose_pack.{state['round']}", {"claims": state["claims"], "assessment": state["assessment"],
            "research": research.model_dump(mode="json")}, lambda: self.reasoning.propose_pack(
                CaseInterpretation.model_validate(state["interpretation"]), claims, assessment, research, execution.context))
        pack = ReportEvidencePack.model_validate(raw)
        supported = {item.claim_id for item in assessment.assessments if item.status == "supported"}
        proposals = {c.claim_id: c for c in claims.claims}
        if pack.interpretation.model_dump(mode="json") != state["interpretation"]:
            raise EvidenceRejected()
        for claim in pack.claims:
            if claim.claim_id not in supported or claim != proposals[claim.claim_id]:
                raise EvidenceRejected()
        gaps = list(dict.fromkeys([*pack.gaps, *assessment.gaps, *research.limitations]))
        if not pack.claims and not gaps:
            gaps = ["No supported matches in the available sources"]
        body = pack.model_dump(mode="json")
        body.update(gaps=gaps, outcome="no_match" if not pack.claims else ("partial" if gaps else pack.outcome))
        pack = ReportEvidencePack.model_validate(body)
        saved = await asyncio.to_thread(self.store.save_pack, execution.context.access, execution.context.run_id, pack, assessment)
        return {"pack": pack.model_dump(mode="json"), **saved}

    async def load_pack(self, state):
        execution = self.execution(state)
        record = await asyncio.to_thread(self.store.pack, execution.context.access, UUID(state["pack_id"]))
        return {"pack": ReportEvidencePack.model_validate(record["payload"]).model_dump(mode="json")}

    async def draft(self, state):
        execution = self.execution(state)
        pack = ReportEvidencePack.model_validate(state["pack"])
        try:
            raw = await execution.call(f"draft.{state['round']}", {"pack_id": state["pack_id"], "instruction": state["instruction"]},
                lambda: self.reasoning.draft(pack, state["instruction"], execution.context))
            draft = DraftRevision.model_validate(raw)
            supported = {claim.claim_id for claim in pack.claims}
            if any(not set(reason.claim_ids) <= supported for reason in draft.reasons):
                raise EvidenceRejected()
            check = await execution.call(f"draft_assessment.{state['round']}", {"draft": raw, "pack_id": state["pack_id"]},
                lambda: self.reasoning.assess_draft(draft, pack, execution.context))
            assessment = DraftAssessment.model_validate(check)
            from backend.contracts.data import configuration_hash
            if assessment.status != "supported" or assessment.draft_hash != configuration_hash(draft.model_dump(mode="json")):
                raise EvidenceRejected()
        except (EvidenceRejected, InvalidModelOutput):
            return {"draft_error": True}
        saved = await asyncio.to_thread(self.store.save_draft, execution.context.access, execution.context,
            UUID(state["pack_id"]), draft, assessment, state["expected_revision"],
            UUID(state["parent_result_id"]) if state.get("parent_result_id") else None)
        return {**saved, "draft_error": False}

    async def reject_draft(self, state):
        raise EvidenceRejected()
