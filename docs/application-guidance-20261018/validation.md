# 本次驗證

使用專案虛擬環境、系統 Chromium 與隔離測試資料。以下為去除重跑重複後、各案例最後一次的結果。

| 範圍 | 結果 |
| --- | --- |
| 新手入口、鍵盤、收合欄位驗證、手機／桌面／深色模式 | 6 passed |
| 工作區、條件同步、登入草稿、時程、志願、文件操作 | 55 passed |
| 前端契約 | 58 passed |
| API、文件與排程 | 53 passed、1 skipped |

既有略過案例為 `test_application_plan_api_uses_bundled_workflow_with_isolated_runtime_data`，原因是 `Phase C data reviewed`。未執行完整儲存庫套件或真實校方送件。

## 重現指令

```bash
.venv/bin/python -m pytest -q \
  tests/test_frontend_contract.py \
  tests/test_my_application_entry.py \
  tests/test_application_description_accuracy.py \
  tests/test_application_documents_api.py \
  tests/test_application_plan_api.py \
  tests/test_application_plan_scheduling.py \
  tests/test_application_writing_guidance.py \
  tests/test_multi_application_plan.py

PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium \
UNIWAY_GLASS_ARTIFACT_DIR=/tmp/abroad-ux-review \
.venv/bin/python -m pytest -q \
  tests/e2e/test_application_guidance.py \
  tests/e2e/test_application_workspace.py \
  tests/e2e/test_my_application_entry.py \
  tests/e2e/test_shared_conditions.py \
  tests/e2e/test_conditions_account_sync.py \
  tests/e2e/test_student_journey_ux.py \
  tests/e2e/test_planning_workspace.py \
  tests/e2e/test_multi_plan_workspace.py \
  tests/e2e/test_workload_journey.py \
  tests/e2e/test_application_ui_refinements.py \
  tests/e2e/test_application_periods.py \
  tests/e2e/test_platform_redesign.py::test_application_workspace_tools_are_available_on_demand \
  tests/e2e/test_platform_redesign.py::test_tracker_lists_tasks_and_switches_views \
  tests/e2e/test_tku_draft_handoff.py \
  tests/e2e/test_ntu_school.py::test_ntu_saved_conditions_keep_gpa_and_rank_without_percent_conversion \
  tests/e2e/test_task_documents_ui.py \
  tests/e2e/test_web_next_phase.py::test_advisor_waits_for_login_and_clears_private_conditions_on_logout

node --check src/exchange_info/static/application-workspace.js
node --check src/exchange_info/static/platform-tracker.js
git diff --check
```

截圖由同一套瀏覽器測試擷取，包含 390px 手機與 1440／1754px 桌面。水平溢位檢查同時涵蓋 `body` 與根元素；日曆檢查確認月份最後一列也在首屏內。原有端對端案例改由可見的展開控制進入次要工具，再驗證既有操作。
