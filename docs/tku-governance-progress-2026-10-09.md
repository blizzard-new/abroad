# TKU 治理接線進度

使用者於 2026-10-09 07:33 UTC 選擇原有計畫選項 3，本批納入五組審核、發布與回滾接線。只在候選分支與隔離合成資料實作／驗證；正式資料庫、main、部署、憑證與存取設定均不在授權範圍。

前一個獨立里程碑 `5af863f50f4ceecbb2b042d512137344fb2988d7` 已推送：12 項舊契約修正，182 項相關單元與 32 項瀏覽器測試通過，實際 collect 1,789 IDs／184 檔與 `09386aa` 原始 CI 相同，沒有移除、重複或新增 skip。產品 src 與 supabase tree 在這個里程碑仍與 `09386aa` 相同。之前 `c6e6155` 兩輪完整 CI 各為 1,767 passed／6 failed／16 skipped；5 項治理缺口及兩輪各一項非同步等待失敗保留原始證據，不予豁免。

治理第一階段將管理 HTML、admin session、來源候選／缺口／快照 CSV、deterministic staging、目的地審核／promote／history／rollback、流程 history／readiness／rollback 接到原有服務。既有 approve/reject/publish 與新增接線共用程序內鎖，所有入口仍用原有管理員驗證，private/no-store。CSV 是唯讀清單，沒有匯入 approvals；工作台沿用現有 UI，沒有自動批准或填補官方缺值。

第一階段當時尚不能由 API 接線宣稱交易驗收完成：原 workflow publication 先分次儲存 revision 再改公開資料，目的地 Supabase event 寫入亦缺少跨程序 CAS。當時下一階段需補既有 stores 的原子命令提交／精確 snapshot 校驗、故障回復與冪等測試；不擴出平行審核機制，不降低雙審與來源／rule hash 門檻。readiness 僅呈現資料阻擋原因，並非部署許可。TKU 63 項官方缺口、未發布的 4 個 workflow 與所有既有學校資料保持原狀。

固定 SHA `e300479` 複核：32 項 API／權限／快照單元通過，但原有管理台錯誤回報 browser case 實際失敗（已結案卡片仍在待處理清單）。API 原本忽略 status query；第一次未固定 SHA 的短暫通過及本次真實失敗分別保留。後續追加 API enum 篩選與隔離回歸，不移除原卡片消失／完整 audit 等斷言。

固定 `e1c551a80ae4503a0c3be4359d028dd1562f3c6c` 的第一階段實際 57 unit／1 原 browser 通過，起迄工作樹乾淨，已正常推送。`5af863f` 兩輪全量 CI 均執行 1,789 unique IDs／184 檔：PR 1,766 passed／7 failed／16 skipped，push 1,768 passed／5 failed／16 skipped。12 舊契約皆通過；PR 另有兩個志願重排等待失敗，沒有改寫為通過。八個原 ZIP、152 原 members、20 原 XML 與實際 CLI byte-identical 重組已保存；完整 payload `ab7812540219a32398f2a54d13a17a6cb098efcc` 的 774 blobs 均由 GitHub remote tree核對，證明另見純證據分支 `artifacts/tku-acceptance-5af863f` 的 `5af863f-complete-remote-proof.json`。較早 `70476d2` 的 28 個被 Git ignore 排除的原 logs 已追加，不覆寫歷史 payload。

第二階段沿用既有命令，新增的 `governance_commands.py` 是 store 的 unit of work，沒有另設審核機制。JSONL 使用同一 data root 的程序／執行緒鎖、完整 snapshot CAS、durable journal、commit marker 與讀取前復原。revision、公開 payload、audit 或目的地 events 與 audit 一次提交；程序中斷與末段失敗必須回復每個原始 byte。來源替換保留原有不同證據角色，不因同 URL 而合併；清除全部 active approvals 前，把完整舊 attestations 保存至 edit history。legacy comparison baseline 使用 superseded reference，staging 不製造 published status 或真人 approvals。

Supabase 候選 migration `20261009080000_atomic_governance_commands.sql` 擴充原有 25-argument revision RPC 的命令 envelope，在同一 transaction 內取得既有命令的共用 advisory lock、校驗實際 DB snapshot、內容 hash、完整雙審與歷史鏈，提交 revision／public payload／audit 或 append-only destination events／audit。RPC signatures、grants、owner、RLS、policies、invoker security、search path 都不改；schema capability marker 沒有 public payload 或 review approvals。舊 schema 缺 capability 即停止寫入，不把 envelope 誤當一般 revision。這是待審 migration 檔，不曾對正式 DB 套用。

公開目的地單筆／列表、coverage 與 advisor 使用同一經審核 publication overlay。原始候選資料仍為 partial；promote 不填補未知事實，rollback 精確恢复前一版本。管理 UI 追加淡江母校選項，原長庚／臺北大學仍保留；只更動本候選分支的 UI 與 cache version，未接管其他 session 的臺大資料或工作目錄。readiness 與 CSV 仍是唯讀，並非發布／部署許可。已發布 workflow 的重複 API 提交維持 409 且零重複寫入；store 可辨識相同發布者、版本與說明的完成重試，舊 rollback 不能覆蓋後續公開版本。

診斷結果與固定 SHA 驗收分開：新增 11 個 store 情境通過；實際 admin／非 admin 與 10 種有效寫入 body 的 API 邊界通過。兩個原先 skipped 的 staging／source-replacement browser cases 在本批移除 skip，原斷言保留。另外兩個歷史 Phase C cases 仍保留原有 skip 和全部斷言：其固定 280 workflows／215 source gaps／7,067 rules、CGU 19 complete／58 pending 及 NTPU 舊矩陣不符合現有 bundles，實際啟用診斷失敗保存。沒有新增 skip／xfail，也不將這兩個案例宣稱已驗收；本批另有現行隔離 synthetic TKU workbench case 驗證真 admin、完整 sources／rules、雙人 attestations、來源修改失效、公開 promote／history／rollback。

全量 Supabase harness 在本環境兩次實際 exit 1：`failed to register layer: no space left on device`。另用獨立 PostgreSQL 17.6／兩個 PostgREST 14.12 跑十個原始治理 migrations 與兩個原始 canonical functions，實際 7 組檢查、20 RPC、16 command audit 通過，RPC 權限前後相同並清理全部隔離資源。初始 SQL 括號、fixture 適用年度與發布重試錯誤都有各自歷史 log。這個 subset 不替代全部 34 migrations、Storage、RLS 與既有 runtime checks；已將同一真實治理驗證接入原 full harness，完整候選 CI 結果另行封存。

後續診斷將 CAS 擴及 required-review-count、base version、發布／復原鏈與審核 metadata，另直接繞過 service 呼叫既有 RPC，驗證 DB 本身拒絕單人或同一人重複的發布。實際第七輪 8 組檢查、22 RPC、16 command audit 通過；migration SHA256 `9db91b01337c77a60a9114a0fb68acbd8f99e3561451bd3b4f357a590029cf5e`，隔離 cleanup 通過。現行 synthetic browser 情境完整通過；加入母校目錄 fixture 與等待真正完成的 publication history，原始診斷失敗仍保存。這些都是提交前診斷，固定 SHA 的起迄 guards、完整 collection 與最終 CI另作驗收。

共用整合點：`api.py`（publication overlay／issue status／shared lock）、`content_governance_routes.py`、`workflow_review_routes.py`、`content_governance.py`、`destination_profile_review.py`、`storage.py`、`release_readiness.py`、`models.py` 的失效 approvals 欄位、`static/content-review.html/js`、`docs/api/openapi.json`、兩個 runtime scripts 與新增 migration。測試共用變更僅對應 cache version、實際非同步 handler 完成 barrier 與上述兩個舊 skip 的解除；新的 API/store/browser 情境放獨立 TKU 檔。CGU／NTPU／NTU official_data 和 TKU 128 records／4 partial workflows／63 gaps 均未在治理階段變更。

固定第二階段候選 `3a8ca75680e941da478e06ec1162cebeb8152619` 已正常推送。開始／結束 clean guard 的 unit 實際 316 passed／4 個原有 skipped，SQL subset 實際 8 組／22 RPC／16 audit，collect 1,824 unique IDs／187 檔，原 1,789 IDs 全保留、增加 35、沒有重複或移除。固定 browser 實際 35 passed／1 failed：原批次 staging case 重新進入工作台時，15 秒內 queue 尚未讀完，按鈕仍 hidden；沒有改動原 body／斷言或再加 skip。後續修正管理台初始化順序，先讀取選定 queue 再讀獨立 history／目的地面板，減少無關讀取爭用同一 snapshot lock；保留全部來源、雙審及 POST 的 hash／CAS 檢查。

`3a8ca756` 完整 CI PR run `37909160698` 與 push run `37909153439` 均失敗，但八個 job 約兩秒結束、steps 全空、artifacts 為空、log 404。八份 GitHub check annotations 明示「The job was not started because recent account payments have failed or your spending limit needs to be increased.」因此不是 1,824 案已執行後的測試失敗，沒有可偽造的完整 XML／34-migration runtime 成功。本批不改付款或 spending limit，固定本機測試和 CI 平台阻塞各自封存。

M1 `e1c551a` 完整原始 PR `37905061634`／push `37905055678` 各實際 1,786 passed／0 failed／16 skipped，1,802 unique IDs／185 檔全部執行，原 1,789 IDs 及 66 個歷史失敗 IDs 保留且實際 PASS。純證據分支 `artifacts/tku-governance-e1c551a` 的 payload `7b1aa1a1c4935247bb7dafca532b25b8bf36fd8d` 含八個原 ZIP／152 members／20 原 XML；每份 XML 實際 CLI 重組與原 bytes 相同，211 raw＋545 readable 的全部 756 remote blobs 的 paths／sizes／git hashes 逐筆相同，readable 每檔小於 500 KB。外加 remote proof commit `da081b9412fc2091fadcddd502a8b52c4c16c4c4` 已正常推送。M1 通過不代替第二階段原子治理候選的固定驗收。

批次 queue 優先載入修正的提交前診斷：原 staging browser body 與全部斷言未修改，實際 1 passed／110.48 秒。後續接受結果仍以新固定 SHA 的起迄 guard、全量 collection 與原始 XML 為準。

本輪三項有界 follow-up 在固定 `3a8ca756` 的十項治理 migrations 真實 DB 重現：一審只由 synthetic-a 落庫時，複製 approval 並僅改 reviewer_id=synthetic-b 的 publish envelope 被接受、snapshot 改變；legacy/fallback 公開流程 revisions 空時 refresh 回傳 400／Staging cannot approve or publish，公開內容未變；隔離 PostgREST cap=2、DB 三筆 revision 時 snapshot 只回兩筆，沒有截斷標示。三份修前 case-result／原始 log 都保存；這些是 service-only 與相容性診斷，沒有證明一般 admin API 可繞過，更不是對外安全事件。

修正仍在既有服務與 RPC：refresh 的 legacy reference 改 superseded；approval 命令一次只能 append 一份綁定 actor 的證據並保留舊 array，publish 不得新增／改寫 approvals，且每一份必須在 DB 中已有獨立 approve 命令的 actor／revision／hash／完整 attestation provenance。API 仍從 authenticated account.id 取得 actor，publish body 仍僅 note。命令 kind／operation 不可錯置，staging／approval／edit／reject 不能夾帶 public payload。完整原始 envelope 的 canonical hash 保存於既有 append-only audit，原 envelope 重送回同一結果且不重做 mutation；此項與 service 重讀後的 no-op 分開驗證。

五表 snapshot 改用 unique-key 穩定排序、offset 分頁及 Prefer count=exact；每頁 Content-Range、總筆數與身份都必須一致，缺 count、未知總數、截斷或重複會停止寫入，剩餘跨頁變動由同一 SQL 全表 CAS 拒絕。只在自有隔離 PostgREST 以 role-local cap=2 驗證，測後 restore settings，未調查或變更正式環境 cap。

提交前真 SQL follow-up 實際 13 組／38 RPC／26 command audit 通過，仍只有十項治理 migrations 與兩個原始 canonical functions。兩個真正不同 PID 的 RPC interval 重疊，回應為一個 200、一個 409，DB 只保存一份 approval；同一勝出 envelope 重送無資料或 audit 差異。cap=2 原 GET 回 2／9，完整 snapshot 回 revisions9／workflows7／reviews5／promotions1／rollbacks1，與 DB 實際 counts 相同，正常 approve 成功且 cap settings 恢復。完整 RPC envelope、每次 audit delta、失效 approvals DB 回讀、legacy baseline／pending 與 public 不變、兩類 exact-envelope retry 均保存。source migration SHA256 `31b353f303a073f1dfd267cb87f67adbdd6f15aacd149c94348889b535504fcd`；RPC ACL／owner／security／search_path 前後相同，cleanup passed。38 個相關 unit 診斷通過；新固定 SHA 驗收另行記錄。

固定 `f99d65d4fdf25d09d302b59cc40106ca74a706a8` 已正常推送，clean 起迄 guard 實際 unit320 passed／4 原 skipped，SQL13組／38RPC／26audit、cleanup passed，collect1827 unique IDs／187檔、原1789全保留、新增38、沒有移除或重複。語法／OpenAPI／34 migrations parse／依賴稽核實際 exit0；原依賴 wrapper 在唯讀 home cache 失敗後，使用 pip-audit 原參數加官方支援 --cache-dir 至任務 /tmp 重跑，沒有改 HOME、憑證或存取權限。此版 browser 實際35 passed／1 failed，仍是原 staging 的15秒 hidden等待，按SHA保留未改写。PR／push八個CI jobs均steps空／artifacts空，原annotations明示付款／spending limit阻止啟動。

`3cbe976` 四個本機全量分片實際完成；原批次 staging 仍有載入失敗，後續原XML計數另行封存，不把前一次單案例通過當成整批穩定通過。後續診斷先將 queue 與 readonly readiness 分開，單獨仍重現失敗，原XML保留。實際 cProfile 再定位到 batch builder 的來源 URL 正規化重複約50萬次：855 workflows／778 batch rows，9478萬calls／21.02秒。對完全純函式加4096筆LRU後，同一資料只350萬calls／3.60秒；1062個實際／邊界URL輸出與f99原函式相同，整個 normalization body AST不變，沒有改URL身份政策、公開資料、hash／CAS／雙審閘門或原test body／assert／15秒timeout。原staging診斷實際1passed／73.73秒；54frontend unit通過。後續新固定SHA guard與整批browser結果另作驗收。

共用整合點補充：`source_url_policy.py` 僅新增純字串函式的有界結果快取；`content-review.js` 的 readiness 仍即時計算、失敗顯示 blocked／檢查失敗，queue和report均使用requestSequence拒絕舊回應。queue載入完成不表示readiness READY；所有發布仍由原server命令驗證。
