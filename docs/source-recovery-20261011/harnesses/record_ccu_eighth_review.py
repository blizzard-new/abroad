"""Independent scoped semantic checks for the 24 newly mapped CCU fields."""
from pathlib import Path
import gzip, hashlib, json, re
from bs4 import BeautifulSoup

base=Path('/tmp/ccu-eighth-fixed-review-20261011/src/exchange_info/official_data/ccu')
out=Path('/workspace/recovery-evidence-20261011')
fields=json.loads((base/'completion-eighth-field-input.json').read_text())
assert len(fields)==24
reading=json.loads((base/'completion-eighth-reading-input.json').read_text())
assert len(reading)==378
for row in reading:
    receipt=json.loads((base/'completion_sources'/f"{row['source_id']}.receipt.json").read_text())
    body=(base/receipt['bundled_file']).read_bytes()
    if receipt['bundled_file'].endswith('.gz'):body=gzip.decompress(body)
    assert hashlib.sha256(body).hexdigest()==receipt['sha256']==row['content_hash']
    assert receipt['source_url']==row['source_url'] and row['review_extent']
bus=out/'ccu-eighth-reviewed-images/p92-life-1.body'
soup=BeautifulSoup(bus.read_bytes(),'html.parser')
assert any(a.get('href')=='https://www.usj.es/sites/default/files/archivos/260824_TARIFAS_AUTOBUSES_USJ_26_27.pdf' for a in soup.find_all('a'))
assert '2026-2027' in soup.get_text(' ',strip=True)
notes={
 'BFSU':'Complete saved2022-02-16 notice read. Fall2022 nominationApr10–May20, applicationApr10–May31. Six documents, two Chinese academic recommendations, original1–4 submitted and5–6 inspected on arrival. Nomination Excel and stamped scan separate. Actual attached form and private portal not obtained. No2027 promotion.',
 'Oneonta':'Complete exchange/visiting and insurance HTML bodies read, campus living body read, Spring2027 calendar overview/monthly/exam sections read. Partner nomination and GPA3/B, named English alternatives, six document categories and six-month finance/passport rules retained. Initial private OGE and postacceptance course form separate. F-1 minimum12 credits not universal J-1. No application fee does not imply no tuition. Jan21–23 versus22–23 Thursday–Saturday contradiction retained. Class Jan25–May14, finalsMay17–21. UHC Spring/SummerJan15–Aug14 seven-month1396.28 not spring-only total.',
 'HWG':'Complete partner incoming main body read. B2 teaching language, one completed home year and home nomination are unyear rules. Adjacent Spring2027 calendar does not independently date these eligibility requirements. No invented accepted test score.',
 'USJ':'Complete transport main body read and actual tarifas anchor checked. The one-page tariff PDF independently rendered and visually read. Annual, single and ten-trip columns checked for five origins. PDF has no printed year; parent2026–27 establishes scope. Existing exchange factsheet p3 transport/Spanish paragraphs rechecked only, not a claim of rereading all5pages. EUR300/semester versus annual fares remains an unresolved programme difference; no division into monthly price. New-entry admissions-fee50% discount and continuous-all-year June/July benefit not applied to spring exchange.',
 'KMITL':'Complete visible Health & Living body read.560 rooms divided188male372female is general student/staff housing inventory, not exchange quota or personal guarantee.',
 'Chitkara':'Medical & Health Centre and campus population/context paragraphs read. General comprehensive-insurance statement lacks exchange eligibility, premium, coverage period and2027 detail. Laboratory/directory boilerplate is not claimed fully reread.',
}
fixes=[
 {'page':117,'field':'housing','original':'新生4學期/transfer2學期為degree對象','replacement':'一般新生須住4學期；轉學生可不住宿，選擇住校者须住2學期，均為degree對象','reason':'Original housing body explicitly says transfer students are not required to live on campus; two semesters applies only when choosing campus housing.'},
 {'page':117,'field':'costs','original':'monthly或fraction USD200.25/16日至USD105.40','replacement':'monthly或fraction USD200.25；最多16日 USD105.40','reason':'Actual table separates Monthly (or fraction of) from Up to16Days. Clarify the Chinese period without changing the source, amount or status.'},
]
for f in fixes:
    value=next(x['value'] for x in fields if x['ccu_page']==f['page'] and x['field']==f['field'])
    assert f['original'] in value
report={'fixed_input':'1b9563c58e2fa83c3c2510a40b7ccdd126db9dd1','new_fields_read':24,'source_bodies_supporting_changed_fields':11,'reading_ledger_hashes_verified':378,'independent_semantic_read_extent':notes,'integration_clarifications_required':fixes,'ledger_scope':'Author107full/263partial over370URLs remains explicit; not independently claiming all378bodies fully read. No unrecorded school URL does not mean exhaustive research.10global/shared remain.','assets':'No new photo or coordinate; prior100licensed photos/101points/103website identities unchanged.','remaining':{'host_missing':604,'photos':4,'coordinates':3,'websites':1,'global_agreement_denominator':None},'formal_release':False}
(out/'ccu-eighth-independent-semantic-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='independent_semantic_read_extent'},ensure_ascii=False,indent=2))
