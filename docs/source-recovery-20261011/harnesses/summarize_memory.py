from pathlib import Path
import json,hashlib,subprocess
root=Path('/workspace/recovery-evidence-20261011');app=Path('/workspace/abroad-globe-20261011')
labels=[('latest-data-before-memory','23365f9c58b059f1da6fb35b3554576ca124bb59','warm before scoped-life/hash/cache repairs',False),('pool-final-warm-memory','0d3d671ef92344970e4de1797a81b050235eecbd','warm final',True),('pool-final-cold-memory','0d3d671ef92344970e4de1797a81b050235eecbd','cold final',True)]
rows=[]
for folder,sha,label,passed in labels:
 data=json.loads((root/folder/'memory-samples.json').read_text())
 assert len(data)==162 and data[-1]['label']=='after-explicit-gc'
 rss=max(r['rss_bytes'] for r in data)/1048576;peak=max(r['peak_rss_bytes'] for r in data)/1048576
 assert (max(rss,peak)<460)==passed
 serverlog=(root/folder/'server.log').read_text()
 assert not serverlog.strip(),serverlog[:100]
 rows.append({'run':folder,'runtime_source_sha':sha,'label':label,'samples':len(data),'maximum_rss_mib':rss,'high_water_mib':peak,'final_rss_mib':data[-1]['rss_bytes']/1048576,'headroom_below_512_mib':512-max(rss,peak),'passed_460_mib':passed,'all_workload_steps_completed':True,'local_server_log_empty':True})
changes=subprocess.check_output(['git','diff','--name-only',labels[0][1],labels[1][1],'--','src/exchange_info/official_data','src/exchange_info/static','sources'],cwd=app,text=True)
assert not changes
result={'scope':'one local Uvicorn worker; browser load generator excluded from server RSS','same_final_data_before_and_after':True,'source_and_frontend_changes_between_comparison_heads':changes.splitlines(),'school_counts':{'CGU':77,'NTPU':206,'NTU':288,'CCU':104,'NCU':214,'TKU':287},'workload':'12 rounds ×6 schools ×5 parallel APIs; 3 full NCU source audits; 3×8 CCU bursts before and after; 390/1440 repeated 3 times with 36 school switches +36 six-school life detail visits +6 NTU globe/photo/life flows; final GC','samples_per_run':162,'harness_sha256':hashlib.sha256((root/'pool-final-warm-memory-command/input-scripts/profile_memory.py').read_bytes()).hexdigest(),'before_failure_policy':'deferred the budget assertion to the end so all 162 steps complete; exit 1 and failed budget preserved','runs':rows,'build_disk_incident':'Separate wheel staging briefly reached ENOSPC at 12:26:34–12:26:36 UTC and was removed. All measured API/browser assertions completed and each app server log was empty. The wheel failure and corrected successful build are both archived.'}
(root/'final-memory-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows,indent=2))
