import json,gzip,re
from collections import Counter
from tku_capture_io import BUNDLE,read_bytes
from audit_tku_unread_candidates import canonical_public_url
chosen={33:['https://www.aoyama.ac.jp/international/from_overseas/exchange/','https://www.aoyama.ac.jp/international/from_overseas/exchange/application.html'],174:['https://wsc.hqu.edu.cn/info/1030/16745.htm','https://wsc.hqu.edu.cn/info/1030/16735.htm'],139:['https://hmt.pku.edu.cn/xssw/jhssw1/lxjhs.htm'],251:['http://hmt.ccnu.edu.cn/jhjls1/lxjhs.htm'],39:['https://www.u-aizu.ac.jp/osip/en/']}
idx=json.loads((BUNDLE/'host_census_capture_index.json').read_text());byid={r['id']:r for r in idx};known={canonical_public_url(u) for r in idx for e in r['sources'] for u in [e['source_url'],e.get('final_url')] if u};candidates=[]
for n,urls in chosen.items():
 id='tku-sister-'+str(n);sources=[json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz')))) for e in byid[id]['sources']]
 for u in urls:
  s,l=next((s,l) for s in sources for l in s.get('links',[]) if l['url']==u);assert canonical_public_url(u) not in known
  candidates.append(dict(ordinal=len(candidates)+1,institution_id=id,url=u,label=l.get('title',''),linked_from=s['source_url'],source_id=s['id'],purpose='specific_incoming_rule_body',reason='Final bounded rule pass; actual directories selected incoming not outbound; up to2specific rule pages plus directly linked2attachments/school'))
# Two actual NQU PDFs: filename New versus old guide link, neither assumed current.
id='tku-sister-186'; sources=[json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz')))) for e in byid[id]['sources']]
for s in sources:
 for l in s.get('links',[]):
  if l.get('title')=='New Application_for_international_Exchange_Programs.pdf' or l['url']=='https://oica.nqu.edu.tw/var/file/3/1003/img/ApplicationforinternationalExchangePrograms.pdf':
   if not any(c['url']==l['url'] for c in candidates):candidates.append(dict(ordinal=len(candidates)+1,institution_id=id,url=l['url'],label=l.get('title',''),linked_from=s['source_url'],source_id=s['id'],purpose='actual_template_binary',reason='Open both actual linked templates; New filename not year; Taiwan domestic route unverified'))
assert len(candidates)==9
(BUNDLE/'milestone6_rule_inputs.json').write_text(json.dumps(dict(base_commit='4f142ea36e69338d2956b4ea5d3d37a9f4116e52',checked_date='2026-10-11',input_count=len(candidates),candidates=candidates,scope='Final concrete incoming pages/direct linked binaries in original42; no36external retries; no login'),ensure_ascii=False,indent=2)+'\n');print('rule/body inputs',len(candidates))
