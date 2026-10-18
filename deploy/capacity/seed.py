"""Create synthetic accounts and sessions only inside the dedicated capacity stack."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import secrets

import requests

from exchange_info.application_documents import all_application_templates
from exchange_info.models import AccountSessionRecord, UserAccount, utc_now
from exchange_info.repositories import SupabaseAccountRepository


def seed(users: int) -> None:
    run_id = os.environ.get('EXCHANGE_CAPACITY_RUN_ID', '')
    if not re.fullmatch(r'[0-9a-f]{32}', run_id):
        raise RuntimeError('Invalid isolated run ID')
    if os.environ.get('EXCHANGE_SUPABASE_URL') != 'https://gateway':
        raise RuntimeError('Seeding is restricted to the isolated gateway')
    identity = requests.get('http://web:8080/capacity/identity', timeout=15)
    identity.raise_for_status()
    if identity.json().get('run_id') != run_id:
        raise RuntimeError('Staging identity mismatch; no accounts written')
    if not 2 <= users <= 2000:
        raise ValueError('users must be 2..2000')
    repo = SupabaseAccountRepository('https://gateway', os.environ['EXCHANGE_SUPABASE_SECRET_KEY'])
    output = Path('/artifacts/actors.json')
    prefix = f'capacity-{run_id}-'
    # Repeated benchmarks rotate only this fixture's previous sessions.
    if output.exists():
        previous = json.loads(output.read_text())
        if previous.get('run_id') != run_id:
            raise RuntimeError('Existing fixture belongs to a different isolated stack')
        for actor in previous['actors']:
            if not actor['account_id'].startswith(prefix):
                raise RuntimeError('Foreign account in fixture')
            repo.delete_session_by_token_hash(hashlib.sha256(actor['token'].encode()).hexdigest())
    expires = utc_now() + timedelta(hours=24)
    local = threading.local()
    def create_actor(i):
        if not hasattr(local, "repo"):
            local.repo = SupabaseAccountRepository("https://gateway", os.environ["EXCHANGE_SUPABASE_SECRET_KEY"])
        repo = local.repo
        account_id = f'{prefix}{i:05d}'
        account = repo.find_account_by_id(account_id)
        if account is None:
            account = repo.create_account(UserAccount(
                id=account_id, email=f'{account_id}@example.invalid',
                display_name=f'Capacity student {i}', home_university='長庚大學',
                email_verified=True, school_email_verified=True,
                student_status_verified=True, verified_university='長庚大學',
                product_tier='subscription',
            ))
        token = secrets.token_urlsafe(40)
        repo.save_session(AccountSessionRecord(account_id=account.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=expires))
        return {'account_id':account.id, 'token':token}
    with ThreadPoolExecutor(max_workers=8) as pool:
        actors = list(pool.map(create_actor, range(users + 2)))
    template = next(t for t in all_application_templates('長庚大學') if t.id == 'guardian-consent')
    data = dict(run_id=run_id, expires_at=expires.isoformat(), school='長庚大學',
                template_id=template.id, template_version=template.version, actors=actors)
    # Exclusive permissions on Linux; Stage.ps1 restricts the enclosing Windows directory.
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(data, stream, ensure_ascii=False)
    print(json.dumps({'seeded_accounts':len(actors), 'expires_at':expires.isoformat()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--users', type=int, default=1000)
    seed(parser.parse_args().users)
