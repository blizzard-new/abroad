from pathlib import Path
import json,re,shutil
root=Path('/workspace/recovery-evidence-20261011');out=Path('/workspace/abroad-globe-evidence/docs/source-recovery-20261011')
sha='0d3d671ef92344970e4de1797a81b050235eecbd'
checks=['frozen-final-full-unit','frozen-final-browser','pool-final-warm-memory-command','pool-final-cold-memory-command','latest-data-before-memory-command','final-frozen-contracts','final-frozen-delivery-audit','final-wheel-build','final-wheel-build-r2','final-release-live-fetch']
lines=[]
for name in checks:
 p=root/name;meta=json.loads((p/'metadata.json').read_text()) if (p/'metadata.json').exists() else {'test_result':'notrun'}
 raw=(p/'stdout.log').read_text(errors='replace') if (p/'stdout.log').exists() else ''
 summary=re.findall(r'(?m)^.*\b\d+ (?:passed|failed|skipped).*$',raw)
 note=summary[-1] if summary else ''
 if name=='pool-final-warm-memory-command':note='162/162 steps; HWM 454.5586 MiB; ≥57.4414 MiB below512'
 if name=='pool-final-cold-memory-command':note='162/162 steps; HWM 458.4922 MiB; ≥53.5078 MiB below512'
 if name=='latest-data-before-memory-command':note='162/162 steps; actual runtime23365f9; HWM556.2734 MiB; deferred budget failure preserves full workload'
 if name=='final-frozen-contracts':note='OpenAPI／JS／uv lock／35migration本地語法／原workflow154/409/288／13原測試AST／3201新來源資產選入'
 if name=='final-frozen-delivery-audit':note='NTU217正文+191引用+59歷史正文、19新照片；TKU13分片／2576成員；全量hash及限制狀態'
 if name=='final-wheel-build':note='暫存複製ENOSPC；只刪除本任務staging後重跑'
 if name=='final-wheel-build-r2':note='宣告setuptools backend，硬連結暫存；5796套件檔案逐一hash相符；zip CRC通過'
 if name=='final-release-live-fetch':note='真實公開雙GET、77列；current_cycle_verified=false'
 lines.append(f"| [{name}]({name}/stdout.log) | {meta['test_result']} | {note} |")
text=f'''# 六校隔離候選：固定輸入、完整驗收與發布邊界

應用程式候選 [{sha}](https://github.com/blizzard-new/abroad/commit/{sha})，[Draft PR #12](https://github.com/blizzard-new/abroad/pull/12)。本階段沒有merge main、部署、正式DB寫入、Quality啟用、Render autoDeploy／branch protection變更、憑證或付費操作。**這是隔離驗收，不是上線成功；資料仍非全校完整。**

## 固定输入及逐段整合

| 輸入 | 固定SHA |
|---|---|
| main | 59a20f27fcee00fb597abc79e75ec11778317422 |
| #8 共用地球／照片識別 | 9927ec1d8765a9772671bbaa68e7f920995f1258 |
| #9 台大第二批 | b6607a0ee5d01e23878950d556f9540aa25aeaf2 |
| #10 中正 | cf4d86f22d89ee698315d46177daf00b49dd8706 |
| #11 中央第三批 | 06bfdfa15e9f773533d3f82e1a136faa99f68104 |
| #13 淡江第一批 | f4819dab2db22507ad8978800aeabbcb9f598294 |

順序為main→#8→長庚來源恢復→固定學校批次→逐hunk協調→記憶體修正→最終固定驗收。[共用路徑審查](shared-hunk-review.json)記錄API、照片scope、操作員待審優先、資料年度、package-data及中央track規則，不以Git無衝突代替語意驗收。

## 最終原始結果

每個run的metadata保留開始／結束SHA、tree、dirty狀態、命令、時間及exit code；stdout／stderr完整保存。早期失敗、診斷與重跑沒有刪除或加總成新的案例數。`running`／`notrun`明確不是通過。

| Run（原始log） | 結果 | 範圍／實際值 |
|---|---|---|
'''+ '\n'.join(lines)+'''

12個既有skip的實際原因見最後全套log的`-rs`輸出。未執行：main merge、正式部署／DB、所有無關E2E檔案、wheel全新隔離安裝及正式容器啟動。已跑的是全套非E2E與列明的擴充重點瀏覽器流程，不聲稱全repo E2E全部跑過。

## 記憶體等負載比較

[完整比較](final-memory-comparison.json)及三組`memory-samples.json`保留162步。比較前後來源檔／前端檔完全相同，六校分母77／206／288／104／214／287；前版為23365f9，快照5799檔在開始／結束逐hash核對。

12輪六校×5並行API，三份完整中央來源稽核，前後各3×8中正並行burst，390／1440重複三輪，36次切校、36次六校生活頁與六次台大地球／照片／生活流程，最後GC。測量單一Uvicorn worker的RSS與high-water，Chrome是外部負載產生器。預先設定460MiB驗收門檻，較512MiB保留至少52MiB。

| 同一最新資料 | 完成步驟 | HWM MiB | 460門檻 |
|---|---:|---:|---|
| 修正前、暖啟動23365f9 | 162 | 556.27 | failed |
| 修正後、暖啟動0d3d671e | 162 | 454.56 | passed |
| 修正後、冷啟動0d3d671e | 162 | 458.49 | passed |

前版只將budget assertion延到結尾，完整量完仍exit1；沒有縮短負載。所有app server log為空、HTTP／瀏覽器斷言完成。另一次wheel暫存曾短暫ENOSPC，獨立失敗與清理時間有記錄；沒有替換來源或縮減欄位來過關。先前短流程約410MiB及tracemalloc診斷不當作完整驗收。

修正內容：2個同步worker、1個catalogue展開名額；預熱逐步共用相同工作池並由lifespan取消。中央source audit改串流並限制8MiB／16筆序列化快取；中正按校保留完整hash／摘錄驗證並只cache4筆；完整104校completion和台大288生活資料用序列化索引，回傳獨立完整模型；PDF／gzip SHA改串流。中央最新214審核、1990來源已全量等值核對，[結果](ncu-third-pass-streamed-payload-parity.json)保留payload hash。中正104與台大288亦有全量原模型相等及防污染測試。

## 來源、照片與仍未完成的資料

- 長庚兩公開表完整成功才原子替換，任一失敗保留前版；沒有快照時明示不可用。真實公開取得與錄製故障fixture分開。列77不代表本期已核實；原workflow154不變，NTPU409、NTU288亦與f6ad1b8位元組相同。
- 台大完整交付217正文／6ZIP、191引用與頁碼、59歷史正文已核對；原缺正文阻擋已結清。生活來源242校，仍缺46；照片／座標各285，仍缺3；129語意待查，282未知quota及6明示0名額維持分別。19新增照片hash、署名授權及手機／桌面真實解碼納入測試。直接Commons HTTP12份403保留，另透過web來源頁核對，未冒稱全數正常下載。
- UC3M Commons分類與描述曾不一致；以校方Colmenarejo相簿中同一Unamuno雕像與建築比對支持原caption，[獨立證據](uc3m-campus-identity-review.json)。只讀比對的校方NC照片沒有安裝為產品資產或再發布；產品仍用原Gotesan／CC BY-SA3.0照片。
- 中正104機構、95點、97授權照、101網站；仍有702host欄位缺口、9點／7照／3網站缺件，全校協議分母未釐清。
- 中央214歷史目錄track，125授權照片；整合44點含PR8及台大共享Malaya新增，[delta](ncu-ntu-shared-location-delta.json)。所有當期完整host批准仍0，214 quota null／agreement_only、流程pending_review；第三輪仍277成功候選待人工讀，329／331協議分母差异待釐清。不能將HTTP成功、舊年參考或官方預定公告當當期可申請。
- 淡江287機構、153含歷史計畫、124校2031摘錄，13照片／3點；4closed、149agreement_only、134reference_only，283未知quota。其餘資料仍大量待取得／人工查核，未宣告完成。
- 既有長庚2／北大15照片授權缺口未在本輪結清。各校missing、pending／needs_confirmation、reference_only、明示zero及官方明示尚未公告仍分开。

## 套件及安全發布順序

[DB／程式發布與回滾計畫](RELEASE-PLAN.md)、[逐PR migration核對](final-migration-audit.json)。相對main每個固定輸入新增／修改migration都是0；35既有SQL僅本地語法驗證，沒有正式DB操作。Render main commit會觸發部署，Actions帳務阻擋下不能假定DB同步。父對話在正式操作前仍須只讀核對實際production SHA、DB版本和備份，再決定是否以單一已驗收候選更新main，避免中間版本被自動部署。回滾到發布前實際穩定SHA；本輪沒有DB down migration或刪資料步驟。

實體wheel：[完整內容hash清單](final-wheel-integrity.json)，5,796檔／1,066,644,735未壓縮bytes全部與候選一致；wheel778,811,706bytes，SHA256 `b92a6f40c4db701b8c7647df3c69d994ae8899e464ab1a670b8d9b037aa6f9b5`。檔案保存在執行環境`/workspace/recovery-wheel-artifacts-20261011/taiwan_exchange_info-0.1.0-py3-none-any.whl`，未推到Git或套件平台。

[所有原始run索引](run-index.json)、[逐run狀態表](RUNS.md)、[檔案SHA256清單](artifact-manifest.json)、[重現工具](harnesses/)。僅收集公開來源、測試截圖與計量；沒有納入runtime帳號、session、私人文件或憑證。
'''
out.mkdir(parents=True,exist_ok=True);(out/'README.md').write_text(text)
shutil.copyfile('/workspace/recovery-tools-20261011/RELEASE-PLAN.md',out/'RELEASE-PLAN.md')
index=json.loads((out/'run-index.json').read_text())
rows=[]
for r in index:
 start=r['start_guard'];end=r.get('end_guard') or {}
 status='固定工作樹' if not start.get('status') and not end.get('status') and start.get('sha')==end.get('sha') else '開發中／工作樹有變更'
 if any(x in r['name'] for x in ('probe','diagnostic','latest-data-before','comparison-memory')):status='診斷／比較；實際來源看stdout及manifest'
 summary=' / '.join(r['pytest_summary']).replace('|','\\|')
 rows.append(f"| [{r['name']}]({r['name']}/metadata.json) | {r['result']} ({r['exit_code']}) | {start['sha'][:8]} | {status} | {summary} |")
(out/'RUNS.md').write_text('# 原始run完整索引\n\n數字不跨重疊run加總。診斷exit0只表示量測完成，不表示記憶體budget通過。失敗run若提前停止，後續未執行步驟不可算通過。完整stdout/stderr和精確SHA以metadata及來源manifest為準。\n\n| Run | status (exit) | 起始SHA | 固定性／用途 | pytest原始結尾 |\n|---|---|---|---|---|\n'+'\n'.join(rows)+'\n')
print({'readme_runs':len(checks),'historical_runs':len(index)})
