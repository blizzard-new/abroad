# 第十五續作：固定223候選查核與生活欄位補充

此批接續遠端 `13a4afdc0e99cd5f9b4c66bca5bc426d68bdfd4b`，完成使用者指定的223筆有限候選之查核分類及必要公開轉址／價表查核。同一Draft PR11；整個中央資料仍是部分補完，不能解讀為所有當期交換資料完成。

223筆中205筆實讀正文全文或明示相關段落；18筆原始回應沒有可用正文，其中HM一筆循literal公開轉址讀到首頁，其餘17筆仍缺正文。逐笔原ID、URL、SHA、擷取／閱讀日、年度、讀取範圍與理由見 [reading-ledger.json](reading-ledger.json)。沒有把空殼、檔名、HTTP200、課程索引或HTML選讀算成PDF全文／當期核准。舊partial-reading-ledger只保留中途182筆檢查點，已明示由新ledger取代。

新增5個必要查核來源（4個有正文閱讀、Tongji轉址仍SPA），另封存24個原始回應及receipt在 `sources/ncu/2026-10-11/resume-fifteenth-original-responses.json.gz`。累計785來源紀錄、675閱讀紀錄；110筆無正文閱讀紀錄分成75個非200／無回應、16個先前已排除的錯範圍候選、19個本批原空殼及Tongji轉址。這些分類見 [all-source-unread-classification.json](all-source-unread-classification.json)，不把全部110筆稱為外部阻礙。

7校11欄變更、6個原缺值補成具來源的參考內容：

- 米尼奧：交換雙人宿舍、有限床位與整期契約、首尾月預付、2026/27房型月租€165／170等。交換頁整月計費與SASUM不足15天半月／日計的差異並列；不保證短住折價或2027/28房價。迎新「強烈建議」保留。
- 上奧地利：自行找房、宿舍未標年€300／月起且不含餐食，四城市不可任意跨校區修課。
- 北亞利桑那：指定日期免費接機、須航班確認；Phoenix交通與約USD20只作未標年參考，不承諾116服務。
- VSB：明示2026迎新舊日程，Student Mode不適用交換等方案，沒有據此建立個人簽證清單。
- LAB：2026/27暫定日期依錄取信；領域、校區與混合授課例外、非Erasmus學習協議、課程系統技術問題。
- 符茲堡：正式交換成績單需申請，學系／醫學院及BIP例外；自行下載WueStudy不是正式ToR。
- 佛羅里達：只補2026/27 Weaver兩房型單學期USD4,161／3,929，與舊價分開，不保證床位。

既有Sungshin2027附件、Oswego2027/28校曆、Donghua三原件、EM Normandie26/27指南、Özyeğin、Ca’Foscari、NTU等資料包逐欄對帳後保留較精確紀錄。NUIST候選實為南京大學，標記排除且不替換已核NUIST校址；HKBU2027/28 Apply Now為HKBU出國方向。ZHAW學位申請費／窗口、EIGSI舊社保費、單科B1先備均不冒用為中央交換通則。[完整前後值與來源](field-reconciliation.json)。

最終3項聚焦、459項NCU／位置／文件目錄回歸、12項Chromium（390／1440）通過。14張最終截圖全部實際打開檢查，存於browser-final並逐張列SHA；原1399张受版本控制PNG全部原SHA，15個bundle重建byte一致。最初6項只檢查來源指南的browser斷言雖過，實際NAU卡片仍顯示翻譯未完成；已修正本批欄位中文、加強直接卡片斷言再跑12項。共用翻譯判斷與matcher未改；其他既有卡片仍可能翻譯待補，不宣稱所有生活卡完成。第一次回歸命令含兩個不存在檔名，零測試執行，修正命令後兩輪完整測試皆過；失敗命令log保留。[驗證](validation.json)。未跑全專案非NCU測試、跨四母校整合PR8驗收或正式DB／部署。

代表位置214/214、授權照片202/214（199不同SHA）、母校另計；本批沒有新增照片或位置，12項缺圖另列remaining-photos。人工host125/214、214項116名額未知、當期完整核實0、嚴格當期缺格3222/4066。75份原生全文PDF與24份全文視讀PDF計數不變，其中1份視讀PDF無原生文字。已選讀的EM Normandie課表剩餘47頁、仁荷23頁課表、CUK1351列等長文件仍非完整核實，屬後續公開研究工作，不列外部阻礙；本有限清單未重新展開所有舊部分文件。

母校最後實查時間：2026-10-12T03:59:16.008794+08:00。仍只觀察到115校別表與116簡章，兩份bytes與前次一致；不推論以後不會發布。214名額及提醒封鎖維持，[實查與原始回應](home-publication-recheck.json)。

公開來源可用性限制另存source-browser-attempts：UEF401、GoogleDrive擁有者禁下載、CityU/VNU-HCM安全頁、USeoulSSO與若干SPA空殼。Chromium遠端HTTPS另遇ERR_CERT_AUTHORITY_INVALID；正常驗證TLS的requests與本地app Chromium可用，沒有TLS繞過、登入或擴權。原中斷未提交第五輪檔案未轉移，所有增量仍由可取得檢查點重建。

無force push、另開PR、merge、部署、正式DB、Quality、安全、憑證或付費變更。整合時保留PR8 `9927ec1d8765a9772671bbaa68e7f920995f1258` 共用匹配；NCU位置hold優先修正 `d29daa6ed49fa51e689d03cb9da21055feaa3e14` 只採一次。
