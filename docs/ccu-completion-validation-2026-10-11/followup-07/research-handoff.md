第七批已把37個優先URL逐項判讀（36個不同原始正文），另追31個公開入口。新增61筆有範圍的閱讀紀錄，含索引／外殼及語意相同的入口，不是61份當期政策。40個先前未記錄閱讀的校別URL已處理，剩370個URL／369個不同原始正文。公開研究仍繼續，未把未讀清單當外部限制或終止條件。

固定研究及測試commit：`2555a082963ca396dbb541bf36eb03d5f0dc0706`。前次交付：`6bd8c3c2d964b8134968b28a204ee24e8f949997`。重新fetch的main仍為`59a20f27fcee00fb597abc79e75ec11778317422`。僅本工作目錄及獨立分支，保留同Draft PR #10。

本批接入32個欄位（30接待欄、2個網站身份scope），填入20個原空缺；完整逐欄前後狀態、來源ID、年度與原文依據在`completion-seventh-public-progress.json`及review matrix。接待1768欄目前357當期核實、314歷史參考、618空值、393待確認、85來源矛盾、1官方TBC。HTTP200不升格當期政策。

- 賽普勒斯：實讀2026/27正文、2頁factsheet、1頁calendar、2頁language、2頁insurance、8頁entry及非Erasmus DOCX。Spring提名10/1、文件10/20、住房11/15、開課2027/1/18及考試核頁碼；B2母校證明接受範圍的公開頁/PDF矛盾保留，Erasmus與雙邊、CS-only GPA6.5/10、跨School與中正舊跨系限制分開。未開放身份不變，簽證附件不當最新個案法律結論。
- UCSI：incoming頁只有2024–25表，資格／語言／日期等7欄明確歷史參考；未核2027。KL D/E住宿另列一般待確認，不套Sarawak／Springhill，不保房位；現行partner清單未列中正不推協議失效。
- CSUN：2026/27一般住宿候補及全年Park費表已讀。總USD11351/9153/8812非春單期報價，分期非月租、後兩另meal plan，Family資格與費率分開。SAC自費方案／學費與春個人合約未核。
- SDU：完整住宿頁补五城市（含Vejle）及中央頁11/1 23:59CET；一般6日與部分城市7日回覆、14日cooling、個人付款不同，未標年保持待確認、不產生2027定時提醒。
- Sungshin：公告長URL與PDFp3短鏈實為同一Spring2027提名form ID，公開第一頁與指示已讀、未按Next或提交。PDFp1另一短鏈是Fall2026、checklist短鏈是closed Spring2026、公告folder只列Spring2026舊材料；不由列表冒稱每PDF正文已讀。9項當期學生文件／新自填Medical Assessment不變；TIS私有學生表与母校coordinator公開提名分開。XLSX V1舊到件年等殘餘矛盾保留。
- LETI：第一方RAfU頁校名與University web site anchor核主站身份，網站數102→103；主站本次503另記，不稱正文成功。非洲預科課程不套CCU交換。

SeoulTech／忠南本校outbound、KIIT會議、Jena單場活動、Zaragoza Erasmus Charter已讀但不補CCU接待申請。西南兩URL同一無年OLE體檢DOC；完整空白模板解析正文与SHA已保存，未列當期全體必繳。

校園資產目前101座標、100張有授權照片、103網站身份。剩座標：同奈／Karviná商學院／墨西哥Uninter；照片：UEL／同奈／印度Presidency／墨西哥Uninter；網站：啟明。新啟明calendar/map/Adams路徑503、Karviná正確opf.slu.cz為Anubis未繞過；opakarvina.cz是另一中學而排除。DNTU新360 bus入口是JS容器，無新增marker與圖授權，不從viewer或租屋點猜校園GPS。先前租屋KML地主姓名／電話沒有刊登。

Gamma本批正常HTTPS `/docs`為空pageProps外殼、無全卡片正文或公開export鏈；正常TLS Chromium確切錯誤`ERR_CERT_AUTHORITY_INVALID`，未忽略憑證或使用私帳號。仍無官方「僅校方可取得」證據，完整公開匯出本次無法取得、協議總母數null。若由用戶提供最小資料，可用國際處「全球姊妹校」現行全卡片PDF匯出與更新日期，或同內容CSV/XLSX；這是需求描述而非猜官方檔名。六校七個私有欄位仍只限制各實際個人表步驟，公開政策可研究。

本批31新請求：24 HTTP200（含1Anubis及索引外殼，不都算正文成功）、2 HTTP502、5 HTTP503。URL、正常TLS、查核時刻、原始SHA與壓縮儲存SHA均保留。APT取得antiword失敗後改用官方Debian包私下解壓並成功解析，未系統安裝或改依賴；工具來源receipt附在證據。初期UCSI原文guard因使用假定措辭失敗，已改實際正文短句；沒有改門檻／年度。

本批沒有共用registry/API/UI/資格/文件程式新增變更；發布流程只更新49與89兩行，另53行位元組保留。整個PR需整合者注意的共用接點是`api.py`中CCU圖片／coverage及location data-dir傳入、`static/index.html`中CCU component版本、`pyproject.toml`中CCU completion source打包规则；CCU詳細UI實作仍在校別`ccu-partner-details.js`。原55 profile位元組前綴SHA為`1375f32052bcdeaedfe696073e7ada6d40f40bdebeba0dc1e7f82353e38b78e6`，其他校資料／名額／母校資格與閉窗不變。嚴格來源驗證器blob`28daf5e1f982a19a1056cb884d1f838e70f49867`未放寬。

398項全部CCU unit＋CGU/NTPU/shared：394 pass、4既有CGU skip、0 fail，315.635秒。390/1440實頁24 pass，71.937秒；6張真實頁面截圖附證，其中p84手機與p115桌面另人工檢視。前置focused兩個測試設定錯誤（句子／不存在API路徑）保留原失敗，修正後14 pass；沒有刪case或豁免。29個派生檔重建兩次位元組一致。Wheel核對3641個CCU檔，SHA`2217d53041dcd68e0610bbbc66200b0d21916700861da25494882e400169a001`。

104身份、25國、104 CCU profile；六校合计893 profile：CGU77/NTPU206/TKU4/NTU288/NCU214不退。母校52公布名額＝49正數＋3不限、3空白、49灰字未開放、0明示零；115／2027春三梯次已閉窗，Fall2027新版尚未核實，不稱官方未公告。

未重跑全平台2668，先前NTU截图路徑及單次Jena限制仍保留。Docker pinned Postgres layer空間阻礙已交整合者，本批未重試或驗DB runtime；Quality workflow仍disabled，未啟用、merge或deploy，沒有修改憑證、權限、付款／安全設定。
