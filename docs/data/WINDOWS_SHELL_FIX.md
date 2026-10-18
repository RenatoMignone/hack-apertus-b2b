# Windows shell-script checkout fix

18 October 2026 · Permanent repository fix: root `.gitattributes` specifies
`*.sh text eol=lf`. Future checkouts retain Linux shell line endings even with
Windows `core.autocrlf=true`. No shell logic, secrets, volumes or migrations change.
The original failure/recovery is recorded in [migration status](../team/MIGRATION_STATUS.md).

## Eric: apply on the existing host checkout

1. Pull this commit into the actual host checkout. Check for intentional edits to
   `src/backend/deploy/init-storage.sh`; preserve them before forcing a checkout.
2. If that script has no intentional local edits, force its existing working copy
   to be rewritten using the new attributes (pull alone may leave old CRLF bytes):

   ```powershell
   git checkout-index --force -- src/backend/deploy/init-storage.sh
   git ls-files --eol src/backend/deploy/init-storage.sh
   ```

   Expect `i/lf w/lf` and the LF attribute. If locally edited, preserve/normalize
   that copy explicitly instead of overwriting it.
3. Coordinate with the ingestion operator before touching running services. Verify
   the normal storage bootstrap **without** the private carriage-return override,
   using the real host env/project and the existing Compose file. No volume reset
   or full stack restart is needed just to inspect the line endings.
4. Remove the temporary override from operational commands only after normal
   bootstrap succeeds. Keep the private pre-upgrade backup/recovery record intact.

Verified on this Mac: Git checkout with `core.autocrlf=true` produced LF-only
`init-storage.sh`; `/bin/sh -n` passed. The existing script is already LF in git.
Docker startup on Eric's host has **not** been rerun by this task; the private
override remains his recovery option until step 3 passes.
