# TKU 候選後續治理整合範圍

查核日：2026-10-09。基準 main：`f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。
本批先完成過期登入提示、私人社群原子重試、校板會員政策、署名一致性與五個瀏覽器回歸的前置條件修補。沒有為測試全綠新增整套治理功能，亦未移除下列失敗測試。

## 已確認的政策與實作邊界

使用者於 2026-10-09 明確決定「所有已驗證 Email 的會員都能看、發文」。校級看板的文章與留言讀寫皆採此會員門檻，不限母校；公共板原有公開讀取政策保留。全站列表與按 ID 篩選亦不得泄漏受限校板內容。自填 `catalog_home_university` 是選校資料，不是已驗證學籍；`verified_school`／`verified_department` 署名只能來自真正的 server-owned `student_status_verified` 與 `verified_university`。

Python 預覽、API 建立與 JSONL 儲存共用 `access_control.community_author_display_name`。SQL 是另一執行環境，追加 migration 恢復相同學籍條件與「學生」署名，並只在現行函式內追加 TKU 的 ID／校名映射。保留 20261003 的跨校 Email 發言、20260930 的留言串／回應，以及 20261007 的其他選校流程邏輯；不覆寫舊 migration、不變更 ACL／RLS／ownership。正式資料庫沒有執行此 migration。

## 仍缺失的五組整合

| 組別／原失敗 | 現有可復用模組 | 缺少的接線 | 有界下一階段 |
|---|---|---|---|
| 管理審核工作台（browser case 3） | `static/content-review.html/js/css`；`workflow_review_routes.py` 的版本列表／比較／approve／publish／reject | 安全 HTML 入口與 UI 使用的其他管理 API；現有 UI 有約 4,000 行，不是單一 selector 錯誤 | 先逐一列出 UI 真正呼叫的路由；只串已存在的 store／service。管理員以外 401／403，private/no-store；不讓 staging 自動 approve／publish |
| 來源替換（case 27） | `review_source_candidates.list_source_replacement_candidates`／`list_source_replacement_candidate_review_rows`；`content_governance.list_source_evidence_gap_review_rows`；既有研究候選檔 | `/admin/application-workflow-source-replacement-candidates`、兩種 source-evidence／replacement CSV 與 pending revision 的修改 API | 先補唯讀候選／snapshot-bound CSV；單筆替換須精確校驗原 URL、版本與 hash，清除舊 approvals，只產生 pending revision。遇 URL 改址不能自動認定當期適用 |
| 快照批次 staging（case 28） | `release_readiness.build_application_workflow_review_batch_rows`、`stage_application_workflow_review_batch`；既有 batch request/result models | `/admin/application-workflow-review-batches/{batch_id}/stage` 及其 snapshot-bound 讀取／rules CSV | 只接受精確快照、既有 deterministic batch 與上限；整批前後 fingerprint 不同則 409。結果必須 `approvals_created=0`、`workflows_published=0`、公開資料無變化 |
| 目的地審核／發布／回滾（case 29） | `destination_profile_review` 的 queue、batch/checklist、`record_destination_profile_review`、`promote_destination_profile`、`rollback_destination_profile`；local／Supabase stores | destination queue／CSV／batch／reviews／promotions／publications／rollbacks API | 先讀取既有 queue／history，之後按既有兩位獨立審核、來源與欄位 hash、CAS 和 append-only audit 串命令；partial profile 不能因 UI 接線而升格完整查核 |
| 流程發布歷史／回滾／readiness（case 30） | `content_governance.build_application_workflow_publication_history`、`rollback_published_workflow`；`release_readiness.build_application_workflow_release_readiness`／`build_web_release_readiness` | `/admin/application-workflow-publications`、`/admin/application-workflow-rollbacks`、`/admin/web-release-readiness` | 先唯讀歷史／缺口／readiness；回滾須驗 current publication、revision/hash、兩位獨立 approvals 和目標歷史完整性，採現有 store 的 CAS。成功後才通知；不新增通知外寄能力 |

## 上架必要性與待定範圍

TKU 128 筆方案資料、當期／舊年分離、資格來源、原始附件与 `official_partial` 目的地資訊可以在既有公開資料 API 展示。本期四個 workflow 仍是未發布的參考流程，這五組管理接線不能代替真人審核、也不能把未知期限或學制補成已知。若要求「完成正式雙審並发布當期流程」，則這些接線與實際審核缺口均是必要前置；目前僅整理資料／可整合候選的要求不授權自動發布。

下一階段需要確認的是產品範圍：只接唯讀管理台與快照報表，或也接現有 staging／審核／發布／回滾命令。現有模組已有命令邏輯，不另造替代儲存、簡化單人發布或自動核准。另應獨立確認「流程錯誤回報」現行選校邏輯與 OpenAPI 的 verified-student 說明是否一致；本次校板政策不自動改動該功能。

所有發布／回滾／並行與晚期故障驗證只能用隔離合成資料。正式 DB、main、其他學校工作目錄、憑證、存取權限與部署均未改動。這五組測試保留失敗，不列為 infrastructure failure 或以 baseline 失敗豁免。
