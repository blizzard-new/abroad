"""Exercise the acceptance process against real isolated Git repositories."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


def runner_module():
    script = Path(__file__).resolve().parents[1] / 'scripts/run_tku_acceptance_suite.py'
    spec = importlib.util.spec_from_file_location('tku_acceptance_runner', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repository(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    for args in [('init', '-q'), ('config', 'user.name', 'Isolated test'),
            ('config', 'user.email', 'isolated@example.invalid')]:
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    (root / 'candidate.txt').write_text('candidate\n')
    subprocess.run(['git', 'add', 'candidate.txt'], cwd=root, check=True)
    subprocess.run(['git', 'commit', '-qm', 'candidate'], cwd=root, check=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    out = tmp_path / 'evidence'
    out.mkdir()
    return root, out, commit


def test_child_failure_is_nonzero_and_remaining_checks_still_run(tmp_path):
    root, out, commit = repository(tmp_path)
    report = {}
    code = runner_module().execute_checks(root, out, commit,
        [('fails', [sys.executable, '-c', 'raise SystemExit(7)']),
         ('continues', [sys.executable, '-c', "print('remaining check executed')"])], dict(os.environ), report)
    assert code == 1 and report['runner_exit_code'] == 1
    assert [check['exit_code'] for check in report['checks']] == [7, 0]
    assert report['all_checks_executed'] and not report['all_checks_passed']
    assert report['ending_commit'] == commit and report['ending_worktree_status'] == ''


@pytest.mark.parametrize('change', ['dirty', 'commit', 'wrong-start-sha'])
def test_candidate_drift_stops_later_checks_and_fails(tmp_path, change):
    root, out, commit = repository(tmp_path)
    script = "from pathlib import Path; Path('candidate.txt').write_text('changed\\n')"
    if change == 'commit':
        script += "; import subprocess; subprocess.run(['git','commit','-qam','changed'],check=True)"
    report = {}
    code = runner_module().execute_checks(root, out, '0' * 40 if change == 'wrong-start-sha' else commit,
        [('changes-candidate', [sys.executable, '-c', script]),
         ('must-not-run', [sys.executable, '-c', 'raise SystemExit(99)'])], dict(os.environ), report)
    assert code == 2 and report['candidate_guard_failure']
    assert not report['all_checks_executed'] and not report['all_checks_passed']
    assert len(report['checks']) == (0 if change == 'wrong-start-sha' else 1)
    if change == 'dirty':
        assert report['ending_worktree_status']
    elif change == 'commit':
        assert report['ending_commit'] != commit and report['ending_worktree_status'] == ''
