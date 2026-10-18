"""One bounded Markdown conversion in the separately provisioned crawler venv.

Invoked as an isolated Python script, not as a backend module. No DB/model
credentials, URL fetching, page scripts or browser tools are available here.
"""
import contextlib
import json
import sys

MAX_BYTES = 8_000_000


def main():
    raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        return 1
    try:
        payload = json.loads(raw)
        if set(payload) != {"html", "base_url"} or not all(isinstance(v, str) for v in payload.values()):
            return 1
        # Third-party startup/progress output cannot corrupt the JSON protocol.
        with contextlib.redirect_stdout(sys.stderr):
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
            markdown = DefaultMarkdownGenerator().generate_markdown(
                input_html=payload["html"], base_url=payload["base_url"])
        output = json.dumps({"markdown": markdown.raw_markdown.strip()}).encode()
        if len(output) > MAX_BYTES:
            return 1
        sys.stdout.buffer.write(output)
        return 0
    except Exception:
        return 1  # Do not print page text, third-party errors or environment.


if __name__ == "__main__":
    raise SystemExit(main())
