"""Compare product attribution to archived Commons responses or fixed base assets."""
from pathlib import Path
from collections import Counter
import gzip,hashlib,io,json,subprocess,zipfile
from bs4 import BeautifulSoup

sha='93cbd9dfee3af95f9ecc89cceb1ccd0e100778af';base='59a20f27fcee00fb597abc79e75ec11778317422'
prefix='src/exchange_info/official_data/tku/'
def blob(path,head=sha):return subprocess.check_output(['git','show',head+':'+path])
def obj(path,head=sha):return json.loads(blob(path,head))
pack=obj(prefix+'capture_pack_manifest.json');photos=obj(prefix+'campus_asset_manifest.json')
plain=lambda value:BeautifulSoup(value or '', 'html.parser').get_text(' ',strip=True)
normalize=lambda value:plain(value).replace('http://','https://').rstrip('/')
index={};captures=0
for arc in pack['archives']:
    names=[name for name,r in pack['files'].items() if r['archive']==arc['file'] and name.endswith('.json.gz') and name.split('/')[0] in ('commons_campus_candidates','asset_batch_sources','asset_source_retries')]
    if not names:continue
    data=b''.join(blob(prefix+'capture_packs/'+p['file']) for p in arc['parts'])
    assert hashlib.sha256(data).hexdigest()==arc['sha256']
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in names:
            raw=archive.read(name);assert hashlib.sha256(raw).hexdigest()==pack['files'][name]['sha256']
            record=json.loads(gzip.decompress(raw));response=record.get('response') or {}
            if not isinstance(response,dict):continue
            pages=response.get('query',{}).get('pages',{})
            if isinstance(pages,dict):pages=pages.values()
            for page in pages:
                for info in page.get('imageinfo',[]):
                    if info.get('descriptionurl') and info.get('extmetadata'):
                        index.setdefault(info['descriptionurl'],[]).append((name,info))
            captures+=1
baseline=obj('src/exchange_info/static/assets/school-images.json',base)['schools']
result=[]
for p in photos:
    matches=[]
    for name,info in index.get(p['source_url'],[]):
        meta=info['extmetadata'];author=plain(meta.get('Artist',{}).get('value'));license=plain(meta.get('LicenseShortName',{}).get('value'));url=meta.get('LicenseUrl',{}).get('value') or info['descriptionurl']+'#Licensing'
        if normalize(author)==normalize(p['author']) and license==p['license'] and normalize(url)==normalize(p['license_url']):matches.append(name)
    base_matches=[r for r in baseline if r.get('local_path')==p['local_path'] and r.get('content_hash')==p['sha256'] and normalize(r.get('artist'))==normalize(p['author']) and r.get('license_name')==p['license'] and normalize(r.get('license_url'))==normalize(p['license_url']) and r.get('official_page_url')==p['source_url']]
    result.append({'id':p['id'],'source_url':p['source_url'],'result':'archived_commons_match' if matches else 'fixed_base_attribution_match' if base_matches else 'needs_individual_source_check','archived_capture_files':sorted(set(matches)),'fixed_base_matches':len(base_matches)})
report={'source_commit':sha,'baseline':base,'archived_commons_captures_examined':captures,'result_counts':dict(Counter(r['result'] for r in result)),'rows':result,'scope':'Archive consistency only. Fixed-base matches preserve existing attribution; they are not a fresh licensing review.'}
Path('/workspace/recovery-evidence-20261011/tku-sixth-license-consistency.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_commit':sha,'result_counts':report['result_counts'],'unresolved':[r for r in result if r['result']=='needs_individual_source_check']},ensure_ascii=False,indent=2))
