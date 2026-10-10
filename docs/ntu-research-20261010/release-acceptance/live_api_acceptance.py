"""Single sequential read-only acceptance pass on the confirmed live release."""
import datetime, hashlib, json, time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'release-acceptance'
OUT.mkdir(exist_ok=True)
REPO=Path('/workspace/abroad-ntu-update-20261010')
BASE='https://uniway-1167.onrender.com'
report={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'expected_merge_sha':'59a20f27fcee00fb597abc79e75ec11778317422',
    'confirmed_render_deploy':'dep-db4qe3p5efls73a1jg7g','requests':[],'checks':{},'mode':'sequential_public_read_only_no_stress'}
session=requests.Session()
session.headers['User-Agent']='Uniway-release-verification/1.0 (sequential read-only acceptance)'
def save():
    (OUT/'live-api-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def get(path,params=None):
    started=time.monotonic()
    response=session.get(BASE+path,params=params,timeout=(12,90))
    report['requests'].append({'path':path,'params':params,'status':response.status_code,
        'elapsed_seconds':round(time.monotonic()-started,3),'body_bytes':len(response.content),
        'sha256':hashlib.sha256(response.content).hexdigest(),'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    save();print(path,params or '',response.status_code,report['requests'][-1]['elapsed_seconds'],flush=True)
    response.raise_for_status()
    value=response.json()
    time.sleep(1)
    return value
try:
    health=get('/health');assert health['status']=='ok' and len(health['supported_schools'])==6
    universities=get('/universities');assert [s['id'] for s in universities]==['cgu','ntpu','ntu','ccu','ncu','tku']
    report['checks']['six_universities']=universities
    dashboard=get('/student-dashboard',{'school':'NTU'})
    partners=dashboard['partner_universities']
    assert dashboard['school_name']=='國立臺灣大學' and len(partners)==288
    assert sum(p['quota'] is None for p in partners)==282
    assert sum(p['quota']=='0 名' for p in partners)==6
    local=[json.loads(x) for x in (REPO/'src/exchange_info/official_data/ntu/partners.jsonl').read_text().splitlines()]
    live={p['source_url'].rsplit('/',1)[-1]:p for p in partners}
    changes=json.loads((REPO/'sources/ntu/2026-10-10-official-changes.json').read_text())
    selected={s['portal_id'] for s in changes['schools']}
    for p in local:
        row=live[p['source_url'].rsplit('/',1)[-1]]
        for field in ['eligibility','application_info','degree_levels','quota','availability_status','source_url']:
            assert row[field]==p[field],(p['school_name'],field)
    report['checks']['all_288_partner_reference_fields_match_tested_bundle']=True
    report['checks']['changed_20_live_content_verified']=sorted(selected)
    report['checks']['quota_counts']={'blank':282,'zero':6,'confirmed_open':0}
    assert all(live[sn]['availability_status']=='agreement_only' for sn in selected)
    assert 'TOEFL iBT 4.0' in live['1200']['eligibility'] and 'TOEFL iBT 80' in live['1200']['eligibility']
    assert 'GPA 達3.30' in live['391']['eligibility'] and 'TOEFL iBT 4.5' in live['391']['eligibility']
    assert 'Winter semester: 1. October 2027' in live['1200']['application_info']
    assert '最終條件與甄選名額仍待確認' in live['1200']['application_info']
    assert 'March 2028' in live['1200']['application_info']
    home_period=dashboard['application_periods'][0]
    assert home_period['opens_at']=='2026-11-03T10:00:00+08:00' and home_period['deadline_at']=='2026-11-09T16:00:00+08:00'
    report['checks']['home_registration_timeline_preserved']=True
    workflow=get('/application-workflow',{'school':'明斯特大學','home_school':'國立臺灣大學','academic_year':'116'})
    assert workflow['review_status']=='pending_review' and workflow['published_at'] is None
    assert workflow['applicability_status']=='needs_confirmation'
    assert all(not s['deadline_reminder_eligible'] for s in workflow['steps'])
    report['checks']['reference_workflow_remains_unpublished_and_reminders_disabled']=True
    deadlines=get('/deadlines',{'school':'NTU'})
    assert '2027-03-05' not in str(deadlines) and '2027-03-06' not in str(deadlines)
    report['checks']['tsukuba_conflict_not_promoted_to_deadlines']=True
    destination=get('/destination-profile',{'school':'德勒斯登工業大學','home_school':'國立臺灣大學'})
    cost_normalized=' '.join(destination['cost_summary'].split())
    assert '900 EUR' in cost_normalized and '350 EUR' in cost_normalized
    assert '最終條件與甄選名額仍待確認' in destination['cost_summary']
    report['checks']['updated_cost_is_dated_reference']=True
    report['checks']['coverage_by_school']={}
    for school in universities:
        coverage=get('/coverage',{'school':school['school_name']})
        assert coverage['total_partner_schools']>0
        report['checks']['coverage_by_school'][school['id']]={k:coverage[k] for k in ['total_partner_schools','workflow_school_count','destination_profile_count']}
    report['status']='passed'
except Exception as error:
    report['status']='failed';report['failure_type']=type(error).__name__;report['failure']=str(error)
    save();raise
finally:
    report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
print(json.dumps(report['checks'],ensure_ascii=False),flush=True)
