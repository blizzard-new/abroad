"""Preserve failed history and promote five actually opened host templates."""
import gzip,hashlib,json,shutil
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'src/exchange_info/official_data/tku'


def main():
    records=json.loads((B/'meiji_2027_attachment_checks_retry1.json').read_text())
    assert len(records)==5 and all(r['http_status']==200 and r['prior_http_status']==503 for r in records)
    index=json.loads((B/'host_census_capture_index.json').read_text())
    institution=next(r for r in index if r['id']=='tku-sister-178')
    for r in records:
        blob=(B/r['local_file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==r['sha256']
        key=hashlib.sha256((r['source_url']+'|'+r['checked_at']).encode()).hexdigest()[:24]
        target=key+Path(r['local_file']).suffix
        shutil.copyfile(B/r['local_file'],B/'host_census_sources'/target)
        s=dict(id=key,source_url=r['source_url'],final_url=r['source_url'],http_status=200,checked_at=r['checked_at'],
            sha256=r['sha256'],local_file=target,error=None,title='Meiji incoming exchange template linked from AY2027 guide',
            role='host_incoming',applicable_year='AY2027 guide-linked template; internal edition separately stated',
            prior_http_status=503,attempt=2,links=[])
        if blob.startswith(b'%PDF'):
            s['pages']=[dict(page=i+1,text=t) for i,t in enumerate(r['pages'])];s['text']='\n'.join(r['pages'])
        else:
            assert blob.startswith(b'PK')
            with ZipFile(B/r['local_file']) as z:
                xml=z.read('word/document.xml');s['document_xml']=xml.decode()
                s['text']='\n'.join(t.text or '' for t in ElementTree.fromstring(xml).iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
        (B/'host_census_sources'/(key+'.json.gz')).write_bytes(gzip.compress(json.dumps(s,ensure_ascii=False).encode(),mtime=0))
        r.update(source_id=key,content_reviewed=True,source_period='AY2027 guide p.8 explicitly linked; DOCX internal edition undated; English course list AY2026 reference')
        if not any(x['id']==key for x in institution['sources']):
            institution['sources'].append({k:s.get(k) for k in ('id','source_url','final_url','http_status','checked_at','sha256','title','error')})
    (B/'host_census_capture_index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    (B/'meiji_2027_attachment_checks_retry1.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(opened_templates=5,prior_failed_history_preserved=True)))


if __name__=='__main__':main()
