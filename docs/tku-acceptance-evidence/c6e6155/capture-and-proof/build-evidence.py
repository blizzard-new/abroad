from pathlib import Path
import json,hashlib,shutil,zipfile
src=Path('/tmp/tku-ci-contract-c6e6155');root=Path('/workspace/abroad-tku-evidence-c6e6155/docs/tku-acceptance-evidence/c6e6155')
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
for name,path in [('current-c6e6155','/tmp/tku-acceptance-contract-c6e6155'),('prior-99aa7c9','/tmp/tku-acceptance-contract-99aa7c9')]:
    for p in Path(path).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:copy(p,root/'local'/name/p.relative_to(path))
for name in ['code-commit.json','pr-merge-commit.json','initial-runs.json','actual-supabase-runtime.json']:
    copy(src/name,root/'capture-and-proof'/name)
for p in src.glob('*.py'):copy(p,root/'capture-and-proof'/p.name)
copy(Path('/tmp/tku-ci-5e010b8/download-original.py'),root/'capture-and-proof/download-original.py')
for p in src.glob('job-*.log'):copy(p,root/'capture-and-proof'/p.name)
summary['latest_local']={'tested_commit':'c6e6155f2268a029f8dff0020f658d95b4c0ecc1','unit':{'passed':182,'failed':0,'actual_exit':0,'guard':json.loads(Path('/tmp/tku-acceptance-contract-c6e6155/unit-run.json').read_text())},'browser':{'passed':24,'failed':0,'actual_exit':0,'guard':json.loads(Path('/tmp/tku-acceptance-contract-c6e6155/browser-run.json').read_text())},'original_twelve_ids_passed':True,'all_1789_original_ids_preserved':True}
summary['prior_local_99aa7c9']={'tested_commit':'99aa7c9f04a8ec2109bab32b85a3fb7edc5ec667','unit':{'passed':181,'failed':1,'actual_exit':1},'browser':{'passed':24,'failed':0,'actual_exit':0},'failure':'Last old availability==open filter literal; corrected to actual common blocked predicate. All original result bytes retained; not relabelled latest.'}
summary['production_change_scope']='None since093: only three original test modules, asset-contract helper and rationale document. src,official data,supabase,.github,scripts,docs/api trees are identical; no migration,deployment,credentials,ACL/RLS/ownership or main changes.'
summary['governance_scope']='Five groups pending explicit product-scope decision; no implementation expansion, no removed tests or acceptance waiver.'
summary['previous_093_originals']='Immutable29659a56c4ef7f5896ebdff94a37f0037ecee0a6;1254 remote blobs verified by84ceca3c28ed268dd5f32f6a5bb6541512b7b1fc. Historical results remain on their own branch.'
summary['original_zip_members_byte_identical']=members
summary['remote_full_worktree_start_end']='Not captured by original CI; not invented. Local exact-SHA guards and candidate/PR identical tree verified separately.'
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(root/'README.md').write_text('''# TKU immutable contract candidate c6e6155

Original8 CI ZIPs and every actual original member,candidate/control XML,logs,IDs and real exits are preserved. Latest fixed-SHA local182 checks and24 browser cases pass; all12 corrected original IDs pass; all1789 IDs remain. Prior99aa7c9 actual181 pass/1 fail and24 browser pass retain their own SHA/results. Production src/data/migrations/config/API/scripts unchanged since093. Five governance groups remain pending; full CI failures are not waived. CI start/end worktree state was not originally recorded and is not invented. Local guards record it.

Small readable indexes are derived; original XML bytes remain intact and byte-exact CLI reassembly is checked. Signed artifact download records are never included. Earlier093 evidence is immutable on its own branch.
''')
manifest=[]
for p in sorted(root.rglob('*')):
    if p.is_file():manifest.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(root/'files-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print({'raw_files':len(manifest)+1,'original_members':members})
