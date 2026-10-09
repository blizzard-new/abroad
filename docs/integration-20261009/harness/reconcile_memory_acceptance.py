"""Retain raw failures and reconcile only documented same-code/test-fixture reruns."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path('/workspace/integration-evidence')
summary = json.loads((root / 'memory-final-full-summary.json').read_text())
outcomes = json.loads((root / 'memory-final-full-case-results.json').read_text())
identity = json.loads((root / 'memory-final-release-delta-proof.json').read_text())
assert summary['all_source_guards_passed']
assert summary['candidate_sha'] == identity['full_suite_sha']
assert summary['collected_unique_cases'] == summary['executed_unique_cases'] == 2647
assert identity['changed_paths'] == ['src/exchange_info/static/index.html', 'tests/test_tku_web_evidence.py']
assert identity['all_src_paths_except_index_byte_identical'] and identity['index_delta']['exact_single_replacement']
assert all(pair['tested'] == pair['final'] for pair in identity['identical_git_objects'].values())
original_skips = json.loads((root / 'original-full-skips.json').read_text())
skip_keys = {(row['class'], row['name'], row['reason']) for row in original_skips}
actual_skips = set()
failures = {}
for shard in range(4):
    for case in ET.parse(root / f'memory-final-full-shard-{shard}' / 'results.xml').getroot().iter('testcase'):
        skipped = case.find('skipped')
        if skipped is not None:
            actual_skips.add((case.get('classname'), case.get('name'), skipped.get('message')))
        failed = case.find('failure')
        if failed is not None:
            node = case.get('classname').replace('.', '/') + '.py::' + case.get('name')
            failures[node] = failed.text or ''
assert actual_skips == skip_keys
rerun_evidence = []
for name, expected_sha, expected_cases in [
    ('memory-final-enospc-rerun', identity['full_suite_sha'], 3),
    ('memory-final-assets-contract', identity['final_head'], 6),
]:
    meta = json.loads((root / name / 'metadata.json').read_text())
    assert meta['test_result'] == 'passed'
    assert meta['start_guard'] == meta['end_guard']
    assert not meta['start_guard']['status'] and meta['start_guard']['sha'] == expected_sha
    cases = list(ET.parse(root / name / 'results.xml').getroot().iter('testcase'))
    assert len(cases) == expected_cases
    for case in cases:
        assert case.find('failure') is None and case.find('error') is None and case.find('skipped') is None
        module = case.get('classname').replace('.', '/') + '.py'
        node = module + '::' + case.get('name')
        assert node in outcomes, node
        if node in failures and module.endswith('test_navigation_guide.py'):
            assert 'No space left on device' in failures[node]
        outcomes[node] = {**outcomes[node], 'outcome': 'passed', 'validated_by': name}
    rerun_evidence.append({'name': name, 'cases': len(cases), 'sha': expected_sha, 'clean_source_guards': True})
browser_dir = root / 'memory-final-assets-browser-clean'
browser_meta = json.loads((browser_dir / 'metadata.json').read_text())
assert browser_meta['test_result'] == 'passed'
assert browser_meta['start_guard'] == browser_meta['end_guard']
assert not browser_meta['start_guard']['status'] and browser_meta['start_guard']['sha'] == identity['final_head']
browser_cases = list(ET.parse(browser_dir / 'results.xml').getroot().iter('testcase'))
assert browser_cases and all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in browser_cases)
counts = dict(Counter(row['outcome'] for row in outcomes.values()))
assert counts == {'passed': 2633, 'skipped': 14}, counts
result = {'at': datetime.now(timezone.utc).isoformat(), 'status': 'passed',
          'final_head': identity['final_head'], 'full_product_suite_sha': identity['full_suite_sha'],
          'raw_full_suite_counts': summary['counts'], 'raw_failures_retained': summary['failed_nodeids'],
          'executed_unique_cases': len(outcomes), 'effective_unique_outcomes': counts,
          'unexpected_or_unexecuted_cases': 0, 'original_skips_identical': True,
          'reruns': rerun_evidence, 'final_browser_followup_passed': len(browser_cases),
          'qualification': 'Full suite executed on f3. Final head changes only deterministic subprocess test I/O and one paired reader cache query token. All Python/JavaScript, data, sources, migrations, dependencies and runner are byte-identical. Final asset/session/browser checks and rebuilt wheel cover the final delta. Raw failed attempts are not rewritten.'}
(root / 'memory-final-acceptance-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
