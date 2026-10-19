"""Editable, deterministic OOXML export reusing the supplied partner template.

No model, network, Node runtime or third-party authoring library at runtime.
"""
import asyncio
from copy import deepcopy
from io import BytesIO
from pathlib import Path, PurePosixPath
import posixpath
import textwrap
from xml.etree import ElementTree as E
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from backend.contracts.presentation import public_limitations
from backend.contracts.services import EvidenceRejected, ServiceUnavailable
from backend.reports.rendering.content import selected_content

MIME = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
for prefix, uri in NS.items():
    E.register_namespace(prefix, uri)


def xml(root):
    data = E.tostring(root, encoding='utf-8', xml_declaration=True)
    # Keep OPC package/property roots in the template's default namespace.
    # Some presentation consumers do not accept equivalent ns0-prefixed roots.
    if root.tag.startswith(('{'+REL+'}', '{'+CT+'}', '{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}')):
        data = data.replace(b'xmlns:ns0=', b'xmlns=').replace(b'<ns0:', b'<').replace(b'</ns0:', b'</')
    return data


def paginated(title, paragraphs):
    # Explicit wrapping/paging keeps text editable without shrinking the template
    # font. Preserve all words, quotes and URLs; no model summaries or truncation.
    lines = []
    for paragraph in paragraphs:
        text, target = paragraph if isinstance(paragraph, tuple) else (str(paragraph), None)
        wrapped = textwrap.wrap(text, width=78, break_long_words=True, break_on_hyphens=False) or ['']
        lines.extend((line, target) if target else line for line in wrapped)
    pages = [lines[i:i+9] for i in range(0, len(lines), 9)] or [[]]
    return [(heading, page) for part, page in enumerate(pages, 1)
        for heading in [title if part == 1 else f'{title} (continued {part})']]


def pages_for(report, kept, evidence, mapping):
    pages = paginated('Bern opportunity brief', ['Reviewed opportunities and public evidence',
        report.interpretation.company_name or 'Company context'] if report.interpretation else ['Reviewed public evidence'])
    if report.interpretation:
        company = report.interpretation
        pages += paginated('Company context', ['Operator-provided context; not independently verified', company.company_summary])
        pages += paginated('Needs and Bern objectives', [*company.needs, *company.bern_intents])
    if report.business_context and report.business_context.lines():
        pages += paginated('Company plans', ['Manually entered operator plans; not actual economic impact', *report.business_context.lines()])
    numbers = {record.evidence_id: index+1 for index, record in enumerate(evidence)}
    for index, reason in enumerate(kept, 1):
        refs = list(dict.fromkeys(numbers[e] for key in reason.claim_ids for e in mapping[key]))
        paragraphs = ['Possible adjacent application; requires expert validation' if reason.kind == 'idea' else 'Direct relevance',
            reason.text + ' ' + ' '.join(f'[{n}]' for n in refs)]
        paragraphs += [f'{entry.name} | {entry.institution}' for entry in reason.entries]
        # Headline is also source-checked, but long headlines must not overflow.
        title = f'{index}. {reason.headline}'
        if len(title) > 65:
            paragraphs.insert(0, reason.headline)
            title = f'Reviewed opportunity {index}'
        pages += paginated(title, paragraphs)
    caveats = public_limitations([*report.limitations, *report.draft.open_questions])
    if caveats:
        pages += paginated('Limitations and next steps', caveats)
    for record in evidence:
        pages += paginated(f'Source [{numbers[record.evidence_id]}]', [record.title, (record.url, record.url),
            f'Retrieved: {record.fetched_at.isoformat()}',
            *([f'Source date: {record.published_at.isoformat()}'] if record.published_at else []),
            f'Origin: {record.origin}; source review: {record.review_status}',
            'Claim support does not certify the source.', record.literal_text])
    if len(pages) > 200:
        raise EvidenceRejected()
    return pages


def fill(shape, lines, relationships):
    body = shape.find('p:txBody', NS)
    for paragraph in list(body.findall('a:p', NS)):
        body.remove(paragraph)
    for line in lines or ['']:
        paragraph = E.SubElement(body, '{'+NS['a']+'}p')
        properties = E.SubElement(paragraph, '{'+NS['a']+'}pPr', {'lvl': '0'})
        E.SubElement(properties, '{'+NS['a']+'}buNone')
        run = E.SubElement(paragraph, '{'+NS['a']+'}r')
        properties = E.SubElement(run, '{'+NS['a']+'}rPr', {'lang': 'en-GB'})
        text, target = line if isinstance(line, tuple) else (line, None)
        if target:
            rid = 'sourceLink'+str(len(relationships)+1)
            E.SubElement(relationships, '{'+REL+'}Relationship', {'Id':rid,
                'Type':NS['r']+'/hyperlink', 'Target':target, 'TargetMode':'External'})
            E.SubElement(properties, '{'+NS['a']+'}hlinkClick', {'{'+NS['r']+'}id':rid})
        E.SubElement(run, '{'+NS['a']+'}t').text = text


class TemplatePptxRenderer:
    def __init__(self, template_path=None):
        self.template_path = Path(template_path) if template_path else Path(__file__).resolve().parents[4]/'docs/provided_material/powerpoint_template.pptx'

    def available(self):
        return self.template_path.is_file()

    async def render(self, report):
        report, kept, evidence, mapping = selected_content(report)
        if not self.available():
            raise ServiceUnavailable()
        return await asyncio.to_thread(self._render, pages_for(report, kept, evidence, mapping))

    def _render(self, pages):
        try:
            with ZipFile(self.template_path) as source:
                parts = {name: source.read(name) for name in source.namelist() if not name.endswith('/')}
            prototype = E.fromstring(parts['ppt/slides/slide10.xml'])
            layout_rels = parts['ppt/slides/_rels/slide10.xml.rels']
            presentation = E.fromstring(parts['ppt/presentation.xml'])
            relationships = E.fromstring(parts['ppt/_rels/presentation.xml.rels'])
            types = E.fromstring(parts['[Content_Types].xml'])
        except (OSError, KeyError, E.ParseError):
            raise ServiceUnavailable() from None
        # Remove all example slides, slide overrides and their relationships.
        for name in list(parts):
            if name.startswith(('ppt/slides/', 'ppt/notesSlides/', 'ppt/charts/', 'ppt/embeddings/')):
                del parts[name]
        for child in list(relationships):
            if child.get('Type', '').endswith('/slide'):
                relationships.remove(child)
        for child in list(types):
            if child.get('PartName', '').startswith(('/ppt/slides/', '/ppt/notesSlides/', '/ppt/charts/', '/ppt/embeddings/')):
                types.remove(child)
        slides = presentation.find('p:sldIdLst', NS)
        slides.clear()
        # Template section/custom-show references can refer to removed examples.
        for child in list(presentation):
            if child.tag in {'{'+NS['p']+'}custShowLst', '{'+NS['p']+'}extLst'}:
                presentation.remove(child)
        for number, (title, lines) in enumerate(pages, 1):
            slide = deepcopy(prototype)
            slide_relationships = E.fromstring(layout_rels)
            for shape in slide.findall('.//p:sp', NS):
                ph = shape.find('.//p:ph', NS)
                if ph is None:
                    continue
                kind = ph.get('type')
                fill(shape, [title] if kind == 'title' else lines if ph.get('idx') == '1' else
                    [str(number)] if kind == 'sldNum' else ['Internal working brief'] if kind == 'ftr' else [], slide_relationships)
            name = f'ppt/slides/slide{number}.xml'
            parts[name] = xml(slide)
            parts[f'ppt/slides/_rels/slide{number}.xml.rels'] = xml(slide_relationships)
            rid = f'caseSlide{number}'
            E.SubElement(slides, '{'+NS['p']+'}sldId', {'id': str(255+number), '{'+NS['r']+'}id': rid})
            E.SubElement(relationships, '{'+REL+'}Relationship', {'Id': rid,
                'Type': NS['r']+'/slide', 'Target': f'slides/slide{number}.xml'})
            E.SubElement(types, '{'+CT+'}Override', {'PartName': '/'+name,
                'ContentType': 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'})
        parts['ppt/presentation.xml'] = xml(presentation)
        parts['ppt/_rels/presentation.xml.rels'] = xml(relationships)
        # Remove stale thumbnail and example deck metadata; keep only reachable
        # package parts so hidden demo slides/contacts cannot leak into exports.
        parts.pop('docProps/thumbnail.jpeg', None)
        parts.pop('docProps/thumbnail.wmf', None)
        rootrels = E.fromstring(parts['_rels/.rels'])
        for child in list(rootrels):
            if 'metadata/thumbnail' in child.get('Type', ''):
                rootrels.remove(child)
        parts['_rels/.rels'] = xml(rootrels)
        if 'docProps/app.xml' in parts:
            app = E.fromstring(parts['docProps/app.xml'])
            for child in list(app):
                if child.tag.rsplit('}',1)[-1] in {'Slides','Notes','HiddenSlides','HeadingPairs','TitlesOfParts'}:
                    app.remove(child)
            E.SubElement(app, '{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Slides').text = str(len(pages))
            parts['docProps/app.xml'] = xml(app)
        types_xml = types
        pending, reachable = [''], {'[Content_Types].xml'}
        while pending:
            part = pending.pop()
            if part:
                reachable.add(part)
            path = PurePosixPath(part)
            relfile = str(path.parent/'_rels'/(path.name+'.rels')) if part else '_rels/.rels'
            if relfile not in parts:
                continue
            relroot = E.fromstring(parts[relfile])
            for relation in list(relroot):
                if relation.get('TargetMode') == 'External':
                    continue
                target = relation.get('Target', '')
                target = posixpath.normpath(str(path.parent/target)).lstrip('/') if part else target.lstrip('/')
                if target not in parts:
                    relroot.remove(relation)
                elif target not in reachable:
                    reachable.add(target)
                    pending.append(target)
            parts[relfile] = xml(relroot)
            reachable.add(relfile)
        for child in list(types_xml):
            if child.tag.endswith('Override') and child.get('PartName', '').lstrip('/') not in reachable:
                types_xml.remove(child)
        parts['[Content_Types].xml'] = xml(types_xml)
        output = BytesIO()
        with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
            for name in sorted(reachable):
                item = ZipInfo(name, date_time=(2000,1,1,0,0,0))
                item.compress_type = ZIP_DEFLATED
                archive.writestr(item, parts[name])
        return output.getvalue()
