from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from io import BytesIO
import re

from backend.contracts.data import Span, configuration_hash


PARSER_HASH = configuration_hash({"parser": "faithful-html-pdf", "version": 2})


@dataclass(frozen=True)
class NormalizedDocument:
    title: str
    body: str
    language: str
    spans: list[Span]
    published_at: datetime | None = None


def publication_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


class PageParser(HTMLParser):
    excluded = {"script", "style", "nav", "footer", "noscript", "template", "svg"}
    blocks = {"p", "div", "section", "article", "li", "br", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.title_parts = []
        self.in_title = False
        self.hidden = []
        self.language = "und"
        self.published_at = None
        self.heading_level = None
        self.heading_parts = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "html":
            language = attributes.get("lang", "und").split("-")[0].lower()
            self.language = language if language in {"en", "de", "fr", "it"} else "und"
        if tag == "meta" and attributes.get("property", attributes.get("name")) in {"article:published_time", "datePublished"}:
            self.published_at = publication_date(attributes.get("content"))
        if self.hidden:
            if tag in self.excluded:
                self.hidden.append(tag)
            return
        if tag in self.excluded:
            self.hidden.append(tag)
        elif tag == "title":
            self.in_title = True
        elif tag in self.blocks:
            self.parts.append("\n")
            if re.fullmatch(r"h[1-6]", tag):
                self.heading_level = int(tag[1])
                self.heading_parts = []

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag == "title":
            self.in_title = False
        elif tag in self.blocks:
            self.parts.append("\n")
            if re.fullmatch(r"h[1-6]", tag) and self.heading_level is not None:
                self.headings.append((self.heading_level, " ".join("".join(self.heading_parts).split())))
                self.heading_level = None

    def handle_data(self, data):
        if not self.hidden:
            (self.title_parts if self.in_title else self.parts).append(data)
            if self.heading_level is not None:
                self.heading_parts.append(data)


def html_spans(body, headings):
    spans, offset, heading_index, path = [], 0, 0, {}
    for line in body.splitlines(keepends=True):
        if heading_index < len(headings) and line.strip() == headings[heading_index][1]:
            level, title = headings[heading_index]
            path = {depth: value for depth, value in path.items() if depth < level}
            path[level] = title
            heading_index += 1
        spans.append(Span(char_start=offset, char_end=offset + len(line), text=line,
            heading_path=[path[depth] for depth in sorted(path)]))
        offset += len(line)
    return spans


def normalize(raw: bytes, mime: str, *, fallback_title="Public source") -> NormalizedDocument:
    if mime.split(";")[0].strip() == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError("PDF extraction unavailable: install the proposed pypdf dependency") from error
        reader = PdfReader(BytesIO(raw))
        if len(reader.pages) > 100:
            raise ValueError("public PDF page budget exceeded")
        pages = [page.extract_text() or "" for page in reader.pages]
        body = "\n\n".join(pages)
        spans, offset = [], 0
        for page_number, page_text in enumerate(pages, start=1):
            if page_text.strip():
                spans.append(Span(char_start=offset, char_end=offset + len(page_text), text=page_text, page=page_number))
            offset += len(page_text) + 2
        document = NormalizedDocument(fallback_title, body, "und", spans)
    elif mime.split(";")[0].strip() in {"text/html", "application/xhtml+xml"}:
        charset = re.search(r"charset=([\w-]+)", mime, re.I)
        parser = PageParser()
        parser.feed(raw.decode(charset.group(1) if charset else "utf-8", errors="strict"))
        body = "\n".join(line for line in (re.sub(r"[\t\r\f\v ]+", " ", part).strip()
            for part in "".join(parser.parts).splitlines()) if line)
        document = NormalizedDocument(" ".join("".join(parser.title_parts).split()) or fallback_title,
            body, parser.language, html_spans(body, parser.headings), parser.published_at)
    else:
        raise ValueError("unsupported public source MIME type")
    if not document.body.strip():
        raise ValueError("source has no extracted text; OCR is unavailable")
    return document


def chunks(document: NormalizedDocument, accepts, *, max_characters=2400) -> list[Span]:
    if max_characters < 1:
        raise ValueError("positive chunk character budget required")
    result = []
    for section in document.spans:
        start = section.char_start
        while start < section.char_end:
            end = min(start + max_characters, section.char_end)
            while end > start and not accepts(document.body[start:end], section.heading_path):
                end = start + (end - start) // 2
            if end <= start:
                raise ValueError("one character exceeds the configured embedding token budget")
            result.append(Span(char_start=start, char_end=end, text=document.body[start:end],
                page=section.page, heading_path=section.heading_path))
            start = end
    return result
