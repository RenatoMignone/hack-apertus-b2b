import re
from uuid import uuid4, uuid5

from sqlalchemy import insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import Span, configuration_hash, content_hash
from backend.data import schema as tables
from backend.data.database import require_scope, transaction


TAG_POLICY = {"max_topic_labels": 3, "max_parent_domains": 3, "max_specific_subjects": 5,
    "max_attributes_per_subject": 4, "primary_label_first": True, "classification_unit": "document_version",
    "unclassified_allowed": True}


def mesh_vocabulary(tree_bytes, manifest):
    if content_hash(tree_bytes) != manifest["source_sha256"]:
        raise ValueError("MeSH release artifact hash mismatch")
    categories = manifest["category_labels"]
    if manifest.get("tag_policy", TAG_POLICY) != TAG_POLICY:
        raise ValueError("MeSH tag policy differs from the versioned implementation")
    subcategories = {}
    for line in tree_bytes.decode("utf-8").splitlines():
        label, separator, code = line.rpartition(";")
        if separator and re.fullmatch(r"[A-Z]\d{2}", code):
            if code[0] not in categories or not label.strip():
                raise ValueError("invalid MeSH subcategory")
            subcategories[code] = label.strip()
    if not subcategories or set(code[0] for code in subcategories) != set(categories):
        raise ValueError("incomplete MeSH top-level release")
    concepts = [{"code": code, "definition": label, "facet": "category" if len(code) == 1 else "subcategory",
        "labels": {"en": [label]}} for code, label in sorted({**categories, **subcategories}.items())]
    concepts.append({"code": "unknown", "definition": "System abstention: no supported MeSH tag; not an NLM MeSH category.",
        "facet": "system", "labels": {"en": ["Unknown"]}})
    relations = []
    for code in sorted(subcategories):
        relations.extend([{"subject": code, "object": code[0], "kind": "broader"},
            {"subject": code[0], "object": code, "kind": "narrower"}])
    return {"name": manifest["name"], "version": manifest["version"], "status": "reviewed",
        "source": {"url": manifest["source_url"], "sha256": manifest["source_sha256"], "release": manifest["release"]},
        "tag_levels": ["category", "subcategory"], "tag_policy": manifest.get("tag_policy", TAG_POLICY),
        "specific_subjects": "Evidence-backed named subjects and attributes; not new MeSH branches or entity types",
        "concepts": concepts, "relations": relations}


def category_tags(tree_numbers, vocabulary):
    allowed = {item["code"] for item in vocabulary["concepts"] if item["facet"] != "system"}
    result = set()
    for value in tree_numbers:
        if not re.fullmatch(r"[A-Z]\d{2}(?:\.\d{3})*|[A-Z]", value):
            raise ValueError("invalid MeSH tree number")
        codes = [value[0]] if len(value) == 1 else [value[0], value.split(".")[0]]
        if not set(codes) <= allowed:
            raise ValueError("MeSH category absent from pinned release")
        result.update(codes)
    return sorted(result)


class MeSHTagger:
    def __init__(self, engine):
        self.engine = engine

    def _span(self, connection, version, span):
        span.validate_body(version["body_text"])
        evidence_id = connection.execute(select(tables.spans.c.evidence_id).where(
            tables.spans.c.document_version_id == version["document_version_id"], tables.spans.c.char_start == span.char_start,
            tables.spans.c.char_end == span.char_end)).scalar_one_or_none()
        if not evidence_id:
            evidence_id = uuid4()
            connection.execute(insert(tables.spans).values(evidence_id=evidence_id, document_version_id=version["document_version_id"],
                scope_id=version["scope_id"], char_start=span.char_start, char_end=span.char_end, literal_text=span.text,
                heading_path=span.heading_path, page=span.page, extraction_method="mesh-subject-support"))
        return evidence_id

    def assign(self, access, version_id, taxonomy_version_id, proposals, *, reviewer=None, subjects=()):
        if any(not re.fullmatch(r"[A-Z](?:\d{2})?", proposal["code"]) for proposal in proposals):
            raise ValueError("only MeSH categories and subcategories can be assigned")
        proposals = [proposal for proposal in proposals if len(proposal["code"]) > 1
            or not any(len(other["code"]) > 1 and other["code"].startswith(proposal["code"]) for other in proposals)]
        proposed_codes = {proposal["code"] for proposal in proposals}
        if len(proposed_codes) > TAG_POLICY["max_topic_labels"] or len(subjects) > TAG_POLICY["max_specific_subjects"]:
            raise ValueError("document label or specific-subject budget exceeded")
        if any(len(subject.attributes) > TAG_POLICY["max_attributes_per_subject"] for subject in subjects):
            raise ValueError("specific-subject attribute budget exceeded")
        with transaction(self.engine, access) as connection:
            version = connection.execute(select(tables.versions).where(tables.versions.c.document_version_id == version_id)).mappings().one()
            require_scope(connection, version["scope_id"], write=True)
            taxonomy = connection.execute(select(tables.taxonomies).where(tables.taxonomies.c.taxonomy_version_id == taxonomy_version_id,
                tables.taxonomies.c.name == "mesh-category-subcategory", tables.taxonomies.c.status == "reviewed")).mappings().one()
            if not taxonomy["artifact_hash"]:
                raise ValueError("pinned MeSH artifact required")
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:version,0))"),
                {"version": str(version_id) + str(taxonomy_version_id)})
            existing_codes = set(connection.execute(select(tables.concepts.c.code).join(tables.assignments).where(
                tables.assignments.c.document_version_id == version_id, tables.concepts.c.taxonomy_version_id == taxonomy_version_id,
                tables.concepts.c.facet == "subcategory")).scalars())
            if len(existing_codes | {code for code in proposed_codes if len(code) > 1}) > TAG_POLICY["max_topic_labels"]:
                raise ValueError("accumulated document topic-label budget exceeded")
            existing_domains = set(connection.execute(select(tables.concepts.c.code).join(tables.assignments).where(
                tables.assignments.c.document_version_id == version_id, tables.concepts.c.taxonomy_version_id == taxonomy_version_id,
                tables.concepts.c.facet == "category")).scalars())
            if len(existing_domains | {code[0] for code in proposed_codes}) > TAG_POLICY["max_parent_domains"]:
                raise ValueError("accumulated document domain-label budget exceeded")
            assignments = []
            assigned_tags = set()
            for priority, proposal in enumerate(proposals, start=1):
                span = proposal["span"]
                span.validate_body(version["body_text"])
                code = proposal["code"]
                if not re.fullmatch(r"[A-Z](?:\d{2})?", code):
                    raise ValueError("only MeSH categories and subcategories can be assigned")
                evidence_id = connection.execute(select(tables.spans.c.evidence_id).where(tables.spans.c.document_version_id == version_id,
                    tables.spans.c.char_start == span.char_start, tables.spans.c.char_end == span.char_end)).scalar_one_or_none()
                if not evidence_id:
                    evidence_id = uuid4()
                    connection.execute(insert(tables.spans).values(evidence_id=evidence_id, document_version_id=version_id,
                        scope_id=version["scope_id"], char_start=span.char_start, char_end=span.char_end,
                        literal_text=span.text, heading_path=span.heading_path, page=span.page, extraction_method="mesh-tag-support"))
                for tag in dict.fromkeys([code[0], code]):
                    if tag in assigned_tags:
                        continue
                    assigned_tags.add(tag)
                    concept_id = connection.execute(select(tables.concepts.c.concept_id).where(tables.concepts.c.taxonomy_version_id == taxonomy_version_id,
                        tables.concepts.c.code == tag)).scalar_one()
                    metadata = {"version_id": str(version_id), "taxonomy_id": str(taxonomy_version_id), "code": tag,
                        "evidence_id": str(evidence_id), "reviewer": reviewer, "priority": priority,
                        "primary": priority == 1}
                    assignment_id = uuid5(version_id, configuration_hash(metadata))
                    derivation_id = uuid5(assignment_id, "mesh-tagging")
                    connection.execute(pg_insert(tables.derivations).values(derivation_id=derivation_id, scope_id=version["scope_id"],
                        inputs=metadata, configuration_hash=configuration_hash({"mesh_tagging": 1}), output_hash=configuration_hash(metadata),
                        status="accepted" if reviewer else "needs_review").on_conflict_do_nothing())
                    connection.execute(pg_insert(tables.assignments).values(assignment_id=assignment_id, scope_id=version["scope_id"],
                        concept_id=concept_id, document_version_id=version_id, derivation_id=derivation_id, mapping_kind="direct",
                        status="accepted" if reviewer else "needs_review").on_conflict_do_nothing())
                    connection.execute(pg_insert(tables.assignment_evidence).values(assignment_id=assignment_id, evidence_id=evidence_id).on_conflict_do_nothing())
                    assignments.append(assignment_id)
            existing_subjects = connection.execute(select(tables.derivations.c.inputs).where(tables.derivations.c.scope_id == version["scope_id"],
                tables.derivations.c.inputs["kind"].astext == "specific_subject",
                tables.derivations.c.inputs["version_id"].astext == str(version_id),
                tables.derivations.c.inputs["taxonomy_version_id"].astext == str(taxonomy_version_id))).scalars().all()
            names = {item["name"].casefold() for item in existing_subjects} | {subject.name.casefold() for subject in subjects}
            if len(names) > TAG_POLICY["max_specific_subjects"]:
                raise ValueError("accumulated document specific-subject budget exceeded")
            for subject in subjects:
                subject.span.validate_body(version["body_text"])
                if subject.name.casefold() not in subject.span.text.casefold():
                    raise ValueError("specific subject must occur in its exact source support")
                for attribute in subject.attributes:
                    attribute.span.validate_body(version["body_text"])
                    if attribute.value.casefold() not in attribute.span.text.casefold():
                        raise ValueError("subject attribute must occur explicitly in its source support")
                metadata = {"version_id": str(version_id), "taxonomy_version_id": str(taxonomy_version_id),
                    **subject.model_dump(mode="json", exclude={"kind"}), "subject_kind": subject.kind, "kind": "specific_subject",
                    "evidence_id": str(self._span(connection, version, subject.span)), "reviewer": reviewer}
                metadata["attributes"] = [{**attribute.model_dump(mode="json"),
                    "evidence_id": str(self._span(connection, version, attribute.span))} for attribute in subject.attributes]
                digest = configuration_hash(metadata)
                connection.execute(pg_insert(tables.derivations).values(derivation_id=uuid5(version_id, digest), scope_id=version["scope_id"],
                    inputs=metadata, configuration_hash=configuration_hash({"mesh_subjects": 1}), output_hash=digest,
                    status="accepted" if reviewer else "needs_review").on_conflict_do_nothing())
            return list(dict.fromkeys(assignments))
