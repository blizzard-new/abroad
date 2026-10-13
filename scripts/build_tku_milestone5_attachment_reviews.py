"""Attachment byte/type/year review, including gated responses and support guides."""
import hashlib,json
from tku_capture_io import BUNDLE,read_bytes
from build_tku_milestone3_host_reviews import source

YEARS={1:'Intrinsically undated prospective guide; filename2026 not year evidence',2:'Intrinsically undated health template linkedSpring2027',3:'Intrinsically undated behaviour/funding template linkedSpring2027',4:'Intrinsically undated course template; example cells, not course offering',5:'Actual body2026 UniversityFactsheet;2027 application not independently verified',6:'Actual bodyAY2027–28 SDW guideline;updatedSeptember2026',7:'Intrinsically undated TAO start guide linkedcurrentSDW',8:'Actual bodyupdatedSeptember2026 Pledge; not independent academic-year statement'}

def row(c,year,scope):
 s=source(c['source_id']);binary=bool(s.get('local_file'))
 if binary:
  blob=read_bytes(BUNDLE/'host_census_sources'/s['local_file']);assert hashlib.sha256(blob).hexdigest()==s['sha256'] and blob.startswith((b'%PDF',b'PK'))
 state='binary_opened_content_reviewed' if binary else 'CAPTCHA_gate_not_document' if '请输入验证码' in s.get('text','') else 'historical_template_directory_not_attachment'
 return dict(institution_id=c['institution_id'],source_id=s['id'],source_url=s['source_url'],checked_at=s['checked_at'],content_sha256=s.get('sha256'),http_status=s.get('http_status'),status=state,attachment_obtained=binary,local_file=s.get('local_file'),applicable_year=year,locator='PDF physical pages / DOCX body / XLSX XML cells' if binary else 'Actual HTML response body',quote=s.get('text','')[:500],pages=len(s.get('pages',[])),review_scope=scope)

def main():
 rows=[row(c,YEARS.get(c['ordinal'],'No document year verified; actual response only'),'Actual relevant instructions/template semantics/year; no filename-only inference; no current home document promotion') for c in json.loads((BUNDLE/'milestone5_document_capture_checks.json').read_text())]
 for name,ordinal,year,scope in [('followup',23,'Intrinsically undated Warsaw factsheet; filename2025 not academic year','All extracted text of physical pages1–2 read; actual programme rules quoted individually'),('body',2,'Actual2026 general international-student guide; not2027 guarantee','Relevant physical pages1,5,6,16 read; no claim to complete substantive review of all32 pages')]:
  c=next(c for c in json.loads((BUNDLE/f'milestone5_{name}_capture_checks.json').read_text()) if c['ordinal']==ordinal);rows.append(row(c,year,scope))
 (BUNDLE/'milestone5_attachment_reviews.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(binary_opened=sum(r['attachment_obtained'] for r in rows),captcha_gates=2,historical_directory=1)))
if __name__=='__main__':main()
