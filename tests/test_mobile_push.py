from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.mobile_auth import mobile_handoff_url, pkce_challenge
from exchange_info.mobile_push import LocalPushStore, MobilePushService
from exchange_info.models import AccountNotification, AccountNotificationPreferences, UserAccount, utc_now


def test_device_ownership_rotation_and_durable_delivery_claim(tmp_path):
    store = LocalPushStore(tmp_path/'push.sqlite3')
    store.register('a', 'i', 'fid1')
    store.remove('b', 'i')
    assert len(store.devices('a')) == 1
    store.register('b', 'i', 'fid2')
    assert store.devices('a') == []
    assert store.devices('b')[0]['fid'] == 'fid2'
    with ThreadPoolExecutor(max_workers=8) as workers:
        claims = list(workers.map(lambda _: store.claim('n', 'i'), range(8)))
    assert claims.count(True) == 1
    store.finish('n', 'i', 'sent')
    assert not LocalPushStore(tmp_path/'push.sqlite3').claim('n', 'i')


def test_push_filters_backlog_read_items_and_deduplicates(tmp_path):
    store = LocalPushStore(tmp_path/'push.sqlite3')
    account = UserAccount(display_name='Student', notification_preferences=AccountNotificationPreferences(push_enabled=True))
    store.register(account.id, 'device', 'fid')
    current = utc_now()+timedelta(seconds=1)
    def notification(key, **fields):
        return AccountNotification(account_id=account.id, dedupe_key=key, title='Private school detail',
            body='Private document detail', source_key='test', kind='content_update', created_at=current, **fields)
    unread = notification('new')
    rows = [unread, notification('read', read_at=utc_now()), notification('deleted', deleted_at=utc_now()),
            notification('old').model_copy(update={'created_at': utc_now()-timedelta(days=2)})]
    sent = []
    repository = SimpleNamespace(list_accounts=lambda: [account], list_notifications=lambda *a, **k: rows)
    service = MobilePushService(repository, SimpleNamespace(refresh_content_updates=lambda **k: None), store,
        SimpleNamespace(send=lambda *args: sent.append(args) or 'sent'))
    assert service.dispatch()['sent'] == 1
    assert service.dispatch()['sent'] == 0
    assert sent == [('fid', account.id, unread.id)]


def test_transient_failure_can_retry_and_unregistered_device_is_removed(tmp_path):
    store = LocalPushStore(tmp_path/'push.sqlite3')
    store.register('a', 'i', 'fid')
    assert store.claim('n', 'i')
    store.finish('n', 'i', 'retrying')
    assert not store.claim('n', 'i')
    with store.connect() as db:
        db.execute('update deliveries set retry_at=0')
    assert store.claim('n', 'i')
    store.finish('n', 'i', 'failed')
    assert not store.claim('n', 'i')


def test_device_api_requires_login_and_does_not_delete_another_accounts_device(tmp_path):
    from urllib.parse import parse_qs, urlparse
    app = create_app(tmp_path)
    client = TestClient(app)
    store = LocalPushStore(tmp_path/'push.sqlite3')
    app.state.mobile_push_service = SimpleNamespace(store=store)
    def login(name):
        account = UserAccount(display_name=name)
        app.state.account_repository.save_account(account)
        url = mobile_handoff_url(app, account.id, pkce_challenge('v'*64), 's'*43)
        code = parse_qs(urlparse(url).query)['code'][0]
        token = client.post('/auth/mobile/exchange', json={'code':code, 'code_verifier':'v'*64}).json()['access_token']
        return account.id, {'Authorization':'Bearer '+token}
    a, header_a = login('A')
    b, header_b = login('B')
    payload = {'installation_id': 'a'*64, 'fid':'firebase-installation'}
    assert client.put('/account/mobile-devices', json=payload).status_code == 401
    assert client.put('/account/mobile-devices', json=payload, headers=header_a).status_code == 204
    assert app.state.account_repository.find_account_by_id(a).notification_preferences.push_enabled
    assert client.delete('/account/mobile-devices/'+'a'*64, headers=header_b).status_code == 204
    assert len(store.devices(a)) == 1
    assert client.delete('/account/mobile-devices/'+'a'*64, headers=header_a).status_code == 204
    assert store.devices(a) == []
