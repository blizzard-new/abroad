import json,pathlib,collections
r=pathlib.Path('/workspace/globe-evidence-20261011')
changes=collections.Counter();details=[]
for p in (r/'local-base-export/snapshots').glob('*-dashboard.json'):
 old=json.loads(p.read_text());new=json.loads((r/'final-export/snapshots'/p.name).read_text());b={(x['school_name'],x['country']):x for x in old['partner_universities']};a={(x['school_name'],x['country']):x for x in new['partner_universities']};assert b.keys()==a.keys()
 for key in b:
  fields=[field for field in set(b[key])|set(a[key]) if b[key].get(field)!=a[key].get(field)]
  changes.update(fields)
  if fields:details.append({'home_school':old['school_name'],'partner':key,'changed_fields':sorted(fields)})
allowed={'location','image_url','image_alt','image_status','image_page_url','image_source_url','city'}
assert not (set(changes)-allowed),(set(changes)-allowed)
result={'comparison':'local main59 vs candidate992, identical bundled input','allowed_visual_fields':sorted(allowed),'changed_field_counts':dict(changes),'nonvisual_partner_fields_value_equal':True,'details':details}
(r/'controlled-partner-field-preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='details'},ensure_ascii=False,indent=2))
