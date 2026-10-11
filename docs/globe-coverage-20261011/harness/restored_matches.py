import json,pathlib,sys
sys.path.insert(0,str(pathlib.Path.cwd()))
sys.path.insert(0,str(pathlib.Path.cwd()/'src'))
from scripts.audit_visual_coverage import image_index
from exchange_info.school_identity import visual_identity_aliases,school_identity_key
R=pathlib.Path('/workspace/globe-evidence-20261011')
before=json.loads((R/'local-base-audit/report/coverage.json').read_text())
after=json.loads((R/'final-coverage-audit/report/coverage.json').read_text())
manifest=image_index(json.loads(pathlib.Path('src/exchange_info/static/assets/school-images.json').read_text())['schools'])
restored=[]
for b,a in zip(before['schools'],after['schools']):
 assert b['school_name']==a['school_name']
 assert len(b['records'])==len(a['records'])
 old_by_key={(r['school_name'],r['country']):r for r in b['records']}
 assert len(old_by_key)==len(b['records'])
 assert set(old_by_key)=={(r['school_name'],r['country']) for r in a['records']}
 for new in a['records']:
  old=old_by_key[(new['school_name'],new['country'])]
  if (new['expected_marker'] and not old['expected_marker']) or (new['api_photo_available'] and not old['api_photo_available']):
   photo=manifest.get((new['school_name'],new['country'])) or {}
   row={'home_school':a['school_name'],'partner':new['school_name'],'country':new['country'],'marker_restored':new['expected_marker'] and not old['expected_marker'],'photo_restored':new['api_photo_available'] and not old['api_photo_available'],'coordinate_source_record':new['location'],'photo_source_record':photo}
   restored.append(row)
   print(a['school_name'],new['school_name'],new['country'],'=>',new['location'].get('school_name') if row['marker_restored'] else '',photo.get('school_name') if row['photo_restored'] else '')
(R/'restored-visual-matches.json').write_text(json.dumps(restored,ensure_ascii=False,indent=2)+'\n')
print('restored rows',len(restored))
