from pathlib import Path
import json, shutil
root=Path('/workspace/abroad-globe-20261011')
p=root/'src/exchange_info/student_view.py'
s=p.read_text(); old='    labels = [col.get("label") or "" for col in payload["table"]["cols"]]'; s=s.replace(old,'    return _partner_rows_from_payload(payload, program_type=program_type, source_url=source_url)\n\n\ndef _partner_rows_from_payload(payload: dict[str, Any], *, program_type: str, source_url: str) -> list[PartnerUniversity]:\n'+old,1);p.write_text(s)
p=root/'src/exchange_info/models.py';s=p.read_text();marker='class StudentDashboard(BaseModel):';s=s.replace(marker,'''class CatalogueSourceStatus(BaseModel):
    status: Literal["retrieved", "saved_reference", "unavailable"]
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    last_attempt_result: Literal["success", "failed"] | None = None
    failure_reason: str | None = None
    snapshot_hash: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    # Retrieval time does not establish the academic year or current publication status.
    current_cycle_verified: bool = False


'''+marker);s=s.replace('class StudentDashboard(BaseModel):\n','class StudentDashboard(BaseModel):\n    catalogue_source: CatalogueSourceStatus | None = None\n',1);p.write_text(s)
dest=root/'src/exchange_info/official_data/cgu_catalogue';dest.mkdir(exist_ok=True)
source=Path('/workspace/cgu-resilience-proposal-20261011/source-capture')
snapshot=json.loads((source/'snapshot.json').read_text());snapshot['snapshot_use']='dated_fallback_reference_not_current_cycle_verification';(dest/'snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
for p in source.glob('*.gviz.json'):shutil.copyfile(p,dest/p.name)
