# TKU CI 逾時續查（2026-10-09 UTC）

固定候選 b455a18ce12ebf679f12c4f8ef4295f6546b2c60 的 PR run 37861005211（job 113596834594）及 push run 37861000761（job 113596801704）都結束為 cancelled。GitHub annotations 明示 exceeded the maximum execution time of 45m0s；不能猜為手動取消、配額或環境斷線。Web pytest 最後12%，已有 F，沒有完整統計／案例名稱；bundled資料未變動後檢查 skipped。安裝、uv lock、語法、frozen OpenAPI、31 migration解析、依賴稽核及隔離 Supabase runtime 有實際成功 log。原始證據177檔逐blob核對，已推送獨立證據commit [e33127d](https://github.com/blizzard-new/abroad/tree/e33127d413cd83dc15173c3f18d4cd5bd55228d5/docs/tku-acceptance-evidence/b455a18)。原89217e1證據1159874保持不變。

本地同SHA重現早期10案例：7通過、3失敗、141.18秒。手機期限案例捕捉到503，但登入完成前的catalogue hydration會另發請求覆蓋狀態；心得原文測試期待 I cooked，實際UI提供中文整理／官方來源提示；登出工作區案例在背景401清除DOM後仍fill，等滿30秒。獨立main f6ad1b8同10案例為8通過、2失敗、153.16秒，後兩項亦失敗；這只是對照，不構成驗收豁免。首次本地coverage約6.9秒、period options約5.8秒、若干translation約5.2秒，是觀測到的請求時間，不能冒稱全部遠端延遲因果已查明。初次本地诊斷忘記指定已下載browser路徑而10 errors，原錯誤保留，重設既有PLAYWRIGHT_BROWSERS_PATH後才取得有效結果。

有界修正保留所有實質斷言：期限案例等登入catalogue requests結束，再注入reload失敗；登出案例接受背景401先移除私人表單或本次寫入401，仍必須開啟登入、清除candidate與localStorage，另外直接核對隔離JSONL未保存過期寫入。修正後同10案例9通過／1失敗，134.21秒；心得原文差異仍保留失敗，未以改產品行為或刪除要求取得綠燈。正式API、資料、權限完全未因此改動。

CI依實際收集browser案例數按檔案分四組，module fixture不跨組；browser 73／73／74／73，其餘unit/integration放第0組。獨立collect-only核對原1757個node IDs與四組union完全相等，0漏項／0重複／0新增，原skip標記不變。fail-fast=false使某組失敗不取消其他組。逐案例名稱、phase、結果、耗時与失敗內容即時輸出，最後生成JUnit；不宣稱runner暫存JUnit已被上傳。資料未變動檢查使用always()，測試失敗仍檢查；逾時job中是否可執行以实际jobs為準。固定45分鐘上限、隔離DB20分鐘上限、permissions、secrets、actions pins、依賴版本都維持原值。9項workflow／dependency contract檢查及actionlint通過。

續查需要在新的精確SHA重跑本地10步驗收並取得新遠端四組終態，不能借用b455a18結果宣稱新SHA通過。新增共用整合點為quality.yml、scripts/run_web_quality_tests.py、兩個browser測試與workflow traceability斷言；清單同步在tku-shared-integration-risks-2026-10-08.json。沒有merge、部署、正式DB或憑證／存取／付款／安全設定變更。
