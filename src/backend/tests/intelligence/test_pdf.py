import asyncio
from io import BytesIO

import pytest

from backend.contracts.services import EvidenceRejected
from backend.reports.rendering import create_pdf_renderer


def render(report, claim, evidence):
    return asyncio.run(create_pdf_renderer().render(report))


def test_pdf_only_kept_reasons_exact_citations_and_determinism(pdf_input,claim,evidence):
    from pypdf import PdfReader
    pdf=render(pdf_input,claim,evidence)
    reader=PdfReader(BytesIO(pdf))
    text="\n".join(p.extract_text() for p in reader.pages)
    assert pdf.startswith(b"%PDF") and pdf==render(pdf_input,claim,evidence)
    assert "Sensor development expertise" in text and "REJECTED MUST NOT APPEAR" not in text
    assert evidence.literal_text in " ".join(text.split()) and evidence.url in text
    assert "unreviewed" in text and "Expert availability remains unknown." in text
    assert any(p.get("/Annots") for p in reader.pages)


def test_unmapped_claim_cannot_export(pdf_input):
    with pytest.raises(EvidenceRejected):
        asyncio.run(create_pdf_renderer().render(pdf_input.model_copy(update={"claims":[]})))


@pytest.mark.parametrize("keys", [[],["missing"],["kept","kept"]])
def test_mutated_or_invalid_selection_rejected(pdf_input,claim,evidence,keys):
    bad=pdf_input.model_copy(update={"kept_reason_keys":keys})
    with pytest.raises(EvidenceRejected):
        render(bad,claim,evidence)


def test_long_content_unicode_and_markup_safe(pdf_input,claim,evidence):
    from pypdf import PdfReader
    report=pdf_input.model_copy(deep=True)
    report = report.model_copy(update={"draft": report.draft.model_copy(update={"reasons": [
        report.draft.reasons[0].model_copy(update={"text": "Glukose, études, ricerca <script> & text. "*150})]})})
    pdf=render(report,claim,evidence)
    reader=PdfReader(BytesIO(pdf))
    assert len(reader.pages)>1
    text="\n".join(p.extract_text() for p in reader.pages)
    assert "<script>" in text and "études" in text
    assert all("Page " in p.extract_text() for p in reader.pages)


def test_adjacent_label_and_web_status_preserved(pdf_input,claim,evidence):
    from pypdf import PdfReader
    report=pdf_input.model_copy(deep=True)
    report = report.model_copy(update={"draft": report.draft.model_copy(update={"reasons": [
        report.draft.reasons[0].model_copy(update={"kind": "idea"})]})})
    text="\n".join(p.extract_text() for p in PdfReader(BytesIO(render(report,claim,evidence))).pages)
    assert "requires expert validation" in text and "unreviewed" in text


def test_pdf_rejects_missing_source_and_direct_label_for_adjacent_claim(pdf_input,claim,evidence):
    with pytest.raises(EvidenceRejected):
        render(pdf_input.model_copy(update={"evidence":[]}),claim,evidence)
    bad=pdf_input.model_copy(update={"claims":[claim.model_copy(update={"kind":"adjacent"})]})
    with pytest.raises(EvidenceRejected):
        render(bad,claim,evidence)
