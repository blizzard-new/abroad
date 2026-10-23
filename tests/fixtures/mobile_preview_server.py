"""Isolated emulator fixture, never part of exchange_info or production routes.

Run with python tests/fixtures/mobile_preview_server.py; bind is loopback only.
"""
import os
from pathlib import Path
import tempfile

if os.environ.get('EXCHANGE_ENVIRONMENT') == 'production':
    raise SystemExit('Fixture server cannot run in production.')
os.environ['EXCHANGE_WARM_CACHES'] = '0'
os.environ['EXCHANGE_ACCOUNT_REPOSITORY'] = 'jsonl'
os.environ['EXCHANGE_VAULT_BACKEND'] = 'local'
os.environ['EXCHANGE_FORM_DRAFT_BACKEND'] = 'local'

from fastapi import Request
import uvicorn
from exchange_info.api import create_app
from exchange_info.mobile_auth import mobile_handoff_url
from exchange_info.models import UserAccount

fixture_directory = tempfile.TemporaryDirectory(prefix='uniway-mobile-fixture-')
app = create_app(Path(fixture_directory.name))
account = UserAccount(display_name='Emulator Student', home_university='長庚大學')
app.state.account_repository.save_account(account)


@app.post('/__fixture__/handoff')
async def handoff(request: Request):
    body = await request.json()
    return {'url': mobile_handoff_url(app, account.id, body['challenge'], body['state'])}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=18765, log_level='warning', access_log=False)
