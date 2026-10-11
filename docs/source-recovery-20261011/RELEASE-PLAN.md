# 隔離整合候選發布與回滾計畫

本計畫不執行發布。本階段沒有 merge main、production DB 寫入或部署，沒有改 Quality、Render autoDeploy、branch protection、憑證或付費。main 於 2026-10-11 11:28 UTC 再查仍為 `59a20f27fcee00fb597abc79e75ec11778317422`，Quality workflow 374368612 仍 `disabled_manually`。Render `srv-db26bgjbc2fs73fdsmhg` 依父對話已核實的設定，`branch=main, autoDeploy=yes, trigger=commit`，更新 main 即可能發布；本計畫未更動設定。

## 固定輸入及合併依賴

| 輸入 | 固定 SHA | 處理 |
|---|---|---|
| main | 59a20f27fcee00fb597abc79e75ec11778317422 | 起點；不假定等於目前 production deploy SHA |
| #8 六校地球／照片識別 | 9927ec1d8765a9772671bbaa68e7f920995f1258 | 整合基底，保留保守精確／唯一別名識別與待審優先 |
| CGU來源恢復 | 985224fd01748a6c591fc183362847d6d7d21c35 | 初次提交；後續補上其他校省略空 source 欄位 |
| #9 NTU 第二批 | b6607a0ee5d01e23878950d556f9540aa25aeaf2 | 取代4566f7f；完整正文包交付已獨立核對 |
| #10 CCU | cf4d86f22d89ee698315d46177daf00b49dd8706 | 含c18aebf批次及測試增量 |
| #11 NCU 第三批 | 06bfdfa15e9f773533d3f82e1a136faa99f68104 | 含第二輪8校及第三輪3機構5track；277成功候選仍待人工查 |
| #13 TKU 第一批 | f4819dab2db22507ad8978800aeabbcb9f598294 | 287機構／153含歷史計畫；尚未全校資料完成 |
| 本輪應用程式候選 | 0d3d671ef92344970e4de1797a81b050235eecbd | Draft PR12；驗收紀錄均記錄固定開始／結束SHA |

依賴圖：`main → #8 → CGU共用來源恢復 → #9/#10/#11/#13固定批次 → 共用hunk協調 → 最終驗收 → 父對話發布決定`。

這是實際整合依賴，不能只依Git的mergeable或無衝突判定：api.py照片scope／coverage／三個座標呼叫點、school_content.py、共用位置檔、index.html資產版本／載入順序、app.js精確識別與授權文字、OpenAPI、兩個跨校分母測試均逐段保留。CGU供應器與四校adapter並存；CCU／NCU／TKU操作員pending、needs_review、verified及非法座標皆優先於資料sidecar。NCU讀JSONL改串流，保持逐列驗證與結果順序。TKU新增capture_packs分片的package-data規則。

## Migration 與相容性

相對 main59，各固定 #8/#9/#10/#11/#13 及本輪CGU修復的 migration 新增／修改均為 **0**。既有35份migration只做本地語法檢查，沒有執行SQL，也沒有因Actions帳務受阻而假定正式DB同步。

本次來源快照存在套件／開發data_dir中，沒有DBschema需求；新API `catalogue_source` 為可選欄位，其他五校省略。舊前端可忽略新欄，舊程式可忽略source_cache。照片與原文皆增加本地資產；OpenAPI新TKU查核端點為additive。原CGU154／NTPU409／NTU288 workflow保留原f6ad1b8位元組。

## 父對話可採用的發布順序

1. 保留Draft。0d3d671e已完成同一固定資料與完整162步負載：修正前556.27MiB失敗，修正後暖454.56MiB／冷458.49MiB通過460MiB門檻，最低53.51MiB餘裕。每個run的原始腳本、採樣、SHA及失敗均保留；沒有提高付費方案、縮短流程或恢復Quality。最後功能驗收以證據README的實際結果為準。資料研究增量須另提供固定SHA再整合，不移動本次證據輸入。
2. 功能／來源／套件驗收完成後，由父對話決定未完成資料是否符合本輪發布範圍。未取得、一般／歷年參考、官方明示尚未公告與明示零名額繼續分開，不將來源取回視為本期已核實。
3. 正式變更前，以已授權只讀管道核對目前production實際deploy SHA、DB已套用migration、備份可用性；無可用讀取權限時回報精確缺項，不新增憑證。此次新增migration=0，若production已含main所需schema則不需DB更新；若發現缺少既有必要migration，停止程式發布並交父對話協調具體DB操作。
4. 若後續確實新增schema需求，先審核可前後相容的additive migration與備份／回復點，再於父對話另行批准的production步驟執行DB變更並驗證，最後才更新main。Actions受阻時不得把push視作DB部署成功；不得擅改workflow或autoDeploy。
5. 建議父對話使用包含全部已驗收hunk的單一最終候選，避免依序更新main讓Render部署未验收的中間狀態。每次main更新都需當成實際發布動作；本階段僅正常push隔離分支和證據。
6. 發布後必須核對Render真實部署完成及實際SHA、health、六校選擇／帳號保存、校別切換、手機桌面、文件條件、verified-email跨校論壇、治理審核／發布／回滾。不以PR合併、task完成、mergeable或CI綠燈代替這些確認。

## 可回滾方案

- 記錄發布前實際已部署的穩定SHA及設定。只有父對話授權正式操作後，才可透過正常回復commit或明確Render rollback還原該版本；不強推main、不更改branch protection或autoDeploy。
- 本次無DB migration，回滾程式不需要DB down migration、不刪除正式資料。若另行執行additive migration，舊程式仍可運作；保留schema與資料，另案處理確有必要的資料修復。
- CGU快照只有完整雙來源成功才原子替換；任一HTTP／解析／空內容／寫入失敗保留前一完整版本。快照讀取或回滾不把新舊年度混為本期資料；沒有任何有效快照時明確回報暫不可用。退回旧程式會失去此來源恢復保護，應列入回滾影響。
- 正式驗證失敗立即回父對話，不在隔離任務中自行改正式DB、部署設定或帳務。

## 本階段明確未執行

main merge、production deployment、production DB讀寫驗收（本階段僅已提供部署設定的只讀資訊）、wheel的全新隔離安裝／正式容器啟動、全部E2E測試檔。範圍內完整非E2E及擴充重點E2E原始結果另列，重疊run不相加冒充唯一案例總數。

## 套件交付

實體wheel已由宣告的setuptools.build_meta建置。首次一般暫存複製仍ENOSPC而失敗，已只移除本任務暫存；重跑以os.link暫存（不變更package discovery、package-data、wheel組裝）成功。5,796份套件內容逐一與固定來源SHA256相同，全部宣告資產及TKU13包分片均存在，zip CRC通過。wheel約779MB，保存於執行環境，未推Git或發布套件；SHA256為`b92a6f40c4db701b8c7647df3c69d994ae8899e464ab1a670b8d9b037aa6f9b5`。原始建置失敗、重跑腳本及完整檔案清單在證據分支。
