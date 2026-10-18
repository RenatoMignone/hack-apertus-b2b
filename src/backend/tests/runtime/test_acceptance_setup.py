"""Deployment credentials must never implicitly select destructive test infrastructure."""
import pytest

from backend.tests import run


def test_runner_does_not_use_private_deployment_credentials(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NAVIGATOR_TEST_ADMIN_DSN", raising=False)
    monkeypatch.setenv("POSTGRES_PASSWORD", "synthetic-deployment-secret")
    deployment = tmp_path / "src/backend/deploy/.env"
    deployment.parent.mkdir(parents=True)
    deployment.write_text("POSTGRES_PASSWORD=another-synthetic-deployment-secret\n")
    def no_tests(*args, **kwargs):
        pytest.fail("destructive tests were selected without an explicit test DSN")
    monkeypatch.setattr(run.pytest, "main", no_tests)
    with pytest.raises(SystemExit, match="isolated disposable"):
        run.main()
    assert not (tmp_path / ".local").exists()


def test_browser_smoke_requires_explicit_disposable_database(monkeypatch):
    from backend.tests.runtime import smoke
    monkeypatch.delenv("NAVIGATOR_TEST_ADMIN_DSN", raising=False)
    monkeypatch.setenv("POSTGRES_PASSWORD", "synthetic-deployment-secret")
    with pytest.raises(SystemExit, match="never use the shared server"):
        smoke.main()
