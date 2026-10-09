"""Identical synthetic HTTP capture on an exact, clean before or after checkout."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--expected-sha',required=True);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();root=args.root.resolve()
sys.path.insert(0,str(root/'src'));sys.path.insert(0,str(root/'tests'))
from fastapi.testclient import TestClient
from exchange_info import api
from exchange_info.storage import ensure_data_dirs,load_community_posts,load_anonymous_identities
from test_community_permissions import _account,_post_payload

def state():
    return dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        dirty=subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip())

before=state();assert before==dict(commit=args.expected_sha,dirty='')
assert Path(api.__file__).resolve()==root/'src/exchange_info/api.py'
records=[]
def record(label,method,path,response,body=None):
    records.append(dict(label=label,request=dict(method=method,path=path,json=body,
        authentication='synthetic owner bearer; value omitted' if label.startswith('owner') else 'guest without credentials'),
        response=dict(status=response.status_code,
            headers={k:v for k,v in response.headers.items() if k.lower() in {'content-type','cache-control','vary'}},
            raw_body=response.content.decode('utf-8'),json=response.json() if response.content else None)))
    return response

data=Path(tempfile.mkdtemp(prefix='tku-raw-privacy-',dir='/tmp'));ensure_data_dirs(data)
started=datetime.now(timezone.utc).isoformat()
with TestClient(api.create_app(data)) as client:
    backends={name:getattr(getattr(client.app.state,name),'backend_name',None)
        for name in ['account_repository','community_repository']}
    assert set(backends.values())=={'jsonl'},backends
    _,headers,identity=_account(data,client,'合成驗收姓名',home_university='淡江大學')
    normal=_post_payload('公共留學板',identity_mode='real_name')
    post=record('owner normal post','POST','/community/posts',client.post('/community/posts',headers=headers,json=normal),normal)
    post_id=post.json()['id']
    body={'body':'合成留言資料','identity_mode':'real_name'}
    record('owner comment','POST',f'/community/posts/{post_id}/comments',client.post(f'/community/posts/{post_id}/comments',headers=headers,json=body),body)
    record('guest initial feed','GET','/community/posts?school=公共留學板',client.get('/community/posts',params={'school':'公共留學板'}))
    record('guest post detail','GET',f'/community/posts/{post_id}',client.get(f'/community/posts/{post_id}'))
    body=_post_payload('公共留學板',body='合成護照號碼：A12345678，僅供隔離測試。')
    sensitive=record('owner sensitive post','POST','/community/posts',client.post('/community/posts',headers=headers,json=body),body)
    guest=record('guest feed after sensitive post','GET','/community/posts',client.get('/community/posts'))
    sensitive_id=sensitive.json().get('id')
    guest_sensitive=[r for r in guest.json() if r['post']['id']==sensitive_id]
    deleted=record('owner account delete','DELETE','/auth/me',client.delete('/auth/me',headers=headers))
    after_feed=record('guest feed after account delete','GET','/community/posts',client.get('/community/posts'))
    retained=[r for r in after_feed.json() if r['post']['id']==post_id]
    stored=[r.model_dump(mode='json') for r in load_community_posts(data) if r.id==post_id]
    identities=[dict(id=r.id,account_id=r.account_id) for r in load_anonymous_identities(data) if r.id==identity['id']]
result=dict(tested_commit=args.expected_sha,starting_state=before,ending_state=state(),
    api_module=str(Path(api.__file__).resolve()),api_module_sha256=hashlib.sha256(Path(api.__file__).read_bytes()).hexdigest(),
    capture_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),started_at=started,
    ended_at=datetime.now(timezone.utc).isoformat(),synthetic_only=True,production_database_access=False,
    repository_backends=backends,isolated_data_directory=str(data),
    raw_http=records,observed=dict(sensitive_status=sensitive.status_code,
        sensitive_moderation_status=sensitive.json().get('status'),sensitive_guest_rows=guest_sensitive,
        delete_status=deleted.status_code,post_delete_guest_rows=retained,post_delete_stored_posts=stored,
        post_delete_linked_identity_rows=identities),
    interpretation='Own POST IDs and guest GET IDs are separately retained. Synthetic A12345678 and names are test data. No raw session/identity credentials are exported.')
result['candidate_guard_passed']=result['starting_state']==result['ending_state'] and not before['dirty']
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert result['candidate_guard_passed']
print(json.dumps(dict(tested_commit=args.expected_sha,candidate_guard_passed=True,
    sensitive_status=sensitive.status_code,sensitive_moderation_status=sensitive.json().get('status'),
    sensitive_guest_rows=len(guest_sensitive),delete_status=deleted.status_code,
    post_delete_names=[r['post']['display_name'] for r in retained]),ensure_ascii=False))
