"""Bind independently read fifth NCU sources to published asset decisions."""
from pathlib import Path
import json,subprocess,hashlib,re,urllib.parse,datetime
from bs4 import BeautifulSoup
root=Path('/workspace/recovery-evidence-20261011');images=root/'ncu-fifth-reviewed-images'
sha='baf98c0df400ef96aa83fb587107eb22513c0b97'
def obj(name):return json.loads(subprocess.check_output(['git','show',sha+':sources/ncu/2026-10-11/'+name]))
audit=json.loads((root/'ncu-fifth-fixed-input-audit.json').read_text())
metadata=json.loads((root/'ncu-fifth-new-photo-source-fields.json').read_text())
photo_results=[]
for p in audit['new_photos']:
 title=urllib.parse.unquote(p['image_page_url'].split('/wiki/')[1]).replace('_',' ')
 if title in metadata:
  source=metadata[title]['metadata'];assert source['Artist']==p['author'];assert source['LicenseShortName']==p['license']
  photo_results.append({'school':p['school_name'],'sha256':p['content_sha256'],'source_artist':source['Artist'],'license':p['license'],'source_date':source['DateTimeOriginal'],'source_description':source['ImageDescription'],'independently_viewed':True})
 else:
  assert p['license'] in ['FAL','Copyrighted free use']
  match=next(r for r in audit['nonCC_grants'] if r['school_name']==p['school_name']);assert match['proof']['image_sha256']==p['content_sha256']
  photo_results.append({'school':p['school_name'],'sha256':p['content_sha256'],'license':p['license'],'original_author_declaration_terms_and_upload_history_read':True,'independently_viewed':True})
decisions={r['capture_row_id']:r for r in obj('resume-fourth-location-review.json')['coordinate_decisions']}
decisions.update({r['capture_row_id']:r for r in obj('resume-fifth-location-review.json')['coordinate_decisions']})
for sid,filename in [('ncu-042','entities_ncu-042_entity.json'),('ncu-060','entities_ncu-060_entity.json'),('ncu-179','entity-discovery_ncu-179_entity.json'),('ncu-212','entity-discovery_ncu-212_entity.json')]:
 entity=next(iter(json.loads((images/(filename+'.raw')).read_bytes())['entities'].values()))
 if sid=='ncu-042':claims=[c['mainsnak']['datavalue']['value'] for c in entity['claims']['P625'] if c['rank']=='preferred'];assert len(claims)==1
 elif sid=='ncu-060':claims=[c['mainsnak']['datavalue']['value'] for c in entity['claims']['P625']];assert len(claims)==1
 else:
  claims=[c['qualifiers']['P625'][0]['datavalue']['value'] for c in entity['claims']['P159'] if 'P625' in c.get('qualifiers',{}) and 'P6375' in c.get('qualifiers',{})];assert len(claims)==1
 r=decisions[sid]['published_record'];assert (r['latitude'],r['longitude'])==(claims[0]['latitude'],claims[0]['longitude'])
 source=(images/(filename+'.raw')).read_bytes();assert hashlib.sha256(source).hexdigest()==r['source_sha256']
r=decisions['ncu-084']['published_record'];assert abs(r['latitude']-(41+33/60+33.8/3600))<1e-10 and abs(r['longitude']+(8+23/60+54.3/3600))<1e-10
text=(images/'fourth-location-support_minho-official-gps_page.html.txt').read_text();assert 'Gualtar' in text and "41°33 '33.8'' N" in text and "8°23'54.3'' W" in text
html=(images/'fifth-support_hiroshima-higashi.html.raw').read_bytes();soup=BeautifulSoup(html,'html.parser');links=[urllib.parse.unquote(a['href']) for a in soup.select('a[href]')]
short='https://goo.gl/maps/wEw39fmWz3Au4wtYA';assert short in links
redirect=json.loads((root/'ncu-fifth-map-live-source-acceptance/hiroshima-short-link-receipt.json').read_text());assert redirect['requested_url']==short and redirect['status']==302
assert redirect['location']==decisions['ncu-115']['published_record']['source_url'] and '!1d132.713964!2d34.4022006' in redirect['location']
r=decisions['ncu-115']['published_record'];assert (r['latitude'],r['longitude'])==(34.4022006,132.713964)
script=(images/'fifth-locations_cuk-map-script.js.raw').read_text();assert "campusId: '1', campusName: '성심교정', campusNameEn: 'Songsim Campus'" in script and "campus: '1', lat: 37.485931, lng: 126.804622" in script
r=decisions['ncu-154']['published_record'];assert (r['latitude'],r['longitude'])==(37.485931,126.804622)
host=obj('reviewed-host-records.json');assert '約五月' in host['ncu-138']['fields']['housing']['points'][2]
for sid in ['ncu-091','ncu-138']:
 for d in host[sid]['host_documents']:assert d['needs_confirmation'] is True and d['applicability_status']=='reference_only'
report={'source_commit':sha,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'source review passed with one wording correction required during integration','photos':photo_results,'seven_named_locations_original_numeric_derivation_verified':True,'coordinate_scope':'Representative named campus only; none confirms current NCU exchange assignment. Catholic photo is Songeui while point is Songsim; explicit distinction preserved.','manual_host_review':{'ktu':'2021 policy full four-page native text; 2025/26 nine-page image factsheet all pages viewed; current undated incoming, 2026/27 calendar and general relocation read with version conflicts; original binary DOC stored text and coordinator signature sections inspected. No GUI rendering of binary DOC claimed.','meiji':'AY2027 nine-page guidelines all native text and all nine rendered pages viewed; doctor health form and photo guide individually viewed; four DOCX document.xml text fully read; factsheet HTML and all four embedded images viewed, including rent and insurance tables. Landing source year/COE/cost/course-version conflicts retained.','preserved_conflicts':['KTU 2021 versus 2025/26 nomination/application dates','KTU semester/exam end differences and separate exchange/general housing costs','Meiji late-March versus August2027 course availability statements','Meiji Spring2027 page versus legacy2026 email template','Meiji May2026 housing prices apply to Spring2027, not guaranteed Fall2027']},'required_integration_correction':{'path':'sources/ncu/2026-10-11/reviewed-host-records.json','row':'ncu-138.fields.housing.points[2]','from':'首學期約五月全額','to':'首學期約五個月全額','source':'Original factsheet: first one semester (about 5 months); this is duration, not month of May. Apply source and derived outputs atomically.'},'merge_constraints':['Preserve explicit operator location override precedence and one NCU candidate-hold rule; missing record alone permits verified shared fallback.','Keep ten remaining unresolved candidate holds and Mons; replace only seven newly substantiated rows.','Retain prior Turku full A1–C2 assessment/signature supplement.','Incoming API precedence test currently writes supposed shared fallback into operator-override file; bind actual shared catalog in fixture, preserving both precedence assertions.'],'current_cycle_completion':False,'new_116_quota_verified':False}
(root/'ncu-fifth-independent-source-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['photos','manual_host_review','merge_constraints']},ensure_ascii=False))
