"""Generate/check the exact schema reference without connecting to a database."""
import argparse
from pathlib import Path

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql

from backend.data.schema import SCHEMA_REVISION, metadata


REFERENCE = Path(__file__).resolve().parents[3] / "docs/data/SCHEMA_REFERENCE.md"


def render():
    dialect = postgresql.dialect()
    lines = [
        "# Exact application schema reference", "",
        f"Generated from `src/backend/data/schema.py`; migration head **`{SCHEMA_REVISION}`**.",
        "Do not edit by hand. Regenerate with `PYTHONPATH=src python -m backend.data.schema_docs`.", "",
        f"**{len(metadata.tables)} application tables.** Read [schema decisions](RELATIONAL_SCHEMA.md) and",
        "[ingestion/retrieval handoff](INGESTION_RETRIEVAL_HANDOFF.md) for meanings and write order.",
        "Only these tables are supported for new queries. `alembic_version` is migration-owned;",
        "optional `legacy` history is maintainer-only. Framework tables live outside this database.", "",
        "UUIDs are supplied by the application. Timestamps are UTC. JSON payload contracts and",
        "database triggers are explained in the owner docs; a nullable field may be omitted.", "",
    ]
    for schema in ("corpus", "taxonomy", "retrieval", "cases", "ops"):
        lines.extend([f"## `{schema}`", ""])
        for table in sorted(metadata.tables.values(), key=lambda t: t.name):
            if table.schema != schema:
                continue
            lines.extend([f"### `{table.fullname}`", "", "| Column | Type | Required | Default | References |",
                          "| --- | --- | --- | --- | --- |"])
            for column in table.columns:
                default = str(column.server_default.arg) if column.server_default is not None else "—"
                references = ", ".join(fk.target_fullname for fk in column.foreign_keys) or "—"
                lines.append(f"| `{column.name}` | `{column.type.compile(dialect=dialect)}` | "
                             f"{'yes' if not column.nullable else 'no'} | `{default}` | {references} |")
            primary = ", ".join(column.name for column in table.primary_key)
            lines.extend(["", f"Primary key: `{primary}`.", ""])
            for constraint in sorted(table.constraints, key=lambda c: (str(c.name), str(getattr(c, "sqltext", "")))):
                if isinstance(constraint, UniqueConstraint):
                    lines.append("- Unique: `" + ", ".join(c.name for c in constraint.columns) + "`.")
                elif isinstance(constraint, CheckConstraint):
                    expression = str(constraint.sqltext).replace("|", "\\|")
                    lines.append(f"- Check: `{expression}`.")
            for index in sorted(table.indexes, key=lambda i: i.name):
                definition = ", ".join(c.name for c in index.columns)
                where = index.dialect_options["postgresql"].get("where")
                predicate = f" where `{where}`" if where is not None else ""
                lines.append(f"- {'Unique index' if index.unique else 'Index'}: `{definition}`{predicate}.")
            lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()
    if args.check:
        if not REFERENCE.exists() or REFERENCE.read_text(encoding="utf-8") != rendered:
            raise SystemExit("schema reference is stale; run python -m backend.data.schema_docs")
    else:
        REFERENCE.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
