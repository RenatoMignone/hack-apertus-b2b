import os
from pathlib import Path
from uuid import uuid4

import pytest

from backend.data.cli import load_environment


def main():
    Path(".local").mkdir(exist_ok=True)
    load_environment("src/backend/deploy/.env")
    os.environ["NAVIGATOR_TEST_ADMIN_DSN"] = f"postgresql://postgres:{os.environ['POSTGRES_PASSWORD']}@127.0.0.1:5432/postgres"
    raise SystemExit(pytest.main([str(Path(__file__).parent), "-q", "--tb=short", "--basetemp",
                                 ".local/pytest-" + uuid4().hex]))


if __name__ == "__main__":
    main()
