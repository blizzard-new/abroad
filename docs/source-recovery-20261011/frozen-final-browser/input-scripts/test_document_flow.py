"""One document, one visible path from filling to submission, without claiming it was sent."""
import pytest
from playwright.sync_api import expect

from .test_document_workbench import open_document
from .test_glass_theme import capture
from .test_web_next_phase import _fill_required_application_fields


def stage(page, name):
    return page.locator(f'#document-flow-steps [data-flow-stage="{name}"]')


@pytest.mark.parametrize('width', [390, 1754])
def test_document_flow_guides_each_step_and_never_claims_submission(page, live_server, width):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    open_document(page, live_server)
    flow = page.locator('#document-flow')
    expect(flow).to_be_visible()
    expect(page.locator('#document-flow-steps li')).to_have_count(6)
    expect(stage(page, 'fill')).to_have_attribute('data-flow-state', 'current')
    expect(stage(page, 'fill')).to_have_attribute('aria-current', 'step')
    for later in ('review', 'download'):
        expect(stage(page, later)).not_to_have_attribute('data-flow-state', 'done')
    for optional in ('check', 'vault'):
        expect(stage(page, optional)).to_have_attribute('data-flow-state', 'optional')
    expect(flow).to_contain_text('不代表已送件、校方受理或錄取')
    expect(page.locator('#document-flow-next')).to_contain_text('填寫必填欄位')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    capture(page, f'document-flow-start-{width}.png')

    # The next-step button lands on the first required field that is still empty.
    page.locator('#document-flow-next').click()
    focused = page.evaluate("document.activeElement && document.activeElement.closest('#application-document-fields') !== null")
    assert focused

    _fill_required_application_fields(page)
    page.locator('#application-document-form button[type=submit]').click()
    expect(stage(page, 'fill')).to_have_attribute('data-flow-state', 'done', timeout=15_000)
    expect(stage(page, 'review')).to_have_attribute('data-flow-state', 'current')
    expect(page.locator('#document-flow-note')).to_contain_text('1 / 6')

    review = page.locator('[data-application-review-template]')
    expect(review).to_be_enabled(timeout=15_000)
    review.check()
    expect(stage(page, 'review')).to_have_attribute('data-flow-state', 'done', timeout=15_000)
    expect(stage(page, 'download')).to_have_attribute('data-flow-state', 'current')

    # "Next step" from the download stage produces the PDF; nothing is marked submitted.
    with page.expect_download():
        page.locator('#document-flow-next').click()
    expect(page.locator('#application-download-dialog')).to_be_visible()
    page.locator('#application-download-dialog [data-close-application-download]').first.click()
    expect(page.locator('#application-download-dialog')).not_to_be_visible()
    expect(stage(page, 'download')).to_have_attribute('data-flow-state', 'done', timeout=15_000)
    expect(stage(page, 'check')).to_have_attribute('data-flow-state', 'current')
    expect(page.locator('#document-flow-skip')).to_be_visible()
    capture(page, f'document-flow-after-pdf-{width}.png')
    expect(stage(page, 'submit')).not_to_have_attribute('data-flow-state', 'done')

    # Optional steps can be skipped; the path then points at signing and submission.
    page.locator('#document-flow-skip').click()
    expect(stage(page, 'vault')).to_have_attribute('data-flow-state', 'current')
    page.locator('#document-flow-skip').click()
    expect(page.locator('#document-flow-next')).to_contain_text('簽名、核章與送件')
    page.locator('#document-flow-next').click()
    expect(page.locator('#document-pane-source')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert errors == []
