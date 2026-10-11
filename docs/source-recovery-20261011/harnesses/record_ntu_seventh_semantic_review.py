"""Record actual independent reading scope, separately from automated hashes."""
from pathlib import Path
import hashlib, json

root = Path('/workspace/recovery-evidence-20261011/ntu-seventh-reviewed-images')
observations = json.loads((root/'new-observations.json').read_text())
assert len(observations) == 267
notes = {
    'Kumamoto': 'All 12 scanned brochure pages visually read. Original 2025/26 factsheet page 2 independently rendered and viewed: March 7, 2025 struck through, red March 14 replaces it; April 18 student application is separate. Historical second-year versus older brochure third-year difference retained. E-course iBT61 and unspecified IELTS, professor letters rejected; J-course N2 separate. Dorm room types, monthly rent, deposits, annual internet and insurance periods remain separate. Neither old source is a 2027 policy.',
    'TUFS': 'All four AY2027 information-sheet pages visually read, complete application HTML and Spring2027 checklist extraction read. GPA2/4 previous semester versus JASSO2.3/3 previous year separate. Student exchange/CoE applications and coordinator document upload all initial procedures. November15,2026 Spring and March15,2027 Fall separate. Insurance 10390/5 months or14870/11 months explicitly AY2026. Winter date typo Early February2027 to March31,2028 retained. Seven weekly classes exclude Interactive English A. Dorm fee types distinct and no guarantee.',
    'Kwansei Gakuin': 'Both 2026/27 factsheet pages visually read and six related HTML bodies fully read. Japanese/Modern Japan tracks, ordinary-course N1 or placement, expected TOEFL71 without certificate, seven periods/ten hours and24 credits remain distinct. Private Jotform not accessed. Spring2027 public documents, health handwriting and professor submission roles preserved. Tentative IBA late examinations/dorm extensions retained. Semester housing totals are not monthly rent; monthly living estimates exclude housing. NHI estimates with different periods are not combined into a bill.',
    'NUFS': 'Four HTML bodies fully read. Special-auditor undergraduate N2/graduate N1 differs from GJP, 2026 Spring test scope retained. Minimum7 classes/10.5 weekly hours versus recommended10–12 and GJP7–11 classroom periods distinct. Assigned dorm not elective, JPY35000 monthly utilities included,10000 one-time and6600 optional bedding distinct.',
    'YNU': 'Three HTML bodies fully read. JOY undergraduate home-partner nomination, old/new TOEFL80/4 or IELTS6 or JapaneseN2 retained without invented GPA. Minesawa lottery and timing distinguished from Tokiwadai room/status eligibility. Monthly shared/private rent, utilities and66000 initial nonrefundable fee remain distinct. JASSO not guaranteed.',
    'Ochanomizu': 'Full four-page FY2027 English extraction read; page4 independently rendered and visually read. Recommended GPA2.5 admits case-by-case lower scores. Female/women-identified eligibility, credit-bearing8 classes versus graduate research noncredit status retained. March18,2027 pre-registration only research; April16 autumn application separate. JPY65300 monthly utilities included,31680 entrance,4000 surety. No form submission or upload performed; public document access information unused.',
    'HUFS': 'Full current Spring/Fall2027 factsheet HTML and NHIS insurance HTML read. Fall Feb1–Apr30 nomination/application; Sept1–Dec21 semester with orientation/dorm dates TBC. English/Korean alternative qualifications preserved. Financial amounts8000000/16000000 are proof covering home tuition and living costs, not host fees. Optional intensive Korean charges and credit restrictions retained. NHIS page internally inconsistent about exemption/periods; no universal Taiwanese exemption or2027 statutory rate inferred.',
    'USP': 'Canonical undergraduate incoming HTML read. Nomination/application distinction, recommended Portuguese and non-degree/free-mover scope retained. Other USP linked documents and graduate sources were not all independently reread.',
}
report = {
    'fixed_input': 'dc9bbcddcf2cd2cf47ef7768e530c6aab6fa4401',
    'new_observations_read': len(observations),
    'schools_with_new_observations': len({o['school_name'] for o in observations}),
    'all_267_added_Chinese_text_scope_and_source_ids_read': True,
    'original_context_review': 'Risk-based independent review; full-source reading is claimed only in the named records below. Automated raw hashes and quotation matching cover all source bodies separately.',
    'school_reviews': notes,
    'other_observations_reviewed_for_scope': 'All 35 school note groups read. Checked original-year qualifiers, missing versus pending versus zero, incoming versus outgoing, programme/degree/campus exceptions, fee periods, nomination versus application, and private-form boundaries. This is not a claim that every one of the 101 new source bodies was manually reread.',
    'selection_rule_confirmed': False,
    'all_700_reference_text_scope_source_visibility': 'Passed separate fixed-module audit; integrated browser and full suite required after merge.',
    'new_photo_assets': 'None; catalog is identical except timestamp to accepted NTU input.',
    'remaining': ['282 NTU school selection rows remain pending and 6 explicitly zero.', 'Complete current requirements are not established for all288 schools.', 'Not every new public source was independently read in full; author review and automated provenance remain distinct.'],
    'review_files': [{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(root.glob('review-*.txt'))],
}
assert report['schools_with_new_observations']==35
Path('/workspace/recovery-evidence-20261011/ntu-seventh-independent-semantic-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('school_reviews','review_files')},ensure_ascii=False,indent=2))
