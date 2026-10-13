"""Capture Wikidata candidates in bounded batches for manual identity review."""
from pathlib import Path
import json,time,requests
from capture_tku_asset_batch import B,request,paused


def values(entity,prop):
    return [c['mainsnak']['datavalue']['value'] for c in entity.get('claims',{}).get(prop,[]) if c.get('rank')!='deprecated' and 'datavalue' in c['mainsnak']]


def main():
    if paused('wikidata'):
        print(json.dumps(dict(status='paused_retry_after',**paused('wikidata'))),flush=True);return
    searches=json.loads((B/'wikidata_asset_batches.json').read_text())
    path=B/'wikidata_asset_entities.json';records=json.loads(path.read_text()) if path.exists() else []
    present={q for r in records for q in r.get('response',{}).get('entities',{})}
    qids=sorted({h['id'] for r in searches for h in r.get('response',{}).get('search',[])})
    pending=[q for q in qids if q not in present]
    for start in range(0,len(pending),30):
        params=dict(action='wbgetentities',ids='|'.join(pending[start:start+30]),format='json',languages='en|zh|zh-tw|ja|fr',props='labels|aliases|claims|descriptions|sitelinks')
        url=requests.Request('GET','https://www.wikidata.org/w/api.php',params=params).prepare().url
        result=request(url,'wikidata');records.append(result);path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(entity_batch=start//30+1,http_status=result.get('http_status'),entities=len(result.get('response',{}).get('entities',{})),error=result.get('error'))),flush=True)
        if result.get('error'):return
        time.sleep(3)
    entities={q:e for r in records for q,e in r.get('response',{}).get('entities',{}).items()}
    countries=sorted({v['id'] for e in entities.values() for v in values(e,'P17') if isinstance(v,dict)})
    cpath=B/'wikidata_asset_countries.json'
    prior=json.loads(cpath.read_text()) if cpath.exists() else []
    country_records=prior if isinstance(prior,list) else [prior]
    present_countries={q for r in country_records for q in r.get('response',{}).get('entities',{})}
    missing=[q for q in countries if q not in present_countries]
    for start in range(0,len(missing),30):
        url=requests.Request('GET','https://www.wikidata.org/w/api.php',params=dict(action='wbgetentities',ids='|'.join(missing[start:start+30]),format='json',languages='en|zh|zh-tw',props='labels|aliases')).prepare().url
        result=request(url,'wikidata');country_records.append(result)
        cpath.write_text(json.dumps(country_records,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(country_entities=len(result.get('response',{}).get('entities',{})),http_status=result.get('http_status'))),flush=True)
        if result.get('error'):return
        time.sleep(3)


if __name__=='__main__':main()
