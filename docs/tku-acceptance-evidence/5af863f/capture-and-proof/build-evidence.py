from pathlib import Path
import json,hashlib,shutil,zipfile
src=Path('/tmp/tku-ci-contract-5af863f');root=Path('/workspace/abroad-tku-evidence-5af863f/docs/tku-acceptance-evidence/5af863f')
root.mkdir(parents=True,exist_ok=False)
def copy(a,b):
    b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b);assert a.read_bytes()==b.read_bytes()
summary=json.loads((src/'complete-evidence-summary.json').read_text())
members=0
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
assert members>0  # Report the actual uploaded member count, including any failure captures.
for name,path in [('current-5af863f','/tmp/tku-acceptance-contract-5af863f'),('prior-8076f4e','/tmp/tku-acceptance-contract-8076f4e')]:
    for p in Path(path).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:copy(p,root/'local'/name/p.relative_to(path))
for name in ['code-commit.json','pr-merge-commit.json','pr-tree-proof.json','actual-supabase-runtime.json']:
    copy(src/name,root/'capture-and-proof'/name)
for p in src.glob('*.py'):copy(p,root/'capture-and-proof'/p.name)
copy(Path('/tmp/tku-ci-5e010b8/download-original.py'),root/'capture-and-proof/download-original.py')
for p in src.glob('job-*.log'):copy(p,root/'capture-and-proof'/p.name)
summary['latest_local']={'tested_commit':'5af863f50f4ceecbb2b042d512137344fb2988d7','unit':{'passed':182,'failed':0,'actual_exit':0,'guard':json.loads(Path('/tmp/tku-acceptance-contract-5af863f/unit-run.json').read_text())},'browser':{'passed':32,'failed':0,'actual_exit':0,'guard':json.loads(Path('/tmp/tku-acceptance-contract-5af863f/browser-run.json').read_text())},'original_twelve_ids_passed':True,'all_1789_original_ids_preserved':True}
summary['prior_807_remote']='Both intermediate runs37898877995 and37898871475 cancelled by workflow concurrency; no complete CI claim.'
summary['production_change_scope']='None since093: only five original test modules, asset-contract helper and rationale document. src,official data,supabase,.github,scripts,docs/api unchanged at5af. No migration,deployment,credentials,ACL/RLS/ownership or main changes.'
summary['governance_scope']='User selected option3 at2026-10-09T07:33:18Z. Five original governance failures at this historical5af milestone remain failures; implementation continues on later fixedSHA.'
summary['previous_093_originals']='Immutable29659a56c4ef7f5896ebdff94a37f0037ecee0a6;1254 remote blobs verified by84ceca3c28ed268dd5f32f6a5bb6541512b7b1fc. Historical results remain on their own branch.'
summary['original_zip_members_byte_identical']=members
summary['remote_full_worktree_start_end']='Not captured by original CI; not invented. Local exact-SHA guards and candidate/PR identical tree verified separately.'
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(root/'README.md').write_text("# TKU immutable candidate5af863f\n\nEight originalCI ZIPs and all members are preserved. Both runs exercise all1789 IDs: PR1766 pass/7 fail/16 skip; push1768 pass/5 fail/16 skip. All12 corrected contracts pass. PR retains two workspace wait failures; five governance failures remain in both runs. ExactSHA local182 unit and32 browser checks pass; this does not relabel the fullCI failures. Option3 governance was authorized at07:33:18UTC and continues on later commits. No acceptance waiver. Actual local guards and eight successful runtime steps/six original complete runtime JSON reports are included; original CI worktree start/end was not captured.\n")
manifest=[]
for p in sorted(root.rglob('*')):
    if p.is_file():manifest.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(root/'files-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print({'raw_files':len(manifest)+1,'original_members':members})
