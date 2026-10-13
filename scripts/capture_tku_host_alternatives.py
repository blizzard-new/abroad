"""Public replacement official sites for stale directory links, bounded to two links.

These are explicitly reviewed institution domains. No login, challenge bypass,
403 endpoint retry or automatic current-cycle eligibility promotion is used.
"""
import json,re,time
from urllib.parse import urlsplit
from capture_tku_census_hosts import BUNDLE,capture,allowed_domain,domain,DISCOVER
ALTERNATIVES={307:'https://www.chd.edu.cn/',280:'https://www.tnu.edu.vn/',244:'https://www.kmitl.ac.th/',245:'https://www.shibaura-it.ac.jp/',238:'https://www.kmutt.ac.th/',236:'https://www.uj.edu.pl/',214:'https://www.psu.ac.th/',215:'https://www.univ-poitiers.fr/',209:'https://www.bu.ac.th/en',188:'https://www.univ.gakushuin.ac.jp/',185:'https://www.uspceu.com/',177:'https://university.sunway.edu.my/',173:'https://www.ulat.ac.pa/',169:'https://www.omu.ac.jp/en/',168:'https://www.fit.edu/',123:'https://www.fwu.ac.jp/',111:'https://www.ritsumei.ac.jp/',7:'https://www.vub.be/',59:'https://www.ubbcluj.ro/ro/',50:'https://hcu.edu.my/',6:'https://uclouvain.be/',62:'https://english.spbu.ru/',53:'https://www.waikato.ac.nz/',127:'https://english.ucas.ac.cn/',60:'https://www.dvfu.ru/',44:'https://www.cju.ac.kr/',76:'https://www.ohio.edu/'}

def main():
    ipath=BUNDLE/'host_census_capture_index.json';index=json.loads(ipath.read_text());byid={r['id']:r for r in index}
    path=BUNDLE/'host_source_alternative_checks.json';checks=json.loads(path.read_text()) if path.exists() else []
    done={r['source_url'] for r in checks}
    existing={s['source_url'] for r in index for s in r['sources']}
    def save(d,url,role):
        if url in done:return next((r for r in checks if r['source_url']==url),None)
        if url in existing:return None
        source=capture(url)
        meta={k:source.get(k) for k in ('id','source_url','final_url','http_status','checked_at','sha256','title','error')}
        meta.update(source_role=role,identity_source_url=d['directory_url'],scope='public host reference; old name/merged institution and exchange programme remain separate')
        d['sources'].append(meta)
        r=dict(meta,institution_id=d['id'],source_id=source['id'])
        checks.append(r);path.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');ipath.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');done.add(url);existing.add(url)
        print(json.dumps(r),flush=True);time.sleep(3)
        return source
    for n,url in ALTERNATIVES.items():
        d=byid['tku-sister-'+str(n)]
        root=save(d,url,'manually_verified_official_domain_alternative')
        if not root or root.get('http_status')!=200 or root.get('error'):continue
        links=[x['url'] for x in root.get('links',[]) if x['url'].startswith('https://') and allowed_domain(x['url'],{domain(url),domain(root.get('final_url',url))}) and DISCOVER.search(x['title']) and not re.search(r'outgoing|outbound|login|log in|apply now|申請系統',x['title'],re.I)]
        for link in list(dict.fromkeys(links))[:2]:save(d,link,'bounded_public_official_discovery')

if __name__=='__main__':main()
