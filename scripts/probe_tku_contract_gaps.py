"""Record actual unresolved shared API behavior with synthetic, isolated data.

This diagnostic does not grant permissions, restore admin features, access a
production database or declare acceptance. Guarded output records the exact SHA.
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))
from fastapi.testclient import TestClient
from exchange_info import api
from exchange_info.storage import (ensure_data_dirs, load_anonymous_identities,
    load_private_conversations, load_private_messages, save_anonymous_identities)
from test_community_permissions import _account, _post_payload
from test_social_community_api import _identity, _partner


def state():
    return dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        worktree_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())


def response(result):
    return dict(status=result.status_code, body=result.json() if result.content else None)


def probe(output):
    before = state()
    data = Path(tempfile.mkdtemp(prefix='tku-synthetic-contracts-',dir='/tmp'))
    ensure_data_dirs(data)
    fetch = api.fetch_partner_universities
    api.fetch_partner_universities = lambda: [_partner()]
    try:
        with TestClient(api.create_app(data)) as client:
            boards = client.get('/community/boards')
            _, unverified, _ = _account(data,client,'合成未驗證',email_verified=False)
            denied = client.post('/community/posts',headers=unverified,json=_post_payload('公共留學板'))
            _, headers, _ = _account(data,client,'合成臺北會員',home_university='國立臺北大學',
                verified_university='國立臺北大學',verified_department='企業管理學系')
            unknown = client.post('/community/posts',headers=headers,
                json=_post_payload('公共留學板',board_id='partner:anywhere'))
            conflicting = client.post('/community/posts',headers=headers,
                json=_post_payload('長庚大學',board_id='public-study-abroad'))
            cross_school = client.post('/community/posts',headers=headers,json=_post_payload('長庚大學'))
            own = client.post('/community/posts',headers=headers,json=_post_payload('公共留學板'))
            post_id = own.json()['id']
            deleted = client.delete(f'/community/posts/{post_id}',headers=headers)
            after_delete = client.get('/community/posts',params={'school':'公共留學板'})
            _, sender = _identity(data,client,'合成私訊發送者')
            recipient, _ = _identity(data,client,'合成私訊收件者')
            mutation_headers = {**sender,'X-Community-Mutation-ID':'tku-synthetic-retry-0001'}
            payload = dict(school_name=_partner().school_name,recipient_id=recipient['id'],
                initial_message='隔離資料：同一請求的私訊重送診斷。')
            first = client.post('/community/conversations',headers=mutation_headers,json=payload)
            save_anonymous_identities([r for r in load_anonymous_identities(data) if r.id!=recipient['id']],data)
            replay = client.post('/community/conversations',headers=mutation_headers,json=payload)
            schema = client.get('/openapi.json').json()
            prefixes = ['/admin/application-workflow-source-replacement-candidates',
                '/admin/application-workflow-review-batches/{batch_id}/stage','/admin/destination-profile-review',
                '/admin/application-workflow-publications']
            result = dict(tested_commit=before['commit'],starting_state=before,synthetic_only=True,
                production_database_access=False,acceptance_waiver=False,
                guest_boards=response(boards),unverified_email_post=response(denied),
                unknown_board=response(unknown),conflicting_board=response(conflicting),
                verified_ntpu_cross_school_post=response(cross_school),
                own_delete=response(deleted),deleted_post_visible_to_guest=any(
                    r['post']['id']==post_id for r in after_delete.json()),
                private_retry=dict(first=response(first),replay=response(replay),
                    exact_replay=first.status_code==replay.status_code and first.json()==replay.json(),
                    stored_conversations=len(load_private_conversations(data)),
                    stored_messages=len(load_private_messages(data))),
                absent_admin_route_families=[p for p in prefixes if not any(
                    path.startswith(p) for path in schema['paths'])],
                actual_admin_paths=sorted(p for p in schema['paths'] if p.startswith('/admin/')),
                interpretation=['Current board behavior permits verified-email cross-school posts; older matching-school test and metadata disagree. No permission policy changed.',
                    'Unknown and conflicting board payloads are probed separately; early assertion failures do not establish later behavior.',
                    'A private first-write/retry mismatch is an actual missing retry behavior, not only missing OpenAPI metadata.',
                    'No fabricated review or publication routes were added. Missing families require real persistence and promotion safeguards.'])
    finally:
        api.fetch_partner_universities = fetch
    result['ending_state'] = state()
    result['candidate_guard_passed'] = (not before['worktree_status'] and
        before==result['ending_state'])
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(tested_commit=result['tested_commit'],
        candidate_guard_passed=result['candidate_guard_passed'],
        private_retry_exact=result['private_retry']['exact_replay'],
        absent_admin_route_families=result['absent_admin_route_families']),ensure_ascii=False))
    return 0 if result['candidate_guard_passed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    raise SystemExit(probe(parser.parse_args().output))
