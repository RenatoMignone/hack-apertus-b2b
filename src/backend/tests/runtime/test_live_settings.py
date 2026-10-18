import json
from uuid import uuid4

import pytest

from backend.config.runtime import RuntimeSettings
from backend.config.runtime_bundle import prepare_live_environment


def test_live_environment_preserves_tokens_checkpoint_storage_and_database_password(tmp_path):
    token_digest = "a" * 64
    old_principal, new_principal, profile = uuid4(), uuid4(), uuid4()
    bindings = [{"principal_id": str(old_principal), "namespace": "fixture_old", "token_sha256": token_digest}]
    unchanged = {"DATABASE_URL": "postgresql://dev_ren:existing-password@127.0.0.1:15432/navigator",
        "LANGGRAPH_DATABASE_URL": "postgresql://checkpoint:keep-this@127.0.0.1:15432/langgraph",
        "S3_ACCESS_KEY_ID": "existing-key", "S3_SECRET_ACCESS_KEY": "existing-secret",
        "LLM_API_KEY": "existing-model-key", "HF_TOKEN": "existing-hf-token"}
    path = tmp_path / ".env"
    path.write_text("# Existing private settings\n" + "\n".join(k + "=" + v for k, v in unchanged.items())
        + "\nRUNTIME_AUTH_BINDINGS=" + json.dumps(bindings) + "\nRUNTIME_PROFILE_ID=\n", encoding="utf-8")
    apply = prepare_live_environment(path, "dev_ren", "pilot_namespace", profile)
    assert "RUNTIME_CORPUS_MODE=" not in path.read_text()  # Preparation has no write effects.
    apply(new_principal)
    values = dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)
    assert all(values[key] == value for key, value in unchanged.items())
    assert values["RUNTIME_CORPUS_MODE"] == "live" and values["RUNTIME_PROFILE_ID"] == str(profile)
    assert json.loads(values["RUNTIME_AUTH_BINDINGS"]) == [{"principal_id": str(new_principal),
        "namespace": "pilot_namespace", "token_sha256": token_digest}]


def test_runtime_settings_load_live_mode_and_reject_unknown_mode(monkeypatch):
    monkeypatch.setenv("RUNTIME_CORPUS_MODE", "live")
    monkeypatch.setenv("RUNTIME_AUTH_BINDINGS", "[]")
    assert RuntimeSettings.from_env().corpus_mode == "live"
    with pytest.raises(ValueError, match="RUNTIME_CORPUS_MODE"):
        RuntimeSettings(corpus_mode="ignore-authorization")


def test_bundle_patch_requires_existing_role_and_token(tmp_path):
    path = tmp_path / ".env"
    path.write_text("DATABASE_URL=postgresql://dev_ren:keep@localhost/navigator\nRUNTIME_AUTH_BINDINGS=[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="existing token binding"):
        prepare_live_environment(path, "dev_ren", "pilot", uuid4())


def test_worker_cli_uses_psycopg_compatible_loop():
    import asyncio
    import sys
    from backend.application.cli import run_async
    async def check():
        return asyncio.get_running_loop()
    loop = run_async(check())
    if sys.platform == "win32":
        assert isinstance(loop, asyncio.SelectorEventLoop)
