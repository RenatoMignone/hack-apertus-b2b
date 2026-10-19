"""Recover a timed-out search branch without retaining an aborted transaction."""
from sqlalchemy.exc import DBAPIError

from backend.observability.logging import event, timed


def run_branch(connection, name, operation, *, allow_partial, run_id, query_count):
    try:
        with timed(f"retrieval.{name}", run_id=run_id, query_count=query_count):
            with connection.begin_nested():
                return operation(), None
    except DBAPIError as error:
        # Only PostgreSQL statement cancellation is recoverable here. Connection,
        # authorization and data errors must still fail the request. Explicit
        # evaluation strategies must never silently measure a different strategy.
        if not allow_partial or getattr(error.orig, "sqlstate", None) != "57014":
            raise
        event("retrieval.branch_unavailable", run_id=run_id, stage=name,
              error_code="statement_timeout")
        return [], f"{name}_search_timeout"
