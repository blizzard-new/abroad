淡江全量名錄與交換計畫資料（2026-10-11）

分支 `data/tku-completeness-20261011`，基準 `59a20f27fcee00fb597abc79e75ec11778317422`。使用獨立 worktree，沒有修改臺大或其他校別資料，也沒有合併 main、部署、修改憑證或權限。Web quality 最後一次成功查詢為 disabled_manually；本次測試在本機執行。

官方[姊妹校總覽](https://sister.tku.edu.tw/schools.asp)共有286筆，與保留的交換計畫機構聯集為287校。上海交通大學存在舊甄選資料、未匹配總覽，保留來源矛盾，沒有推定協議終止。學校不因出現在姊妹名錄就取得本期名額。

原128筆計畫全部保留，新增2027–2028日本第一梯25筆、歷史50名額，原文19頁PDF已開啟並核對p.13–14表格。第一梯大二資格與第二梯大三資格分開；校內學生期限、申請修改期限分開。第一梯公告22353後續重開HTTP503，系所送國際處期限不列已核實。最新第二梯四校、七名額的母校申請2026/9/30中午已截止，新增可申請數為零。

資料及證據：

- `partner_census.jsonl`：286筆姊妹名錄原始機構；每筆保留名錄、detail、官方入口、地址、查核時間與來源快照。
- `full_census_baseline.json`：補查前固定287校／128計畫基準。
- `earlier_round_programmes.jsonl`：25筆已結束第一梯；不混入本期文件或名額。
- `partner_enrichment.jsonl`：287校來源索引，124校有2031段官方原文參考；一般來源期間、淡江提名、學制、院系及校區對應未核實時保留reference_only。原文索引不是語義及當期審核全部通過。
- `curated_partner_facts.json`：明治AY2027九頁簡章實讀；母校先提名、春秋期限、分院系及新舊TOEFL量尺、文件、校區、宿舍、費用與保險。明治不在最新淡江第二梯，不能因此新增校內名額。五份指定模板HTTP503，附件內容及可開啟性未核實。官方明示2027課程尚未定案、2027/3下旬才定案，與其他來源「尚未核實新版」分開。
- `destination_profiles.jsonl`：287份資料列。原四校列逐位元保留；126校有部分生活資料，其他161校保留not_collected及來源缺口，沒有填入虛構生活費。
- `full_census_audit.json`及`full_census_acceptance.json`：287校逐校22類欄位，分verified_current、verified_asset、reference_only、缺值及矛盾；逐校列出查過來源、錯誤與查核日期，不以開啟首頁當整校資料完成。
- `campus_asset_manifest.json`及`campus_asset_visual_review.json`：新增12張實際校景，保留作者、授權、授權URL、拍攝期、校區、原始檔SHA256；已逐張檢視，沒有修改下載檔。另明確沿用固定基準既有立命館授權照片一張，保留原有16:9裁切說明與原檔雜湊，合計13/287。Commons與Wikidata批次HTTP429已停止，其他274校不是「沒有照片」。PR #8恢復既有立命館配對不列本次新增。
- `campus_location_manifest.json`：兩個新增核對的實體校園點；Royal Holloway官方命名Egham地標採!3d/!4d，不取@視窗；成蹊為Commons校園照片camera location、核對官方地址，不當精確校園中心。另沿用既有立命館校級代表點一個、維持representative精度，顯示合計3/287；不聲稱代表點已核實當期交換校區。其他284校不代入國家、城市、宿舍或行政辦公室。當期提名校區與實體校園座標另列。

全部新爬取、建立及驗收程式位於 `scripts/*tku*census*`、`build_tku_japanese_first_round.py`、`build_tku_curated_references.py`、`*tku*campus*`；`tku_baseline_assets.py`只明確連接固定基準立命館素材及代表點，沒有重寫共用matcher。離線重建順序為：campus assets、第一梯歷史資料、curated references、public references、census audit、census profiles、full census acceptance。原 `build_tku_catalog.py` 在有全量audit時會接續重建全量profiles，避免回退至四列。更新外部來源時沿用快照快取，明確保存真實失敗，不登入私人系統。

新增原始來源以 `capture_packs` 內五個ZIP封裝2576個原始快照／附件，`capture_pack_manifest.json`逐檔保存原始名稱、大小、SHA256與封裝位置；解壓後位元完全一致。`scripts/tku_capture_io.py`直接讀封裝，支援本機鬆散爬取快取及乾淨checkout離線重建。沒有封裝或搬動原有任何校別資料；當期原四校附件維持原位置。

GitHub連接器限制MCP请求16MiB，邏輯ZIP以9MiB以內順序片段傳送；manifest另列每片段SHA256及組合後ZIP SHA256。reader會驗證並組合於暫存檔，再讀取原附件；沒有變更PDF內容。原始完整ZIP亦保留本機。

必要共用變更供單一整合者審核：

- `api.py`：只在TKU路徑採用TKU授權校景、座標及coverage；其他校API原行為保留。
- `school_content.py`：TKU profile採自己的source-bound資產，不套別校或全球補充。
- `static/index.html`：載入TKU獨立校景模組及僅作用於淡江詳情的署名背景樣式。`static/app.js`及共用地球渲染程式未修改；TKU模組只在淡江目錄优先採用本次已核對校景並顯示作者及授權，裁切狀態以可讀中文呈現。
- `docs/api/openapi.json`：新增兩個只讀查核端點 `/tku/partner-census`及`/tku/partner-census/{institution_id}`。
- `static/regions.js`：僅加總覽新出現的台灣原拼字、巴拉圭及馬拉威地區列，不重寫學校名稱／國別匹配；跨校profile數量測試更新為1127，其他五校數量原值保持。

TKU registry、adapter、完整度、eligibility router改動在校別獨立檔案。没有新增本期資格、共用母校門檻或虛構可執行流程；reference_only／agreement_only全部不產生本期名額，最新原四校的JLPT及文件年期測試保留。

剩餘缺口仍大：全287校的當期母校資格有四校來源矛盾、其餘未核實；283校沒有核實本期名額／校內期限／本期母校文件；接待校期限284校未核實當期，表單287校仍有部分未知或矛盾；校區、費用與生活資訊依逐欄狀態列出。原四校63項缺口與18項矛盾仍保留。來源失敗為HTTP503／403／404／412及連線錯誤，沒有推定官方未公告或登入限定。

本機驗證與實際剩餘阻擋見同批 `tku-full-census-validation-20261011.json`；遠端固定SHA、draft PR與tree比對結果在交接回報。GitHub shell傳輸曾HTTP503；使用GitHub連接器Git-data提交，驗證遠端tree與本機已測tree一致。只開draft PR，不merge或deploy。
