"""Export actual local TKU data/test/browser evidence, including existing failures."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from exchange_info.tku_data import BUNDLE, load_tku_records, load_tku_sources, tku_integrity_report
from exchange_info.tku_completeness import matrix_row


def test_result(path):
    root=ET.parse(path).getroot();cases=root.findall('.//testcase')
    failures=[c.get('classname')+'::'+c.get('name') for c in cases if c.find('failure') is not None or c.find('error') is not None]
    skipped=sum(c.find('skipped') is not None for c in cases)
    return dict(tests=len(cases),passed=len(cases)-len(failures)-skipped,failed=len(failures),skipped=skipped,
        failure_ids=failures,junit_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main(args):
    current=test_result(args.junit);baseline=test_result(args.baseline_junit)
    sources=load_tku_sources();rows=load_tku_records(include_reference=True)
    data=tku_integrity_report()
    data.update(source_count=len(sources),unique_source_urls=len({s['source_url'] for s in sources}),
        downloaded_original_attachments=sum(bool(s.get('local_file')) for s in sources),
        failed_reads=[dict(id=s['id'],url=s['source_url'],error=s['error']) for s in sources if s.get('open_status')=='failed'],
        current_matrix=[dict(id=r.id,school_name=r.fields['school_name'].value,field_states=matrix_row(r)['field_states']) for r in rows if r.selection_status=='listed'],
        matrix_school_count=len(rows),matrix_fields_per_school=38,currently_open_choices=0,
        quota_states=dict(Counter(r.quota_status for r in rows)),
        host_documents_by_school=[dict(school=r['school_name'],phases=dict(Counter(d['phase'] for d in r['documents']))) for r in json.loads((BUNDLE/'host_documents.json').read_text())])
    browser=json.loads(args.browser.read_text())
    if len(browser.get('document_catalog_checks',[]))!=4:raise ValueError('Latest four-school document-browser evidence is not complete')
    report=dict(checked_at='2026-10-08',branch='data/tku-exchange-20261008',integration_main='293546e807294dc0812f390b240a4cfb68e86cd0',
        data=data,current_tests=current,baseline_failure_comparison=baseline,
        new_failure_ids=sorted(set(current['failure_ids'])-set(baseline['failure_ids'])),
        browser=browser,
        observed_ui_issue='Switching an existing document-centre target retained the original target after confirmation; main reproduction not yet verified. Four schools are tested in fresh independent student contexts.',
        checks=dict(openapi='passed',python_syntax='passed',javascript_syntax='passed',diff_check='passed',offline_rebuild='passed',
            lockfile_check='failed on both this branch and untouched main: lockfile needs update; no lockfile change',
            remote_ci='Previous quality run 37719707403 failed with no jobs/checks; log unavailable. Latest run status recorded separately after push.'),
        remaining_scope='124 archived rows have home sources; their host current fields are explicitly not individually researched. Four latest Japanese choices have reviewed public host material and field-specific gaps. Not all application forms are public, and not all 2027 dates/prices are verified.')
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'docs/tku-source-link-check-2026-10-08.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,lineterminator='\n',fieldnames=['source_id','official_url','http_status','open_status','applicable_year','checked_at','local_file','sha256','error'])
        writer.writeheader()
        for s in sources:writer.writerow(dict(source_id=s['id'],official_url=s['source_url'],**{k:s.get(k,'') for k in writer.fieldnames[2:]}))
    print(json.dumps(dict(tests=current,data_records=data['records'],new_failure_ids=report['new_failure_ids']),ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--junit',type=Path,required=True);p.add_argument('--baseline-junit',type=Path,required=True)
    p.add_argument('--browser',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
