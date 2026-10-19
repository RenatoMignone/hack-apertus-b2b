"""Render the committed, inspected retrieval receipt. No network or evidence writes."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


REPOSITORY = Path(__file__).resolve().parents[3]


def validate_receipt(data):
    """Check public-record consistency, not source bodies or semantic relevance."""
    queries = data['queries']
    hits = [hit for query in queries for hit in query['hits']]
    counts = {
        'returned_passage_occurrences': len(hits),
        'distinct_documents': len({hit['document_id'] for hit in hits}),
        'exact_slice_checks_passed': sum(hit['exact_body_slice'] is True for hit in hits),
        'body_hash_checks_passed': sum(hit['body_sha256_valid'] is True for hit in hits),
    }
    if not queries or any(data[key] != value for key, value in counts.items()):
        raise ValueError('Receipt totals disagree with recorded hits')
    if not hits or counts['exact_slice_checks_passed'] != len(hits) or counts['body_hash_checks_passed'] != len(hits):
        raise ValueError('Receipt contains failed passage integrity checks')
    by_query = {query['id']: query for query in queries}
    if len(by_query) != len(queries):
        raise ValueError('Duplicate query identifiers')
    for example in data['selected_examples']:
        query = by_query[example['query_id']]
        hit = next((hit for hit in query['hits'] if hit['rank'] == example['rank']), None)
        if hit is None or any(example[key] != hit[key] for key in ('chunk_id', 'source_url', 'body_sha256')):
            raise ValueError('Selected example does not match its ranked source')
        for quote in example['quotes']:
            start, end = quote['char_start'], quote['char_end']
            if not (hit['char_start'] <= start <= end <= hit['char_end']) or len(quote['text']) != end - start:
                raise ValueError('Quote offsets disagree with the recorded source span')
    return counts


def render(data, output, *, font=None, font_bold=None, receipt_hash=''):
    counts = validate_receipt(data)
    fonts = Path(reportlab.__file__).parent / 'fonts'
    pdfmetrics.registerFont(TTFont('PoC', str(font or fonts / 'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('PoCBold', str(font_bold or fonts / 'VeraBd.ttf')))
    pdfmetrics.registerFontFamily('PoC', normal='PoC', bold='PoCBold', italic='PoC', boldItalic='PoCBold')
    ink, red, muted = colors.HexColor('#193246'), colors.HexColor('#B3343D'), colors.HexColor('#50616B')
    body = ParagraphStyle('body', fontName='PoC', fontSize=10, leading=14, textColor=ink, spaceAfter=9)
    small = ParagraphStyle('small', parent=body, fontSize=8, leading=11, textColor=muted, spaceAfter=6)
    heading = ParagraphStyle('heading', parent=body, fontName='PoCBold', fontSize=21, leading=26, spaceAfter=15)
    sub = ParagraphStyle('sub', parent=body, fontName='PoCBold', fontSize=12, leading=16, spaceBefore=7)
    quoted = ParagraphStyle('quote', parent=body, fontSize=9, leading=12, leftIndent=8,
        borderPadding=6, backColor=colors.HexColor('#F1F4F6'), spaceAfter=8)
    story = []

    def p(text, style=body):
        story.append(Paragraph(text, style))

    def grid(rows, widths):
        table = Table([[Paragraph(escape(str(value)), small) for value in row] for row in rows],
            colWidths=widths, hAlign='LEFT', repeatRows=1)
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F4F6')),
            ('LINEBELOW', (0, 0), (-1, 0), .8, red),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
        story.extend([table, Spacer(1, 10)])

    def quote(value):
        p(escape(' '.join(value.split())), quoted)

    moment = datetime.fromisoformat(data['completed_at'])
    p('TEAM STREGONI / B TO BERN', small)
    p('Real-source retrieval.<br/>Traceable research leads.', heading)
    p('HelioSense retrieval proof of concept', sub)
    p('A fictional glucose-sensor company asks which Bern research capabilities could support its R&amp;D. '
      'This experiment shows how the backend retrieves real institutional passages and makes the results inspectable.')
    p('Experiment: ' + moment.strftime('%d %B %Y, %H:%M UTC') +
      '. Presentation revised 19 October 2026; original measurements retained.', small)
    grid([['Corpus capture', 'Queries', 'Passage occurrences', 'Documents'],
        [f"{data['capture']['chunks']:,} chunks", str(len(data['queries'])),
         str(counts['returned_passage_occurrences']), str(counts['distinct_documents'])]],
        [46*mm, 26*mm, 51*mm, 47*mm])
    p('What worked', sub)
    p(f"All {counts['exact_slice_checks_passed']} recorded exact-passage checks and "
      f"{counts['body_hash_checks_passed']} source-body hash checks passed. Retrieved publications include "
      'documented sensing, closed-loop systems and glucose-prediction research. The next page shows three examples.')
    grid([['Query', 'Encoding + search', 'Hits'], *[[q['id'], f"{q['seconds']:.3f} s", len(q['hits'])]
        for q in data['queries']]], [88*mm, 52*mm, 30*mm])
    p('Method', sub)
    p('Four requests used the full company brief and alternative glucose-sensor, CGM and everyday biosensing wording. '
      'Lexical and vector search ran independently; reciprocal rank fusion combined their results. '
      'The queries contained no researcher names. Examples were selected after inspecting the rankings.')
    p('What this establishes', sub)
    p('Working retrieval and source traceability. This run returned no accepted structured entity profiles, '
      'so researcher mentions are leads extracted from publications. Expert Recall@10 was not measured. '
      'The broader application pipeline was tested separately (page 3).')
    p('Timing is one observation per query, including hosted encoding. It is the original baseline, '
      'not a measurement of the latest SQL optimization.', small)

    story.append(PageBreak())
    p('Selected research leads', heading)
    p('Real publications support these examples. Publication dates identify their historical context; '
      'confirm current roles and collaboration availability before outreach.', small)
    for example in data['selected_examples']:
        p(escape(example['name']), sub)
        p(escape(example['classification']), small)
        p(escape(example['interpretation']))
        for item in example['quotes']:
            quote(item['text'])
        p('<link href="' + escape(example['source_url'], {'"':'&quot;'}) +
          '" color="#B3343D"><u>Original institutional source</u></link> | ' +
          escape(example['query_id']) + ', passage rank ' + str(example['rank']), small)
    p('One ranking weakness', sub)
    p('A rehabilitation page ranked first for the sensor query. Retrieved passages therefore still need '
      'a relevance assessment. Passage rank is not a validated researcher score.', small)
    p('The JSON retains every ranking, selected quotation, source URL, character offset and body hash. '
      'Whitespace in displayed quotations is normalized for readability.', small)

    story.append(PageBreak())
    p('Evidence, scope and reproduction', heading)
    p('Three separate checks', sub)
    grid([['Evidence', 'Result and scope'],
        ['This retrieval experiment', 'Real corpus; fictional company. Passage integrity and selected research leads. '
         'No reranking, web research or Apertus drafting in this run.'],
        ['Later pipeline acceptance', 'Actual Apertus with fictional sources and local PostgreSQL checkpoints: '
         'match, clarification/resume, assessed report, review and PDF export. Separate restart tests used scripted providers.'],
        ['Later live SQL measurements', 'Six-input retrieval over 144,268 chunks completed in 6.04-7.43 s; '
         'complete RRF returned 30 hits in 6.81 s with cached real query vectors. Encoding and reranking excluded.']],
        [48*mm, 122*mm])
    p('The two timing sets use different captures and include different work; they are not a like-for-like speedup. '
      'Remaining acceptance is expert recall/coverage, a fresh complete case on the optimized live corpus, '
      'and the selected deployment environment.', small)
    p('Inspect or rebuild', sub)
    p('The committed receipt and this PDF can be inspected without services or credentials. Rebuild the '
      'presentation from repository root with the installed backend:', small)
    quote('python -m backend.evaluation.render_proof_of_concept')
    p('The renderer reads docs/proof-of-concept/retrieval-results.json and writes only the PDF. '
      'It checks receipt consistency; it does not rerun retrieval or revalidate private source bodies.', small)
    p('To collect a new experiment, use an existing authorized run and matching encoder settings:', small)
    quote('python -m backend.evaluation.proof_of_concept --env-file PRIVATE_ENV --run-id OWNED_RUN_ID')
    p('This calls the configured encoder and database. Current retrieval permits temporary tables, '
      'with no persistent corpus/case writes. A new run produces a separate result, not the original measurement.', small)
    p('Recorded provenance', sub)
    grid([['Field', 'Original experiment'],
        ['Schema', data['schema_revision']], ['Snapshot', data['capture']['snapshot_id']],
        ['Source', data['source_commit'][:12] + ' + local changes'],
        ['Encoder', data['encoder']['artifact'] + '; ' + str(data['encoder']['dimension']) + ' dimensions'],
        ['Encoder revision', data['encoder']['revision']]], [39*mm, 131*mm])
    p('Receipt SHA-256: ' + receipt_hash, small)
    p('Related records: docs/proof-of-concept/README.md; docs/project/PIPELINE_RELIABILITY.md; '
      'docs/project/FRONTEND_RECOVERY.md; docs/data/LIVE_RETRIEVAL_PERFORMANCE.md.', small)

    def decorate(canvas, doc):
        width, height = doc.pagesize
        canvas.setStrokeColor(red)
        canvas.line(20*mm, height-16*mm, width-20*mm, height-16*mm)
        canvas.setFont('PoC', 8); canvas.setFillColor(muted)
        canvas.drawString(20*mm, 12*mm, 'B2B / STREGONI - retrieval experiment, 19 October 2026')
        canvas.drawRightString(width-20*mm, 12*mm, str(doc.page))
    output.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(output), pagesize=(210*mm, 297*mm), leftMargin=20*mm, rightMargin=20*mm,
        topMargin=23*mm, bottomMargin=21*mm, title='B to Bern - HelioSense Retrieval Proof of Concept',
        author='Team Stregoni').build(story, onFirstPage=decorate, onLaterPages=decorate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=REPOSITORY/'docs/proof-of-concept/retrieval-results.json')
    parser.add_argument('--output', type=Path, default=REPOSITORY/'output/pdf/Stregoni_Retrieval_Proof_of_Concept.pdf')
    parser.add_argument('--font', type=Path, help='Optional Unicode TTF; defaults to ReportLab bundled Vera')
    parser.add_argument('--font-bold', type=Path, help='Optional bold Unicode TTF')
    args = parser.parse_args()
    raw = args.input.read_bytes()
    render(json.loads(raw), args.output, font=args.font, font_bold=args.font_bold,
        receipt_hash=hashlib.sha256(raw).hexdigest())
    print('Rendered ' + str(args.output))


if __name__ == '__main__':
    main()
