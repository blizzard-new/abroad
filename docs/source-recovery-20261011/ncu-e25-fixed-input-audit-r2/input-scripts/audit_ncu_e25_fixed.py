"""Independently validate fixed NCU e25 Git blobs without changing the app tree."""
from pathlib import Path
import base64, collections, gzip, hashlib, io, json, subprocess, re, html
from PIL import Image, ImageDraw

SHA='e25ff02a1ebc69ea126a814d105e88b272539351'
PREV='f44eaf82a2a1133f1ba91466034ae6e8d7ebc822'
ROOT=Path('/workspace/recovery-evidence-20261011')
OUT=ROOT/'ncu-e25-reviewed-images'; OUT.mkdir(exist_ok=True)
def blob(p,sha=SHA): return subprocess.check_output(['git','show',sha+':'+p])
def obj(p,sha=SHA):
    b=blob(p,sha); return json.loads(gzip.decompress(b) if p.endswith('.gz') else b)
def source(p,sha=SHA):return obj('sources/ncu/2026-10-11/'+p,sha)
def digest(b):return hashlib.sha256(b).hexdigest()
pack_names=['resume-visual-sourcepack.json.gz','resume-second-sourcepack.json.gz','resume-discovery-sourcepack.json.gz','resume-third-photo-sourcepack.json.gz','resume-third-location-sourcepack.json.gz','resume-eivp-original-responses.json.gz']
byhash=collections.defaultdict(list);packs=[];raws=0;binary=0
for name in pack_names:
    rows=source(name)
    for r in rows:
        receipt=r['receipt']; assert receipt['status']==200, (name,receipt)
        byhash[receipt['sha256']].append(r)
        if 'raw_utf8' in r:
            assert digest(r['raw_utf8'].encode())==receipt['sha256']; raws+=1
        if 'raw_base64' in r:
            b=base64.b64decode(r['raw_base64']); assert digest(b)==receipt['sha256']; binary+=1
            (OUT/(r['source_id']+'.pdf')).write_bytes(b)
    packs.append({'name':name,'receipts':len(rows),'sha256':digest(blob('sources/ncu/2026-10-11/'+name))})
assets=obj('src/exchange_info/static/assets/ncu-school-images.json')['schools']
oldassets=obj('src/exchange_info/static/assets/ncu-school-images.json',PREV)['schools']
assert len(assets)==193 and len(oldassets)==146
prior_note_sanitization=[]
for a in oldassets:
    n=next(x for x in assets if x['school_name']==a['school_name'])
    assert {k:v for k,v in a.items() if k!='note'}=={k:v for k,v in n.items() if k!='note'}
    assert html.unescape(re.sub('<[^>]*>','',a['note']))==html.unescape(re.sub('<[^>]*>','',n['note']))
    if a!=n:prior_note_sanitization.append(a['school_name'])
photos={r['id']:r for r in source('campus-photo-reviews.json')['rows']}
decisions=[]
for name in ['resume-second-review.json','resume-discovery-review.json','resume-third-photo-review.json']:
    decisions.extend(source(name)['photo_decisions'])
assert len(decisions)==47
new=[]
for d in decisions:
    r=photos[d['id']]; b=blob(r['file']); h=digest(b)
    assert h==r['sha256']==d['sha256'] and h in byhash,r['id']
    im=Image.open(io.BytesIO(b));im.load();assert min(im.size)>=100
    assert r['http_status']==200 and r['review_status']=='accepted_campus_reference'
    md=json.loads(next(x['raw_utf8'] for x in byhash[r['commons_metadata_sha256']] if 'raw_utf8' in x))
    assert md==r['commons_metadata'];page=next(x for x in md['query']['pages'].values() if x['title']==r['title'])
    ext=page['imageinfo'][0]['extmetadata'];assert ext['LicenseShortName']['value']==r['license']
    assert r['author_html'] and (r['license_url'] or r['license']=='Public domain')
    a=next(x for x in assets if x['school_name']==r['school_name'])
    assert a['local_path']=='/'+r['file'].split('src/exchange_info/',1)[1]
    assert a['official_page_url']==r['page_url'] and a['license_name']==r['license']
    (OUT/(r['id']+'.jpg')).write_bytes(b)
    new.append({k:r.get(k) for k in ['id','school_name','country','title','page_url','license','license_url','author_html','photographed_at_original','review_note','sha256','attribution_resolution']}|{'dimensions':list(im.size),'metadata_artist':ext.get('Artist'),'metadata_description':ext.get('ImageDescription'),'canonical_source_rows':d.get('canonical_source_rows')})
for n in range((len(new)+7)//8):
    selected=new[n*8:(n+1)*8];canvas=Image.new('RGB',(1200,800),'white');draw=ImageDraw.Draw(canvas)
    for i,r in enumerate(selected):
        im=Image.open(OUT/(r['id']+'.jpg'));im.thumbnail((296,315));x=(i%4)*300;y=(i//4)*400;canvas.paste(im,(x,y));draw.text((x+3,y+318),r['id'],fill='black');draw.text((x+3,y+340),r['title'].replace('File:','')[:40],fill='black')
    canvas.save(OUT/f'contact-{n+1}.jpg')
locations=source('campus-locations.json')['locations'];assert locations==obj('src/exchange_info/official_data/ncu/campus-locations.json')['locations']
loc={r['school_name']:r for r in locations};oldloc={r['school_name']:r for r in source('campus-locations.json',PREV)['locations']}
coords=[];pending=[]
for name in ['resume-second-review.json','resume-discovery-review.json','resume-third-location-review.json']:
    for d in source(name)['coordinate_decisions']:
        p=d.get('published_record')
        if p is None:
            if 'pending' in d.get('decision',''):pending.append(d)
            continue
        assert p==loc[d['school_name']],d['school_name']
        receipt=d['source_receipt'];raw=next(x['raw_utf8'] for x in byhash[receipt['sha256']] if 'raw_utf8' in x)
        entity=json.loads(raw)['entities'][d['qid']]
        orig=d.get('original_P625',d.get('original_selected_P625'));assert orig
        for claim in orig:assert claim in entity['claims']['P625']
        for field,prop in [('original_P17','P17'),('original_P856','P856')]:
            if field in d:assert d[field]==entity['claims'].get(prop,[])
        points=[c['mainsnak']['datavalue']['value'] for c in orig if 'datavalue' in c['mainsnak'] and c['rank']!='deprecated']
        assert any(p['latitude']==q['latitude'] and p['longitude']==q['longitude'] for q in points)
        assert p['current_exchange_campus_confirmed'] is False and p['source_sha256']==receipt['sha256']
        coords.append({'file':name,'capture_row_id':d.get('capture_row_id'),'canonical_source_rows':d.get('canonical_source_rows'),'school_name':d['school_name'],'country':d['country'],'qid':d['qid'],'published_record':p,'entity_labels':entity.get('labels'),'entity_countries':[x['mainsnak'].get('datavalue',{}).get('value') for x in entity['claims'].get('P17',[])],'entity_websites':[x['mainsnak'].get('datavalue',{}).get('value') for x in entity['claims'].get('P856',[])],'selected_campus_qualifier':d.get('selected_campus_qualifier'),'identity_note':d.get('identity_note',d.get('reason'))})
protected=['src/exchange_info/official_data/ncu/partners.jsonl','src/exchange_info/official_data/ncu/application_workflows.jsonl','sources/ncu/2026-10-11/host-web-evidence.json.gz']
for p in protected:assert blob(p)==blob(p,PREV),p
changes=subprocess.check_output(['git','diff','--name-only',PREV,SHA],text=True).splitlines()
assert not any(p.startswith(('supabase/','.github/')) for p in changes)
all_photo_hashes=[]
for a in assets:
    path='src/exchange_info'+a['local_path'];b=blob(path);Image.open(io.BytesIO(b)).load();all_photo_hashes.append(digest(b))
report={'source_commit':SHA,'compared_to':PREV,'sourcepacks':packs,'sourcepack_receipts':sum(p['receipts'] for p in packs),'raw_text_bodies_hash_verified':raws,'embedded_PDF_bodies_hash_verified':binary,'all_193_photo_files_decoded':True,'unique_photo_hashes':len(set(all_photo_hashes)),'prior_146_images_and_license_fields_exactly_preserved':True,'prior_notes_html_sanitized_only':prior_note_sanitization,'new_photo_rows':new,'accepted_coordinate_rows':coords,'pending_coordinate_decisions':pending,'prior_location_count':len(oldloc),'new_location_count':len(loc),'protected_unchanged':protected,'migration_delta':[],'visual_and_identity_review_status':'pending; raw hash/metadata verification does not substitute for visual institution review'}
(ROOT/'ncu-e25-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['new_photo_rows','accepted_coordinate_rows','pending_coordinate_decisions']},ensure_ascii=False,indent=2))
