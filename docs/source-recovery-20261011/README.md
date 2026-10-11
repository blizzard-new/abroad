# 六校隔離驗收證據

最新**完整執行但未通過**的固定候選：`3129ce1bfcf6987a872574587cc53b60043d64ba`，tree `6f78825d430fbe395cc62cee0a790a9b300dbbc9`。四分片完整對帳2,891個collected node：**2,874 passed／4 failed／13 skipped**，沒有排除或未對帳案例。四分片起訖均同一clean SHA。[逐案例對帳](ccu2-full-suite-summary.json)及 `ccu2-full-shard-0..3` 原始stdout、JUnit、collection/partition、metadata皆保留。13 skips為9項既有Phase C、4項缺Ollama模型，未當通過。

4失敗：兩種寬度的行事曆被全域來源橫幅推下；土庫新摘要蓋掉先前已讀Language Assessment表格細節；記憶體單元案例在Playwright session迴圈啟動後呼叫asyncio.run。[根因與独立重現](ccu2-known-failures-review.json)。CSS注入診斷2 passed只證明根因，**不算未修改候選通過**。隔離修正進行中，將固定新SHA完整重驗。

同一3129候選已完成：

- [175步冷／暖記憶體](ccu2-memory-results.json)：451.50／455.82421875 MiB，固定460MiB門檻。僅適用此資料版本。
- [完整本機Supabase runtime](ccu2-full-runtime-summary.json)：35 migrations、37 RLS tables、0 browser grants、真實Storage API、2個PostgREST、跨校verified-email、回滾／CAS／重播與帳號刪除通過；74實際治理RPC、31audit、17檢查，清理通過且無殘留容器。原始完整輸出 `ccu2-full-supabase-runtime/`。不是正式DB驗收。
- `ccu2-final-contracts`、`ccu2-wheel-build`、`ccu2-installed-wheel`、`ccu2-final-delivery`、`ccu2-final-ncu-parity`通過。wheel SHA256 `eca3ad5390a0aec79ced5d718bd512cf60351f52e741436419aca3e941a30f44`，6,451檔案實際打包／隔離安裝hash核對；從checkout外執行六校smoke。

最新已正常推送的應用檢查點仍是[8e65c47d](https://github.com/blizzard-new/abroad/commit/8e65c47d1d42bd0d065ff53c8d6572d0be994bf2)，[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。[舊檢查點報告](checkpoint-8e65c47d.md)不覆蓋3129及之後資料。3129未標作驗收通過推送。

## 下一輪固定輸入與阻擋

- NCU PR11 `e25ff02a1ebc69ea126a814d105e88b272539351`：[固定原件核對](ncu-e25-fixed-input-audit.json)、[逐圖／PDF／校區複核](ncu-e25-independent-review.json)。193圖片全解碼、47新增條目逐圖檢視；EIVP四HTML與兩PDF共7頁核對。直接整合會將廣島共用舊點誤回填為第182點，必須阻擋，預期181點。Chuo後樂園與SJTU閔行新具名證據可個別解除舊暫緩，不代表116分配校區。仍缺21照片／33位置、317成功未讀來源及大量當期欄，不能稱全校完整。
- TKU PR13 `563fb9328c7ce15efc1ac3883d8c3d641df01e98`：[264圖解碼／26分片4219成員hash](tku-third-fixed-input-audit.json)通過；[校名／署名檢查有阻擋](tku-third-photo-blockers.json)。`tku-sister-65` Sunderland誤用UWE Frenchay照片；`tku-sister-52`作者只有Unknown author，待原始署名證據。尚未合入，264張不能全列已驗收。
- CCU PR10 `6bd8c3c2d964b8134968b28a204ee24e8f949997`只讀核對中。HCMUTE新位置及Sungshin Spring2027七附件／九文件須審核期限來源優先序、原54筆其他workflow不變與母校已關閉期限。作者測試不直接計作整合通過。
- NTU `acf0cebb24ae58b70c5604b2f1261fe8ae2c46ad`：[只讀範圍核對](ntu-stage5-readonly-scope-review.json)。runtime608，stage5另51候選尚未匯入，文件659=608+51。等待原工作者交完成匯入固定SHA；尚未合入、不代作者重做。

## 發布邊界

本工作未merge main、未寫正式DB、未部署，未改Quality停用、Render autoDeploy、branch protection、憑證或付費。[安全發布及回滾計畫](RELEASE-PLAN.md)。main更新即觸發Render，Actions帳務受阻，不能假定DB同步。父對話須先讀實際production SHA、migration history與備份，僅套缺少的必要相容migration後，發布單一已驗收候選；完成任務／mergeable不等於上線成功。

[所有原始run](run-index.json)保留failed／skipped／interrupted／not run與歷次ENOSPC，不能把重疊run相加充當覆蓋率。[全部證據hash](artifact-manifest.json)。只封存公開來源、測試截圖及計量；不封存runtime帳號、session、私人文件或憑證。
