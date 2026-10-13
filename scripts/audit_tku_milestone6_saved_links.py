import json,gzip,re
from collections import Counter
from urllib.parse import urlsplit
from tku_capture_io import BUNDLE,read_bytes
from audit_tku_unread_candidates import canonical_public_url
snapshot=json.loads((BUNDLE/'milestone5_full_gap_outcomes.json').read_text());schools=[s for s in snapshot['schools'] if s['state']=='needs_source'];idx=json.loads((BUNDLE/'host_census_capture_index.json').read_text());allknown={canonical_public_url(u) for r in idx for c in r['sources'] for u in [c['source_url'],c.get('final_url')] if u};byid={r['id']:r for r in idx}
pattern=re.compile(r'incoming|inbound|exchange|international|global|mobility|外国|外國|交換|交流|留学|留學|合作|国际|國際|협력|교환|intercambio|movilidad|intercâmbio|etudiant|étudiant|internacional|relations|bilateral|study.?abroad',re.I)
strong=re.compile(r'incoming|inbound|exchange.student|student.exchange|交換留学|交換留學|international.office|international.relations|来华|來華|study.?at|incoming.exchange',re.I)
def domain(u):
 h=(urlsplit(u).hostname or '').lower();p=h.split('.');return '.'.join(p[-3:]) if '.'.join(p[-2:]) in {'ac.jp','edu.cn','edu.tw','ac.in','com.kh','com.vn','edu.vn','ac.th','edu.py','edu.ar','edu.mx','edu.ph','ac.id'} else '.'.join(p[-2:])
rows=[];candidate_count=0
for s in schools:
 row=byid[s['id']];domains={domain(e['source_url']) for e in row['sources']};discovered={};body_count=0;fail_count=0
 for e in row['sources']:
  c=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz'))));text=c.get('text','');body_count+=bool(text.strip()) and c.get('http_status')==200;fail_count+=c.get('http_status')!=200 or not text.strip()
  for l in c.get('links',[]):
   u=l.get('url');label=l.get('title','');joined=label+' '+str(u)
   if not u or urlsplit(u).scheme not in {'http','https'} or domain(u) not in domains or not pattern.search(joined):continue
   key=canonical_public_url(u)
   if key in allknown:continue
   score=(10 if strong.search(joined) else 0)+(3 if pattern.search(label) else 0)-(5 if re.search(r'news|event|people|staff|research|alumni|degree|master|phd|policy|strategy|business',joined,re.I) else 0)
   old=discovered.get(key)
   if not old or score>old['score']:discovered[key]={'url':u,'label':label,'linked_from':c.get('final_url') or c['source_url'],'source_id':c['id'],'score':score}
 links=sorted(discovered.values(),key=lambda x:(-x['score'],len(x['url'])))
 shortlisted=[x for x in links if x['score']>=3][:2];candidate_count+=len(shortlisted)
 rows.append({'id':s['id'],'school_name':s['school_name'],'baseline_assessment':s['assessment'],'recorded_source_count':len(row['sources']),'readable_record_count':body_count,'failed_or_empty_record_count':fail_count,'all_matching_unattempted_links':links,'bounded_new_official_links':shortlisted})
print('school_count',len(rows),'bounded_links',candidate_count,'schools_with_new_official_links',sum(bool(r['bounded_new_official_links']) for r in rows))
for r in rows:
 print(r['id'],r['school_name'],'sources='+str(r['recorded_source_count']),'new='+str(len(r['bounded_new_official_links'])))
 for l in r['bounded_new_official_links']:print(' ',l['score'],l['label'][:80],l['url'])
(BUNDLE/'milestone6_official_link_inventory.json').write_text(json.dumps({'base_commit':'4f142ea36e69338d2956b4ea5d3d37a9f4116e52','checked_date':'2026-10-11','scope':'Only42 needs_source institutions frozen at M5; no36 external retries; actual captured official hyperlinks only; max2newlinks/institution at intake','institutions':42,'candidate_count':candidate_count,'schools':rows},ensure_ascii=False,indent=2)+'\n')
