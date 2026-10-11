# 第十二續作：待讀核銷及舊原件再驗證

基於`a2df55b16f72455f7154d7afff44934fc8dbf99d`，同一Draft PR11。九筆候選實際擷取文字已讀（Centrale Méditerranée、IPSA、Devinci、UTBM、千葉二頁、NUFS入口二份同SHA、九工大交換入口）。閱讀紀錄374→383，成功待讀257→248；來源722與人工host120不變，原生PDF全文75＋圖文全文10不變。本批沒有增加校數／獨立規則／照片／座標。214代表位置、202圖／199不同SHA，中央母校另計；12缺圖、3222／4066當期嚴格缺格仍在。

## 讀取範圍

- Centrale舊exchange URL實際首頁，千葉二頁是Global／International Exchange導覽，九工大exchange頁Under Construction；不把一般學位、出國、faculty或研究交換當incoming規則。其餘已讀來源仍按頁面年度／track。
- IPSA頁五類文件、推薦B2与英測／母校信分流已讀；€4,500明列nonpartner Study Abroad，不當中央交換費用。Devinci的EHIC只EU、成績只4–5年級、語言表可後補；UTBM Eiffel2026截止不當交換截止。這些具體規則已有更早人工包，保留原有內容。
- 名古屋外大10頁與4個直接PDF重新下載，**14個SHA與較早`host-nufs-next3-*`來源完全相同**。五個ZIP表格member另逐件算SHA，容器與既有`host-nufs-next3-package`SHA相同。這些是原件再驗證，不另加19個來源或7份全文數。
- 三頁checklist、十二頁英文instructions、四頁獎學金規程、兩頁medical、英日release各一頁、獎學金表一頁，合計七個PDF共24頁原生文字及逐張圖像已讀。英文操作畫面只有公開教材，沒有註冊／登入／填資料／送申請。日文十二頁instructions此輪未重新閱讀，較早已讀紀錄保留；不冒稱本輪讀完。
- 推薦XLSX單一Sheet1原生欄位／全部sharedStrings已讀；當前PATH沒有LibreOffice，這份XLSX不宣稱轉PDF或視讀。先前HKA的已保存轉換仍是當時產物，沒有套作此次XLSX證據。

## 保留較完整資料

NUFS原有13項條件文件、8個外校階段及2026春秋課綱保留；包含財力替代件、條件醫療／JLPT／出入境／JPETS，不能以本輪清單11類覆寫成全員必繳。原先已讀宿舍手冊及課綱也不因本輪僅讀入口而降成未知。IPSA既有5件與2026/27校區差異、課程30ECTS參考保留。所有年度、先修、例外、無名額與提醒封鎖維持。初始未提交草案曾覆蓋兩個較早base記錄；發現雙層來源後已在提交前移除，沒有發布此退步。

`reading-manifest.json`記錄九筆核銷、19個capture與既有來源對應、ZIP／member SHA和24頁圖像；`resume-twelfth-original-responses.json.gz`的capture_id不是新增production source_id。原始資料來源及其年度仍在原包。學校正式資料不以本輪同SHA重取日期冒充新年度。

實際回歸／Chromium結果見validation.json。390與1440的原始NUFS完整資料、13件與生活頁測試通過後逐張檢查12PNG；兩張overview是全頁縮圖，用作整體排版證據，條件文字由DOM及局部截圖核對，沒有聲稱縮圖每字都可閱讀。無正式DB／部署／Quality／安全／matcher／renderer變更。

仍有248成功候選待讀與12授權圖未核實，持續查證；待讀不是外部阻礙。原中斷第五輪未提交檔案沒有轉移。最近母校公告實查仍為前批臺灣10/12 01:37（115表），本批未新增公告查核。
