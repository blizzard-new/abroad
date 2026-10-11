from pathlib import Path
import base64, gzip, hashlib, json, subprocess
from bs4 import BeautifulSoup

SHA='a1d6b7aa7539998613c44e9130e3915c7115bb38'
OLD='13a4afdc0e99cd5f9b4c66bca5bc426d68bdfd4b'
OUT=Path('/workspace/recovery-evidence-20261011/ncu-fifteenth-reviewed-images');OUT.mkdir(exist_ok=True)
def blob(path,sha=SHA): return subprocess.check_output(['git','show',sha+':'+path])
def obj(path,sha=SHA):
    data=blob(path,sha);return json.loads(gzip.decompress(data)if path.endswith('.gz')else data)
def digest(data):return hashlib.sha256(data).hexdigest()
base='sources/ncu/2026-10-11/'
prod='src/exchange_info/official_data/ncu/'
docs='docs/data/ncu-completion-20261011/resume/fifteenth/'
sources={s['id']:s for s in obj(prod+'source-evidence.json.gz')}
old_sources={s['id']:s for s in obj(prod+'source-evidence.json.gz',OLD)}
assert len(sources)==len(old_sources)+5
for sid,source in old_sources.items():assert sources[sid]['sha256']==source['sha256'],sid
manifest=obj(docs+'new-source-manifest.json');assert set(sources)-set(old_sources)==set(manifest['source_ids'])
responses=obj(base+'resume-fifteenth-original-responses.json.gz');assert len(responses)==24
receipts=[];body_map={}
for i,r in enumerate(responses):
    raw=base64.b64decode(r['raw_base64']);receipt=r['receipt']
    assert digest(raw)==receipt['sha256'],r['artifact']
    soup=BeautifulSoup(raw,'html.parser')
    for e in soup(['script','style','noscript']):e.decompose()
    text=soup.get_text('\n',strip=True)
    name=f'{i:02d}-'+Path(r['artifact']).stem+'.txt';(OUT/name).write_text(text)
    row={'artifact':r['artifact'],'text_file':name,'bytes':len(raw),'receipt':receipt};receipts.append(row)
    body_map.setdefault(receipt['sha256'],[]).append(row)
for sid in manifest['source_ids']:
    source=sources[sid];assert source['sha256'] in body_map,sid
    assert not source.get('current_116_applicability_verified',False),sid
ledger=obj(docs+'reading-ledger.json');assert len(ledger['rows'])==ledger['assessed_candidates']==223
assert len({r['id']for r in ledger['rows']})==223
assert ledger['original_bodies_selected_or_full_html_read']==205 and ledger['original_shell_bodies_not_read']==18
for r in ledger['rows']:
    assert r['id'] in sources and r['sha256']==sources[r['id']]['sha256'],r['id']
    assert r['url']==sources[r['id']]['url'],r['id']
old=obj(base+'reviewed-host-records.json',OLD);new=obj(base+'reviewed-host-records.json');assert set(old)==set(new)
changed={k:{'before':old[k],'after':v}for k,v in new.items()if old[k]!=v};assert len(changed)==7
assert new['ncu-081']==old['ncu-081'] and new['ncu-138']==old['ncu-138']
(OUT/'changed-host-records.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n')
(OUT/'field-reconciliation.json').write_text(json.dumps(obj(docs+'field-reconciliation.json'),ensure_ascii=False,indent=2)+'\n')
(OUT/'reading-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(OUT/'new-sources.json').write_text(json.dumps({k:sources[k]for k in manifest['source_ids']},ensure_ascii=False,indent=2)+'\n')
for path in ['supabase/migrations','.github/workflows','uv.lock','src/exchange_info/static','src/exchange_info/official_data/cgu','src/exchange_info/official_data/ntu','src/exchange_info/official_data/ntpu','src/exchange_info/official_data/ccu','src/exchange_info/official_data/tku',base+'campus-locations.json',base+'campus-photo-reviews.json',base+'document-conditions.json']:
    assert not subprocess.check_output(['git','diff','--name-only',OLD,SHA,'--',path]).strip(),path
partners=[json.loads(r)for r in blob(prod+'partners.jsonl').splitlines()];prior=[json.loads(r)for r in blob(prod+'partners.jsonl',OLD).splitlines()]
assert len(partners)==len(prior)==214
for a,b in zip(prior,partners):
    for key in ['school_name','country','quota','availability_status','academic_year','application_round']:assert a.get(key)==b.get(key)
    assert b.get('quota')is None and b['availability_status']=='agreement_only'
report={'source_sha':SHA,'compared_to':OLD,'new_sources':manifest['source_ids'],'all24_raw_response_hashes_verified':True,'receipts':receipts,'all223_original_ledger_ids_urls_hashes_match_packaged_sources':True,'old_source_body_hashes_unchanged':True,'changed_host_records':list(changed),'turku_meiji_incoming_rows_still_base':True,'photos_coordinates_sql_frontend_other_schools_document_conditions_unchanged':True,'all214_unknown_quota_agreement_only':True,'semantic_scope':'Byte/provenance check; independent semantic review is bounded and separately recorded. Does not inherit author full-reading claim.'}
Path('/workspace/recovery-evidence-20261011/ncu-fifteenth-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='receipts'},ensure_ascii=False))
