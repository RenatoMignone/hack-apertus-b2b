#!/bin/sh
set -eu
attempt=0
until mc alias set host http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  attempt=$((attempt+1))
  test "$attempt" -lt 60 || exit 1
  sleep 1
done
mc mb --ignore-existing host/navigator
mc mb --ignore-existing host/langfuse
mc version enable host/navigator
mc version enable host/langfuse
mc admin policy create host navigator-artifacts /policies/navigator.json
mc admin policy create host langfuse-traces /policies/langfuse.json
mc admin user add host "$S3_ACCESS_KEY_ID" "$S3_SECRET_ACCESS_KEY"
mc admin user add host "$TRACE_S3_ACCESS_KEY" "$TRACE_S3_SECRET_KEY"
mc admin policy attach host navigator-artifacts --user "$S3_ACCESS_KEY_ID"
mc admin policy attach host langfuse-traces --user "$TRACE_S3_ACCESS_KEY"
