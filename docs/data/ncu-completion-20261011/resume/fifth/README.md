# 中斷後第五續作：200授權校景、188合作位置

基於 `d29daa6ed49fa51e689d03cb9da21055feaa3e14` 同一Draft PR11續作。本批193→200／214照片（190→197不同SHA），186→188合作位置；中央母校另計。還缺14圖、26點，3250／4066格嚴格當期缺口。host人工118／214、665來源／261段落／51原生PDF全文、3份圖文全文與314成功候選未讀計數不變，照片／地理資料不冒充host條件已讀。

## 七張真實照片

Reims Moulin de la Housse（Gérald Garitan／CC BY-SA4.0）、Aschaffenburg（Aschaffenburczyk／CC BY-SA3.0）、DHBW Lörrach（Wladyslaw Sojka／FAL）、韓國天主教Songeui醫學校區（poly／CC0）、新加坡Nanyang Polytechnic庭園（User:Sengkang／Copyrighted free use）、Brawijaya Malang校門（Lorrainevyu／CC BY4.0）、Airlangga人文學院CampusB（antonov0002／CC BY3.0）。每張原始下載圖已看、SHA不变，本地保留原件／Commons縮圖位元，照片頁、作者、版權聲明與上傳歷史、拍攝或原始上傳日期及具名校區分開記錄。

- **FAL不是CC。** DHBW原作者Own work上傳，原頁要求全名Wladyslaw Sojka及連到www.sojka.photo。完整FAL1.3原文、原檔案頁、上傳history均保留SHA；介面顯示全名、FAL條款、攝影者網站及原件來源連結。原頁2011/9/24與上傳註解2011/9/11差異保留，不自行改成同日。
- **Copyrighted free use不是Public domain。** NYP原作者Own work與2006本人上傳註明拍攝對得上；保持這一授權名稱並鏈到該檔Licensing聲明，不把第三人公開上傳當權利授予。
- NCU資產builder新增僅這兩個明示授權類型的逐件proof校驗：原始檔頁、條款、upload history三份SHA，且綁定照片SHA和原始檔URL。缺proof／換圖／換頁／改條款／錯授權URL均拒絕。原CC及PD流程保留。
- 韓國天主教另張InternationalHub為第三人搬校方圖且無原grant，拒用；本次選poly本人CC0照片。**照片是首爾Songeui，地球代表位置另為富川Songsim**，caption與座標note均明示，不能推中央可交換醫學。
- HCMUS三張候選仍都缺作者、來源為新聞／招生頁，上傳者非原作者；不以Commons CC／CC0標籤自動採用。IDRAC政治人物、ISIT醫療影像、公車與公益活動等錯用途一律不當校景。
- Airlangga採有2016 Panoramio授權檢查紀錄的CC BY3.0原件，保留2011為上傳日期未知拍攝日；前批Pixabay授權時點疑義圖仍未採用。

見 `sources/ncu/2026-10-11/resume-fifth-photo-review.json`、`resume-fifth-photo-sourcepack.json.gz`、`resume-fifth-licenses/`，逐張review有canonical來源列，capture序號不是原116／115表列號。原始作者、授權與校區亦寫入顯示用manifest。七張都只是歷史校景參考，116實際接收校區不推定。

## 兩處具名校區位置，整合提醒

**廣島前批hold已取得新原件而解決校區身份，並非被共用fallback蓋掉。** 官方Higashi-Hiroshima交通頁原link解析到1Chome-3-2Kagamiyama，路線終點34.4022006,132.713964。已核取該具名東廣島校區；不取廣島站、URL的@視窗中心或舊共享市區34.382222,132.458056。前一份needs_review紀錄完整存於新review的previous_record；Kasumi／Higashi-Senda另址，116分配依然未知。

**韓國天主教Songsim** 官方公開campus-map程式第2行定campus1=Songsim，第24行是該校方選定校區中心37.485931,126.804622，交通頁同址43Jibong-ro,Bucheon。屬校區代表中心，不是假設城市中心；不借Wikidata首爾神學校區。

`resume-fifth-location-review.json`及`resume-fifth-location-sourcepack.json.gz`保留完整原頁／程式／原始地圖終點URL、座標推导和previous hold。**請整合者持續保留NCU明示待核優先於共用verified的程式保護**：測試以Hiroshima與Mons模擬新的scoped hold，即使共享更新verified也不外洩座標。Chuo仍是第三續作Korakuen／Bunkyo，不是Tama或Myogadani。這些代表點與中央當期交換分配是兩個狀態。

## 官方名額與驗證

最後官方狀態證據沿用前批臺灣2026/10/11 22:57：入口仍115名單＋116公告，公告第2頁預定10/12公告名額，第6頁為2027/9–2028/2、2027/9–2028/6、2028/2–6。[原文／時區／URL](../fourth/home-publication-recheck.json)。本批尚未跨臺灣10/12，未新排程。214quota仍null／agreement_only，流程pending_review，host截止提醒不開。若工作跨午夜，需同入口再實查。

418項最終NCU／來源／位置／API／記憶體回歸全部通過；8個照片授權介面案例（7項目，DHBW390及1280）＋母校及188地球，共9項Chromium通過，10個歷次案例deselected。照片實際載入、只有一張、署名／授權／作者網站／校區警語、無overflow／JS錯誤均已驗；地球188、選單189含母校。測試先抓到2個問題：API照片期待值還是193、修改asset後來源provenance未重建。已改期待200、完整重建catalog並重跑418通過；失敗log保留，不以重跑數字遮蓋。驗證範圍及截圖SHA見[validation](validation.json)。

UI只補NCU照片caption的可點條款及原作者網站，未重寫共用matcher。app／community-reader版本成對更新；其他home顯示預設邏輯保留。未merge、部署、改正式DB／Quality／安全設定、憑證或權限。

剩14圖／26點及314公開候選仍須續查，任務未完成。另23個短HTML候選已在外部工作目錄閱讀、沿官方連結取得續查原件，尚未寫入本檢查點或虛算來源已讀；後續批次須將審查紀錄與實際欄位一併保存。原中斷任務第五輪未提交檔案仍未轉移，本批是新環境可驗證重建。
