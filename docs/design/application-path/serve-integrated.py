"""Local integration review with synthetic accounts; never deploy this fixture."""
from pathlib import Path
import os
import sys
import secrets
import hashlib
from datetime import timedelta

ROOT = Path(__file__).resolve().parents[3]
for key in list(os.environ):
    if key.startswith(('EXCHANGE_', 'SUPABASE_', 'GOOGLE_OAUTH_', 'SMTP_')):
        del os.environ[key]
DATA = ROOT / 'output/application-path-review/integrated-data'
os.environ.update(EXCHANGE_ENVIRONMENT='development', EXCHANGE_INFO_DATA_DIR=str(DATA),
    EXCHANGE_ACCOUNT_REPOSITORY='jsonl', EXCHANGE_VAULT_BACKEND='local',
    EXCHANGE_FORM_DRAFT_BACKEND='local', EXCHANGE_EMAIL_VERIFICATION_BACKEND='disabled',
    EXCHANGE_WARM_CACHES='0', EXCHANGE_SEO_INDEXABLE='false')
sys.path.insert(0, str(ROOT / 'src'))
from exchange_info.api import create_app, AUTH_COOKIE_NAME
from exchange_info.models import UserAccount, AccountSessionRecord, utc_now
from exchange_info.repositories import JsonlAccountRepository
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn

app = create_app(DATA)
preview = ROOT / 'docs/design/application-path'
preview.mkdir(parents=True, exist_ok=True)
app.mount('/design-preview', StaticFiles(directory=preview, html=True), name='design-preview')
repository = JsonlAccountRepository(DATA)
account = UserAccount(id='local-integrated-review-only', email='design-review@example.test',
    display_name='整合測試學生', home_university='國立臺北大學', email_verified=True,
    school_email_verified=True, student_status_verified=True,
    verified_university='國立臺北大學', verified_department='資訊工程學系')
account = repository.find_account_by_id(account.id) or account
repository.save_account(account)
token = secrets.token_urlsafe(32)
repository.save_session(AccountSessionRecord(account_id=account.id,
    token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now()+timedelta(hours=12)))

@app.get('/local-review-session', include_in_schema=False)
def review_session():
    repository.save_session(AccountSessionRecord(account_id=account.id, token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now()+timedelta(hours=12)))
    response = RedirectResponse('/#my-application')
    response.set_cookie(AUTH_COOKIE_NAME, token, httponly=True, samesite='lax', max_age=43200)
    return response

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=18775, access_log=False, log_level='warning')
