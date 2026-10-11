from pathlib import Path
import os

def write_atomic(p,s):
 temp=p.with_suffix(p.suffix+'.integration-tmp');temp.write_text(s);os.replace(temp,p)
p=Path('src/exchange_info/ncu_student_view.py');s=p.read_text();start=s.index('def fetch_ncu_partner_universities()');end=s.index('\n\ndef build_ncu_student_dashboard',start)
s=s[:start]+'''def fetch_ncu_partner_universities() -> list[PartnerUniversity]:
    # Stream the reviewed JSONL; read_text().splitlines() retains two copies of
    # the whole Unicode source while the validated models are being built.
    with (NCU_OFFICIAL_DATA_DIR / "partners.jsonl").open(encoding="utf-8") as handle:
        return [PartnerUniversity.model_validate_json(line) for line in handle if line.strip()]
'''+s[end:]
start=s.index('def ncu_processed_pages()');end=s.index('\n\ndef ncu_field_audit',start)
s=s[:start]+'''def ncu_processed_pages() -> list[ProcessedPage]:
    with (NCU_OFFICIAL_DATA_DIR / "pages.jsonl").open(encoding="utf-8") as handle:
        return [ProcessedPage.model_validate_json(line) for line in handle if line.strip()]
'''+s[end:];write_atomic(p,s)
p=Path('tests/test_fit_signals.py');write_atomic(p,p.read_text().replace('assert len(profiles) == 844','assert len(profiles) == 893  # CCU adds49 reference profiles; no current-cycle promotion'))
p=Path('tests/test_school_completeness.py');s=p.read_text().replace("'國立中正大學':55", "'國立中正大學':104").replace('assert len(scores) == 844','assert len(scores) == 893');write_atomic(p,s)
p=Path('/workspace/recovery-tools-20261011/audit_integrated_sources.py');s=p.read_text().replace("sum(p.quota=='0' for p in ntu)","sum(p.quota=='0 名' for p in ntu)");p.write_text(s)
