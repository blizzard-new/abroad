from pathlib import Path
import json,subprocess,os
from urllib.request import Request,urlopen
R=Path('/workspace/abroad-ntu-completion-20261011');H=Path(__file__).parent;expected='c7357f974faaec8e60ef19698d4d21633c322dc8'
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'}
with urlopen(Request('https://api.github.com/repos/blizzard-new/abroad/pulls/9',headers=headers),timeout=30) as response:p=json.load(response)
assert p['head']['sha']==expected and p['draft'] and not p['merged']
def git(*args,input=None):return subprocess.check_output(['git','-c','core.quotePath=false',*args],cwd=R,text=True,input=input).strip()
git('diff','--check');git('add','docs/ntu-completion-20261011','sources/ntu','src/exchange_info/official_data/ntu','src/exchange_info/static/assets/school-images.json','src/exchange_info/ntu_completion.py','src/exchange_info/ntu_field_review.py','scripts/export_ntu_completion_report.py','tests/test_ntu_completion.py','tests/test_ntu_destination_enrichment.py','tests/e2e/test_ntu_completion.py','tests/test_ntu_review_classification.py');git('commit','-m','Conclude all429 existing NTU candidate fields with scoped references and explicit missing items')
local=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}');remote=git('commit-tree',tree,'-p',expected,input='Conclude all429 existing NTU candidate fields with scoped references and explicit missing items\n');ref='refs/heads/ntu-stage9-publication';git('update-ref',ref,remote)
changed=git('diff','--name-only',expected,remote).splitlines();objects={line.split('\t',1)[1]:line.split()[2] for line in git('ls-tree','-r',tree).splitlines()};manifest=[{'path':path,'blob_sha':objects[path]} for path in changed if path in objects]
(H/'publish-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');receipt={'remote_commit':remote,'remote_tree':tree,'local_commit':local,'expected_previous_remote_commit':expected,'changed_blobs':len(manifest),'source_sha256':__import__('hashlib').sha256((R/'sources/ntu/completion-2026-10-11.json').read_bytes()).hexdigest()};(H/'publication.json').write_text(json.dumps(receipt,indent=2)+'\n')
subprocess.run(['git','-c','credential.helper=!gh auth git-credential','push','https://github.com/blizzard-new/abroad.git',ref+':refs/heads/data/ntu-completion-20261011'],cwd=R,check=True)
print(json.dumps(receipt))
