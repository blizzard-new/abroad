"""Supplemental actual UI evidence; never modify the test report or timeout."""
from pathlib import Path
import datetime, hashlib, json, os
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != 'call' or not report.passed or item.funcargs.get('slug') != 'tohoku':
        return
    page = item.funcargs['page']; width = item.funcargs['width']
    out = Path(os.environ['NCU_VISUAL_OUT']); out.mkdir(parents=True, exist_ok=True)
    result = {'sha': os.environ['NCU_VISUAL_SHA'], 'width': width,
              'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'original_assertions_and_timeouts_unchanged': True, 'images': []}
    try:
        page.locator('#detail-tab-application').click()
        coe = page.locator('#detail-application .workflow-step').filter(
            has=page.locator(':scope > summary').filter(has_text='四類指定資料／財力條件')).first
        if not coe.evaluate('(el) => el.open'):
            coe.locator(':scope > summary').click()
        text = coe.inner_text()
        assert coe.locator('.workflow-documents > li').count() == 4
        assert '再次上傳護照PDF' in text and 'Proceeding' in text
        assert 'JASSO證明與資料核定與否皆禁用' in text
        result['actual_coe_text'] = text
        p = out / f'tohoku-coe-four-documents-{width}.png'; coe.screenshot(path=str(p))
        result['images'].append({'name': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
        page.locator('#detail-tab-overview').click()
        group = page.locator('.partner-summary-group').filter(
            has=page.get_by_role('heading', name='合作校申請步驟')).first
        more = group.locator('.partner-summary-more')
        if more.count() and not more.evaluate('(el) => el.open'):
            more.locator(':scope > summary').click()
        text = group.inner_text()
        assert '再次上傳護照PDF' in text and '核定與否皆禁用' in text
        result['actual_expanded_summary_text'] = text
        p = out / f'tohoku-expanded-student-summary-{width}.png'; group.screenshot(path=str(p))
        result['images'].append({'name': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
        result['capture_passed'] = True
    except Exception as exc:
        result['capture_passed'] = False
        result['capture_error'] = repr(exc)
    (out / f'visual-{width}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
