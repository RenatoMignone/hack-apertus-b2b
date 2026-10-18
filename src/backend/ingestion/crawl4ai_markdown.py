"""Crawl4AI conversion without mixing crawler and LangGraph dependencies."""
import json
import os
from pathlib import Path
import subprocess

from backend.contracts.services import ServiceUnavailable


def convert(html, base_url, *, python_executable=""):
    if not python_executable:
        # Existing installations can still supply a compatible in-process extra.
        try:
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        except ImportError:
            raise ServiceUnavailable() from None
        return DefaultMarkdownGenerator().generate_markdown(
            input_html=html, base_url=base_url).raw_markdown.strip()
    interpreter = Path(python_executable)
    if not interpreter.is_absolute() or not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise ServiceUnavailable()
    from backend.ingestion.crawl4ai_worker import MAX_BYTES
    payload = json.dumps({"html": html, "base_url": base_url}).encode()
    if len(payload) > MAX_BYTES:
        raise ValueError("crawler conversion byte budget exceeded")
    environment = {key: os.environ[key] for key in ("PATH", "HOME", "TMPDIR", "LANG") if key in os.environ}
    try:
        result = subprocess.run([str(interpreter), "-I", str(Path(__file__).with_name("crawl4ai_worker.py"))],
            input=payload, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=20, check=False, env=environment)
        if result.returncode or len(result.stdout) > MAX_BYTES:
            raise ServiceUnavailable()
        value = json.loads(result.stdout)
        if set(value) != {"markdown"} or not isinstance(value["markdown"], str) or not value["markdown"].strip():
            raise ServiceUnavailable()
        return value["markdown"]
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
        raise ServiceUnavailable() from None
