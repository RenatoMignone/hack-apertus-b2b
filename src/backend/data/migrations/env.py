from alembic import context

from backend.data.schema import metadata


connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("run migrations through navigator db-migrate with a maintainer connection")
context.configure(connection=connection, target_metadata=metadata, include_schemas=True,
                  transactional_ddl=True)
with context.begin_transaction():
    context.run_migrations()
