"""Capture supplemental host evidence to new staging output; review before promotion."""
from __future__ import annotations
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from refresh_tku_sources import read_source

PAGES = [
    ('nagasaki-nics-2027','https://www.nagasaki-gaigo.ac.jp/studying-abroad/receiving_program/nics_program/','2027 Spring','host_incoming'),
    ('nagasaki-partners','https://www.nagasaki-gaigo.ac.jp/studying-abroad/partner_university/','general / no cycle stated','directory_reference'),
    ('nagasaki-courses','https://www.nagasaki-gaigo.ac.jp/studying-abroad/receiving_program/nics_program/nics_curriculum/','general course list linked by 2027 Spring NICS','host_incoming'),
    ('nagasaki-calendar','https://www.nagasaki-gaigo.ac.jp/campus-life/calendar/','requires_content_review','host_incoming'),
    ('ritsumeikan-howto-2027','https://en.ritsumei.ac.jp/skp/apply/howto/','2027 Spring','host_incoming'),
    ('ritsumeikan-support','https://en.ritsumei.ac.jp/skp/life-in-skp/support-services/','general / no cycle stated','host_incoming'),
    ('uec-courses','https://www.fedu.uec.ac.jp/en/future_students/jusst/course-description/','requires_content_review','host_incoming'),
    ('uec-program','https://www.fedu.uec.ac.jp/en/future_students/jusst/program-description/','requires_content_review','host_incoming'),
    ('uec-life','https://www.fedu.uec.ac.jp/en/current_students/everyday-life/','requires_content_review','host_incoming'),
    ('uec-life-corrected','https://www.fedu.uec.ac.jp/en/current/everyday-life/','general / updated 2025-10-24; body includes older guidance','host_incoming'),
    ('uec-residence','https://www.fedu.uec.ac.jp/en/current/everyday-life/various-procedures-related-to-international-student-id/foreign-resident-registration.html','general / updated 2025-09-24','host_incoming'),
    ('uec-national-insurance','https://www.fedu.uec.ac.jp/en/current/everyday-life/health-insurance-and-other-individual-insurance/national-health-insurance.html','general / no 2027-specific fees','host_incoming'),
    ('uec-private-insurance','https://www.fedu.uec.ac.jp/en/current/everyday-life/health-insurance-and-other-individual-insurance/enrollment-in-private-insurance.html','general / no 2027-specific fees','host_incoming'),
    ('taiwan-coe-visa','https://www.koryu.or.jp/visa/taipei/general/detail1/','general visa guidance for Taiwan passport holders with COE','directory_reference'),
    ('taiwan-visa-form-index','https://www.koryu.or.jp/visa/taipei/application/','general visa forms / not school application forms','directory_reference'),
    ('uec-fact-sheets','https://www.fedu.uec.ac.jp/en/exchanges_programs/fact-sheets/','general statistics / not exchange application sheet','directory_reference'),
    ('japan-student-visa','https://www.mofa.go.jp/j_info/visit/visa/long/visa6.html','general visa guidance / no academic cycle','directory_reference'),
    ('japan-residence','https://www.moj.go.jp/isa/applications/status/student.html','general residence guidance / no academic cycle','directory_reference'),
    ('tku-news-recheck','https://oieie.tku.edu.tw/oieie/?page_id=55','general / no cycle stated','directory_reference'),
    ('tku-outbound-recheck','https://oieie.tku.edu.tw/oieie/?page_id=19024','general / no cycle stated','directory_reference'),
]

def capture(output:Path):
    output.mkdir(parents=True,exist_ok=False)
    def get(spec):
        id,url,year,role=spec
        try:
            row=read_source(url,id,output,'2026-10-08T00:00:00+00:00')
            row['open_status']='verified_open'
        except Exception as exc:
            row={'id':id,'source_url':url,'checked_at':'2026-10-08T00:00:00+00:00',
                 'open_status':'failed','error':str(exc)}
        row.update(applicable_year=year,role=role,applicability_review_status='requires_content_review')
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages=list(pool.map(get,PAGES))
    attachments=[]
    for parent in pages:
        if parent['id']!='nagasaki-nics-2027':continue
        relevant=parent.get('links',[])
        for link in relevant:
            if link['title'] in ['出願ガイド','誓約書','志望動機書','経費支弁書','中国語記入例','推薦書','健康診断書（学生）','健康診断書（医師）']:
                names={'出願ガイド':'form-a-guide','誓約書':'pledge','志望動機書':'form-b','経費支弁書':'form-c',
                       '中国語記入例':'form-c-chinese-sample','推薦書':'form-d','健康診断書（学生）':'form-e1','健康診断書（医師）':'form-e2'}
                attachments.append((f"nagasaki-{names[link['title']]}",link['url'],'undated form linked by 2027 Spring NICS notice','host_incoming'))
    # UEC forms are from a general page; never label them 2027-specific on capture.
    uec=read_source('https://www.fedu.uec.ac.jp/en/future_students/jusst/application/','uec-application-recheck',output,'2026-10-08T00:00:00+00:00')
    uec.update(role='host_incoming',applicable_year='general / updated 2025-10-28',applicability_review_status='requires_content_review')
    pages.append(uec)
    for link in uec['links']:
        if urlsplit(link['url']).path.lower().endswith(('.pdf','.docx')):
            filename=urlsplit(link['url']).path.rsplit('/',1)[-1]
            if any(word in filename for word in ['form','Form']):
                attachments.append(('uec-'+filename.replace('.','-'),link['url'],'undated general JUSST form / 2027 version not verified','host_incoming'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages+=list(pool.map(get,attachments))
    (output/'sources.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'sources':len(pages),'failed':[{k:r[k] for k in ['id','error']} for r in pages if r.get('open_status')=='failed']},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    capture(p.parse_args().output)
