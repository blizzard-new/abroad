from pathlib import Path
import hashlib,json,subprocess,zipfile,io,re
from collections import Counter
from bs4 import BeautifulSoup
from exchange_info.ntu_completion import validate
from exchange_info.ntu_student_view import fetch_ntu_partner_universities
from exchange_info.tku_student_view import fetch_tku_partner_universities
from exchange_info.tku_census import census_audit
from scripts.verify_ntu_reviewed_source_archives import verify
from scripts.tku_capture_io import read_bytes,BUNDLE

root=Path.cwd();sources=root/'sources/ntu';snap=json.loads((sources/'completion-2026-10-11.json').read_text());manifest=json.loads((sources/'reviewed-source-bodies-current-manifest.json').read_text());entries={e['url']:e for e in manifest['entries']}
ntu=fetch_ntu_partner_universities();validate(snap,ntu)
photo_rows=[]
for row in snap['schools']:
 if not row.get('photo'):continue
 p=row['photo'];review=row['photo_review'];entry=entries.get(p['official_page_url']);proof=None
 if entry:
  with zipfile.ZipFile(sources/entry['archive_file']) as archive:body=archive.read(entry['archive_body_path'])
  assert hashlib.sha256(body).hexdigest()==entry['sha256']
  text=BeautifulSoup(body,'html.parser').get_text(' ',strip=True)
  assert p['artist'].lower() in text.lower(),row['school_name']
  if p['license_name'].startswith('CC BY'):assert p['license_url'].rstrip('/').replace('https:','').encode() in body
  elif p['license_name']=='CC0':assert 'CC0' in text
  elif p['license_name']=='Public domain':assert 'public domain' in text.lower()
  proof={'source_id':entry['source_id'],'sha256':entry['sha256'],'author_and_license_match':True}
 assert review['assigned_exchange_campus_confirmed'] is False
 assert review['official_school_identity_source']==row['portal_receipt']['url']
 photo_rows.append({'school_name':row['school_name'],'country':row['country'],'campus':review['campus_name'],'local_file_hash':p['content_hash'],'source_url':p['official_page_url'],'author':p['artist'],'license':p['license_name'],'archived_commons_body':proof,'review_scope':'named campus reference, not assigned exchange campus'})
tku=fetch_tku_partner_universities();audit=census_audit();pack=json.loads((BUNDLE/'capture_pack_manifest.json').read_text());checked=0;archive_parts=0
for archive in pack['archives']:
 digest=hashlib.sha256()
 for part in archive['parts']:
  data=(BUNDLE/'capture_packs'/part['file']).read_bytes();assert len(data)==part['bytes'];assert hashlib.sha256(data).hexdigest()==part['sha256'];digest.update(data);archive_parts+=1
 assert digest.hexdigest()==archive['sha256']
for name,record in pack['files'].items():
 assert hashlib.sha256(read_bytes(BUNDLE/name)).hexdigest()==record['sha256'];checked+=1
assert len(tku)==287 and sum(p.quota is None for p in tku)==283
assert all(p.availability_status!='open' for p in tku)
assert all(p.quota_status=='reference_only' and p.quota is None for p in tku[4:])
result={'sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'ntu_archives':verify(),
 'ntu_photos':photo_rows,'ntu_photo_summary':{'new_reviewed_photos':len(photo_rows),'archived_commons_bodies_independently_rechecked':sum(bool(p['archived_commons_body']) for p in photo_rows),'remaining_photos_scope':'first-stage source metadata, hash and identity review validated; no independent fresh Commons body retrieval claimed'},
 'ntu_selection':{'rows':len(ntu),'null_quota':sum(p.quota is None for p in ntu),'explicit_zero_quota':sum(p.quota=='0 名' for p in ntu),'all_current_cycle_fields_verified':snap['all_current_cycle_fields_verified'],'observations':sum(len(r['observations']) for r in snap['schools']),'new_batch_life_reference_schools':sum(bool(r['life_evidence']) for r in snap['schools']),'all_bundled_life_reference_schools':sum(bool(json.loads(line)['evidence']) for line in (root/'src/exchange_info/official_data/ntu/student_life.jsonl').read_text().splitlines())},
 'tku':{'institutions':len(tku),'programmes':audit['programme_count'],'availability':dict(Counter(p.availability_status for p in tku)),'quota_null':sum(p.quota is None for p in tku),'archive_parts':archive_parts,'source_members_all_hashes_verified':checked,'photos':audit['field_counts']['campus_photo'],'coordinates':audit['field_counts']['coordinates'],'not_full_current_cycle_acceptance':True},
 'migration_changes':subprocess.check_output(['git','diff','--name-only','59a20f2','HEAD','--','supabase/migrations'],text=True).splitlines()}
assert archive_parts==18 and checked==3616
assert len(entries)==345 and len({e['archive_file'] for e in entries.values()})==12
assert result['ntu_selection']['observations']==433
assert result['ntu_selection']['all_bundled_life_reference_schools']==272
out=Path('/workspace/recovery-evidence-20261011/ccu2-delivery-audit.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='ntu_photos'},ensure_ascii=False,indent=2))
