import json,gzip
from tku_capture_io import BUNDLE,read_bytes
idx={r['id']:r for r in json.loads((BUNDLE/'host_census_capture_index.json').read_text())}
chosen={33:['https://www.aoyama.ac.jp/wp-content/uploads/2024/07/2_AGU-Exchange-Program-Pledge-Signature-page.pdf','https://www.aoyama.ac.jp/wp-content/uploads/2024/12/Health-Certificate.pdf'],39:['https://u-aizu.ac.jp/osip/information/ay2027_spring_sas_1_course_selection_form.xlsx','https://u-aizu.ac.jp/osip/information/ay2027_spring_sas_2_4_common.docx']};candidates=[]
for n,urls in chosen.items():
 id='tku-sister-'+str(n);sources=[json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz')))) for e in idx[id]['sources']]
 for u in urls:
  s,l=next((s,l) for s in sources for l in s.get('links',[]) if l['url']==u);candidates.append(dict(ordinal=len(candidates)+1,institution_id=id,url=u,label=l.get('title',''),linked_from=s['source_url'],source_id=s['id'],purpose='public_linked_template_content',reason='Final2public templates/school; Aizu explicitly password-protected Packet/Checklist not requested; no current home document promotion'))
(BUNDLE/'milestone6_template_inputs.json').write_text(json.dumps(dict(base_commit='4f142ea36e69338d2956b4ea5d3d37a9f4116e52',checked_date='2026-10-11',input_count=len(candidates),candidates=candidates,scope='Final4 public templates; bounded per named pass; no further network expansion after these'),ensure_ascii=False,indent=2)+'\n');print('templates',len(candidates))
p=BUNDLE/'milestone6_official_inputs.json';d=json.loads(p.read_text());d['scope']['followup_limit']='Only actual relevant public links within frozen institutions; at most2sources/school in each named bounded pass; each final pass frozen before requests; no new institutions';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
