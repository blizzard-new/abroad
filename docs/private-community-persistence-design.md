# 私人社群持久層與交易邊界

- 狀態：`2026-08-31-pre-review.129`；Web 技術實作完成，21／21 份 migration 的 fresh PostgreSQL／PostgREST／Storage API file backend runtime 已通過，且 C-01 審查批次與 DATA-003 來源證據 CSV 的內容變更競態都會 fail closed；正式 Supabase 專案、既有資料升級、遠端 CI 與真人發布驗收尚未完成，維持 `NOT READY`
- 範圍：私訊邀請、接受邀請、訊息、封鎖、檢舉、檢舉審核，以及帳號刪除的公開去識別、私人清理、關聯資料 cascade 與加密物件清理收據
- 不包含：Flutter／SwiftUI／Kotlin、產品 AI、本地 Gemma 4 功能

## 1. 需求與不變條件

1. production 的私人社群資料只能使用 Supabase；JSONL 只供 development／test fallback。
2. 每一個私人社群寫入由單一 repository mutation 完成；Supabase 對應單一 RPC 與單一 PostgreSQL transaction。
3. 寫入必須重新驗證 account、anonymous identity、identity token、停權、參與者與資源狀態，不能只信任 API 先前的讀取結果。
4. 私訊邀請必須同時建立 conversation 與 initial message；任一失敗時兩者都不能留下。
5. 未接受邀請、非參與者或任一方已封鎖時不能新增訊息。
6. 封鎖自己不成立；封鎖前雙方必須曾有私訊邀請。
7. 同一位使用者不能檢舉自己的內容；同一資源只能有一筆該使用者的 pending 檢舉。
8. 檢舉審核採 expected-status CAS，並在同一 transaction 寫入 append-only moderation audit。
9. 相同 mutation ID 與相同使用者語意必須回放第一次結果；相同 ID、不同語意必須回傳 conflict。
10. 刪帳前應刪除私人對話、訊息與封鎖；pending 安全檢舉只去識別並保留 90 天，已結案檢舉可刪除。

## 2. 元件與資料流

```text
Web request
   │  account session + anonymous identity token
   ▼
FastAPI route
   │  typed mutation request + X-Community-Mutation-ID
   ▼
CommunityRepository
   ├─ development/test: JsonlCommunityRepository
   │    └─ 15 個社群檔案共用程序鎖、原子 replace、失敗 rollback
   └─ production: SupabaseCommunityRepository
        └─ 單一 service-role RPC
             └─ PostgreSQL transaction
                  ├─ account / identity / parent row locks
                  ├─ invariant checks
                  ├─ resource writes
                  └─ mutation receipt / moderation audit
```

API 不直接 append 或 save 私訊、封鎖與檢舉檔案。讀取也統一經由 `CommunityRepository`，避免 production 的 Supabase 寫入與本機 JSONL 稽核形成兩個來源。

## 3. Supabase 資料模型

| Table | 用途 | 關鍵完整性 |
| --- | --- | --- |
| `exchange_community_private_conversations` | 邀請、參與者、狀態與 revision | sender／recipient identity FK；兩者不可相同；狀態只允許 pending／accepted |
| `exchange_community_private_messages` | initial message 與後續訊息 | conversation／author identity FK；conversation 刪除時 cascade |
| `exchange_community_blocks` | 單向封鎖關係 | owner／target identity FK；唯一 owner＋target；不可封鎖自己 |
| `exchange_community_reports` | 公開內容或私訊檢舉 | pending／resolved／dismissed shape；reporter 可於去識別後為 NULL；reviewer 帳號刪除時 SET NULL |
| `exchange_community_mutation_receipts` | idempotency 結果 | mutation ID、operation、request fingerprint 唯一回放 |
| `exchange_community_moderation_audits` | 檢舉審核證據 | report 的 pending → resolved／dismissed 與 reviewer、note、fingerprint |

四張私人社群 table 全部啟用 RLS，撤銷 anon、authenticated 與 service role 的 direct mutation，只把 server-side select 與專用 RPC execute 權限授予 service role。

## 4. 鎖序與並行策略

一般順序為：

```text
account row
  → identity advisory lock（兩個 identity 時依字串排序）
  → actor identity row
  → counterpart identity row（需要時）
  → conversation / target resource row
  → child message or report row
  → mutation receipt
```

- conversation 建立與 block 會先對兩個 identity 取固定排序的 advisory transaction lock，避免 A→B 與 B→A 互鎖。
- message 與 conversation status 先鎖 conversation，再檢查當前狀態。
- 檢舉 private message 時先鎖 conversation、再鎖 message，與刪除 conversation 後 cascade message 的順序一致。
- report review 先鎖 moderator account，再鎖 report，CAS 成功後才更新 report、寫 audit 與 receipt。
- 資料庫時間由 `clock_timestamp()` 產生；client 送入的名稱、狀態與時間不成為可信欄位。

## 5. 語意型 idempotency

FastAPI 在未提供 header 時仍會產生 mutation ID；Web 或未來 App 若要安全重送，應在結果不確定時重用原本的 `X-Community-Mutation-ID`。

fingerprint 保留 actor、target、conversation 關係、訊息本文、檢舉理由與預期狀態，但排除每次 API 呼叫會重新產生的 resource ID、display name、server status 與 timestamp。這使「相同內容重送但生成不同 UUID」回放第一筆結果，而修改本文、target 或審核決定仍會得到 idempotency conflict。Python fallback 與 SQL 會各自重算相同語意 fingerprint，並拒絕 adapter 傳入不一致的值。

## 6. 刪帳生命週期

Supabase API 現在以 `exchange_commit_account_deletion` 執行單一資料庫 transaction：

1. 先依 account → session → 排序後 identity 固定順序鎖定 actor，並重驗 exact session。
2. 在刪除 identity 前，將公開內容作者改為「已刪除帳號」、清除 `source_url` 與 publish events。
3. 刪除私人 conversations（訊息 cascade）、blocks；pending reports 去識別並設定 90 天保留期限；其他本人 reports 與可能含私人 response 的 actor mutation receipts 刪除。
4. 先擷取私人文件庫的加密 Storage object keys，再刪除 account；workspace、session、provider links、通知、草稿、vault metadata、transient auth 與 identity 由 FK cascade／SET NULL 完成，Email challenge 依 server-side HMAC fingerprint 同交易刪除。
5. 寫入不含 account ID、Email 或 session token hash 的 deletion receipt；只保存 request fingerprint、二次雜湊 replay proof、計數與待刪 object keys。
6. PostgreSQL commit 後才呼叫 Storage API；成功後以 proof-bound RPC 標記完成。若 DB response 或 Storage 結果不確定，Web 保留並重用 `X-Account-Deletion-Mutation-ID`，同一 session token 可回放既有收據後重試物件刪除。

Supabase Storage API 不可能加入 PostgreSQL transaction，因此這裡採 durable cleanup handoff，而不是宣稱跨服務 ACID。未完成 Storage 收據不會因一般 retention cleanup 被刪除；既有文件庫 orphan cleanup 仍是第二道清理。JSONL／本機後端保留原有程序鎖清理流程，production 不會使用它。

## 7. 失敗處理與觀測

- repository transport／schema 錯誤回 503，不降級寫入 JSONL。
- stale status、重複但不同語意的 mutation、狀態競爭回 409。
- 權限、非參與者與封鎖回 403；缺資源回 404；無效 target 回 422。
- 每個 committed mutation 都保存 receipt；report review 另保存 moderation audit。
- 去識別 pending report 由 `exchange_purge_private_community_operational_data` 在保留期限後清除。
- 刪帳 receipt 只有 Storage 已完成的資料可在 7 天後清除；pending receipt 保留以供重送與營運清理。

## 8. 驗證與未完成門檻

本機驗證包含 JSONL 原子提交／rollback、語意重送、狀態 CAS、封鎖、檢舉、審核 audit、刪帳 transaction／Storage 失敗後重送、Supabase adapter RPC、SQL 靜態鎖序／權限，以及 OpenAPI 的私人社群、帳號刪除 mutation header 與來源證據 snapshot-bound export。現行 production 啟動會集中核對九個 backend identity；account、content governance、destination review、document vault、form drafts、transient auth、community、community suspension 與 workflow issue reports 都必須是指定 Supabase backend。`2026-08-31-pre-review.129` 的完整回歸為 804 項非 E2E＋49 項 Chromium E2E，合計 853 passed。固定版 `pglast 8.4` 已解析全部 21 份 migration 的 471 個頂層 statements、11 個 SQL function bodies 與 51 個 PL/pgSQL units，並納入 pytest 與 CI；OpenAPI 現行 snapshot 為 `2026-08-31.2`。

`scripts/validate_supabase_runtime.py` 已以 pinned PostgreSQL 17.6／兩個獨立 PostgREST 14.12／Storage API 1.60.4，在全新 tmpfs DB 與隔離 Storage volume 依序套用 21／21 份 migration。fresh runtime 驗證 32／32 張 table 啟用並強制 RLS、browser direct grants 為 0、三個 workflow issue report service RPC 的 ACL 正確，以及既有五張敏感表 direct DELETE denial、transient auth 並行限流、workspace CAS、刪帳晚期錯誤完整 rollback、Storage timeout 保留 durable receipt 與密文、真實批次 delete／重送、proof-bound ack，及 `list-v2` 巢狀 orphan cleanup 只移除未引用物件。

同一輪 runtime 已實際執行 workflow issue report 的提交、冪等回放／衝突、審核 expected-status CAS、限流與非安全來源 URL 防護；刪帳時 pending 案件會去識別並保留最多 90 天，已結案案件會隨帳號刪除，去識別後才結案的終態最多保留 24 小時，已刪除 reviewer 也會去識別。到期案件 purge、Storage orphan cleanup，以及 Compose project 的 container、network、volume 零殘留清理均已實跑通過。

同一 fresh runtime 也透過兩個 API 實例同時驗證公開社群同 mutation 發文、父貼文刪除／留言新增、私人社群雙向邀請、封鎖／傳訊與雙管理員檢舉審核；每種結果都與最終 resource、receipt 及 audit 數量一致。公開發文、公開 moderation、私人邀請＋初始訊息、私人訊息、公開貼文檢舉及檢舉審核另在 receipt 最後寫入點注入六次 `P0001`，錯誤均向外傳遞，且 resource、rate event、conversation、message、report、status、revision、audit 與 receipt 均完整 rollback，`partial_rows=0`。每次執行只使用隨機 loopback port 與程式產生的唯一保留前綴 Compose project；down return code 及 project label 下的 container、network、volume 零殘留都是必要通過條件。

`scripts/validate_supabase_runtime.py` 現亦由 `.github/workflows/quality.yml` 以 frozen 環境執行，step 上限 20 分鐘且失敗不能忽略。所有外部子程序另有 10／30／120／600 秒分級 timeout，任意完整 project 名稱會被拒絕；validation 成功但 final cleanup 非零或仍有 label 殘留時，腳本仍 exit 1 且不輸出 passed。validation、logs 與 cleanup 同時失敗時，原始 validation error 保持主要錯誤。上述證據只代表本機全新資料庫與隔離 Storage file backend；遠端 GitHub Actions 尚未首次執行，也不能取代正式 Supabase 或既有資料升級驗證。

下列項目仍需正式環境完成，不能由本機測試代替：

- 將目前 21 份 migration 依相同順序套用到正式 Supabase 專案，並另以具代表性的既有資料驗證升級與 rollback 路徑；本機 fresh clean apply 不能代替既有資料升級。
- 在正式 Supabase 設定再次核對 RPC signature、service-role grants 與 RLS；本機 PostgREST direct DML denial 已通過。
- 在正式 Supabase project 及既有資料上重驗兩個以上 API instance 的邀請、訊息／封鎖、檢舉／刪帳與雙管理者審核；本機全新資料庫的核心競態已通過。
- 在正式 Supabase 專案的實際 Storage backend 重驗 DB commit 後 bucket delete timeout、重送、orphan cleanup、pending receipt 營運告警與備份還原；本機已證明真實 Storage API file backend 行為，但不能代替正式環境。
- 讓遠端 GitHub Actions 首次完整執行 frozen tests、migration parser 與 runtime gate；本機 853 passed 不能冒充遠端 CI 證據。

因此 `2026-08-31-pre-review.129` 仍為 `NOT READY`；本機 fresh runtime、審查批次與來源證據 composite snapshot fail-closed 通過只關閉本機驗證缺口，不會自動核准正式部署、真人資料或 Web 發布。

## 9. 取捨與成長門檻

- 目前 Supabase private read 由 service-role server 讀取後在 API 依 identity／conversation 過濾，沒有把資料直接交給 browser，但資料量增長後應把 filter 下推到 repository query 或受控 read RPC。
- 共用 core mutation RPC 能集中鎖序與 invariant；代價是 SQL 較長，因此保留小型 wrapper 與 adapter 單元測試，避免 API 依賴 core payload 細節。
- JSONL 採全社群鎖以確保本機 fallback 正確性，不追求多程序擴展；production 不允許使用此 backend。
