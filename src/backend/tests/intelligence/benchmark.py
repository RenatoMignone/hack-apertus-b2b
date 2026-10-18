"""Opt-in 70B-first comparison on identical, explicitly synthetic public-safe cases.

No database, confidential documents or external evidence collection. Never
prints prompts, credentials or provider response bodies; outputs are local JSON.
"""
import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import monotonic

from backend.contracts.pipeline import CaseInterpretation, ReportEvidencePack, SupportedClaim
from backend.contracts.services import EvidenceRecord, PersistedClaims, ResearchBundle, ServiceError
from backend.evidence import create_reasoning_services
from backend.models.reasoning import ModelSettings
from backend.models.reasoning.client import StructuredTasks
from backend.tests.intelligence.conftest import ident
from backend.contracts.data import AccessContext
from backend.contracts.services import RunContext


def fixture():
    context = RunContext(access=AccessContext(principal_id=ident("principal"),namespace="test_intelligence"),
        case_id=ident("case"),input_id=ident("input"),run_id=ident("run"),snapshot_id=ident("snapshot"),
        profile_id=ident("profile"),taxonomy_version_id=ident("taxonomy"),build_id=ident("build"),
        embedding_config_hash="synthetic-only",mode="connected",
        deadline_at=datetime.now(timezone.utc)+timedelta(minutes=12),max_output_tokens=1800,
        request_id="intelligence-opt-in-comparison")
    text=("Example Laboratory develops glucose sensors. The sensor is not clinically approved. "
          "Partner availability is not stated.")
    evidence=EvidenceRecord(evidence_id=ident("evidence"),document_version_id=ident("version"),
        scope_id=ident("scope"),title="Synthetic model comparison; not an actual institution",
        url="https://fixture.invalid/research",language="en",body_hash="a"*64,char_start=0,char_end=len(text),
        literal_text=text,fetched_at=datetime(2026,10,18,tzinfo=timezone.utc),origin="web",review_status="unreviewed")
    interpretation=CaseInterpretation(company_summary="Synthetic operator requests sensor development.",
        activity_label="Glucose sensors",primary_field="medtech",needs=["Glucose sensor development"],
        bern_intents=["Research collaboration"],constraints=["Exclude animal testing."])
    claims=[SupportedClaim(claim_id=ident(name),text=statement,evidence_ids=[evidence.evidence_id])
        for name,statement in [("supported","Example Laboratory develops glucose sensors."),
            ("contradicted","The sensor is clinically approved."),
            ("unsupported","Example Laboratory is willing to collaborate immediately.")]]
    return context,evidence,interpretation,claims


async def compare(model_name,values):
    context,evidence,interpretation,claims=fixture()
    receipts=[]
    settings=ModelSettings(base_url=values.get("LLM_BASE_URL","https://gateway.keera.ch/api/v1"),
        model_name=model_name,api_key=values.get("LLM_API_KEY",""),timeout_seconds=90,max_attempts=1,
        max_output_tokens=1800)
    service=create_reasoning_services(settings,receipt=receipts.append)
    raw_outputs=[]
    class SyntheticRecordingTasks(StructuredTasks):
        async def _invoke(self,messages,context,task,**kwargs):
            result=await super()._invoke(messages,context,task,**kwargs)
            raw_outputs.append({"task":task,"content":result.content})
            return result
    service.tasks=SyntheticRecordingTasks(service.tasks.model,receipt=receipts.append)
    rows=[]
    async def step(name,call,expected=None):
        started=monotonic()
        try:
            value=await call()
            row={"task":name,"status":"valid","elapsed_seconds":round(monotonic()-started,3),
                 "output":value.model_dump(mode="json")}
            if expected:
                row["expected_fixture_check"]=expected(value)
        except ServiceError as error:
            row={"task":name,"status":error.code,"elapsed_seconds":round(monotonic()-started,3)}
        rows.append(row)
        print(json.dumps({"model":model_name,**{k:v for k,v in row.items() if k!="output"}}),flush=True)
    await step("interpret_ambiguity",lambda:service.interpret(
        "Synthetic case: we make devices and want help in Bern, but have not specified the capability needed.",
        {"concepts":[]},context),lambda v:bool(v.blocking_questions))
    research=ResearchBundle(evidence=[evidence])
    await step("extract",lambda:service.extract(interpretation,research,context),
        lambda v:bool(v.entities) and any(c.statement==claims[0].text for c in v.claims))
    def check_assessment(value):
        statuses={str(a.claim_id):a.status for a in value.assessments}
        return statuses=={str(c.claim_id):s for c,s in zip(claims,["supported","contradicted","unsupported"])}
    await step("assess",lambda:service.assess(PersistedClaims(claims=claims),[evidence],context),check_assessment)
    pack=ReportEvidencePack(interpretation=interpretation,claims=claims[:1],outcome="partial",
        gaps=["Clinical approval and expert availability must not be implied."],
        coverage={"fixture":"synthetic"})
    await step("draft",lambda:service.draft(pack,"Use one concise reason; preserve all caveats.",context))
    draft_row=next((r for r in rows if r["task"]=="draft" and r["status"]=="valid"),None)
    if draft_row:
        from backend.contracts.pipeline import DraftRevision
        draft=DraftRevision.model_validate(draft_row["output"])
        await step("assess_draft",lambda:service.assess_draft(draft,pack,context),lambda v:v.status=="supported")
    return {"model":model_name,"fixture":"synthetic only; not retrieval/real-company quality",
            "rows":rows,"receipts":receipts,"synthetic_raw_outputs":raw_outputs}


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--env-file",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--models",nargs="+",default=["apertus-v1-5-70b","apertus-v1-5-8b"])
    args=parser.parse_args()
    values={}
    for line in args.env_file.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k,v=line.split("=",1);values[k.strip()]=v.strip().strip('"').strip("'")
    output=[]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for model in args.models:
        output.append(await compare(model,values))
        args.output.write_text(json.dumps(output,indent=2))


if __name__=="__main__":
    asyncio.run(main())
