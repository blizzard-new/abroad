from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates, templates_for_context
from exchange_info.models import ApplicationCenterContext
from exchange_info.ntpu_student_view import fetch_ntpu_partner_universities
from exchange_info.tku_data import BUNDLE, load_tku_records, load_tku_sources, tku_integrity_report
from exchange_info.tku_eligibility import assess_tku_eligibility
from exchange_info.tku_student_view import build_tku_student_dashboard, fetch_tku_partner_universities, load_tku_workflows
from exchange_info.university_registry import TKU, resolve_university
from exchange_info.workflow_structuring import workflow_structure_issues


def test_catalogue_preserves_current_round_reference_scope_and_native_years():
    current=load_tku_records();all_rows=load_tku_records(include_reference=True)
    assert len(current)==4 and len(all_rows)==128
    assert {r.academic_year for r in current}=={"2027-2028"}
    assert sum(r.quota_number for r in current)==7
    assert Counter(r.round_id for r in all_rows if r.selection_status=="reference_only")=={
        "english-european-115":89,"mainland-macau-kinmen-115":35}
    assert len({r.id for r in all_rows})==128
    assert all(r.fields["country"].value for r in all_rows)
    provisional=[r for r in all_rows if r.quota_status=="provisional"]
    assert len(provisional)==19
    assert all(r.quota_number is None and "TBC" in r.fields["quota"].value for r in provisional)
    assert not tku_integrity_report()["issues"]


def test_current_fields_have_year_role_date_and_official_evidence():
    sources={s["id"]:s for s in load_tku_sources()}
    for row in load_tku_records(include_reference=True):
        for fact in row.fields.values():
            assert fact.evidence
            if fact.status in {"missing_in_source","not_verified_new","not_applicable"}:assert fact.value is None
            for evidence in fact.evidence:
                source=sources[evidence.source_id]
                assert evidence.source_url==source["source_url"] and evidence.locator
                assert evidence.applicable_year and evidence.checked_at.date().isoformat()=="2026-10-08"
                assert source.get("http_status")==200
                if row.selection_status=="listed" and evidence.role=="home_outbound":
                    assert evidence.applicable_year=="2027-2028"


def test_dashboard_and_search_include_reviewed_nagasaki_evidence_without_expanding_mapping():
    from exchange_info.tku_student_view import tku_processed_pages
    dashboard = build_tku_student_dashboard()
    wording = " ".join(detail for item in dashboard.scholarship_info for detail in item.details)
    assert "正確交換頁及2027期限、住宿價目尚未核實" not in wording
    assert "NICS／研究生對應仍待確認" in wording
    assert "53,100" in wording and "21,000" in wording
    required = {"nagasaki-nics-2027", "nagasaki-partners", "nagasaki-form-a-online", "nagasaki-pledge"}
    sources = {row["id"]:row for row in load_tku_sources()}
    urls = {sources[id]["source_url"] for id in required}
    assert urls <= {source.source_url for source in dashboard.sources}
    pages = tku_processed_pages()
    assert urls <= {page.source_url for page in pages}
    naga = [page for page in pages if "nagasaki-gaigo.ac.jp" in page.source_url]
    assert all("本輪／研究生的對應尚未核實" in page.summary for page in naga)
    assert all(page.text and page.content_hash for page in pages)
    failed = {row["source_url"] for row in sources.values() if row.get("open_status") == "failed"}
    assert not failed.intersection(page.source_url for page in pages)
    audit_pages=[page for page in pages if 'rest_route=' in page.source_url]
    assert len(audit_pages)==3 and all('不是本期申請文件' in page.text for page in audit_pages)


def test_new_notice_audit_covers_all_official_archive_pages_without_claiming_unpublished():
    report=json.loads((BUNDLE/'current_notice_audit.json').read_text())
    archive=[row for row in report['evidence'] if 'entries' in row]
    entries=[entry for row in archive for entry in row['entries']]
    assert len(archive)==report['rest_pages']==3
    assert len(entries)==len({row['id'] for row in entries})==report['rest_total']==293
    assert not report['new_english_chinese_candidates']
    assert report['finding_status']=='not_verified_new'
    assert '不是官方明示尚未公告' in report['finding']
    assert len(report['conflicts_checked'])==13
    assert all(row['http_status']==200 and row['sha256'] and row['checked_at'].startswith('2026-10-08') for row in archive)
    assert any(row['http_status']==404 and 'OverseasStudents' in row['url'] for row in report['evidence'])


def test_document_template_api_honours_tku_year_and_round(tmp_path):
    client=TestClient(create_app(tmp_path))
    query={'school':'TKU','academic_year':'2027-2028','application_round':'日語組第二次甄選'}
    assert len(client.get('/application-center/templates',params=query).json())==2
    assert client.get('/application-center/templates',params={**query,'academic_year':'2028-2029'}).json()==[]
    assert client.get('/application-center/templates',params={**query,'application_round':'英歐語組'}).json()==[]


def test_document_catalog_scopes_four_mothers_even_for_same_japanese_partner(tmp_path, monkeypatch):
    from exchange_info.models import PartnerUniversity
    from exchange_info.ntu_student_view import fetch_ntu_partner_universities
    from exchange_info.storage import load_bundled_application_workflows
    from exchange_info.application_documents import build_application_document_catalog
    cgu=PartnerUniversity(program_type='交換學生',school_name='林肯大學 Lincoln University',country='紐西蘭',
        source_url='https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554')
    monkeypatch.setattr('exchange_info.api.fetch_partner_universities',lambda:[cgu])
    client=TestClient(create_app(tmp_path))
    ntu=fetch_ntu_partner_universities()
    cases=[('CGU','長庚大學',cgu,'116'),
        ('NTPU','國立臺北大學',fetch_ntpu_partner_universities()[0],'115'),
        ('NTU','國立臺灣大學',next(p for p in ntu if '立命館' in p.school_name),'116'),
        ('TKU','淡江大學',fetch_tku_partner_universities()[0],'2027-2028')]
    workflows=load_bundled_application_workflows()
    for alias,home,partner,year in cases:
        context=ApplicationCenterContext(school_name=home,target_school=partner.school_name,academic_year=year)
        expected=build_application_document_catalog(context,[w for w in workflows if w.home_university==home])
        response=client.get('/application-center/catalog',params={'school':alias,'target_school':partner.school_name,'academic_year':year})
        assert response.status_code==200,response.text
        actual=response.json()
        assert actual['context']['school_name']==home and actual['academic_year']==year
        assert actual['workflow_found'] and actual['items']
        assert actual['items']==expected.model_dump(mode='json')['items']
        # A future unsupported cycle never falls back to the previous school's/year's files.
        unknown=client.get('/application-center/catalog',params={'school':alias,'target_school':partner.school_name,'academic_year':'2099-2100'}).json()
        assert not unknown['workflow_found'] and unknown['items']==[]


def test_bundled_attachments_open_and_content_confirms_cycle():
    sources=load_tku_sources()
    for source in sources:
        if source.get("local_file"):
            blob=(BUNDLE/source["local_file"]).read_bytes()
            assert hashlib.sha256(blob).hexdigest()==source["sha256"]
            assert blob.startswith((b"%PDF",b"PK"))
    jp=next(s for s in sources if s["id"]=="jp-revision-attachment-1")
    assert "2027-2028" in jp["pages"][0]["text"]
    assert "2026 年 9 月 23 日" in jp["pages"][2]["text"]
    assert "9月17日" in jp["pages"][5]["text"] # Preserve conflict, do not silently fix original.
    english=next(s for s in sources if s["id"]=="english-115-partners")
    assert all("2026-2027" in sheet["rows"][0]["A1"] for sheet in english["sheets"])
    assert any(s.get("open_status")=="failed" and "404" in s["error"] for s in sources)


def test_revision_wins_and_expired_internal_round_never_looks_open():
    before=datetime(2026,9,22,tzinfo=timezone.utc)
    active=datetime(2026,9,24,tzinfo=timezone.utc)
    after=datetime(2026,9,30,4,1,tzinfo=timezone.utc)
    assert {r.availability_status for r in fetch_tku_partner_universities(reference_time=before)}=={"quota_unconfirmed"}
    assert {r.availability_status for r in fetch_tku_partner_universities(reference_time=active)}=={"open"}
    assert {r.availability_status for r in fetch_tku_partner_universities(reference_time=after)}=={"closed"}
    periods=build_tku_student_dashboard(reference_time=after).application_periods
    assert periods[0].deadline_at.isoformat()=="2026-09-30T12:00:00+08:00"
    assert periods[0].status=="closed" and periods[0].reminder_eligible is False
    assert all(p.status=="reference_only" and p.deadline_at is None for p in periods[1:])


def test_specific_programme_rules_and_conflicting_rank_alternative():
    jp="jp-2027-2028-round-2"
    assert assess_tku_eligibility(round_id=jp,academic_average=70,department_top_percent=50)["academic_status"]=="fail"
    assert assess_tku_eligibility(round_id=jp,academic_average=74,department_top_percent=30)["academic_status"]=="needs_confirmation"
    assert assess_tku_eligibility(round_id="english-european-115",academic_average=74,department_top_percent=30)["academic_status"]=="pass"
    assert assess_tku_eligibility(round_id="mainland-macau-kinmen-115",academic_average=74,department_top_percent=30)["academic_status"]=="pass"
    assert assess_tku_eligibility(round_id="english-european-116",academic_average=99)["application_status"]=="not_verified_new"
    common=dict(round_id=jp,academic_average=85,year_of_study=3,degree_level="大學部")
    assert assess_tku_eligibility(**common,jlpt_level="N3")["home_status"]=="fail"
    assert assess_tku_eligibility(**common,jlpt_level="N1")["home_status"]=="pass"
    assert assess_tku_eligibility(**common,jlpt_level="N2",partner_id=jp+"-ritsumeikan")["home_status"]=="fail"
    assert assess_tku_eligibility(**common,partner_id=jp+"-uec")["home_status"]=="needs_confirmation"


def test_incoming_rules_do_not_replace_home_language_and_corrected_url_keeps_conflict():
    rows={r.id.rsplit("-",1)[-1]:r for r in load_tku_records()}
    assert 'nagasaki-gaigo.ac.jp' in rows["nagasaki"].fields["website"].value
    assert rows['nagasaki'].fields['host_programme_mapping'].status=='needs_confirmation'
    assert "nagasaki-wrong-url" in rows["nagasaki"].conflicts
    assert rows["uec"].fields["degree_levels"].status=="missing_in_source"
    assert rows["uec"].fields["department_scope"].value.endswith("學生優先")
    seikei=rows["seikei"]
    assert "2027/9" in seikei.fields["costs"].value and "120,000" in seikei.fields["costs"].value
    assert "2027" in seikei.fields["host_deadline"].value
    assert seikei.fields["host_deadline"].evidence[0].role=="host_incoming"


def test_offline_api_registry_documents_search_and_life_profile(tmp_path,monkeypatch):
    def reject_network(*args,**kwargs):raise AssertionError("TKU catalogue must work offline")
    monkeypatch.setattr("requests.get",reject_network)
    for alias in ["淡江大學","淡江","淡大","TKU","Tamkang University"]:assert resolve_university(alias)==TKU
    client=TestClient(create_app(tmp_path))
    supported=client.get("/universities").json()
    tku=next(u for u in supported if u["id"]=="tku")
    assert tku["partner_count"]==4 and tku["support_level"]=="basic"
    response=client.get("/student-dashboard",params={"school":"TKU"})
    assert response.status_code==200,response.text
    dashboard=response.json()
    assert dashboard["school_name"]=="淡江大學" and len(dashboard["partner_universities"])==4
    assert all(p["availability_status"]=="closed" for p in dashboard["partner_universities"])
    assert "JST" in dashboard["partner_universities"][0]["application_deadline"]
    assert "9/30" in dashboard["partner_universities"][0]["availability_note"]
    for partner in dashboard['partner_universities']:
        summary=partner['student_summary_zh']
        assert summary['eligibility_points'] and summary['application_steps'] and summary['tuition_points']
        assert 'JLPT N2' in ' '.join(summary['eligibility_points']) and '研究所N1' in ' '.join(summary['eligibility_points'])
        assert '全額學雜費' in ' '.join(summary['tuition_points'])
        assert '已截止' in ' '.join(summary['application_steps'])
    assert "系前40%" in dashboard["academic_score_rule"]
    assert "長庚" not in json.dumps(dashboard,ensure_ascii=False)
    results=client.get("/search",params={"school":"TKU","q":"日語"}).json()
    assert results and all("ntpu.edu.tw" not in r.get("source_url","") for r in results)
    name=load_tku_records()[0].fields["school_name"].value
    profile=client.get("/destination-profile",params={"school":name,"home_school":"TKU"})
    assert profile.status_code==200 and "50,000" in profile.json()["cost_summary"]
    workflow=client.get("/application-workflow",params={"school":name,"home_school":"TKU",
        "academic_year":"2027-2028","application_round":"日語組第二次甄選"})
    assert workflow.status_code==200 and len(workflow.json()["steps"])==6
    catalog=client.get("/application-center/catalog",params={"school":"TKU","target_school":name,
        "academic_year":"2027-2028","application_round":"日語組第二次甄選"})
    assert catalog.status_code==200 and catalog.json()["workflow_found"] is True
    assert Counter(i['phase'] for i in catalog.json()['items'])=={'校內申請':8,'外校申請':9,'行前':6}
    assert all(i["needs_confirmation"] and not i["download_available"] for i in catalog.json()["items"])


def test_documents_and_workflows_do_not_invent_official_layout_or_new_year():
    templates=all_application_templates("TKU")
    assert len(templates)==2 and all(not t.official_layout for t in templates)
    assert "長庚" not in "".join(t.model_dump_json() for t in templates)
    assert templates_for_context(ApplicationCenterContext(school_name="淡江大學",academic_year="2028-2029"))==[]
    workflows=load_tku_workflows()
    assert len(workflows)==4 and all(not workflow_structure_issues(w) for w in workflows)
    assert all(w.review_status=="legacy" and w.published_at is None for w in workflows)
    assert all(not s.deadline_reminder_eligible for w in workflows for s in w.steps)
    assert all(w.academic_year=="2027-2028" for w in workflows)


def test_host_documents_preserve_conditions_versions_and_submission_phase(tmp_path):
    catalog=json.loads((BUNDLE/'host_documents.json').read_text())
    assert len(catalog)==4
    expected={'ritsumeikan':(9,6),'nagasaki':(11,0),'seikei':(10,0),'uec':(15,2)}
    client=TestClient(create_app(tmp_path))
    workflows={w.school_name:w for w in load_tku_workflows()}
    for row in catalog:
        slug=row['partner_id'].rsplit('-',1)[-1];wf=workflows[row['school_name']]
        assert len(wf.steps[1].document_requirements)==8
        assert all('Form A' not in d.name and 'COE' not in d.name for d in wf.steps[1].document_requirements)
        assert (len(wf.steps[3].document_requirements),len(wf.steps[4].document_requirements))==expected[slug]
        response=client.get('/application-center/catalog',params=dict(school='TKU',target_school=row['school_name'],academic_year='2027-2028',application_round='日語組第二次甄選'))
        assert response.status_code==200
        items=response.json()['items']
        assert sum(d['phase']=='校內申請' for d in items)==8
        assert sum(d['phase']=='外校申請' for d in items)==expected[slug][0]
        assert all(d['source_urls'] and d['source_checked_at'] for d in items)
        for doc in row['documents']:
            assert doc['condition'] and doc['evidence']['locator'] and doc['applicable_year']
            if slug=='uec':assert doc['status']=='reference_only' and '2027' in doc['applicable_year']
    seikei=next(r for r in catalog if r['partner_id'].endswith('seikei'))
    conditional=next(d for d in seikei['documents'] if d['key']=='financial-statement')
    assert conditional['condition']=='僅獎學金申請人'
    assert any(d['key']=='coe' and '財力' in d['name'] for d in seikei['documents'])
    rit=next(r for r in catalog if r['partner_id'].endswith('ritsumeikan'))
    assert next(d for d in rit['documents'] if d['key']=='health')['phase']=='行前'
    uec=next(r for r in catalog if r['partner_id'].endswith('uec'))
    assert next(d for d in uec['documents'] if d['key']=='funding')['phase']=='行前'
    assert '不套所有臺灣' in next(d for d in uec['documents'] if d['key']=='tb')['condition']
    assert '大學部' in next(d for d in uec['documents'] if d['key']=='research-ug')['condition']
    assert '研究所' in next(d for d in uec['documents'] if d['key']=='research-grad')['condition']
    health=next(d for d in uec['documents'] if d['key']=='health')
    assert health['signatures']==['申請人','母校國際處／授權人'] and '醫師' not in health['name']


def test_nagasaki_current_body_and_uec_scholarship_opportunity_are_preserved():
    rows={r.id.rsplit('-',1)[-1]:r for r in load_tku_records()}
    naga=rows['nagasaki']
    assert '2026/10/31消印有效' in naga.fields['host_deadline'].value
    assert '2026-09-30' in naga.fields['home_deadline'].value
    assert '50,000' in naga.fields['costs'].value and '53,100' in naga.fields['costs'].value
    assert '270,000' in naga.fields['costs'].value and '不套用' in naga.fields['costs'].value
    assert {'nagasaki-photo-count','nagasaki-essay-translation','nagasaki-study-period','nagasaki-programme-mapping'}.issubset(naga.conflicts)
    sources={r['id']:r for r in load_tku_sources()}
    assert 'Spring 2027' in sources['nagasaki-pledge']['pages'][0]['text']
    assert '2027' in sources['nagasaki-form-a-online']['text'][:300]
    assert '淡江大学' in sources['nagasaki-partners']['text']
    assert '2009' in sources['uec-private-insurance']['applicable_year']
    scholarship=rows['uec'].fields['scholarships']
    assert scholarship.status=='verified' and scholarship.evidence[0].role=='home_outbound'
    assert scholarship.evidence[0].applicable_year=='2027-2028'
    assert '有機會' in scholarship.value and '不是保證' in scholarship.value


def test_completeness_is_per_school_field_and_general_pages_are_partial(tmp_path):
    matrix=json.loads((BUNDLE/'completeness_matrix.json').read_text())
    assert len(matrix['schools'])==128
    assert len({r['id'] for r in matrix['schools']})==128
    assert all(len(r['fields'])==38 for r in matrix['schools'])
    assert all(c['reason'] and c['evidence'] and c['checked_entries'] for r in matrix['schools'] for c in r['fields'])
    assert all(c['value'] is None for r in matrix['schools'] for c in r['fields'] if c['status'] in {'not_verified_new','missing_in_source','not_applicable'})
    client=TestClient(create_app(tmp_path))
    for row in load_tku_records():
        name=row.fields['school_name'].value
        response=client.get('/school-data-completeness',params=dict(school=name,home_school='TKU'))
        assert response.status_code==200
        report=response.json();items={i['key']:i for i in report['items']}
        assert len(items)==38 and items['home_deadline']['status']=='available'
        assert items['housing_application_deadline']['status'] in {'missing','needs_confirmation'}
        assert items['arrival_date']['status'] in {'missing','needs_confirmation'}
        assert items['course_schedule_2027']['status']=='needs_confirmation'
        assert '2026-10-08' in items['latest_forms']['note']
        if row.id.endswith('uec'):
            assert items['host_documents']['status']=='partial' and items['housing_costs']['status']=='partial'
            assert items['scholarships']['status']=='available'
        profile=client.get('/destination-profile',params=dict(school=name,home_school='TKU')).json()
        assert len(profile['student_guide_sections'])==14
        assert all(s['source_urls'] and '2026-10-08' in s['points'][0] for s in profile['student_guide_sections'])
        assert profile['coverage_status']=='official_partial'
        assert any(s['caution'] for s in profile['student_guide_sections'])


def test_existing_cgu_and_ntpu_scope_counts_unchanged():
    from exchange_info import storage
    from exchange_info.student_view import fetch_partner_universities
    ntpu=fetch_ntpu_partner_universities()
    assert len(ntpu)==206 and Counter(p.availability_status for p in ntpu)=={"open":169,"agreement_only":37}
    # The official CGU sheet is bundled; this check uses it without live requests.
    workflows=storage.load_bundled_application_workflows()
    cgu=[w for w in workflows if w.home_university=="長庚大學"]
    assert Counter(w.academic_year for w in cgu)=={"115":77,"116":77}
    current=[w for w in cgu if w.academic_year=="116"]
    assert len({w.school_name for w in current})==77
    assert sum("參考" in w.program_type for w in current)==2


def test_expired_tku_choice_cannot_be_added_as_an_available_personal_plan():
    from exchange_info.application_rules import build_personal_application_plan
    from exchange_info.models import PersonalApplicationPlanRequest
    partners=fetch_tku_partner_universities(reference_time=datetime(2026,10,8,tzinfo=timezone.utc))
    request=PersonalApplicationPlanRequest(home_school="淡江大學",academic_score=99,
        degree_level="大學部",academic_year="2027-2028",application_round="日語組第二次甄選",
        preferences=[{"rank":1,"school_name":partners[0].school_name}])
    plan=build_personal_application_plan(request,partners,load_tku_workflows(),academic_score_minimum=75)
    assert plan.choices[0].status=="unavailable"
    assert any(c.code=="availability" and c.status=="fail" for c in plan.choices[0].checks)


def test_build_is_reproducible_without_network():
    names=["partners_current.jsonl","partners_reference.jsonl","rounds.json","conflicts.json","application_workflows.jsonl","destination_profiles.jsonl","integrity.json","host_documents.json","completeness_matrix.json"]
    before={name:(BUNDLE/name).read_bytes() for name in names}
    script=BUNDLE.parents[3]/"scripts"/"build_tku_catalog.py"
    subprocess.run([sys.executable,str(script)],cwd=script.parents[1],check=True,capture_output=True)
    assert {name:(BUNDLE/name).read_bytes() for name in names}==before


def test_xlsx_parser_preserves_country_merges_and_quota_unknown_states():
    import importlib.util
    scripts=BUNDLE.parents[3]/"scripts"
    spec=importlib.util.spec_from_file_location("tku_refresh",scripts/"refresh_tku_sources.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source=next(s for s in load_tku_sources() if s["id"]=="english-115-partners")
    assert module.xlsx_sheets((BUNDLE/source["local_file"]).read_bytes())==source["sheets"]
    spec=importlib.util.spec_from_file_location("tku_build",scripts/"build_tku_catalog.py")
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    assert builder.quota_state(None)==("blank",None)
    assert builder.quota_state("0")==("zero",0)
    assert builder.quota_state("2 (TBC)")==("provisional",None)
    assert builder.quota_state("2")==("numeric",2)


def test_frontend_marks_closed_and_reference_choices_unavailable():
    script=(BUNDLE.parents[1]/"static"/"app.js").read_text(encoding="utf-8")
    function=script.split("function partnerAvailabilityMeta(item) {",1)[1].split("function renderPartnerAvailabilityNotice",1)[0]
    javascript="function partnerAvailabilityMeta(item) {"+function+"""
    for (const status of ['closed', 'reference_only', 'quota_unconfirmed']) {
      const result = partnerAvailabilityMeta({availability_status: status});
      if (!result.blocked || result.status !== status) throw new Error(status);
    }
    if (partnerAvailabilityMeta({availability_status: 'open'}).blocked) throw new Error('open');
    """
    subprocess.run(["node","-e",javascript],check=True,capture_output=True,timeout=10)
    deadline=script.split("function partnerDeadlineReference(item) {",1)[1].split("function partnerSummaryPoints",1)[0]
    code="const activeUniversityProfile = () => ({id:'tku'}); const partnerStudentSummary = () => ({});\nfunction partnerDeadlineReference(item) {"+deadline+"""
    const result = partnerDeadlineReference({application_deadline: '2027春季：2026/11/2 09:00 JST'});
    if (!result.label.includes('外校') || !result.value.includes('JST') || result.value.includes('適用年度待確認')) throw new Error('host deadline');
    """
    subprocess.run(["node","-e",code],check=True,capture_output=True,timeout=10)
