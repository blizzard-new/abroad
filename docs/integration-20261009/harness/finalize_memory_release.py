"""Require actual post-deploy evidence before recording bounded release acceptance."""
from datetime import datetime, timezone
import json
from pathlib import Path

root = Path('/workspace/integration-evidence')
read = lambda name: json.loads((root / name).read_text())
stamp = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00'))
observation = read('memory-production-final-observation.json')
remote = read('memory-final-render-configuration.json')
deploy = remote['deploy']
assert deploy['status'] == 'live' and deploy['commit']['id'] == '8139be4d3604a60265029dbbe41af21c094e609d'
assert all(remote['unchanged_configuration_checks'].values())
assert observation['events'] == []
assert observation['app_errors']['logs'] == [] and not observation['app_errors']['hasMore']
assert (stamp(observation['checked_at']) - stamp(deploy['finishedAt'])).total_seconds() >= 900
instance = 'srv-db26bgjbc2fs73fdsmhg-qvscr'
def series(kind):
    metric = next(m for m in observation['metrics']['metrics'] if m['type'] == kind)
    matches = [s for s in metric['data'] if any(label['field'] == 'instance' and label['value'] == instance for label in s['labels'])]
    assert len(matches) == 1
    return matches[0]['values']
usage, limits = series('memory_usage'), series('memory_limit')
peak = max(v['value'] for v in usage)
limit = min(v['value'] for v in limits)
assert peak < limit
quiet_start = stamp(read('memory-production-ntu/metadata.json')['finished_at'])
quiet = [v for v in usage if stamp(v['timestamp']) >= quiet_start]
assert len(quiet) >= 10 and (stamp(quiet[-1]['timestamp']) - quiet_start).total_seconds() >= 300
health = read('memory-production-quiet-health.json')
assert health and all(x['status'] == 200 and x['body']['status'] == 'ok' for x in health)
assert (stamp(health[-1]['at']) - stamp(deploy['finishedAt'])).total_seconds() >= 900
for name in ['memory-production-identity', 'memory-production-six-school', 'memory-production-ntu']:
    meta = read(name + '/metadata.json')
    assert meta['test_result'] == 'passed' and meta['start_guard'] == meta['end_guard']
    assert not meta['start_guard']['status'] and meta['start_guard']['sha'] == '49882dfce64449abeb682d01ae01a8da5c10ba8d'
local = read('memory-final-post-browser-burst-summary.json')
assert local['status'] == 'passed' and local['source_guards_clean'] and local['headroom_to512MiB_bytes'] > 0
acceptance = read('memory-final-acceptance-summary.json')
assert acceptance['status'] == 'passed' and acceptance['effective_unique_outcomes'] == {'passed': 2633, 'skipped': 14}
runtime = read('memory-final-runtime-result.json')
assert runtime['status'] == runtime['cleanup_status'] == 'passed' and runtime['migration_count'] == 35
github = read('final-five-pr-github-state.json')
assert github['main'] == deploy['commit']['id'] and github['quality']['state'] == 'disabled_manually'
old = read('pr2-render-memory-502-metrics.json')
old_series = next(s for m in old['metrics'] if m['type'] == 'memory_usage' for s in m['data'] if any(x['field'] == 'instance' and x['value'].endswith('-smwhz') for x in s['labels']))
old_peak = max(v['value'] for v in old_series['values'])
result = {
    'status': 'passed_with_bounded_observation', 'finalized_at': datetime.now(timezone.utc).isoformat(),
    'accepted_head': '49882dfce64449abeb682d01ae01a8da5c10ba8d', 'main_merge': deploy['commit']['id'],
    'deploy_id': deploy['id'], 'live_at': deploy['finishedAt'], 'instance': instance,
    'observed_until': observation['checked_at'],
    'minutes_since_live': (stamp(observation['checked_at']) - stamp(deploy['finishedAt'])).total_seconds() / 60,
    'last_catalogue_browser_test_finished': quiet_start.isoformat(),
    'quiet_observation_minutes': (stamp(quiet[-1]['timestamp']) - quiet_start).total_seconds() / 60,
    'sampled_memory_peak_bytes': peak, 'sampled_memory_peak_mib': peak / 2**20,
    'memory_limit_bytes': limit, 'minimum_observed_headroom_bytes': limit - peak,
    'minimum_observed_headroom_mib': (limit - peak) / 2**20,
    'latest_memory_bytes': usage[-1]['value'], 'latest_memory_mib': usage[-1]['value'] / 2**20,
    'quiet_sample_range_bytes': [min(v['value'] for v in quiet), max(v['value'] for v in quiet)],
    'previous_oom_sampled_peak_bytes': old_peak, 'previous_oom_sampled_peak_mib': old_peak / 2**20,
    'previous_oom_event': 'evt-db4gsjp7lnhs73db9320',
    'new_failure_restart_events': 0, 'app_error_log_entries': 0,
    'production_checks': {'static_exact_bytes': 2, 'school_http': 6, 'guest_forum_denials': 6, 'school_browser_switches': 12, 'ntu_globe_photo_life_widths': [390, 1440], 'health_openapi': 'passed'},
    'full_suite': acceptance, 'final_head_post_browser_burst_peak_mib': local['peak_overall_mib'],
    'database': '35 migrations already applied and read back; PR6 adds none; full isolated runtime35 passed',
    'quality': 'disabled_manually', 'settings_credentials_permissions_paid_changes': False,
    'qualification': 'Observed low-load public flows and quiet interval passed; 30-second Render samples are not instantaneous peaks or a guarantee for arbitrary future traffic. Production concurrency stress was not performed. Existing data gaps and14original skips remain explicit.'
}
(root / 'final-release-acceptance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in {'full_suite', 'production_checks'}}, ensure_ascii=False))
