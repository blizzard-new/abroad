from pathlib import Path
from collections import Counter
import json,hashlib,datetime,shutil,zipfile,re
from openpyxl import load_workbook
R=Path('/workspace/abroad-ntu-completion-20261011');D=R/'docs/ntu-completion-20261011';S=D/'stage6';V=S/'validation';H=Path(__file__).parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
snap=read(R/'sources/ntu/completion-2026-10-11.json');matrix=read(S/'all-school-review.json');summary=read(S/'review-summary.json');progress=read(R/'sources/ntu/priority-review-progress-current-2026-10-11.json');m=read(R/'sources/ntu/reviewed-source-bodies-current-manifest.json');manual=read(R/'sources/ntu/semantic-review-current-2026-10-11.json');ledger=read(R/'sources/ntu/full-body-review-current-2026-10-11.json')
assert sha(V/'tested-source-snapshot.json')==sha(R/'sources/ntu/completion-2026-10-11.json');assert summary['new_observations']==659 and len(matrix)==4032
# Require actual successful final lines; do not count an in-progress run or a prior source version.
results={}
for name in ['full-regression','browser','pr8-combined-browser','pr8-visual-locations-content','pr8-combined-guard']:
 text=(V/(name+'.log')).read_text();last=next((line for line in reversed(text.splitlines()) if re.search(r'\d+ passed',line)),None);assert last and 'failed' not in last,(name,'must pass first');results[name]={'final_line':last,'source_sha256':sha(V/'tested-source-snapshot.json'),'log':name+'.log'}
book=load_workbook(S/'288校逐欄查核_可回填.xlsx',read_only=True);sheets={s.title:s.max_row-1 for s in book};assert len(sheets)==7 and sheets['288校逐欄回填']==4032 and sheets['固定501項正文進度']==501 and sheets['逐源全文閱讀紀錄']==476;assert not any(c.data_type=='f' for s in book for row in s for c in row);book.close()
write(V/'summary.json',{'tested_source_sha256':sha(V/'tested-source-snapshot.json'),'observations':659,'tests':results,'excel':{'sheet_rows':sheets,'formula_cells':0,'GUI_visual_workbook_review_performed':False},'scope':read(V/'scope-and-rebuild.json'),'archive':read(S/'archive-verification.json'),'pr8_intersection':read(H/'pr8-intersection.json'),'original_ten_field_fully_verified_rows':0,'merge_or_deploy':False})
by=Counter(o['applicability_status'] for s in snap['schools'] for o in s['observations']);pending={r['portal_id'] for r in matrix if r['field']=='quota' and not r['target_requirement_confirmed']};tenfields={'quota','eligibility','language','documents','deadlines','calendar','housing','cost','courses','insurance_visa'};ten=[r for r in matrix if r['portal_id'] in pending and r['field'] in tenfields];assert len(ten)==2820 and not any(r['target_requirement_confirmed'] for r in ten)
coverage={'school_denominator':282,'field_denominator':10,'rows':len(ten),'fully_verified_rows':0,'old_workbook_retrieved':False,'old_exact_membership_comparison_available':False,'publication_statuses':dict(Counter(r['publication_status'] for r in ten)),'readable_unread_rows':sum(bool(r['unread_candidate_body_count']) for r in ten),'exclusive_external_blocker_rows':sum(r['external_blocker_exclusive'] for r in ten)};write(S/'282-school-ten-field-coverage.json',coverage)
base=read(D/'stage5/daily-baseline-2026-10-11.json');base.update(stage='stage6_51_references_materialized',research_checkpoint_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_snapshot_sha256=sha(V/'tested-source-snapshot.json'),reviewed_observations=659,runtime_validated_observations=659,incremental_imported_observations=51,incremental_unimported_observations=0,reviewed_source_quotes=332,archived_body_count=511,manual_semantic_decisions=len(manual),unread_public_body_rows=summary['readable_unread_rows'],fixed_priority_progress={k:v for k,v in progress.items() if k!='fields'},timestamp_note='本批按各來源原checked_at匯入；臺大正式三入口最後實際讀取仍UTC10:42、288詳情08:31–08:37。平台重建／測試及整理時間不是全網再查日期。');base.pop('combined_candidate_observations',None);base.pop('incremental_candidate_observations',None);write(S/'daily-baseline-2026-10-11.json',base)
shutil.copyfile(R/'sources/ntu/completion-2026-10-11.json',S/'結構化候選資料.json');shutil.copyfile(R/'sources/ntu/reviewed-source-bodies-current-manifest.json',S/'reviewed-source-bodies-manifest.json')
for filename in ['46-life-gap-source-origin-comparison.json','remaining-independent-host-life-research.json']:
 shutil.copyfile(D/'stage4'/filename,S/filename)
report=f'''# 第六批：51則已按範圍匯入同一Draft PR9

照片仍缺3校：加州大學(9)、加州州立大學(12)、特魯瓦科技大學(67)。座標仍缺3校：加州大學(9)、加州州立大學(12)、蒙斯大學(1302)。UC/CSU的臺大正式profile未指定分校，不能拿總部或任選校區補。特魯瓦官方[legal頁](https://www.utt.fr/mentions-legales)再製要求許可；Commons候選未取得能同時驗本體、作者、授權的照片，沒有向校方發信。蒙斯[比利時官方校頁](https://www.studyinbelgium.be/en/universite-de-mons)已核Place du Parc20；官方校圖讀取不可用，Charleroi、BdDolez31與Warocque17候選地址／校區不同或缺交叉核對，不能當該代表校區坐標。完整收據沿用[資產證據](../stage4/evidence/asset-gap-review.json)。此批資產未增加。

## 實际平台結果

第五批51則已匯入`sources/ntu/completion-2026-10-11.json`並重建partner application_info與destination學生指南，**608→659則**。全部新資料保留原學年／學期／programme／campus、PDF頁碼、URL、原文索引與checked_at；每項`selection_rule_confirmed=false`。平台仅在同一Draft PR9分支，未merge/deploy，不能稱正式網站已上线。本批沒有未匯入的51則殘留；可核對[51則匯入增量](第五批51則已匯入增量.json)。

立命館2027春的初申与資格不當2027秋新入學規定，全年cohort才涵蓋的Fall2027calendar保留條件；聖加倫26/27两份春住宿截止5/31與6/30矛盾並列；九州各programme與2019舊學分費分開；LMU Summer2026費率與到校語言／初申階段分開。Bennett26/27新生宿舍滿額不是2027交換保障或臺大甄選名額。

## 來源與分母

引用來源332、逐源全文閱讀476列、人工語意280列；封存511個本文版本、510個sourceID、18件ZIP，既有478版本／16分件逐项不變，另添33版本／2分件。659則中的所有來源原文索引及第五批51則逐項原文与PDF頁碼驗過；27張PDF目視證據驗SHA。

固定優先正文仍**501校欄／117校／890個原候選本文SHA**，本批匯入时完整讀过集合**120/501，381待續**；不是整欄當期需求核實。下一批已開始阅读，以自己的快照和驗證回报，未混入本批659測試。

全288校×14欄4032列、原282待定校×10類2820列保留；2820列完整當期核實仍0，整校完整核實0。具年局部事實、舊版、未標年、真正官方明說待發布、讀到但未找到、正文未讀及指定母校／錄取後取得分開。全矩陣可讀未讀{summary['readable_unread_rows']}列，原十類{coverage['readable_unread_rows']}列；純外部限制{summary['exclusive_external_blocker_rows']}列，原十類{coverage['exclusive_external_blocker_rows']}列。可讀未讀仍是工作，沒有當外部阻礙。

任一具範圍官方生活文字272校／1963段，缺16校；原46校獨立接待校來源缺38校，兩分母分開。此批51則没有新增生活段落，不稱這些缺口已解。

## 正式臺大基準與驗證

116-1时程與正式簡章已公告，臺灣2026/11/3 10:00–11/9 16:00報名；當日名單282格空白、6格0，不用舊內頁名額或hostcapacity替代。臺大3入口實際最後读取UTC10:42，288內頁08:31–08:37。本批重建時間不當重新爬完所有學校的checktime。原2026-10-07工作簿未取得，重建288portalID只能保留當日282待定集合，不能宣稱與舊282逐格／成員完全相同。

当前659來源SHA **{sha(V/'tested-source-snapshot.json')}**。全套、NTUbrowser、固定PR8组合browser/視覺/守門測試结果均在[驗證摘要](validation/summary.json)，每项绑定同一來源SHA。全288校正式資格、臺大名額、申請截止、可用狀態、身份與sourceURL逐項和main基準相同；workflows及其他母校資料byte一致；全重建byte-idempotent。PR8固定9927ec…只在隔離工作樹組合測試，PR9与PR8座標變更record交集为空，沒有改PR8或shared app.js。

Excel7表结构、4032列／501進度／476閱讀與0公式验证完成；没有冒稱做過Excel GUI全表目視。前5批保持當時候選／測試狀態。Library先前401且父端停止重試，沒有檔案ID；交付使用同Draft PR9固定commit，父端可下載。没有建立重複日排程，父端11校本批未輸入；后續可合併核實資料，不能稱全體缺口已解。
''';(S/'問題解決報告.md').write_text(report)
for filename in ['問題解決報告.md','review-summary.json','288校逐欄查核_可回填.xlsx','結構化候選資料.json','all-school-review.csv','all-school-review.json','daily-baseline-2026-10-11.json','282-school-ten-field-coverage.json','46-life-gap-source-origin-comparison.json','remaining-independent-host-life-research.json']:
 shutil.copyfile(S/filename,D/filename)
for p in H.glob('*.py'):
 dst=S/'research-scripts'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
a=S/'臺大288校候選查核_可回填.zip'
with zipfile.ZipFile(a,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in S.rglob('*'):
  if p.is_file() and p!=a and p.suffix!='.zip' and p.name!='tested-source-snapshot.json':z.write(p,p.relative_to(S))
 z.write(R/'sources/ntu/priority-original-cached-texts-2026-10-11.zip','接續原候選文字.zip')
 z.writestr('原始本文說明.txt','18個原始本文分件在同repo sources/ntu，由本包reviewed-source-bodies-manifest.json逐檔驗SHA；不重複包入45.9MB掃描原件。前批27張PDF核對圖在stage4/evidence、stage5/evidence。\n')
shutil.copyfile(a,D/a.name)
write(S/'deliverables-manifest.json',[{'path':str(p.relative_to(R)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in [S/'288校逐欄查核_可回填.xlsx',S/'問題解決報告.md',S/'結構化候選資料.json',a]])
(D/'README.md').write_text('''# 臺大288校研究與Draft PR9資料交付\n\n最新为[第六批報告](stage6/問題解決報告.md)、[Excel](stage6/288校逐欄查核_可回填.xlsx)、[JSON](stage6/結構化候選資料.json)与[回填ZIP](stage6/臺大288校候選查核_可回填.zip)。current別名同第六批；前5批保留其原始研究／候選狀態，不改寫為後來的測試結果。\n\n第五批51則已按原scope實際匯入Draft PR9，current659則全部測試對應SHA见stage6/validation/summary.json；未merge/deploy。固定501項优先正文完成120、381項仍待續；原2820列完整當期核實仍0。任一官方生活文字缺16校、原46校獨立接待校生活來源缺38校；照片UC/CSU/特魯瓦、座標UC/CSU/蒙斯各缺3。具名來源／拒用证据见報告。\n\n511個本文版本以18件rawbodyZIP按SHA保存；原優先932sourceID／890rawSHA候選抽取文字另在sources/ntu可攜ZIP。Library先前401，父端已停止重試，沒有LibraryID；固定GitHubcommit作接續下載入口。\n''')
print(json.dumps({'source_sha':sha(V/'tested-source-snapshot.json'),'observations':659,'sheets':sheets,'tests':results},ensure_ascii=False))
