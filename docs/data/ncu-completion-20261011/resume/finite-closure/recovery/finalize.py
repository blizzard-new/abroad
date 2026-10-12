from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,subprocess,shutil,xml.etree.ElementTree as ET
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/finite-closure');D=R/'docs/data/ncu-completion-20261011/resume/finite-closure';CANDIDATE='61dd19069c49efac327a9cc8951a29b332ad0fcd';FINAL_DATA='233e8f7b7a0324756f5ad8bad62e6a2f8727cf25'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==FINAL_DATA

def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def results(name):
 root=ET.parse(W/name).getroot();cases=root.findall('.//testcase');failed=[c.attrib['classname']+'::'+c.attrib['name']for c in cases if c.find('failure')is not None or c.find('error')is not None];passed=[c.attrib['classname']+'::'+c.attrib['name']for c in cases if c.find('failure')is None and c.find('error')is None and c.find('skipped')is None];return {'cases':len(cases),'failed':failed,'passed':passed}
reg=results('regression.xml');fixed=results('regression-repair-final.xml');browser=results('browser.xml');browserfix=results('browser-utar.xml')
assert len(reg['passed'])==513 and len(reg['failed'])==2;assert not fixed['failed'] and len(fixed['passed'])==23;assert set(reg['failed'])<=set(fixed['passed']);assert len(browser['passed'])==10 and not browser['failed'];assert len(browserfix['passed'])==2 and not browserfix['failed']
api=json.load(open(W/'pending-chinese-cards-after.json'));assert api['partners']==214 and api['pending_evidence_rows']==0
old=json.load(open('/workspace/ncu-resume-work/browser-output-fix/tracked-png-before.json'));assert len(old)==1399;assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in old.items())
prior=[p for p in subprocess.check_output(['git','ls-tree','-rz','--name-only','bfbef520'],cwd=R).decode().split('\0')if p.endswith('.png')];assert len(prior)==1948
assert all(subprocess.check_output(['git','hash-object',p],cwd=R).strip()==subprocess.check_output(['git','rev-parse','bfbef520:'+p],cwd=R).strip()for p in prior)
shots=sorted(Path('/tmp/ncu-final-browser').rglob('*-final.png'))+sorted(Path('/tmp/ncu-final-browser-utar').rglob('*-final.png'));assert len(shots)==12
captures=[{'tmp_path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'visually_inspected':True,'accepted_final_capture':not('/ncu-final-browser/'in str(p)and p.name.startswith('utar')),'note':'原UTAR截圖以補測可見中文費用段落版本取代；全部只保留tmp_path，未寫入受控PNG。'}for p in shots];js(D/'browser-captures.json',captures)
for name in ['regression.log','regression.xml','regression-repair.log','regression-repair.xml','regression-repair-final.log','regression-repair-final.xml','browser.log','browser.xml','browser-utar.log','browser-utar.xml','all-life.log','build-repair.log']:
 raw=(W/name).read_bytes();clean='\n'.join(l.rstrip()for l in raw.decode().splitlines()).rstrip()+'\n';(D/name).write_text(clean)
for name in ['pending-chinese-cards-after.json','life-contexts-after.json.gz']:shutil.copy2(W/name,D/('all-214-'+name))
for name in ['check_all_life.py','finalize.py']:shutil.copy2(W/name,D/'recovery'/name)
classification=json.load(open(D/'frozen-candidate-classification.json'));sources={s['id']:s for s in json.load(gzip.open(R/'src/exchange_info/official_data/ncu/source-evidence.json.gz'))};drive=[sources[s['id']]for s in json.load(gzip.open(R/'sources/ncu/2026-10-08/drive-evidence.json.gz'))]
validation={'checked_at':datetime.now(timezone.utc).isoformat(),'full_run_candidate_sha':CANDIDATE,'final_data_sha':FINAL_DATA,'finite_scope_acceptance_complete':True,'all_public_exchange_data_complete':False,'full_regression':{'collected':515,'initial_passed':513,'initial_failed':reg['failed'],'subsequent_targeted_checks':23,'remaining_failures':[],'repair_sha':FINAL_DATA,'note':'只跑一次完整套件；修正舊頁數斷言，補回東北未讀頁破損字型限制，再跑受影響23項。不是宣稱最終SHA重新515項全跑。'},'browser':{'initial_scenarios_passed':10,'targeted_capture_repairs_passed':2,'capture_repair_sha':'8fe9ef07e18c5fb40eab606c2330624cff54390d','accepted_final_captures':10,'images_inspected':12,'screenshots_written_only_to_tmp_path':True,'later_source_metadata_repair_only':True},'all_214_partner_life_api':{k:v for k,v in api.items()if k!='items'},'historic_png_checked':1399,'all_preclosure_tracked_png_checked':1948,'prior_png_changed':0,'new_source_page_pngs':16,'new_browser_pngs_in_git':0,'full_original_sources_since_frozen_300':20,'remaining_not_fully_read':280,'remaining_cited_sources':59,'remaining_cited_valid_unique_sha':55,'remaining_cited_sources_without_sha':1,'remaining_cited_alias_extras':3,'remaining_uncited_candidates':221,'cited_field_sources_lacking_reading_evidence_except_blocked_historical_excerpt':[],'new_cited_parts_read':61,'blocked_historical_original_parts':2,'drive_full_original_read':sum(s['content_status']['all_pages_read']for s in drive),'drive_sources_with_some_visual_review':sum(s['content_status']['visual_reviewed']for s in drive),'reviewed_host_records':155,'partners_without_manual_host_review':59,'representative_partner_locations':214,'licensed_photo_items':202,'unique_photo_sha':199,'missing_licensed_photos':12,'reference_translation_rows':753,'quota_unknown':214,'current_fully_verified':0,'strict_current_gaps':3222,'total_field_cells':4066,'shared_runtime_or_matcher_changed':False,'integration_remains_user_paused':True,'original_untransferred_fifth_batch_used':False}
js(D/'validation.json',validation)
(D/'FINAL-ACCEPTANCE.md').write_text(f'''# 有限範圍驗收結果

資料候選 `{CANDIDATE}`；最後資料修補 `{FINAL_DATA}`。後續只新增驗收記錄，不改應用資料。

一次完整回歸515項：初次513通過、2失敗。兩項舊閱讀頁數斷言更新後，補測發現東北未核頁日文字型破損限制未保留，已補回資料原有限制與前次閱讀紀錄；受影響23項全部通過，原兩項失敗均已覆蓋。沒有冒稱最終SHA重新全跑515項。完整與兩次補測原始失敗／成功記錄均保存。

五情境390／1440共10browser通過。初次UTAR手機截图未定位費用段落，修正腳本選可見中文li後只補跑UTAR兩尺寸，2通過。12圖全部實看、接受10張最終圖；PNG只在tmp_path，路徑／SHA見browser-captures.json。資料頁顯示B2只在西班牙、RM1000–RM1200只在UTAR且明標年份未核；九工完整兩頁仍非116、Aarhus學院20＋10例外及Chuo協議非配額都可見。最後東北修補只恢復來源閱讀限制，不改前述五校資料／介面。

214校生活API於{api['checked_at']}全部成功、待翻譯0。其後只修來源閱讀metadata；已驗收卡片文字無變更。原1399與本輪之前1948 PNG位元組未變，共用matcher／runtime未改。資料詳細分母、221候選與59校具名後續、12缺圖及胡志明歷史表阻礙見README及分類清單。

有限交付已完成；全部公開交換資料補齊尚未完成。尚可讀的公開候選不得記成外部阻礙，未公開或未核當期名額仍未知。整合維持userpaused，沒有合併／部署／正式DB／Quality／安全／憑證／權限變更。
''')
p=D/'README.md';s=p.read_text();s=s.replace('此候選固定後只集中跑一次完整回歸與受影響browser場景；結果另記驗證文件。','此候選固定後已集中跑一次完整回歸與受影響browser場景；含失敗、修復及補測的精確範圍見[最終驗收](FINAL-ACCEPTANCE.md)與[驗證清單](validation.json)。');s=s.replace('`recovery/stage.py`已套用','`recovery/stage.py`及`recovery/repair_read_scope.py`已套用');p.write_text(s)
p=D.parents[1]/'README.md';s=p.read_text();target='詳見[有限驗收與交接](resume/finite-closure/README.md)。';s=s.replace(target,target+' 一次完整515項檢查的2項失敗已經受影響23項補測修復；10browser及2補拍通過，214校生活卡待翻譯0。[精確驗收範圍](resume/finite-closure/FINAL-ACCEPTANCE.md)。',1);p.write_text(s)
print(json.dumps(validation,ensure_ascii=False))
