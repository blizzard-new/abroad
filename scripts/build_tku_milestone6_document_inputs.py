import json,gzip
from tku_capture_io import BUNDLE,read_bytes
idx={r['id']:r for r in json.loads((BUNDLE/'host_census_capture_index.json').read_text())};chosen=[]
for e in idx['tku-sister-33']['sources']:
 s=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz'))))
 for l in s.get('links',[]):
  if l['title'] in {'2027 Spring Application Instructions for Exchange Program (English)','交換留学プログラムファクトシート'}:
   if not any(c['url']==l['url'] for c in chosen):chosen.append(dict(ordinal=len(chosen)+1,institution_id='tku-sister-33',url=l['url'],label=l['title'],linked_from=s['source_url'],source_id=s['id'],purpose='official_binary_content_year_review',reason='Read actual instructions and factsheet; no filename-only year inference; current home applicability unverified'))
for e in idx['tku-sister-39']['sources']:
 s=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz'))))
 for l in s.get('links',[]):
  if l['url']=='https://www.u-aizu.ac.jp/osip/en/information/icrp-app.html' and not any(c['url']==l['url'] for c in chosen):chosen.append(dict(ordinal=len(chosen)+1,institution_id='tku-sister-39',url=l['url'],label=l['title'],linked_from=s['source_url'],source_id=s['id'],purpose='specific_incoming_rule_body',reason='Actual programme announced at center; stop after this body and needed directly linked forms'))
assert len(chosen)==3,len(chosen)
(BUNDLE/'milestone6_final_document_inputs.json').write_text(json.dumps(dict(base_commit='4f142ea36e69338d2956b4ea5d3d37a9f4116e52',checked_date='2026-10-11',input_count=len(chosen),candidates=chosen,scope='Only2actual AGU binaries and1actual Aizu ICRP rule in original42; no new institutions or failed-route retries'),ensure_ascii=False,indent=2)+'\n');print('final documents',len(chosen),[c['url'] for c in chosen])
