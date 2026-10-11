"""Last frozen three already-named public documents in the same42-school scope."""
import json
from build_tku_milestone3_host_reviews import source
from tku_capture_io import BUNDLE

def main():
 rows=[]
 for identifier,sid in [('tku-sister-33','15b582c84f5c2c90e5c61e52'),('tku-sister-174','377d52effdf7ecee727110fa')]:
  s=source(sid)
  urls=[l for l in s['links'] if ('Spring-2027' in l['url'] and l['url'].endswith('.xlsx')) or l['url']=='https://wsc.hqu.edu.cn/xzzq/lxs.htm']
  unique={l['url']:l for l in urls}
  assert len(unique)==(2 if identifier=='tku-sister-33' else 1)
  for l in unique.values():rows.append(dict(ordinal=len(rows)+1,institution_id=identifier,url=l['url'],label=l['title'],linked_from=s['source_url'],source_id=sid,purpose='remaining_explicit_public_document',reason='Final named document closeout;2 AGU campus CoE forms and1 HQU download directory. Only a clearly newer2026/2027 applicable semester guide may justify one further binary; otherwise stop. No new institutions or protected routes.'))
 (BUNDLE/'milestone6_remaining_document_inputs.json').write_text(json.dumps(dict(base_commit='4f142ea36e69338d2956b4ea5d3d37a9f4116e52',checked_date='2026-10-11',input_count=3,candidates=rows,scope='Three already-named public inputs only; current year must come from body, not labels'),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
