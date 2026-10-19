# Eric: activate the measured live-capture performance fix

19 October 2026. [Problem, implementation and measurements](../data/CAPTURE_PERFORMANCE.md).
The shared server is still at 0010; do not claim the SQL fix is active there yet.
Existing ingestion, enrichment, checkpoints, storage monitoring, users and flags
must remain in place. No credentials are needed in this document or Git.

1. Review/pull the performance change, preserving ongoing ingestion work. Review
   `0011_capture_performance.py` and `live_capture_fast.sql`; historical 0008 SQL
   remains unchanged. The new migration replaces only the capture function. It
   creates no persistent application tables and does not change corpus rows,
   vectors, taxonomy, grants, active pointers or previous captures.
2. Coordinate a brief pause of new application submissions; let valid work finish
   or cancel only explicitly identified stale application captures. Do not stop
   ingestion/watchdogs or terminate arbitrary database sessions. Keep the normal
   validated backup/recovery procedure. Use the approved migration-owner env.
3. From the host repository root run the existing migration command:

   ```text
   navigator --env-file PRIVATE_MAINTAINER_ENV db-migrate
   ```

   Never use a developer application DSN or redistribute the maintainer env.
   Lock wait is limited to three seconds; if busy, stop and retry after coordination
   rather than widening privileges or disabling triggers. Confirm revision
   `0011_capture_performance` and a repeated migration is a no-op. Compare preserved
   corpus IDs/counts and existing owner/access checks.
4. Update API/worker code together and restart them. Keep private credentials,
   bindings, domain profile, optional-output settings and encoder pins. The new
   capture timeout defaults to 30 seconds; do not raise it to hide a slow plan.
   Existing core 0008–0010 servers remain source-compatible, but only 0011 installs
   the faster function. No database restart or embedding rebuild is required.
5. Repeat Renato-side read-only readiness. Create one permitted case, record the
   elapsed case-creation time and `live_capture_completed` diagnostic, and confirm
   a live owning-case capture with expected source coverage. Do not add fixtures to
   the shared corpus. Do not replay the old quadratic benchmark on the shared host.
6. Verify old captures/reports still read, another user's capture stays inaccessible,
   and a new research run sees newly ready data while existing runs stay pinned.
   Complete actual research, flagged web sources, review and PDF/PPTX download.
   Record real timings and any remaining model/retrieval/fetch bottleneck.

Renato has prepared/tested the patch locally and cancelled only his two stale
capture requests. No shared migration/grant/source change was made for this fix.
