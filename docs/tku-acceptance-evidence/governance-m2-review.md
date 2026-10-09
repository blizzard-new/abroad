# TKU 原子治理與有界相容性驗證

候選產品分支 `data/tku-exchange-20261008`，固定 source `5d48a01a7a58aad7fe972e7ec1434e0fb74e93c3`。原 main 基準及本輪遠端 main 均為 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。本文件位於純證據分支 `artifacts/tku-governance-m2`；未合併 main、部署或操作正式資料庫，未更動付款、憑證、存取權限或安全設定。Draft PR #2 保持 draft／未 merge。

TKU 資料為128唯一計畫列／119原文學校名稱。最新已核實的2027–2028日語二甄僅4校／7名；2026-09-30 12:00 Asia/Taipei校內申請已截止，0個可校內新申請選項。124個115／2026–2027舊期計畫清楚分開；不把全部協議姊妹校、院系計畫或外校incoming條件混入校級outbound。當期重要欄位89／152核實（58.6%），63缺口（45有界查找後新版未核實、18來源矛盾／適用問題），13矛盾群組。所有四校workflow仍未發布、沒有真人approval；欄位來源保存官方URL、頁碼／原文、適用年度及查核日。

五組管理台／來源替換／快照staging／目的地審核發布回滾／流程歷史readiness回滾沿用既有服務。JSONL命令以完整snapshot CAS、程序鎖、durable journal、commit marker及讀取前復原一次提交公開內容与audit。既有Supabase RPC保持signature／owner／ACL／invoker security／search_path，新增同交易advisory lock、全表CAS与完整審核provenance；舊schema不支援命令即停止寫入。雙人與完整source／rule hash要求保持。來源變更保存完整invalidated approvals、清空active approvals。

三項修前重現均固定在`3a8ca756`的自有隔離真SQL：僅A已落庫卻複製approval改B的raw publish被接受；legacy/fallback無revision的首次refresh遭400；cap2／DB3回2而未報截斷。原始`case-result.json`、driver及logs分開保存。這些是service-only相容性／provenance診斷，沒有證明一般admin API可繞過，沒有對外事件主張。修後publish不得新增／改寫approvals，每份均須有DB獨立approve的actor／revision／hash／full attestation證據；approve只能append一份綁定actor的證據。baseline改superseded reference，snapshot以穩定唯一鍵、exact count、Content-Range與offset完整分頁；缺count／未知total／截斷／重複停止寫入。

## 按實際 source 保存結果

| 固定產品source | 實際本機結果 | 範圍與限制 |
|---|---|---|
| `3a8ca756` | unit316P／4原S；browser35P／1F；SQL8組／22RPC／16audit；collect1824 | 原staging15秒hidden失敗按原XML保留 |
| `3cbe976` | 全量1824個unique IDs全部執行：1808P／2F／14原S，187檔 | 原staging及migration固定33檔計數失敗；四分片原XML、全部IDs／guards保存 |
| `f99d65d` | unit320P／4原S；browser35P／1F；SQL13組／38RPC／26audit；collect1827 | 三項SQL follow-up修正通過；原staging仍F |
| `2f4d7ec` | unit320P／4原S；browser36P；SQL13組／38RPC／26audit；collect1827；七項checks0 | 純URL有界快取／queue與readonly readiness分開後，原staging body／assert／15秒timeout不變並通過 |
| `5d48a01` | unit322P／4原S；browser36P；SQL13組／38RPC／26audit；collect1827；七項checks0；TKU補充86P | 四種主要命令起迄clean guard；只同步migration test精確34／563／73與新增逐檔断言；產品src／scripts／supabase／E2E trees均與2f相同 |

最新source實際collect為1827 unique IDs／187檔；原093 CI的1789 IDs全保留、新增38、沒有移除／重複／新增skip。3c全量與後續有界修正驗證分別列示；未宣稱5d已重跑完整1827案。兩個既有PhaseC資料矩陣不符現有bundles的skip仍保留，原診斷失敗另保存；另外兩個original staging／source cases只解除skip，body與斷言未改，新固定版均通過。CGU／NTPU／NTU官方資料tree和TKU資料tree均保留。

13組SQL subset使用十個原始治理migrations／兩個原始canonical functions及兩個真PostgREST。完整38次RPC envelope、每次full audit delta、失效approvals的DB回讀、原始workflow／destination envelope重送、legacy baseline與公開不變、cap2的完整五表snapshot保存。兩個真不同PID的請求interval重疊，實際200／409且只有一份approval；勝出原始envelope重送的response完全相同，所有snapshot bytes與audit均不變。DB五表實際完整筆數9／7／5／1／1，cap2原GET只有2／9，改後全部取回並正常approve；隔離cap設定恢復、cleanup passed。每個結果都有固定source與起迄clean guards，不用service重新讀取後no-op代替原始envelope replay。

全量34-migration／Storage harness在本環境兩次真失敗：Docker `failed to register layer: no space left on device`，保留兩份原log，沒有宣稱subset代替完整runtime。各版本GitHub PR／push CI的8 jobs均約兩秒结束、steps空／artifacts0；所有原annotations明示付款失敗或spending limit阻止啟動，CI test counts為null。5d PR37916457733／push37916447785，PR merge7d46cb4f8caa07fd7a9d9a83ecd4a297c351c5d0與候選code tree相同；原run／jobs／8 annotations／artifacts／commit／tree proof完整保存。沒有偽造CI XML或調整付款設定。

此前M1 `e1c551a`的兩輪完整CI各1786P／0F／16原S、1802 IDs全部執行，與M2明確分開。純證據分支`artifacts/tku-governance-e1c551a`的payload7b1aa1a保存8原ZIP／152members／20原XML，211raw＋545readable共756ALL blobs已核對遠端；每XML實際CLI byte-identical，外置remote proof commit為`da081b9412fc2091fadcddd502a8b52c4c16c4c4`。M1通過不代替M2完整runtime／CI。

## 證據讀取

每個source的raw目錄保存原XML／log／JSON／collection／command與guards，不改寫失敗。對應`*-readable`提供逐案index、完整failure text、每RPC完整envelope與delta、SQL摘要；大JSON／log／XML以150000 byte base64切片，`reassemble.py`校驗offset／SHA並重組。`actual-cli-reassembly-proof.json`列實際CLI exit與逐byte核對，每readable檔小於500KB。補充TKU資料命令86P有獨立執行metadata；因沒有另記該補充命令的start guard，明示這項限制，不混入四種主guard結果。

`governance-precommit-diagnostics`專收未固定source的歷史診斷與失敗／重試，不能當固定SHA驗收。原source-cache診斷僅部分AST比較，完整body proof才核對全函式；兩份均保留並說明。純URL函式1062個actual／edge vectors輸出相同，4096LRU有界，不改hash政策；readiness錯誤顯示blocked／檢查失敗，完成queue不代表READY或部署许可。

共用merge surfaces：原registry／API／UI／資格與document接線外，治理修改api.py、content_governance_routes.py、workflow_review_routes.py、content_governance.py、destination_profile_review.py、governance_commands.py、storage.py、release_readiness.py、models.py invalidated approvals、source_url_policy.py有界純函式快取、static/content-review.html/js與cache literals、OpenAPI、runtime scripts、新atomic migration與migration syntax精確計數測試。各校official_data未跨校改動，未接管臺大工作目錄；之後由整合session統一審查這些共用檔案。
