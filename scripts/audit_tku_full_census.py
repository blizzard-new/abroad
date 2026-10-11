"""Produce machine-readable per-school acceptance, including real blockers."""
from __future__ import annotations

import gzip
from tku_capture_io import read_bytes, exists, captures
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'src/exchange_info/official_data/tku'
BASE='59a20f27fcee00fb597abc79e75ec11778317422'


def main():
    from exchange_info.tku_data import load_tku_records
    from exchange_info.tku_census import census_audit
    from exchange_info.models import DestinationProfile
    audit=census_audit()
    profiles=[DestinationProfile.model_validate_json(line) for line in (B/'destination_profiles.jsonl').read_text().splitlines()]
    assert len(profiles)==len({p.school_name for p in profiles})==287
    sources=[json.loads(gzip.decompress(read_bytes(p))) for p in captures(B/'host_census_sources')]
    attachments=[]
    for source in sources:
        if not source.get('local_file'):continue
        path=B/'host_census_sources'/source['local_file'];blob=read_bytes(path)
        valid_magic=blob.startswith(b'%PDF') or blob.startswith(b'PK')
        assert valid_magic and hashlib.sha256(blob).hexdigest()==source['sha256']
        attachments.append(dict(source_url=source['source_url'],file=source['local_file'],bytes=len(blob),sha256=source['sha256'],magic_valid=valid_magic,checked_at=source['checked_at']))
    unchanged=[]
    for home in ['cgu','ntpu','ntu','ccu','ncu']:
        prefix=f'src/exchange_info/official_data/{home}/'
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',prefix],cwd=ROOT,text=True).splitlines()
        for path in paths:
            original=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
            assert (ROOT/path).read_bytes()==original,path
        unchanged.append(dict(home=home,files=len(paths),status='byte_identical_to_base'))
    old_profiles=subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/destination_profiles.jsonl'],cwd=ROOT)
    assert (B/'destination_profiles.jsonl').read_bytes().startswith(old_profiles)
    schools=[]
    for row in audit['schools']:
        counts=dict(Counter(cell['status'] for cell in row['fields'].values()))
        errors=[dict(url=s['source_url'],http_status=s.get('http_status'),error=s['error']) for s in row['public_source_checks'] if s.get('error')]
        schools.append(dict(id=row['id'],school_name=row['school_name'],country=row['country'],programme_ids=row.get('programme_ids',[]),
            fields=counts,remaining_fields=[dict(key=k,label=c['label'],status=c['status'],reason=c['reason']) for k,c in row['fields'].items() if c['status'] not in {'verified_current','verified_asset'}],
            public_sources_checked=len(row['public_source_checks']),source_open_errors=errors,
            photo_search=row['fields']['campus_photo']['asset_search_check'],coordinate_search=row['fields']['coordinates']['asset_search_check']))
    unknown={k:287-v.get('verified_current',0)-v.get('verified_asset',0) for k,v in audit['field_counts'].items()}
    record_count=len(load_tku_records(include_reference=True))
    assert record_count==128
    states=dict(Counter(s.get('http_status','connection_error') for s in sources if s.get('error')))
    result=dict(base_commit=BASE,checked_date='2026-10-11',directory_rows=286,institutions=287,programme_rows=153,
        original_programmes_preserved=record_count,first_round_history_rows=25,first_round_history_quota=50,
        latest_round_schools=4,latest_round_quota=7,newly_open_applications=0,destination_profiles=len(profiles),
        institutions_with_official_reference_excerpts=sum(bool(r['fields']) for r in map(json.loads,(B/'partner_enrichment.jsonl').read_text().splitlines())),
        public_source_captures=len(sources),opened_sources=sum(not s.get('error') for s in sources),failed_sources=sum(bool(s.get('error')) for s in sources),
        source_failure_statuses=states,downloaded_attachments=attachments,licensed_visual_reviewed_photos=13,
        new_licensed_photos=12,reused_baseline_photos=1,verified_physical_campus_coordinates=2,
        reused_baseline_representative_coordinates=1,total_displayable_coordinates=3,
        current_or_asset_gap_counts=unknown,field_counts=audit['field_counts'],other_home_bundles=unchanged,
        original_tku_destination_prefix='byte_identical_to_base',schools=schools,
        scope_note='來源開啟與原文索引不等於所有欄位已核实；287校每校22欄缺口全列。名額只有4校最新已截止梯次，照片／實體校園座標核對另列，不代表提名校區。',
        blockers=['除最新四校外，當期母校名額與資格尚未核實；總覽不能作本期可選。',
            '接待校一般原文需核對當期、學制、院系、校區與淡江提名；舊文件不混入當期文件。',
            'Wikidata及Commons批次HTTP429已停止，未查完項明確保留技術狀態。',
            '明治2027五份指定模板HTTP503，未列可開啟附件；原文規定和連結適用期另存。',
            '原四校63項缺口與18項矛盾保留，不以新全量資料層掩蓋。'])
    (B/'full_census_acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'schools','downloaded_attachments','field_counts'}},ensure_ascii=False))


if __name__=='__main__':main()
