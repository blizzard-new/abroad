# 六校地球與照片驗收規格（2026-10-11）

基線：`59a20f27fcee00fb597abc79e75ec11778317422`（PR #7）。本輪只在獨立分支測試與建立 draft PR；不更新 main、正式資料庫、Render 或 Actions 設定。

## 分母與狀態

- 六校分別驗證 CGU、NTPU、NTU、CCU、NCU、TKU。分母使用該校公開 `/student-dashboard` 的全部 `partner_universities`；另列官方來源名冊尚未納入的差集。現有 API 筆數不等於官方全量已完成。
- 官方分母須另外區分「合作協議學校」、「申請計畫／track」與「本期可選學校」，各自附來源、年度與去重方式。機器報告沒有這些官方名冊時明列 `null / not_established`，不可用 API 列數推算。例如淡江 287 校合作目錄、128 計畫與本期開放名單是不同集合；工作者自報數量待固定 SHA 和來源核對後才能列為已驗證。
- 母校標記單列 1 個，不受合作校搜尋、國家、學制、名額狀態篩選影響。多校區要明示代表校區；不可用城市中心冒充校園。
- 合作校列表與地球共用篩選後資料。地球 GeoJSON 應逐筆等於其中 `verified` 且有限合法經緯度的集合。群聚圓點、重疊與地球背面不能當作資料點遺失。
- `pending`、`needs_review` 與未取得座標均保留在列表，地圖列出逐校原因、来源和詳情入口；不補假座標。
- 照片分開驗證校名／國家／校區身分、檔案存在與雜湊、來源頁、作者、授權依據，以及瀏覽器實際載入。舊 `status=verified` 僅代表既有素材核對，沒有授權欄位者不能算已取得再利用授權。
- 授權待複核照片不能繞過 `needs_review` 而顯示；檔案遺失／載入失敗要有可讀狀態。圖片来源與作者／授權在詳情可查。
- 名額空白、零名額、未公告、舊年參考和已截止維持原狀。照片／地點已核對不能推導本期交換規則已核實；PR #7 的 NTU 年度與 TOEFL 尺度邊界不變。

## 共用程式與校別資料的整合界面

本分支負責共用視覺身分對應、四校母校座標、缺漏呈現與驗收腳本。四校任務提供各校合作名冊、合作校座標與照片；取得固定 SHA 後逐筆整合共用 JSONL/JSON，保留其他學校記錄。不得用整份檔案覆蓋取代逐筆協調。合併素材更新時也須更新照片清冊及前端資源的版本參數；app.js 與 community-reader.js 保持同一版本。

視覺配對先用既有校名身分鍵＋相同國家標籤的精確紀錄。僅在不存在精確紀錄時，依序核對 PDF 空白／標點／重音差異、清冊中明列的中英雙語校名；各步驟都必須只有一個候選，歧義時停止。南韓／韓國、台灣／臺灣、中國／中國大陸／大陸地區是有限的同國標籤對應；香港、澳門始終獨立。含院系／分校／校區限定的名稱不拆出泛稱大學別名。精確的 pending／needs_review、同名歧義與不同國家不被越過。此規則不修改帳號、workflow 或其他治理身分鍵，也不更動列表顯示與篩選的原始國家名稱。

各校交付應包含：固定 SHA、官方全量名冊與目前收錄差集、逐校座標來源與代表校區、照片作者及授權來源、遺漏原因、當期與歷年資料邊界、原始測試及桌面／手機畫面。資料完整度與軟體驗收結果分開回報。

## 母校位置來源

三校以官方網站確認校名／校址，ROR 官方網域＋TW 唯一身分對應 Wikidata 單一座標，查核日 2026-10-11：

| 母校 | 官方校址／校區 | 身分 | 座標來源 |
| --- | --- | --- | --- |
| 臺大（校總區） | [官方地圖](https://www.ntu.edu.tw/about/map.html) | [ROR 05bqach95](https://ror.org/05bqach95) | [Wikidata Q32746](https://www.wikidata.org/wiki/Q32746) |
| 中正（民雄） | [官方校園導覽](https://ccu-navigation.ccu.edu.tw/) | [ROR 0028v3876](https://ror.org/0028v3876) | [Wikidata Q697299](https://www.wikidata.org/wiki/Q697299) |
| 中央（中壢） | [官方校園地圖](https://www.ncu.edu.tw/p/412-1000-105.php?Lang=zh-tw) | [ROR 00944ve71](https://ror.org/00944ve71) | [Wikidata Q714891](https://www.wikidata.org/wiki/Q714891) |
| 淡江（淡水代表校區） | [官方四校區](https://about.tku.edu.tw/campus.html)、[交通地圖](https://classic.tku.edu.tw/road.asp) | [ROR 04tft4718](https://ror.org/04tft4718) | [Wikidata Q5952880](https://www.wikidata.org/wiki/Q5952880) |

淡江不能自動採第一組座標：Wikidata 有三個實體校區。人工依官方淡水校區「新北市淡水區英專路151號」及交通圖核對，採 25°10′20″N、121°26′40″E 作母校代表點；臺北與蘭陽校區不混入。自動查詢保留 pending 的結果亦保留在原始證據中。

## 軟體驗收

逐校檢查桌面與手機：選校、母校標記、所有可用合作點、資料缺口、搜尋／國家／名額篩選集合一致、地圖及列表進詳情、圖片載入及來源、返回與切校。保留 CGU/NTPU/NTU workflow parity、六校帳號與導覽、verified-email 跨校隔離，以及 NTU reference 年度測試。

記憶體測量僅在隔離本機執行，使用正式相同單 worker 與 512 MiB 預算。正式站只做單一訪客的必要低頻觀察；不以 mergeable、測試綠燈或舊站存活推導本候選已上線。本輪預期沒有 migration，DB／部署狀態不變；未取得四校固定 SHA 時不得聲稱整合完成。

機器資料稽核：`PYTHONPATH=src python scripts/audit_visual_coverage.py --base-url http://127.0.0.1:8767 --output output/visual-coverage`。或以可重複的 `--snapshot-dir` 讀取 `*-dashboard.json`、`universities.json`／瀏覽器 `observations.json`。輸出含逐校缺口及來源，不會觸發爬蟲或寫入伺服器。

真實六校瀏覽器測試：`pytest tests/e2e/test_six_school_visual_coverage.py`；可用 `VISUAL_EVIDENCE_DIR` 指定截圖位置、`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` 指定已安裝的 Chromium。雲端首次用 headless-shell 觀察在重建多個 WebGL 地球時卡住，改用完整 Chromium 後六校測試通過；原始工具失敗和重跑結果都保留。
