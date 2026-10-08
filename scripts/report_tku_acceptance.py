"""Derive final acceptance evidence from one guarded candidate run and main baseline."""
import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from exchange_info.content_governance import workflow_content_hash
from exchange_info.storage import load_bundled_application_workflows

ROOT=Path(__file__).resolve().parents[1]


def junit(path):
    cases=[]
    for case in ET.parse(path).getroot().iter('testcase'):
        state='passed'; reason=''
        for tag in ['error','failure','skipped']:
            child=case.find(tag)
            if child is not None:
                state=tag; reason=child.get('message','')
                break
        cases.append(dict(id=case.get('classname','')+'::'+case.get('name',''),status=state,reason=reason))
    return dict(counts=dict(Counter(c['status'] for c in cases)),cases=cases)


def report(args):
    out=args.output.resolve()
    run=json.loads((out/'run.json').read_text())
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if run['tested_commit']!=head or run['ending_commit']!=head or run['ending_worktree_status'] or not run['all_checks_executed']:
        raise RuntimeError('Candidate run was incomplete or changed; cannot issue acceptance evidence')
    current=junit(out/'suite.xml'); baseline=junit(args.baseline_suite)
    failed=lambda data:{c['id'] for c in data['cases'] if c['status'] in ['failure','error']}
    rows=[w for w in load_bundled_application_workflows() if w.home_university!='淡江大學']
    old=json.loads(args.baseline_hashes.read_text())
    hashes={'|'.join([w.home_university,w.school_name,w.program_type,w.academic_year,w.application_round or '']):workflow_content_hash(w) for w in rows}
    drift=sorted(key for key in set(old)|set(hashes) if old.get(key)!=hashes.get(key))
    browser=[json.loads(path.read_text()) for path in sorted((out/'browser').glob('*.json'))]
    switch=json.loads((out/'switch.json').read_text())
    if len(browser)!=12 or any(r['tested_commit']!=head or r['status']!='passed' for r in browser) or switch['tested_commit']!=head:
        raise RuntimeError('Browser evidence does not belong to this complete candidate')
    result=dict(tested_commit=head,baseline_commit=args.baseline_commit,runner_exit_code=run['runner_exit_code'],
        all_checks_passed=run['all_checks_passed'],candidate_invariant_passed=True,
        candidate_counts=current['counts'],baseline_counts=baseline['counts'],
        added_failures=sorted(failed(current)-failed(baseline)),resolved_failures=sorted(failed(baseline)-failed(current)),
        failures=[c for c in current['cases'] if c['status'] in ['failure','error']],
        skipped=[c for c in current['cases'] if c['status']=='skipped'],
        inherited_wrapper=junit(out/'wrapper.xml'),checks=run['checks'],
        school_hash_preservation=dict(count=len(old),candidate_count=len(hashes),differences=drift,counts=dict(Counter(w.home_university for w in rows))),
        tku_unit_runner_counts=dict(Counter(c['status'] for c in current['cases'] if c['id'].startswith(('tests.test_tku_support::','tests.test_tku_acceptance_runner::')))),
        relevant_browser_counts=dict(Counter(c['status'] for c in current['cases'] if c['id'].startswith('tests.e2e.'))),
        tku_browser=browser,switch=switch,not_run=run['deliberately_not_run']+
            ['E2E files outside the seven selected suites and the specified CGU PDF node; not counted as passed'],
        data_scope=dict(records=128,current_round=4,reference_rows=124,current_quota=7,open_new_applications=0,
            matrix_fields=152,verified=85,verified_percent=55.9,unresolved_source_conflicts=13,
            host_documents=53,official_exchange_attachments=28,registration_colleges=9,registration_units=44),
        human_acceptance='Limited TKU UI/data review can start if no added failures/hash drift; full current-year application readiness remains blocked by missing official data and inherited/CI failures.')
    (out/'acceptance-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['tested_commit','runner_exit_code','candidate_counts','baseline_counts','added_failures','school_hash_preservation','tku_unit_runner_counts','relevant_browser_counts']},ensure_ascii=False))
    return 1 if drift or result['added_failures'] else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--baseline-suite',required=True,type=Path)
    parser.add_argument('--baseline-hashes',required=True,type=Path)
    parser.add_argument('--baseline-commit',required=True)
    raise SystemExit(report(parser.parse_args()))
