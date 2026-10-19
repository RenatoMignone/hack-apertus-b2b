"""Tolerant display-label input; factual/public interpretation stays strict."""
from copy import deepcopy

from pydantic import Field, create_model

from backend.contracts.pipeline import CaseInterpretation

fields = {name: (field.annotation, deepcopy(field))
          for name, field in CaseInterpretation.model_fields.items()}
fields["activity_label"] = (str | list[str], Field(
    description="A short display label, preferably one to three words, e.g. glucose sensors."))
fields["ambiguities"][1].description = (
    "ONLY ambiguity in what the USER wants, requiring their answer before search. "
    "MUST be [] for a clear research request. Missing public facts are research_questions.")
fields["research_questions"][1].description = (
    "Questions the AGENT should research in sources: experts, facilities, projects, "
    "availability, suitability. These do not require user clarification.")
# Do not inherit public validators before translating the private wire shape.
InterpretationResponse = create_model("InterpretationResponse",
    __config__=CaseInterpretation.model_config, **fields)


def interpretation_value(value) -> CaseInterpretation:
    body = value.model_dump()
    label = body["activity_label"]
    label = " ".join(label) if isinstance(label, list) else label
    label = " ".join(label.split())
    if not label:
        raise ValueError("activity_label must not be empty")
    if len(label.split()) > 3:
        # Presentation must not abort research. Preserve ALL scientific wording
        # as a query aid, never truncate the intent to fit a display field.
        body["search_terms"] = list(dict.fromkeys([*body["search_terms"], label]))
        label = "Research request"
    body["activity_label"] = label
    if (not body["needs"] or not body["bern_intents"] or body["ambiguities"]) and not body["blocking_questions"]:
        raise ValueError(
            "blocking_questions: add a targeted question for each material ambiguity in USER intent, "
            "or the missing capability/Bern objective. Preserve unresolved ambiguities; do not invent "
            "answers. Example: unspecified device capability -> 'Which technical capability do you "
            "need in Bern?' Unknown researchers or facility availability belong in research_questions "
            "and do not block a clear capability/objective request.")
    return CaseInterpretation.model_validate(body)
