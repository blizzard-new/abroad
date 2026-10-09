# TKU runtime恢復、Quality停用及rollback覆核

使用者於2026-10-09T11:36:59.368787+00:00批准關閉blizzard-new/abroad自動測試，保留Render與部署。本環境既有gh存取於11:40可用（沒有修改登入或token）；官方PUT `/repos/blizzard-new/abroad/actions/workflows/374368612/disable`於11:41:04 UTC成功。API名`.github/workflows/quality.yml`／檔內名Web quality，active→disabled_manually已回讀。部署workflow374368613 `Deploy to Supabase`仍active；main、branch protection、付款／權限／憑證／Render不變。沒有重試GitHub帳務run或刪歷史artifact／通知。完整readback與disable證明保存在`/tmp/tku-governance-runtime-recovery/quality-disable-proof.json`。

只讀磁碟查核：root overlay32GB／可用約17GB、獨立tmp8.9GB／可用約2.9GB，inodes並未用滿；Docker driver=vfs、無containers／volumes／build cache，兩個image約299MB是API邏輯估值，不能代表VFS實際磁碟量。`du`／`stat /var/lib/docker/vfs`被permission denied，沒有繞過讀取或改daemon。29層pinned SupabasePostgres manifest的compressed blobs合計367,203,535 bytes；VFS逐層deep copy可能放大空間，但不是已核實唯一成因。[Docker官方VFS說明](https://docs.docker.com/engine/storage/drivers/vfs-driver/)。

原兩份ENOSPC log已核對與既有遠端raw證據byte-identical。四個舊worktrees含本機keys與screenshots，全部排除清理；唯一安全清理是自有`/tmp/tku-package-build-{12b30cd,5e010b8}/build/lib`，每個1009檔皆SHA256等於保留的src副本，無unique evidence或credential。共釋放380,440,118文件bytes，tmp可用約3.3GB，root仍約17GB。未刪Docker dangling image（歸属不能確認）、worktrees、證據、data或其他session檔案。

同固定source `5d48a01a7a58aad7fe972e7ec1434e0fb74e93c3`於11:42:26–11:44:11原命令完整`validate_tku_community_runtime.py`再跑104.53秒，起迄clean、實際exit1，仍在原pinned Postgres拉取時`failed to register layer: no space left on device`，未到34 migrations／Storage。原log26,740 bytes，SHA256 `3b8da32ee15702a20de53fecd8093da8f427edb24b4eaf350b6fdb8b4be96440`；run guards與清理清單保留。無法確認更深清理安全，故停止full-runtime反覆嘗試；後續需環境owner查核daemon實際磁碟／quota，或另明確授權的資源處理。沒有擴容付費、換image／driver或把subset當full通過。GitHub帳務只阻塞GitHub runner渠道，不是本機驗收必須付費的前提。

第二次service-only覆核在未修改5d的隔離SQL重現，沿用固定raw RPC005 envelope與原mutation deltas；原publish409／六表不變，僅operation改`rollback_published_workflow`後200／六表改變。只屬合成SQL相容性／provenance邊界，不主張一般admin API可達。舊raw與`1343abd` proof未覆寫；新修前driver、完整六表before/after及responses在`rollback-pre-fix/result.json`，cleanup passed。

候選SQL仍沿用原RPC signature／grants／owner／invoker security／search_path，新增operation／publication_action一致性、唯一published row、不可夾帶／修改舊revision、stored current public pointer一致、new version／base／restore chain與精確歷史review快照。實際published狀態觸發provenance驗證，不能用operation標籤豁免；rollback沿已落庫、可追溯的rollback鏈找到original standard publication，每一份review須已有相應revision／hash／完整attestation的獨立approve記錄及真正published receipt。無完整legacy audit provenance則停止，不能補造歷史真人approval。

原子的完整來源／rule hash與required review count仍不變；staging不製造approval或publish。否決會回409並保持六表snapshot／audit不變。11個真否決case涵蓋operation/action錯置、NULL／缺失／當期restore IDs、非current被撤回、wrong version、假reviewer、改superseded companion與reject標籤夾帶published row；暫時損壞合成歷史review array的negative fixture在finally精確restore。另驗合法rollback、replay及恢復曾完成rollback的版本，精確保留original review lineage。

提交前第一次／第二次真SQL診斷各失敗，因嚴格metadata比较將Postgres timestamptz尾端0的輸出差異誤當變更；實際trace取得`.032280`／`.03228`。修正僅對detected_at／reviewed_at按timestamptz同instant比較，其他metadata仍完全相同；positive fixture固定尾0，原失敗log與逐欄trace不改寫。第三輪真SQL16組／55RPC／31command audit通過、ACL等前後相同、cleanup passed。這些屬提交前診斷，新固定source的全量local suite與真SQL結果另封存，不將舊5d重標為修正後成功。

CI有界方案僅提案、未改YAML：現有PR＋feature push各4shards、github.ref不同無去重，各shard重做同一fullRuntime。完整M1實際8 artifacts19,279,122 bytes，仍按原30天保存。現在Quality保持停用；日後若另獲授權恢復，可只對PR／main push／manual跑同一完整suite，feature push不另重複，約減半每PR更新重複工作；同一run的syntax／OpenAPI／parse／dependency/fullRuntime可只做一次，4shards仍完整執行全部IDs、全部原斷言／閘門不變。維持30天留存及所有唯一XML／log／官方原附件／HTTP錯誤／screenshots；只對hash證明的generated source/cache副本提出未来排除，不改既有remote證據。[GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)、[artifact retention](https://docs.github.com/en/actions/tutorials/store-and-share-data)。

本輪共用merge surfaces只有atomic governance migration與既有runtime script，另新增`validate_governance_rollback.py`的隔離test情境；不更動各校official_data、一般學生API、Render或部署設定。


## 缺失發布陣列的後續覆核

固定 `b8f5e075fe920860492c0eb3e18e06c5da71903b` 的自有隔離 DB 上，從合法 rollback envelope 只刪除 `published` 鍵，實際回200並改變六表快照；未主張一般API可達。原 `case-result.json`、完整before/after、envelope及原log保存在 `/tmp/tku-governance-runtime-recovery/missing-published-pre-fix/`。原driver以刻意拋出例外停止並清理，exit1是重現結果，不是補修後通過。

補修先用 `jsonb_typeof(...) IS DISTINCT FROM 'array'` 明確拒絕缺失、JSON null、object與string，再執行array長度限制，防止SQL NULL跳過拒絕。標準發布與rollback各自驗證8種非法型別回400、空public payload回409且六表不變；rollback另驗重複revision ID回409。合法發布／rollback／精確重試、獨立雙人review、真正並行CAS與late-failure atomicity仍保留。歷史standard及rollback收據須同時綁定實際actor、review count、完整review快照與公開workflow payload，不能只存在operation／revision標籤。[PostgreSQL JSON extraction與NULL](https://www.postgresql.org/docs/17/functions-json.html)、[NULL-safe比較](https://www.postgresql.org/docs/17/functions-comparison.html)。

既有b8四分片測試在原固定工作目錄繼續保留結果；新SQL／驗證程式須另在新固定source完整執行，不能將b8結果換標。原學校data、src、tests、工作流程YAML及原timeout／skip／斷言沒有修改。本輪新候選推送只存程式碼，Quality保持disabled，不啟動GitHub付費或自動測試。
