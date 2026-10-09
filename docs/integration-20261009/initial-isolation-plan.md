# 隔離整合驗收（進行中）

基準 main f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59。隔離 repo `/workspace/abroad-integration`，分支 `integration/pr2-pr5-20261009`。本任務不允許 main merge、正式 DB、部署、Quality 啟用、Render 設定、branch protection、憑證或付費變更。

## 依賴與候選順序

main → #5 NTU enrichment → #3 CCU adapter → #4 NCU adapter → #2 TKU＋治理（等父端固定修復 SHA）。這是隔離整合順序，不是 production 發布授權。所有共用 hunk 逐項審查；無 Git 衝突不等於語意相容。

## 已知阻擋

- #2 `5d48a01a7a58aad7fe972e7ec1434e0fb74e93c3` 是診斷基準，非最終驗收；operation-label rollback／published array 修復及全量驗證由原任務負責。未重做修復。
- main clean checkout 的 pytest collection 失敗：未追蹤 `.pyc` dependency；原始結果在 main-collect（1680 collected + 1 error，exit 2）。沒有補不明快取或弱化斷言。
- Actions 帳務阻擋、Quality disabled；本地通過不代表 CI 或上線。
- main push 立即觸發 Render；main migration path push 另外觸發 Supabase workflow，不能假定 DB 先完成。

## 記錄方式

每個 run 保存 stdout.log、stderr.log、metadata.json（完整 command、timeout、UTC 起迄、SHA/tree/clean guard、exit code）。pytest 原始 XML 另存。failed/timeout/skip/not-run 與 passed 分列，歷史檔不覆寫。測試移除生產 EXCHANGE/SUPABASE/DB 環境，使用專屬 development data path。實際 DB 只使用 repo pinned Docker runtime。

完整 repo 與 .agents 指引：main 無 AGENTS.md/SKILL.md/.agents files；工作區 .agents 空。已讀 README 測試章、conftest、兩個 workflows、Supabase rollout runbook（內有舊數量／舊狀態，不能當本次證據）及 Supabase skill。
