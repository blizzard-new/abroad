import json
from pathlib import Path
from uuid import uuid4
import requests
from playwright.sync_api import expect
from exchange_info.models import CommunityPost, CommunityPostComment
from exchange_info.storage import append_community_post, append_community_post_comment
from tests.e2e.conftest import login_through_web
pytest_plugins=['tests.e2e.conftest']


def test_reader_expiry_clears_school_body_and_private_draft(page, live_server):
    marker='合成校板私人正文'+uuid4().hex[:8]
    post=CommunityPost(board_id='tku',board_kind='university_exchange',school_name='淡江大學',author_id='synthetic-owner',display_name='匿名學生',title=marker,body=marker+'，僅供隔離驗證。')
    append_community_post(post,live_server.data_dir)
    append_community_post_comment(CommunityPostComment(post_id=post.id,author_id='synthetic-commenter',display_name='匿名學生',body='合成校板回覆，僅供隔離驗證。'),live_server.data_dir)
    email='reader-expiry-'+uuid4().hex[:8]+'@example.com';live_server.register(email)
    login_through_web(page,live_server,email)
    page.goto(f'{live_server.base_url}/?discussion={post.id}#university-posts')
    expect(page.locator('#discussion-article-title')).to_have_text(marker)
    expect(page.locator('#discussion-comments')).to_contain_text('合成校板回覆')
    page.locator('#discussion-reply-body').fill('合成私人草稿，失效後必須清除。')
    page.wait_for_function("() => Object.keys(sessionStorage).some(k => k.startsWith('uniway-discussion-draft:'))")
    cookies={c['name']:c['value'] for c in page.context.cookies() if c['name']=='exchange_guide_session'}
    assert requests.post(f'{live_server.base_url}/auth/logout',cookies=cookies,timeout=10).status_code==204
    with page.expect_response(lambda r: '/comments?' in r.url and r.status==401):
        page.locator('#discussion-comment-sort').select_option('latest')
    expect(page.locator('#auth-dialog')).to_be_visible()
    observed=page.evaluate("""() => ({readerOpen:document.querySelector('#discussion-reader').open,body:document.querySelector('#discussion-reader-body').textContent,draftKeys:Object.keys(sessionStorage).filter(k=>k.startsWith('uniway-discussion-draft:')),authHidden:document.querySelector('#auth-dialog').hidden,account:state.account})""")
    Path('/tmp/tku-ci-reader-repro/observed.json').write_text(json.dumps(observed,ensure_ascii=False,indent=2)+'\n')
    page.screenshot(path='/tmp/tku-ci-reader-repro/expired-reader.png',full_page=True)
    expect(page.locator('#discussion-reader')).not_to_be_visible()
    assert marker not in page.locator('#discussion-reader-body').text_content()
    assert observed['draftKeys']==[]
    page.locator('#login-form input[name=email]').fill(email)
