from pathlib import Path
import gzip,json,subprocess
R=Path('/workspace/abroad');B=R/'sources/ncu/2026-10-08';p=B/'host-web-evidence.json.gz';rows=json.load(gzip.open(p));old={s['id']:s for s in json.loads(gzip.decompress(subprocess.check_output(['git','show','bfbef520:sources/ncu/2026-10-08/host-web-evidence.json.gz'],cwd=R)))}
for s in rows:
 if s['id']in ['host-tohoku-attachment-24','host-chiba-course-list2025']:
  s['previous_reading_review']=old[s['id']]['reading_review']
 if s['id']=='host-tohoku-attachment-24':
  limit='；其餘頁日文字型破損仍未逐字核對，學位費不覆蓋exchange協議免學費，原15頁不計全文已讀。'
  assert limit not in s['reading_review']['scope'];s['reading_review']['scope']+=limit;s['source_read_scope_note_zh']+=limit
p.write_bytes(gzip.compress(json.dumps(rows,ensure_ascii=False).encode(),mtime=0))
