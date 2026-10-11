from pathlib import Path
import datetime, hashlib, json, subprocess

root = Path('/workspace/recovery-evidence-20261011')
app = Path('/workspace/abroad-globe-20261011')
run = root/'integration-final4-full-supabase-runtime'
meta = json.loads((run/'metadata.json').read_text())
report = next(json.loads(line) for line in reversed((run/'stdout.log').read_text().splitlines()) if line.startswith('{"account_deletion":'))
assert meta['test_result'] == report['status'] == report['cleanup_status'] == 'passed'
assert meta['start_guard'] == meta['end_guard'] and meta['start_guard']['status'] == ''
# Keep the full raw runtime output. This companion removes only verbose synthetic RPC payloads.
summary = {k: v for k, v in report.items() if k != 'atomic_governance'}
summary['atomic_governance'] = {k:v for k,v in report['atomic_governance'].items() if k != 'rpc_evidence'}
summary.update(candidate=meta['start_guard'], run=run.name, raw_stdout_sha256=hashlib.sha256((run/'stdout.log').read_bytes()).hexdigest(), raw_stdout_bytes=(run/'stdout.log').stat().st_size)
(root/'integration-final4-full-runtime-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
inputs = json.loads((root/'final3-fixed-input-ancestry.json').read_text())['fixed_inputs']
def git(*args): return subprocess.check_output(['git',*args],cwd=app,text=True).strip()
sha = git('rev-parse','HEAD')
for fixed in inputs.values(): subprocess.run(['git','merge-base','--is-ancestor',fixed,sha],cwd=app,check=True)
assert not git('status','--porcelain')
assert not git('diff','--name-only','59a20f27fcee00fb597abc79e75ec11778317422',sha,'--','supabase/migrations')
ancestry = {'candidate':sha, 'tree':git('rev-parse','HEAD^{tree}'),'clean':True,'fixed_inputs':inputs,'all_inputs_ancestors':True,'migration_diff_from_main59':[],'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(root/'final4-fixed-input-ancestry.json').write_text(json.dumps(ancestry,indent=2)+'\n')
print(json.dumps({'candidate':sha,'runtime':'passed','migrations':report['migration_count'],'governance_checks':report['atomic_governance']['check_count'],'ancestry':'passed'}))
