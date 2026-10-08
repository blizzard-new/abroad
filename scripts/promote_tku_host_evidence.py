"""Promote only the explicitly reviewed October 8 host snapshots; no year inference.

Run with both capture directories. This is a manual-review recipe, not a crawler
that automatically treats a newly downloaded document as current.
"""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1] / 'src/exchange_info/official_data/tku'
REVIEWS = {
    'nagasaki-nics-2027': ('2027 Spring', 'Notice heading, qualifications, 11 documents, fees, insurance and curriculum read.'),
    'nagasaki-partners': ('general partnership directory', 'Taiwan section explicitly lists Tamkang University, agreement dated 2004-05-17; not a quota list.'),
    'nagasaki-courses': ('general course list linked from 2027 Spring notice', 'Course list read; individual 2027 offerings are not guaranteed.'),
    'nagasaki-calendar': ('2026 academic calendar; 2027 not verified', 'Page heading says 2026年度. Do not transplant dates into 2027.'),
    'nagasaki-form-a-online': ('2027 Spring', 'Form heading and periods read; public form inspected without entering information or submitting.'),
    'nagasaki-pledge': ('2027 Spring', 'Body explicitly says March-August 2027 / March 2027-February 2028; signature and first-term housing provisions read.'),
    'ritsumeikan-howto-2027': ('2027 Spring', 'Nomination/application periods, admission, housing, COE and health procedures read.'),
    'ritsumeikan-support': ('general support services, no cycle stated', 'Counselling, international centre and accessibility support read; no annual fees.'),
    'ritsumeikan-fees': ('general fee page reflecting Spring 2027 support fee; living-budget cycle unstated', 'Exchange vs self-sponsored fees separated; budget insurance overlap needs confirmation.'),
    'ritsumeikan-kinugasa-housing': ('moving in from March 2026; subject to change each semester', 'Three I-House fee tables, initial fees, facilities and commute descriptions read; not confirmed 2027 offer.'),
    'ritsumeikan-bkc-housing': ('moving in from March 2026; subject to change each semester', 'Type A/B monthly totals and entrance/cleaning/processing/fire-insurance exclusions read.'),
    'ritsumeikan-oic-housing': ('moving in from March 2026; subject to change each semester', 'Monthly total 64,200 yen and initial fees read; dormitory visit form is not a housing application.'),
    'uec-courses': ('2026 Spring and Fall course schedules; 2027 not verified', 'Listed latest course schedules and descriptions read; future courses may differ.'),
    'uec-program': ('general JUSST description, updated 2025-09-25', 'Undergraduate and graduate course obligations distinguished; no 2027-specific timetable.'),
    'uec-application-recheck': ('general JUSST application, updated 2025-10-28; 2027 not verified', 'Eligibility alternatives, 17 document entries and conditional post-acceptance finance/TB requirements read.'),
    'uec-life-corrected': ('general life index, updated 2025-10-24', 'Corrected URL read; generic index is not a 2027 arrival guide.'),
    'uec-residence': ('general residence guidance, updated 2025-09-24', 'Residence card and municipal address procedures read; no 2027 school arrival date.'),
    'uec-national-insurance': ('general insurance guidance, created 2010, updated 2025-09-24', 'Enrollment procedures read; amounts are general estimates, not 2027 premiums.'),
    'uec-private-insurance': ('general guidance containing a fee table valid October 2009', '2009 table explicitly dated in body; do not use its premiums as current.'),
    'uec-fact-sheets': ('general university statistics', 'Statistical fact sheets, not an incoming exchange application sheet.'),
    'japan-student-visa': ('general student visa guidance, updated 2023-03-17', 'Required documents, electronic COE and nationality-dependent additions read; COE does not guarantee visa.'),
    'taiwan-coe-visa': ('general visa guidance for Taiwan passport holders with COE', 'Original passport/ID, signed form, 4.5x3.5 cm photo and COE requirements read; different from host application photos.'),
    'taiwan-visa-form-index': ('general visa forms, no academic cycle', 'Official download index read; school application forms remain separate.'),
    'tku-news-recheck': ('general news index checked 2026-10-08', 'Exchange-selection headlines checked; 2027-2028 English/Chinese selection not verified, not evidence of non-announcement.'),
    'tku-outbound-recheck': ('general outbound guidance checked 2026-10-08', 'Programme routes checked; departmental junior-abroad programme not equated to current exchange choices.'),
}

def main(paths):
    existing = json.loads((BUNDLE/'sources.json').read_text())
    by_id = {r['id']: r for r in existing}
    for path in paths:
        for row in json.loads((path/'sources.json').read_text()):
            source_id=row['id']
            if row.get('open_status') == 'failed':
                row['applicability_review_status']='unavailable_at_check'
                row['review_note']='Failed read retained as an attempted entry point; not used for a verified fact.'
            elif source_id in REVIEWS:
                row['applicable_year'],row['review_note']=REVIEWS[source_id]
                row['applicability_review_status']='reviewed_content'
            elif source_id.startswith('nagasaki-form-'):
                row['applicable_year']='undated form currently linked by 2027 Spring NICS notice'
                row['review_note']='Full form content reviewed; current applicability is based on the 2027 notice link, not filename year. Photo-count/essay translation conflicts retained.'
                row['applicability_review_status']='reviewed_content'
            elif source_id.startswith('uec-') and row.get('local_file'):
                row['applicable_year']='general JUSST form; 2027-specific version not verified'
                row['review_note']='Full PDF/DOCX contents read; Form A copyright 2023 and annual recurring dates are reference only. ver22/ver23 are version labels, not inferred academic years.'
                row['applicability_review_status']='reviewed_content'
            else:
                raise ValueError(f'No explicit content review: {source_id}')
            if source_id=='tku-news-recheck':
                # Selection research does not need applicant names from result posts.
                row['text']='\n'.join(line for line in row['text'].splitlines() if '甄選' in line and '結果' not in line)
                row['extraction_note']='Only exchange-selection headline lines retained; personal result content excluded.'
                row['links']=[l for l in row.get('links',[]) if '甄選' in l['title'] and '結果' not in l['title']]
            if row.get('local_file'):
                shutil.copyfile(path/row['local_file'], BUNDLE/row['local_file'])
            by_id[source_id]=row
    (BUNDLE/'sources.json').write_text(json.dumps(list(by_id.values()),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'sources':len(by_id),'reviewed_host_snapshots':sum(r.get('applicability_review_status')=='reviewed_content' for r in by_id.values())}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('staging',type=Path,nargs='+')
    main(p.parse_args().staging)
