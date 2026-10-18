# Report generation, checks and rendering

`generation/`, `validation/`, `rendering/` are future integrations; the
[processing contract](../../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md) defines
their stages. `data/repositories/drafts.py` persists reason cards only after an
explicit supported assessment of the exact draft hash. It carries selections
only for unchanged content/support, and binds review to the selection hash.
Live semantic draft checks and PDF rendering remain unimplemented; tests use
explicit synthetic validator assertions and artifact bytes. Editable PowerPoint
follows PDF, using the challenge-only template/logo. Writers cannot browse or
mutate a frozen pack. Unsupported assertions route to evidence preparation.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
