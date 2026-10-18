import logging
from queue import Empty, Full, Queue
from threading import Thread
from urllib.parse import urlparse


ALLOWED_FIELDS = {"run_id", "case_id", "thread_id", "snapshot_id", "build_id", "config_hash",
                  "stage", "duration_ms", "candidate_count", "accepted_count", "error_code"}


def sanitized(metadata):
    if not isinstance(metadata, dict):
        return {}
    output = {}
    for key, value in metadata.items():
        if key in ALLOWED_FIELDS and isinstance(value, (str, int, float, bool)):
            if key.endswith("_id"):
                from uuid import UUID
                try:
                    output[key] = str(UUID(str(value)))
                except ValueError:
                    continue
            elif key in {"stage", "error_code"}:
                if value in {"retrieval", "fusion", "reranking", "publication", "checkpoint", "stage",
                             "unavailable", "invalid", "timeout"}:
                    output[key] = value
            elif key == "config_hash":
                import re
                if re.fullmatch(r"[a-f0-9]{64}", str(value)):
                    output[key] = value
            elif isinstance(value, (int, float, bool)):
                import math
                if math.isfinite(value):
                    output[key] = value
    return output


class SafeTracer:
    def __init__(self, sender=None, capacity=128):
        self.sender = sender
        self.queue = Queue(maxsize=capacity)
        self.degraded = False
        self.thread = None
        if sender:
            self.thread = Thread(target=self._drain, daemon=True)
            self.thread.start()

    def emit(self, metadata):
        if not self.sender:
            return
        try:
            self.queue.put_nowait(sanitized(metadata))
        except Full:
            self.degraded = True

    def _drain(self):
        while True:
            try:
                item = self.queue.get(timeout=.5)
            except Empty:
                continue
            try:
                if item is None:
                    return
                self.sender(item)
            except Exception:
                self.degraded = True
                logging.getLogger(__name__).warning("local tracing unavailable")
            finally:
                self.queue.task_done()

    def close(self, timeout=2):
        if self.thread:
            try:
                self.queue.put_nowait(None)
            except Full:
                self.degraded = True
            self.thread.join(timeout=timeout)


def langfuse_tracer(endpoint, public_key, secret_key):
    if urlparse(endpoint).hostname not in {"localhost", "127.0.0.1", "langfuse-web"}:
        raise ValueError("tracing must target the configured local deployment")
    from langfuse import Langfuse

    client = Langfuse(base_url=endpoint, public_key=public_key, secret_key=secret_key,
                      timeout=2, sample_rate=1, mask=lambda **arguments: sanitized(arguments.get("data", {})))

    def send(metadata):
        with client.start_as_current_observation(name=metadata.get("stage", "stage"), as_type="span") as observation:
            observation.update(metadata=metadata)

    return SafeTracer(send)
