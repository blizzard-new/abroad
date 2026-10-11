# 四校固定輸入隔離整合：最終驗收進行中

候選 [7a7c7e3560527ce08ca225c0930397772a8b79aa](https://github.com/blizzard-new/abroad/commit/7a7c7e3560527ce08ca225c0930397772a8b79aa)，tree `61d4824d59c3477960ace89fbcf5f02d4ca030ce`；[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。本任務沒有 merge main、部署或正式 DB 寫入；只讀再次確認 main59a20f27、Quality374368612 disabled_manually。Render main autoDeploy 及安全／帳務設定未改。

固定輸入：CCU `52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8`；NCU `a2df55b16f72455f7154d7afff44934fc8dbf99d`；NTU `c7357f974faaec8e60ef19698d4d21633c322dc8`；TKU `93cbd9dfee3af95f9ecc89cceb1ccd0e100778af`。逐 hunk commits：CCU e16381c → NCU d0c84c5 → NTU 7e0c29e → TKU ca194735 → NCU測試截圖輸出位置7a7c7e35。全部固定輸入為候選祖先，工作樹乾淨；相對main59的migration增量0。

TKU Sunderland錯校圖及UAEMEX未核實署名／授權人鏈圖已移至 `sources/tku/withdrawn-campus-assets/` 研究區。全1149張應用圖片掃描無兩圖副本；最終wheel逐檔hash／路徑無兩圖；實際隔離安裝載入六校dashboard前後，兩個原URL皆404。保留262展示照片、264座標；研究保存不等於可公開部署。

獨立來源核對：CCU全部21欄差異，19新補欄；離線两輪145資料檔完全一致，保留先前10項體檢、可選換宿與105.40/16日修正。NCU全部26新定位名稱與原數值、兩張照片及18校中文資料變更核對，保留圖爾庫原文件／簽章與明治五個月修正；214代表點／202照片（199唯一），不代表116指定校區或當期開放。NTU全部673新增中文說明、1228原件版本／42ZIP及611引用核驗；原46校獨立接待網域生活來源缺39，全288同標準缺44，任一生活內容缺16。TKU全部320新增M3–M6中文值、108來源／387引用核對，4529pack檔、45分片、262圖片hash與拍攝期檢查通過。原文為風險抽查，不宣稱獨立全文重讀全部作者501組或全網資料。

| 7a7c7e35 驗收項目 | 原始結果 |
|---|---|
| contracts／來源交付／NCU串流完整性 | PASSED；CGU154/NTPU409/NTU288逐byte parity、35SQL／uv／Actions不變、OpenAPI／JS／compile；NTU1373觀察、TKU4529pack成員、NCU214+2177完整記錄核驗。 |
| 完整本地Supabase runtime | PASSED；35migrations、真Storage file backend、2 PostgREST、37表RLS且0 browser grants；治理17檢查／74 RPC／31 audit；6校12個unverified拒絕、40aliases；6種late failure全回滾0partial rows；cleanup PASSED。原始stdout完整保存，另有短summary。 |
| wheel與隔離安裝 | PASSED；6,955檔共1,564,025,091未壓縮bytes逐hash相符，package-data完整、CRC通過；wheel SHA256 `b3e3dfe6c560dfd02c85bb4a89a246b914ff35774d2fe7bcdd596c47a6728953`。wheel fresh target、既有受驗證dependency venv，沒有宣稱全新dependency解析。CGU官方live雙來源成功、六校API與原workflow通過，撤回圖404。 |
| 175步冷／暖記憶體 | 冷測FAILED：第8取樣（首輪TKU）峰值472.656MiB >460；餘下167取樣未執行。暖測NOTRUN。另啟完整diagnostic（僅將budget失敗延至結尾，仍需exit1），不作通過。負載、等待與460MiB門檻不變；僅TKU固定inventory期望由264圖260點調整為262圖264點，差異receipt保存。 |
| 原完整測試套件 | 此SHA NOTRUN，記憶體回歸需修復後重新固定候選再執行原4shard、最多2個同時；不得繼承舊SHA通過紀錄。 |

ca194735 的完整suite已CANCELLED：3085 collected，觀察到118個call passed，剩餘2967未完成／未執行；沒有完整pass。原因是4個新增NCU模組將截圖写入tracked docs，已保存截圖／log後還原並在7a7只修OUT輸出路徑；全部test function AST／assert／wait未改。

上一版dbc4afd6：2985 unique＝2803 passed／43 failed／126 setup errors／13 skipped，0漏列；126 setup errors的test body未執行。多數browser crash/closed，另有discovery globe initialized真實assertion timeout，不能一概歸因環境。其Storage ENOSPC失敗也保留。較早160aeacd、4a011fab的结果只屬各自SHA。

歷史見 [ca194 checkpoint](checkpoint-ca194-f08acbf.md)、[dbc4 checkpoint](checkpoint-dbc4-f728af8.md)；完整 [run index](run-index.json)、[runtime摘要](integration-final4-full-runtime-summary.json)、[wheel檔案hash](integration-final4-wheel-integrity.json)、[固定輸入與migration](final4-fixed-input-ancestry.json)、[發布／回滾計畫](RELEASE-PLAN.md)。目前不是上線成功或發布許可；最終所有門檻完成後再更新。
