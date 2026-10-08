"""Synthetic, isolated before/after API privacy evidence for the fixed candidate.

Never reads user or production data. Requires the repository test fixtures and
leaves output outside the code worktree, recording whether it was clean.
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
from exchange_info.api import create_app
from exchange_info.storage import ensure_data_dirs, load_community_posts
from test_community_permissions import _account, _post_payload


def probe(output):
    before = subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    data = Path(tempfile.mkdtemp(prefix='tku-synthetic-privacy-', dir='/tmp'))
    ensure_data_dirs(data)
    with TestClient(create_app(data)) as c:
        _, headers, identity = _account(data, c, '合成驗收姓名', home_university='淡江大學')
        created = c.post('/community/posts',headers=headers,json=_post_payload('公共留學板',identity_mode='real_name'))
        post_id = created.json()['id']
        comment = c.post(f'/community/posts/{post_id}/comments',headers=headers,
                         json={'body':'合成留言資料','identity_mode':'real_name'})
        guest = c.get('/community/posts',params={'school':'公共留學板'}).json()
        detail = c.get(f'/community/posts/{post_id}').json()
        sensitive = c.post('/community/posts',headers=headers,
                           json=_post_payload('公共留學板',body='合成護照號碼：A12345678，僅供隔離測試。'))
        sensitive_id = sensitive.json().get('id')
        publicly_visible = any(r['post']['id']==sensitive_id for r in c.get('/community/posts').json())
        deleted = c.delete('/auth/me',headers=headers)
        public_after = c.get('/community/posts').json()
        names = [r['post']['display_name'] for r in public_after if r['post']['id']==post_id]
        comment_names = [z['display_name'] for r in public_after if r['post']['id']==post_id for z in r['comments']]
        linked = any(p.author_id==identity['id'] for p in load_community_posts(data))
        checks = dict(own_post_response_hides_author_id=not created.json().get('author_id'),
            own_comment_response_hides_author_id=not comment.json().get('author_id'),
            guest_feed_hides_author_id=all(not r['post'].get('author_id') for r in guest),
            guest_detail_hides_author_id=not detail.get('author_id'),
            sensitive_rejected_before_publication=sensitive.status_code==422 and not publicly_visible,
            deleted_post_and_comment_deidentified=deleted.status_code==204 and names==['已刪除帳號'] and comment_names==['已刪除帳號'] and not linked)
        result = dict(tested_commit=head, synthetic_only=True, production_database_access=False,
            starting_worktree_status=before, ending_worktree_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),
            post_create_status=created.status_code, post_create_author_id_present=bool(created.json().get('author_id')),
            guest_list_author_id_present=any(bool(r['post'].get('author_id')) for r in guest),
            guest_detail_author_id_present=bool(detail.get('author_id')), sensitive_status=sensitive.status_code,
            sensitive_visible_to_guest=publicly_visible, delete_status=deleted.status_code,
            post_delete_names=names, post_delete_comment_names=comment_names, stored_author_still_linked=linked,
            checks=checks, all_checks_passed=all(checks.values()))
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['all_checks_passed'] and not before and not result['ending_worktree_status'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(probe(p.parse_args().output))
