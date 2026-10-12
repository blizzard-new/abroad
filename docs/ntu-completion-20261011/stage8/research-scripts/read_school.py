from research_curator import Curator
from pathlib import Path
import json,sys
c=Curator();r=Path(__file__).parent;q=json.loads((r/'priority-source-roster.json').read_text())
import hashlib
for pid in sys.argv[1:]:
 print('SCHOOL',pid,q[pid]['name']);print('FIELDS',q[pid]['fields'])
 seen={}
 for sid in q[pid]['sources']:
  d=c.read_source(sid);print('\nSOURCE',sid,d['url'],'SHA',d.get('sha256'),'CHARS',len(d['text']))
  key=(d.get('sha256'),hashlib.sha256(d['text'].encode()).hexdigest())
  if key in seen:
   print('EXACT RAW AND EXTRACTED TEXT ALIAS of fully displayed source',seen[key]);continue
  seen[key]=sid
  if d.get('pages'):
   for page in d['pages']:print('PDF PAGE',page['page'],'\n'+page['text'])
  else:print(d['text'])
