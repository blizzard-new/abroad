from research_curator import Curator
from pathlib import Path
import json,sys
c=Curator();q=json.loads((Path(__file__).parent/'priority-source-roster.json').read_text());pid=sys.argv[1];s=q[pid];print('SCHOOL',pid,s['name'],'FIELDS',s['fields'])
for sid in list(s['sources'])[int(sys.argv[2]):int(sys.argv[3])]:
 d=c.read_source(sid);print('\nSOURCE',sid,d['url'],'CHARS',len(d['text']))
 if d.get('pages'):
  for page in d['pages']:print('PDF PAGE',page['page'],'\n'+page['text'])
 else:print(d['text'])
