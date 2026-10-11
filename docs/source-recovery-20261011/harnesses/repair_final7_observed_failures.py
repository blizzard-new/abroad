"""Apply source-backed fixes only after all four fixed-SHA shards finish."""
from pathlib import Path
import ast
import hashlib
import json
import re

root = Path('/workspace/abroad-globe-20261011')
raw = Path('/workspace/recovery-evidence-20261011')
summary = json.loads((raw / 'integration-final7-full-suite-summary.json').read_text())
assert summary['sha'] == '5e7114182093fa77203ee946a4f86a88d3b10345'
assert summary['all_collected_nodes_accounted_exactly_once']
assert summary['all_shards_same_clean_fixed_sha']
assert summary['notrun'] == 0
changes = []

def change(relative, transform, reason):
    p = root / relative
    before = p.read_text()
    after = transform(before)
    assert before != after, relative
    p.write_text(after)
    changes.append({'path': relative, 'reason': reason,
                    'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
                    'after_sha256': hashlib.sha256(after.encode()).hexdigest()})

# Keep the full current-photo decode, attribution, capture-period and coordinate
# assertions. Two rejected photos must not be restored to satisfy an old count.
change('tests/e2e/test_tku_census_assets.py',
       lambda s: s.replace("assert len(results['photos'])==264", "assert len(results['photos'])==262"),
       'Two rejected photo assets withdrawn; points remain 264 and all individual checks remain.')

# Explicitly select the non-TKU school and load the actual new dependency in
# these small JS harnesses. Every original assertion stays unchanged.
for relative, state_before, state_after, names_before, names_after in [
    ('tests/test_ccu_semantics.py',
     'const state={dashboard:{academic_gpa_minimum:3,academic_score_minimum:70}};',
     "const state={homeSchool:'國立中正大學',dashboard:{academic_gpa_minimum:3,academic_score_minimum:70}};",
     "for(const name of ['academicScopeNeedsConfirmation'", "for(const name of ['activeHomeSchool','academicScopeNeedsConfirmation'"),
    ('tests/test_school_photo_and_match.py',
     'const state = {eligibilityProfile: null, schoolImages: []};',
     "const state = {homeSchool: '長庚大學', eligibilityProfile: null, schoolImages: []};",
     "for (const name of ['normalize'", "for (const name of ['activeHomeSchool', 'normalize'"),
    ('tests/test_pending_availability_semantics.py',
     'let planning = true;',
     "const state = {homeSchool: '國立中央大學'};\n    let planning = true;",
     "for (const name of ['partnerAvailabilityMeta'", "for (const name of ['activeHomeSchool','partnerAvailabilityMeta'"),
]:
    def transform(s):
        assert s.count(state_before) == 1 and s.count(names_before) == 1, relative
        changed = s.replace(state_before, state_after).replace(names_before, names_after)
        # JS assertions are part of the Python string, so compare assertion
        # statements literally in addition to the Python Assert AST.
        assertion_lines = lambda text: [line.strip() for line in text.splitlines() if 'assert.' in line]
        assert assertion_lines(s) == assertion_lines(changed)
        py_asserts = lambda text: [ast.dump(node, include_attributes=False) for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Assert)]
        assert py_asserts(s) == py_asserts(changed)
        return changed
    change(relative, transform, 'Original isolated JS test omitted activeHomeSchool after the TKU branch was added; load actual function with explicit home-school fixture.')

# The generic unknown state cannot claim an official future announcement.
for p in sorted((root / 'tests/e2e').glob('test_ncu_*.py')):
    if '本期名額待公告' not in p.read_text():
        continue
    change(str(p.relative_to(root)), lambda s: s.replace('本期名額待公告', '本期名額待核實'),
           'Keep the visible pending assertion aligned with unknown availability, without asserting official non-announcement.')

change('tests/e2e/test_ncu_school.py',
       lambda s: s.replace('"4天" if school == "圖爾庫"', '"前一工作日中午" if school == "圖爾庫"'),
       'Archived TYS arrival original a34e03ca68b1fd8f6d5f8fcf40a6ebd934d7c96d957511d7590a1d092412c124 says notify key-locker by noon on previous working day; no four-day rule. Retain visible arrival and insurance assertions.')

def paired_versions(s):
    for script in ['app.js', 'community-reader.js']:
        s, count = re.subn(r'(/static/' + re.escape(script) + r'\?v=)[^"\s]+',
                           r'\g<1>20261011-six-school-final-2', s)
        assert count == 1, script
    return s
change('src/exchange_info/static/index.html', paired_versions,
       'Version cooperating scripts together while preserving their load order and the existing routing contract.')

(raw / 'final7-source-backed-failure-repairs.json').write_text(json.dumps({
    'original_failed_suite_sha': summary['sha'], 'original_results_retained': True,
    'changes': changes, 'validation': 'New clean candidate must pass focused and complete same-SHA gates.'
}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(changes, ensure_ascii=False, indent=2))
