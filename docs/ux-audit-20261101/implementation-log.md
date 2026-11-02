# 工作臺實作紀錄

每一批都先在測試版（`docs/staging-local-test.md`）確認，再更新伺服器。

## 第一批（2026-11-02）：「今天」檢視＋條件檢查狀態

| 項目 | 內容 |
| --- | --- |
| 新增 | 「我的申請」預設進入「今天」：現在做這件事、下一個已確認期限、階段進度、接下來 5 項、資格條件檢查計數 |
| 修正 UX-01 | 條件檢查任務頁先顯示「符合／不符合／待確認」與說明（原本收合在備註裡）；確認框改成一般文字框，不再像按鈕 |
| 修正 UX-11（部分） | 任務頁狀態列與頁尾加上與卡片一致的左右內距 |
| 改動 | 新建計畫、切換計畫、從學校頁開始計畫都會進到「今天」；網址 `view=progress／map／level` 照舊可用 |
| 後端 | `application_path.py`：條件檢查的關卡多一個 `check_status` 欄位 |
| 檔案 | `application-path.js`、`application-path-template.js`、`application-today.css`（新）、`index.html`、`application_path.py` |
| 測試 | 新增 `tests/e2e/test_application_today.py`（4 項）與 `tests/test_application_path.py` 一項；`test_application_task_ux.py` 一項改成預期落在「今天」 |

### 既有失敗（與這批無關）

在原本的程式碼上重跑，這 9 項測試就已經失敗，這批沒有修也沒有動：
`test_application_ui_refinements.py::test_calendar_appears_first_and_tools_still_work`（2）、`test_multi_plan_workspace.py::test_shared_progress_survives_reorder_removal_and_reload`（2）、`test_application_guidance.py::test_first_visit_has_a_clear_start_and_optional_tools`（3）、`test_application_guidance.py::test_preparation_prioritizes_next_action_and_retains_secondary_tools`（2）。

## 接下來

| 批次 | 內容 | 修的問題 |
| --- | --- | --- |
| 第二批 | 建立計畫表單：單一「出發學期」＋年份換算與後端驗證；頁首管理動作收進 ⋯；封存改成可復原 | UX-02、06、09 |
| 第三批 | 合併「準備與時程」：「時程」檢視（期限、每週時間、倒排）、個人待辦就地新增；舊網址轉址 | UX-03、04、14 |
| 第四批 | 「計畫」檢視並排比較；完成回饋（進度變化與撤銷）；側欄加文字標籤與命名統一 | UX-10、12 |
| 第五批 | 樣式整併成使用 `--uw-*` 變數的單一檔案 | UX-13 |
