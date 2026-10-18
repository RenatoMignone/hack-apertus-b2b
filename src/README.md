# Application source

**Backend and HTTP frontend integrated; shared real-corpus rollout pending.**

- [frontend/](frontend/README.md): React/Vite browser client over authenticated HTTP; explicit mock demo mode.
- [backend/](backend/README.md): HTTP server and separated backend components.

Read the [source structure](../docs/plans/SOURCE_STRUCTURE.md),
[frontend/backend handoff](../docs/plans/FRONTEND_BACKEND_API.md) and
[processing boundaries](../docs/plans/REPORT_PROCESSING_BOUNDARIES.md).
The root submission template remains unchanged. [Current status](../docs/project/STATUS.md)
and [live setup](../docs/data/LIVE_SETUP.md) distinguish tested synthetic integration
from real corpus/model deployment. Run the data layer using the
[deployment guide](../docs/data/DEPLOYMENT.md).

For independent feature work, follow the [module handoffs](../docs/plans/MODULE_HANDOFFS.md).
The frontend is separately owned; backend tasks must leave it unchanged.
