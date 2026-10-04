# App 同步簡報（Web 已完成、App 尚未同步）

狀態：**App 沒有修改。** 依專案既有規則，Web 流程經真人確認後才同步到 Flutter／iOS／Android（[README](../README.md)），本輪遵守這個順序。這份只列出同步時 App 端要對齊的 API 變動，避免之後重新盤點。

## 新增或變動的 API（皆為向前相容的新增欄位）

| 位置 | 變動 | App 端要做的事 |
| --- | --- | --- |
| `POST /application-plan/evaluate`、`/application-plan/schedule` 回應的每個 task | 新增 `document_link`（`template_ids`、`requirement_names`、`unmapped_requirement_names`、`basis`）、`task_origin`（`official`／`reference_year`）、`reference_academic_year`、`suggested_effort_hours` | 任務列顯示「開啟對應文件」；`reference_year` 任務標示「預估，非官方期限」；工時未填時顯示系統建議值 |
| 同上，每個 choice | 新增 `reference_academic_year` | 年度尚未發布時顯示預估來源年度 |
| `schedule` 回應的 `issues[].code` | 新增 `suggested_effort`（非阻擋）；階段順序的等待用既有 `waiting` | 把 `suggested_effort` 合併成一行說明，不逐項列出 |
| `POST /advisor/plan` 請求 | 新增 `preferred_teaching_language`（`english`／`japanese`／`chinese`／`other`）、`course_interests`（≤120 字） | 條件表單加兩個欄位 |
| `POST /advisor/plan` 回應的每所學校 | 新增 `budget_fit`、`teaching_language`、`course_interest` | 卡片加「費用、語言與課程」區塊；**`unknown` 必須顯示原因，`within` 不可寫成「負擔得起」** |
| `GET /account/workspace` 的 `selection_conditions.profile` | 新增 `preferred_teaching_language`、`course_interests` | 讀寫時保留；舊版客戶端省略時伺服器補預設值 |
| `GET /account/notifications/{id}/changes` | 新增 `affected_tasks[]`（`action`：`recheck_completed`／`review_progress`／`new_task`／`retired_task`） | 變更通知顯示受影響的任務與指引；不自動修改進度 |
| 新增 `GET /school-data-completeness?school=&home_school=` | 10 項（臺北大學／長庚）資料完整度 | 學校詳情加「資料完整度」 |

OpenAPI 快照：`docs/api/openapi.json` 已依目前程式重新匯出。

## 同步前的注意事項

- `api.py` 原本沒有呼叫 `install_openapi_contract`；本輪已接上，`/openapi.json` 現在帶 `x-contract-version: 2026-10-02.1`，快照與即時 schema 一致。README 提到的管理審查批次等路由在工作樹中仍不存在，同步前先確認哪一份是正式版本。
- Web 端文件「一路完成」進度條（填寫 → 核對 → PDF → 檢查 → 保存 → 送件）純前端，狀態來源都是既有欄位；App 端若要同步，沿用同一個階段定義即可。
- 階段順序等待（`stage_gate_reason`）由伺服器計算，App 不需實作。
