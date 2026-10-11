from pathlib import Path
import ast, hashlib, json
tools=Path('/workspace/recovery-tools-20261011')
source=tools/'profile_growth_memory.py'; target=tools/'profile_final4_growth_memory.py'
before=source.read_text()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='f71bf3bf6e3bc2ed38610a3beef0c2d9978bd756f11846aac8aee36845c3eefe'
changes={"{'photos':264,'points':260,'representative':255}":"{'photos':262,'points':264,'representative':255}","all-264-tku-photos-and-260-points-":"all-262-tku-photos-and-264-points-"}
after=before
for old,new in changes.items():
    assert after.count(old)==1
    after=after.replace(old,new)
target.write_text(after)
reverse=after
for old,new in changes.items(): reverse=reverse.replace(new,old)
assert reverse==before
digest=hashlib.sha256(target.read_bytes()).hexdigest()
observer=(tools/'observe_memory_browser_failures.py').read_text()
observer=observer.replace("profile_growth_memory.py","profile_final4_growth_memory.py").replace('f71bf3bf6e3bc2ed38610a3beef0c2d9978bd756f11846aac8aee36845c3eefe',digest)
(tools/'observe_final4_memory_browser_failures.py').write_text(observer)
report={'original_harness_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'final4_harness_sha256':digest,'exact_replacements':changes,'all_other_bytes_identical':True,'reason':'Fixed authorized TKU input withdrew two photos and added four independently reviewed campus points; update exact inventory expectation, retaining every image.decode, credit, map and school-scope assertion. Workload, waits and 460 MiB gate unchanged.','samples_expected':175}
Path('/workspace/recovery-evidence-20261011/final4-memory-harness-reconciliation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
