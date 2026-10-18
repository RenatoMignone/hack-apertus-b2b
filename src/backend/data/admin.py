import secrets
from uuid import uuid4

from psycopg import sql
from sqlalchemy import insert, text

from backend.data import schema as tables


def provision_principal(engine, role, namespace, *, password=None, ingestion=False):
    if not role.replace("_", "").isalnum() or len(role) > 50:
        raise ValueError("role must contain letters, numbers or underscores, at most 50 characters")
    principal_id = uuid4()
    password = password or secrets.token_hex(24)
    with engine.begin() as connection:
        raw = connection.connection.driver_connection
        raw.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(role), sql.Literal(password)))
        if ingestion:
            raw.execute(sql.SQL("GRANT navigator_app TO {}").format(sql.Identifier(role)))
            for schema in ("corpus", "taxonomy", "retrieval", "cases", "ops"):
                raw.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO navigator_app").format(sql.Identifier(schema)))
                raw.execute(sql.SQL("GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA {} TO navigator_app").format(sql.Identifier(schema)))
            connection.execute(text("REVOKE INSERT,UPDATE ON ops.principals,ops.scope_grants FROM navigator_app"))
            connection.execute(text("REVOKE ALL ON FUNCTION ops.prevent_change() FROM PUBLIC"))
            connection.execute(text("GRANT EXECUTE ON FUNCTION ops.ensure_case_scope(uuid) TO navigator_app"))
        else:
            raw.execute(sql.SQL("GRANT navigator_runtime TO {}").format(sql.Identifier(role)))
        connection.execute(insert(tables.principals).values(principal_id=principal_id, database_role=role, namespace=namespace))
    return principal_id, password


def configure_runtime_access(engine, role, namespace, scope_ids):
    """Bind an existing login to live public reads without rotating its password.

    Existing principal rows/cases are retained. Ingestion logins must never use
    this command: it explicitly removes their navigator_app membership.
    """
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from backend.contracts.data import AccessContext
    AccessContext(principal_id=uuid4(), namespace=namespace)
    with engine.begin() as connection:
        flags = connection.execute(text("""SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls
            FROM pg_roles WHERE rolname=:role AND rolcanlogin"""), {"role": role}).mappings().one()
        if any(flags.values()):
            raise ValueError("runtime access requires an ordinary application login")
        raw = connection.connection.driver_connection
        raw.execute(sql.SQL("GRANT navigator_runtime TO {}").format(sql.Identifier(role)))
        if connection.execute(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_app')")).scalar_one():
            raw.execute(sql.SQL("REVOKE navigator_app FROM {}").format(sql.Identifier(role)))
        for table in tables.metadata.tables.values():
            for privilege in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
                if connection.execute(text("""SELECT has_table_privilege(:role,:table,:privilege)
                    AND NOT has_table_privilege('navigator_runtime',:table,:privilege)"""),
                    {"role": role, "table": table.fullname, "privilege": privilege}).scalar_one():
                    raise ValueError("remove residual shared-corpus write privileges before configuring this login")
        principal = connection.execute(select(tables.principals).where(
            tables.principals.c.database_role == role, tables.principals.c.namespace == namespace)).mappings().one_or_none()
        if principal is None:
            principal_id = uuid4()
            connection.execute(insert(tables.principals).values(principal_id=principal_id, database_role=role, namespace=namespace))
        else:
            if not principal["active"]:
                raise ValueError("principal is disabled; review revocation before changing access")
            principal_id = principal["principal_id"]
        for scope_id in set(scope_ids):
            scope = connection.execute(select(tables.scopes).where(tables.scopes.c.scope_id == scope_id)).mappings().one()
            if scope["kind"] != "public" or scope["revoked"]:
                raise ValueError("only explicit active public corpus scopes may be granted")
            connection.execute(pg_insert(tables.scope_grants).values(principal_id=principal_id, scope_id=scope_id,
                can_write=False).on_conflict_do_update(index_elements=["principal_id", "scope_id"], set_={"can_write": False}))
    return principal_id


def grant_scope(engine, principal_id, scope_id, *, write=False):
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    with engine.begin() as connection:
        connection.execute(pg_insert(tables.scope_grants).values(principal_id=principal_id, scope_id=scope_id,
            can_write=write).on_conflict_do_update(index_elements=["principal_id", "scope_id"], set_={"can_write": write}))


def revoke_scope(engine, scope_id):
    with engine.begin() as connection:
        connection.execute(text("UPDATE corpus.scopes SET revoked=true WHERE scope_id=:scope"), {"scope": scope_id})
        connection.execute(text("""
            UPDATE cases.exports e SET status='revoked' FROM cases.result_revisions r
            WHERE e.result_id=r.result_id AND EXISTS (
              SELECT 1 FROM cases.pack_items p JOIN corpus.evidence_spans s USING(evidence_id)
              WHERE p.pack_id=r.pack_id AND s.scope_id=:scope)
        """), {"scope": scope_id})
        connection.execute(text("""
            INSERT INTO ops.outbox(event_id,namespace,idempotency_key,event_type,payload)
            SELECT :event,p.namespace,:key,'scope.revoked',jsonb_build_object('scope_id',CAST(:scope AS text))
            FROM ops.principals p JOIN ops.scope_grants g USING(principal_id)
            WHERE g.scope_id=:scope LIMIT 1 ON CONFLICT(idempotency_key) DO NOTHING
        """), {"event": uuid4(), "key": f"revoke:{scope_id}", "scope": scope_id})
