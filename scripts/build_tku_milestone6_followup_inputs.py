import json,gzip
from collections import Counter
from tku_capture_io import BUNDLE,read_bytes
from audit_tku_unread_candidates import canonical_public_url
chosen={
 290:['https://www.uade.edu.ar/media/0w1njwvw/mobility-guideline-for-partners.pdf','https://www.uade.edu.ar/media/sb2jl0fq/mobility-guideline-for-students.pdf'],
 193:['http://www2.una.py/internacionales/images/carta_de_compromiso_Ingles.docx'],
 186:['https://oica.nqu.edu.tw/p/405-1003-6582,c1149.php?Lang=zh-tw','https://oica.nqu.edu.tw/p/405-1003-6577,c1149.php?Lang=zh-tw'],
 174:['https://wsc.hqu.edu.cn/xsxm/lxjl.htm'],
 144:['http://sie.whut.edu.cn/english/teac/ex/','http://sie.whut.edu.cn/english/ist/lan/'],
 139:['https://hmt.pku.edu.cn/xssw/zxxx.htm'],
 251:['http://hmt.ccnu.edu.cn/'],
 33:['https://www.aoyama.ac.jp/international/'],
 39:['https://u-aizu.ac.jp/en/intro/initiatives/globalization/'],
}
idx=json.loads((BUNDLE/'host_census_capture_index.json').read_text());byid={r['id']:r for r in idx};known={canonical_public_url(u) for r in idx for e in r['sources'] for u in [e['source_url'],e.get('final_url')] if u};candidates=[]
for n,urls in chosen.items():
 id='tku-sister-'+str(n);sources=[json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz')))) for e in byid[id]['sources']]
 for u in urls:
  found=next(((s,l) for s in sources for l in s.get('links',[]) if l['url']==u),None)
  if found:s,l=found;label=l.get('title','')
  else:
   s=next(s for s in sources if u in s.get('text',''));label='Explicit official URL quoted in readable body'
  assert canonical_public_url(u) not in known,(id,u)
  candidates.append(dict(ordinal=len(candidates)+1,institution_id=id,url=u,label=label,linked_from=s['source_url'],source_id=s['id'],purpose='host_incoming_or_direct_binary',reason='At most2new explicit official sources/institution; Aoyama corporate-to-university bridge, Aizu globalization link; no guessed application routes'))
result=dict(base_commit='4f142ea36e69338d2956b4ea5d3d37a9f4116e52',checked_date='2026-10-11',input_count=len(candidates),candidates=candidates,scope='Original42only; no36external retries; no login submission; at most2direct sources/institution in this pass')
(BUNDLE/'milestone6_followup_inputs.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('followups',len(candidates))
