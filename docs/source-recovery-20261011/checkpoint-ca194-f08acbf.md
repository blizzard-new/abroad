# 四校固定輸入隔離整合：最終驗收進行中

候選 [ca1947351467fcc726ce58ef849437c6af11358e](https://github.com/blizzard-new/abroad/commit/ca1947351467fcc726ce58ef849437c6af11358e)，tree `25e0ffa961845865dcf10b8cd2540a8a7438fe27`；[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。沒有 merge main、部署或正式 DB 寫入；Quality disabled、Render main autoDeploy及安全／帳務設定未改。

固定輸入：CCU `52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8`；NCU `a2df55b16f72455f7154d7afff44934fc8dbf99d`；NTU `c7357f974faaec8e60ef19698d4d21633c322dc8`；TKU `93cbd9dfee3af95f9ecc89cceb1ccd0e100778af`。順序中間 commits：CCU e16381c → NCU d0c84c5 → NTU 7e0c29e → TKU ca194735。

TKU Sunderland錯校圖及UAEMEX未核實署名／授權人鏈圖已從公開static與應用package原始碼移至 `sources/tku/withdrawn-campus-assets/` 研究區。全1149張應用圖片雜湊扫描無兩圖副本。262展示照片、264座標；直接URL404／六校快取切換／最終wheel實測正在跑，不能先稱全部通過。

獨立來源核對：CCU全部21欄差異，19新補欄；離線两輪145資料檔完全一致，保留先前10項體檢、可選換宿與105.40/16日修正。NCU全部26新定位名稱與原數值、兩張照片及18校中文資料變更核對，保留圖爾庫原文件／簽章與明治五個月修正；214代表點／202照片（199唯一），不代表116指定校區或當期開放。NTU全部673新增中文說明、1228原件版本／42ZIP及611引用核驗；原46校獨立接待網域生活來源缺39，全288同標準缺44，任一生活內容缺16。TKU全部320新增M3–M6中文值、108來源／387引用核對，4529pack檔、45分片、262圖片hash與拍攝期檢查通過。原文為風險抽查，不宣稱獨立全文重讀全部作者501組或全網資料。

目前 ca194735：contracts PASSED（CGU154/NTPU409/NTU288原workflow逐byte、35SQL/uv/Actions不變、OpenAPI/JS/compile）；delivery audit PASSED（NTU1373觀察與TKU全pack）；原完整suite RUNNING（原四shard、最多兩個同時執行，原assert/wait不改）。最終完整Supabase runtime、wheel fresh install、175項cold/warm 460MiB測量尚未完成，不繼承舊SHA的結果。

上版 dbc4afd6 原完整套件：2985個唯一案例，2803 passed / 43 failed / 126 setup errors / 13 skipped，0漏列；126 setup errors 的test body未執行。多數是browser crash/closed，另有discovery globe initialized屬真實assertion timeout，不一概歸因環境。原log/XML與全分母保留，不能用單項重跑或舊SHA綠燈取代。本版改為最多兩個shard同時跑以減少資源競爭。dbc4完整Supabase runtime因Storage建立ENOSPC失敗；35SQL前置通過不能算完整runtime通過。

歷史與發布限制見 [先前 checkpoint](checkpoint-dbc4-f728af8.md)、[發布計畫](RELEASE-PLAN.md)及 [原始 run index](run-index.json)。本文件是驗收中狀態，不是上線成功或發布許可。
