"""Export preparation and registration with exact current approval and access."""
from uuid import UUID

from sqlalchemy import select

from backend.contracts.data import ArtifactRef, configuration_hash
from backend.contracts.services import StaleRevision
from backend.data import schema as t
from backend.data.repositories.drafts import selection_hash


class VerifiedBytes:
    def __init__(self, reference, data):
        self.reference, self.data = reference, data

    def read(self, reference):
        if reference != self.reference:
            raise PermissionError()
        return self.data


class Exporting:
    def export_input(self, access, case_id, result_id, body):
        with self.session(access) as c:
            result = self._result(c, access, case_id, result_id)
            case = self.case(c, access, case_id)
            review = c.execute(select(t.reviews).where(t.reviews.c.review_id == UUID(body["review_id"]),
                t.reviews.c.result_id == result_id)).mappings().one()
            digest = selection_hash(c, result_id, require_complete=True)
            if (case["current_result_id"] != result_id or result["result_hash"] != body["expected_result_hash"]
                or digest != body["expected_selection_hash"] or review["decision"] != "accepted"
                or review["selection_hash"] != digest or review["result_hash"] != result["result_hash"]
                or configuration_hash(result["payload"]) != result["result_hash"]):
                raise StaleRevision()
            pack = c.execute(select(t.packs).where(t.packs.c.pack_id == result["pack_id"])).mappings().one()
            kept = list(c.execute(select(t.reasons.c.reason_key).join(t.reason_selections).where(
                t.reasons.c.result_id == result_id, t.reason_selections.c.selection == "kept")
                .order_by(t.reasons.c.reason_key)).scalars())
            return {"run_id": pack["run_id"], "draft": {k: v for k, v in result["payload"].items() if k != "validation"},
                    "kept": kept, "pack": dict(pack), "selection_hash": digest, "result_hash": result["result_hash"]}

    def queue_export(self, access, key, case_id, result_id, body):
        if self.settings.template_version in {"", "unconfigured"} or self.settings.renderer_version in {"", "unconfigured"}:
            from backend.contracts.services import ServiceUnavailable
            raise ServiceUnavailable()
        if body.get('format', 'pdf') == 'pptx' and not self.rich_outputs_available():
            from backend.contracts.services import ServiceUnavailable
            raise ServiceUnavailable()
        # Initial check is repeated inside the command transaction and before/after rendering.
        def callback(c):
            data = self.export_input_bound(c, access, case_id, result_id, body)
            job = self.enqueue(c, access, data["run_id"], "runtime.export",
                {"case_id": str(case_id), "result_id": str(result_id), **body}, suffix=key)
            return {"operation_id": str(job), "status_url": f"/api/v1/operations/{job}"}
        return self.command(access, key, f"export:{result_id}", body, callback)

    def export_input_bound(self, c, access, case_id, result_id, body):
        # Reuse the same transaction (including existing approval gates) without nested locks.
        from backend.application.persistence.store import RuntimeStore
        from backend.application.persistence.session import BoundEngine
        return RuntimeStore(BoundEngine(c), self.settings, self.artifacts).export_input(access, case_id, result_id, body)

    def register_export(self, access, job, reference, data):
        body = job["outputs"]["command"]
        case_id, result_id = UUID(body["case_id"]), UUID(body["result_id"])
        with self.session(access) as c:
            self.export_input_bound(c, access, case_id, result_id, body)
            old = c.execute(select(t.exports.c.export_id).where(t.exports.c.result_id == result_id,
                t.exports.c.review_id == UUID(body["review_id"]), t.exports.c.format == body.get("format", "pdf"), t.exports.c.status == "ready",
                t.exports.c.selection_hash == body["expected_selection_hash"],
                t.exports.c.template_version == self.settings.template_version,
                t.exports.c.renderer_version == self.settings.renderer_version)).scalar_one_or_none()
            if old:
                return old
            # The already written/read bytes are local here; no object/network operation under SQL locks.
            return self.repositories(c)[0].record_export(access, result_id, UUID(body["review_id"]), reference,
                artifacts=VerifiedBytes(reference, data), template_version=self.settings.template_version,
                renderer_version=self.settings.renderer_version, format=body.get("format", "pdf"))

    def download(self, access, case_id, export_id):
        with self.session(access) as c:
            self.case(c, access, case_id)
            row = c.execute(select(t.exports, t.results.c.case_id, t.artifacts).select_from(
                t.exports.join(t.results).join(t.artifacts)).where(t.exports.c.export_id == export_id,
                t.results.c.case_id == case_id)).mappings().one()
            if row["status"] != "ready":
                raise StaleRevision()
            result = c.execute(select(t.results).where(t.results.c.result_id == row["result_id"])).mappings().one()
            self.repositories(c)[0]._validate_pack(c, result["pack_id"])
            case = self.case(c, access, case_id)
            if (case["current_result_id"] != row["result_id"] or
                    selection_hash(c, row["result_id"], require_complete=True) != row["selection_hash"]):
                raise StaleRevision()
            reference = ArtifactRef(key=row["storage_key"], sha256=row["sha256"], mime=row["mime"], byte_count=row["byte_count"])
        return self.artifacts.read(reference)

    def export_view(self, access, case_id, export_id):
        with self.session(access) as c:
            self.case(c, access, case_id)
            record = c.execute(select(t.exports).join(t.results).where(t.exports.c.export_id == export_id,
                t.results.c.case_id == case_id)).mappings().one()
            self._result(c, access, case_id, record["result_id"])
            return {"export_id": str(export_id), "result_id": str(record["result_id"]), "status": record["status"],
                "format": record["format"], "download_url": f"/api/v1/cases/{case_id}/exports/{export_id}/download"
                    if record["status"] == "ready" else None}
