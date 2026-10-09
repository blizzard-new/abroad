from pathlib import Path
import json,hashlib,shutil,zipfile
src=Path('/tmp/tku-ci-governance-e1c551a')
root=Path('/workspace/abroad-tku-evidence-e1c551a/docs/tku-acceptance-evidence/e1c551a')
root.mkdir(parents=True,exist_ok=False)
def copy(a,b):
    b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b);assert a.read_bytes()==b.read_bytes()
summary=json.loads((src/'complete-evidence-summary.json').read_text());members=0
for kind in ['pr','push']:
    for suffix in ['run','jobs','artifacts','case-results','original-failure-triage']:
        copy(src/f'{kind}-{suffix}.json',root/'remote'/f'{kind}-{suffix}.json')
    for row in json.loads((src/f'{kind}-artifacts.json').read_text())['artifacts']:
        aid=str(row['id']);z=src/'remote-artifacts'/f'{aid}.zip';copy(z,root/'remote/original-zips'/z.name)
        with zipfile.ZipFile(z) as archive:
            for name in archive.namelist():
                if not name.endswith('/'):
                    p=src/'remote-artifacts'/aid/name;copy(p,root/'remote'/kind/row['name']/name);assert p.read_bytes()==archive.read(name);members+=1
        copy(src/'remote-artifacts'/f'{aid}-download-proof.json',root/'remote/download-proof'/f'{aid}.json')
for tag,folder in [('current-e1c551a','/tmp/tku-governance-e1c551a'),('prior-e300479','/tmp/tku-governance-e300479')]:
    for p in Path(folder).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:copy(p,root/'local'/tag/p.relative_to(folder))
for name in ['code-commit.json','pr-merge-commit.json','actual-supabase-runtime.json']:
    copy(src/name,root/'capture-and-proof'/name)
for p in src.glob('*.py'):copy(p,root/'capture-and-proof'/p.name)
copy(Path('/tmp/tku-ci-5e010b8/download-original.py'),root/'capture-and-proof/download-original.py')
for p in src.glob('job-*.log'):copy(p,root/'capture-and-proof'/p.name)
summary['latest_local']={'tested_commit':'e1c551a80ae4503a0c3be4359d028dd1562f3c6c',
    'unit_passed':57,'browser_passed':1,'actual_exit_codes':[0,0],
    'unit_guard':json.loads(Path('/tmp/tku-governance-e1c551a/unit-run.json').read_text()),
    'browser_guard':json.loads(Path('/tmp/tku-governance-e1c551a/browser-run.json').read_text())}
summary['historical_e300479']='Original fixedSHA32 unit pass/1 browser failure retained. Status-filter correction follows in e1; no historical relabel.'
summary['governance_scope']='M1 existing API/UI/service adapters only. Atomic/CAS/recovery integration is later3a8ca75; greenM1 CI does not claim fulltransaction acceptance.'
summary['historical_5af']='PR1766P7F16S and push1768P5F16S preserved on artifacts/tku-acceptance-5af863f; immutable complete payloadab781254,774 remote blobs verified byb7e6cbc4. PR390/1754 wait failures remain failures on their original SHA.'
summary['original_zip_members_byte_identical']=members
summary['remote_full_worktree_start_end']='Not captured by original CI; not invented. Actual local exact-SHA clean guards and PR/code identical tree separately verified.'
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(root/'README.md').write_text('# TKU governance adapter milestone e1c551a\n\nBoth completeCI runs:1786 passed/0 failed/16 skipped,1802 uniqueIDs/185 files. All1789 original093 IDs and all66 original4e failure IDs retained and actually exercised passing. Eight originalZIPs and all original members/XML/control logs/real exits preserved. Six actualcomplete runtime reports and eight original successful runtime steps validate33migrations; atomicgovernance is later3a8ca75, not claimed here. LocalfixedSHA57unit/1originalbrowser passes with cleanstart/endguards. Historicale300 browserfailure and5af fullCI failures remain attached to their own SHAs. No acceptance waiver; no mainmerge/deploy/productionDB or credentials/permission changes.\n')
manifest=[]
for p in sorted(root.rglob('*')):
    if p.is_file():manifest.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(root/'files-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print({'raw_files':len(manifest)+1,'original_members':members})
