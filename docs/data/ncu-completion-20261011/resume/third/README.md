# 中央續作第三批：193項授權照片、181項位置

從 `07bc44967a3cc47155ea362e973ec34a5158c7f3` 增加14項真實校景與5項新位置；合計193／214照片（190個不同SHA）、181／214合作項目位置，中央母校另計。仍缺21图、33點；317份成功公開候選待讀，3264／4066格嚴格當期缺口。任務尚未完成，待讀不是外部阻礙。

照片逐張檢視身份、國別、校區及原作者授權。新增涵蓋UMLP、BUEM、Aarhus Navitas、Douglas Coquitlam、Oswego自費、Arizona Old Main、GIST、Sookmyung、東北林業、廣西大學、Syiah Kuala、ITB Ganesha、Can Tho、HCMUTE。Oswego兩track僅共用地理／照片，資格費用不互借。UMLP由官方2025新EPE頁核對UFR SLHS歷史校區延續。新聞媒體Brawijaya照片缺作者授權、Airlangga Pixabay原授權時點不明、HCMUS作者不明、VNU International與Saigon International錯校，均未採用。

新增Centrale Marseille Château-Gombert、DHBW Lörrach、BUEM Bratislava、香港浸會及Oswego自費位置。另用日本中央大學官方Korakuen地址修正既有東京點搭配Hachioji城市的矛盾，只改NCU專用sidecar，不增加位置數；不是Tama或Myogadani，也不宣稱116接收校區已定。

EIVP新增四個官方HTML、March2026五頁課綱、June2025兩頁brochure，兩份PDF完整原生文字已讀。B1 teacher證明是交換語言，TOEIC785是工程學位畢業條件；€5,055只屬free-mover課程费。2026/3/31與5/31期限不改標116，brochure的Diploma awarded與網站不發學位文字差異保留。初次完整附件仍是提名後email通知，host_documents保持missing，宿舍不保證。

人工參考紀錄116／214；新來源652、段落閱讀245、原生PDF全文47，另2份既有圖文全讀。原459份Drive／全文29仍分開。EIVP與Rennes兩份landing已讀，成功待讀319→317；Reims雖HTTP200但空白且原有exclusion，不計成功可讀候選，也未標已讀。

- [照片決策](../../../../../sources/ncu/2026-10-11/resume-third-photo-review.json)及[精確來源包](../../../../../sources/ncu/2026-10-11/resume-third-photo-sourcepack.json.gz)
- [校區位置決策](../../../../../sources/ncu/2026-10-11/resume-third-location-review.json)及[座標／官方原文](../../../../../sources/ncu/2026-10-11/resume-third-location-sourcepack.json.gz)
- [EIVP六份原始回應及PDF bytes](../../../../../sources/ncu/2026-10-11/resume-eivp-original-responses.json.gz)
- [400項NCU／位置／記憶體測試](tests-ncu-all.txt)、[11項Chromium驗收](browser-check.txt)、[命令與畫面SHA](validation.json)
- [八校真實照片及署名](browser-credits-contact.jpg)、[母校與181位置地球](browser/ncu-mother-and-181-points.png)、[EIVP手機申請](browser/eivp-390-application.png)、[桌面生活頁](browser/eivp-1280-life.png)

第一次測試的四個失敗與browser計數失敗保留在 `*-first.txt`：181計為180、空欄被序列化省略、空白Reims原有exclusion，以及增加來源檔後需重建來源hash。修正測試假設並重新產生bundle後，完整回歸400與browser11全部通過；沒有略過失敗案例。

全部214名額仍null／agreement_only，流程pending_review；外校提醒仍封鎖。原第五輪未提交資料仍未轉入。共用matcher、Quality設定、正式DB、部署與合併均無變更。
