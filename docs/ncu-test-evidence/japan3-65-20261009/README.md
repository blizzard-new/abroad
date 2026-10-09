# 中央65 partial候選的固定SHA原始證據

實作SHA為`2ce9b25f8314dd4be457b3ae1be3fc3dadad12e0`，固定checkout `/tmp/abroad-ncu-japan3-65`起迄同SHA且clean。開始2026-10-09 02:17:16 UTC，完成02:41:45 UTC。這是完整必要本機驗證，不代表214校资料完整或CI通過。

| 檢查 | 實際結果 | 原始證據 |
| --- | --- | --- |
| NCU資料／API／年度／來源／文件條件 | 295 passed | candidate-2ce9b25/ncu_unit.log、.xml |
| CGU／NTPU／NTU及共用回歸 | 193 passed、2 skipped | candidate-2ce9b25/shared_regression.log、.xml |
| 既有gate | 65 passed | candidate-2ce9b25/existing_gate_failures.log、.xml |
| OpenAPI snapshot、三個JS語法、lock、候選diff | 全部exit 0 | candidate-2ce9b25對應原始log |
| 原main851流程同schema／multiset比較 | 0語意差異；CGU154、NTPU409、NTU288 | candidate-2ce9b25/workflow_parity.log與manifest |
| 真實瀏覽器 | 62 passed，1180.96秒；原56加本批三校390／1440六案例 | candidate-2ce9b25/browser_ncu_ntu.log、.xml；62筆browser-events |
| 原畫面 | 112張PNG；final副本逐張bytes相同 | candidate-2ce9b25/original-browser.zip及checksum-manifest |
| GitHub CI（之後另查） | Quality37874452701 failure／0 jobs；Supabase113639693059 skipped；combined pending | ci-2ce9b25原始API JSON與查核manifest |

[執行manifest](candidate-2ce9b25/manifest.json)保留原始bytes，包括當時`ci_status=not_checked_yet`；CI是完成後另查的紀錄，沒有改寫原驗證manifest。必要本機檢查通過，`data_acceptance_passed=false`及`acceptance_status=blocked`仍保留：65／214 partial、149項待整理，116全欄核准0，當期名額未知。沒有放寬原測試timeout或再跑冷效能輪次。

舊3b14037的55 passed／1個GPA重載5秒失敗、9bf90c8的52／4及單例诊斷仍在[原效能證據](../performance-20261009/README.md)。本次62項通過不能證明那些歷史失敗根因已關閉。瀏覽器執行期間另於工作分支整理後續三校来源；候選checkout保持固定且clean，這不是專用CPU的效能benchmark。

[六張實際檢視紀錄](visual-inspection.json)覆蓋三校手機流程／來源及桌面生活内容，確認規劃範圍與待核字樣、費用參考及未讀57頁提示。全部112張由測試保存，沒有稱112張皆人工看過。原件20頁另在來源證據目錄。

原始log、JUnit、事件JSON與driver未清洗；大JSON確定性gzip保留原bytes。`checksum-manifest.json`記錄原始與存檔SHA，ZIP列112張PNG SHA。Playwright trace ZIP可能含隔離測試session header，留在/tmp；公開事件不含header值或response body。忽略規則中的.log按精確清單強制加入，不改全域ignore。

[合併點](merge-points.json)固定在2026-10-09 02:18 UTC：main f6ad1b8、CCU5eadeb5交集15檔、TKUce83a50交集20檔。沒有merge其他分支或覆蓋共用檔；Quality workflow修正依分工留給TKU。本輪沒有部署、正式DB操作、credentials／security更動或聯絡學校。
