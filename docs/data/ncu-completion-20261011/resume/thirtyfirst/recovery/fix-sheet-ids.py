from pathlib import Path
import json,gzip,zipfile,xml.etree.ElementTree as E
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtyfirst');B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/thirtyfirst';ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
with zipfile.ZipFile(W/'host-sdu-id.xlsx')as z:
 rels={r.attrib['Id']:r.attrib['Target']for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))};mapping={s.attrib['name']:'xl/'+rels[s.attrib['{'+ns['r']+'}id']]for s in E.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',ns)}
p=B/'host-web-evidence.json.gz';pack=json.load(gzip.open(p));s=next(s for s in pack if s['id']=='host-sdu-id');assert set(mapping.values())=={p['sheet']for p in s['pages']};s['reading_review']['sheet_names_reviewed']=list(mapping);s['reading_review']['sheets_reviewed']=list(mapping.values());s['reading_review']['sheet_name_to_archive_part']=mapping;p.write_bytes(gzip.compress(json.dumps(pack,ensure_ascii=False).encode(),mtime=0))
p=D/'sdu-blank-workbook-cells.json';x=json.load(open(p));x['sheet_name_to_archive_part']=mapping;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');print(mapping)
