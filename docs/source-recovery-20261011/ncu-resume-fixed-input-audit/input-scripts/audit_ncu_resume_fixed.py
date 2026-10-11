"""Read fixed Git objects while the current integrated candidate remains frozen."""
from pathlib import Path
import collections,gzip,hashlib,io,json,subprocess
from PIL import Image,ImageOps,ImageDraw
SHA='f44eaf82a2a1133f1ba91466034ae6e8d7ebc822';PREV='358a72e7302476ba8dd19c47c35fc398fc205a47'
ROOT=Path('/workspace/recovery-evidence-20261011'); OUT=ROOT/'ncu-resume-reviewed-images';OUT.mkdir(exist_ok=True)
def blob(p,sha=SHA):return subprocess.check_output(['git','show',sha+':'+p])
def obj(p,sha=SHA):
 b=blob(p,sha);return json.loads(gzip.decompress(b) if p.endswith('.gz') else b)
review=obj('sources/ncu/2026-10-11/resume-visual-review.json');pack=obj('sources/ncu/2026-10-11/resume-visual-sourcepack.json.gz');bykey={r['local_evidence_key']:r for r in pack};byhash=collections.defaultdict(list)
raw_count=0
for row in pack:
 receipt=row['receipt'];assert receipt['status']==200
 byhash[receipt['sha256']].append(row)
 if 'raw_utf8' in row:
  assert hashlib.sha256(row['raw_utf8'].encode()).hexdigest()==receipt['sha256'],row['local_evidence_key'];raw_count+=1
locations=obj('sources/ncu/2026-10-11/campus-locations.json')['locations'];assert locations==obj('src/exchange_info/official_data/ncu/campus-locations.json')['locations']
loc={r['school_name']:r for r in locations};oldloc={r['school_name']:r for r in obj('sources/ncu/2026-10-11/campus-locations.json',PREV)['locations']}
coords=[]
for row in review['coordinate_decisions']:
 if row['decision']!='accepted_representative_point':continue
 published=row['published_record'];assert published==loc[row['school_name']]
 receipt=row['source_receipt'];raw=bykey['entities/'+row['row_id']+'/entity.json'];assert raw['receipt']==receipt
 entity=json.loads(raw['raw_utf8'])['entities'][row['qid']]
 assert row['original_P625']==entity['claims']['P625']
 pts=[r['mainsnak']['datavalue']['value'] for r in entity['claims']['P625'] if r['mainsnak'].get('datavalue') and r['rank']!='deprecated']
 assert any(published['latitude']==p['latitude'] and published['longitude']==p['longitude'] for p in pts)
 assert published['current_exchange_campus_confirmed'] is False and published['precision']=='representative'
 assert published['source_sha256']==receipt['sha256'] and row['ror_names'] and row['ror_domains']
 coords.append({k:row[k] for k in ['row_id','school_name','country','entity_label','ror_country','ror_domains']}|{'lat':published['latitude'],'lon':published['longitude'],'city':published['city'],'qid':row['qid'],'source_sha256':receipt['sha256']})
photo_rows=obj('sources/ncu/2026-10-11/campus-photo-reviews.json')['rows'];photos={r['id']:r for r in photo_rows};assets=obj('src/exchange_info/static/assets/ncu-school-images.json')['schools'];oldassets=obj('src/exchange_info/static/assets/ncu-school-images.json',PREV)['schools']
assert len(assets)==146 and len(oldassets)==125
for r in oldassets:assert r in assets,r['school_name']
new=[]
for decision in review['photo_decisions']:
 r=photos[decision['id']];b=blob(r['file']);digest=hashlib.sha256(b).hexdigest();assert digest==r['sha256']==decision['sha256'];assert digest in byhash
 im=Image.open(io.BytesIO(b));im.load();assert min(im.size)>=100
 assert r['review_status']=='accepted_campus_reference' and r['http_status']==200
 assert r['commons_metadata_sha256'] in byhash
 metadata=json.loads(next(x['raw_utf8'] for x in byhash[r['commons_metadata_sha256']] if 'raw_utf8' in x));assert metadata==r['commons_metadata']
 info=next(iter(metadata['query']['pages'].values()))['imageinfo'][0];ext=info['extmetadata'];assert ext['LicenseShortName']['value']==r['license']
 assert r['author_html'] and r['license_url'] and r['page_url']
 for key in r.get('attribution_resolution',{}).get('evidence_files',[]):assert key in bykey
 a=next(a for a in assets if a['school_name']==r['school_name']);assert a['local_path']=='/'+r['file'].split('src/exchange_info/',1)[1]
 assert a['license_name']==r['license'] and r['page_url']==a['official_page_url']
 (OUT/(r['id']+'.jpg')).write_bytes(b)
 new.append({k:r.get(k) for k in ['id','school_name','country','title','page_url','license','author_html','photographed_at_original','review_note','sha256','attribution_resolution']}|{'dimensions':list(im.size),'ext_artist':ext.get('Artist'),'description':ext.get('ImageDescription')})
for batch in range(3):
 selected=new[batch*7:(batch+1)*7];canvas=Image.new('RGB',(1000,720),'white');draw=ImageDraw.Draw(canvas)
 for i,r in enumerate(selected):
  im=Image.open(OUT/(r['id']+'.jpg'));im.thumbnail((245,295));x=(i%4)*250;y=(i//4)*360;canvas.paste(im,(x,y));draw.text((x+3,y+300),r['id'],fill='black');draw.text((x+3,y+318),r['title'].replace('File:','')[:34],fill='black')
 canvas.save(OUT/f'contact-{batch+1}.jpg')
home=obj('sources/ncu/2026-10-11/resume-home-location-evidence.json.gz')
for r in home['sources']:assert hashlib.sha256(r['raw_utf8'].encode()).hexdigest()==r['receipt']['sha256'] and r['receipt']['status']==200
shared=[json.loads(l) for l in blob('src/exchange_info/official_data/university_locations.jsonl','3129ce1bfcf6987a872574587cc53b60043d64ba').splitlines()];assert home['record'] in shared
protected=['src/exchange_info/official_data/ncu/partners.jsonl','src/exchange_info/official_data/ncu/application_workflows.jsonl','sources/ncu/2026-10-11/host-web-evidence.json.gz']
for p in protected:assert blob(p)==blob(p,PREV),p
changed=subprocess.check_output(['git','diff','--name-only',PREV,SHA],text=True).splitlines();assert not any(p.startswith(('supabase/','.github/')) for p in changed)
report={'source_commit':SHA,'compared_to':PREV,'sourcepack_receipts':len(pack),'raw_text_bodies_hash_verified':raw_count,'binary_receipts_checked_against_git_photos':len(new),'coordinate_decisions':dict(collections.Counter(r['decision'] for r in review['coordinate_decisions'])),'all_accepted_P625_and_published_payloads_exact':True,'accepted_coordinate_rows':coords,'old_location_count':len(oldloc),'new_location_count':len(loc),'old_official_pins':{k:v for k,v in oldloc.items() if 'wikidata' not in v.get('source_url','')},'photos_before':125,'photos_after':146,'new_photo_rows':new,'protected_unchanged':protected,'home_point_exactly_already_present':True,'migration_delta':[],'independent_visual_review':'pending separate contact-sheet and attribution inspection; hash evidence is not visual acceptance','source_limitations':'ROR names/domains are author identity assertions pending cross-check to retained prior ROR originals; no current-year exchange-campus assertion.'}
(ROOT/'ncu-resume-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['accepted_coordinate_rows','new_photo_rows','old_official_pins']},ensure_ascii=False,indent=2))
