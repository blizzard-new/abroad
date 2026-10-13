"""Actual ZIP/XML cells establish2027 CoE campus values; not filenames."""
import io,json
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from build_tku_milestone3_host_reviews import source
from tku_capture_io import BUNDLE as B,read_bytes

def main():
 rows=[];ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 for sid,campus,address,entryday in [('bf53f687e0acbef4028554a8','Aoyama','東京都渋谷区渋谷4-4-25', '20'),('366d16d98d9232b4a559db3d','Sagamihara','神奈川県相模原市中央区淵野辺5-10-1','')]:
  s=source(sid);assert s['http_status']==200 and not s.get('error')
  blob=read_bytes(B/'host_census_sources'/s['local_file']);assert blob.startswith(b'PK')
  with ZipFile(io.BytesIO(blob)) as z:
   names=[e.attrib['name'] for e in ET.fromstring(z.read('xl/workbook.xml')).findall('.//s:sheet',ns)]
   assert len(names)==8 and not any(x.endswith('vbaProject.bin') for x in z.namelist())
  cells={k:v for r in s['sheets'][0]['rows'] for k,v in r};assert cells['H55']=='2027' and cells['N55']=='3' and cells.get('R55','')==entryday and address in cells['I29']
  office={k:v for r in s['sheets'][6]['rows'] for k,v in r};assert office['I41']=='2027' and office['O41']=='4' and office['S41']=='1'
  rows.append(dict(source_id=sid,source_url=s['source_url'],checked_at=s['checked_at'],content_sha256=s['sha256'],local_file=s['local_file'],campus=campus,source_period_verified=True,applicable_year='Actual2027Spring linked form; entry cells2027March and office-use enrollment2027April1; filename not used',status='binary_opened_sheet_content_reviewed',sheets=names,xml_parts=[sh['xml_part'] for sh in s['sheets']],body_cells=dict(Application_1={k:cells.get(k,'') for k in ['I29','H55','N55','R55']},AGU_Office_Use_1={k:office.get(k,'') for k in ['I41','O41','S41']}),sample_and_office_sheets_distinct=True,form_default_dates_are_guaranteed_arrival=False,current_TKU_document=False,macros_executed=False,external_links_updated=False,limitation='CoE application blanks/examples/office-use distinguished; entry20 March Aoyama vs blank day Sagamihara are defaults, not binding travel/calendar or TKU eligibility. Undated signature/health templates remain separately unverified.'))
  print(sid,campus,'eight sheets;actual2027March/April cells')
 h=source('3675c3089c34a13f131c06f2');assert '2023/01/24' in h['text'] and '2022/09/27' in h['text'] and '2019/04/22' in h['text']
 rows.append(dict(source_id=h['id'],source_url=h['source_url'],checked_at=h['checked_at'],content_sha256=h['sha256'],status='historical_template_directory_no_new_applicable_guide',quote='留学生入境前后签证办理须知\n2023/01/24',actual_listing_dates=['2023/01/24','2022/09/27','2022/09/21','2019/04/22'],new2026_2027_exchange_guide_verified=False,limitation='Specific named download directory read; listed visa/pledge/health items historical, no newer2026/2027 semester guide located in this body. Does not prove official not announced elsewhere; stop without fetching unrelated historical visa forms.'))
 (B/'milestone6_remaining_document_reviews.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
