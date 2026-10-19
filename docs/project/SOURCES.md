# Requirements and source provenance

| Material | What it establishes | Limits |
| --- | --- | --- |
| [Supplied Notion text](../sources/NOTION_CHALLENGE_2026-10-18.md) / [challenge brief](../challenge/CHALLENGE_BRIEF.md) | Partner objective, three source families, structured/traceable results, evaluation and compliance requirements | User-supplied page contents; not independent live-page verification |
| Root submission template | Required layout, report PDF/video and model variables | Current organizer instructions may clarify event/form details |
| [Workshop transcripts](../recordings/README.md) / [timestamped insights](../recordings/RECORDING_INSIGHTS.md) | Operator workflow, permitted intake, scientific/business vocabulary gap, human selection and concise output | Transcription/speaker authority not audio-verified; other-track statements are not requirements |
| [Partner materials](../provided_material/README.md) | UniBE discovery workbook, slide template and English logo | Workbook is best-effort, not exhaustive; branding challenge-only |
| Current source contracts/schema | Implemented data fields, ports and HTTP surface | Implementation is not proof of model quality or deployed availability |
| [Verification](../judges/VERIFICATION.md) | Dated tests/probes and narrow partial live result | Synthetic, protocol, live quality and deployment checks have different scope |

The team chose PostgreSQL/pgvector, LangGraph/LangChain, local Langfuse, explicit
Apertus 70B and a shared embedding protocol; these are implementation decisions,
not additional organizer mandates. Current architecture is in the focused guides,
not a chronological task log.

When requirements and conversational suggestions differ, preserve the stronger
written traceability requirement and document the distinction. The 80% Recall@10
target is official; intent-balanced aggregation is the team's operational definition.
Workbook Notes mention 71 domains but the supplied sheet contains 42 populated
entries; use actual rows without inventing missing records. Source families can
overlap, and a page count cannot establish coverage.

Preserve raw transcripts, the supplied Notion snapshot and original binary assets.
They support requirements/history and do not enter the scientific evidence corpus.
Apache-2.0 code licensing does not grant all third-party redistribution rights.
