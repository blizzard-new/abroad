from pathlib import Path
import hashlib, json, resource, sys, time
from exchange_info import tku_census as census
from json_object_stream_prototype import read_json_object_array
start=time.monotonic()
if sys.argv[1]=='original':
    summary,rows,index=census._snapshot()
    aliases=index.aliases
else:
    rows,aliases={},{}
    def receive(row):
        identifier=row['id']
        assert identifier not in rows
        rows[identifier]=json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()
        names={row['school_name'],census.census_school_name(row)}
        names.update(census.programme_map()[pid]['fields']['school_name']['value'] for pid in row.get('programme_ids',[]))
        aliases.update({name:identifier for name in names})
    with (census.BUNDLE/'full_census_audit.json').open(encoding='utf-8') as handle:
        metadata=read_json_object_array(handle,'schools',receive)
    summary=json.dumps(metadata,ensure_ascii=False,separators=(',',':')).encode()
report={'mode':sys.argv[1],'candidate_source':'7a7c7e3560527ce08ca225c0930397772a8b79aa','diagnostic_only':True,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'seconds':time.monotonic()-start,'rows':len(rows),'row_payload_bytes':sum(len(p) for p in rows.values()),'ordered_row_hash':hashlib.sha256(b''.join(rows.values())).hexdigest(),'summary_hash':hashlib.sha256(summary).hexdigest(),'alias_hash':hashlib.sha256(json.dumps(aliases,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
print(json.dumps(report))
