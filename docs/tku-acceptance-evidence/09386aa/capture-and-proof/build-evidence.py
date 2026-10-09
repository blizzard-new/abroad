from pathlib import Path
import json,hashlib,shutil,zipfile
src=Path('/tmp/tku-ci-09386aa');root=Path('/workspace/abroad-tku-evidence-09386aa/docs/tku-acceptance-evidence/09386aa');root.mkdir(parents=True,exist_ok=False)
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
for name,folder in [('current-incremental-09386aa','/tmp/tku-acceptance-09386aa'),('prior-full-1bc4ae5','/tmp/tku-acceptance-1bc4ae5-full'),('prior-incremental-1bc4ae5','/tmp/tku-acceptance-1bc4ae5'),('prior-incremental-545d19d','/tmp/tku-acceptance-545d19d'),('prior-shard2-545d19d','/tmp/tku-acceptance-545d19d-shard2'),('prior-incremental-607929e','/tmp/tku-acceptance-607929e'),('prior-predicate-error-83d7e08','/tmp/tku-acceptance-83d7e08'),('diagnostic-unguarded-multiplan-1bc4ae5','/tmp/tku-acceptance-1bc4ae5-multiplan')]:
 for p in Path(folder).rglob('*'):
  if p.is_file() and not any(x in p.parts for x in ['wheel','uv-cache','__pycache__']):copy(p,root/'local'/name/p.relative_to(folder))
for name in ['test_reader_expiry.py','repro.log','repro.xml','repro-verified.log','repro-verified.xml','observed.json','expired-reader.png','empty-legacy-before.json','first-fix.log','first-fix.xml','boundary-unit.log','boundary-unit.xml','migration-new.log']:
 p=Path('/tmp/tku-ci-reader-repro')/name
 if p.exists():copy(p,root/'synthetic-reproduction'/name)
for log in src.glob('job-*.log'):copy(log,root/'capture-and-proof'/log.name)
for directory in ['/tmp/tku-ci-607929e','/tmp/tku-ci-83d7e08','/tmp/tku-ci-545d19d','/tmp/tku-ci-1bc4ae5']:
 for q in Path(directory).glob('*.py'):copy(q,root/'capture-and-proof'/Path(directory).name/q.name)
for q in Path('/tmp/tku-ci-607929e').glob('*precommit*'):copy(q,root/'capture-and-proof'/'precommit'/q.name)
q=Path('/tmp/tku-ci-607929e/initial-driver-guard-rejection.json');copy(q,root/'capture-and-proof'/q.name)
for name in ['code-commit.json','pr-merge-commit.json','initial-runs.json','pr-runtime-completed-jobs.json','push-runtime-completed-jobs.json','summarize-evidence.py','download-original.py','build-evidence.py','verify-package.py','verify-source-scope.py','run-incremental.py','run-original-browsers.py','acceptance-driver.log','package-build.log','actual-supabase-runtime.json']:
 p=src/name
 if p.exists():copy(p,root/'capture-and-proof'/name)
summary['latest_incremental']={'tested_commit':'09386aa318c9574862a6f3b1447c5022a6c26433','counts':{'passed':66},'actual_exit_code':0,'guard':json.loads(Path('/tmp/tku-acceptance-09386aa/incremental-run.json').read_text())}
summary['prior_full_suite']={'tested_commit':'1bc4ae5ee856462552645143d6e25c8927e7268e','counts':{'passed':1511,'failed':16,'skipped':8},'all_ten_checks_executed':True,'other_nine_actual_exits':0,'relevant_browser_passed':54,'not_relabelled_as_latest_candidate':True}
summary['prior_paired_regressions']={'545d19d_shard2_passed':75,'545d19d_incremental_passed':57,'607929e_incremental_passed':57,'83d7e08_wrong_predicate_actual':{'passed':64,'failed':2},'precommit_and_unguarded_diagnostic_results_not_counted_as_guarded_acceptance':True}
summary['previous_12b_originals']='Immutable c6bd78f4fbeeb6fa4cdda012c3898121cf2f5800: push1788 all cases,1753/19/16; PR1090 executed,698 unrun,1062/13/15 plus1 internal EAGAIN. Originals retained, never rewritten.'
summary['production_database_or_deployment_changed']=False
summary['remote_ci_starting_and_ending_full_worktree_state']='Not recorded by the original CI runner; not retroactively invented. Local guards record exact start/end SHA and clean state. PR merge and head code trees match.'
summary['reproduction_scope']='All accounts, reader bodies, drafts, aliases and mutations use isolated synthetic fixtures; screenshots are not production leakage evidence.'
summary['governance_decision_document']='docs/tku-followup-governance-integration-plan-2026-10-09.md; five groups remain unexpanded pending product scope selection.'
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(root/'README.md').write_text("""# TKU immutable candidate 09386aa

Original remote candidate/main-control XML, logs, collected IDs, actual exits and uploaded ZIP digests are retained. Small indexes and extracted failure text are derived and clearly identified; original XML byte reassembly remains exact. No original XML reconstruction or result relabeling.

Latest fixed-SHA incremental: 66 pass, clean start/end. Prior 1bc full suite:1511 pass/16 fail/8 skip,54 related browser pass,other9 checks exit0; prior545 shard2:75 pass; prior83 wrong payload predicate:64 pass/2 fail. Each remains bound to its own SHA. A plain2-case diagnostic and precommit results are not promoted to guarded acceptance. Temporary607 SHA guard typo ran0 tests. Original12b PR interrupted at terminal.flush EAGAIN and its698 unrun IDs stay on its immutable branch; push all1788 with19 failures. All historical failure/precondition records preserved separately.

Governance five groups remain deliberately unexpanded, with concrete scope/effect decisions in the source document. No production migration, deployment, credentials, ACL/RLS/ownership changes or main merge. Final runner failure is retained whenever any applicable test fails; baseline failure is not a waiver.
""")

manifest=[]
for p in sorted(root.rglob('*')):
 if p.is_file():manifest.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(root/'files-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'payload_files':len(manifest)+1,'bytes':sum(r['bytes'] for r in manifest)}))
