from pathlib import Path
import subprocess,json,hashlib,sys
app=Path('/workspace/abroad-globe-20261011');raw=Path('/workspace/recovery-evidence-20261011');bundle=app/'src/exchange_info/official_data/ccu'
scripts=['review_ccu_public_convergence.py','build_ccu_completion_reviews.py','build_ccu_completion_inventory.py','build_ccu_gap_research_queue.py','build_ccu_remaining_public_worklist.py','build_ccu_convergence_acceptance.py'];rounds=[]
for n in range(2):
 for s in scripts:
  r=subprocess.run([sys.executable,'scripts/'+s],cwd=app,capture_output=True,text=True);print(s,r.stdout,r.stderr,flush=True);assert r.returncode==0
 hashes={str(p.relative_to(app)):hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir() if p.suffix in {'.json','.jsonl','.csv'}};rounds.append(hashes)
assert rounds[0]==rounds[1]
r=json.loads((bundle/'completion-ninth-convergence-acceptance.json').read_text());assert r['changed_host_fields']==21 and r['previously_missing_host_fields_filled']==19 and r['host_status_counts']['missing']==585
p=bundle/'application_workflows.jsonl';assert p.read_bytes()==subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(app))],cwd=app)
changed=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=app,text=True).splitlines();allowed=('src/exchange_info/official_data/ccu/','docs/ccu-completion-validation-2026-10-11/','scripts/build_ccu_convergence_acceptance.py','scripts/review_ccu_public_convergence.py','scripts/fetch_ccu_public_convergence.py','tests/test_ccu_','tests/e2e/test_ccu_','docs/CCU')
unknown=[p for p in changed if not p.startswith(allowed)]
report={'source_commit':'52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8','predecessor':'dbc4afd64b4116e199c218d0d22e4223c9ff2db1','offline_rounds':2,'all_top_level_data_hashes_identical':len(hashes),'workflow55_byte_parity':True,'acceptance':r,'changed_paths':changed,'scope_check_unknown_paths':unknown,'final_hashes':hashes}
(raw/'ccu-ninth-offline-rebuild.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'hashes':len(hashes),'changed':len(changed),'scope_check_unknown_paths':unknown},ensure_ascii=False))
assert not unknown,unknown
