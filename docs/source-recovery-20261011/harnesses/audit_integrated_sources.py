"""Offline hash/denominator audit. No collectors, writes to source data or network."""
from collections import Counter
import gzip, hashlib, json, re
from pathlib import Path
import subprocess

from exchange_info.ccu_campus_assets import reviewed_assets
from exchange_info.ccu_completion import reviewed_completion
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.ncu_student_view import fetch_ncu_partner_universities
from exchange_info.ntu_student_view import fetch_ntu_partner_universities

root=Path.cwd();pkg=root/'src/exchange_info';bundle=pkg/'official_data/ccu'
assets, completion=reviewed_assets(),reviewed_completion()
receipts=Counter();response_bytes=0
for path in sorted((bundle/'completion_sources').glob('*.receipt.json')):
 row=json.loads(path.read_text()); relative=row.get('bundled_file')
 if relative:
  raw=(bundle/relative).read_bytes()
  if relative.endswith('.gz'):
   assert hashlib.sha256(raw).hexdigest()==row['stored_sha256'],path
   raw=gzip.decompress(raw)
  assert hashlib.sha256(raw).hexdigest()==row['sha256'],path
  response_bytes+=len(raw);receipts['original_bodies_verified']+=1
 else:receipts['without_body']+=1
 receipts['total']+=1
 receipts['http200' if row.get('http_status')==200 else 'http_other_or_failed']+=1
ncu_assets=json.loads((pkg/'official_data/ncu/campus-assets.json').read_text())['photos']
for row in ncu_assets:
 file=pkg/row['image_url'].removeprefix('/')
 assert hashlib.sha256(file.read_bytes()).hexdigest()==row['content_sha256'],file
 assert all(row.get(k) for k in ('author','license','license_url','image_page_url','identity_source_url','photographed_at_original','caption_zh'))
 if row['license'] == 'Public domain':
  assert row['license_url'] == row['image_page_url']
 elif row['license'] == 'CC0':
  assert row['license_url'].replace('http://','https://').startswith('https://creativecommons.org/publicdomain/zero/1.0')
 else:
  license_match=re.fullmatch(r'CC BY(-SA)? (1\.0|2\.0|2\.5|3\.0|4\.0)(?: ([a-z]{2}))?',row['license'])
  assert license_match,row['license']
  slug='by-sa' if license_match[1] else 'by'
  expected=f'https://creativecommons.org/licenses/{slug}/{license_match[2]}' + ('/'+license_match[3] if license_match[3] else '')
  assert re.sub(r'/deed\.[a-zA-Z_-]+/?$', '', row['license_url'].replace('http://','https://')).rstrip('/') == expected,(row['school_name'],row['license_url'],expected)
ccu,ncu,ntu=fetch_ccu_partner_universities(),fetch_ncu_partner_universities(),fetch_ntu_partner_universities()
assert len(ccu)==104 and len(ncu)==214 and len(ntu)==288
assert all(p.quota is None and p.availability_status=='agreement_only' for p in ncu)
old=subprocess.check_output(['git','show','59a20f2:src/exchange_info/official_data/ccu/destination_profiles.jsonl'])
assert (bundle/'destination_profiles.jsonl').read_bytes().startswith(old)
for school in ('cgu','ntpu','ntu'):
 p=f'src/exchange_info/official_data/{school}/application_workflows.jsonl'
 assert (root/p).read_bytes()==subprocess.check_output(['git','show','f6ad1b8:'+p])
result={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'mode':'offline_hash_and_status_validation_not_fresh_research',
 'ccu':{'displayed_identities':len(ccu),'global_agreement_denominator':None,'availability':dict(Counter(p.availability_status for p in ccu)),
 'quota_status':dict(Counter(p.quota_status for p in ccu)),'source_receipts':dict(receipts),'original_response_bytes_verified':response_bytes,
 'photo_license_distribution':dict(Counter(r['photo']['value']['license_name'] for r in assets.values() if r['photo']['status']=='verified_current')),
 'coordinates':sum(r['coordinates']['status']=='verified_current' for r in assets.values()),'photos':sum(r['photo']['status']=='verified_current' for r in assets.values()),
 'host_field_states':dict(Counter(f['status'] for r in completion.values() for f in r['host_fields'].values()))},
 'ncu':{'displayed_items':len(ncu),'quota_null':sum(p.quota is None for p in ncu),'availability':dict(Counter(p.availability_status for p in ncu)),
 'verified_photo_bytes_and_attribution':len(ncu_assets),'license_distribution':dict(Counter(r['license'] for r in ncu_assets)),
 'next_eight_schools_23_sources_included':False,'current_host_full_verification':0},
 'ntu':{'displayed_items':len(ntu),'quota_null':sum(p.quota is None for p in ntu),'quota_zero':sum(p.quota=='0 名' for p in ntu),'pr9_original_source_delivery_gap':'still_open_at_4566f7f; separate read-only review retained'},
 'workflow_parity_original':{'cgu':154,'ntpu':409,'ntu':288},'production_actions':[]}
out=Path('/workspace/recovery-evidence-20261011/integrated-source-audit.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
