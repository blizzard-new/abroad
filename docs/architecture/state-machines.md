# 全專案狀態機與轉移總表

本文件整理 UniWay 後端、Web 前端、Flutter 與行銷代理辦公室中的所有狀態機、轉移規則、併發保護與工程規範，供開發者與代理在單一檔案查閱，對應表格式測試位於 `tests/test_state_machine_transitions.py`。

## 工程決策與設計準則

1. **純函式轉移，不引入狀態機函式庫**：新流程比照 `src/exchange_info/submission_progress.py` 的 `transition(current, request) -> next_state`，在單一純函式內完成前置守衛、狀態轉移與繁體中文錯誤訊息。
2. **伺服器回傳 `allowed_actions`**：凡是有跨端（Web／Flutter）共用轉移守衛的流程，由後端模型直接計算並回傳 `allowed_actions`，前端僅依 `allowed_actions` 決定按鈕與表單顯示，不各自複製狀態規則。
3. **不安全的「進行中」殘留一律轉為 `failed` 由人確認**：外部副作用（例如社群平台發文）若在 `publishing` 途中重啟，啟動時必須轉為 `failed` 而非 `approved`，避免自動重發造成重複貼文。
4. **審核與安全類流程採 CAS（`expected_status`／`expected_revision`／`content_hash`）＋冪等收據（`mutation_id`）**：不重寫既有原子儲存層，統一以本表與表格式測試作為規格契約。
5. **學生自我記錄清單保持自由跳躍**：文件處理進度（#8）、行事曆準備狀態（#9）與工作區待辦（#10）屬於學生個人紀錄，不加伺服器端順序鎖死。
6. **Web 新非同步流程一律使用單一狀態欄位**：比照 `state.authRestoreState`（`"pending" | "authenticated" | "anonymous" | "unavailable"`），不再新增分散的 `*Loading`／`*Error` 布林組合；工作區同步狀態統一透過只讀推導函式 `deriveAccountWorkspaceSyncStatus()` 對齊 Flutter 的 6 個狀態。

---

## 全專案狀態機總覽（#1–#16）

| # | 領域 | 狀態列舉 | 主要位置 | 轉移與併發機制 |
|---|---|---|---|---|
| 1 | 送件進度 | `not_started` → `preparing` → `submitted` → `receipt_confirmed` → `completed`（含逐步 `revert`） | `src/exchange_info/submission_progress.py`、`models.py` | 純函式守衛＋伺服器計算 `allowed_actions`＋工作區 `expected_revision` |
| 2 | 申請流程內容審核 | `legacy_unclassified`、`draft`、`pending_review`、`published`、`rejected`、`superseded`（含回滾） | `src/exchange_info/content_governance.py` | 雙審人核准、`expected_content_hash` 快照比對、原子提交與回滾 |
| 3 | 目的地資料雙審 | `unstarted`、`partial`、`ready_for_promotion`、`changes_required` | `src/exchange_info/destination_profile_review.py` | 由審核事件不可變日誌即時推導（≥2 位核准且無退回才可升級） |
| 4 | 流程錯誤回報／社群檢舉 | `pending` → `resolved`｜`dismissed` | `src/exchange_info/workflow_issue_reports.py`、`community_repositories.py` | 終態不可逆、`expected_status=pending` CAS 與 `mutation_id` 冪等重播 |
| 5 | 公開社群內容審核 | `pending`、`approved`、`hidden` | `src/exchange_info/community_repositories.py` | 管理員帶 `expected_status` 原子轉換為 `approved` 或 `hidden`，並寫入稽核紀錄 |
| 6 | 私訊邀請 | `pending` → `accepted`｜`declined` | `src/exchange_info/community_repositories.py`、`api.py` | 僅收件者可操作、`expected_status=pending` CAS；僅 `accepted` 可傳訊 |
| 7 | 通知信寄送 | `pending` → `sent`｜`retrying` → `failed`｜`cancelled` | `src/exchange_info/notifications.py` | 排程迴圈內依重試次數上限（`MAX_EMAIL_ATTEMPTS`）與資格複查轉換 |
| 8 | 文件處理狀態 | `draft`、`ready_to_print`、`pending_signature`、`pending_department_stamp`、`pending_submission`、`completed` | `src/exchange_info/models.py`（`AccountApplicationSelection`） | 學生個人清單，允許任意跳躍，無伺服器端順序限制 |
| 9 | 行事曆事件準備狀態 | `todo`、`preparing`、`ready` | `src/exchange_info/models.py`（`AccountCalendarEvent`） | 清單型自由切換；未達 `ready` 時匯出 ICS 產生提醒鬧鐘 |
| 10 | 交換工作區任務 | `todo`、`doing`、`waiting`、`done` | `src/exchange_info/exchange_workspace.py`（`WorkspaceTask`） | 學生全旅程個人待辦（含等候對象 `waiting_for`），允許自由切換 |
| 11 | Web 登入還原 | `pending`、`authenticated`、`anonymous`、`unavailable` | `src/exchange_info/static/app.js`（`state.authRestoreState`） | 單一列舉欄位＋`authRestoreRequestId` 序號防過期回應覆蓋 |
| 12 | Web 各資料載入 | 各區塊既有 `*Loading`／`*RequestId`／`*Error` | `src/exchange_info/static/app.js` | 既有欄位維持相容；新功能一律改採單一列舉欄位（比照 #11） |
| 13 | Web 工作區同步 | 只讀推導：`loading`、`saved`、`pending`、`syncing`、`conflict`、`expired` | `src/exchange_info/static/app.js`（`deriveAccountWorkspaceSyncStatus`） | 以只讀 selector 收斂既有同步欄位供 UI 顯示，對齊 #14 規格 |
| 14 | Flutter 工作區同步 | `loading`、`saved`、`pending`、`syncing`、`conflict`、`expired` | `mobile_flutter/lib/state/workspace_sync.dart` | 明確 `WorkspaceSyncStatus` 列舉＋三向合併（`mergeWorkspaces`） |
| 15 | 行銷辦公室草稿 | `pending_approval`、`needs_changes`、`approved`、`publishing`、`published`、`failed`、`rejected` | `marketing/agent-office/office/store.py`、`office.py`、`agents/publisher.py` | 啟動時自動將殘留 `publishing` 轉為 `failed`（不自動重發） |
| 16 | 驗證碼／OAuth 暫存／刪帳 | 時間戳、TTL、嘗試次數、單次 `consume_state`、`mutation_id` 收據 | `email_verification.py`、`transient_auth.py`、`repositories.py` | 以原子消費、雜湊指紋與冪等收據保證一次性或可安全重試 |

---

## 重點狀態轉移表

### #1 送件進度與 `allowed_actions`（`submission_progress.py`）

當 `method == "unknown"` 時，不開放任何進度記錄（`allowed_actions = []`）。其餘送件方式規則如下：

| 現況 `status` | 送件方式 `method` | 伺服器回傳 `allowed_actions` | 轉移結果 |
|---|---|---|---|
| `not_started` | 非 `unknown` | `["start"]` | `start` → `preparing` |
| `preparing` | 非 `unknown` | `["submit", "revert"]` | `submit` → `submitted`；`revert` → `not_started` |
| `submitted` | `paper`、`mixed` | `["confirm_receipt", "revert"]` | 必須先 `confirm_receipt`（附 `proof_metadata`）→ `receipt_confirmed`；禁止直接 `complete` |
| `submitted` | `online`、`email`、`in_person` | `["confirm_receipt", "complete", "revert"]` | 可記錄證明 → `receipt_confirmed`，或無回條手動 `complete` → `completed` |
| `receipt_confirmed` | 非 `unknown` | `["complete", "revert"]` | `complete` → `completed`；`revert` → `submitted`（清除收件證明） |
| `completed` | 非 `unknown` | `["revert"]` | 若有收件證明／時間戳，`revert` → `receipt_confirmed`；否則 `revert` → `submitted` |

---

### #2 申請流程內容審核（`content_governance.py`）

| 起點狀態 | 操作函式 | 守衛條件 | 目標狀態 |
|---|---|---|---|
| 無／既有版本 | `stage_workflow_refresh` | 內容雜湊與既有待審／已發佈不同 | 建立 `pending_review`（無差異則 `noop`） |
| `pending_review`／`draft` | `approve_workflow_revision` | 審核人非同一人重複、來源與規則鍵完整、`expected_content_hash` 相符 | 維持 `pending_review` 並累積獨立核准紀錄 |
| `pending_review` | `publish_workflow_revision` | 至少 2 位不同審核人核准同一個 `content_hash`、無待補缺口 | 目標版本 → `published`；先前 `published` 版本 → `superseded` |
| `pending_review`／`draft` | `reject_workflow_revision` | 提供退回原因 | `rejected` |
| `published` | `rollback_published_workflow` | 指定歷史已核准版本且通過完整性檢查 | 建立回滾修訂並設為 `published`；原 `published` → `superseded` |

---

### #3 目的地資料雙審（`destination_profile_review.py`）

`DestinationProfileReviewRow.review_progress` 不直接寫死於欄位，而是由當前 `profile_content_hash` 對應的最新審核事件集合推導：

| 當前內容雜湊下的審核事件 | 推導 `review_progress` | `ready_for_promotion` |
|---|---|---|
| 0 筆核准、0 筆退回 | `unstarted` | `False` |
| 1 筆核准、0 筆退回 | `partial` | `False` |
| ≥ 2 位不同審核人核准、0 筆退回 | `ready_for_promotion` | `True` |
| 任一審核人標記 `changes_required` | `changes_required` | `False` |

> 當目的地資料內容更新導致 `profile_content_hash` 改變時，舊雜湊的審核事件不再計入 `current_reviews`，自動回到 `unstarted`。

---

### #4–#6 社群審核、回報與私訊邀請

| 狀態機 | 允許轉移 | 拒絕轉移（回傳衝突或驗證錯誤） |
|---|---|---|
| #4 流程錯誤回報（`ApplicationWorkflowIssueReportStatus`） | `pending` → `resolved`｜`dismissed` | 從 `resolved`／`dismissed` 再次審核（`STATUS_CONFLICT`） |
| #4 社群檢舉（`CommunityReportStatus`） | `pending` → `resolved`｜`dismissed` | 新建非 `pending`、或從終態再次變更（`STATUS_CONFLICT`） |
| #5 公開社群內容（`ModerationStatus`） | `{pending, approved, hidden}` → `{approved, hidden}`（須符合 `expected_status`） | 目標設為 `pending`，或現況不等於 `expected_status`（`STATUS_CONFLICT`） |
| #6 私訊邀請（`ConversationStatus`） | `pending` → `accepted`｜`declined`（限收件者 `recipient_id`） | 發起者自行接受／拒絕（`RECIPIENT_ONLY`）、`accepted`↔`declined` 互轉、封鎖關係下操作、在非 `accepted` 對話傳訊 |

---

### #7 通知信寄送（`notifications.py`）

| 現況 | 事件 | 下一狀態 |
|---|---|---|
| `pending`／`retrying` | 帳號不存在、通知已刪除、取消訂閱或不再符合提醒條件 | `cancelled` |
| `pending`／`retrying` | SMTP／寄送成功 | `sent`（記錄 `sent_at`） |
| `pending`／`retrying` | 寄送拋出例外且 `attempt_count + 1 < MAX_EMAIL_ATTEMPTS` | `retrying`（依 `EMAIL_RETRY_DELAYS` 排程下次重試） |
| `pending`／`retrying` | 寄送拋出例外且 `attempt_count + 1 >= MAX_EMAIL_ATTEMPTS` | `failed` |

---

### #8–#10「學生做到哪了」四套詞彙邊界

| 編號 | 模型 | 詞彙 | 語意定位 |
|---|---|---|---|
| #1 | `AccountSubmissionProgress` | `not_started` / `preparing` / `submitted` / `receipt_confirmed` / `completed` | **官方流程送件步驟紀錄**：需區分紙本送達與收件證明，唯一有嚴格轉移守衛的狀態機 |
| #8 | `AccountApplicationSelection` | `draft` / `ready_to_print` / `pending_signature` / `pending_department_stamp` / `pending_submission` / `completed` | **申請表單／文件印簽清單**：對應紙本核章步驟，允許學生自由跳躍 |
| #9 | `AccountCalendarEvent` | `todo` / `preparing` / `ready` | **行事曆期限準備度**：控制日曆提醒鬧鐘是否繼續觸發 |
| #10 | `WorkspaceTask` | `todo` / `doing` / `waiting` / `done` | **個人交換工作區任務**：支援 `waiting_for` 等候外部回覆的通用看板 |

---

### #13–#14 Web 與 Flutter 工作區同步六態對照

Web `deriveAccountWorkspaceSyncStatus(source, { online })`（`src/exchange_info/static/app.js`）將分散欄位唯讀映射至與 Flutter `WorkspaceSyncStatus`（`mobile_flutter/lib/state/workspace_sync.dart`）一致的六個標準狀態：

| 標準狀態 `status` | 觸發條件（Web `deriveAccountWorkspaceSyncStatus`） | Web UI `data-sync-state`／顯示文案 |
|---|---|---|
| `loading` | 尚未完成首次工作區載入，或 `GET /account/workspace` 載入中且無 `PUT` 通道執行中 | `syncing`（「正在同步」） |
| `syncing` | `accountWorkspaceSyncLanes` 有進行中的 `PUT /account/workspace` | `syncing`（「正在同步」） |
| `pending` | 有待送出 `accountWorkspacePending`、離線待同步，或發生可重試網路／5xx 錯誤（變更保留於本機） | `pending`（「等待同步」）／離線時 `offline`／錯誤時 `failed` |
| `saved` | `accountWorkspaceHasSynced === true` 且無待送出與錯誤 | `synced`（「已同步」）／離線且無待送變更時 `offline` |
| `conflict` | 同步錯誤狀態碼為 `409`（自動合併重試後仍版本衝突） | `failed`（「同步失敗」，顯示重試按鈕） |
| `expired` | 同步錯誤狀態碼為 `401` 或工作階段因過期被隔離（`quarantinedAccountOwnerId`） | `failed` |

---

### #15 行銷辦公室草稿（`marketing/agent-office`）

| 現況 | 觸發事件 | 目標狀態 | 備註 |
|---|---|---|---|
| 製作完成 | 審稿未過／自動核准／人工審核 | `needs_changes`／`approved`／`pending_approval` | — |
| `needs_changes` | 老闆編輯儲存（`Office.edit`） | `pending_approval` | — |
| 可編輯狀態（非 `published`／`publishing`） | `Office.approve`／`Office.reject` | `approved`／`rejected` | `approve` 會清除舊 `error` |
| `approved`（到排程時間） | `Publisher.publish` 發文前檢查未過 | `needs_changes` | 附 `PREFLIGHT_HOLD` 原因 |
| `approved`（到排程時間） | `Publisher.publish` 進入平台呼叫前 | `publishing` | 鎖定禁止編輯 |
| `publishing` | 平台 API 成功／拋出例外 | `published`／`failed` | — |
| `publishing`（異常中斷殘留） | `Office.__init__` 呼叫 `Store.recover_interrupted_publishing` | `failed` | **絕不自動轉回 `approved`**，由人確認平台未發出後再按「重新發佈」 |

---

### #16 驗證碼、OAuth 暫存狀態與帳號刪除

- **Email 驗證碼（`email_verification.py`）**：以 `expires_at`（15 分鐘 TTL）、`resend_available_at`（60 秒冷卻）、每小時寄送上限與 `attempt_count < 5` 控制有效性；驗證成功後立即標記帳號 `email_verified=True` 並清除挑戰。
- **OAuth／學生驗證暫存狀態（`transient_auth.py`）**：以 SHA-256 `state_hash` 與 `expires_at` 儲存，`consume_state` 原子比對 `kind`／`account_id`／`session_id`／`provider_id` 後單次刪除並回傳，身分不符時不破壞原狀態，過期或二次消費回傳 `None`。
- **帳號刪除（`repositories.py` `AccountDeletionMutationRequest`）**：首次刪除帶 `(mutation_id, session_token_hash, account_id, session_id)` 原子清除個資、匿名化公開貼文並寫入收據；重試可僅憑 `(mutation_id, session_token_hash)` 冪等取回 `idempotent=True` 結果與待清理物件鍵；同一 `mutation_id` 配不同指紋則回傳 `IDEMPOTENCY_CONFLICT`。
