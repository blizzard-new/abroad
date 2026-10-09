# TKU 治理接線進度

使用者於 2026-10-09 07:33 UTC 選擇原有計畫選項 3，本批納入五組審核、發布與回滾接線。只在候選分支與隔離合成資料實作／驗證；正式資料庫、main、部署、憑證與存取設定均不在授權範圍。

前一個獨立里程碑 `5af863f50f4ceecbb2b042d512137344fb2988d7` 已推送：12 項舊契約修正，182 項相關單元與 32 項瀏覽器測試通過，實際 collect 1,789 IDs／184 檔與 `09386aa` 原始 CI 相同，沒有移除、重複或新增 skip。產品 src 與 supabase tree 在這個里程碑仍與 `09386aa` 相同。之前 `c6e6155` 兩輪完整 CI 各為 1,767 passed／6 failed／16 skipped；5 項治理缺口及兩輪各一項非同步等待失敗保留原始證據，不予豁免。

治理第一階段將管理 HTML、admin session、來源候選／缺口／快照 CSV、deterministic staging、目的地審核／promote／history／rollback、流程 history／readiness／rollback 接到原有服務。既有 approve/reject/publish 與新增接線共用程序內鎖，所有入口仍用原有管理員驗證，private/no-store。CSV 是唯讀清單，沒有匯入 approvals；工作台沿用現有 UI，沒有自動批准或填補官方缺值。

尚不能由 API 接線宣稱交易驗收完成：現有 workflow publication 先分次儲存 revision 再改公開資料，目的地 Supabase event 寫入亦缺少跨程序 CAS。下一階段需補既有 stores 的原子命令提交／精確 snapshot 校驗、故障回復與冪等測試；不擴出平行審核機制，不降低雙審與來源／rule hash 門檻。readiness 僅呈現資料阻擋原因，並非部署許可。TKU 63 項官方缺口、未發布的 4 個 workflow 與所有既有學校資料保持原狀。

固定 SHA `e300479` 複核：32 項 API／權限／快照單元通過，但原有管理台錯誤回報 browser case 實際失敗（已結案卡片仍在待處理清單）。API 原本忽略 status query；第一次未固定 SHA 的短暫通過及本次真實失敗分別保留。後續追加 API enum 篩選與隔離回歸，不移除原卡片消失／完整 audit 等斷言。

固定 `e1c551a80ae4503a0c3be4359d028dd1562f3c6c` 的第一階段實際 57 unit／1 原 browser 通過，起迄工作樹乾淨，已正常推送。`5af863f` 兩輪全量 CI 均執行 1,789 unique IDs／184 檔：PR 1,766 passed／7 failed／16 skipped，push 1,768 passed／5 failed／16 skipped。12 舊契約皆通過；PR 另有兩個志願重排等待失敗，沒有改寫為通過。八個原 ZIP、152 原 members、20 原 XML 與實際 CLI byte-identical 重組已保存；完整 payload `ab7812540219a32398f2a54d13a17a6cb098efcc` 的 774 blobs 均由 GitHub remote tree核對，證明另見純證據分支 `artifacts/tku-acceptance-5af863f` 的 `5af863f-complete-remote-proof.json`。較早 `70476d2` 的 28 個被 Git ignore 排除的原 logs 已追加，不覆寫歷史 payload。

第二階段沿用既有命令，新增的 `governance_commands.py` 是 store 的 unit of work，沒有另設審核機制。JSONL 使用同一 data root 的程序／執行緒鎖、完整 snapshot CAS、durable journal、commit marker 與讀取前復原。revision、公開 payload、audit 或目的地 events 與 audit 一次提交；程序中斷與末段失敗必須回復每個原始 byte。來源替換保留原有不同證據角色，不因同 URL 而合併；清除全部 active approvals 前，把完整舊 attestations 保存至 edit history。legacy comparison baseline 使用 superseded reference，staging 不製造 published status 或真人 approvals。

Supabase 候選 migration `20261009080000_atomic_governance_commands.sql` 擴充原有 25-argument revision RPC 的命令 envelope，在同一 transaction 內取得既有命令的共用 advisory lock、校驗實際 DB snapshot、內容 hash、完整雙審與歷史鏈，提交 revision／public payload／audit 或 append-only destination events／audit。RPC signatures、grants、owner、RLS、policies、invoker security、search path 都不改；schema capability marker 沒有 public payload 或 review approvals。舊 schema 缺 capability 即停止寫入，不把 envelope 誤當一般 revision。這是待審 migration 檔，不曾對正式 DB 套用。

公開目的地單筆／列表、coverage 與 advisor 使用同一經審核 publication overlay。原始候選資料仍為 partial；promote 不填補未知事實，rollback 精確恢复前一版本。管理 UI 追加淡江母校選項，原長庚／臺北大學仍保留；只更動本候選分支的 UI 與 cache version，未接管其他 session 的臺大資料或工作目錄。readiness 與 CSV 仍是唯讀，並非發布／部署許可。已發布 workflow 的重複 API 提交維持 409 且零重複寫入；store 可辨識相同發布者、版本與說明的完成重試，舊 rollback 不能覆蓋後續公開版本。

診斷結果與固定 SHA 驗收分開：新增 11 個 store 情境通過；實際 admin／非 admin 與 10 種有效寫入 body 的 API 邊界通過。兩個原先 skipped 的 staging／source-replacement browser cases 在本批移除 skip，原斷言保留。另外兩個歷史 Phase C cases 仍保留原有 skip 和全部斷言：其固定 280 workflows／215 source gaps／7,067 rules、CGU 19 complete／58 pending 及 NTPU 舊矩陣不符合現有 bundles，實際啟用診斷失敗保存。沒有新增 skip／xfail，也不將這兩個案例宣稱已驗收；本批另有現行隔離 synthetic TKU workbench case 驗證真 admin、完整 sources／rules、雙人 attestations、來源修改失效、公開 promote／history／rollback。

全量 Supabase harness 在本環境兩次實際 exit 1：`failed to register layer: no space left on device`。另用獨立 PostgreSQL 17.6／兩個 PostgREST 14.12 跑十個原始治理 migrations 與兩個原始 canonical functions，實際 7 組檢查、20 RPC、16 command audit 通過，RPC 權限前後相同並清理全部隔離資源。初始 SQL 括號、fixture 適用年度與發布重試錯誤都有各自歷史 log。這個 subset 不替代全部 34 migrations、Storage、RLS 與既有 runtime checks；已將同一真實治理驗證接入原 full harness，完整候選 CI 結果另行封存。

後續診斷將 CAS 擴及 required-review-count、base version、發布／復原鏈與審核 metadata，另直接繞過 service 呼叫既有 RPC，驗證 DB 本身拒絕單人或同一人重複的發布。實際第七輪 8 組檢查、22 RPC、16 command audit 通過；migration SHA256 `9db91b01337c77a60a9114a0fb68acbd8f99e3561451bd3b4f357a590029cf5e`，隔離 cleanup 通過。現行 synthetic browser 情境完整通過；加入母校目錄 fixture 與等待真正完成的 publication history，原始診斷失敗仍保存。這些都是提交前診斷，固定 SHA 的起迄 guards、完整 collection 與最終 CI另作驗收。

共用整合點：`api.py`（publication overlay／issue status／shared lock）、`content_governance_routes.py`、`workflow_review_routes.py`、`content_governance.py`、`destination_profile_review.py`、`storage.py`、`release_readiness.py`、`models.py` 的失效 approvals 欄位、`static/content-review.html/js`、`docs/api/openapi.json`、兩個 runtime scripts 與新增 migration。測試共用變更僅對應 cache version、實際非同步 handler 完成 barrier 與上述兩個舊 skip 的解除；新的 API/store/browser 情境放獨立 TKU 檔。CGU／NTPU／NTU official_data 和 TKU 128 records／4 partial workflows／63 gaps 均未在治理階段變更。
