# fff2760b 同 SHA 測試原始證據（仍未驗收）

測試 SHA：`fff2760b378d844701b6c5b373e5625ac74f1ca6`。起訖 2026-10-08T23:21:14.033619+00:00 至 2026-10-08T23:46:32.196696+00:00 UTC；兩端及各階段前 HEAD 固定、工作樹乾淨。`manifest.json` 是 runner 原始輸出，未改寫。此資料夾由後續 evidence-only commit 保存；保存 commit 沒有被這批測試涵蓋。

- 中央271 passed；共用164 passed／2 skipped。
- NCU／NTU手機390與桌面1440共56項browser全部通過。94張原始截圖在三次冷測之前即複製，zip內 `original-56` 不被後續新潟截圖覆寫；冷測第三次3張另列 `performance-cold-3`。SHA256對照見artifact map。
- 北海道院級／校級的實際流程、生活及原件閱讀範圍均檢查；校級JLCSP原表格href及母校簽名、公章需求實際顯示。83頁HUSTEP只讀1–4，未讀頁沒有宣稱全文。
- 三次全新Python串行冷啟動直接呼叫原始新潟390函式，預設5秒未改，三次均passed；ASGI、HTTP／DOM、LongTask、catalog build原始報告分列在performance目錄。三次不是SLA或原始ded2ed1失敗豁免。
- 既有3 modules仍55 passed／10 failed；10個名稱與未改main f6ad1b8完全相同，未通過。後续修正必须新SHA验证，不能回改本结果。
- OpenAPI、3份JS、lock、diff通過；CGU154／NTPU409／NTU288共851份流程同schema逐值multiset差異0。
- GitHub quality [37858934103](https://github.com/blizzard-new/abroad/actions/runs/37858934103) 實際failure、0 jobs，根因未取得；Supabase Preview skipped。TKU負責CI配置修正，NCU未改workflow。Docker／migration／dependency完整CI未本地執行，本集合不等同完整CI。
- 資料62 partial／214，152項尚可持續查核，0 full116；740筆公開來源紀錄、97筆讀取錯誤，Drive459份中19份原生全文人工讀取。116校別名額母校預定10/12公布。関西国際／駒澤／東北新研究仍在tmp，未納入此SHA或覆蓋率。

沒有merge、deploy、正式DB、credentials變更或對外聯絡。資料、必要測試與CI驗收仍blocked。
