import os
from pathlib import Path
from uuid import uuid4

import pytest


def require_test_admin_dsn():
    """Destructive tests never derive administrator access from deployment secrets."""
    value = os.environ.get("NAVIGATOR_TEST_ADMIN_DSN", "").strip()
    if not value:
        raise SystemExit("Set NAVIGATOR_TEST_ADMIN_DSN explicitly to an isolated disposable "
                         "PostgreSQL cluster; never use the shared server or deployment credentials.")
    return value


def main():
    require_test_admin_dsn()
    Path(".local").mkdir(exist_ok=True)
    raise SystemExit(pytest.main([str(Path(__file__).parent), "-q", "--tb=short", "--basetemp",
                                 ".local/pytest-" + uuid4().hex]))


if __name__ == "__main__":
    main()
