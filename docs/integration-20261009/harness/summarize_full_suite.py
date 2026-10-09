"""Verify every original node ID has exactly one final pytest outcome."""
import collections
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

prefix, destination = sys.argv[1:3]
root = Path('/workspace/integration-evidence')
outcomes = {}
shards = []
for shard in range(4):
    directory = root / f'{prefix}-{shard}'
    metadata = json.loads((directory / 'metadata.json').read_text())
    assert metadata['test_result'] != 'running'
    xml = ET.parse(directory / 'results.xml').getroot()
    cases = list(xml.iter('testcase'))
    rows = re.findall(r'WEB_CASE (.*?) (setup|call|teardown) (passed|failed|skipped) ([\d.]+)s',
                      (directory / 'stdout.log').read_text())
    assert len(rows) == len(cases), (shard, len(rows), len(cases))
    counts = collections.Counter(status for _, _, status, _ in rows)
    xml_counts = collections.Counter('failed' if c.find('failure') is not None or c.find('error') is not None
                                    else 'skipped' if c.find('skipped') is not None else 'passed' for c in cases)
    assert counts == xml_counts, (shard, counts, xml_counts)
    for node, phase, status, duration in rows:
        assert node not in outcomes, node
        outcomes[node] = {'outcome': status, 'phase': phase, 'duration_seconds': float(duration), 'shard': shard}
    shards.append({'shard': shard, 'metadata': metadata, 'case_count':len(cases), 'counts':dict(counts),
                   'source_guard_passed': metadata['start_guard'] == metadata['end_guard'] and not metadata['start_guard']['status']})
collection = [n for shard in range(4)
              for n in (root / f'{prefix}-{shard}/collect-nodeids.txt').read_text().splitlines()
              if n.startswith('tests/') and '::' in n]
assert len(collection) == len(set(collection))
assert set(collection) == set(outcomes), {'missing':sorted(set(collection)-set(outcomes)),
                                        'unexpected':sorted(set(outcomes)-set(collection))}
result = {'candidate_sha':shards[0]['metadata']['start_guard']['sha'], 'complete_full_suite':True,
          'collected_unique_cases':len(collection), 'executed_unique_cases':len(outcomes),
          'counts':dict(collections.Counter(r['outcome'] for r in outcomes.values())),
          'all_source_guards_passed':all(r['source_guard_passed'] for r in shards),
          'shards':shards, 'failed_nodeids':[n for n,r in outcomes.items() if r['outcome']=='failed'],
          'skipped_nodeids':[n for n,r in outcomes.items() if r['outcome']=='skipped']}
(root / (destination + '-summary.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(root / (destination + '-case-results.json')).write_text(json.dumps(outcomes,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'shards','skipped_nodeids'}},ensure_ascii=False))
