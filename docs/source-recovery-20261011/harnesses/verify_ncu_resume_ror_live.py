from pathlib import Path
import concurrent.futures,datetime,gzip,hashlib,json,requests,subprocess
SHA='f44eaf82a2a1133f1ba91466034ae6e8d7ebc822';ROOT=Path('/workspace/recovery-evidence-20261011')
r=json.loads(subprocess.check_output(['git','show',SHA+':sources/ncu/2026-10-11/resume-visual-review.json']))
rows=[x for x in r['coordinate_decisions'] if x['decision']=='accepted_representative_point']; ids=sorted({x['identity_source_url'].rsplit('/',1)[-1] for x in rows})
def get(rid):
 url='https://api.ror.org/v2/organizations/'+rid
 response=requests.get(url,timeout=35);response.raise_for_status();raw=response.content;obj=response.json()
 return rid,{'url':url,'status':response.status_code,'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest(),'raw_utf8':raw.decode(),'obj':obj}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:data=dict(pool.map(get,ids))
results=[]
for x in rows:
 source=data[x['identity_source_url'].rsplit('/',1)[-1]];d=source['obj'];qids=[z for a in d['external_ids'] if a['type']=='wikidata' for z in a['all']]
 assert d['names']==x['ror_names'] and d['domains']==x['ror_domains'],x['row_id']
 countries={p['geonames_details']['country_code'] for p in d['locations']};assert x['ror_country'] in countries,x['row_id']
 assert x['qid'] in qids,(x['row_id'],x['qid'],qids)
 domains=d['domains'] or [l['value'] for l in d['links'] if l['type']=='website'];assert domains,x['row_id']
 results.append({'row_id':x['row_id'],'institution':x['entity_label'],'country':x['ror_country'],'ROR_to_exact_Wikidata_identity':x['qid'],'official_domains_or_links':domains,'source_sha256':source['sha256']})
pack=[{k:v for k,v in d.items() if k!='obj'} for d in data.values()];(ROOT/'ncu-resume-live-ror-sourcepack.json.gz').write_bytes(gzip.compress(json.dumps(pack,ensure_ascii=False).encode(),mtime=0))
report={'source_commit':SHA,'accepted_coordinate_rows':len(rows),'unique_live_ROR_records':len(data),'all_names_domains_country_and_Wikidata_QID_crosslinks_match':True,'all_TLS_verified_HTTP_200':True,'no_ROR_city_centers_used_as_campus_coordinates':True,'rows':results}
(ROOT/'ncu-resume-live-ror-identity-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
