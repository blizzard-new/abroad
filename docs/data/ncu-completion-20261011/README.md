# 中央逐校補完查核，2026-10-11

基底 `59a20f27fcee00fb597abc79e75ec11778317422`，分支 `data/ncu-completion-20261011`。基底已含 PR6 六校記憶體修正與 PR7 臺大更新。本輪僅中央資料、照片及必要顯示適配；未部署、套正式 DB、合併 main、更動安全設定或執行 Quality CI。

**本批是可審閱的部分補完，中央全部資料尚未完成。** [116-1 簡章](https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf) 第2、6頁預定 2026/10/12 公告名額校表。10/11 [官方交換頁](https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw) 仍連115歷史表；不得將歷史校別或外校2026/27資料當116當期。214項 quota 均為 null、agreement_only；214流程 pending_review，外校截止提醒與當期文件下載閘門維持封鎖。

## 分母與可追溯檔

- 115名額表216列整理成214交換目錄項目，含院級／自費等 track，32國別標籤，並非214當期開放學校。[逐校19欄 JSON](exchange-field-inventory.json.gz)、[CSV](exchange-field-inventory.csv)、[原 main 基線](baseline-field-inventory.json.gz)、[各欄計數](field-counts.json)、[3503個未解欄位及已查 URL](unresolved-fields.json.gz)。
- [合作校頁](https://oia.ncu.edu.tw/p/412-1026-1850.php?Lang=zh-tw) 摘要329，更新2025/11/13；同頁[官方 XLS](https://oia.ncu.edu.tw/static/file/26/1026/img/274/2025Partner.xls) 有578協議列、331個原始國別＋英文名群組、42國別標籤。XLS SHA256 `23bbf7f17a404a81ca3088b1f1a0d280d7d6185c4ab6b05042df16ff8dd419d2`。
- 逐字校名去重音／空白／標點且同國別安全對應119群組／119目錄項；212群組未硬併。329／331差異待官方釐清，MOU、雙聯及研究協議不自動當交換資格。見[完整協議原列／分類](../../../sources/ncu/2026-10-11/agreement-denominator-audit.json)。

## 本批已讀內容

兩輪共33校新／補充紀錄，新增32校、補充既有Turku，人工參考紀錄74→98→106。第二輪增加 Centrale Méditerranée、EM Normandie、ISIT、Rouen、Hohenheim、Liège、Ca’ Foscari、Nord。第一輪包括 EIGSI、De Vinci、Rennes SB、Lyon3、UTBM、Aschaffenburg、HKA、DHBW Lörrach、Würzburg、Namur、UHasselt、Thomas More、ZHAW、SSE、Alicante、UEF、LAB、Turku、Upper Austria、VSB Ostrava、Pardubice、Mendel、Minho、Özyeğin、Sungshin。

見[人工欄位、版年、引用頁及未解問題](../../../sources/ncu/2026-10-11/reviewed-host-records.json)、[新來源原文與讀取紀錄](../../../sources/ncu/2026-10-11/host-web-evidence.json.gz)、[條件文件與來源 SHA 綁定](../../../sources/ncu/2026-10-11/document-conditions.json)。491次來源嘗試（473個完整 URL／472去fragment URL），427成功、64失敗；137份有人工段落閱讀紀錄，其中26份PDF全原生文字逐頁讀完。下載、抽取、段落閱讀、全文閱讀、當期批准是不同狀態。原459份Drive來源全文已讀29的舊計數保持分開。

具體防錯與補充：

- home正式語檢仍必繳，UEF host不要求語言測驗不等於home豁免；Özyeğin不收IELTS且LA录取後才交。Lyon3、De Vinci及ZHAW依school／年級／學制保留範圍，沒有regex資格判定。
- UTBM網址檔名2025/2024，但PDF内文Year2027／GuideVERSION2027，2027秋期限分EU／OutsideEU。初次五附件與到校／雙聯文件分開；過渡保險1.5／2個月矛盾保留。
- Sungshin Spring/Fall2027表內紙本截止／LOA卻寫2026，博士9／12學分、宿舍6／7月及自評／舊醫檢字樣矛盾分列；不自行改年並開提醒。
- ZHAW只有School of Engineering程序，不推全部部門；完整初次portal清單未取得，host_documents仍missing。碩士春orientationwk37／7、FCE／C1與完成學期措辭矛盾保留。
- Namur LA空白文件已讀，但頁面版本2023/24、原件Erasmus2022；財力835是2025/26。比利時政府2026/27財力1062與UHasselt校方1100 blocked account程序額分別列，非116數字／學費。
- DHBW Lörrach已公告Spring2027，Guide末頁EditionSeptember2022即使網址2024。只供學士、無宿舍，八初次附件與SummerSchool費用分開；民責「German statutory」與Schengen/studentvisa用詞仍有疑問。
- Würzburg三份教師證明／非Erasmus選課空白原件已讀，不是home正式語檢替代；programme宿舍保證有期限及押金條件。註冊LOA／付款／健保文件另階段。
- Thomas More初次完整清單仍missing；LA到校前提交另階段。交換宿舍另行申請，不套普通學生4/27–5/4期限、非先來先得或保證床位。
- 德國在台協會2026/5/1就學頁原文、交換生文件／豁免及Auslandsportal程序已存，五所德國校的簽證文件以錄取後條件步驟呈現，與host初次附件分開。未沿用官網舊工讀天數作法律判斷。
- UTAR網址改回馬來西亞UTAR，不能用西班牙RamonLlull；Ryukoku University與同網域JuniorCollege身份分開。17個錯身份／outgoing／研究中心／場地來源明列排除，原文與HTTP錯誤保留。

- 第二輪從 EM Normandie 舊網址的outgoing頁找到真正incoming頁及2026/27新附件；三／四初次附件、兩組秋期限與Dubai4500／6000AED矛盾分列。HUB錄取後兩週註冊、degree CVEC與畢業英檢不套交換。
- ISIT初次五附件已讀，2025/26資料表／43頁Guide、2024/25課表與2026/27校曆版本分開；degree C1不套exchange，補充醫保required／recommended及CPAM時點矛盾保留。課表只讀前4／25頁，不稱課程全文已審。
- Liège初次六附件接受有學生與母校名稱的校務系統非正式成績，非EU5/31只是建議；26/27冬考卻寫2026不自行改年。Liège／Gembloux／Arlon住宿分開，2023保險頁不當116法律。
- Hohenheim交換只StudentServices fee、2026/27一般費174.50不可通套；934生活預算DSW2022。宿舍7/15–12/15與專页建議6/30–1/15矛盾，whole-semester租／押金600asof2022分清；初次高中證書等六項含track條件。
- Ca’ Foscari真正Overseas四初次附件、一頁LA已讀；學生期限從通知起一月，不能硬寫5/15。70%為Erasmus范围不套Overseas，兩個6ECTS模組須同修。Guide檔名2025但封面2026/27；入境後permit kit七項另階段。
- Rouen公開頁不列完整初次附件，host_documents仍missing；LA在初次審查後、LOA前（after_application）單獨步驟，公用DownloadForms不當exchange包，degree B2與exchange強烈建議B2分開。
- Nord最低B2與graduate建議C1、母校提名英語confirmation及home正式語檢分開；Spring2026財力91014／asof2025 permit fee不當116。非Erasmus一頁LA已讀，犯罪紀錄只placement通知条件。
- FranceVisas臺灣頁及官方面試PDF保存：學生預約由CampusFrance安排，交換LOA可電子列印；政府文件錄取後條件步驟與初次host分開。舊PDF辦公地址與現行網頁不同，按當期通知辦理。

## 參考內容缺漏前後，分母214

下表只計沒有已核對內容的 `missing`；`needs_confirmation` 是有參考內容但當期仍需確認，不能拿它當完整116批准。home文件與校內截止均214項available；所有host當期完整批准仍0。

| 欄位 | main 缺內容 | 本批缺內容 |
| --- | ---: | ---: |
| 城市／校區 | 160 | 136 |
| 交通 | 161 | 146 |
| host初次文件 | 140 | 116 |
| host截止 | 145 | 120 |
| 交換期間 | 10 | 10 |
| 課程 | 143 | 112 |
| 學費／其他校費 | 153 | 137 |
| 生活費 | 118 | 103 |
| 住宿 | 120 | 101 |
| 保險 | 109 | 92 |
| 簽證居留 | 113 | 94 |
| 到校準備 | 146 | 120 |
| 可顯示座標 | 207 | 204 |
| 已核對且具可用授權照片 | 214 | 89 |

## 真實校園照片與共享顯示修正分開

125張校園JPEG，已逐張看畫面，保留原作者、CC授權／public-domain原聲明、拍攝日期、校名國家身份、Commons原頁、原件SHA。Commons提供的縮圖位元未再修改，未用AI圖。場景不等於116錄取校區或最新現況。見[人工媒體審查](../../../sources/ncu/2026-10-11/campus-photo-reviews.json)、[平台署名資料](../../../src/exchange_info/official_data/ncu/campus-assets.json)、[265次ROR原始回應與URL／SHA](campus-registry-original-responses.json.gz)。

EDHEC共享舊圖實際是404插畫，已看原件並留[拒用證據](../../../sources/ncu/2026-10-11/edhec-legacy-image-rejection.json)；NCU改用實際校景與CC BY-SA4.0原件，共享舊manifest未改。Nanyang、Dalian、Jilin、Southeast、Nanjing、Zhejiang、HUST七筆與既有共享身份重新核對並新抓Commons署名原圖，未重用無授權裁圖。

新4個官方具名校區座標＋main既有7筆（EdUHK重疊1）＝本分支可見10；31照片GPS候選仍needs_review且公開API不輸出座標。照片125不表示125校區位置已核准。

共同整合PR8固定head `9927ec1d8765a9772671bbaa68e7f920995f1258` 的NCU40點／51舊圖是matching修正。本批125有授權圖與其中42重疊；舊51僅24筆原有署名授權，該24均已覆蓋。新座標另增加3，與PR8合併後預計43；**43是讀取PR8 index的離線比較，尚未以整合分支browser實測**。詳見[逐筆比較](../../../sources/ncu/2026-10-11/common-visual-coverage-comparison.json)。

## 無法取得與仍須續查

- 真正官方預定尚未公告：116校別／名額10/12；Sungshin2027秋英文課明列學期前一月才提供。
- 真正提名後通知：Özyeğin、ZHAW、Thomas More、Rouen公開頁明說申請入口／文件寄給獲提名學生；個別接收通知／房源契約尚無。這不代表所有缺欄都登入限定。
- 64失敗嘗試：34×404、10無response、10×503、6×403、2×412、1×520、1×502。UTAR incoming503未當登入限制；Thomas More舊ImportantDeadlines連結404但另正常頁期限已查。具體URL、結果與已排除來源逐校列於inventory及sourcepack。
- 354次嘗試未作段落閱讀紀錄：包括64失敗及未讀成功候選；扣除錯配來源，目前274次成功候選仍須人工續查，部分只是generic導覽／首頁，不能說都是incoming資料。這是尚未完成的公開補查工作，不是官方未公告。
- Nord UDI公開頁本次HTTP403已保存，非官方未公告；Studentinord公開JS頁在HTTP200及browser渲染後仍僅campus入口標題，詳細房型／deadline未取得，不擅稱登入限制。
- 照片缺89項；座標缺204項。錯校區／歷史照片、自訂授權未讀或HTTP失败拒用，不代用城市中心、研究中心或juniorcollege。

## 本機驗證與合併位置

檢查使用隔離runtime目錄、unset Supabase環境，只跑本機，無CI／部署。第二輪NCU／共用套件412通過（含21項completion資料／API）、六校memory4通過；新增八校browser8通過；第二輪CGU／NTPU／NTU資料／API回歸103通過、4既有skip。首輪六browser及248通過／4既有skip另記。完整驗證結果記錄在本目錄的validation.json；OpenAPI以`export_openapi.py --check`核對，models/API schema未改。browser以390／1280檢查實際文件、矛盾、生活費、照片載入／授權及無JS錯誤，不只校數。

共享合併位置：`api.py` 的中央照片／coverage／校區適配；`school_content.py`中央guide photo；`static/app.js`中央sidecar、署名／排除來源及防重複照片；`index.html`的app與community-reader成對cache version。**保留PR8的VisualRecordIndex和有限雙語／國別匹配**，將中央sidecar適配接在其上；本輪未改`school_identity.py`、`university_locations.py`或地球renderer，勿用本分支旧base覆盖共同修正。其他五校資料無變動。整合後座標測試須按實際43及新增來源核對，不能把本base10當整合期待。

離線重建：`PYTHONPATH=src:. python scripts/build_ncu_catalog.py`；19欄盤點：`python scripts/audit_ncu_completion.py --output /tmp/ncu-inventory.json`。輸入皆在repo，照片複製前重驗原件SHA及明示授權，未知值不升格當期。

最後複驗 [中央官方頁](home-final-recheck.json) 2026/10/11 10:56 UTC仍只連115校表；main遠端仍59a20f27。第二輪公開補查加入64次嘗試、8校，不把第一次推送当結案。
