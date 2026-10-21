# 查核工作交接紀錄

本檔是工作狀態，並非查核完成證明。2026-10-21 更新。

- 使用工作樹 `C:\Users\User\.codex\worktrees\university-data-verification\留學`、分支 `codex/university-data-verification-20261021`；基準 `b662dced2607bc67c3354c95b7aaad202448bea7`，目標遠端 `abroad`（blizzard-new/abroad）。原始 OneDrive 工作目錄有使用者變更，不可覆寫。
- 持續目標是逐間核對 25 所母校及全部 4,585 筆合作方案的公開資料，整理完整與缺漏，最後提出 PR。沒有任何整校或整筆合作方案宣告完成；尚未建立 PR，沒有部署或合併。
- 原始盤點已移到忽略目錄 `output/data-verification-20261021/baseline/`；不可覆蓋。`current/` 是中途版本，不能當作最新盤點。原始檔雜湊在 `baseline-manifest.json`。
- 原始共有 1,881,425 個非空欄位、250,157 個空欄位和 21,536 個候選網址。欄位包含重複的共同規則、衍生文字和媒體；連結讀取成功不代表事實驗證。
- 來源取得程式持續寫入 `source-receipts.jsonl`；快取主要在 `output/data-verification-20261021/`，後來的人工補查在其 `source-cache/`。舊快取為 `{url_id}.body.gz/.txt.gz`，新快取為 `bodies/{sha256}.gz`、`texts/{text_sha256}.gz`。使用前核對原始內容雜湊。
- 已處理部分 CGU、NTU、NCU、FJU、SCU、NTHU、NCHU、YUNTECH 母校規則；NKUST、YUNTECH、NTOU 缺期限證據時不再產生推估的精確期限或提醒。每校其他資料仍待核對。
- FJU 合作總表原匯入程式把「簽約名額」當年級、「備註／排名」當交換期間，已修正 parser 和 234 筆對應資料。這不能證明總表名額就是當期名額。新一期 1346、1347 PDF 的名額欄也明列參考用途。
- NTHU 舊 PDF URL 取得的是導覽 HTML；已找到公告連結的真正 PDF。NTHU 只可採 GPA 3.2 或排名前 50%，不可用固定百分制 78 替代。SCU 不可用平均 65 分替代排名要求；兩校 registry 殘留門檻已清除。
- NTPU、CCU、NCKU 官方 PDF 已讀取並檢查關鍵頁面圖像，期限卡修正已完成；NTNU、NCCU 兩種計畫也已讀取核心規則及文件頁，修正期限卡、資格判斷與 dashboard 共用門檻。相關本機 PDF、PNG 放在忽略的 output 目錄。
- NTPU 官方公告面試：英文組 2026/11/23、11/25，中文／日文組 11/27；申請表親簽後上傳指定 Google 表單，非申請系統。CCU 公告確有「每個志願一份研修計畫」，PDF 則提供每項約一頁指引，不能設硬性三頁上限。NCKU 不支持現有 1,000 元報名費與 09:00 開始時間；同份簡章對申請表簽章的文字不一致，需要明列待確認。
- FJU available_count 下限已改為驗證實際資格缺口；NTHU 圖片計數 175/176 原因為完全相同證據的中英文別名誤判衝突，已修正，來源或狀態不同仍拒絕合併。第4輪相關測試 143 passed，第5輪 NTNU/NCCU 修正測試 70 passed。
- 第6輪新增 2,551、第7輪新增 3,548 個欄位綁定，總數 9,425；所有 whole_record_verified 仍為 false。來源取得仍持續，數量見 review-progress.json，不是事實驗證數。
- 第6輪已同步 FJU 234 筆工作流程：紙本雙面申請表與三份 PDF（各20MB）分工、70分不可替代、A117 官方地址；SCU 191 筆流程資訊場次不再當期限，研究所是平均80分；NCKU未支持的09:00開放與下一梯推估日期已清除。88項相關測試通過。
- 第7輪 FCU GPA3.0不可平均75或排名替代；官方1151只赴2027春，161流程適用範圍限1151；下期日期待確認。NSYSU 190非日本流程的預告期限取消正式提醒，學業採班排名計分；大陸預告01/15開放，01/12公告。99 passed, 2 skipped。
- workflow_structuring 現保留明確 needs_confirmation，不因來源／年度有填自動升級；NSYSU KMUTT兩個照片來源不同，衝突保持待確認。
- 已完成39個修改Python、38個JSON、19個JSONL格式檢查、node --check及CRLF容許的diff --check。FCU其他原始複製文字仍有下一梯日期、學費補助、住宿、學期等未證實主張，尚待逐項同步。
- Python 單獨 inline 匯入時須先 `sys.path.insert(0, str(Path("src").resolve()))`，否則共用 venv 的 editable installation 會指回原始 OneDrive 工作目錄；pytest 的 pyproject pythonpath 和 census 腳本已明確使用工作樹。
- 每次變更應執行有關測試、更新 review-decisions、README 和進度 CSV。`review-decisions.jsonl` 的列數是欄位綁定數，不是不重複事實數，且所有 whole_record_verified 均為 false。
- Windows 部分既存檔案直接覆寫／truncate 會失敗；採同資料夾暫存檔加 `os.replace`，保留原始換行。檢查空白使用 `git -c core.whitespace=cr-at-eol diff --check`。
- Python 使用 `C:\Users\User\OneDrive\文件\留學\.venv\Scripts\python.exe -X utf8`。不得將快取、原始大型清單或生產資料庫加入 PR。

後續仍須核對未完成的母校規則、每筆合作關係與個別資格／名額／期限、海外校生活與課程等資訊、所有公開衍生內容及正式站差異；來源失敗應補查或明確保留無法確認，不得等同官方未公告。

- 第8輪逢甲方案：新增 `fcu_source_review.py`、官方原始快照 `sources/fcu/oiasap_programs_1151_reviewed_20261021.json`（SHA 9718ca3988d53984648aa4f1c53db0f0e6854746803f0001d7a937c3493e5f89）、`report_fcu_source_review.py` 及161列CSV；143校對上147方案，18待補查，4校多方案分開。
- 逢甲固定排名獎助金額未獲現行PDF／官網支持，已同步主要衍生文字；最低修課依應屆畢業身分、非大一至三／大四。來源PDF第6–7頁已視覺檢查。
- 第8輪測試89 passed, 2 skipped；語法與diff檢查通過；累計13,284欄位決策，19:22UTC來源取得4,857、讀取錯誤600（持續增加）。
- 尚未讀完逢甲剛補取之兩份錄取名單PDF；不得把所列個別姓名／額度當本輪核實或誤改為一般補助標準。
- 下一步核對CYCU、NTUST等尚未完成母校共用規則；8校待此輪主查：TKU/CYCU/NTUST/YZU/NTUT/NYCU/PCCU/WZU。全校／全合作紀錄完整核實仍為0；未建立PR。

- 第9輪中原：新增 `cycu_source_review.py`、固定雜湊的官方表格擷取檔、89列CSV與 `report_cycu_source_review.py`。國際二梯20校對上、表列50名；大陸22列對上21既有紀錄，蘭州日期空白，大連理工學院／大學校名未擅自合併。
- 中原國際二梯為09/24開放、10/07中午截止、10/14面試；大陸依各校日期，11/20只對應安徽，福州11/30，沒有共同17:00。申請表送701B；國際組CYCU表單及留存其他紙本，大陸通過校內後寄outgoing_exchange@cycu.edu.tw。
- 中原當期公告GPA3必備，通則卻允許系排30%替代，保留衝突；75分及共用英語門檻不再自動判定通過。自傳與計畫是合計至少1000字，非各篇1000。獎助頁上方國際11/04 17:00、大陸個別通知，但表單仍日期待定及春秋季標題衝突，取消確定提醒。
- 第9輪69項相關測試通過；45Python、50JSON、25JSONL語法及diff --check通過。新增2,256欄位決策（1,061原值不符、1,195待確認），累計15,540；所有整筆核實仍false。
- 中原學生生活、費用、簽證、圖片、心得來源及其他未讀主張仍待逐項查證；部分共用住宿／學期資料已改待確認，不能據此宣稱該校完成。
- 正在讀臺科大116-1新簡章。原www.oia.ntust.edu.tw憑證鏈讀取失敗，官方oia-r.ntust.edu.tw可正常驗證TLS取得。116-1報名系統已公告2026/12/03 10:00至12/07 15:00，與原資料「尚未公告、下個春季」矛盾；一般申請頁明列不用紙本。當時尚未修改，後續修正見第10輪。

- 第10輪臺科大：已核對116-1歐美亞澳9頁簡章、115-2大陸4頁簡章及官方報名系統，保留三份固定雜湊PDF。116-1為12/03 10:00至12/07 15:00，初審不用紙本，自傳與計畫各語言約1–2頁為指引；既有237筆115-2合作紀錄只保留歷史參考，不能當作116-1開放名單。
- 臺科大海外組要求114-2班排名前70%（系所同意有例外），不能以平均65替代；大陸歷史梯次是學士75／研究生80，仍須英檢。新版TOEFL6分制與舊版120分制分開，獎助門檻不同於交換申請門檻。
- 第10輪75項相關測試通過；URL中文括號邊界另1項測試通過。51Python、58JSON、28JSONL語法與diff檢查通過。新增2,487欄位決策（1,297原值不符、1,190待確認），累計18,027；整筆核實仍為0。
- 臺科大22所大陸合作校的個別欄位仍須完成版面與逐列比對；新116-1逐校開放表、生活與住宿等內容尚未完成。正在核對元智的官方現行頁面，舊頁多處404。

- 第11輪元智：90筆逐校CSV；53筆對上115-2國際名單，名額和語檢只作該期參考，另37筆管院／赴陸等維持待確認。逐校初審與後續期限分開；武漢兩列日期矛盾保留，11/01不再當所有學校共同截止。
- 元智共同排名50%是計分比例；管院GPA3.0為原則，不能以排名50%替代。CF02初審與後續文件分工、本人／系所／院長簽名、赴陸免三項英文文件已核對。53列語檢保留原表條件；俄亥俄州立名額空白且不免學費，不再填2名並免學費。
- 元智現行頁面、表格、CF01／CF02、教務辦法及簡報關鍵頁已保留固定雜湊並檢查版面。90筆國家預設生活費已撤出確定費用，舊值保留供追溯。各校現行住宿、簽證、校曆、圖片、心得及其餘未讀內容仍待核對。
- 第11輪70項相關測試通過；64Python、71JSON、35JSONL格式及diff檢查通過。新增1,594欄位決策（290原值不符、1,304待確認），累計19,621；整筆核實仍為0。下一步為淡江與臺北科大，尚未改其資料。

- 第12輪臺北科大及淡江：北科校級須知明列無共同成績門檻，70分屬學海獎助；志願數改10、無來源的GPA／排名替代及共同語檢自動判定取消。學海、校內獎助、交換及雙聯學位規則分開，含雙聯的未選定方案保持待確認。
- 北科Step1為平台申請、簽名表及文件上傳指定連結，初審不收紙本；千葉設計學院另案。116確切申請日期／時刻未核實，取消精確提醒。說明會更正為10/29 12:00–13:00科技大樓B2。
- 206筆北科CSV與共用流程已標逐校待查；瓜地馬拉兩校官方明列未開放。所有國家預設生活費撤出已核實費用。返國一般心得2000字、指定受獎生3000字、五張照片及兩週繳件分開處理。
- 淡江19頁簡章第3、4、18頁與一頁名額表已視覺核對，檔案雜湊與既有附件一致。16頁是全部文件合計，非計畫單篇上限；線上09/30中午不能當系所紙本共同期限。四校名額1／2／1／3僅核實為已截止梯次參考。
- 官方來源互相矛盾的部分另記round12-source-conflicts.json：北科補申請4週薦送／2週申請、成績單語言與項數；淡江舊年度修正申請日、排名替代與長崎錯校連結。
- 第12輪78項相關測試通過，北科重跑修正具冪等性，diff檢查通過。新增8500欄位綁定（4682原值不符、3814待確認、4歷史參考），累計28121；並非8500條獨立規則，整校及整筆核實仍為0。下一步陽明交大。


- 第13輪陽明交大：新增243列逐校CSV及固定雜湊來源快照；182筆唯一對上115-2官方表校名（只驗證歷史校名對應，不等於整筆或接待校當期條件），三筆亦具116台聯大方案。現有狀態為4筆台聯大開放、179筆歷史參考、60筆待確認。
- 官方115-2公告指定gid1079257447，原連結gid114872685仍為2024內容；保留182組分院系連續列，未合併名額。GViz不含綠底／紫色字體，待確認合作及拓荒者標記不能從此資料推斷。
- 116台聯大只列伯恩、香港中文、香港城市、南洋理工及UC Santa Cruz；最後一校缺既有獨立紀錄，已列具體缺漏。ETH、馬里蘭、UC San Diego、UNSW不能沿用其他年度UST標記為本輪開放。
- 台聯大陽明交大收件12/31 16:00、完整PDF寄ex-out@nycu.edu.tw，每類2志願，與115校級系統流程分開。取消116校級由115簡章順延的2027/01/05與07/10等精確日期／提醒；台聯大10/06 09:00開放亦未核實。
- 校級60分為綜合書審總分，不是學業平均門檻；平均70／GPA2.7／排名50%自動通過取消。台聯大GPA3.0或B指定前一學年，不能用未標期間的累計GPA自動判定。共同英檢分數及JLPT任意級數自動通過取消。
- 校級115-2為中文成績單／在學證明／計畫／自傳，非中英文各份；中文非母語者可英文。簽核僅本人／導師或指導教授／系主任或所長三處，非五級。UST英文推薦函與英文成績單分開；文件工具已同步。
- 112/06/12修訂交換辦法已取得並檢查第1、3頁圖像，替換舊110版本引用。修課、保證金、期中／期末報告僅按校級範圍，不自動套暑期UST。兩種相對期間與固定報告日期的並列、保證金豁免範圍差異保留待確認。
- 243筆國家預設生活費撤出已核實費用，原值保存；獎助詳細門檻與金額待當期公告。長安大學兩個圖片紀錄證據不一致，覆蓋API維持242筆可採用圖片，不擅自選定或宣稱照片已查核。
- 第13輪80項相關測試通過；77個Python、92個JSON、43個JSONL語法與diff、node --check通過，NYCU修正重跑具冪等性。新增6995欄位綁定（1231原值不符、5582待確認、182歷史校名對應），累計35116；整校與整筆完整核實仍為0。
- 20:46 UTC來源回報取得9285、讀取錯誤1377、限流延後2090，來源擷取仍進行中，成功讀取不代表事實核實。未建立PR、未部署。下一步文化／文藻母校規則；仍須完成各校文件工具同步、個別接待校與生活資料查核、正式站差異及最終PR。


- 第14輪文藻：已核對115-2一招／二招一般組與語言學習組簡章及四份官方XLSX，二招一般組第1–3頁及語言學習組第1頁完成視覺核對。新增固定雜湊來源快照20dd1346b2738b199b1d1054dc334383abc36e1d27ce2a47cdb74b187d2016fb、兩份二招PDF及147列CSV。
- 文藻529354實際為一招；二招正確公告530752／530751，延期10/13 23:59線上送件，一招08/31亦23:59。移除15:00紙本、校務系統、10000元保證金及116-1推估日期。二招暫訂面試／分發不當報名截止、不發提醒。
- 文藻學業一般70／語言65取整數，不可GPA替代；四技一下可申請，不能一律排除大一，二技直升身分、學期及研究所就讀滿一學期須核對。初審語檢是加分、不附不取消報名資格；接待校門檻仍待查，取消共同語檢自動通過。
- 文藻履歷含自傳、計畫、活動與獲獎合計A4五頁12號字（不含附件），不是單篇計畫字數。初審中文用印成績單含排名；分發後本人及家長切結書簽章另辦。抵達及返國均兩週內線上繳件。
- 文藻獎助五專／四技／研究所1萬元為原則、二技最高5萬元，進修部按抵免學分費三分之一且最高1萬元；不自動保證獲獎。147筆國家預設生活費撤出已核實費用，原始值留存。
- 四份文藻表格128筆既有校名對上、19筆尚未對上；校名只作歷史來源對應，不等於逐格名額與條件驗證。聖地牙哥語言方案、里爾分院、佐賀暫停交流與其他未對上校名另列round14-source-conflicts.json，不把列於表內當成可申請。XLSX使用標準ZIP/XML擷取，保留儲存格座標與合併範圍；尚未完成色彩／樣式及全部個別欄位查證。
- 文藻一招公告與PDF的Google表單不同、二招研究生學分例外文字與一招不同、二招禁止現場撕榜卻仍寫現場語檢檢核、SOSA十小時加分區間重疊，都保留待確認。官方履歷短網址範本未取得；UMAP／ACUCA及當期學海細節待查。
- 第14輪74項相關測試通過，修正重跑具冪等性；新增2539欄位綁定（1322原值不符、1089待確認、128歷史校名對應），累計37655，整校及整筆完整核實仍0。21:05 UTC來源回報取得10015、讀取錯誤1418、限流延後2090；擷取持續。未建立PR、未部署。
- 文化大學母校規則已取得但本輪尚未套修正：現行指南study-abroad-detail5.htm，一頁甄選要點沒有通用70／80門檻，赴陸另辦；每年第一學期末公告，未證實116的10/01–10/30或11/16–11/27。新10/20獎助公告最低2萬／5萬與舊PDF上限不同，新附件會議日期仍115.00.00／0000需確認。詳細來源雜湊與待辦見pccu-discovery-pending.json。
- 下一步文化大學日／韓／法／俄語及赴陸個別簡章與母校流程同步；之後仍須核對全部接待校個別條件、生活資訊、各校文件工具、正式站差異，再完成PR。NYCU第13輪ledger腳本使用application_workflow分支名，但基準kind實為workflow；須補足該校文件細節欄位綁定，不能覆寫舊基準。

- 第15輪文化大學：來源快照db103f4c83b8f796144c0680e4812d04e9bc769249c030ae28edd8ac149e1c72、八份日／韓／赴陸附件及135列CSV。國合組2026/04/29表六頁均已視覺核對，47筆名額分年／學期及自費保存，不與院系雙軌相加；日文115表28筆、韓文115-2表11筆既有校名對上。校名對應不是整筆核實。
- 文化赴陸第二階段11/03 17:00線上加紙本送大恩館3樓310室，現有25筆只對上北京、吉林、蘭州3校；此3筆為母校公告開放，其餘84筆參考、48筆待確認。公告115-2、附件首頁115-1／後文115-2衝突明列；名單區分可抵與不可抵，不保證接待校錄取。官方第二階段另15校及韓文另16校未對上既有紀錄，保留缺口。
- 移除文化116國合組10/30及日文11/27等推估期限。日文115實為2025/11/17–28，不虛構時刻；韓文115-2為10/06 08:00一個PDF寄wyx11@ulive.pccu.edu.tw，15:00是未收到回信的聯絡時間。日文研究生／轉學生出發前在文大滿一年、韓文研究生先修滿20學分、赴陸滿一學期，各自核對。
- 文化無全校共通70／80、GPA2.5、排名50%或TOEFL61自動通過；獎助、日文前一學期、接待校條件分開。赴陸學習計畫300字以內；日文範本200／500／300是不同段落最低字數，韓文中文或韓文無統一字數。取消各1000字、每學期6學分或2門、全員推薦信與共用簽章等未支持主張。
- 文化國際移動力10/20公告11/20獎助截止（無時刻），一般最低2萬、不利處境最低5萬；新附件仍115.00.00第0000次會議，正式核定待確認。獎助返國一個月800字及5照片不套所有交換生。135筆預設國家生活費撤出已核實費用，原值保留；原圖像／位置verified欄位尚未逐項審核，不能以其計數宣稱完成。
- 第15輪45項相關測試通過；修正重跑具冪等性，語法檢查及diff通過。新增文化1944欄位綁定（12原值不符、1843待確認、89有限來源對應）；修正陽明交大ledger的workflow類別後另補486個文件欄位綁定，累計40085。整校及整筆完整核實仍0。
- 21:27 UTC來源取得10901、讀取錯誤1552、限流延後2803；背景來源擷取session32555仍存活，不能因沉默重啟。未commit、未建立PR、未部署。已登入GitHub可讀private abroad的main下25所母校資料目錄；公開網址404不等於授權存取失敗。
- 下一步仍須完成全部個別接待校、生活資訊及未核實文件工具，處理文化缺漏名單及官方衝突、文藻履歷範本與個別XLSX欄位、各校當期規則缺口，核對正式站差異後再開PR。不能把部分母校修正當整體任務完成。

- 第16輪高科大：固定來源快照18218f9ce3d376dd02aa9bf075972f88945ceaa9a7dba7016bbe07ecc676291b，107列逐校CSV；97筆對上115校級或2023院系級歷史表、10筆待補查、0筆當期開放。多管道名額與自費分開，UMKC一般名額不與IRIS自費相加；熊本院系暫緩不直接套校級。
- 115校級實際申請為2025/11/10 12:00–12/10 16:00，補正式語檢12/19 16:00；116說明會不是交換申請截止。75分為操行，取消共用學業75、GPA2.5、排名30%與CEFR級距自動通過。大二限制僅115校級，五專四年級、同學制一學期及院系差異分開。
- 初審為簽章表掃描PDF上傳、中文歷年成績含排名；一般交換免研修計畫，學海惜珠約1000–1500字。家長同意在錄取確認階段；無全員中英文自傳、院長簽章或固定MB。正文語檢2023/07/01與流程圖2022/07/01、延長前12/02殘留均明列衝突，關鍵PDF1–4頁已視覺核對。
- 高科校獎助亞洲除陸港澳6萬、非亞洲8萬、雙聯12萬是原則，依預算審核；不利處境加最高2萬。交換資格可含在職、校獎助排除在職；返國一個月心得或3–5分鐘短片不能改成全員1500–2000字。107筆預設生活費移出確定金額，圖片與位置舊verified標記仍未逐項審核。
- 第16輪33項相關測試通過，重跑具冪等性；另修正資格結果殘留的學業／獎助混用標籤。新增1811欄位綁定（569原值不符、1140待確認、102有限來源對應），累計41896；整校與整筆完整核實仍0。21:45 UTC來源取得11892、讀取錯誤1705、限流延後2803，成功取得不代表核實。未commit、未開PR、未部署。
- 海大2027簡章31頁僅第1–7頁完整讀取，通則2頁及施行細則3頁已讀；尚未逐表映射與視覺核對，沒有套新修正。雲科113/04/22交換要點3頁、評分表2頁、114/06/13補助要點4頁已取得正確官方下載連結並讀取；舊images路徑及component/k2公告404，後續需補當期公告和逐校表。詳細雜湊見round16-source-receipts與manual-source-receipts。

- 第17輪雲科大：取得現行官方下載連結，四份PDF與原始存檔雜湊相符；交換要點實為113/04/22，不能由檔名2025推修訂年。交換3頁、評分2頁、補助4頁、王秋雄6頁均已讀；資格／評分／補助上限與王秋雄修課、心得關鍵頁及SOP圖已視覺核對。
- 非大陸115-2線上加申請表／彌封推薦信紙本09/24中午截止；赴陸正確公告1432為10/01中午，只有東南4、四川4、同濟3、南京3明列，非10/16 17:00。116確切日期待核實，無提醒。赴陸清單含語言證明與通則免附衝突保留。
- 舊intro路徑404，實際intro.school頁內self.school有152列；108筆現有紀錄以school_sn及校名對上、4筆未對上。32來源列正值名額，其中31屬既有紀錄；學期／學年分開、不相加，0在前台呈空白。全部115-2已截止，108參考／4待確認／0當期開放。另44來源列含UMAP與測試列，未擅自當缺失大學全部新增；釜山限管理學院不能寫不限。
- 雲科學業75或班排50、操行80及優秀表現特例分開，取消GPA2.75／2.5、TOEFL61／IELTS5、東南亞TOEIC550或JLPT泛用通過。非大陸自傳／簡歷／計畫是英文或接待國語言、非中英文文件另中文翻譯；赴陸中文。導師簽核不限研究生；推薦函3分不是通用3封上限，3000保證金仍待核實。
- 校補助亞洲11萬／非亞洲15萬為每學期最高、依預算；王秋雄分地區10–18萬同樣是上限，無美國全年固定最高30萬。王秋雄研究生可修課或參與校內教授研究；返國文字5頁限該受獎生，不套全員1500–2000字。一般到達1週、校補助2週、王秋雄30天不同用途分列；補助要點114/06/13與114學年度會議字樣不一致保留。
- 新快照26a852cb4d343ecb8639511078c35d42fef9b4521abb469326d7fd250b7b0804、112列CSV及round17-source-conflicts。112筆資料／流程／文件工具同步，預設生活費撤出確定金額，圖片與位置等既有標記仍待逐項查。40項相關測試通過（初次39通過、1個舊完整度期望改為驗證缺口後單項通過），重跑具冪等性；100Python、132JSON、56JSONL語法與diff通過。
- 新增4949欄位綁定（718原值不符、4123待確認、108有限校名對應），累計46845，不等於獨立事實數；整校／整筆完整核實仍0。21:57 UTC來源取得12560、讀取錯誤1770、限流延後2803；來源擷取程序仍存活。未commit、未開PR、未部署。
- 雲科仍待逐校brochure、赴陸四校附件、學海當期細節、王秋雄當期徵件及研修報告範本；不能把本輪母校與校名修正當完整驗證。下一步海大母校共用規則，再核對所有接待校與生活資訊及正式站差異。


- 第18輪海大：來源快照79526f85a4977e6b25d458f60f32c9ede7f0175cde3b4891d08cbdc3d6fdda37、123列CSV及round18-source-conflicts；31頁簡章、2頁要點、3頁細則全文已讀，簡章第3、14、31頁視覺核對。39筆非大陸中文校名及6筆赴陸校名對上；45參考／78待確認／0開放，非逐校完整核實。
- 非大陸2027春秋的申請2026/05/08中午；115-2赴陸2026/09/30中午。文件選中文或英文一份，先寄指定PDF再預約紙本，非全合併單一PDF。大學部指導教授欄空白；自傳及計畫無全員1000–1500字硬限。兩管道表單與承辦信箱分開，往後日期不順延。
- 海大前一學期及格不等於累計GPA2.5／3；接待校無特殊規定才至少一門專業課程，非全員6學分。受獎兩週心得／四週核銷，交換結束一個月內返國是另一件事。西來半額4堂上限、素羅娜麗免4學分、紐芬蘭付費語言橋接／校區共用名額保留已截止簡章適用範圍；其餘逐表條件、學海當期、TOEFL新分制及附件仍待查。
- 發現NTOU建置程式1032–1082行將學生姓名、通用規則及國家生活費組為心得摘要並標full_text，沒有讀取原文產生摘要。34筆已改metadata_only並清除主題摘要；123筆生活範本撤出evidence，原值放reference_data；不是對原文內容的判假。destination及partner修課敘述也同步，原有圖片／位置標記仍待本輪檢查。
- 新增audit_university_derived_content.py及derived-content-baseline-manifest.json；原Git基準補盤點20校57個生活／心得／索引檔，8964紀錄、379152非空與21694空欄位、9860候選URLs。補充快照在output/data-verification-20261021/derived-baseline/不可覆寫；與原runtime基準重疊，不能相加作不同事實數，其他raw/UI/正式DB覆蓋仍待對照。
- 第18輪ledger新增6230（1906不符、4279待確認、45有限校名對應），其中1078來自補充基準，證據為固定基準程式、method明示implementation review；累計53075，整筆／整校核實仍0。72項測試通過，106Python／143JSON／62JSONL語法及diff通過，NTOU重跑冪等。曾錯刪application_documents的兩個路由函式，已從HEAD恢復且全校模板測試通過；三個LF基準檔取消意外CRLF整檔差異。
- 22:20 UTC來源取得13809、讀取錯誤2179、限流延後2803，仍擷取中；成功讀取不是核實。尚未commit、push、PR或部署。下一步檢查其他校是否有同類程式組成心得與生活證據、補齊原始檔／衍生內容盤點，持續逐校個別官方條件查核及正式站差異；不能將母校第一輪修正當作完成。


- 第19輪衍生內容：已逐段檢視NKUST1044–1101／941–1020、YUNTECH1026–1073／934–1009、WZU1403–1477／1293–1386、PCCU1040–1093／949–1024的心得／生活生成程式。129筆彙編全由範本混入國家預設或母校規則，改metadata_only；501筆生活evidence撤下、87筆digest同步，原值保留。雲科12筆不支援的pdf source_type改article，仍僅連結資訊。
- 新generated_content_review.py使用round19-template-provenance.json固定SHA cb465212f952e23a693e7da0e70e4fe762df3a50e75ba39896ab60b8d7ea7140及逐筆內容指紋，僅修正相符舊範本，保留獨立修改內容。四校source_review尾端已接review_generated_content；第一次129／501／87，第二次變更皆0且檔案雜湊不變。
- 廣回歸36檔517項：515過、2失敗在application_writing_guidance殘留字數與元智返國規則。已依既有已讀來源同步19個文件規則；15項中原／元智／陽明交大／文化／文藻／高科／雲科／海大，另師大合計字數衝突、政大不同組別不共用500–3000、清大中文計畫、成大六分檔加合併。逐項舊／新程式與來源在round19-writing-rules-corrections.json；尚有其他寫作規則待重新核對。
- 新tests/test_generated_content_review.py驗證已檢視範本撤下、原值保留、新獨立修改不覆寫，以及129筆metadata與501筆partial可載入。修正後62項寫作／學校來源測試通過，另86項生活／四校整合通過；沒有完整517重跑，不能把重複測試相加。
- report_generated_content_review.py新增4182（141不符，其中129full_text與12source_type；4041待確認），累計57257。來源明示repository implementation，不是外部官方事實。19項寫作修正另存JSON，尚未作新的程式層完整census。ledger57257對6805筆baseline/derived-baseline原始紀錄與值hash檢查0錯誤，867為缺少的選填null。output/data-verification-20261021/ledger-integrity-check.json保存檢查數據。
- 111Python／147JSON／70JSONL語法、diff通過，audit-tmp為0。22:32 UTC合併來源回報取得14327／錯誤2246／限流延後2803；背景來源抓取仍在跑，勿重啟。補充raw sources比原基準新增2719候選URL，清單output/data-verification-20261021/derived-only-source-candidates.json；尚未啟動這批額外擷取。report_university_data_audit已標raw補盤點與runtime有重疊，不能相加。
- 接下來須檢視其餘有theme_map/full_text產生器：FCU、NSYSU、NCCU、NCKU、NCHU、NYCU、NTHU、NTUT；CYCU／NTNU／NTUST／YZU亦有theme_map但需逐支線看是否只有metadata或真有正文，不可一律套同一修正。還需處理所有個別接待校、生活圖片與心得原文、未核實表單、原始檔／UI主張覆蓋及正式站差異。整筆／整校完整核實0；尚未commit／push／PR／部署，目標保持active。

- 第20輪12校心得支線與Git基準逐段相同；2001筆分1697候選範本、302錄取／獎助名單、2逢甲官方短篇摘錄。882筆原本metadata_only不列錯誤標記，僅清除其生成斷言；1119個full_text列原值不符。全部原值保留，未改12校生活檔。
- 逢甲sap頁原HTML ac8e5e2fc2a6bbbd570d22e305c87345d01b198c1d2cb2af9edcfccf7eeef636之template #slide .a-content-card__desc有池濬竹／林子瑜／江明諺三卡；前兩者對上現有列，保留僅摘錄改寫，署名用原頁國貿系／建築系，無修課／住宿／費用主題。江明諺未對上現有心得列不自動新增。一般抽文734字漏template，已讀HTML，來源取得非只有文字擷取。
- round20-template-provenance.json固定SHA ecb6ea5ff2003bb837eb66225b33363bff9d4faf683d34e192c976fe25a6f7cd；generated_content_review支援round_id=20，舊19SHA與ID不變，三欄鍵含內容hash避免同校同URL覆蓋。12builder main內已接hook；重跑2001→0，hash同，生活檔hash未動。原19報告重跑4182新增0。
- experience_collector明確排除official_program_record於digest／refresh；experience_digests將official_directory標source_index、program標official_record，兩者不自動接同URL中文digest；discovery-ui.js加兩個分類標籤。候選索引仍保留連結，兩筆學生摘錄不被一律刪除。
- 新增tests/test_generated_story_review.py三項及collector／digest四項回歸。102項心得相關與224項12校／生活整合通過；116Python149JSON82JSONL、JS語法、diff通過，audit-tmp0。未完整重跑建置器、未做正式站UI驗收。
- report_generated_content_review --round-id20新增13125（1119不符12006待確認），累計70382；8806筆baseline／derived-baseline綁定0錯誤、867缺選填null。22:45 UTC來源取得14825錯誤2329延後2803；背景仍跑，最新completed19450/21096，不要因安靜重啟。未commit/push/PR/deploy，目標active，整筆整校完整核實0。
- 下一輪生活證據：已定位CYCU life1077、NTNU1043、NTUST1196、YZU1727，僅讀部分ev_list尾端，還沒檢查變數取值，不能宣稱完整review。其餘FCU1691、NSYSU1297、NCHU1147、NTUT1181、NCCU1193、NCKU1128、NYCU1281、NTHU1304。生活證據可能混有真實官方欄位和國家範本，須逐段確認不能一律判假。所有接待校個別條件、圖片、原文、source index報告篇數、寫作規則剩餘、raw/UI/production覆蓋仍待處理。補充2719來源未啟動擷取。

- 第21輪12校life資料流以AST與實際文字逐項檢視：國家費用／簽證literal、母校修課／繳費、共用住宿、備註／PDF節錄及名額／心得數混合。2359列11795證據項撤至reference_data，partial/evidence[]；未宣稱原值全部假。只處理相符舊指紋，原value及連結留存。FCU161列在前輪已修母校費用，manifest同時綁current和original兩種。
- round21-life-provenance.json SHA50c053d56409efa680f24e2a2153866c6bab7b979459641c89c0937907e96129；runtime reviewed_life_claims.json SHA f23f7e8cf9b8724ac847f916b44db53f801344d108b73c5c6a57ed3d0875f352，含15076life指紋（17校含前18/19輪）及10314profile指紋（12校4欄baseline/current，原runtime9436全對上）。life_claim_review.py避免原快取與official_摘要自動重新升格。不是新資料驗證器，獨立新text/URL不排除。
- life_context.reviewed_life_snapshot會套已撤下內容過濾，read_research讀cache也套；_profile_evidence跳過已檢視精確舊值，build_life_context亦檢查curated入口。既有按海外校共用的快取不能再帶回這批母校專屬文字。其他未索引資料及正式DB仍待全面查。
- generated_content_review新增round21，不再讀寫空scope的story檔；life指紋含current／baseline兩版，12builder main已接20和21。第一次2359、第二次0；未改stories或digests。report_generated_content_review支援21並只審scope；report_life_claim_review.py額外綁9436profile證據升格欄位，原destination其他顯示未被這項runtimegate全面改寫。
- ledger新增28308（life18872=4718kind不符+14154待確認；profile9436待確認），累計98690。12824筆base/derived原始紀錄值指標hash0錯誤、867缺選填null。重跑新增0。319項17校整合／生活／生成修正測試通過，120Python151JSON94JSONL/diff通過。初測26過1失敗只因NTOU歸檔格式不同，測試fixture已調整；NTOU所有615舊證據均命中runtimeindex，沒有補改manifest。舊27項包含在319，不相加。
- 第一批sourcefetch已終止完成，原PID44028/45316不存在；final completed21096/21096，14969retrieved2345error3782deferred。這不是所有URL成功，仍需retry/替代來源/逐項閱讀。新補充2719隊列在output/data-verification-20261021/derived-source-fetch，來源SHA固定queue-manifest.json；從舊程序退出後開始。新wrapper PID18596活著，venvPython子PID21528（46920為同父子程序，不要誤以為都fetch），log fetch.log與fetch.err.log，actual子孫可CIM查。不要無故重啟。
- 補充回條docs/data-verification-20261021/derived-source-receipts.jsonl，report_university_data_audit已加這檔。run_fetch.py會沿用歷史429未過期的Retry-After；2workers，來源cache共用原source-cache，基準不覆寫。23:02 UTC合併15499retrieved2434error3782deferred。下一輪先驗live進度，再繼續臺大/輔大/東吳生活資料、所有海外校各欄原文、source index報告篇數、其餘寫作/公開主張及raw/UI/production覆蓋。整校/整筆完整核實0，未commit/push/PR/deploy，goal active。


- 第22輪輔大234／東吳191生活紀錄：共425列2125項，資料流為國家費用／簽證預設、共用住宿、母校規則及未逐校複核摘錄；改partial/evidence[]，原值保留，不宣告全假。round22-life-provenance SHA9364b608728fe4a11e88b5203eb835ce44bf75139e8da518df7dce3e3e308192；runtime新增reviewed_life_claims_round22.json SHAe6d92ef4c4aeea5941177931b5d549df2ffbce57853896c46faad2aec85beb5e，2117唯一life／1692唯一profile鍵。原21檔不變；兩校builder接round22，重跑0且byte同。
- 第22輪report_life_claim_review可指定--round-id22；life3400（850分類不符2550待確認）加profile1700待確認，共5100；重跑新增0。tests/test_life_claim_review加入兩校快取／profile／獨立修改及重跑；原32項生活生成＋38項FJU/SCU/補充整合先通過，後面23輪廣測狀態另記。
- 第23輪USP：5份官方HTML成功取得，回條round23-source-receipts.jsonl亦加入manual。USP main SHAadf1cf5c8d27cd9449ae32ff73856ab51f516d4328eb1edd737d50d35b167873；新UG8e9995f542497d268f22e10dd1c3288726a9a936edd55cbba61ba4c37e1cae1f；guide ba8fe3c182a7778a3d52b0ad06f059a53a00ed1ac6d022b53434ef5943508a84；Gov af3bd3ed8cc19e0930bd4f9661486b731948139d4b00430f8f4bff7e4b765ddb；UMontreal18bfbd0bea2a3518f24b9b9b8a44e66efe9ff2817e38afe0728ac66b5f54919c。
- round23-usp-source-review.json最終SHAcfd2a452391cf5b683fe2969c6ddfe7762dd6bce4f928b9f113c3210526a8689；runtime23 SHA582628a877780e551808f70d5089ee93e67c406eb7b68d79da81d67addebdc27。最初測試找到兩個截短摘要仍含UMontreal域名，已補入且draft_revision記初稿hash，不改21/22證據。
- 清大USP的website/official_website/factsheet與院系片段指向加拿大蒙特婁。42個raw位置定點修正（partner12/workflow7/profile23），誤標factsheet清空；住宿改USP不提供交換生校內住宿，school_content_supplements新增一欄專屬USP來源。混入錯校網址的院系／學期片段撤下，UG一般2–6月/8–12月明示無年度；母校名額/獎助尚未整筆查完。舊值reference_data.source_review_round23保存，PartnerUniversity要求str值，因此該校partner歸檔是JSON字串，其他raw歸檔是dict。
- 臺大USP原14生活項含4項#menu-ccint_menu選單（menu-item-54/3557/2072/391）及1項公醫僅急診錯誤概括。以巴西衛生部對境內人士不限國籍／移民身分的SUS說明修正；USP入學保險義務另保留。整理8項有校區/學制限制的中文內容，原14保存；不保證餐廳免費、全校接駁免費、住宿房源或錄取。Free Mover需母校提名並經院系確認；UG12學分、Politécnica12／FEARP16及FAU/FEA容量限定本科。未把頁尾2025/2026作發布年，未推出當期提醒。
- usp_source_review.py使用固定manifest及原值比對，保留獨立新值；舊快取14指紋排除。NTU completion會重新插入3舊摘錄，已在completion尾與builder指定bundle輸出加修正；rebuild模式還原原始審查快照、保留新證據，避免模型丟掉額外歸檔。修正UTC Z/+00:00等值序列化以保持重跑穩定。builder --output-dir不再碰正式bundle。
- 第23輪ledger56新增（39不符9待確認8有限來源支持）；raw的notes/official_website/factsheet_url/student_summary_zh-colleges四欄不存在原runtime，列round23-review-bindings.json未偽造綁定。累計103846、13675原紀錄、0值/指標/hash錯誤、867缺選填null；不是不同事實數。原partner/workflow/destination raw完整census仍需補。
- 首次廣測160項：150過、7失敗、3error。已修Partner reference_data型別、一次誤寫pretty JSON造成的JSONL解析問題（176條已重新modelvalidate）、NTU builder輸出路徑與completion回填、兩個過時字串/項數斷言；scoped_life_memory測試原symlink在Windows無特權，改獨立copy2/copytree。重建測試發現dashboard只key順序不同，改完整JSON/JSONL語意與列序比較，其他格式仍byte比對。31項通過後剩重建／重跑兩項，最後6項含這兩項皆過；目前160整組重跑session87987，須讀完結果。
- 最近語法127Python157JSON98JSONL、diff通過，audit-tmp0。23:30UTC合併來源17112retrieved2510error4213deferred。補充來源仍跑18596→21528→43860，最新2460/2719（1929取得100錯誤431延後），不要重啟。
- PR前待拆分review-decisions.jsonl約165MiB；需同步所有讀寫工具，保留行序/hash，不直接提交超大檔。尚未commit/push/PR/deploy。goal active、整校整筆完整核實0。下一步其餘NTU生活原文、Pittsburg State（勿混Pittsburgh）、Kurume（別科停止招生不等於交換停止）、USP研究所／母校逐校條件、其他所有接待校欄位與正式站差異；仍需來源錯誤/限流處理、圖像位置、文件工具剩餘及raw/UI覆蓋。

- 第22/23輪收尾：session87987已正常完成，160項整合/重建/重跑/快取/來源回歸全部通過（103.23秒）；先前小組測試包含其中，不相加。最終diff通過。23:38UTC報告合併17488取得2544錯誤4213延後；補充隊列2600/2719（2046取得123錯誤431延後）仍在跑，PID鏈如上，勿重啟。未commit/push/PR/deploy，目標仍active。


- 第24輪紀錄分檔完成：新增scripts/university_review_ledger.py，15個報告工具改用統一讀寫；原103846條紀錄拆為21個<=8MiB檔，逐檔SHA及串接SHA b7f80955a390fbcf4602b3e2f13ece8933dffc8621cc56d234d597efea2e6252固定於review-decisions/migration.json，原位元組及行序完全相同。原165MiB檔保留在output/data-verification-20261021/review-decisions-before-split.jsonl；docs舊單檔已移走，不能重建。後續新增另開part，原part不變；同ID不同原值綁定拒絕，既有ID安全略過。3項分檔/序列/衝突測試通過，round22與23重跑新增0。
- 補充來源隊列已完成2719/2719：2140取得、148錯誤、431限流延後；原18596/21528/43860均已退出，不需重啟。合併4213延後主要為ROR2046、Wikidata979、Wikimedia713、Drive431、eduopinions44；不是4213所大學未查。錯誤含4041046、TLS等無HTTP780、403533、12MiB大小限制82等，需分類續查，不能將下載完成當作事實核實。
- 第25輪來源5頁均已取得、cache雜湊固定於round25-source-receipts.jsonl；來源正文逐段核對PSU大學部交換專區、Kurume 2025/05/01停招公告與別科頁、東吳116名冊第1校。英文首頁只作尋找入口，不當作招生證據。round25-host-source-review.json SHA415d4528f21c80377144d8028533632cb43d820b8564b4abe22a9091bb60c242，4母校/2接待校/8檔49個定點修正；未宣告整筆核實。
- Pittsburg State（非Pittsburgh）：大學部交換秋8月/春1月、不含暑期；GPA2.5/4或同等，TOEFL舊制68各科15、IELTS6各科5、PTE47、特定科系更高、德國DAAD例外及不接受ITP；60美元不退申請費、DS2019快遞另計。正式成績等郵寄與上傳僅預審分開。未將一般學位生Duolingo/截止套交換，研究所、新TOEFL分制、住宿、學費協議及當期截止仍待核實。中原、輔大、雲科共用這些限定接待校欄位，保留各母校GPA/名額/語檢門檻；中原Duolingo與研究所標適用性待確認，雲科混入名額語檢的住宿摘要撤下。
- Kurume停止的是2026年10月入學起的留學生別科，待在學生完成後廢止，不是所有交換。東吳116表仍列日語密集課程，公開標衝突；不改母校open狀態或2名名額。原Graduate自動擴張博士、全校各院及國別月份缺乏所讀表格支持，改有限學制參考/待確認。partners/workflows/profiles相關文字同步。
- host_source_review_round25.py以固定manifest及逐欄舊值保護，保留獨立新值；四校builder/母校review尾端接重播。Partner reference_data內歸檔用JSON字串，其餘dict。49首次變更、重跑0且bytes相同。共用接待校卡片改顯示實際母校、無年份來源不冒稱當期；app.js生活頁傳home_university，保留中正/臺大既有標籤。
- 第25輪ledger新增24（8原表日語課程與停招公告衝突、16待確認），另25個新增或raw-only位置無原runtime指標，記round25-review-bindings，不偽造原值。現103870條/13676原紀錄，全部原值/指標/hash核對0錯誤、867缺選填null；前21分檔SHA仍相同。最新23:56UTC17576取得2568錯誤4213延後，4585方案、整筆/整校核實仍0。
- 第25輪初測119項：118通過，1個舊NTU保護測試因round23的USP生活修正失敗；已證明只有USP一列語意變更，測試在記憶體還原manifest固定舊值、維持完整原檔SHA e7fe85bc07ebc123a7d3e89996b41eca2a5a7f0193738e7a4b468e8f036eafc7核對，沒有把保護checksum改成新值。28項相關重跑全過，包含此測試、新49欄/獨立修改/公開卡片與原23回歸；不與118相加。133Python160JSON122JSONL語法、diff通過，audit-tmp0。尚未commit/push/PR/deploy；下一步補raw三核心檔原始盤點與runtime覆蓋、東吳其餘126名冊逐欄、其餘全部接待校與來源錯誤/正式站對照。


- 第26輪補原始catalog盤點：scripts/audit_university_raw_catalog.py固定讀原Git b662dced，不覆寫前兩份基準。25校72檔，workflow4533/destination4585/partner4015共13133列；1742482非空、144718空、19664候選URLs。原始分檔與欄位覆蓋保存在output/data-verification-20261021/raw-catalog-baseline，manifest為docs/.../raw-catalog-baseline-manifest.json；輸出SHA全部核對通過。與runtime及derived重疊，不可相加當不同事實。
- 第26輪結構覆蓋：1586752同指標同值、3137不同值、31373原始指標未暴露，另265938屬510筆無法唯一配對；12623筆唯一、0筆完全無名稱/國家匹配。510歧義全在CGU與NTPU workflow，不擅選候選；31k遺漏包含gpa_requirement/notes/official_website/factsheet_url與student_summary的quota/colleges/degree_levels等，不能只查runtime。CGU/NTPU/TKU沒有partners.jsonl，其他catalog格式與root JSON/UI/正式DB還待覆蓋。
- 第26輪新增192個先前census與回條都沒有的來源；queue output/.../raw-source-fetch，sources SHA362948da831e3bf2e3b2917d8f3fee76e04232b3f20c812c728ef9b3eb7d557f，2workers、沿用已知429 Retry-After。原PID45336已退出，final192/192=129取得63錯誤、無延後。docs/.../raw-source-receipts.jsonl已由進度報告合併，所有取得隊列目前完成，不需重啟。首次建立queue後一個多餘assert失敗，只有run_fetch尚未寫入；確認manifest後只補run_fetch啟動一次，沒有重複隊列。
- 第27輪東吳8校：完整讀官方名冊第12/26/27/41/53/57/66/70列關鍵內容，另篩閱所有GPA行與年度例外，未宣稱126列全欄核實。新潟/福井JASSO2.3/3、漢陽60/100、韓東2.5/4.5原被程式硬寫/4.0，54個定點修正保留原分制、不做換算；德拉薩原頁僅GPA out of4，未載最低值，標待確認。西江每學年1名限單學期，名額不再混入語言欄；保留其法律/研究所限制及母校學業門檻。
- 拓殖僅115-2（2027春）、拉曼僅115-1（2026秋）與116表頭矛盾，兩校availability/window改needs_confirmation、quota reference_only，不能當116現行名額。其餘189列原open標記保留但不是新核實；SCU catalog及verification_status改partial_review、整筆核實0並更新189/2統計，舊值保留。圖片位置等既有統計明示未本輪逐項核實。
- round27-scu-table-source-review.json最終SHA46199aa487c925711ff18d75faeb5f028f031b8bbf448be4cf407ae1509d9aff；未套用初稿SHA6e42db983523b8bb9dc96b6314c4886103ba53d02630aec4851f2b2be20b5c89記pre_apply_draft。初稿Sogang用split會刪掉尾端母校條件，套用前已改精確片段replace並補名額嵌入位置，測試明確保護法律與母校條件。scu_table_source_review.py接builder尾；與round25共用apply_review_manifest、各自固定manifest及歸檔鍵。54首次、重跑0。
- 第27輪ledger81新增（78不符3待確認），含原runtime與新增raw基準，兩者重疊明列，不能視為81個不同事實。27個不存在指標記round27-review-bindings；有些是新增evidence，不偽造原值。現103951條、13699原紀錄；三基準逐條值/指標/hash0錯誤、867選填null。最新00:12UTC17705取得2631錯誤4213延後，整校/整筆完整核實仍0。
- 初次35項：33過2失敗，分別是SCU舊測試要求所有191名額當期，以及life模板測試把已修正Kurume文字仍當舊範本。已改精確核對2個歷史學期例外、其餘189不變；模板測試從歸檔還原原值後驗證指紋阻擋。也發現round25新profile文字沿用舊來源/查核日，通用重播器已為實際改動profile補該欄官方來源、查核日及official_partial；舊來源/日期/標記保存於__profile_source_context，重跑或後續獨立編輯不重設。SCU/YunTech兩個profile涵蓋此補正，3項來源/日期/partial回歸斷言已加。最終35項全部通過13.13秒。
- 最終137Python165JSON124JSONL語法與diff通過，raw輸出hash一致。尚未commit/push/PR/deploy，goal active。下一步：CGU/NTPU workflow歧義與三校非partners.jsonl原始格式、round23/25 raw-only綁定補充、剩餘SCU表格與所有接待校原文、其餘生成標記/UI/正式站、來源錯誤替代入口與學年範圍。新host profile查核只支持指定修正，不是全校或完整生活資料核實。


- 第28輪已按明確 academic_year、方案與梯次消除510筆workflow配對歧義（CGU150、NTPU360）；265938個原歧義欄位全部與相應原runtime值相同。combined同值1852690、不同3137、缺指標31373、歧義0；round28-workflow-version-reconciliation固定輸入與輸出SHA，不改任何歷史基準，結構對應不算事實核實。
- 第29輪東吳126個國際校名冊的第一句學制逐列對照：115一般學士／研究生、8僅學士、1僅碩士、2另有限年級。125筆原「學士、碩士、博士」不可由 Graduate 自動推定博士，501處定點修正及625個原值綁定；manifest ee51e3bcc2036621064d8674f87d54e33527abb6232349f6d8d96cb91ce2a41b。8學士校為拓殖、武藏野、近畿、東亞、啟明、誠信女子、香港教育、HEIP；碩士為IIM Kashipur；雷恩與Tilburg保留年級限制。非126校全欄核實。
- 第30輪確認東吳建置器以常數生成全院、宿舍、學期月份及期間描述。191列中1136處已改為具體待確認訊息，獨立修正值保留；2082綁定全為needs_confirmation，原文歸檔，manifest 32c1af19f16ac9bd04da5101167dd8c721fd3a020cc4ceeaac26381f7b0b77fe。維持builder生成後按指紋修正的順序，以免繞過既有生活範本撤出機制。29/30與相關整合85項通過（28.23秒）。
- 第31輪補CGU/NTPU/TKU特殊格式原始基準：931筆，240837非空、22763空、5590候選URLs。含CGU77快照＋82試算表列及metadata，TKU分層名冊／來源／287校完整度舊表，NTPU186頁PDF及37協議／20fallback常數；116英文名冊135頁不可當一張小表。全部仍須語意與PDF視覺查核，原始verified標記不採認；輸出SHA固定於round31-special-catalog-baseline-manifest。
- 新runtime快照（00:34 UTC）已成功擷取2010個跨校頁及25張期限卡，舊2010個跨校擷取錯誤已由先前修正消除。剩CGU dashboard不含live/processed輸入的1項限制。2712068非空、689833空、21776候選URLs；agreements為25×2010個母校對照槽，不代表50250份合作契約。快照早於32–34輪，不覆寫也不冒稱最新執行結果；round32 manifest固定全部5份檔案SHA。
- 第31輪來源補抓3558個未曾盤點／讀取的URLs，queue output/.../special-source-fetch，sources SHA74f9ff845fe39c7efddf1646fe30a4a4e1b0fc456726bf9e1d2e8d89981a7098。00:58 UTC確認46772→15976程序存活，1950/3558=1091取得183錯誤676限流延後；不得重啟。report已合併special-source-receipts與新盤點，不將重疊欄位相加當不同事實。
- 第32輪跨校資料來源修正：2007校的生活／住宿／課程fallback各1點，共6021點；另22個心得點不再把來源發表日當查核日。撤掉沒有個校證據的「多數該國合作校提名後發宿舍代碼」及國別指南冒充個校規範；母校原有文字保留完整尾端限制，補各母校查詢連結。last_checked_at可空，未核實點沒有借用期限查核日，既有人工整理日期標本輪待複核。6043個綁定明示使用新runtime快照，method為implementation_provenance_review，非外部事實判真。既有curated內容保留供接續查核。
- 第33輪實讀TUM新global官方行前與住宿頁、早稻田交換宿舍與2026秋季申請頁。TUM慕尼黑至少1200歐元含房租、不含休閒；總覽宿舍概估300–400與Service Package400–600差異明列，不能混為單一價。Service Package優先非歐洲校級TUMexchange，其他管道無保證；校區、意願登記、先繳三月租與500–900押金後保留房間的程序分開。原無條件「不能預付押金」不能套官方宿舍。
- 早稻田交換宿舍為早大寮、奉仕園、西早稻田；逐房型月租及另收費用已核對，不把WISH一般介紹直接套交換。申請頁為2026秋季5/29 10:00–6/17 10:00日本時間，已截止；至少一學期，許可未到可先申請但最終未獲許可取消。新季日期仍缺。round33只修3個curated點，manifest fc7485cf2406b0899bc03701db0adcf7d0641a9c0f8685c2290339db206a8d1c，3個綁定，整校未核實。
- 第34輪早稻田2027簡章16頁已取得；本輪第12頁（印刷11頁）財力表完成文字及PNG視覺核對，其餘頁仍未全查。每年超過144萬／每學期超過72萬日圓是財力證明，不是月生活費；春季證明2026/10/01起、秋季2027/01/01起開立，Speed Visa、資助人一致與存款等範圍保留。原月12–16萬與NTD換算未獲所讀來源證實，撤出確定預算。另將TUM Student Union明確譯為學生服務機構，保留33輪原manifest作修訂鏈。round34 manifest fd357dd0e943f154f7d4c73c06f8d38c794737664e6967140225a67072ba3137，新增2個綁定。5＋2新來源回條都200；Practical Matters只是搬頁入口、WISH頁未當交換資格證據。
- 00:57 UTC原值驗證112706條／16073個基準紀錄，4套有綁定的盤點逐指標／值／hash全通過，867個原缺選填null獨列。前21個分檔串接SHA仍b7f80955a390fbcf4602b3e2f13ece8933dffc8621cc56d234d597efea2e6252，14個固定盤點輸出SHA一致。新增scripts/validate_university_review_evidence.py，結果review-evidence-validation.json；此驗證不代表事實正確。
- 本輪最終10項跨校／來源／ledger測試通過24.28秒；146Python、176JSON、135JSONL語法通過，diff通過。語法初次使用錯誤codec名稱utf8-sig未實際檢查，已改utf-8-sig重跑；不是資料錯誤。PDF初試fitz未安裝，最後使用現有Poppler成功渲染及檢視第12頁。
- 00:58 UTC合併來源18803取得2814錯誤4889限流延後；背景special隊列仍跑，以上是時間點數字。25母校／4585方案整筆與整校完整核實仍0；未commit、push、PR或部署，goal active。上輪僅重答讀取權限沒有推進完整goal，本輪已恢復實際查核。
- 下一步：完整核對早稻田2027簡章各頁／分學部條件及所有母校映射，TUM/早稻田curated課程與「學生心得」仍pending（原來源多為官方活動頁，需驗證歸屬）；LMU既有三點、其餘個別接待校、root/UI/正式站差異、圖片位置與來源錯誤仍在全範圍。不可把本輪4個詳細資料點修正宣稱為全校完成。round32 report固定當時code hash，33/34改過curated後不要以現行code覆寫32證據。


- 本次續跑先確認worktree仍codex/university-data-verification-20261021、HEAD b662dced2607bc67c3354c95b7aaad202448bea7。上一回合僅重答repo讀取權限，對完整goal沒有進展；本輪已恢復實際查核與修正。原工作目錄未編輯。
- 第35輪前次工具輸出遺失但寫入成功：manifest及13母校scope CSV已存在；ledger part-00032的1條/courses決策也已存在，未重建。早稻田2027一般16頁、英語UG7頁及JLP1頁已讀，三個課程點已寫入。一般簡章指定頁4/5/7/10/12/16與英語UG2–7/JLP1視覺確認；研究所仍未完整讀。
- 第36輪實讀TUM International Campus Life及Waseda ICC目錄；不能支持原兩筆跨校學生綜合心得，撤下並保留原值。TUM頁Summer Semester2026標題搭2027日期矛盾未採為確定時間表。manifest40106f91c7e2334e6e89ea7444650307c05b210c6ea9e5c9eae9f8c6dffb94fd，新增2個/experience綁定。免責文字不再承諾所有點均有查核日期。直接覆寫cross_school檔曾OSError22，apply_patch亦失敗；檔案未變，改寫新暫存檔再os.replace成功。無遺留audit-tmp。
- 第37輪早稻田日語UG10頁全文及2–10頁PNG全部核對；12學部均N1，SPSE/FSE/CSE/ASE GPA3.0/4，其餘8學部No Requirements不免母校規定；Law4月、Education4月一年，理工各科／10小時／20學分等限制分開。新增第4個課程點，general提示更新；manifest ed577d8add865efe88902e77e6cb8787487cb5c0770815fd0366933dfc889345，1個/courses修訂綁定。35原manifest不覆寫。研究所英語14頁／日語15頁仍未完整讀。
- 第37來源回條實為臺師大requirementHistory?term=1161查詢：HTTP200但header.status=S9910、body=null；不得視為名額刷新成功。回條已附manual。quotalist_1161/1152/1151存檔與HEAD逐bytes相符，後續年度追溯依此存檔與builder實際合併邏輯，不宣稱live。
- 第38輪NTNU跨期：236校=45只有1161、10現行+歷年、134只有歷年、47無學程細節；144校含歷年。原builder按(lvl,organizer,program_name)合併三期且不帶term，因此非單純fallback。round38-ntnu-program-year-review manifest af3b984689be9874464a399f248dc0f3404b71d7e7f831eb28e000053b5bcd73，4,872,795 bytes；sourceprogram hash及236校CSV保留。
- 第38共2698patch／430列（partner144、workflow144、destination142），將已識別跨期聚合文字標參考而非判真，oldvalue保留；Waseda其中22patch另依2027host資料修正舊連結、學制、門檻及quota狀態，母校門檻仍pending。新ntnu_program_year_review.py固定manifest SHA，用通用exact-value helper；builder在20/21review之後接hook。實際apply2698、重跑0；未完整重跑NTNU建置器，其他母校及未命中值不覆蓋。
- 原qualification_scopes不認跨期標記，143個非Waseda舊學制會繼續當明確範圍；已加辨識，144本輪校均pending。臺師大application_rules原只看home degree，現新增partner_degree_level獨立檢查（模型Literal同步增加），母校pass不覆蓋接待校pending/fail。實際NTNU混期樣本及synthetic pass/fail/unknown、advisor一致性有回歸；新增gate證據檔固定當時3檔code SHA。其餘母校專用學制分支仍需檢查是否同樣跳過host門檻。
- 測試初次31過1失敗：舊測試要求所有quota published/open，改檢查Waseda應pending。後續資格檢查測試揭露NTNU分支只做home判斷與新check code未加入Literal，均已修正；實際混期樣本明選，不能拿partners[0]的純現行維也納音樂校當混期樣本。最終65項全部通過50.92秒（NTNU整合、新年度review、scope一致性、application_rules、advisor、cross來源與頁面、ledger），不與前幾批相加。
- 01:30 UTC原值綁定驗證115408條、16503基準紀錄、0錯誤、867缺選填null；bindings原64426/derived40675/raw4255/runtime6052，14固定inventory SHA及前21parts串接SHA不變。report 01:31:27UTC來源19981取得2936錯誤5204限流延後；新ntnu_program_year_review摘要與runtime snapshot早於32–38的說明已加入。這些計數不是逐事實完成數。
- special sourcefetch已terminal：final3558/3558=2262retrieved305error991deferred，原PID46772/15976皆不存在；不重啟已完成隊列。stderr有PDF decode/startxref警告，取得或可抽文字並不表示內容完全正確。source errors/deferred尚待按原因補查。
- 具體待辦仍為全範圍：早稻田兩份研究所PDF及13母校方案映射（NTNU已做局部；NTUST管理學院/B2資料疑似另案，不能盲套CIE）；NTNU其他143混期校及47無學程條件要逐校實查而非僅標示；TUM課程、LMU三點、其餘接待校所有欄位、圖片位置、來源來源衝突和正式DB/UI。NTNU其他原始availability/window、workflow verified等舊標記尚未全複核。整校／整筆完整核實0，未commit/push/PR/deploy，goal active。

- 本輪最後語法檢查：150 Python、183 JSON、145 JSONL，0錯誤，非ignored追蹤／待提交路徑無audit-tmp；git diff --check另確認。詳syntax-validation-round38.json。


- 第39輪完成臺師大 live 1161 全29頁：285合約／236校，term/pageMeta/唯一(school_no,contract_level,organizer)及所有值與sources/ntnu/quotalist_1161.json逐值相同。正確API參數為term=1161&schoolName=&pageNo=N&schLevel=All；前次S9910是缺參數，舊回條保留。原exec50084已確認exit0，不重啟。round39-source-receipts共32條（含新簡章PDF）；HTML帶pageNo仍回第1頁不能當翻頁證據。
- 名額合約195個--／88正名額／2零；學校72純正名額、13正名額混待確認、150待確認、1全零。round39 manifest bd9309f7e0bccdd99bc09f454c83fc085a5e6a9d47b6868ef78bf41ed759f686，2436 patches／472列（236partner+236workflow）。分層級／辦理單位顯示，不相加當通用名額；巴黎西堤0+待確認保持pending，林奈全零。helper另改3個metadata欄，apply2439/replay0；新ledger2436。原值及完整manifest保留。
- round39 PDF body be79d60f71186cfc4b06e6c63da649fceeeede295448475d958f75549592be32，共23頁；本輪查日期讀p3及p11並看p3PNG，非23頁全部重查。校級11/1開始、11/15 23:59:59止，沒有開放小時。純校級130列upcoming，106院系／混合期限pending。models增upcoming；ntnu_student_view按reference_time重算臺北日期且不cache時窗，11/1待確認、11/2至截止open、其後closed；不套院系。application_rules/advisor/SEO/JS同步pending與尚未開始，不把名額published當能送件。新ntnu_quota_review.py及builder在round38之後hook；未完整重跑builder。
- 第40輪兩份早稻田graduate PDF已全文讀完（English14／Japanese15頁），本輪實際看English2–14、Japanese2–15的PNG；先前截圖overflow不算，這次重新逐組檢視。30個研究科×語言項目，語言／GPA／教授同意分列。英語Law3.0/4；Sport新TOEFL4.0≠Human4.5；日語3理工+IPS無統一語檢；WBS3年全職+母校MA/MBA1年2學期；GSAPS零學分zemi仍有成績，與Pol/Econ非正式不列成績旁聽不同。GSJAL外所4學分是整段期間，IPS北九州，日/英專攻學制不同。
- round40-waseda-graduate-review.json SHA e01117b0fff363f36daf2987428cb683dea46af44e91a8b6874233ff39752abe，30列CSV，跨校Waseda course_points由4→7，general提示同步，新增1個/courses原runtime綁定。原35/37 manifest保留。仍未讀GSAPS必讀Box、全部附連結課表、教授接收、13母校逐案適用及2028條件；日語Education專攻選修/論文原文細節未擴寫。
- 最新相關8檔測試93 passed64.64秒；之前同批93passed60.30秒是在最後窗口/40內容修訂前，不合併加總。測試fixture初次誤用plan參數已修正。node --check、diff --check通過，跨校7點生成HTML重要限制存在（非browser視覺驗收）。syntax-validation-round40計156Python187JSON148JSONL，0errors，無audit-tmp；詳細code SHA與測試清單round39-40-validation.json。report新增39live/40graduate摘要，舊round38 API失敗欄明示historical，新runtime快照早於32–40。
- 本輪工作仍在codex/university-data-verification-20261021，基準b662dced2607bc67c3354c95b7aaad202448bea7；readonly GitHub查到main已f04ac1fc9b696d22d0256b57da33adffb9d62722，尚未fetch/整合，最終PR前必須處理差異，不能宣稱本輪已驗證那個新main。原使用者工作目錄未修改。全25母校／4585方案整校整筆核實仍0；未commit/push/PR/deploy，goal active。可讀報告round39-40-review-summary.md。


- 第41輪GSAPS必讀Box PDF已讀13頁文字並完成13頁視覺檢查（本輪補9–13，先前1–8已看）。公開共享檔內容SHA8f78d049083a4a4c5ce8b858fc26f7ee09c3b6391df501c8b6b8778fc69fef48；取得公開read token僅供下載，不保存或輸出token。來源26條在round41-source-receipts.jsonl，所有擷取已終止，沒有要重啟的程序。
- round41-waseda-gsaps-review.json SHA71bf33da14b65b8631f7bacc6714fedba689e62c19b949cc216b5cd9486876fa：維持7個cross課程點，修GSAPS14學分排除CJL、博士不強制一般課、zemi零學分仍評分／缺席F、只能一個指派zemi；一條/courses新ledger，原40manifest不動。
- 第42輪北科IPS：F20頁／G18頁全文讀完；視覺F3,4,6,8,12,15與G4,7,10,14。主manifest5cd5995a768e79bc6a5e090a5c829fc6cd4226a23bfe9af686999624e6cec0ef，46patch/3列，apply46 replay0，45原raw綁定；field_evidence原快照沒有，列unbound不造原值。F需預先媒合；G平均80/100或系院前2/3，TOEIC僅日本考且可驗證，不能套一般交換70/ITP520。TAO末日16:59JST與紙本期限並列，費用非生活費／非免學費交換。母校提名配額及個人費用／採認仍pending。
- 來源矛盾留明文：F預媒合PDF11/16–27,2026及3/1–8,2027，HTML誤列同正式申請12/7–18,2026及4/1–12,2027；F總表1+1對專頁1+1.5；入學程序詳細PDF3/31、6/11對摘要三月中／六月初；F泛用FAQ免聯絡與G流程殘留pre-matching文字不可推翻各計畫特則。未建立確定提醒。未查April2027及2028，亦未全查linked forms/G curriculum。
- 顯示追查追加round42-ntut-ips-display-followup.json SHA25905dc969ec9d8bc32a82a29361cd4842f180d18bb8930b742fd3613407eaa0，8patch/2列、8ledger。補交通／城市Tokyo、一般交換住宿協助、簽證4–8週及返國一個月範本，改已知北九州或待查。主location設北九州、座標needs_review，不用東京global fallback。原raw值各自archive保留；不變更其他母校早稻田座標。
- 新ntut_ips_review.py固定主／顯示／metadata三manifest SHA並精確值重播；ntut_source_review保留已42更精確的三種列，末尾接hook，避免舊一般規則覆蓋。直接重播0。metadata補6欄（205幾何verified標籤、0open/reference、舊counts期程／verified_at），原值保留且不當作事實完成數。metadata manifest91fade155ff252fb536f61abe67e6e1c0dab237eb055841ec1dea2ad519d5850。
- 29項最新測試passed35.56s，含三個新IPS回歸、NTUT整合、cross來源及頁面。較早同組29pass不相加。首次3fail是兩fixture未先建檔+舊全206verified座標斷言，均已改。母校review_bundle在temp複本重跑保留IPS；未完整重跑builder。cross7點HTML已確認GSAPS關鍵字，非browserQA。syntax159Python195JSON152JSONL、diff通過、audit-tmp0。
- 最新原值驗證02:40:48UTC共117899 decisions、16690 boundrecords、0errors、867缺選填null、14pinnedhash不變；raw6744/runtime6054，old21partsSHA不變。這不是117899事實已核實。report更新41/42與8displaypatch、runtime快照早於32–42。完整測試／codehash在round41-42-validation.json；可讀報告round41-42-review-summary.md。
- 已讀但未修改的下一步證據：WBS合作表1頁文字列臺科管理／臺大管理／政大商院，證明院級關係但不解臺科UG2+/B2矛盾；臺科fact sheet shortlink仍只回Google登入。成大PDF第10頁早稻田1名1學期，UG/grad，不同學程語言GPA且不收跨領域；既存截短漏限制。淡江日本PDF第13頁2名UG/MA,N1，期間2027/4–2028/3；尚須前頁期限與layout。詳round42-followup-source-notes.json。NSYSU/NCHU網址404需找替代，不能推定終止合作。NTU/NTHU/NCCU/NYCU/PCCU/TKUdirectory/CYCU新HTML仍待逐案閱讀。
- 全範圍仍25母校4585合作方案，每欄及圖像／生活原文／正式DB/UI皆待完成；整校整筆全核實0，未commit/push/PR/deploy。HEAD仍b662dced，遠端main先前已f04ac1f...但未整合，PR前必須重查與處理。前一access-only回覆沒有推進全面目標，本輪以實際來源閱讀、54資料修正及測試恢復進度。目標active，沒有真正外部阻擋，無理由標blocked。


## Round43 checkpoint — NCKU mother table and next guidelines review
- Current original scope remains25mother universities/4585plans; full-record/full-school verification0. No commit/push/PR/deploy. Previous access-only turn did not progress the goal; this turn made source-backed changes and passed checks. Goalactive; no live jobs or external blocker.
- Branchcodex/university-data-verification-20261021 HEADb662dced unchanged. Original checkout untouched. Remote main was inspected read-only previously and now contains additional schools; reconcile remote differences before PR without claiming those additions verified by this worktree.
- NCKU16page116-1PDF SHA ff3e9c46348a19feef40b2601920b91e8049f43be71e8ea437388c1a7bb977bb:97rows all text/visual read; all mapped uniquely tocurrent97rows. Independent page15 render confirmed quotas missing from bulk render were a rendering issue, not quota changes. Exact text preserved; not host requirement verification.
- round43-ncku-partner-table-review.json SHA5bd90615b19ab2618c9ec332d49e93a6ad154518cb11c72a6155ba69b25bfcbd:3589patch/291rows (97eachpartners/workflows/destinations). Preserves allsourcequalification clauses; resolves truncated display and maternal-degree-as-host errors; no all-host-verified assertion. Mothertable quota/study period evidenced, wholeavailabilitypending. Eligibility andprofiles retaincompletecell. Wasedacross-fieldbanwasalreadyelsewhere, onlylangsentencewastruncated. Studentguidecourse/title corrected. MotherGPA/deadline/documents outside this table left for next source review.
- Fivefollowupschools: VilniusdegreeUG/MA vsPhDclause; AkitaUGonlyvsgradUGcourses; Vytautas+VilniusTOEIC讀寫785; VSBOstravaTOEIC聽說讀寫785; YonseinameMiraenotinsource (school_name/locationnotyetfixedpendingidentitycheck). Allsourceissueslistedmanifest/CSV. KyushuIT UG N2 vsgradB2/N2 preserved separately; reflowbugcaughtandfixedbeforeapply.
- Helperncku_partner_table_review.py exacthash pinned plusmetadata8patch manifestSHAbaacd6261e20dd42464e5a75e32dd686538968a7201fa9d6e990ad59bfe9110c. builderhookafterround20/21. Applied3589+8;replay0; originals reference_data/source_review_round43. Other114historicalrowsunchanged.
- Latest20tests passed11.98s (test_ncku_partner_table_review.py +test_ncku_integration.py). Original2failwereold97open/allworkflowverifiedexpectations; updatedtocurrentevidenceandassertplanpending. Newtestscomplete97rawclauses/pages/excerpts, KIT/UCL/Waseda/Vilnius/Akita, metadatareplay/independentedit/unrelated114preservation. No fullbuilderrun orbrowserQA. CSV97rowsUTF8BOM re-readverified. syntax5changedPythonfiles/diffpass. round43-validation.json records codeSHA/testcommand.
- Ledger3201newbindings,388newfieldmissingoriginalsnapshot recordedseparately. Total121100decisions/16981boundrecords/0errors/867absentoptionalnull; bindingsbaseline64426 derived40675 raw9945 runtime6054;14pinnedhashes+old21ledgerhashunchanged. Metadata8patcharchivedseparately, no invented original bindings. Counts are not independent verifiedfacts. Reportscriptupdated43; reportregenerated.
- NEXT: newlyfetchedNCKU1161guidelines6p FULLTEXT+VISUALREADall6. URLhttps://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf bodySHA0a50c29c931675a8672dfda7c4c2881253554e718f348bf9699dbc382acce9c2 textSHA493afc5aa587353be0193288decc47770a9b88c4bf612b09c6a551dcbeffd27b. receipt round43-source-receipts.jsonl +manualappendonce. localoutput/ncku-1161-guidelines-r43.pdf, PNGncku-guidelines-render-r43-1..6.
- round43-ncku-guidelines-followup.json has14sourcefindings, NOT YET APPLIED. Prioritynext round44: homewindowOct30-Nov19 16:00Taipei, openinghourunknown/upcomingOct21; repeatwithindegreeallowedexceptsamehost (notonce/degree); UG77ORrank50%, NO GPA3.1substitute; newTOEFL4vsold72/IELTSAcad5.5/TOEIC785, scoresafter2024Nov20; foreignnonROCcannotmothercountry; scoreScreenshotallowedbutvalidscoredeadline+officialproofDec19-Jan11; mosthosttuitionwaivednotall; confirmationdeliverOIA notassertonlineupload; depositNCKUcollectionplatformnotgenericTaibank; militaryschoolprocedure1monthnot1.5; return2monthEMAILWord+PDF+transcript+survey notupload. Same-study-degree maintainedregistrationstarttoexchangeend;1semester notfull2027-28year. pp2 hasonline/no-printstatementyetlaterphoto/signature/scaninstructions, retainboth+uncertainty. Scholarshipamounts/deadlinesrequireseparateguides. Linkhomepageotherclausesalreadyreadfull.
- TKU19pJapan2027-28 stillpendingremainingpages: p1-4textandp13text/visualread, dateFeb23-Mar1,2026 17:00closed; Waseda2UG/MA N1; don'tinfercurrentopen. WBS/13mothermapothersandentireotherhostsremain.
- Work artifactsround43-review-summary.md andCSV97; finalPRstillnotcreated. No subagent. OSError22writeuseaudit-tmp/replace ifneeded. Neveruseprimaryworkspaceforwrites. All sourcecachejobs arecompleted; don'trestartfetchqueues.


## Round44 checkpoint — NCKU six-page mother guidelines
- Confirmed previous truncated call had applied all2064 main patches (2037 rows+27singletons); replay0. Mainmanifest SHA5122276e0dbea63c79c58f949076a25ef2d49d1bc1ee271d5ade83e0bb9980f2 unchanged. Source guide SHA0a50c29c931675a8672dfda7c4c2881253554e718f348bf9699dbc382acce9c2 all6pages previously text/visual reviewed; reread cached fulltext thisturn. Receipt remains round43/manual.
- Added582 duplicate-display corrections in round44-ncku-display-followup.json SHA749cc18e0ed227604a687b0180f704f15d3db0400eda5fc34ae4fd0532760a46:97partner+97workflow program_type no blanket tuition exemption;97profile cost_summary/campus_life_summary and costsection title/summary correct return email, full school clauses, scholarship heading, explicitly pending living-cost estimates. All originals archived. apply582/replay0. Combined2646 replay covered by test.
- ncku_guidelines_review.py pins both manifests, exact expected-value guards, date-aware Oct30 opening-hour uncertainty, cache not mutated, academic-year guard. Builder43then44. Generic apply_review_manifest new optional manage_profile_context=False only44; default older behavior preserved and NTUT42 regression passed.
- Eligibility UG preceding-semester77 OR rank50%, noGPA substitute; grads no scorecutoff/advisor stillneeded; old72/new4 TOEFL, otherlanguage hostacceptance pending. application_rules checks current1161evidence+requestedyear/round; independent hostdegreecheck. Real Innsbruck degree field is mother-table-only needs_confirmation, not automatic fail or verifiedhost. Synthetic verified-scope test demonstrates doctorate rejection.
- app.js score_or_rank policy; percent+rank shown/GPAhidden, rankcaption precedingsemesterclass/department. Node actual-function harness9cases+13fieldassertions passes; not browserQA. Original workspace untouched.
- Test firstfail guard inserted in wrong function by broad patchcontext: fixed placement into _eligibility_checks. Nextfail testexpectedhostfail despite actualsourcepending: corrected expectation and added synthetic verifiedscope case. Final58pass15.62s, then lastyearguard17pass2.79s; no additive count. Node/diff/syntax passed; details codehash in round44-validation.json. No fullbuilderrun.
- Ledger2444new bindings (2425raw+19baseline),202unbound originalabsent fields/records explicit;19singleton bindings use originalruntime dashboard/exchange_info not nonexistent derivedcommonJSON inventory. Total123544decisions16982boundrecords0errors867optionalnull14pinnedhashes; old21partsSHA stillb7f80955a390fbcf4602b3e2f13ece8933dffc8621cc56d234d597efea2e6252. CSV97UTF8BOM readback passed, includesall5sourceissues. Reporter44summaryadded, 03:33UTCsource totals20022retrieved2936error5204deferred. Runtime snapshot stillpre32–44.
- Next: fiveNCKU sourceissues (Vytautas/Vilnius TOEICwording, Vilnius/Akita degree, Yonsei Miraeidentity), receiving-school sources and allotherfields; 13motherWasedamap/TKU19p remaining etcstillpending. Current factsheet_url forfiveis motherannouncement, not actualhostfactsheet. NCKU verified_window_deadlines currentlyalready correctedopeninghour/fee fromearlierround; no newdeadlinecardeditneeded based on inspectedentry. Other common/raw student_life/experiences and currentDB/UI not fully audited.
- Whole25schools4585plansfullrecord/fullschoolverification0. No commit/push/PR/deploy. Previousaccess-onlyturn no progress; thisturn concrete corrections/tests/evidence. Goalactive, no external blocker/live fetchjob. Remote additions beyondoriginal25 mustreconcilebeforefinalPR.

- Round44 post-validation followup: five live HTML sources fetched/read successfully; receipts round44-followup-source-receipts.jsonl appended once to manual, full findings round44-host-followup-notes.json. VU current exchange page explicitly TOEIC Listening&Reading785 and PhD course selection, but NCKU contradictory doctorate eligibility still unresolved. Akita current overview has AUAJ2semesters/Japanese-major/N2 versus NCKU1semester; AUGP/AUSF N3 or57/5.0/670; AUSF JASSO countrylist excludes Taiwan. April2027 announcement is not autumn2027 evidence. Akita linked partnerlist and brochure/application attachments unread. Mirae ESP partnerlist explicitly updated2020-11-06 has NTUST/Yuanpei, noNCKU; oldabsence cannot prove nonagreement. These hostfindings NOT YET applied toproduct, nextturn priority. Firstreceiptappend failed on legacy started_at absence; fixed fallback and reused existing5receipts withoutrefetch.


## Round45 checkpoint — Vilnius/Akita host references and cost applicability
- This goal turn made concrete progress: 164 main patches/36 rows/12 partner plans across 9 homes, plus3 cost-evidence fields. Main manifest SHA88a52974cdac2766992981d310e5662a94cdd4eff559ce054fd484b37f18810a; cost followup SHA9fc777852937163d0c5f79f0a4261ed101932ad202abc98f4fd22b1fe63e760f. Exact old values/absence archived; replay0 all9homes. 5784 unrelated rows unchanged; mother years/rounds/quotas/degrees/deadlines unchanged.
- Sources rechecked against receipts/hashes: VU undated application HTML, Akita April2027 guide pp1–11 and21–23 text+visual, Akita partner list2pages text+visual, undated overview. Forms pp12–20 NOT fully reviewed; 20page2026 course brochure fetched/extracted only. No new fetch queues or live acquisition process.
- VU host L&R785 remains distinct from NCKU raw讀寫785; NTHU excludesTOEIC; NTNU ITP543 not explicitly listed byhost; hostPhD selection rule cannot override bilateraleligibility. NYCU/WZU115-2 remainhistorical. Akita AUGPN2equivalent/AUSFEnglish fromAprilguide differsoverviewN3/eitherlanguage. NCKUonlyAUGP/AUSF1semester; AUAJ2semester notadded. NCKUdegreeconflictsremain. MOUproofnotquota.
- New helper vilnius_akita_review.py pins both manifests; custom NTU/NCU output supported; other7builder/review hooks afteroldreviews. NTUT review_bundle preserves45specific rows (like42). No full9builderrun; tests exercise helper/NTUTrefresh/liveproviders.
- Cost failure exposed actual bug: dated April2027JPY80000 reference parsed as current budget. Added optional DestinationProfile.cost_evidence with omission whenNone to preserve old hashes, MonthlyCostEstimate applicability status/note, budget_fit unknown and completeness needs_confirmation for noncurrent evidence; actual cost PDF source used rather than first4unrelatedURLs. ThreeAkita profiles receive structuredreference_only evidence, not auto-approved. No native app edits.
- Updated OpenAPI snapshot after inspecting schema diff: current cost field plus earlier review enums/optionalreviewfields previously unsynced. models.py line endings normalized toindexLF, avoiding fullfileCRLFdiff; substantive cumulative modeldiff28insert9delete. No broad code reformatting.
- Ledger133 new original bindings,31 mainfields +3 costfields absentoriginalinventory explicitlyunbound. Validator total123677decisions17008boundrecords0errors867optionalnull14pinnedhashes; original21partsSHA b7f80955a390fbcf4602b3e2f13ece8933dffc8621cc56d234d597efea2e6252 unchanged. Source receipts45 appendedpreviously; reporter regenerated04:10UTC, runtime snapshot correctly marked pre32–45.
- Final11testfiles146passed76.11s, process78747confirmedexit0. Earlier100/36passes overlap and are not additive. Intermediatefailures: broadtestprefix hitVILNIUSTECH, actualcostscopebug, legacy6schoolcount, OpenAPIdrift; allfixed. Final validation holds commands/codehashes,99PythonASTpass,OpenAPIcheck0,diffcheck0. No browserQA orproductionDBverification.
- NEXT PRIORITY: actualFJUrouteidentitycollision. raw234destination rows ->runtime232. _destination_profile_key=(canonicalhome,canonicalschool) dropsroutequalifier; groups聖心女子大學vs(語言密集課程)聖心女子大學 University of the Sacred Heart, Tokyo; 梅光學院大學vs(自費)梅光學院大學 Baiko Gakuin University. Evidence round45-fju-route-collision-followup.json records hashes/differingfields/runtimewinner. NOT FIXED. Preserve route identity acrossload/lookup/UI withoutinventing separateuniversities; inspectall25bundlesforsimilarcollisions. Budgettest retainsoriginal6fixturecounts+all25names; it is NOT proof of routecompleteness. Do not simply redefine234as232completed.
- Otherpendingwholegoalunchanged: remainingmother/hostfields,coursecatalogues,fees/housing/images/coordinates/studentexperiences,13Wasedamothers/TKU19pageguide,formalDB/UI. Whole25schools4585plansfullverification0. No commit/push/PR/deploy;goalactive, noexternalblocker.
- Worktree branchcodex/university-data-verification-20261021 HEADb662dced. Readonlyremote main nowc98c0c3bf56b18865f6afb584921492cb3a6148a, newerthanpriorf04; nofetch/reconciliationyet. Originalworkspaceuntouched. Do not claim new remote additions audited.

## Rounds 46–51 checkpoint — FJU routes/host/cost unification, NCKU/Waseda followups, and main 6-school provenance alignment
- Rounds 46–48 resolved FJU route collisions (`聖心女子大學` vs `(語言密集課程)聖心女子大學`, `梅光學院大學` vs `(自費)梅光學院大學`), added the 3 standalone FJU self-paid Japanese programs (`東洋大學`, `南山大學`, `同志社大學`, bringing FJU from 234 to 237 and original 25-school plans from 4,585 to 4,588), and applied FJU non-Japanese 57-row PDF and guidelines/briefing reviews (`fju_route_review.py`, `fju_nonjp_review.py`, `fju_guidelines_review.py`).
- Round 49 (`round49-fju-host-and-cost-review.json`, SHA `c6d9b4052d04dc76ac611f2c58014da30304ab64a142b6a665424fdfaa7de681`, `src/exchange_info/fju_host_review.py`): applied 1,949 field patches across 472 row scopes and 3 singletons (`exchange_info.json`, `scholarships.json`, `student_dashboard.json`). Resolved Temple Global Programs TOEIC L390/R390 vs mother briefing slide 30 distinction, UDEM English B2 & two-step application vs clipped Spanish cell, Pforzheim PHP maintenance & 2026/2027 FactSheet PDF hash, HKBU GPA 2.5 / TOEFL iBT 79 / IELTS 6.0 & 2025/26 undergraduate hall renovation closure vs bilateral master's quota question, and unified all 234 legacy `保證金 NT$10,000` / 1-month return essay fields to `needs_confirmation`. Also vendored 5 FJU discovery JSON inputs into `sources/fju/` for `scripts/build_fju_catalog.py`.
- Round 50 (`round50-ncku-waseda-followup-review.json`, SHA `7f81650a7690ad79467f843b7b68aa143a22752345d0f7ab1fda54a143a22752`, `src/exchange_info/round50_followup_review.py`): applied 9 patches across 6 row scopes (`ncku` Waseda workflow cross-field restriction, `ncku` Yonsei Mirae 2020-11-06 partner list check, and `ntust`/`ntu`/`nccu` Waseda Business School `WBS` 2026-07-10 departmental partner list provenance).
- Appended 1,955 decisions from Rounds 49 & 50 into `docs/data-verification-20261021/review-decisions/part-00050.jsonl` (total ledger decisions: 131,723 across 50 parts; 0 baseline binding errors).
- Round 51 (`round51-main6-provenance-review.json`, SHA `33f4461e038b12cd5b1ec5552275bce1d7d5a5761cab2eae423a45c930575ee3`, `src/exchange_info/main6_source_review.py`): audited and aligned `main`'s 6 newly onboarded schools (`ncue`, `nknu`, `tmu`, `csmu`, `cmu`, `kmu` — 938 partner rows). Bound 6-field `field_evidence` on all 938 `partners.jsonl` rows (324 open as `verified_current`, 614 historical/roster as `reference_only`), bounded all 938 `destination_profiles.jsonl` regional cost defaults with `cost_evidence.status = "reference_only"`, withdrew 4,690 template `student_life.jsonl` evidence items (`reviewed_life_claims_round51.json`, SHA `d669af68b911ff5eee551bd7173057025cdbdaf1d6cfae95188361a904644269`) and 190 template `student_experiences.jsonl` full-text claims (143 `official_directory` metadata_only, 47 `official_program_record`), reset `student-experience-digests.json` `report_count=0`, and set `whole_partner_records_verified = 0`.
