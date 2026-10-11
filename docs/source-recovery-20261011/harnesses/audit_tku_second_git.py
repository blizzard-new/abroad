"""Immutable TKU second-batch assets and capture packs; contact sheets for review."""
from pathlib import Path
from collections import Counter
import hashlib, io, json, subprocess, zipfile
from PIL import Image, ImageDraw, ImageFont

sha='88bd00531d9a77fb98ba54dbfd8786cbde18db96'
base='f4819dab2db22507ad8978800aeabbcb9f598294'
prefix='src/exchange_info/official_data/tku/'
def blob(path, head=sha):return subprocess.check_output(['git','show',head+':'+path])
def obj(path, head=sha):return json.loads(blob(path,head))
photos=obj(prefix+'campus_asset_manifest.json');locations=obj(prefix+'campus_location_manifest.json')
audit=obj(prefix+'full_census_audit.json');schools={r['id']:r for r in audit['schools']}
assert len(schools)==287 and len(photos)==264 and len(locations)==260
assert len({p['id'] for p in photos})==264 and len({p['id'] for p in locations})==260
allowed={'CC BY 2.0','CC BY 2.5','CC BY 3.0','CC BY 4.0','CC BY-SA 2.0','CC BY-SA 2.5','CC BY-SA 3.0','CC BY-SA 4.0','CC0','Public domain'}
root=Path('/workspace/recovery-evidence-20261011/tku-second-contact-images');root.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',13)
summary=[];sheets=[];sheet=None
for i,p in enumerate(photos):
    row=schools[p['id']]
    assert p['school_name']==row['school_name'] and p['country']==row['country'],p['id']
    assert p['license'] in allowed and p['license_url'] and p['author'] and p['identity_source_url'],p['id']
    raw=blob('src/exchange_info/'+p['local_path'].split('?')[0].lstrip('/'))
    assert len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256'],p['id']
    assert p['review_status']=='verified_asset' and p['visual_review']['sha256']==p['sha256']
    with Image.open(io.BytesIO(raw)) as image:
        image.load();size=image.size;thumb=image.convert('RGB');thumb.thumbnail((190,125))
    if i%48==0:
        if sheet is not None:
            path=root/f'contact-{len(sheets)+1:02}.jpg';sheet.save(path,quality=90);sheets.append(str(path))
        sheet=Image.new('RGB',(1200,1440),'white');draw=ImageDraw.Draw(sheet)
    x=(i%6)*200;y=((i%48)//6)*180
    sheet.paste(thumb,(x+(200-thumb.width)//2,y))
    draw.text((x+3,y+127),f'{i+1:03} {p["id"]}',fill='black',font=font)
    draw.text((x+3,y+145),p['school_name'][:13],fill='black',font=font)
    draw.text((x+3,y+161),p['country'][:10],fill='black',font=font)
    summary.append({'id':p['id'],'school_name':p['school_name'],'country':p['country'],'sha256':p['sha256'],'actual_dimensions':size,'declared_dimensions':[p['width'],p['height']],'license':p['license'],'author':p['author'],'source_url':p['source_url'],'campus_pair_mismatch':bool(p.get('campus_pair_mismatch'))})
path=root/f'contact-{len(sheets)+1:02}.jpg';sheet.save(path,quality=90);sheets.append(str(path))
for p in locations:
    assert p['id'] in schools and p['verification_status']=='verified_asset'
    loc=p['location'];assert -90<=loc['latitude']<=90 and -180<=loc['longitude']<=180
    assert loc['geocode_status']=='verified' and loc['source_url'] and loc['identity_source_url'] and loc['note']
assert Counter(p['location']['precision'] for p in locations)=={'campus':5,'representative':255}
pack=obj(prefix+'capture_pack_manifest.json');old=obj(prefix+'capture_pack_manifest.json',base)
assert all(pack['files'][name]==r for name,r in old['files'].items())
checked=set();parts=0
for arc in pack['archives']:
    content=bytearray()
    for part in arc['parts']:
        raw=blob(prefix+'capture_packs/'+part['file']);assert len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'];content.extend(raw);parts+=1
    assert hashlib.sha256(content).hexdigest()==arc['sha256']
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert archive.testzip() is None
        for name,r in pack['files'].items():
            if r['archive']!=arc['file']:continue
            raw=archive.read(name);assert hashlib.sha256(raw).hexdigest()==r['sha256'];checked.add(name)
assert len(checked)==3616 and parts==18
other_changes=subprocess.check_output(['git','diff','--name-only',base,sha,'--',*[f'src/exchange_info/official_data/{h}' for h in ('cgu','ntpu','ntu','ccu','ncu')]],text=True).strip()
assert not other_changes
report={'source_commit':sha,'compared_to':base,'photos':264,'photos_reused':sum(p.get('acquisition_status')=='reused_baseline_asset' for p in photos),'locations':260,'location_precision':dict(Counter(p['location']['precision'] for p in locations)),'capture_members_verified':len(checked),'capture_parts_verified':parts,'previous_2576_members_preserved':len(old['files'])==2576,'five_other_school_data_unchanged':True,'contact_sheets':sheets,'assets':summary,'scope':'All asset bytes, decode, row identity and declared attribution metadata verified. Contact sheets require separate visual review; metadata presence alone does not independently confirm the upstream license.'}
Path('/workspace/recovery-evidence-20261011/tku-second-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='assets'},ensure_ascii=False,indent=2))
