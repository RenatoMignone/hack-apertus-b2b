"""Constrained model response shape; the public interpretation stays unchanged."""
from copy import deepcopy
from typing import Annotated

from pydantic import BeforeValidator, Field, StringConstraints, create_model

from backend.contracts.pipeline import CaseInterpretation

Word = Annotated[str, StringConstraints(pattern=r"^\S+$")]
# Existing fixtures/adapters may provide the public string shape. Apply exactly
# the same word-count validation after splitting; never discard excess words.
ActivityWords = Annotated[list[Word], BeforeValidator(
    lambda value: value.split() if isinstance(value, str) else value)]
fields = {name: (field.annotation, deepcopy(field))
          for name, field in CaseInterpretation.model_fields.items()}
fields["activity_label"] = (ActivityWords, Field(min_length=1, max_length=3,
    description="An array of one to three individual words, e.g. [glucose, sensors]. Each item is exactly one word. Longer descriptions belong in needs/company_summary."))
InterpretationResponse = create_model("InterpretationResponse",
    __config__=CaseInterpretation.model_config, **fields)


def interpretation_value(value) -> CaseInterpretation:
    return CaseInterpretation.model_validate({**value.model_dump(),
        "activity_label": " ".join(value.activity_label)})
