"""Compact model vocabulary; canonical taxonomy records remain unchanged in storage."""
from collections import Counter, defaultdict


def interpretation_taxonomy(context: dict) -> tuple[dict, dict[str, str]]:
    """Use short codes in prompts and map model selections to canonical IDs.

    All concepts, labels, ambiguities and directed relationships are retained.
    Canonical UUIDs, row timestamps and repeated reviewer provenance stay out of
    the prompt. No lexical shortlist discards potentially relevant concepts.
    """
    rows = context.get("concepts", [])
    codes = Counter(str(row.get("code", "")) for row in rows)
    canonical_ids, tokens = {}, {}
    for index, row in enumerate(rows):
        canonical = str(row.get("concept_id", row.get("id")))
        code = str(row.get("code", ""))
        token = code if code and codes[code] == 1 else f"@{index}"
        # Reserve fallback tokens even for unusual operator-supplied codes.
        if token in canonical_ids:
            token = f"@{index}:{canonical}"
        canonical_ids[token], tokens[canonical] = canonical, token
    aliases = defaultdict(list)
    for row in context.get("labels", []):
        aliases[str(row.get("concept_id"))].append([
            row.get("language"), row.get("label"), row.get("preferred"), row.get("ambiguity", {})])
    vocabulary = {}
    for row in rows:
        canonical = str(row.get("concept_id", row.get("id")))
        value = {key: row[key] for key in ("definition", "facet") if key in row}
        if row.get("code") and tokens[canonical] != str(row["code"]):
            value["code"] = row["code"]
        notes = {key: item for key, item in row.get("notes", {}).items() if key != "reviewer"}
        if notes:
            value["notes"] = notes
        labels = aliases.pop(canonical, [])
        if labels:
            value["labels"] = labels
        vocabulary[tokens[canonical]] = value
    result = {"concepts": vocabulary,
        "instructions": "Select keys from concepts. Related/broader links are hints, not equivalence.",
        "label_columns": ["language", "label", "preferred", "ambiguity"],
        "relation_columns": ["subject", "kind", "object"],
        "relations": [[tokens.get(str(row["subject_id"]), str(row["subject_id"])), row["kind"],
            tokens.get(str(row["object_id"]), str(row["object_id"]))] for row in context.get("relations", [])]}
    for name in ("version", "profile"):
        if name in context:
            result[name] = {key: value for key, value in context[name].items()
                if key not in {"created_at", "namespace"}}
    for name in ("limitations", "note"):
        if name in context:
            result[name] = context[name]
    if aliases:
        result["unbound_labels"] = dict(aliases)
    return result, canonical_ids
