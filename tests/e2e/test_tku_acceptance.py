"""Real TKU acceptance flows using bundled evidence and isolated local accounts."""
import json
import re
import os
import subprocess
import shutil
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation, open_partner_filters
from .test_open_catalog import attach_session, sign_in_cookie, wait_until
from .test_web_next_phase import _wait_for_workspace

HOME = "淡江大學"
OUTPUT = Path(os.environ.get("TKU_ACCEPTANCE_OUTPUT", "/tmp/tku-acceptance/browser"))
ROOT = Path(__file__).resolve().parents[2]
TESTED_COMMIT = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def start(page, live_server, width, route, verified=False):
    page.set_viewport_size({"width":width, "height":900})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    session = sign_in_cookie(live_server, school=HOME)
    if verified:
        live_server.verify_student(session["profile"]["id"], university=HOME)
    attach_session(page, live_server, session)
    enter_public_site(page, live_server, route)
    wait_until(page, "state.dashboard?.school_name === '淡江大學' && !state.homeSchoolLoading && !state.applicationLoading")
    return session, errors


def record(page, name, width, errors, **facts):
    assert not errors, errors
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=30000)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUTPUT / f"{name}-{width}.png"))
    (OUTPUT / f"{name}-{width}.json").write_text(json.dumps(dict(status="passed", viewport=width,
        tested_commit=TESTED_COMMIT, scenario=name, page_errors=errors, **facts), ensure_ascii=False, indent=2) + "\n")


@pytest.mark.parametrize('width', [390,1280])
def test_tku_jlpt_comparison_persistence_and_closed_cycle(page, live_server, width):
    session, errors = start(page, live_server, width, 'advisor')
    expect(page.locator('#advisor-jlpt-level')).to_be_visible()
    page.locator('#advisor-college').select_option('工學院')
    page.locator('#advisor-department').select_option('資訊工程學系')
    page.locator('#advisor-degree').select_option('大學部')
    page.locator('#advisor-academic-score').fill('85')
    page.locator('#advisor-jlpt-level').select_option('N2')
    result = page.locator('#tku-eligibility-result')
    expect(result).to_have_attribute('data-language-status', 'pass')
    page.locator('#tku-eligibility-partner').select_option('ritsumeikan')
    expect(result).to_have_attribute('data-language-status', 'fail')
    page.locator('#advisor-jlpt-level').select_option('N1')
    expect(result).to_have_attribute('data-language-status', 'pass')
    page.locator('#tku-eligibility-partner').select_option('uec')
    expect(result).to_have_attribute('data-language-status', 'needs_confirmation')
    expect(result).to_have_attribute('data-application-status', 'closed')
    with page.expect_response(lambda r:r.url.endswith('/advisor/plan') and r.request.method=='POST') as response:
        page.locator('#advisor-submit').click()
    assert response.value.request.post_data_json['jlpt_level'] == 'N1'
    assert response.value.json()['recommendations'] == []
    saved = _wait_for_workspace(live_server, session, lambda r:
        (r['workspace'].get('selection_conditions',{}).get('profile') or {}).get('jlpt_level') == 'N1', home_school=HOME)
    assert saved['workspace']['selection_conditions']['profile']['language_score'] is None
    page.reload()
    expect(page.locator('#advisor-jlpt-level')).to_have_value('N1')
    assert page.evaluate('state.eligibilityProfile.jlptLevel') == 'N1'
    record(page, 'jlpt-home-check-and-persistence', width, errors, saved_jlpt='N1',
        n1_stronger_than_n2=True, uec_requires_confirmation=True, open_recommendations=0, reload_preserved=True)


@pytest.mark.parametrize("width", [390,1280])
def test_tku_shared_home_query_follows_explicit_school_choice_and_navigation(page, live_server, width):
    _, errors = start(page, live_server, width, "application-center")
    assert page.evaluate("new URL(location.href).searchParams.get('home')") == HOME

    def choose(home):
        open_navigation(page)
        page.locator('#school-switcher').click()
        page.locator(f'#school-options [data-home-school={json.dumps(home,ensure_ascii=False)}]').click()
        wait_until(page, f"state.dashboard?.school_name === {json.dumps(home,ensure_ascii=False)} && !state.homeSchoolLoading && !state.applicationLoading")
        assert page.evaluate("new URL(location.href).searchParams.get('home')") == home

    choose('國立臺北大學')
    page.evaluate("location.hash='#overview'")
    wait_until(page, "state.dashboard?.school_name === '國立臺北大學' && !state.homeSchoolLoading")
    expect(page.locator('#application-workspace-context')).to_contain_text('國立臺北大學')
    assert page.evaluate("activeHomeSchool()") == '國立臺北大學'
    page.reload()
    wait_until(page, "state.dashboard?.school_name === '國立臺北大學' && !state.homeSchoolLoading")
    assert page.evaluate("activeHomeSchool()") == '國立臺北大學'
    choose(HOME)
    page.evaluate("location.hash='#application-center'")
    expect(page.locator('#application-context-form')).to_be_visible()
    year=page.locator('#application-context-form input[name="academic_year"]')
    year.fill('2027-2028');year.press('Tab')
    wait_until(page, '!state.applicationLoading')
    target=page.evaluate('state.dashboard.partner_universities[0].school_name')
    page.locator('#application-target-school').select_option(target)
    wait_until(page, "state.applicationDocumentCatalog?.context.school_name === '淡江大學' && !state.applicationLoading")
    assert page.evaluate("state.applicationDocumentCatalog.academic_year") == '2027-2028'
    assert page.evaluate("activeHomeSchool()") == HOME
    record(page, 'shared-home-query-navigation', width, errors,
        query_follows_explicit_choice=True, navigation_preserves_choice=True,
        reload_preserved=True, returned_to_tku=True, tku_document_context_preserved=True)


@pytest.mark.parametrize("width", [390,1280])
def test_tku_list_filters_favorites_comparison_and_reload(page, live_server, width):
    session, errors = start(page, live_server, width, "partners")
    page.locator('[data-partner-view="list"]').click()
    table = page.locator("#partner-table")
    expect(table).to_have_attribute("data-result-count", "287")
    assert page.evaluate("state.dashboard.partner_universities.slice(0,4).every(row=>row.availability_status==='closed') && state.dashboard.partner_universities.slice(4).every(row=>['reference_only','agreement_only'].includes(row.availability_status)&&row.quota===null)")
    open_partner_filters(page)
    page.locator("#availability-filter").select_option("open")
    expect(table).to_have_attribute("data-result-count", "0")
    page.locator("#availability-filter").select_option("closed")
    page.locator("#country-filter").select_option("日本")
    page.locator("#region-filter").select_option("east-asia")
    expect(table).to_have_attribute("data-result-count", "4")
    page.locator("#partner-search").fill("Nagasaki")
    expect(table).to_have_attribute("data-result-count", "1")
    page.locator("#partner-search").fill("")
    expect(table).to_have_attribute("data-result-count", "4")
    names = page.evaluate("state.dashboard.partner_universities.map(row=>row.school_name)")
    for name in names[:2]:
        # The heart sits on the card photo at every width, so the card needs no opening first.
        page.locator(f'#partner-table .favorite-toggle:visible[data-school-name={json.dumps(name,ensure_ascii=False)}]').click()
    page.evaluate("location.hash='#favorites'")
    expect(page.locator("#favorite-count")).to_have_text("2 所")
    expect(page.locator("#selection-workspace .discovery-candidate")).to_have_count(2)
    checkboxes = page.locator("#selection-workspace [data-compare-school]")
    for index in range(checkboxes.count()):
        checkboxes.nth(index).check()
    expect(page.locator("#discovery-comparison")).to_contain_text(names[0])
    expect(page.locator("#discovery-comparison")).to_contain_text(names[1])
    expect(page.locator("#discovery-comparison")).to_contain_text("名額")
    saved = _wait_for_workspace(live_server, session, lambda row:
        len(row["workspace"].get("favorite_schools",[])) == 2, home_school=HOME)
    assert set(saved["workspace"]["favorite_schools"]) == set(names[:2])
    page.reload()
    expect(page.locator("#favorite-count")).to_have_text("2 所")
    expect(page.locator("#selection-workspace .discovery-candidate")).to_have_count(2)
    record(page, "filters-favorites-comparison", width, errors, listed=287, current_round=4, open=0,
        saved_favorites=names[:2], reload_preserved=True)


@pytest.mark.parametrize("width", [390,1280])
def test_tku_conditions_directory_native_years_and_no_false_open_plan(page, live_server, width):
    session, errors = start(page, live_server, width, "advisor")
    expect(page.locator("#advisor-college option")).to_have_count(10)
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department").select_option("資訊工程學系")
    page.locator("#advisor-degree").select_option("大學部")
    page.locator("#advisor-academic-score").fill("85")
    expect(page.locator("#advisor-department-source")).to_have_attribute("href", "https://www.tku.edu.tw/acad.asp")
    with page.expect_response(lambda r:r.url.endswith("/advisor/plan") and r.request.method=="POST") as result:
        page.locator("#advisor-submit").click()
    assert result.value.ok and result.value.json()["recommendations"] == []
    assert result.value.request.post_data_json["college"] == "工學院"
    assert result.value.request.post_data_json["department"] == "資訊工程學系"
    saved = _wait_for_workspace(live_server, session, lambda row:
        (row["workspace"].get("selection_conditions",{}).get("profile") or {}).get("college") == "工學院", home_school=HOME)
    assert saved["workspace"]["selection_conditions"]["profile"]["academic_score"] == 85
    page.locator('#application-workspace-tools a[href="#eligibility"]').click()
    options = page.locator("#eligibility-academic-year option").evaluate_all("rows=>rows.map(row=>row.value).filter(Boolean)")
    assert "2027-2028" in options and not any(re.fullmatch(r"11\d", year) for year in options)
    page.locator("#eligibility-academic-year").select_option("2027-2028")
    rounds=page.locator("#eligibility-application-round option").evaluate_all("rows=>rows.map(row=>row.value).filter(Boolean)")
    assert "日語組第二次甄選" in rounds and "第一梯次" not in rounds and "其他／尚未公告" not in rounds
    expect(page.locator("#eligibility-preference-1 option")).to_have_count(1)
    page.reload()
    expect(page.locator("#advisor-college")).to_have_value("工學院")
    expect(page.locator("#advisor-department")).to_have_value("資訊工程學系")
    expect(page.locator("#advisor-academic-score")).to_have_value("85")
    record(page, "conditions-native-years", width, errors, colleges=9, department="資訊工程學系",
        years=options, closed_schools_not_formal_preferences=True, conditions_reload_preserved=True)


@pytest.mark.parametrize("width", [390,1280])
def test_tku_documents_stages_conditions_official_sources_and_target_persistence(page, live_server, width):
    session, errors = start(page, live_server, width, "application-center", verified=True)
    year = page.locator('#application-context-form input[name="academic_year"]')
    year.fill("2027-2028"); year.press("Tab")
    wait_until(page, "!state.applicationLoading")
    names = page.evaluate("state.dashboard.partner_universities.slice(0,4).map(row=>row.school_name)")
    for name in names:
        previous = page.evaluate("state.applicationContext.target_school")
        page.locator("#application-target-school").select_option(name)
        if previous and previous != name:
            page.locator('#planning-target-change-dialog button[value="confirm"]').click()
        wait_until(page, f"state.applicationDocumentCatalog?.context.target_school === {json.dumps(name,ensure_ascii=False)} && !state.applicationLoading")
        page.locator("#application-requirement-list details").evaluate_all("rows=>rows.forEach(row=>row.open=true)")
        assert name in page.locator("#application-requirement-summary").inner_text()
        catalog = page.evaluate("state.applicationDocumentCatalog")
        assert catalog["academic_year"] == "2027-2028"
        assert len(catalog["items"]) == (23 if "Ritsumeikan" in name else 19 if "Nagasaki" in name else 18 if "Seikei" in name else 25)
        assert all(url.startswith("https://") for row in catalog["items"] for url in row["source_urls"])
        if "Seikei" in name:
            expect(page.locator("#application-requirement-list")).to_contain_text("僅獎學金申請人")
        if "Electro" in name:
            expect(page.locator("#application-requirement-list")).to_contain_text("一般參考／2027版未核實")
        assert any(row["conditional"] and row["condition"] for row in catalog["items"])
        expect(page.locator("#application-requirement-list")).to_contain_text("符合條件才需要")
        host_items = [row for row in catalog["items"] if row["phase"] in ("外校申請", "行前")]
        for row in host_items:
            expected_stage="after_application" if "Ritsumeikan" in name and "COE網路表" in row["name"] else "student_application" if row["phase"]=="外校申請" else "post_offer"
            assert row["stage"]==expected_stage
        if "Ritsumeikan" in name:
            coe=next(row for row in host_items if "COE網路表" in row["name"])
            assert coe['stage']=='after_application'
            assert '11月上旬至12月上旬' in coe['applicability_note'] and '早於12月下旬錄取結果' in coe['applicability_note']
            card=page.locator('.application-requirement-item').filter(has_text='COE網路表')
            expect(card).to_contain_text('階段：外校申請後')
            expect(card).to_contain_text('行政書士另通知')
            assert '階段：錄取後' not in card.inner_text()
            workflow=page.request.get(live_server.base_url+'/application-workflow',params={'school':name,'home_school':HOME,'academic_year':'2027-2028'}).json()
            requirements=[r for step in workflow['steps'] for r in step['document_requirements'] if 'COE網路表' in r['name']]
            assert len(requirements)==1 and requirements[0]['stage']=='after_application'
            assert any('11月上旬至12月上旬' in detail for step in workflow['steps'] for detail in step['details'])
        assert all(row["applicability_year"] and row["applicability_note"] for row in host_items)
        links = page.locator("#application-requirement-list .application-requirement-source a")
        expected = [row["official_form_url"] if row["download_available"] else row["source_urls"][0] for row in catalog["items"]]
        assert links.evaluate_all("rows=>rows.map(row=>row.getAttribute('href'))") == expected
        if "Nagasaki" in name:
            expect(page.locator("#application-requirement-list")).to_contain_text("長崎NICS與淡江本輪／研究生對應仍待確認")
            assert any(row["official_form_verified"] and row["download_available"] for row in host_items)
        if "Electro" in name:
            assert all(row["applicability_status"] == "reference_only" for row in host_items)
            expect(page.locator("#application-requirement-list")).to_contain_text("開啟官方一般參考表格")
    saved = _wait_for_workspace(live_server, session, lambda row:
        row["workspace"].get("application_context",{}).get("target_school") == names[-1], home_school=HOME)
    assert saved["workspace"]["application_context"]["academic_year"] == "2027-2028"
    assert not saved["workspace"].get("deadline_events")
    page.evaluate("location.hash='#overview'")
    expect(page.locator("#planning-target-summary")).to_contain_text(names[-1])
    expect(page.locator("#planning-preview-button")).to_be_disabled()
    page.reload()
    expect(page.locator("#planning-target-summary")).to_contain_text(names[-1])
    expect(page.locator("#planning-preview-button")).to_be_disabled()
    page.evaluate("location.hash='#application-center'")
    expect(page.locator("#application-target-school")).to_have_value(names[-1])
    wait_until(page, "!state.applicationLoading")
    expect(page.locator("#application-requirement-list")).to_contain_text("一般參考／2027版未核實")
    record(page, "conditional-catalog-persistence", width, errors, schools_checked=names,
        nominated_host_scope_preserved=True, exact_deadline_events=0, reload_preserved=True,
        preparation_target_reload_preserved=True, closed_choice_schedule_preview_disabled=True)


@pytest.mark.parametrize("width", [390,1280])
@pytest.mark.parametrize("template_id", ["tku-autobiography-preparation", "tku-study-plan-preparation"])
def test_tku_preparation_pdf_is_not_an_official_application_form(page, live_server, width, template_id):
    _, errors = start(page, live_server, width, "application-center", verified=True)
    year = page.locator('#application-context-form input[name="academic_year"]')
    year.fill("2027-2028"); year.press("Tab")
    wait_until(page, "!state.applicationLoading")
    assert page.evaluate("state.applicationTemplates.length===2 && state.applicationTemplates.every(row=>row.official_layout===false)")
    page.locator(f'[data-open-application-template="{template_id}"]').first.click()
    expect(page.locator("#application-document-form")).to_be_visible()
    title='自伝' if 'autobiography' in template_id else '研修計画'
    values={'chinese_text':f'淡江驗收中文內容：{template_id}。隔離測試假資料。',
        'japanese_text':f'淡江の検証用：日本語の{title}です。これはテスト用データです。'}
    for field,value in values.items():
        page.locator(f'#application-document-fields textarea[name="{field}"]').fill(value)
    page.locator("#application-document-form button[type=submit]").click()
    review = page.locator("[data-application-review-template]")
    expect(review).to_be_enabled(timeout=15000)
    review.check()
    source = page.locator("#application-form-source")
    expect(source).to_have_attribute("href", re.compile(r"https://oieie\.tku\.edu\.tw/.+#page=4"))
    download_button = page.locator("#download-single-application-document")
    expect(download_button).to_be_enabled()
    with page.expect_download(timeout=30000) as result:
        download_button.click()
    download = result.value
    assert download.failure() is None
    OUTPUT.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT / f"{template_id}-{width}.pdf"
    download.save_as(str(filename))
    from pypdf import PdfReader
    text = " ".join(page.extract_text() or "" for page in PdfReader(filename).pages)
    assert "淡江" in text and "長庚" not in text
    assert "準備稿" in text
    for value in values.values():
        assert re.sub(r'\s+','',value) in re.sub(r'\s+','',text)
    assert shutil.which('pdftoppm'), 'PDF rendering check requires pdftoppm; do not report this check passed without it'
    prefix=OUTPUT / f'{template_id}-{width}-render'
    rendering=subprocess.run(['pdftoppm','-png','-r','110',str(filename),str(prefix)],check=True,capture_output=True,timeout=40)
    assert b'CMap' not in rendering.stderr and b'Unknown font' not in rendering.stderr, rendering.stderr.decode(errors='replace')
    rendered=sorted(OUTPUT.glob(prefix.name+'-*.png'))
    assert len(rendered)==len(PdfReader(filename).pages)
    from PIL import Image,ImageChops
    for path in rendered:
        with Image.open(path) as bitmap:
            assert bitmap.width>=800 and bitmap.height>=1000
            assert ImageChops.difference(bitmap.convert('RGB'),Image.new('RGB',bitmap.size,'white')).getbbox() is not None
            # Table borders alone previously satisfied a nonblank-page check.
            # Require substantial dark glyph pixels as well as embedded fonts.
            dark=bitmap.convert('L').histogram()
            assert sum(dark[:100])>1500, 'Rendered page has no readable text'
    descriptors=[font.get_object().get('/FontDescriptor')
        for pdf_page in PdfReader(filename).pages for font in pdf_page['/Resources']['/Font'].values()]
    embedded=[descriptor for descriptor in descriptors if descriptor and '/FontFile2' in descriptor.get_object()]
    assert embedded, 'CJK preparation font must be embedded in the actual PDF'
    field_values = page.locator("#application-document-fields textarea").evaluate_all("rows=>rows.map(row=>({name:row.name,value:row.value}))")
    expect(page.locator("#application-draft-sync-status")).to_contain_text("一般欄位已加密同步", timeout=15000)
    page.reload()
    expect(page.locator("#application-document-form")).to_be_visible()
    for field in field_values:
        expect(page.locator(f'#application-document-fields textarea[name="{field["name"]}"]')).to_have_value(field["value"], timeout=15000)
    record(page, template_id, width, errors, official_layout=False,
        templates=2, actual_pdf=str(filename), mother_school_name_correct=True, draft_reload_preserved=True,
        rendered_pages=[str(path) for path in rendered], pdf_contains_both_answers=True,
        official_source=source.get_attribute("href"))
