"""Freeze remaining TKU scope and bounded actual official-link alternatives."""
import gzip,json,re
from collections import Counter
from tku_capture_io import BUNDLE,read_bytes
from audit_tku_unread_candidates import canonical_public_url

BASE='4f142ea36e69338d2956b4ea5d3d37a9f4116e52'
# Actual links already captured from official sources. Exclude news, events,
# outbound, testimony and login alternatives from the next network pass.
HOST_LINKS={
 290:['https://www.uade.edu.ar/uade-internacional/incoming/application/'],
 252:['http://www.scut.edu.cn/sie/'],
 251:['https://www.ccnu.edu.cn/hzjl/gathzyjl.htm'],
 193:['https://relacionesinternacionales.una.py/movilidades-bilaterales/'],
 191:['http://oice.fjnu.edu.cn/main.htm'],
 186:['https://oica.nqu.edu.tw/p/412-1003-1149.php?Lang=zh-tw'],
 174:['https://wsc.hqu.edu.cn/'],
 144:['http://sie.whut.edu.cn/lhlx/','http://sie.whut.edu.cn/english/'],
 139:['https://hmt.pku.edu.cn/'],
 79:['https://cge.fresnostate.edu/international/index.html'],
}
ASSET_LINKS={
 'tku-sister-322':['https://hz.nl/en/locations/contact','https://hz.nl/en/our-campuses'],
 'tku-sister-242':['https://www.iact.edu.my/contact-us/'],
 'tku-sister-175':['https://www.um.edu.mo/wp-content/uploads/2026/08/UMMap202608.pdf','https://maps.um.edu.mo/go.php/8krBcV'],
 'tku-sister-207':['https://www.uma.es/conoce-la-uma/cms/menu/campus/','https://www.uma.es/conoce-la-uma/navegador_de_ficheros/MAPAS-CAMPUS/descargar/2025%20mapa%20UNIVERSIDAD%20DE%20MALAGA%20-%20web%20(1).pdf'],
 'tku-sister-203':['https://u-paris.fr/nos-sites-et-campus/','https://maps.app.goo.gl/viSk1fWacnW2yhQX7'],
 'tku-sister-307':['https://www.chd.edu.cn/ggfw/xydt.htm'],
 'tku-sister-15':['https://www.openstreetmap.org/way/32469535'],
 'tku-sister-195':['https://www.esiea.fr/ecole/campus-laval/'],
}

def main():
 gap=json.loads((BUNDLE/'milestone5_full_gap_outcomes.json').read_text());remaining=[s for s in gap['schools'] if s['state']=='needs_source'];assets=json.loads((BUNDLE/'milestone5_asset_outcomes.json').read_text());idx=json.loads((BUNDLE/'host_census_capture_index.json').read_text());byid={s['id']:s for s in idx}
 known={canonical_public_url(u) for r in idx for e in r['sources'] for u in [e['source_url'],e.get('final_url')] if u};rows=[];candidates=[];pending=[]
 for purpose,chosen in [('host_incoming',{'tku-sister-'+str(k):v for k,v in HOST_LINKS.items()}),('asset_identity_or_named_map',ASSET_LINKS)]:
  allowed={s['id'] for s in remaining} if purpose=='host_incoming' else {s['id'] for s in assets['schools']}
  assert set(chosen)<=allowed
  for identifier,urls in chosen.items():
   linked={}
   for e in byid[identifier]['sources']:
    d=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz'))))
    for l in d.get('links',[]):linked.setdefault(l['url'],dict(url=l['url'],label=l.get('title',''),linked_from=d['source_url'],source_id=d['id']))
   for url in urls:
    assert url in linked,(identifier,url)
    c=dict(linked[url],institution_id=identifier,purpose=purpose,reason='Explicit unattempted link in previously captured official body; finite remaining scope')
    if canonical_public_url(url) in known:pending.append(dict(c,decision='already_attempted_do_not_repeat'))
    else:candidates.append(dict(c,ordinal=len(candidates)+1))
 for s in remaining:
  prior=byid[s['id']]['sources'];sources=[]
  for e in prior:
   d=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['id']+'.json.gz'))));sources.append(dict(source_id=d['id'],source_url=d['source_url'],final_url=d.get('final_url'),checked_at=d['checked_at'],http_status=d.get('http_status'),error=d.get('error'),body_characters=len(d.get('text','')),content_sha256=d.get('sha256')))
  rows.append(dict(id=s['id'],school_name=s['school_name'],baseline_state=s['state'],baseline_assessment=s['assessment'],official_entry_attempted=bool(prior),prior_source_checks=sources,new_bounded_candidates=[c for c in candidates if c['institution_id']==s['id'] and c['purpose']=='host_incoming']))
 assert len(rows)==42 and all(r['official_entry_attempted'] for r in rows)
 result=dict(base_commit=BASE,checked_date='2026-10-11',scope=dict(remaining_host_institutions=42,original_gap_institutions=98,asset_gap_institutions=39,no_repeat_external_institutions=36,max_intake_host_links_per_institution=2,max_intake_asset_links_per_institution=2,followup_limit='Only actual relevant public links within frozen institutions; at most2sources/school in each named bounded pass; each final pass frozen before requests; no new institutions'),input_count=len(candidates),candidates=candidates,already_attempted_not_repeated=pending,schools=rows)
 (BUNDLE/'milestone6_official_inputs.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(schools42=len(rows),never_attempted_official_entry=sum(not r['official_entry_attempted'] for r in rows),candidates=len(candidates),purposes=Counter(c['purpose'] for c in candidates),schools_with_host_leads=sum(bool(r['new_bounded_candidates']) for r in rows)),ensure_ascii=False))

if __name__=='__main__':main()
