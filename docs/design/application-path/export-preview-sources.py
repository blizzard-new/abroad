"""Copy two existing public workflow excerpts; never fetch or update school data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / 'src/exchange_info/official_data/ntpu/application_workflows.jsonl'
rows = [json.loads(line) for line in source.read_text(encoding='utf-8-sig').splitlines()]
selected = [row for row in rows if str(row.get('academic_year')) == '116'][:2]
keys = ('workflow_id', 'home_university', 'school_name', 'academic_year',
        'application_round', 'review_status', 'last_checked')
step_keys = ('rule_id', 'title', 'phase', 'summary', 'required_documents',
             'source_urls', 'deadline_at', 'deadline_status', 'needs_confirmation')
payload = [{**{k: row.get(k) for k in keys},
            'steps': [{k: step.get(k) for k in step_keys} for step in row['steps']]}
           for row in selected]
target = Path(__file__).with_name('source-data.js')
target.write_text('// Existing repository excerpts, not a new verification.\n'
                  'window.UNIWAY_PREVIEW_SOURCES = '
                  + json.dumps(payload, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8', newline='\n')
print('Exported existing excerpts:', ', '.join(row['school_name'] for row in selected))
