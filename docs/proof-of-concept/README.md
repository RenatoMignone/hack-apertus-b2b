# B2B / Stregoni - Retrieval proof of concept

[Open the standalone PDF](../../output/pdf/Stregoni_Retrieval_Proof_of_Concept.pdf).
[Machine-readable rank/source evidence](retrieval-results.json).

## Outcome

Four real-corpus queries completed against one authorized capture of 127,902 chunks. They returned 120 passage occurrences across 52 documents. All 120 exact slices and body-hash checks passed. The company is fictional; institutional evidence is real.

**Accepted structured entity profiles: zero for each query.** This proves document retrieval with source-backed researcher mentions, not a validated canonical expert directory.

## Measured queries

- **full-demo-brief**: 24.824 s, 30 hits, 30 literal checks passed.
- **glucose-sensors**: 21.839 s, 30 hits, 30 literal checks passed.
- **cgm**: 18.119 s, 30 hits, 30 literal checks passed.
- **biosensing-lay-terms**: 17.542 s, 30 hits, 30 literal checks passed.

Times cover search/encoding before separate verification and entity projection; each input was run once.

## Selected source-backed examples

### Lilian Witthauer

Direct sensing research lead in a 2023 source.

The retrieved interview identifies Witthauer with diabetes technology at UniBE/DCB and describes a continuous blood-glucose sensor. This supports an exploratory sensing lead for HelioSense.

Query biosensing-lay-terms, passage rank **3**. [Original source](https://www.dcberne.com/wp-content/uploads/2023/08/DE_dJournal_01_2023_web_Partnerseite.pdf).

> Lilian Witthauer ist Assistenzprofessorin für Diabetestechnologie an der Universität Bern und dem Diabetes Center Berne (DCB).

Exact source characters 5138:5265.

> Eines meiner aktuellen Projekte be - fasst sich mit der Entwicklung eines Sensors, der kontinuierlich und verzö- gerungsfrei den Glukosegehalt im Blut misst.

Exact source characters 3202:3361.

**Boundary:** Historical 2023 interview. Current role, technology readiness and availability require confirmation.

### José García-Tirado

Adjacent systems/control capability in a 2024 source.

The DCB publication lists García-Tirado with closed-loop systems. The same passage describes glucose sensors, insulin pumps and algorithmic control. This is a documented systems connection, not proof of a HelioSense-compatible sensor.

Query biosensing-lay-terms, passage rank **9**. [Original source](https://www.dcberne.com/wp-content/uploads/2024/08/dJournal_Ausgabe_2_24_fr_web_def_DCB.pdf).

> Prof. Dr José García-Tirado, Systèmes en boucle fermée

Exact source characters 159:214.

> technologiques composés de capteurs de glucose et de pompes à insuline,

Exact source characters 610:682.

**Boundary:** 2024 source context; no claim of a verified current appointment or willingness to collaborate.

### Stavroula Mougiakakou

Historical diabetes algorithms lead; follow-up verification needed.

The ARTORG report names Mougiakakou in Diabetes Technology Research and discusses glucose-profile prediction with statistical/computational methods. This supports historical relevance to signal processing.

Query glucose-sensors, passage rank **19**. [Original source](https://www.artorg.unibe.ch/unibe/portal/fak_medizin/dept_weitere/ins_artorg/content/e977173/e977178/e977270/pane977271/e993919/files993926/2012-ISTB_eng.pdf).

> Diabetes Technology Research Stavroula Mougiakakou, Technical Head of Research Group

Exact source characters 80319:80403.

> Data-driven models, based on advanced statistical and computational intelligence meth- ods are developed for the prediction of glucose profile in the near future

Exact source characters 79430:79593.

**Boundary:** The URL identifies a 2012 report. This is historical evidence, not a current role/contact listing.

## Honest limits

- Document retrieval and researcher mentions are demonstrated; accepted canonical entity profiles returned: zero for every query.
- No independent expert precision, Recall@10 or semantic-support percentage is measured.
- No names were inserted into the queries or used to prefilter retrieval. Examples were selected after inspecting results.
- Results contain weak candidates and historical publications; relevance and freshness still need review.
- These returned documents cover ARTORG/UniBE and DCB, not proof of UniBE-outside-ARTORG coverage.
- Reranking, web, Apertus interpretation/drafting, API review/export and frontend integration were not exercised.
- Times are single-run observations with a connected encoder, not production latency benchmarks.

Ranking counterexample: a DextEgg rehabilitation page ranked first for the sensor wording. It is not presented as a glucose-sensing match. Complete rankings are retained.

## Reproduce without the frontend

Use the installed backend, a private single-operator environment and an existing owner-authorized run/capture with the matching encoder configuration/tokenizer:

~~~text
python -m backend.evaluation.proof_of_concept --env-file PRIVATE_ENV --run-id OWNED_RUN_ID
~~~

Optional --db-host HOST --db-port PORT selects the connection address of the same authorized database. The harness enforces read-only connections and prints no credentials. It makes real configured hosted-embedding calls using permitted fictional/public input. It creates no case or migration.

Exact queries, model/capture pins, all rank/source records, hashes and selected quotes are in retrieval-results.json. Full raw text remains in ignored .local/proof-concept/raw-results.json rather than being republished wholesale.

~~~text
python -m backend.evaluation.render_proof_of_concept
~~~

The renderer uses ReportLab and defaults to Windows Arial. On other systems pass --font and --font-bold with Unicode TTF files. This fallback PDF is distinct from an application-approved company export and from the required technical-report PDF.

## Provenance

- Completed UTC: 2026-10-19T09:22:42.998125+00:00.
- Source commit: a35d70af7f654c7cb55614c0040fe56c80d3e239; existing local runtime/ingestion changes were present.
- New PoC scripts were uncommitted at this run; no clean-release certification is claimed.
- Schema: 0012_membership_lookup.
- Snapshot: 658224cd-9e05-4fa1-bbbb-bc7d309f7fdf.
- Demo brief SHA-256: 8055986536c86a6c64bf936014b8c001762ab30a8e88f9a830b4213ddc4a1a6f.
- PDF SHA-256: 259b6f431253516e078a2ee60532fbddcfe4d803f44a7668b0bd58c2d59cc9d8.
- An initial harness schema-reference error was corrected before this successful receipt. Production retrieval was not changed by this task.
- Relevance was inspected by the assistant; there are no independent human gold labels.
- No frontend, shared migration, ingestion change, public entity approval, commit or push was performed.
