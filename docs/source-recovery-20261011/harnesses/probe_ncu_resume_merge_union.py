"""Read-only projection: fixed current matcher plus future NCU sidecar in this process only."""
from pathlib import Path
import json,subprocess,tempfile
from exchange_info import ncu_completion as ncu
from exchange_info.ncu_student_view import build_ncu_student_dashboard
from exchange_info.university_locations import load_university_locations,public_location
raw=Path('/workspace/recovery-evidence-20261011');sha='f44eaf82a2a1133f1ba91466034ae6e8d7ebc822'
with tempfile.TemporaryDirectory(prefix='ncu-next-projection-') as tmp:
 p=Path(tmp)/'campus-locations.json';p.write_bytes(subprocess.check_output(['git','show',sha+':src/exchange_info/official_data/ncu/campus-locations.json']))
 ncu.LOCATIONS=p;ncu._locations_snapshot.cache_clear();shared=load_university_locations(Path(tmp))
 own={r['school_name']:r for r in json.loads(p.read_text())['locations']};rows=[];extras=[]
 for partner in build_ncu_student_dashboard().partner_universities:
  fallback=public_location(shared,partner.school_name,partner.country);location=ncu.campus_location(partner,fallback,Path(tmp))
  if location.geocode_status=='verified':
   rows.append({'school_name':partner.school_name,'country':partner.country,'location':location.model_dump(mode='json')})
   if own.get(partner.school_name,{}).get('geocode_status')!='verified':extras.append(rows[-1])
report={'kind':'projection only; current application files and SHA unchanged, not acceptance of merged output','current_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'next_ncu_sha':sha,'author_verified':sum(r.get('geocode_status')=='verified' for r in own.values()),'predicted_integrated_verified':len(rows),'PR8_shared_valid_fallback_additions':extras,'all_verified':rows}
(raw/'ncu-resume-merge-location-projection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['all_verified','PR8_shared_valid_fallback_additions']});print('extras',[r['school_name'] for r in extras])
