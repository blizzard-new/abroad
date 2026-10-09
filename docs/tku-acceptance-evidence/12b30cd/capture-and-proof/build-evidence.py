from pathlib import Path
import json,hashlib,shutil,zipfile
src=Path('/tmp/tku-ci-12b30cd');root=Path('/workspace/abroad-tku-evidence-12b30cd/docs/tku-acceptance-evidence/12b30cd');root.mkdir(parents=True,exist_ok=False)
def copy(source,destination):
 destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination);assert destination.read_bytes()==source.read_bytes()
summary=json.loads((src/'complete-evidence-summary.json').read_text())
for kind in ['pr','push']:
 for suffix in ['run','jobs','artifacts','case-results','original-failure-triage']:
  copy(src/f'{kind}-{suffix}.json',root/'remote'/f'{kind}-{suffix}.json')
 meta=json.loads((src/f'{kind}-artifacts.json').read_text())
 for row in meta['artifacts']:
  aid=str(row['id']);z=src/'remote-artifacts'/f'{aid}.zip';copy(z,root/'remote'/'original-zips'/z.name)
  with zipfile.ZipFile(z) as archive:
   for name in archive.namelist():
    if not name.endswith('/'):
     p=src/'remote-artifacts'/aid/name;copy(p,root/'remote'/kind/row['name']/name);assert p.read_bytes()==archive.read(name)
  copy(src/'remote-artifacts'/f'{aid}-download-proof.json',root/'remote'/'download-proof'/f'{aid}.json')
for name,folder in [('incremental-first','/tmp/tku-acceptance-12b30cd'),('original-browsers-separated','/tmp/tku-acceptance-12b30cd-browsers'),('full-suite-browser-path-error','/tmp/tku-acceptance-12b30cd-full'),('case4-prior-source-5aeb8bb','/tmp/tku-acceptance-5aeb8bb')]:
 for p in Path(folder).rglob('*'):
  if p.is_file() and not any(x in p.parts for x in ['wheel','uv-cache','__pycache__']):copy(p,root/'local'/name/p.relative_to(folder))
for name in ['test_reader_expiry.py','repro.log','repro.xml','repro-verified.log','repro-verified.xml','observed.json','expired-reader.png','empty-legacy-before.json','first-fix.log','first-fix.xml','boundary-unit.log','boundary-unit.xml','migration-new.log']:
 p=Path('/tmp/tku-ci-reader-repro')/name
 if p.exists():copy(p,root/'synthetic-reproduction'/name)
for log in src.glob('job-*.log'):copy(log,root/'capture-and-proof'/log.name)
for name in ['code-commit.json','pr-merge-commit.json','initial-runs.json','pr-runtime-completed-jobs.json','push-runtime-completed-jobs.json','summarize-evidence.py','download-original.py','build-evidence.py','verify-package.py','verify-source-scope.py','run-incremental.py','run-original-browsers.py','acceptance-driver.log','package-build.log','actual-supabase-runtime.json']:
 p=src/name
 if p.exists():copy(p,root/'capture-and-proof'/name)
summary['local_incremental_first']={'counts':{'passed':52,'errors':7},'actual_exit_code':1,'errors':'Seven original browser cases did not execute because page fixture was not found. Original XML/log retained.'}
summary['local_original_browsers_separate']={'counts':{'passed':7},'actual_exit_code':0,'guard':json.loads(Path('/tmp/tku-acceptance-12b30cd-browsers/incremental-run.json').read_text())}
summary['local_full_suite']={'counts':{'passed':1456,'failed':17,'skipped':8,'errors':54},'actual_exit_code':1,'all_ten_checks_executed':True,'browser_errors':'Invocation omitted the installed PLAYWRIGHT_BROWSERS_PATH; launch searched an absent default executable. Synthetic switching check did run. No setup error counted as passing.'}
summary['remaining_followup']='Follow-up commits separately restore SQL declaration compatibility, drain reader boot, use native sort keyboard input, protect all pytest writers with streamed regular-file output, and await the actual reordered top-level PUT. Later candidate results are never attributed to 12b30cd.'
summary['remote_execution_note']='PR shard0 actual exit3 after terminalwriter.flush EAGAIN; incomplete case execution/unrun IDs remain explicit. Push completed all 1788 cases with 19 failures. Workflow completion is not all-case completion.'
summary['production_database_or_deployment_changed']=False
summary['remote_ci_starting_and_ending_full_worktree_state']='Not recorded by this original CI runner; not retroactively invented. Local guards record exact start/end SHA and clean state.'
summary['reproduction_scope']='All reader content, accounts, aliases and empty-board writes are isolated synthetic fixtures. Before screenshots are not production leakage evidence; setup-auth failure and corrected reproduction are preserved distinctly.'
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(root/'README.md').write_text('''# TKU immutable boundary candidate 12b30cd

Each run retains its original XML, log, collected IDs, actual exit and candidate SHA. Original uploaded ZIP members are byte-identical and checked against published digests. Derived JSON indexes are not substitute original JUnit. The 5e010b8 payload remains on its own immutable branch/commit; later 1bc4ae5 results are separate.

The first incremental invocation passed 52 cases but seven browser nodes errored at fixture setup; all seven separately passed at the same clean SHA. The first full suite omitted the installed browser directory: 54 setup errors, 1456 pass, 17 failure, 8 skip. Original SQL declaration compatibility failure is retained. Exact source guards, package and 851 original workflow hashes are in local evidence. Remote CI did not record its full start/end dirty state; unknown fields are not filled from local checks.

Governance five groups remain deliberately unexpanded. No production migrations, deployment, credentials, grants, RLS, ownership, main merge or other school's worktree edits.
''')
manifest=[]
for p in sorted(root.rglob('*')):
 if p.is_file():manifest.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(root/'files-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'payload_files':len(manifest)+1,'bytes':sum(r['bytes'] for r in manifest)}))
