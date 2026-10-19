"""Deterministic authorized PDF rendering; no model, lookup, network or SQL."""
from __future__ import annotations

import asyncio
from functools import partial
from html import escape
from io import BytesIO
from pathlib import Path
from threading import RLock
from uuid import UUID

from backend.contracts.services import EvidenceRejected, PdfInput, ServiceUnavailable

_FONT_LOCK = RLock()


class ReportLabPdfRenderer:
    def __init__(self, *, logo_path: Path | None = None, max_text_chars: int = 180000):
        self.logo_path = logo_path or Path(__file__).resolve().parents[4] / \
            "docs/provided_material/Logo_SF_BE_EN.png"
        self.max_text_chars = max_text_chars

    async def render(self, report: PdfInput) -> bytes:
        try:
            report = PdfInput.model_validate(report.model_dump(mode="json"))
        except ValueError:
            raise EvidenceRejected() from None
        if len(report.model_dump_json()) > self.max_text_chars:
            raise EvidenceRejected()
        records = {e.evidence_id: e for e in report.evidence}
        if len(records) != len(report.evidence):
            raise EvidenceRejected()
        kept = [r for r in report.draft.reasons if r.id in set(report.kept_reason_keys)]
        if not kept or len(kept) != len(report.kept_reason_keys):
            raise EvidenceRejected()
        claims = {c.claim_id: c for c in report.claims}
        if len(claims) != len(report.claims):
            raise EvidenceRejected()
        mapping = {c.claim_id: c.evidence_ids for c in report.claims}
        for reason in kept:
            for cid in reason.claim_ids:
                if not mapping.get(cid) or not set(mapping[cid]) <= records.keys():
                    raise EvidenceRejected()
                if claims[cid].kind == "adjacent" and reason.kind != "idea":
                    raise EvidenceRejected()
        # Copy only selected source records; rejected-card material never leaks to export.
        ids = list(dict.fromkeys(e for r in kept for c in r.claim_ids for e in mapping[c]))
        return await asyncio.to_thread(self._render, report, kept, [records[e] for e in ids], mapping)

    def _render(self, report, kept, evidence, mapping):
        try:
            import reportlab
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_LEFT
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.utils import ImageReader
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen.canvas import Canvas
            from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
        except ImportError:
            raise ServiceUnavailable() from None
        fonts = Path(reportlab.__file__).parent / "fonts"
        if not self.logo_path.is_file() or not (fonts / "Vera.ttf").is_file():
            raise ServiceUnavailable()
        with _FONT_LOCK:
            if "NavigatorVera" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("NavigatorVera", str(fonts / "Vera.ttf")))
                pdfmetrics.registerFont(TTFont("NavigatorVeraBold", str(fonts / "VeraBd.ttf")))
                pdfmetrics.registerFontFamily("NavigatorVera", normal="NavigatorVera", bold="NavigatorVeraBold")
        ink, red = colors.HexColor("#193238"), colors.HexColor("#bc242d")
        style = ParagraphStyle("body", fontName="NavigatorVera", fontSize=10, leading=15,
                               textColor=ink, spaceAfter=9, splitLongWords=True)
        title = ParagraphStyle("title", parent=style, fontName="NavigatorVeraBold", fontSize=23,
                               leading=29, spaceAfter=16)
        heading = ParagraphStyle("heading", parent=style, fontName="NavigatorVeraBold", fontSize=13,
                                 leading=18, spaceBefore=13, spaceAfter=7, keepWithNext=True)
        small = ParagraphStyle("small", parent=style, fontSize=8, leading=12, alignment=TA_LEFT)
        quote = ParagraphStyle("quote", parent=small, leftIndent=11, borderColor=red,
                               borderWidth=1, borderPadding=8, spaceBefore=7, spaceAfter=15)
        def para(text, st=style):
            return Paragraph(escape(str(text)).replace("\n", "<br/>"), st)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=(595.276, 841.89), leftMargin=48,
            rightMargin=48, topMargin=42, bottomMargin=45, title="Bern opportunity brief",
            author="Bern Economic Development Agency", pageCompression=1, invariant=1)
        width, height = ImageReader(str(self.logo_path)).getSize()
        story = [Image(str(self.logo_path), width=190, height=190 * height / width, hAlign="LEFT"),
                 Spacer(1, 24), para("Bern opportunity brief", title),
                 para("Reviewed opportunities and supporting public evidence", small)]
        if report.interpretation:
            company = report.interpretation
            story.append(para(company.company_name or "Company context", heading))
            story.append(para("Operator-provided context; not independently verified", small))
            story.append(para(company.company_summary))
            for label, values in (("Bern objectives", company.bern_intents), ("Needs", company.needs)):
                if values:
                    story.append(para(label, heading))
                    story.extend(para("- " + value) for value in values)
        if report.business_context and report.business_context.lines():
            story.append(para('Company plans', heading))
            story.append(para('Manually entered operator plans; not actual economic impact', small))
            story.extend(para(line) for line in report.business_context.lines())
        nums = {e.evidence_id: i + 1 for i, e in enumerate(evidence)}
        for index, reason in enumerate(kept, 1):
            story.append(para(f"{index}. {reason.headline}", heading))
            story.append(para("Possible adjacent application - requires expert validation"
                if reason.kind == "idea" else "Direct relevance", small))
            refs = list(dict.fromkeys(nums[e] for c in reason.claim_ids for e in mapping[c]))
            story.append(para(reason.text + " " + " ".join(f"[{n}]" for n in refs)))
            for entry in reason.entries:
                entry_refs = list(dict.fromkeys(nums[e] for c in entry.claim_ids for e in mapping[c]))
                story.append(para(f"{entry.name} | {entry.institution} " +
                                  " ".join(f"[{n}]" for n in entry_refs), small))
        from backend.contracts.presentation import public_limitations
        caveats = public_limitations([*report.limitations, *report.draft.open_questions])
        if caveats:
            story.append(para("Limitations and next steps", heading))
            story.extend(para("- " + item) for item in caveats)
        story.append(para("Sources and exact supporting passages", heading))
        for e in evidence:
            story.append(para(f"[{nums[e.evidence_id]}] {e.title}", heading))
            story.append(Paragraph(f'<link href="{escape(e.url, quote=True)}" color="#116959">'
                                   f'{escape(e.url)}</link>', small))
            dates = f"Retrieved: {e.fetched_at.isoformat()}"
            if e.published_at:
                dates += f" | Source date: {e.published_at.isoformat()}"
            story.append(para(dates, small))
            story.append(para(f"Origin: {e.origin}; source review: {e.review_status}. "
                "Claim support does not certify the source." +
                (f" Page {e.page}." if e.page else ""), small))
            story.append(para(e.literal_text, quote))
        def footer(canvas, document):
            canvas.saveState()
            canvas.setFont("NavigatorVera", 7)
            canvas.setFillColor(ink)
            canvas.drawString(48, 25, "Bern Navigator | Challenge-only branding | " + report.template_version[:48])
            canvas.drawRightString(547, 25, f"Page {document.page}")
            canvas.restoreState()
        # Invariant canvas removes creation-time/random-ID drift for identical input.
        doc.build(story, onFirstPage=footer, onLaterPages=footer,
                  canvasmaker=partial(Canvas, invariant=1))
        return buffer.getvalue()


def create_pdf_renderer(**kwargs) -> ReportLabPdfRenderer:
    return ReportLabPdfRenderer(**kwargs)
