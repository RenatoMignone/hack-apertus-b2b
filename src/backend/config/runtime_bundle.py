"""Patch private runtime identity/configuration while preserving existing secrets."""
import json
from pathlib import Path

from sqlalchemy.engine import make_url


def prepare_live_environment(path, role, namespace, profile_id):
    """Validate the private file before changing DB grants; return a patch builder."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    values = dict(line.split("=", 1) for line in lines if line.strip() and not line.lstrip().startswith("#") and "=" in line)
    bindings = json.loads(values.get("RUNTIME_AUTH_BINDINGS", "[]"))
    selected = [b for b in bindings if make_url(values[b.get("database_url_env", "DATABASE_URL")]).username == role]
    if not selected:
        raise ValueError("private runtime file has no existing token binding for this database role")
    if any(not b.get("token_sha256") for b in selected):
        raise ValueError("preserve the operator's existing token digest; do not generate a replacement")

    def apply(principal_id):
        for binding in selected:
            binding.update(principal_id=str(principal_id), namespace=namespace)
        replacements = {"RUNTIME_AUTH_BINDINGS": json.dumps(bindings, separators=(",", ":")),
            "RUNTIME_PROFILE_ID": str(profile_id), "RUNTIME_CORPUS_MODE": "live"}
        output, found = [], set()
        for line in lines:
            key = line.split("=", 1)[0]
            if key in replacements:
                output.append(key + "=" + replacements[key])
                found.add(key)
            else:
                output.append(line)
        output.extend(key + "=" + value for key, value in replacements.items() if key not in found)
        # Write to the existing private file so its restrictive ACL is retained.
        path.write_text("\n".join(output) + "\n", encoding="utf-8", newline="\n")
    return apply
