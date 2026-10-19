import asyncio
from io import BytesIO
from xml.etree import ElementTree as E
from zipfile import ZipFile

import pytest
from backend.contracts.business import BusinessContext
from backend.contracts.services import EvidenceRejected
from backend.reports.rendering.pptx import TemplatePptxRenderer, NS


def test_template_kept_only_editable_citations_deterministic(pdf_input, interpretation, tmp_path):
    report = pdf_input.model_copy(update={'interpretation': interpretation,
        'business_context': BusinessContext(planned_jobs=5, investment_amount='250000.00', investment_currency='CHF', timeline='Planned 2027; unconfirmed')})
    renderer = TemplatePptxRenderer()
    data = asyncio.run(renderer.render(report))
    assert data == asyncio.run(renderer.render(report))
    with ZipFile(BytesIO(data)) as z:
        assert z.testzip() is None
        slides = [n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
        text = ' '.join(t.text or '' for name in slides for t in E.fromstring(z.read(name)).findall('.//a:t', NS))
        assert 'Sensor development expertise' in text and 'REJECTED MUST NOT APPEAR' not in text
        assert 'Planned jobs: 5' in text and '250000.00 CHF' in text
        assert 'not actual economic impact' in text and 'unreviewed' in text
        assert 'https://fixture.invalid/research' in text
        assert any(b'Target="https://fixture.invalid/research"' in z.read(n) and b'TargetMode="External"' in z.read(n)
            for n in z.namelist() if n.startswith('ppt/slides/_rels/') and n.endswith('.rels'))
        assert 'Expert availability remains unknown.' in text
        assert 'Lorem ipsum' not in text and 'vorname.name@be.ch' not in text
        assert 'ppt/slides/slide19.xml' not in z.namelist()
        with ZipFile(renderer.template_path) as source:
            # Supplied style, masters and logo bytes remain unchanged.
            for name in z.namelist():
                if name.startswith(('ppt/theme/', 'ppt/media/')):
                    assert z.read(name) == source.read(name)
            assert E.fromstring(z.read('ppt/presentation.xml')).find('p:sldSz', NS).attrib == E.fromstring(source.read('ppt/presentation.xml')).find('p:sldSz', NS).attrib
    (tmp_path/'checked.pptx').write_bytes(data)


@pytest.mark.parametrize('change', [{'claims': []}, {'evidence': []}, {'kept_reason_keys': []}])
def test_pptx_rejects_unresolved_citations_or_empty_selection(pdf_input, change):
    with pytest.raises(EvidenceRejected):
        asyncio.run(TemplatePptxRenderer().render(pdf_input.model_copy(update=change)))


@pytest.mark.parametrize('body', [{'planned_jobs': 1.5}, {'investment_amount': '20'},
    {'investment_amount':'-1','investment_currency':'CHF'}, {'investment_currency':'CHF'}, {'timeline':''}])
def test_manual_business_values_reject_invalid_or_incomplete_data(body):
    with pytest.raises(ValueError):
        BusinessContext.model_validate(body)
