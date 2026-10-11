# 中央中斷後續作：第一個可重建檢查點

本環境從遠端 Draft PR #11 的 `358a72e7302476ba8dd19c47c35fc398fc205a47` 續作；基底仍為 `59a20f27fcee00fb597abc79e75ec11778317422`。PR／Git遠端皆核對相同SHA。saved環境原本只有main乾淨工作樹，沒有舊任務未提交的第五輪檔案；舊任務所報134照片／47位置／32測試／7生活頁並未移入，不當作本次成果。`/workspace/.agents`為空，repo沒有AGENTS.md或SKILL.md。

本批重新取得公開來源後，照片125→146／214（145不同SHA；北海道院級／校級共用同一張札幌照片）、合作項目可顯示位置10→122／214。中央母校中壢位置另外補入，採PR8相同紀錄並重新讀取官方地址、ROR及Wikidata原件。母校不計入214。照片仍缺68項、位置仍缺92項；319筆成功公開候選仍待逐筆接續，並非外部阻礙。19欄4066格仍有3370格嚴格當期缺口；照片及一般地理資料增加，不代表任何116外校流程已核准。

所有新增位置逐項核對機構名稱、國別、ROR／官方域名、Wikidata原始P625及城市範圍；位置只標校級代表點，不用ROR城市中心或照片拍攝GPS替代。原本四個官方具名pin保留。慕尼黑應用、米尼奧、上海交大多點不任選；Monaco／Siena遷址及Hiroshima／Chuo校區差異另保留待確認。部分照片與代表點本來就屬不同校區，不能據此推定交換分配。

照片每張實際看圖，保存作者、拍攝日期或缺值理由、授權、來源頁、Commons原始回應、下載SHA及校區範圍。Manitoba、UF、Wisconsin、Niigata與Temple原extmetadata缺作者或僅寫「See below」，另讀file-description與完整image history：self宣告、唯一原始上傳者、原文作者或WTPTeam Audrey分開保存；上傳日期不冒充拍攝日期。圖片未另作內容修改。Niigata1910舊醫科校門不採用。

僅參考固定PR9 `ed7479073df36deb8fc0393e86fedb102e1cf2b7`、PR10 `0a089493e59426c61dc864db2ef49a40e92ea130`、PR13 `88bd00531d9a77fb98ba54dbfd8786cbde18db96` 的真實資產，再抓原Commons來源核對；不帶入其他母校名額或年度。西班牙Ramon Llull／馬來西亞UTAR、Florida／West Florida、越南Can Tho／英國Kent等錯配已明列拒用。

- [逐項位置與照片審閱及拒用紀錄](../../../../sources/ncu/2026-10-11/resume-visual-review.json)
- [保留精確原文及SHA的公開來源包](../../../../sources/ncu/2026-10-11/resume-visual-sourcepack.json.gz)
- [中央母校三個來源原件](../../../../sources/ncu/2026-10-11/resume-home-location-evidence.json.gz)
- [測試、指令、畫面SHA](validation.json)：54項來源／API／位置測試通過，另6項原件完整性／防錯校／記憶體測試通過；8項Chromium測試通過（七校生活照片與一個母校／122點地球）。OpenAPI檢查通過。這些是不同command，不與前四輪相加。
- [天普390px實際生活頁](browser/天普-390-life.png)、[母校及122點地球](browser/ncu-mother-and-122-points.png)、[七張照片與署名實際畫面](browser-credits-contact.jpg)

保留原四輪主資料及其檢查記錄。共用matcher、地球renderer、Quality設定未改；共享位置檔只新增與PR8完全一致的中央母校一行，整合時去重並保留PR8 matcher。未合併、部署、寫正式DB、新增憑證、擴權、付費升級或執行CI。

本檢查點尚未完成整項任務，後續照片候選仍在逐筆排除錯校、人物、徽章、地圖及缺授權內容；沒有把已下載的候選計為完成。
