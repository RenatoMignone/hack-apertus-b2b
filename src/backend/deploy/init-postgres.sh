#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<'SQL'
\getenv navigator_password NAVIGATOR_MIGRATOR_PASSWORD
\getenv graph_password LANGGRAPH_PASSWORD
\getenv trace_password LANGFUSE_DB_PASSWORD
SELECT format('CREATE ROLE navigator_migrator LOGIN PASSWORD %L', :'navigator_password') \gexec
SELECT format('CREATE ROLE langgraph LOGIN PASSWORD %L', :'graph_password') \gexec
SELECT format('CREATE ROLE langfuse LOGIN PASSWORD %L', :'trace_password') \gexec
CREATE ROLE navigator_app NOLOGIN;
CREATE DATABASE navigator OWNER navigator_migrator;
CREATE DATABASE langgraph OWNER langgraph;
CREATE DATABASE langfuse OWNER langfuse;
REVOKE CONNECT ON DATABASE navigator, langgraph, langfuse FROM PUBLIC;
GRANT CONNECT ON DATABASE navigator TO navigator_app;
GRANT CONNECT ON DATABASE langgraph TO langgraph;
GRANT CONNECT ON DATABASE langfuse TO langfuse;
SQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname navigator -c 'CREATE EXTENSION vector; REVOKE CREATE ON SCHEMA public FROM PUBLIC;'
