"""Opt-in mobile devices and retryable FCM delivery of published rule updates.

Production uses the same Postgres database as accounts. Only an authenticated
administrator can run dispatch; reading the inbox never sends a push.
"""
from __future__ import annotations

from datetime import timedelta
import os
from pathlib import Path
import re
import sqlite3
import time

from fastapi import HTTPException, Request, Response
from pydantic import BaseModel, Field

from .models import utc_now
from .supabase_keys import supabase_key_headers
from . import supabase_http


class DeviceRegistration(BaseModel):
    installation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    fid: str = Field(min_length=10, max_length=256, pattern=r"^[A-Za-z0-9_:\-]+$")


class LocalPushStore:
    """Development store; SQLite transactions also protect concurrent test workers."""
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.executescript("""
                create table if not exists devices (
                  installation_id text primary key, account_id text not null,
                  fid text not null unique, registered_at real not null);
                create table if not exists deliveries (
                  notification_id text, installation_id text, state text,
                  retry_at real, attempts integer,
                  primary key(notification_id, installation_id));
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def register(self, account_id, installation_id, fid):
        with self.connect() as db:
            db.execute("delete from devices where fid=? and installation_id<>?", (fid, installation_id))
            db.execute("""insert into devices values(?,?,?,?) on conflict(installation_id)
                do update set account_id=excluded.account_id, fid=excluded.fid,
                registered_at=case when devices.account_id=excluded.account_id then devices.registered_at else excluded.registered_at end""",
                (installation_id, account_id, fid, time.time()))

    def remove(self, account_id, installation_id):
        with self.connect() as db:
            db.execute("delete from devices where account_id=? and installation_id=?", (account_id, installation_id))

    def devices(self, account_id):
        with self.connect() as db:
            return [dict(row) for row in db.execute("select * from devices where account_id=?", (account_id,))]

    def claim(self, notification_id, installation_id):
        with self.connect() as db:
            row = db.execute("""insert into deliveries values(?,?,'sending',?,1)
                on conflict(notification_id,installation_id) do update
                set state='sending', retry_at=excluded.retry_at, attempts=attempts+1
                where deliveries.state not in ('sent','failed') and deliveries.retry_at<=? and deliveries.attempts<5
                returning attempts""", (notification_id, installation_id, time.time()+120, time.time())).fetchone()
            return row is not None

    def finish(self, notification_id, installation_id, status):
        with self.connect() as db:
            db.execute("update deliveries set state=?,retry_at=? where notification_id=? and installation_id=?",
                       (status, time.time()+300, notification_id, installation_id))


class SupabasePushStore:
    def __init__(self):
        url = os.getenv('EXCHANGE_SUPABASE_URL') or os.getenv('SUPABASE_URL', '')
        key = os.getenv('EXCHANGE_SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        if not url.startswith('https://') or not key:
            raise RuntimeError('Mobile push requires the configured account database.')
        self.url = url.rstrip('/') + '/rest/v1/'
        self.headers = {**supabase_key_headers(key), 'Content-Type': 'application/json'}

    def request(self, method, path, **kwargs):
        response = supabase_http.request(method, self.url+path, headers=self.headers, timeout=15, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None

    def register(self, account_id, installation_id, fid):
        self.request('POST', 'rpc/exchange_register_mobile_device', json={
            'p_account_id': account_id, 'p_installation_id': installation_id, 'p_fid': fid})

    def remove(self, account_id, installation_id):
        self.request('DELETE', 'exchange_mobile_devices', params={
            'account_id': 'eq.'+account_id, 'installation_id': 'eq.'+installation_id})

    def devices(self, account_id):
        rows = self.request('GET', 'exchange_mobile_devices', params={'account_id': 'eq.'+account_id})
        from datetime import datetime
        return [{**row, 'registered_at': datetime.fromisoformat(row['registered_at'].replace('Z','+00:00')).timestamp()} for row in rows]

    def claim(self, notification_id, installation_id):
        return self.request('POST', 'rpc/exchange_claim_mobile_push', json={
            'p_notification_id': notification_id, 'p_installation_id': installation_id}) is True

    def finish(self, notification_id, installation_id, status):
        self.request('PATCH', 'exchange_mobile_push_deliveries', params={
            'notification_id': 'eq.'+notification_id, 'installation_id': 'eq.'+installation_id},
            json={'state': status, 'retry_at': (utc_now()+timedelta(minutes=5)).isoformat()})


class FcmSender:
    def __init__(self, project: str):
        if not re.fullmatch(r'[a-z][a-z0-9-]{4,62}', project):
            raise ValueError('Invalid Firebase project ID')
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/firebase.messaging'])
        self.session = AuthorizedSession(credentials)
        self.url = f'https://fcm.googleapis.com/v1/projects/{project}/messages:send'

    def send(self, fid, account_id, notification_id):
        # Data-only allows the app to reject messages for a signed-out account.
        # Private title/body/files never travel to the lock screen.
        response = self.session.post(self.url, timeout=20, json={'message': {
            'fid': fid,
            'data': {'account_id': account_id, 'notification_id': notification_id},
            'android': {'priority': 'high', 'ttl': '86400s'},
        }})
        if response.ok:
            return 'sent'
        try:
            details = response.json().get('error', {}).get('details', [])
            if any(row.get('errorCode') == 'UNREGISTERED' for row in details):
                return 'unregistered'
        except (ValueError, AttributeError):
            pass
        # Configuration/permission/invalid-payload errors must not discard devices.
        return 'retrying'


class MobilePushService:
    def __init__(self, repository, notifications, store, sender):
        self.repository, self.notifications, self.store, self.sender = repository, notifications, store, sender

    def dispatch(self):
        result = {'sent': 0, 'retrying': 0, 'unregistered': 0}
        now = utc_now()
        for account in self.repository.list_accounts():
            if not account.notification_preferences.push_enabled:
                continue
            devices = self.store.devices(account.id)
            if not devices:
                continue
            self.notifications.refresh_content_updates(now=now, accounts=[account])
            for notification in self.repository.list_notifications(account.id, limit=100):
                if (notification.kind != 'content_update' or notification.read_at or notification.deleted_at
                        or notification.created_at < now-timedelta(days=1)):
                    continue
                for device in devices:
                    if notification.created_at.timestamp() < device['registered_at']:
                        continue
                    if not self.store.claim(notification.id, device['installation_id']):
                        continue
                    try:
                        status = self.sender.send(device['fid'], account.id, notification.id)
                    except Exception:
                        status = 'retrying'
                    self.store.finish(notification.id, device['installation_id'], 'failed' if status == 'unregistered' else status)
                    if status == 'unregistered':
                        self.store.remove(account.id, device['installation_id'])
                    result[status] += 1
        return result


def register_mobile_push_routes(app, authenticated_account, authenticated_admin, data_dir):
    # Lazy configuration: web login and local reminders remain usable without Firebase.
    app.state.mobile_push_service = None

    def service():
        if app.state.mobile_push_service is not None:
            return app.state.mobile_push_service
        project = os.getenv('EXCHANGE_FIREBASE_PROJECT_ID', '')
        if not project:
            raise HTTPException(503, '遠端推播尚未設定；本機日期提醒仍可使用。')
        try:
            repository = app.state.account_repository
            store = SupabasePushStore() if repository.backend_name == 'supabase' else LocalPushStore(Path(data_dir)/'processed/mobile-push.sqlite3')
            app.state.mobile_push_service = MobilePushService(repository, app.state.notification_service, store, FcmSender(project))
            return app.state.mobile_push_service
        except Exception:
            raise HTTPException(503, '遠端推播設定尚未完成。') from None

    @app.put('/account/mobile-devices', status_code=204)
    def register(payload: DeviceRegistration, request: Request):
        account, _ = authenticated_account(request)
        svc = service()
        svc.store.register(account.id, payload.installation_id, payload.fid)
        if not account.notification_preferences.push_enabled:
            preferences = account.notification_preferences.model_copy(update={'push_enabled': True})
            app.state.account_repository.patch_account_fields(account.id, {'notification_preferences': preferences.model_dump(mode='json')})
        return Response(status_code=204, headers={'Cache-Control': 'no-store'})

    @app.delete('/account/mobile-devices/{installation_id}', status_code=204)
    def remove(installation_id: str, request: Request):
        account, _ = authenticated_account(request)
        if not re.fullmatch(r'[a-f0-9]{64}', installation_id):
            raise HTTPException(422, 'Invalid installation ID')
        service().store.remove(account.id, installation_id)
        return Response(status_code=204, headers={'Cache-Control': 'no-store'})

    @app.post('/admin/mobile-push/run-due')
    def dispatch(request: Request, response: Response):
        authenticated_admin(request)
        response.headers['Cache-Control'] = 'no-store'
        return service().dispatch()
