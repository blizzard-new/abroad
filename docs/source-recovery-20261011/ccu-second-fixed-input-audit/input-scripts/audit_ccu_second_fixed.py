"""Independent fixed-input receipts, identity, assets and compatibility audit."""
from pathlib import Path
from collections import Counter
import gzip, hashlib, json, subprocess
from bs4 import BeautifulSoup
from PIL import Image
from exchange_info.ccu_completion_sources import validate_completion_source

app=Path('/workspace/abroad-globe-20261011')
root=Path('/workspace/ccu-second-fixed-review-20261011')
bundle=root/'src/exchange_info/official_data/ccu'
sha='ebe059fc317bf1cb55a0604b3ce354fe6fa12939'
before='cf4d86f22d89ee698315d46177daf00b49dd8706'
def git(*args):return subprocess.check_output(['git',*args],cwd=app)
def original(name):return json.loads(git('show',before+':src/exchange_info/official_data/ccu/'+name))
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

git_files=[]
for line in git('ls-tree','-r',sha,'--','src/exchange_info/official_data/ccu','src/exchange_info/static/assets/ccu/campuses').decode().splitlines():
    meta,name=line.split('\t');mode,kind,blob=meta.split();assert kind=='blob'
    file=root/name;body=file.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob,name
    git_files.append({'path':name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
rows=json.loads((bundle/'completion-reviewed-fields.json').read_text())['schools']
old={r['ccu_page']:r for r in original('completion-reviewed-fields.json')['schools']}
assert len(rows)==len(old)==104
checked={};states=Counter();overrides={}
for row in rows:
    previous=old[row['ccu_page']]
    for key in ['school_name','country','availability_status','application_window_status']:
        assert row[key]==previous[key],(row['ccu_page'],key)
    assert row['application_window_status']=='closed'
    assert not set(row.get('host_override_keys',[]))-set(row['host_fields'])
    if row.get('host_override_keys'):overrides[str(row['ccu_page'])]=row['host_override_keys']
    for group in ['general_campus_fields','host_fields','profile_fields']:
        for field in row[group].values():
            if group=='host_fields':states[field['status']]+=1
            if field['status']=='missing':assert field['value'] is None
            if field['value']:assert field['evidence']
            for ev in field['evidence']:validate_completion_source(bundle,ev,checked)
assets=json.loads((bundle/'campus-assets.json').read_text())['schools']
old_assets={r['ccu_page']:r for r in original('campus-assets.json')['schools']}
photos=[];coordinates=[];new_photos=[];new_coordinates=[];coordinate_changes=[]
for row in assets:
    page=row['ccu_page'];assert row['school_name']==old_assets[page]['school_name']
    for key in ['coordinates','photo']:
        for ev in row[key]['evidence']:validate_completion_source(bundle,ev,checked)
    photo=row['photo']['value']
    if photo:
        file=root/'src/exchange_info'/photo['local_path'].removeprefix('/')
        assert digest(file)==photo['sha256']
        with Image.open(file) as im:assert im.size==(photo['width'],photo['height']);im.verify()
        photos.append(page)
        old_photo=old_assets[page]['photo']['value']
        if old_photo:
            for key in ['sha256','artist','license_name','license_url','source_page_url']:assert photo[key]==old_photo[key]
        else:
            matches=[]
            for ev in row['photo']['evidence']:
                receipt=json.loads((bundle/'completion_sources'/f"{ev['source_id']}.receipt.json").read_text())
                file=bundle/receipt['bundled_file']
                body=gzip.decompress(file.read_bytes()) if file.suffix=='.gz' else file.read_bytes()
                try:api=json.loads(body)
                except (ValueError,UnicodeDecodeError):continue
                for item in api.get('query',{}).get('pages',{}).values():
                    for info in item.get('imageinfo',[]):
                        ext=info.get('extmetadata',{})
                        author=BeautifulSoup(ext.get('Artist',{}).get('value',''),'html.parser').get_text(' ',strip=True)
                        if author==photo['artist'] and ext.get('LicenseShortName',{}).get('value')==photo['license_name'] and ext.get('LicenseUrl',{}).get('value','').rstrip('/')==photo['license_url'].rstrip('/'):
                            matches.append({'title':item.get('title'),'source_id':ev['source_id'],'author':author,'license':photo['license_name']})
            assert matches,(page,'Commons author/license not independently matched')
            new_photos.append({'page':page,'school_name':row['school_name'],'photo':photo,'commons_matches':matches})
    coordinate=row['coordinates']['value']
    if coordinate:
        assert -90<=coordinate['latitude']<=90 and -180<=coordinate['longitude']<=180
        assert coordinate['school_name']==row['school_name'] and coordinate['country']==row['country']
        coordinates.append(page)
        old_coordinate=old_assets[page]['coordinates']['value']
        if old_coordinate is None:new_coordinates.append({'page':page,'school_name':row['school_name'],'coordinates':row['coordinates']})
        elif any(coordinate[k]!=old_coordinate[k] for k in ['latitude','longitude']):coordinate_changes.append(page)
assert len(photos)==100 and len(coordinates)==100 and len(new_photos)==3 and len(new_coordinates)==5
assert not coordinate_changes
assert states['missing']==643
protected=[f'src/exchange_info/official_data/{school}' for school in ['cgu','ntpu','ntu','ncu','tku']]
protected+=['supabase/migrations','uv.lock','.github/workflows','src/exchange_info/official_data/university_locations.jsonl','src/exchange_info/static/assets/school-images.json','src/exchange_info/official_data/ccu/partners.jsonl','src/exchange_info/official_data/ccu/application_workflows.jsonl']
assert not git('diff','--name-only',before,sha,'--',*protected).strip()
profiles=(bundle/'destination_profiles.jsonl').read_bytes().splitlines(keepends=True)
assert hashlib.sha256(b''.join(profiles[:55])).hexdigest()=='1375f32052bcdeaedfe696073e7ada6d40f40bdebeba0dc1e7f82353e38b78e6'
report={'source_commit':sha,'baseline':before,'verified_git_files':len(git_files),'all_files':git_files,'identities':104,'primary_source_receipt_hashes_verified':len(checked),'host_status_counts':dict(states),'host_override_keys':overrides,'licensed_photos':len(photos),'coordinates':len(coordinates),'new_photos':new_photos,'new_coordinates':new_coordinates,'old_coordinate_positions_changed':coordinate_changes,'old_97_photo_hash_attribution_unchanged':True,'original_55_profile_prefix_unchanged':True,'protected_paths_unchanged':protected,'website_identity_scope':'Author102 profile identities =98 campus reviews +4 existing document identities; not a claim of102 freshly read websites.','full_current_data_acceptance':False,'remaining':{'photos':4,'coordinates':4,'websites':2,'host_missing_fields':643,'global_agreements':None},'visual_new_photo_review':'pending independent inspection; see followup evidence','official_marker_review':'pending independent receipt/marker inspection; see followup evidence'}
out=Path('/workspace/recovery-evidence-20261011/ccu-second-fixed-input-audit.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['all_files','new_photos','new_coordinates']},ensure_ascii=False,indent=2))
