import collections,gzip,hashlib,json,pathlib,re,subprocess
R=pathlib.Path('/workspace/abroad-pr5');O=pathlib.Path('/workspace/integration-evidence/pr5-source-audit-final');O.mkdir(exist_ok=True)
s=json.loads(gzip.decompress((R/'sources/ntu/destinations-2026-10-08.json.gz').read_bytes()));pages=json.loads(gzip.decompress((R/'sources/ntu/destination-pages-2026-10-08.json.gz').read_bytes()))
review=json.loads((R/'sources/ntu/photo-license-review-2026-10-09.json').read_text());pending={(r['school_name'],r['country']) for r in review['rows']}
photos=[r for r in s['photos'] if r['status']=='verified' and (r['school_name'],r['country']) not in pending]
assert len(photos)==266
for r in photos:
 assert r.get('license_name') and r['official_page_url'].startswith('https://commons.wikimedia.org/')
 assert hashlib.sha256((R/'src/exchange_info/static'/r['local_path'].split('?')[0].removeprefix('/static/')).read_bytes()).hexdigest()==r['content_hash']
 if r['license_name'].startswith('CC BY'):assert r.get('artist') and r.get('license_url')
workflow={}
for school,expected in [('cgu',154),('ntpu',409),('ntu',288)]:
 files=subprocess.check_output(['git','ls-tree','-r','--name-only','f6ad1b8','--',f'src/exchange_info/official_data/{school}'],cwd=R,text=True).splitlines()
 for p in files:assert (R/p).read_bytes()==subprocess.check_output(['git','show','f6ad1b8:'+p],cwd=R),p
 count=sum(len(p.read_text().splitlines()) for p in (R/f'src/exchange_info/official_data/{school}').glob('*application_workflows*.jsonl'))
 assert count==expected,(school,count);workflow[school]={'unchanged_files':len(files),'workflows':count}
norm=lambda x:re.sub(r'\s+',' ',x).strip()
rows=[]
for life in s['life']:
 for e in life['evidence']:
  text=e.get('original_text') or e['text'];sources=e['sources'];found=[]
  for x in sources:
   candidates=[(key,page) for key,page in pages.items() if key == x['url'] or page.get('final_url') == x['url']]
   for key,p in candidates:
    if norm(text) in norm(p.get('text','')):found.append({'url':x['url'],'snapshot_key':key,'checked_at_matches':str(e['checked_at']).replace('Z','+00:00')==str(p.get('checked_at'))})
  rows.append({'school':life['school_name'],'sources':[x['url'] for x in sources],'found':found,'scope':e.get('scope'),'checked_at':e.get('checked_at')})
assert all(r['scope'] and '116-1' in r['scope'] and r['checked_at'] for r in rows)
result={'candidate_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'licensed_photos':len(photos),'pending_permission':len(pending),'missing_campus':2,'license_counts':dict(collections.Counter(r['license_name'] for r in photos)),'workflow_parity':workflow,'life_excerpts':len(rows),'exact_normalized_source_matches':sum(bool(r['found']) for r in rows),'unmatched':[r for r in rows if not r['found']],'no_new_migration':subprocess.check_output(['git','diff','--name-only','f6ad1b8','HEAD','--','supabase/migrations'],cwd=R,text=True)==''}
(O/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'life-provenance.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='unmatched'},ensure_ascii=False));print('unmatched',len(result['unmatched']))
