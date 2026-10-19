# HelioSense demo run checklist

## 1. Create and run a case

1. Connect the application to the authenticated backend in HTTP mode. Confirm it
   is not using the frontend's mock demo mode.
2. Create a new case and paste the full text from `case-brief.md`.
3. Start research and follow the run status until it succeeds, requests
   clarification, or reports a failure. A queued case is not a completed run.
4. Open the result and inspect each card's cited evidence excerpt and original
   URL. Check that every factual field is supported by its own cited passage.
5. Review all cards. Keep only the items relevant to this fictional scenario;
   reject weak fits as an editorial decision, not as proof the source is false.
6. Accept the exact reviewed result and export the PDF. The server should block
   export until all cards are reviewed and at least one is kept.

## 2. Exercise manual business context (optional)

If the case detail advertises manual business context, enter the values from
`business-context.json` through the UI and confirm that they are permitted
fictional scenario inputs. They should appear as attributed hypothetical plans,
not as facts about a real company or economic impact. Saving them creates a new
case input/research revision, so run and review the resulting report again.

Do not opt this case into own-case memory. It is synthetic and must remain
ineligible for that feature.

## 3. Compare terminology

Create separate cases using each prompt in `query-variants.json`, against the
same corpus/configuration where possible. Compare the cited people/units and
their source support. Treat the output as a qualitative smoke check only: the
fixture provides no independently reviewed expected-expert labels, and equal
results are not guaranteed.

## 4. Acceptance notes

- Intake retains the fictional scenario and does not request confidential files.
- The run's actual status and limitations are visible; no success is inferred
  from a returned case ID.
- Every reported person, affiliation, role, project and service has direct source
  evidence; missing information remains missing.
- The report keeps direct evidence separate from adjacent fit or transfer ideas.
- Source links resolve to the allowed institutional domains and excerpts support
  the claims beside them.
- All-card review and one-kept-item gates are enforced before PDF export.
- Record the case/run IDs, corpus snapshot or live-capture time, model settings,
  source families returned, failures, and human review notes separately from the
  fictional prompt. Do not report synthetic runs as retrieval-quality scores.
