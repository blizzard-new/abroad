"""Selected-document continuity, explicit transfers, and stale-result isolation."""
from hashlib import sha256
from pathlib import Path
import re
from urllib.parse import quote

import pytest
import requests
from playwright.sync_api import expect

from .test_glass_theme import verified_login, capture
from .test_web_next_phase import _fill_required_application_fields, _auth_headers
from .conftest import open_navigation


def open_document(page, live_server):
    session = verified_login(page, live_server)
    page.evaluate("location.hash='#application-center'")
    link = page.locator('.application-template-open').first
    expect(link).to_be_visible()
    route = '#application-form=' + quote(link.get_attribute('data-open-application-template'), safe='')
    second_route = '#application-form=' + quote(page.locator('.application-template-open').nth(1).get_attribute('data-open-application-template'), safe='')
    link.click()
    expect(page.locator('#application-document-form')).to_be_visible()
    return session, route, second_route


@pytest.mark.parametrize('width', [390, 1754])
def test_document_panes_keep_draft_and_legacy_tools_have_one_form(page, live_server, width):
    page.set_viewport_size({'width':width, 'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    _, route, _ = open_document(page, live_server)
    field = page.locator('#application-document-fields input[type=text]').first
    field_name = field.get_attribute('name')
    field.fill('工作區保留的未完成草稿')
    field.evaluate('element => window.originalDocumentField = element')
    for pane in ['check','vault','source']:
        page.locator(f'[data-document-tab={pane}]').click()
        assert page.url.endswith(route)
        expect(page.locator(f'#document-pane-{pane}')).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    expect(page.locator('#application-form-source')).to_have_attribute('href', re.compile('https://'))
    page.locator('#document-tab-source').press('Home')
    expect(page.locator('#document-tab-edit')).to_be_focused()
    expect(field).to_have_value('工作區保留的未完成草稿')
    assert field.evaluate('element => element === window.originalDocumentField')
    capture(page, f'document-workbench-{width}.png')
    for legacy, form in [('document-check','document-check-form'),('documents','private-vault-form')]:
        page.evaluate('(hash) => location.hash=hash', f'#{legacy}')
        expect(page.locator(f'#{legacy} #{form}')).to_be_visible()
        expect(page.locator(f'#{form}')).to_have_count(1)
    page.evaluate('(hash) => location.hash=hash', route)
    expect(page.locator(f'#application-document-fields [name="{field_name}"]')).to_have_value('工作區保留的未完成草稿')
    page.reload()
    expect(page.locator(f'#application-document-fields [name="{field_name}"]')).to_have_value('工作區保留的未完成草稿', timeout=15_000)
    assert errors == []


def test_generated_pdf_is_checked_and_saved_only_with_separate_consent(page, live_server):
    session, _, _ = open_document(page, live_server)
    _fill_required_application_fields(page)
    page.locator('#application-document-form button[type=submit]').click()
    review = page.locator('[data-application-review-template]')
    expect(review).to_be_enabled(timeout=15_000)
    review.check()
    expect(page.locator('#download-single-application-document')).to_be_enabled()
    transferred = []
    page.on('request', lambda request: transferred.append(request.url) if request.method == 'POST'
            and (request.url.endswith('/document-check') or request.url.endswith('/account/vault/documents')) else None)
    with page.expect_download() as download_info:
        page.locator('#download-single-application-document').click()
    download = download_info.value
    pdf = Path(download.path()).read_bytes()
    assert pdf.startswith(b'%PDF')
    page.locator('[data-generated-document-action=check]').click()
    expect(page.locator('#document-pane-check')).to_be_visible()
    expect(page.locator('#document-upload-title')).to_have_text(download.suggested_filename)
    expect(page.locator('#document-check-consent')).not_to_be_checked()
    page.locator('#document-check-form').dispatch_event('submit')
    expect(page.locator('#document-check-status')).to_contain_text('同意')
    assert transferred == []
    page.locator('#document-check-consent').check()
    with page.expect_response(lambda response: response.url.endswith('/document-check')) as checked:
        page.locator('#document-check-submit').click()
    assert checked.value.status == 200
    expect(page.locator('.document-check-provenance')).to_contain_text(download.suggested_filename)
    browser_hash = page.evaluate("""async () => {
        const bytes = await state.documentCheckGeneratedCandidate.blob.arrayBuffer();
        const hash = await crypto.subtle.digest('SHA-256', bytes);
        return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2,'0')).join('');
    }""")
    assert browser_hash == sha256(pdf).hexdigest()
    page.locator('[data-document-tab=vault]').click()
    page.locator('[data-use-generated-vault]').click()
    expect(page.locator('#private-vault-form [name=consent]')).not_to_be_checked()
    page.locator('#private-vault-form').dispatch_event('submit')
    expect(page.locator('#private-vault-form-status')).to_contain_text('同意')
    assert len(transferred) == 1
    page.locator('#private-vault-form [name=consent]').check()
    with page.expect_response(lambda response: response.url.endswith('/account/vault/documents') and response.request.method == 'POST') as saved:
        page.locator('#private-vault-form button[type=submit]').click()
    assert saved.value.status == 201
    item = saved.value.json()
    expect(page.locator('#private-vault-list')).to_contain_text(item['label'])
    version = item['versions'][0]
    headers = _auth_headers(session)
    grant = requests.post(f"{live_server.base_url}/account/vault/versions/{version['id']}/download-grant", headers=headers, timeout=10)
    grant.raise_for_status()
    response = requests.post(f"{live_server.base_url}/account/vault/download",
                             headers={**headers, 'X-Vault-Download-Token':grant.json()['token']}, timeout=10)
    response.raise_for_status()
    assert sha256(response.content).digest() == sha256(pdf).digest()


def test_switching_template_discards_previous_file_consent_and_late_check(page, live_server):
    _, first_route, second_route = open_document(page, live_server)
    assert second_route != first_route
    page.locator('[data-document-tab=check]').click()
    page.locator('#document-check-file').set_input_files({'name':'first.txt', 'mimeType':'text/plain', 'buffer':('申請文件內容。'*80).encode()})
    page.locator('#document-check-consent').check()
    deferred = []
    page.route('**/document-check', lambda route: deferred.append(route))
    page.locator('#document-check-submit').click()
    page.wait_for_function("document.querySelector('#document-check-submit').disabled")
    assert deferred
    response = deferred[0].fetch()
    assert response.status == 200
    page.evaluate('(hash) => location.hash=hash', second_route)
    expect(page.locator('#document-pane-edit')).to_be_visible()
    # Deliver a real check response after the template switch. It must not appear.
    try:
        deferred[0].fulfill(response=response)
    except Exception as error:
        assert 'cancel' in str(error).lower() or 'intercept' in str(error).lower()
    page.locator('[data-document-tab=check]').click()
    expect(page.locator('#document-check-consent')).not_to_be_checked()
    assert page.locator('#document-check-file').evaluate('element => element.files.length') == 0
    expect(page.locator('#document-check-result')).to_contain_text('尚未檢查文件')
    expect(page.locator('#document-check-submit')).to_be_enabled()


def test_editing_after_generation_does_not_offer_old_pdf_as_current_document(page, live_server):
    open_document(page, live_server)
    _fill_required_application_fields(page)
    page.locator('#application-document-form button[type=submit]').click()
    review = page.locator('[data-application-review-template]')
    expect(review).to_be_enabled(timeout=15_000)
    review.check()
    expect(page.locator('#download-single-application-document')).to_be_enabled()
    with page.expect_download():
        page.locator('#download-single-application-document').click()
    page.locator('[data-generated-document-action=check]').click()
    page.locator('#document-check-consent').check()
    page.locator('[data-document-tab=edit]').click()
    page.locator('#application-document-fields input[type=text]').first.fill('修改後的內容')
    page.locator('[data-document-tab=check]').click()
    expect(page.locator('[data-check-generated-document]')).to_be_hidden()
    expect(page.locator('#document-check-consent')).not_to_be_checked()
    expect(page.locator('#document-check-result')).to_contain_text('尚未檢查文件')
    page.locator('[data-document-tab=vault]').click()
    expect(page.locator('#generated-vault-candidate')).to_be_hidden()


def test_logout_clears_live_fields_and_selected_check_file(page, live_server):
    open_document(page, live_server)
    field = page.locator('#application-document-fields input[type=text]').first
    field.fill('僅屬於目前帳號的文件草稿')
    page.locator('[data-document-tab=check]').click()
    page.locator('#document-check-file').set_input_files({'name':'private.txt','mimeType':'text/plain','buffer':b'private draft'})
    page.locator('#document-check-consent').check()
    open_navigation(page)
    page.locator('#account-button').click()
    page.locator('#logout-button').click()
    expect(page.locator('#account-button')).to_contain_text('登入')
    expect(page.locator('#application-document-fields [data-application-field]')).to_have_count(0)
    assert page.locator('#document-check-file').evaluate('element => element.files.length') == 0
    expect(page.locator('#document-check-consent')).not_to_be_checked()
