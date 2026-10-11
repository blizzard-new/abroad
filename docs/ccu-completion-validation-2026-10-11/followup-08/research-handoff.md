第八批已完成第七批所列370個學校URL的範圍判讀，保留369個不同的同校原始正文與所有URL。107筆核閱完整可見內容、263筆僅抽讀開頭／末尾／指定政策段；完整可見內容也包含短索引、登入／錯誤訊息與一張校園圖，不能當作107份完整當期政策。另8筆新增成功來源閱讀，合計378筆，全部保留實際閱讀範圍。沒有把抽讀或HTTP200升格為當期核實，也沒有宣稱所有網站／子頁研究窮盡。

固定資料／程式commit：`da1c6ead286dad57ce22ec12a0ea847c1513152d`。瀏覽器定位修正commit：`f3ef6820237d5519d6bbf5ea19343b060892dfee`，只改新測試從來源頁完全等值比對為首頁比對（Oneonta條目跨頁）。`browser-repair-proof.json.gz`逐Git物件證明產品src/scripts/data/依賴/Supabase不變，全部選定單元測試及conftest blob不變；未把測試宣稱跑在另一個SHA。前次交付`258ce9bbb38081792658f9720bdb457a5344b2bb`，重新fetch的main仍為`59a20f27fcee00fb597abc79e75ec11778317422`。同一獨立分支`data/ccu-completion-20261011`與Draft PR #10。

本批接入24個接待欄位，填入14個原空值。104校×17接待欄＝1768欄：359當期核實、313歷史／一般參考、604空值、404待確認、87來源矛盾、1官方明示TBC。欄位前後狀態、原文、官方URL、PDF頁碼或HTML引文定位、適用年與查核日見`completion-eighth-public-progress.json`、`completion-eighth-field-input.json`及完整matrix。

- 北京外國語大學：完整讀2022-02-16公告，正文明示2022秋，提名4/10–5/20、申請4/10–5/31與6項文件／原件查驗只作歷史參考。未取附件正文與系統內模板，2027新版尚未核實；中正灰字不變。
- Oneonta：一般exchange/visiting與degree/transfer分開；母校提名、GPA3.0或B、語言選項、6類文件、選課／F-1最低12credits與一學期／一學年規則未標年，均待核。May15/November15不能直接生成2027確定提醒。一般新生4學期／transfer2學期住宿義務不套交換，未保床位；申請費0不等於學費0。2026/27 Spring校曆上課1/25–5/14、考試5/17–21已核；迎新總表1/21–23與月別22–23且星期未對齊，保留來源矛盾。UHC Spring/Summer 1/15–8/14七個月USD1396.28為當期保險組件，不是春季單期／住房／總預算。個人完整表須母校提名後OGE登入，僅讀公開指示，新增一個有原文依據的私有步驟。
- HWG Ludwigshafen：partner incoming正文完整讀，授課語言B2、母校完成一年與母校提名的門檻段未標年，不能由相鄰Spring2027校曆替語言證明補年度。保留既有當期校曆／期限；一般degree/fulltime保險、Mentoring與2026交通施工資訊不推交換適用。
- USJ：讀完整2026–27交通頁及其連結的一頁費率PDF。PDF自身未印年度，由交通正文2026–27段落的實際tarifas連結核關聯，不只看檔名。交換factsheet約EUR300/semester與一般路線年票／單程／10次票方案未對齊，保留雙源差異、未選價或除月。新生50%入學試／預錄付費條件與全學年連續訂閱才免Jun/Jul2027的優惠，不自動套春季交換。
- KMITL一般宿舍560間（男188／女372）與Chitkara Punjab一般醫療保險宣稱只列reference_only；沒有交換床位、保費、保额或有效期保證。Presidency OIA的outgoing免學費／獎助、Tokiwa與UWB烏克蘭難民專案、職員福祉／創業育成等不混入CCU普通incoming規定。

本批10筆新收據：8 HTTP200、2 HTTP404。Vel Tech incoming FAQ相同URL已於2026-10-08映射，本次完整重核未計新增政策，EUR150/250與其他來源金額差異保留。UWB國際處實際連出的交換／application兩個網址回404，保存URL、resolved URL、UTC、原始SHA与壓縮SHA，沒有反覆重試或猜新路徑。全量completion來源1281筆，不等於1281份已核當期政策。

目前校別工作清單沒有「可讀但尚無閱讀範圍紀錄」URL；仍有10筆shared/global來源未納入該host-reading ledger（含原申請文件與Gamma入口）。這不是10份新政策，也不代表全站／每個子頁已全文讀完。Gamma仍無全卡片公開匯出、全球協議母數null，沒有官方僅校方可取得的證據。六校七個既有個人步驟保留，加Oneonta為七校八個欄位；未登入、建立帳號、送表、聯絡學校或繞過限制。

校園資產維持101座標、100張授權照片、103網站身份。待核座標：同奈、Silesian商學院Karviná、墨西哥Uninter；照片：UEL、同奈、印度Presidency、Uninter；網站身份：啟明。無可安全核實的新來源便保留空值；DNTU頁尾與大學無關片段不採證、不開連結，不從租屋KML、viewer或其他學校猜校園GPS。歷史Anubis／503／TLS錯誤與圖授權限制維持原紀錄，並非重試成功。

409項全部CCU單元＋CGU/NTPU/shared：405 pass、4既有CGU skip、0 fail，339.605秒，實際head為資料commit。手機390／桌面1440實頁28 pass，80.438秒，實際head為瀏覽器修正commit。首跑26 pass／2 fail（定位測試錯誤）原log與JUnit保留；沒有刪case或豁免。4張截圖附證，其中Oneonta手機與USJ桌面另人工檢視。Ruff通過；首次2個import排序錯誤保留並修正。CSV沿用既有CRLF，以一次性`core.whitespace=cr-at-eol`檢查，不改全域Git設定。60個派生／輸入檔重建兩次位元組一致。

Wheel核對3700個CCU檔，SHA `3bcc30e01c04376059c99049a19a8bcc4e7d9757e6461473e6824f425e24b5d3`。原55份profile位元組前綴SHA `1375f32052bcdeaedfe696073e7ada6d40f40bdebeba0dc1e7f82353e38b78e6`保留。104身份、25國、104 CCU profile；六校合计893 profile：CGU77／NTPU206／TKU4／NTU288／NCU214。母校52公布名額＝49正數＋3不限；3空白、49灰字未開放、0明示零。115／2027春三梯次已閉窗，Fall2027新版尚未核實，不稱官方未公告。當期接收規則不改中正名額、母校資格、閉窗或灰字。

第八批只有校別資料、校別讀取／來源擷取／進度程式與測試變更，沒有新增共用runtime變更。本PR整體仍須整合者留意三個共用接點：`src/exchange_info/api.py`的CCU圖片／coverage及location data-dir；`src/exchange_info/static/index.html`的CCU component版本；`pyproject.toml`的CCU source打包規則。詳細UI在校別`ccu-partner-details.js`。本批不改registry／資格／文件共用程式或其他學校資料；先前49與89兩個workflow已核實行仍保留，其餘53行與本批全部workflow不變。

本批未重跑全平台2668測試，先前NTU截图路徑及單次Jena限制仍保留；DB runtime未驗，先前pinned Postgres layer空間阻礙交整合者，未重試其他session環境。GitHub Web quality仍disabled_manually、該分支Actions讀回0筆，故沒有宣稱CI綠燈。Deploy workflow只針對main migration push或手動觸發，未執行。本批未merge、deploy或改憑證／存取／付款／安全設定。
