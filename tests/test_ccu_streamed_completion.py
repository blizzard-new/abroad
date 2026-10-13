"""Every school must pass source validation before a completion cache is shared."""
import json

import pytest

from exchange_info import ccu_completion as completion


def test_late_source_failure_never_publishes_a_partial_completion_index(tmp_path, monkeypatch):
    rows = [{'ccu_page': page, 'host_fields': {}, 'general_campus_fields': {
        'reference': {'status': 'reference_only', 'value': '歷年參考',
                      'evidence': [{'source_id': str(page)}]}}} for page in range(104)]
    (tmp_path/'completion-reviewed-fields.json').write_text(json.dumps({'schools': rows}))
    monkeypatch.setattr(completion, 'BUNDLE', tmp_path)
    calls = []
    reject_last = True
    def validate(bundle, evidence, checked):
        calls.append(evidence['source_id'])
        if reject_last and evidence['source_id'] == '103':
            raise ValueError('Changed final-school source')
    monkeypatch.setattr(completion, 'validate_completion_source', validate)
    completion.reviewed_completion.cache_clear()
    try:
        for _ in range(2):
            with pytest.raises(ValueError, match='Changed final-school source'):
                completion.reviewed_completion()
        assert calls == [str(page) for page in range(104)] * 2
        reject_last = False
        actual = completion.reviewed_completion()
        assert dict(actual.items()) == {row['ccu_page']: row for row in rows}
        assert calls == [str(page) for page in range(104)] * 3
    finally:
        completion.reviewed_completion.cache_clear()
