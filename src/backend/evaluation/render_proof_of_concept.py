"""Build a standalone PDF and public evidence record from the real retrieval receipt."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(".local/proof-concept/raw-results.json"))
    parser.add_argument("--output", type=Path, default=Path("output/pdf/Stregoni_Retrieval_Proof_of_Concept.pdf"))
    parser.add_argument("--evidence-dir", type=Path, default=Path("docs/proof-of-concept"))
    parser.add_argument("--font", default="C:/Windows/Fonts/arial.ttf")
    parser.add_argument("--font-bold", default="C:/Windows/Fonts/arialbd.ttf")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    assert len(data["queries"]) == 4 and all(q["status"] == "succeeded" for q in data["queries"])
    all_hits = [h for q in data["queries"] for h in q["hits"]]
    assert len(all_hits) == 120 and all(h["exact_body_slice"] and h["body_sha256_valid"] for h in all_hits)

    def find(qid, rank):
        return next(h for q in data["queries"] if q["id"] == qid for h in q["hits"] if h["rank"] == rank)

    def span(hit, start, end):
        a = hit["text"].index(start)
        b = hit["text"].index(end, a) + len(end)
        return {"text": hit["text"][a:b], "char_start": hit["char_start"] + a, "char_end": hit["char_start"] + b}

    specifications = [
        ("Lilian Witthauer", "biosensing-lay-terms", 3, "DE_dJournal_01_2023",
         "Direct sensing research lead in a 2023 source",
         "The retrieved interview identifies Witthauer with diabetes technology at UniBE/DCB and describes a continuous blood-glucose sensor. This supports an exploratory sensing lead for HelioSense.",
         "Historical 2023 interview. Current role, technology readiness and availability require confirmation.",
         [("Lilian Witthauer ist", "Diabetes Center Berne (DCB)."), ("Eines meiner aktuellen Projekte", "misst.")]),
        ("José García-Tirado", "biosensing-lay-terms", 9, "dJournal_Ausgabe_2_24_fr",
         "Adjacent systems/control capability in a 2024 source",
         "The DCB publication lists García-Tirado with closed-loop systems. The same passage describes glucose sensors, insulin pumps and algorithmic control. This is a documented systems connection, not proof of a HelioSense-compatible sensor.",
         "2024 source context; no claim of a verified current appointment or willingness to collaborate.",
         [("Prof. Dr José", "Systèmes en boucle fermée"), ("technologiques composés", "pompes à insuline,")]),
        ("Stavroula Mougiakakou", "glucose-sensors", 19, "2012-ISTB",
         "Historical diabetes algorithms lead; follow-up verification needed",
         "The ARTORG report names Mougiakakou in Diabetes Technology Research and discusses glucose-profile prediction with statistical/computational methods. This supports historical relevance to signal processing.",
         "The URL identifies a 2012 report. This is historical evidence, not a current role/contact listing.",
         [("Diabetes Technology Research", "Technical Head of Research Group"), ("Data-driven models", "in the near future")])
    ]
    examples = []
    for name, qid, rank, expected_url, classification, interpretation, boundary, slices in specifications:
        hit = find(qid, rank)
        assert expected_url in hit["source_url"], "Recorded ranking changed; inspect examples before rendering"
        examples.append({"name": name, "query_id": qid, "rank": rank, "classification": classification,
                         "interpretation": interpretation, "boundary": boundary, "hit": hit,
                         "quotes": [span(hit, a, b) for a, b in slices]})
    capability = find("full-demo-brief", 2)
    capability_quote = span(capability, "For the glucose sensors", "directly in the blood.")
    public = {k: data[k] for k in ("started_at", "completed_at", "mode", "strategy", "reranker_enabled",
        "reasoning_model_called", "database_read_only", "cases_created", "schema_revision", "capture", "encoder",
        "source_commit", "demo_fixture", "input_sha256")}
    public.update(frontend_used=False, returned_passage_occurrences=120,
        distinct_documents=len({h["document_id"] for h in all_hits}), exact_slice_checks_passed=120,
        body_hash_checks_passed=120, quality_score=None,
        review_status="Assistant source inspection only; no independent human gold labels",
        working_tree_note="Existing local runtime/ingestion changes were present; new PoC scripts were uncommitted.")
    public["queries"] = []
    for q in data["queries"]:
        public["queries"].append({"id": q["id"], "query": q["query"], "seconds": q["seconds"],
            "limitations": q["limitations"], "accepted_entity_count": len(q["accepted_entity_projection"]),
            "hits": [{k: h[k] for k in ("rank", "chunk_id", "document_id", "document_version_id", "source_url", "title",
                "char_start", "char_end", "evidence_ids", "lexical_rank", "vector_rank", "fusion_score",
                "cosine_distance", "exact_body_slice", "body_sha256_valid", "body_sha256", "version_created_at")}
                for h in q["hits"]]})
    public["selected_examples"] = [{**{k: v for k, v in e.items() if k != "hit"},
        "source_url": e["hit"]["source_url"], "chunk_id": e["hit"]["chunk_id"],
        "evidence_ids": e["hit"]["evidence_ids"], "body_sha256": e["hit"]["body_sha256"]} for e in examples]
    public["capability_example"] = {"query_id": "full-demo-brief", "rank": 2,
        "source_url": capability["source_url"], "quote": capability_quote}
    limitations = [
        "Document retrieval and researcher mentions are demonstrated; accepted canonical entity profiles returned: zero for every query.",
        "No independent expert precision, Recall@10 or semantic-support percentage is measured.",
        "No names were inserted into the queries or used to prefilter retrieval. Examples were selected after inspecting results.",
        "Results contain weak candidates and historical publications; relevance and freshness still need review.",
        "These returned documents cover ARTORG/UniBE and DCB, not proof of UniBE-outside-ARTORG coverage.",
        "Reranking, web, Apertus interpretation/drafting, API review/export and frontend integration were not exercised.",
        "Times are single-run observations with a connected encoder, not production latency benchmarks."
    ]
    public["limitations"] = limitations
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    (args.evidence_dir / "retrieval-results.json").write_text(json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("PoC", args.font))
    pdfmetrics.registerFont(TTFont("PoCBold", args.font_bold))
    pdfmetrics.registerFontFamily("PoC", normal="PoC", bold="PoCBold", italic="PoC", boldItalic="PoCBold")
    ink, accent = colors.HexColor("#193246"), colors.HexColor("#B3343D")
    pale, muted = colors.HexColor("#F1F4F6"), colors.HexColor("#50616B")
    body = ParagraphStyle("PoCBody", fontName="PoC", fontSize=10, leading=14, textColor=ink, spaceAfter=8)
    small = ParagraphStyle("PoCSmall", parent=body, fontSize=8, leading=11, textColor=muted, spaceAfter=5)
    head = ParagraphStyle("PoCHead", parent=body, fontName="PoCBold", fontSize=19, leading=23, spaceAfter=12)
    sub = ParagraphStyle("PoCSub", parent=body, fontName="PoCBold", fontSize=12, leading=16, spaceBefore=7)
    title = ParagraphStyle("PoCTitle", parent=head, fontSize=29, leading=34, spaceAfter=15)
    quote_style = ParagraphStyle("PoCQuote", parent=body, fontSize=9.5, leading=13, leftIndent=10,
        borderColor=accent, borderWidth=0.7, borderPadding=8, backColor=pale, spaceAfter=11)
    story = []

    def p(value, style=body):
        story.append(Paragraph(value, style))
    def safe(value):
        return escape(str(value))
    def quote(value):
        p(safe(" ".join(value.split())), quote_style)
    def source(hit, label):
        p("<b>" + safe(label) + '</b> | <link href="' + safe(hit["source_url"]) +
          '" color="#B3343D"><u>Open original institutional source</u></link>', small)
        p("Chunk " + hit["chunk_id"] + " | body characters " + str(hit["char_start"]) + "-" + str(hit["char_end"]), small)
    def grid(rows, widths):
        table = Table([[Paragraph(safe(v), small) for v in row] for row in rows], colWidths=widths, hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),pale), ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LINEBELOW",(0,0),(-1,0),0.8,accent),
            ("LINEBELOW",(0,1),(-1,-1),0.3,colors.HexColor("#D8E0E5")),
            ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
        story.extend([table, Spacer(1,10)])

    moment = datetime.fromisoformat(data["completed_at"])
    p("STREGONI / B TO BERN", small)
    p("Retrieval works.<br/>The evidence is inspectable.", title)
    p("HelioSense proof of concept", head)
    p("A standalone fallback for demonstrating backend retrieval without a working frontend connection.")
    p("Test: " + moment.strftime("%d %B %Y, %H:%M UTC") + " / " +
      moment.astimezone(ZoneInfo("Europe/Madrid")).strftime("%H:%M Madrid"), small)
    grid([["Capture searched","Demo queries","Passages returned","Distinct documents"],
          ["127,902 chunks","4 completed","120 occurrences","52 documents"]], [45*mm,39*mm,44*mm,42*mm])
    p("What the test demonstrates", sub)
    p("The production hybrid-retrieval adapter returned real institutional passages for the fictional HelioSense demo. "
      "Selected passages identify relevant people and explain sensing, closed-loop and glucose-prediction capabilities. "
      "Every returned passage matched its exact stored body slice and body hash.")
    p("Named source-backed examples", sub)
    p("<b>Lilian Witthauer</b> - sensing/diabetes technology; passage rank 3 in the lay-wording query.<br/>"
      "<b>José García-Tirado</b> - closed-loop systems; passage rank 9 in that query.<br/>"
      "<b>Stavroula Mougiakakou</b> - historical algorithms research; passage rank 19 in the sensor query.")
    p("Scope of this proof", sub)
    p("This demonstrates document retrieval and inspected researcher mentions. The accepted structured-entity projection "
      "returned zero profiles for every query. It is not a complete expert-directory or Recall@10 benchmark. "
      "Historical publications require freshness review.")
    p("Fictional company input / real corpus evidence / no frontend / no database writes", small)

    story.append(PageBreak())
    p("01 / The demo and measured results", head)
    p("HelioSense is a fictional Swiss medtech company exploring wearable continuous glucose monitoring. It asks for "
      "Bern expertise in sensing, algorithms, device development and evaluation. No real company plan was submitted.")
    grid([["Input","Search time","Hits","Literal checks"],
          *[[q["id"],str(q["seconds"])+" s","30","30 / 30 passed"] for q in data["queries"]]],
         [76*mm,28*mm,20*mm,46*mm])
    p("Times cover encoding/search before separate body verification and entity projection. "
      "Each input was run once. Cold/warm conditions were not controlled.", small)
    for q in data["queries"]:
        p(q["id"], sub)
        p(safe(q["query"]) if q["id"] != "full-demo-brief" else
          "The entire demo/case-brief.md was submitted verbatim, including simulation boundaries. "
          "The exact input is preserved in the companion JSON.", small)
    p("Procedure", sub)
    p("Queries contained no researcher names and used no name-based prefilter. Lexical and dense branches ran independently, "
      "then reciprocal rank fusion combined them. No reranker or web discovery was used. "
      "Examples were selected only after inspecting results.")
    p("All 30 passages per query are retained in the companion rank/source record. A passage's rank is not the "
      "rank of a deduplicated person. No expert-level score is inferred.", small)

    story.append(PageBreak())
    p("02 / Source-backed people", head)
    for e in examples[:2]:
        p(e["name"], sub)
        p(safe(e["classification"]), small)
        p(safe(e["interpretation"]))
        for q in e["quotes"]:
            quote(q["text"])
        source(e["hit"], e["query_id"] + ", rank " + str(e["rank"]))
        p("<b>Boundary:</b> " + safe(e["boundary"]), small)
        story.append(Spacer(1,6))
    p("Original source language/characters are retained; whitespace is normalized for display. "
      "Exact text and absolute source character offsets are preserved in retrieval-results.json.", small)

    story.append(PageBreak())
    p("03 / Historical lead and capability evidence", head)
    e = examples[2]
    p(e["name"], sub); p(safe(e["classification"]), small); p(safe(e["interpretation"]))
    for q in e["quotes"]:
        quote(q["text"])
    source(e["hit"], e["query_id"] + ", rank " + str(e["rank"]))
    p("<b>Boundary:</b> " + safe(e["boundary"]), small)
    p("Direct capability from the full demo brief", sub)
    quote(capability_quote["text"])
    source(capability, "full-demo-brief, rank 2")
    p("The DCB Sensing & Smart Monitoring passage supports optical glucose-measurement research without assigning "
      "that capability to a person not named in this passage.")
    p("Ranking still needs improvement", sub)
    p("The sensor-wording query ranked a DextEgg fine-motor rehabilitation page first. The full-brief query ranked "
      "a generic ARTORG passage first. These are weak matches, not supported glucose-sensing claims. "
      "Need-fit assessment and source inspection remain necessary.")

    story.append(PageBreak())
    p("04 / Verify or replay without the frontend", head)
    p("Mechanical checks", sub)
    p("For each of 120 returned passage occurrences, the ordinary authorized connection read the stored document version, "
      "compared body[char_start:char_end] with the hit and recomputed the complete body's SHA-256. All passed. "
      "Literal integrity does not establish semantic correctness or source truth.")
    p(("Connections enforced read-only transactions" if data.get("database_read_only") else
       "Connections permitted only temporary retrieval tables and no persistent writes") +
      " and bounded statement/lock timeouts. An existing owned capture "
      "was reused. No case, snapshot, claim, grant, corpus update or migration was created.")
    grid([["Item","Recorded value"],["Schema",data["schema_revision"]],
          ["Snapshot",data["capture"]["snapshot_id"]],["Build",data["capture"]["build_id"]],
          ["Encoder","google/embeddinggemma-2; 768 dimensions"],["Encoder revision",data["encoder"]["revision"]],
          ["Application source",data["source_commit"][:12]+" + existing local changes"],
          ["Strategy","Independent lexical/dense + RRF; no reranker"],
          ["Evidence record","docs/proof-of-concept/retrieval-results.json"]], [39*mm,131*mm])
    p("Replay using a private authorized environment and an existing owned run:", small)
    quote("python -m backend.evaluation.proof_of_concept --env-file PRIVATE_ENV --run-id OWNED_RUN_ID")
    p("Optional --db-host HOST --db-port PORT selects the same authorized database's connection address. "
      "Credentials and local tokenizer assets are not included. Full instructions and hashes are in the companion README.", small)
    p("What remains unproven", sub)
    p("Independent human gold labels, expert precision/Recall@10, current availability, complete profiles, "
      "UniBE-outside-ARTORG coverage, full Apertus reasoning/drafting, API export, frontend integration and target "
      "deployment were not tested. These are inspectable research leads, not invitations, clinical advice or partnerships.")
    p("Team Stregoni: Renato Mignone, Elia Innocenti, Eric Ruiz Giménez, Mohamed Kechiche.", small)

    def decorate(canvas, doc):
        w,h = doc.pagesize
        canvas.setStrokeColor(accent); canvas.setLineWidth(1); canvas.line(20*mm,h-17*mm,w-20*mm,h-17*mm)
        canvas.setFont("PoC",8); canvas.setFillColor(muted)
        canvas.drawString(20*mm,12*mm,"B2B / STREGONI - backend retrieval proof of concept")
        canvas.drawRightString(w-20*mm,12*mm,str(doc.page))
    document = SimpleDocTemplate(str(args.output), pagesize=(210*mm,297*mm),
        leftMargin=20*mm,rightMargin=20*mm,topMargin=24*mm,bottomMargin=21*mm,
        title="B to Bern - HelioSense Retrieval Proof of Concept",author="Team Stregoni")
    document.build(story,onFirstPage=decorate,onLaterPages=decorate)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    lines = ["# B2B / Stregoni - Retrieval proof of concept","",
        "[Open the standalone PDF](../../output/pdf/Stregoni_Retrieval_Proof_of_Concept.pdf).",
        "[Machine-readable rank/source evidence](retrieval-results.json).","",
        "## Outcome","",
        "Four real-corpus queries completed against one authorized capture of 127,902 chunks. "
        "They returned 120 passage occurrences across 52 documents. All 120 exact slices and body-hash checks passed. "
        "The company is fictional; institutional evidence is real.","",
        "**Accepted structured entity profiles: zero for each query.** This proves document retrieval with "
        "source-backed researcher mentions, not a validated canonical expert directory.","","## Measured queries",""]
    lines += ["- **"+q["id"]+"**: "+str(q["seconds"])+" s, 30 hits, 30 literal checks passed." for q in data["queries"]]
    lines += ["","Times cover search/encoding before separate verification and entity projection; each input was run once.",
              "","## Selected source-backed examples",""]
    for e in examples:
        lines += ["### "+e["name"],"",e["classification"]+".","",e["interpretation"],"",
            "Query "+e["query_id"]+", passage rank **"+str(e["rank"])+"**. [Original source]("+e["hit"]["source_url"]+").",""]
        for q in e["quotes"]:
            lines += ["> "+" ".join(q["text"].split()),"",
                "Exact source characters "+str(q["char_start"])+":"+str(q["char_end"])+".",""]
        lines += ["**Boundary:** "+e["boundary"],""]
    lines += ["## Honest limits","",*["- "+s for s in limitations],"",
        "Ranking counterexample: a DextEgg rehabilitation page ranked first for the sensor wording. It is not "
        "presented as a glucose-sensing match. Complete rankings are retained.","","## Reproduce without the frontend","",
        "Use the installed backend, a private single-operator environment and an existing owner-authorized run/capture "
        "with the matching encoder configuration/tokenizer:","","~~~text",
        "python -m backend.evaluation.proof_of_concept --env-file PRIVATE_ENV --run-id OWNED_RUN_ID","~~~","",
        "Optional --db-host HOST --db-port PORT selects the connection address of the same authorized database. "
        "Current replays allow temporary retrieval tables but no persistent writes and print no credentials. They make real configured "
        "hosted-embedding calls using permitted fictional/public input. It creates no case or migration.","",
        "Exact queries, model/capture pins, all rank/source records, hashes and selected quotes are in "
        "retrieval-results.json. Full raw text remains in ignored .local/proof-concept/raw-results.json "
        "rather than being republished wholesale.","","~~~text",
        "python -m backend.evaluation.render_proof_of_concept","~~~","",
        "The renderer uses ReportLab and defaults to Windows Arial. On other systems pass --font and --font-bold "
        "with Unicode TTF files. This fallback PDF is distinct from an application-approved company export "
        "and from the required technical-report PDF.","","## Provenance","",
        "- Completed UTC: "+data["completed_at"]+".",
        "- Source commit: "+data["source_commit"]+"; existing local runtime/ingestion changes were present.",
        "- New PoC scripts were uncommitted at this run; no clean-release certification is claimed.",
        "- Schema: "+data["schema_revision"]+".",
        "- Snapshot: "+data["capture"]["snapshot_id"]+".",
        "- Demo brief SHA-256: "+data["input_sha256"]+".",
        "- PDF SHA-256: "+digest+".",
        "- An initial harness schema-reference error was corrected before this successful receipt. "
        "Production retrieval was not changed by this task.",
        "- Relevance was inspected by the assistant; there are no independent human gold labels.",
        "- No frontend, shared migration, ingestion change, public entity approval, commit or push was performed.",""]
    (args.evidence_dir/"README.md").write_text("\n".join(lines),encoding="utf-8")
    print("Created "+str(args.output))
    print("Created public evidence record and Markdown under "+str(args.evidence_dir))


if __name__ == "__main__":
    main()
