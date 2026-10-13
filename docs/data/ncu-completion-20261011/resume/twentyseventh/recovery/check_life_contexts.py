from pathlib import Path
from datetime import datetime, timezone
import json, gzip, tempfile, collections
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities

W = Path('/workspace/ncu-resume-work/twentyseventh')
client = TestClient(create_app(Path(tempfile.mkdtemp(prefix='ncu16-local-check-'))))
contexts, pending = [], []
for i, partner in enumerate(fetch_ncu_partner_universities()):
    res = client.get('/school-life-context', params={'school': partner.school_name, 'home_school': 'NCU'})
    res.raise_for_status()
    body = res.json()
    contexts.append(body)
    for card in body['categories']:
        for evidence in card['evidence']:
            if evidence['translation_status'] == 'pending':
                pending.append({'school_name': partner.school_name, 'theme': card['theme'], 'evidence': evidence})
    if (i+1) % 40 == 0:
        print({'checked': i+1, 'pending_evidence': len(pending)}, flush=True)
report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'partners': len(contexts),
    'pending_evidence_rows': len(pending), 'pending_cards': len({(x['school_name'], x['theme']) for x in pending}),
    'affected_partners': len({x['school_name'] for x in pending}), 'items': pending}
(W / 'life-contexts-after.json.gz').write_bytes(gzip.compress(json.dumps(contexts, ensure_ascii=False).encode(), mtime=0))
(W / 'pending-chinese-cards-after.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print({k: v for k, v in report.items() if k != 'items'}, flush=True)
