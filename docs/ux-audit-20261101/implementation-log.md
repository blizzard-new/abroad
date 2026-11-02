# 工作臺實作紀錄

每一批都先在測試版（`docs/staging-local-test.md`）確認，再更新伺服器。

## 完成的項目（2026-11-02）

| 問題 | 做了什麼 | 狀態 |
| --- | --- | --- |
| UX-01 條件檢查結果看不到 | 任務頁先顯示「符合／不符合／待確認」與說明；後端關卡帶 `check_status` | 完成 |
| UX-02 年份可以填反 | 建立計畫改成選「預計出發學期」，民國學年度由系統換算並顯示；後端拒絕「民國欄填西元」「西元欄填民國」 | 完成 |
| UX-03 準備與時程看不到計畫的任務 | 「時程」的待辦列表直接讀這份計畫的任務（進行中、接下來可開始的、已完成）；進度分母用計畫本身的數字 | 完成 |
| UX-04 好功能被藏起來 | 「準備與時程」併入「我的申請」的「時程」分頁：已確認期限在最上面、依期限預留準備天數預設展開、排程工具自動以目前計畫為目標 | 完成（舊的排程工具沿用，重新排列與調整樣式，沒有重寫） |
| UX-05 期限卡是死路 | 沒有已確認期限時，說明原因並提供官方公告連結 | 完成 |
| UX-06 頁首按鈕太多 | 「重新載入」「封存計畫」「新增計畫」收進頁首右側的 ⋯ 選單 | 完成 |
| UX-07 清單 43 項全攤開 | 預設只看「今天」：現在做這件事＋接下來 5 項；完整清單與路徑地圖在「計畫」分頁裡 | 完成 |
| UX-09 封存用瀏覽器視窗 | 直接封存，提示條有「復原」；已封存的計畫在「計畫」分頁可復原 | 完成 |
| UX-10 命名重複、導覽只有圖示 | 側欄移除「準備與時程」；收合的側欄在圖示下方顯示文字；其他工具頁的子導覽改稱「時程」；舊網址 `#overview` 轉到「時程」 | 完成 |
| UX-11 任務頁版面 | 狀態列與頁尾加內距；確認框改成一般文字框 | 完成 |
| UX-12 完成回饋太小 | 完成一項後顯示「準備進度 n / 總數」並可「撤銷」；完成畫面也顯示進度 | 完成 |
| UX-14 新增待辦會離開頁面 | 「今天」與「時程」都能就地新增待辦 | 完成 |
| 情境 C 多計畫比較 | 新「計畫」分頁：每份計畫一張卡，並排比較下個期限、進度、缺的文件、目前階段、下一步；列出每份計畫都需要的同名文件 | 完成 |
| UX-08 網路失敗顯示英文原始訊息 | 網路錯誤改顯示「目前沒有網路連線。」或「目前連不上伺服器。」，輸入的文字保留，連線後自動儲存 | 完成（有自動測試） |
| UX-16 觸控裝置顯示快速鍵標籤 | 觸控裝置隱藏 `kbd` 標籤 | 完成 |
| UX-15 一般使用者每次載入多一個 403 | 沒處理 | **未做** |
| UX-17 `transition: all` | 沒處理 | **未做** |
| UX-18 手機上計畫選單被截斷 | 沒處理 | **未做** |
| UX-13 樣式分叉 | 新介面用 `application-today.css`（只用 `--uw-*` 變數）；舊的 `application-path.css` 沒有整併 | **未做**：舊樣式仍在，需要另外安排 |
| UX-19 斷線內容只留在分頁記憶體 | 依你的決定維持現狀 | 未改（維持） |

### 順手修掉的既有錯誤
「讀書計畫工作臺」遇到名額只有一個字（例如「2」）或語言要求只有「無」的學校會回 500（`StudyPlanPartnerCourseLookup` 要求至少 2 字）。新的「時程」會自動帶入計畫的學校而碰到它，已在 `study_plan_workbench.py` 修正並加測試。

### 檔案
`application-path.js`、`application-path-template.js`、`application-today.css`（新）、`platform-tracker.js`、`application-workspace.js`、`application-plan-index.js`、`app.js`、`index.html`；後端 `application_path.py`、`study_plan_workbench.py`。

## 測試
- 新增：`tests/e2e/test_application_today.py`（4）、`tests/e2e/test_application_workbench.py`（12）、`tests/test_application_path.py`（1）、`tests/test_study_plan_workbench.py`（1）、`tests/test_staging_runner.py`（8）。
- 因為設計刻意改變而更新的既有測試：`test_application_task_ux.py`（2）、`test_application_stage_guide.py`（1）、`test_my_application_entry.py`（2）、`test_application_workspace.py`（1）。
- 在原本程式上就失敗的既有測試（這次沒有動）：`test_application_ui_refinements.py::test_calendar_appears_first_and_tools_still_work`、`test_multi_plan_workspace.py::test_shared_progress_survives_reorder_removal_and_reload`、`test_application_guidance.py`（5）、`test_navigation_guide.py`（5）等共 14 項。
- 有一項（`test_workspace_navigation_preserves_draft_target_and_old_routes[390]`）在整批一起跑時偶發失敗，單獨重跑通過，原因是頁面載入時機。

## 還沒做 / 需要你決定
1. 「條件檢查」的「已看過」是否繼續計入「準備進度 n / 43」（目前維持計入）。
2. UX-13 樣式整併。
3. 「時程」裡的排程預覽與「進階時間安排」是舊工具重新排列，不是重寫；如果要更像專業工作臺，下一步是重做這兩塊。
4. 沒有真人使用者測試；沒有在 Windows 與實機手機驗證。
