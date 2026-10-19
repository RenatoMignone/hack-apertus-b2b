"""Idempotent graph persistence. All writes reuse evidence/draft repository gates."""
from datetime import datetime, timedelta

from sqlalchemy import select

from backend.contracts.services import EvidenceRejected
from backend.data import schema as t


class Outputs:
    def ask_questions(self, access, run_id, questions, attempt):
        def callback(c):
            repo = self.repositories(c)[0]
            return {"questions": [{"id": str(repo.ask(access, run_id, field="clarification", reason=q)),
                                   "question": q} for q in questions]}
        return self.commit_stage(access, run_id, f"questions.{attempt}", {"questions": questions}, {}, callback)

    def save_interpretation(self, access, run_id, interpretation):
        def callback(c):
            key = self.repositories(c)[2].interpret(access, run_id, interpretation)
            return {"interpretation_id": str(key)}
        return self.commit_stage(access, run_id, "interpretation.persist", interpretation.model_dump(mode="json"), {}, callback)

    def save_pack(self, access, run_id, pack, assessment):
        def callback(c):
            _, _, repo, _ = self.repositories(c)
            for item in assessment.assessments:
                old = c.execute(select(t.assessments.c.payload).where(t.assessments.c.run_id == run_id,
                    t.assessments.c.claim_id == item.claim_id)).scalar_one_or_none()
                if old is None:
                    repo.assess(access, run_id, item)
                elif old != item.model_dump(mode="json"):
                    raise EvidenceRejected()
            evidence_ids = {e for claim in pack.claims for e in claim.evidence_ids}
            local = list(c.execute(select(t.spans.c.evidence_id).join(t.scopes).where(
                t.spans.c.evidence_id.in_(evidence_ids), t.scopes.c.kind == "case",
                t.scopes.c.case_id == pack_context_case(c, run_id))).scalars())
            manifest = repo.manifest(access, run_id, local) if local else None
            pack_id = repo.freeze(access, run_id, pack, manifest_id=manifest)
            created = c.execute(select(t.packs.c.created_at).where(t.packs.c.pack_id == pack_id)).scalar_one()
            config = c.execute(select(t.runs.c.configuration).where(t.runs.c.run_id == run_id)).scalar_one()
            deadline = datetime.fromisoformat(config['deadline_at'])
            allowance = timedelta(seconds=config.get('draft_deadline_seconds', 0))
            # Anchor to the immutable pack timestamp, not to retries or worker
            # restarts. Never extend beyond the research deadline + allowance.
            draft_deadline = min(max(deadline, created + allowance), deadline + allowance)
            return {"pack_id": str(pack_id), "draft_deadline_at": draft_deadline.isoformat()}
        return self.commit_stage(access, run_id, "pack.persist", pack.model_dump(mode="json"), {}, callback)

    def save_draft(self, access, context, pack_id, draft, assessment, expected_revision, parent_id):
        inputs = {"pack_id": str(pack_id), "draft": draft.model_dump(mode="json"), "revision": expected_revision}
        def callback(c):
            result = self.repositories(c)[1].create(access, context.case_id, pack_id, draft,
                expected_revision=expected_revision, assessment=assessment, parent_id=parent_id)
            return {"result_id": str(result)}
        return self.commit_stage(access, context.run_id, "draft.persist", inputs, {}, callback)


def pack_context_case(c, run_id):
    return c.execute(select(t.runs.c.case_id).where(t.runs.c.run_id == run_id)).scalar_one()
