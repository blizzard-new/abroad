"""Persist an offline, macro-disabled legacy DOC review without replacing history."""
import gzip,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from tku_capture_io import BUNDLE,read_bytes,exists

def main():
    old_id='6cc748378bad5a267bf4bc28'
    old=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(old_id+'.json.gz'))))
    assert old['sha256']=='b2414f1816859cc67e73e607ffd53cf01f63eec0a81d6cd6b29f73c900cd3a11'
    raw=Path('/tmp/tku-doc-offline-20261011/'+old_id+'.txt').read_bytes()
    text=raw.decode('utf-8-sig');lines=text.splitlines()
    assert '（2026年度）' in text and '博士研究生/ Doctor graduate student' in text
    assert 'APPLICATION FORM FOR LIAONING GOVERNMENT SCHOLARSHIP' in text
    derived_id=hashlib.sha256((old_id+':offline-libreoffice-text-20261011').encode()).hexdigest()[:24]
    if exists(BUNDLE/'host_census_sources'/(derived_id+'.json.gz')):
        saved=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(derived_id+'.json.gz'))))
        assert saved['parser']['converted_text_sha256']==hashlib.sha256(raw).hexdigest()
        print(json.dumps(dict(status='retained_immutable_offline_review',source_id=derived_id)))
        return
    stamp=datetime.now(timezone.utc).isoformat()
    derived=dict(old,id=derived_id,text=text,paragraphs=[s.strip() for s in lines if s.strip()],checked_at=stamp,original_capture_id=old_id,content_extraction_status='parsed_legacy_DOC_text_offline',programme_scope='full_degree_doctoral_scholarship_not_TKU_exchange',applicable_year='2026; explicitly printed in DOC body',content_scope='Liaoning Government Scholarship doctoral form, not a TKU exchange application form',parser=dict(tool='LibreOfficeDev 26.8.0.0.alpha0',mode='headless txt:Text conversion',macro_security_level=3,external_link_update=0,requested_network_operations=0,converted_text_sha256=hashlib.sha256(raw).hexdigest(),converted_text_bytes=len(raw),conversion_exit_code=0,conversion_warning='Fontconfig no writable cache directories; conversion completed'))
    store=BUNDLE/'host_census_sources';store.mkdir(exist_ok=True)
    (store/(derived_id+'.json.gz')).write_bytes(gzip.compress(json.dumps(derived,ensure_ascii=False).encode(),mtime=0))
    path=BUNDLE/'host_census_capture_index.json';index=json.loads(path.read_text())
    row=next(r for r in index if r['id']=='tku-sister-225')
    meta={k:derived.get(k) for k in ('id','source_url','final_url','http_status','checked_at','sha256','title','error')}
    meta.update(source_role='offline_macro_disabled_DOC_content_review',original_capture_id=old_id,scope='read and excluded: 2026 doctoral scholarship, not TKU exchange')
    if not any(s['id']==derived_id for s in row['sources']):row['sources'].append(meta)
    path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    locators=[]
    for needle in ['APPLICATION FORM FOR LIAONING GOVERNMENT SCHOLARSHIP','（2026年度）','博士研究生/ Doctor graduate student']:
        locators.append(dict(locator='LibreOffice text lines '+','.join(str(i) for i,l in enumerate(lines,1) if needle in l),quote=needle))
    review=dict(source_id=derived_id,original_capture_id=old_id,source_url=old['source_url'],binary_sha256=old['sha256'],checked_at=stamp,applicable_year='2026',status='read_and_excluded_full_degree_scholarship',reason='Actual form body explicitly names 2026 Liaoning government scholarship and doctoral study; no TKU exchange programme mapping.',evidence=locators,parser=derived['parser'])
    (BUNDLE/'legacy_doc_content_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(review,ensure_ascii=False))

if __name__=='__main__':main()
