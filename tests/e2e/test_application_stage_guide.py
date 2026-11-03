"""The retired three-stage banner is replaced by level tools, while schedule URLs survive."""
import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize('width', [390, 768, 1440])
def test_legacy_tool_routes_have_no_duplicate_stage_guide(page, live_server, width):
    page.set_viewport_size({'width':width,'height':960})
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','長庚大學')")
    for route in ('advisor','eligibility','application-center','overview','calendar'):
        page.goto(f'{live_server.base_url}/#{route}')
        page.wait_for_load_state('networkidle')
        # 準備與時程 is the 時程 tab of 我的申請 now; its old address redirects there.
        shown = '#schedule-view' if route == 'overview' else f'[data-university-page="{route}"]'
        expect(page.locator(shown)).to_be_visible()
        expect(page.locator('#application-journey-steps, #planning-next-action, #application-workspace-tool-menu')).to_have_count(0)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('.application-tools-heading a[href="#overview"]').click()
    expect(page.locator('#tracker-title')).to_have_text('待辦與期限')


def test_glide_select_keeps_keyboard_selection_and_dependent_options(page, live_server):
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立臺北大學')")
    page.goto(f'{live_server.base_url}/#advisor')
    page.wait_for_load_state('networkidle')
    trigger=page.locator('#advisor-college + .glide-select__trigger')
    trigger.click()
    page.get_by_role('listbox',name='學院',exact=True).get_by_role('option',name='電機資訊學院',exact=True).click()
    expect(page.locator('#advisor-college')).to_have_value('電機資訊學院')
    expect(page.locator('#advisor-department + .glide-select__trigger')).to_be_enabled()
    trigger=page.locator('#advisor-degree + .glide-select__trigger')
    trigger.press('Enter')
    trigger.press('End')
    trigger.press('Enter')
    expect(trigger).to_have_attribute('aria-expanded','false')
    assert page.locator('#advisor-degree').input_value() != ''
    assert page.locator('select:not(.glide-select__native)').count()==0
