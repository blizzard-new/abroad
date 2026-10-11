第六批完成原98校範圍內的有限來源收斂，並優先撤下兩張整合阻擋照片。分支 `data/tku-completeness-20261011`，main基準 `59a20f27fcee00fb597abc79e75ec11778317422`，第五批固定輸入 `4f142ea36e69338d2956b4ea5d3d37a9f4116e52`，資料checkpoint `154abd57a742ff1c7fdad6a2a4ed566006407639`。同Draft PR13，沒有merge／deploy。

原42校官方根入口均已嘗試；SHA比對排除3個同正文HTTP／index別名的「新增來源」說法。初始分類為9校尚有未讀相關official leaf、12校指定入口失敗、21校已讀但無適用正文；本輪後7校接入61欄參考、12校入口失敗、23校已讀仍無適用內容。原98校累計27接入／36外部限制／35需來源，71校仍無可接入參考。原36限制逐項完全保留，沒有重試。

累計286官方名錄列／287機構及profiles、153計畫（原128＋25已截止日語第一梯歷史）；人工47校346欄、216/287校有官方參考（75.26%）、另2350段literal index不變。18校160欄可確認來源年期，含歷史資料；不等於淡江當期適用。最新2027–2028日語第二梯4校7名額已於2026/9/30中午Asia/Taipei截止，0新開放母校申請；其他283校名額149尚未核實新版／134協議或歷史參考。英歐語／中文組新版尚未核實，不稱官方尚未公告。

新增接待內容全部reference_only，帶官方URL、PDF頁或XLSXsheet/cell／原文、年期、查核時間與SHA。青山URL寫2007Spring但14頁正文實載2027春；新舊iBT量尺、科系／校區／研究所限制、兩階段申請與提名期限分開。兩份CoE各8表，實際2027/3及Office Use2027/4/1與校區地址核實；3/20或空日是預填值，不是保證行事曆。signature／health未載年度，不升成全部2027模板。

UADE一般學期／短期／dual-degree／freemover分開，兩份未載年指南實載5/15、11/15學生截止與4/30、10/31提名，不能補2027。UNA雙邊與無協議費用分開，西語能力與最多30ECTS保留；英語承諾DOCX一次ReadTimeout。NQU國際incoming與淡江臺灣國內交换未對應，網頁2張／兩表3張照片矛盾；表單母校博士勾選不等於接收博士。HQU正文2025港澳台簡章為歷史；指定下載目錄只列2019–2023簽證／承諾等，未取得2026/27更新，不證明官方尚未公告。PKU校級／院系級HMT報到及母校提名分開，common links的淡江不當名額。Aizu2027春In preparation與已過2026/9/17截止矛盾保留；Packet／Checklist明示母校Office取密碼，未請求／登入／解密。公開兩SAS表HTTP200實為含EncryptionInfo／EncryptedPackage的加密OLE，只有opaque bytes與格式已核對，不稱可讀模板。

新增5項pending官方確認：NQU照片張數、AGU英語替代證明條件、AGU成績單時間、AGUhealth模板與2027要求、Aizu2027春狀態／已過日期。加既有5項共10，兩方原件／頁碼保留，不修猜日期或默選。

照片阻擋固定文件SHA `8b7570acca35fc10154e52e8621b9829bc9a815b`；緊急修正 `35e28149c926705ea620692baefcddce89bab3d4` 已先推送，逐項證據見 [照片修正報告](tku-photo-blockers-resolved-20261011.md)。Sunderland誤配UWE圖片撤下；UAEMEX正確校景但Unknown作者、Facebook原件登入門與unknown上傳歷史未支持獨立署名／授權人鏈，也撤下，不判侵權。262其餘照片與固定輸入逐筆完全相同，座標264逐byte不變。現262照片（91.29%）／264座標（91.99%），25／23缺，41校聯集（原39＋2撤下），不維持虛假264計數。

原39資產缺口中有明確新線索的8校已限查；UM2頁map封面Produced Aug2026與未完工新campus分開；UMA2頁地圖未由2025檔名定年；HZ两校区学科對應、IACT現地址、長安多校區、OSM特定研究建物及ESIEA經度矛盾不代配。Paris Grands Moulins真marker48.8292405,2.3817211與viewport分清，但Diderot協議承繼／指定campus未驗，僅候選。0新展示資產；不宣稱全球安全来源耗盡。

本輪56host capture records／54URL（兩Aizu格式複核重用同網址另ID），另4份照片原頁／原來源／歷史查核。10PDF（8文字＋2視讀map）、2CoE XLSX可開；2加密OLE不可讀內容、1DOCXtimeout另列。HTTP200本身不等於有適用內容。累計2700captures／2303opened／397failed含重試與歷史，不當2700當期規則。

附件總表追加source_id／original_capture_id與正文擷取狀態，修正「HTTP200無error即正文可讀」：6筆legacy DOC原件紀錄仍未解析；6筆後續離線解析紀錄已有實際正文，對應5個原件，剩1個原件未得可讀解析。兩層以來源ID區分、原始bytes／SHA不變，不把成功解析當限制。這項邊界Focused 10 passed、5.159秒；初次9pass/1fail是把12筆都當未解析的錯誤測試假設，真實解析紀錄查明後更正並保留失敗log/XML。上列新增文件的12可讀／2加密／1timeout分類不變。附件metadata修正沒有改UI；瀏覽器證據驗的是相同UI程式與實際資料欄。

最終相關TKU／CGU／NTPU／共用回歸：220 passed、4 skipped、0failed/errors，80.97秒；4skip為既有CGU條件。實際390/1280 browser 4 passed、0failed/errors，70.3秒，真實展開學校卡片、來源及生活指南，最新年／track、unknown quota與兩撤下圖片／credit核對。不是全repository／另一session NTU全綠宣稱。OpenAPI --check與真實兩JS node --check exit0。

Pack-only只用manifest與transport parts還原4529檔／21封存／45分片、332,697,911 bytes，逐檔SHA通過；舊4455檔／15archives／36parts原樣，新增74members（56hostJSON＋10PDF＋2XLSX＋2OLE＋4photo captures）。M3/M4/M5的45快照、既有40校285人工欄、原128programmes／4profiles前綴及其他CGU3／NTPU12／NTU17／CCU1215／NCU13官方檔不變。

初始錯誤及中間驗證保留：Focused4pass/3fail與full217pass/3fail/4skip是3個測試字串／shape／NQU缺欄假設，按實際原文／schema修正；新增CoE後Focused6pass/1fail因生成audit未重建，依序重建後最終完整套件核對全部實際API值。前一完整220pass/4skip86.85秒是最後3文件前，不能代替上列最終測試。照片browser未展開指南、最後文件抓取用不存在--output exit2、fitz未安裝／PNG未生成功能錯誤均保留或如實記載，改用真實--checks与已裝pdftoppm，沒有宣稱初次成功或安裝依賴。

第六批與照片fix只動TKU資料／抓取與生成器／測試／證據，無新增共享registry/API/UI/资格/母校文件catalog更動。整份PR較main需主session統一整合的共享檔明列：`docs/api/openapi.json`、`src/exchange_info/api.py`、`src/exchange_info/school_content.py`、`src/exchange_info/static/app.js`、`src/exchange_info/static/index.html`、`src/exchange_info/static/regions.js`、`tests/test_fit_signals.py`、`tests/test_school_completeness.py`。既有API／profile路由使用TKU獨立照片與座標ledger，協議參考頁不標當期官方已核實；UI顯示TKU來源／年期／圖片credit及相關區域別名。以上不由本輪新增來源重寫。未動他校工作區、憑證、存取、付款或安全設定。

重現：以已凍結 `milestone6_*_inputs/checks` 及pack為來源，依序執行remaining_document_reviews、milestone6_reviews、milestone6_handoff、curated_references、public_references、census_audit、census_profiles、audit_tku_full_census、continuation_milestone及測試。intake builders用於請求前凍結，不能事後用新的index重造原「未嘗試」清單。爬取driver僅固定inputs，保留失敗與cooldown；不用網路即可重建交付資料。

下表逐校列最低所需校方內容；沒有送出訊息。所有逐URL狀態、原文／錯誤、日期、SHA在 [42校機讀證據](../src/exchange_info/official_data/tku/milestone6_remaining_source_outcomes.json)；完整98校、39資產及10項矛盾在相鄰milestone6／milestone5 JSON。尚未核實不等於官方未公告。

| ID／學校 | 初始／本輪分類 | 本輪attempts／接入欄 | 最少需校方提供 |
|---|---|---|---|
| tku-sister-341 清奈理工學院 | 指定入口失敗／指定入口失敗 | 0／0 | 可用的官方學期incoming入口、適用學年、提名程序、可接收學制與科系；目前交換標題無可追正文，正常瀏覽器TLS失敗。 |
| tku-sister-334 伊達爾戈州自治大學 | 指定入口失敗／指定入口失敗 | 0／0 | 真正incoming目錄／partner factsheet、適用年度与期限；另需Campo Tiro接收校區命名點，不能採La Garza行政點。 |
| tku-sister-328 華美中醫學院 | 指定入口失敗／指定入口失敗 | 0／0 | 學期交換受入規則與academic campus身分／點；Main Clinic及外院聯絡地址不能作教學校区。 |
| tku-sister-320 柬埔寨IIC 科技大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 實體學期交換與MBA/PhD eLearning的適用分界、當期提名與文件；另需有重用授權、拍攝年月及校區身分的校景。 |
| tku-sister-312 巴拉圭發展學院 | 已讀無適用正文／已讀無適用正文 | 0／0 | 對境外partner學生的學期incoming factsheet／期限／文件；World Bank或研究介紹不適用。 |
| tku-sister-311 麻州大學羅爾分校 | 已讀無適用正文／已讀無適用正文 | 0／0 | 對母校提名學生的incoming programme與當期規則；Global Partner Exchange出國清單不能代替。 |
| tku-sister-310 金山大學 | 指定入口失敗／指定入口失敗 | 0／0 | 目前真正International Office／incoming公開入口及當期partner factsheet；兩個假設入口404不證明全校未公告。 |
| tku-sister-290 阿根廷企業大學 | 未讀相關路徑／接入參考 | 3／9 | TKU協議學制／院系／campus与當期名額、具年度期限；公開一般指南未載獨立年，2026 factsheet只能參考，Learning Agreement模板需母校取得。 |
| tku-sister-306 合肥工業大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 適用臺灣學生的非學位學期交换正文與年度、提名／申請資料；漢語及獎學金頁不代替。 |
| tku-sister-281 堪薩斯州立大學 | 指定入口失敗／指定入口失敗 | 0／0 | 有效incoming exchange入口／当期partner factsheet；outbound Education Abroad及degree admissions不代替。 |
| tku-sister-270 德州大學阿靈頓分校 | 指定入口失敗／指定入口失敗 | 0／0 | 可用OIE incoming／partner factsheet URL及學年、提名與學生期限；已查兩個舊route404。 |
| tku-sister-267 羅馬大學 | 指定入口失敗／指定入口失敗 | 0／0 | 精確接收機構／院系雙邊計畫與臺灣學生適用年度、提名文件；不能補一般Erasmus規則。 |
| tku-sister-253 阮必成大學 | 指定入口失敗／指定入口失敗 | 0／0 | 可用incoming正文與當期適用資訊；新international路徑正文soft404。若需校景，提供有重用授權與拍攝年月候選。 |
| tku-sister-252 華南理工大學 | 指定入口失敗／指定入口失敗 | 1／0 | 可讀的臺港澳incoming方案正文／年度／期限；SIE HTTPS與直接官方HTTP入口只回12字。 |
| tku-sister-251 華中師範大學 | 未讀相關路徑／已讀無適用正文 | 3／0 | 臺灣學期incoming當期規則、接收學制／科系與模板；已讀港澳台合作目錄，未見適用正文。 |
| tku-sister-249 蘇州大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 非學位臺灣學期交换的接收與提名規則；degree、language scholarship及summer公告不可代替。 |
| tku-sister-246 香港科技專上書院 | 已讀無適用正文／已讀無適用正文 | 0／0 | 獨立incoming exchange programme與年度／協議範圍；外國degree／課程註冊有效期不適用。 |
| tku-sister-224 滁州學院 | 已讀無適用正文／已讀無適用正文 | 0／0 | 臺灣學生學期incoming規則、期限與指定校區；出國、暑期營及degree訊息不適用。 |
| tku-sister-214 宋卡王子大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 雙邊非Erasmus臺灣incoming factsheet与接收校區；歐盟capacity-building及credit-transfer計畫不能直接套用。 |
| tku-sister-203 巴黎第七大學 | 已讀無適用正文／已讀無適用正文 | 2／0 | Paris Diderot原協議由Paris Cité承繼的證據、當期incoming學制／院系／campus；Grands Moulins命名map point雖讀得但承繼未核實。 |
| tku-sister-193 國立亞松森大學 | 未讀相關路徑／接入參考 | 2／7 | 當期雙邊交換日程實際日期、TKU協議／院系费用與可用承諾模板；公開英語DOCX一次ReadTimeout，未登入協議表或申請系統。 |
| tku-sister-191 福建師範大學 | 已讀無適用正文／已讀無適用正文 | 1／0 | 適用臺灣incoming semester规则／年與期限；留學degree與世新／澳門／Oswego本校出國公告不適用。 |
| tku-sister-186 國立金門大學 | 未讀相關路徑／接入參考 | 5／10 | 淡江臺灣學生是否走國內交换而非國際方案、當期學制／院系／費率／期限，並確認照片需兩張或三張；两公開申請表正文未載年。 |
| tku-sister-183 穆罕默迪大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 學期incoming交換與當期partner條件；2027/28 full-time degree Batch2不能當交換年度。 |
| tku-sister-184 尼赫魯大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 真正non-degree incoming exchange而非國際degree／研究所介紹、當期期限及文件。 |
| tku-sister-174 華僑大學 | 未讀相關路徑／接入參考 | 5／8 | 更新2026／2027港澳台来校交流指南與模板、TKU协议和接收科系／校區；2025明文僅歷史參考。 |
| tku-sister-126 蒙古國立大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 境外partner incoming流程／年與期限；國際關係學院是學術單位而非必然交換承辦。 |
| tku-sister-55 巴拿馬大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | incoming接待規則与年度、提名及文件；Movilidad Estudiantil本校出國選拔已明確排除。 |
| tku-sister-39 會津大學 | 未讀相關路徑／接入參考 | 7／6 | 確認2027春In preparation與已過2026/9/17截止矛盾、TKU partner適用；由母校取得Packet／Checklist及公開但實際加密SAS表格之可讀官方版本。 |
| tku-sister-37 平成國際大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | incoming当期指南、資格／期限／文件；library／art museum／research／degree頁不適用。校景另需實際拍攝年月，不使用上傳年。 |
| tku-sister-144 武漢理工大學 | 未讀相關路徑／已讀無適用正文 | 4／0 | 公開臺灣學期incoming實際申請／教務規則、學年與模板；已讀教務處交換目錄與國際學生院lhlx，只見degree／獎學金／漢語／summer或空目錄。 |
| tku-sister-33 青山學院大學 | 未讀相關路徑／接入參考 | 9／16 | TKU協議UG/Master及接收校區／科系、當期名額与2027課表；兩校區CoE XLSX已讀2027正文預填值但非保證旅行日期。請確認英語替代證明、成績單時間及health模板與2027指南差異。 |
| tku-sister-139 北京大學 | 未讀相關路徑／接入參考 | 3／5 | TKU校級或院系級協議、適用學制／科系、當期提名／截止／初次申請模板；common links含淡江不等於交換表／名額。 |
| tku-sister-9 亞瑟柏大學 | 指定入口失敗／指定入口失敗 | 0／0 | 真正exchange及實體／線上學期適用，官方可用入口；distance degree不可默認實體交換。 |
| tku-sister-86 美國三一學院 | 已讀無適用正文／已讀無適用正文 | 0／0 | incoming exchange當期partner factsheet／deadline／模板；OISS一般支援及Study Away出國不可代替。 |
| tku-sister-61 莫斯科國立語言大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | 真正incoming公开规则／年／期限；國際候選返回同一root正文，不是交換頁。 |
| tku-sister-63 拿瓦拉大學 | 指定入口失敗／指定入口失敗 | 0／0 | 真正incoming／院系bilateral agreement資料与當期期限；假設exchange網址正文為404。 |
| tku-sister-44 清州大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | incoming當期指南與適用臺灣學生規則；English sitemap僅degree／general course。校景另需自由重用授權、校區與拍攝年月。 |
| tku-sister-79 加州州立大學 (弗雷斯諾分校) | 已讀無適用正文／已讀無適用正文 | 1／0 | incoming exchange J-1／partner規則与當期提名期限，不能用degree International Office要求。 |
| tku-sister-56 聖湯瑪士大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | incoming programme／partner factsheet；各院contacts不等於交換條件。 |
| tku-sister-23 亞細亞大學 | 已讀無適用正文／已讀無適用正文 | 0／0 | exchange受入規則／年／期限；AUCP出國及International Students degree不適用，最後目錄空體。 |
| tku-sister-22 中央學院大學 | 指定入口失敗／指定入口失敗 | 0／0 | 官方實際國際交流受入資料／學年／deadline；兩條route404且browser TLS失敗；cgu.ac.jp不同臺灣CGU。 |

原39資產缺口逐校停止原因（另兩照片withdrawal不混入原39分母）：

| ID／學校 | 已查新線索或既有原因 |
|---|---|
| tku-sister-339 閩南師範大學 | "闽南师范大学"：HTTP200、0檔；"闽南师范大学"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 |
| tku-sister-332 河內國家大學所屬工業大學 | "VNU University of Engineering and Technology"：HTTP200、0檔；"Đại học Công nghệ" "Hà Nội"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 |
| tku-sister-334 伊達爾戈州自治大學 | TKU地址Campo de Tiro與Wikidata中央La Garza座標不一致，需指定實體校區，不以行政舊址替代。 |
| tku-sister-328 華美中醫學院 | "American College of Acupuncture"：HTTP200、0檔；"American College of Acupuncture and Oriental Medicine"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。；ACAOM英名及精確百科名稱查無可核對實體點；官方acaom.edu HTTP200擷取無命名地圖連結或座標片段，仍需實體校舍數值來源。 |
| tku-sister-322 HZ應用科技大學 | 官方contact／Our campuses實讀：Vlissingen Edisonweg與Middelburg Het Groene Woud按學科分布；exchange programme指定校區與數值點仍未驗，不採任意一住所。 |
| tku-sister-330 西貢國際大學 | 正確SIU母體有點但無官方網址，來源點與原Thao Dien地址／Lewis及Fleming照片場址未對應。 |
| tku-sister-320 柬埔寨IIC 科技大學 | 實際為2008設校核准公函掃描、2014翻譯章，沒有校園景觀；不得當照片或交換表格。 |
| tku-sister-319 阿得雷德大學 | 2026機構合併需核對現官方校區與保留歷史協議，不能自動轉為新大學。 |
| tku-sister-314 卡拉薩琳根學院 | 實際內容為培訓活動海報與人物介紹；不能因檔名Kalasalingam University而當成校園照。 |
| tku-sister-312 巴拉圭發展學院 | "Instituto Desarrollo" "Paraguay"：HTTP200、0檔；"Instituto Desarrollo" "Asunción"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。；Instituto Desarrollo/Paraguay/Asunción查無可核對實體點；官方首頁及contacto HTTP200擷取均無命名地圖或座標片段，不以Asunción市中心補值。 |
| tku-sister-316 西貢文郎大專學院 | "Van Lang Saigon College"：HTTP200、0檔；"Văn Lang Sài Gòn"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。；Van Lang Saigon College英名／別名查無可核對實體點；官方英文站連線由proxy回403而失敗，不能改用Van Lang University母體座標。 |
| tku-sister-289 巴黎歐洲商學院 | "European Business School Paris"：HTTP200、0檔；"EBS Paris"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 |
| tku-sister-307 長安大學 | 長安大學官方校园地图directory實讀，未得單一數值點／交換校區對應，多校區不代選。 |
| tku-sister-287 總統大學 | 精確名稱命中Nissar Ahmed人物與Venugopalaswamy寺廟銘文；不是Presidency Bangalore校園。 |
| tku-sister-288 太原農林大學 | "Thai Nguyen University of Agriculture and Forestry"：HTTP200、0檔；"Đại học Nông Lâm" "Thái Nguyên"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 |
| tku-sister-280 太原大學 | 正確母體Thai Nguyen University Q10841229已查得，但無座標；不得使用農林學院Q10829106的點。 |
| tku-sister-268 里爾大學 | 里爾多個校区及歷史合併機構，不選第一座標。 |
| tku-sister-253 阮必成大學 | 命中Color/Open Day活動、Hana Cam Tien人物及可移動隔間產品；沒有已核對的命名校舍外觀。 |
| tku-sister-275 南十字星大學 | campus檢索無結果，Lismore候選為1944 RAAF飛機／軍人，不是Southern Cross大學。 |
| tku-sister-242 IACT學院 | IACT官方聯絡正文有VSQ@PJ City Block2 Unit13A-01地址，沒有校園數值點；地址或generic SST degree費用公告不當交換費率或定位完成。 |
| tku-sister-216 商業突破大學 | Business Breakthrough University為大學母體；TKU Kenichi Ohmae Graduate School為研究所，尚未核對校區／學制對應。 |
| tku-sister-212 Vel Tech Dr.RR & Dr.SR科技大學 | Campus-vtu已實見為人物宣傳畫面而拒收；Vtmt1僅稱VTMT campus Avadi，未核實與DR.RR/DR.SR大學主體對應。 |
| tku-sister-207 馬拉加大學 | UMA2頁官方map實際視讀，正文未核實獨立年，不能由2025檔名定年；Teatinos／El Ejido／city centre各faculty不同，沒有TKU指定校區，圖上位置不代數值point。 |
| tku-sister-203 巴黎第七大學 | 官方Campus directory多校区；官方連Google map命名Grands Moulins marker48.8292405,2.3817211；@48.8294977,2.3795055只是viewport。舊Diderot協議／校區承繼未驗，marker只存候選。 |
| tku-sister-206 聖路易斯大學 | 命中HUBrussel/Hogeschool-Universiteit Brussel照片及其他文獻／活動，非Université Saint-Louis Bruxelles。 |
| tku-sister-195 法國高等計算機電子及自動化學校 | ESIEA新官方campus-laval alias正文實讀；未獲消除舊JSON-LD與named map經度矛盾的證據，保留既有差異，不改展示坐標。 |
| tku-sister-173 巴拿馬拉丁大學 | ULAT PA-2拍攝欄與EXIF拍攝時間皆空白。年份未核實，停止展示，保留舊圖與查核；新的精確名稱查詢未取得可替代照片。；官方TKU標籤巴拿馬但原地址Paso Canoas Costa Rica與巴拿馬機構不符，保留來源矛盾，不推定接待校區座標。 |
| tku-sister-175 澳門大學 | UM2頁官方map已實際視讀，封面Produced August2026。現有Hengqin主校區與未完工Cooperation Zone新campus不同；map/go跳轉僅JS shell，未提供可採的單一數值point。 |
| tku-sister-169 大阪公立大學 | Q101579967大阪公立大學主體沒有P625；另兩命中分別為附屬醫院Q11440418與高專Q11441055，不能作校級代表點。舊osakafu-u官方端點兩次503歷史保留。 |
| tku-sister-167 雲南大學 | 雲南大學東陸與呈貢多點，需官方校區對應。 |
| tku-sister-155 安徽財經大學 | "Anhui University of Finance and Economics"：HTTP200、0檔；"安徽财经大学"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 |
| tku-sister-166 江西財經大學 | 候選為現代經濟管理學院北門及校徽；前者與TKU名錄江西財經大學主體／地址對應未核實，後者不是校景。 |
| tku-sister-37 平成國際大學 | Hiu-01拍攝欄只有2008原始上傳日、無相機拍攝日期。年份未核實，停止展示，保留舊圖與查核；新的精確名稱查詢未取得可替代照片。 |
| tku-sister-51 英豪多媒體學院 | "IHM College" "Malaysia"：HTTP200、0檔；"In-House Multimedia College"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。；IHM College及Malaysia別名／精確百科名稱未命中；官方ihmc.edu.my HTTP200擷取無命名地圖或座標片段，不用同名他國飯店管理學院的點。 |
| tku-sister-48 韓新傳播學院 | "Hanxing"：HTTP200、0檔；"韩新学院"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 |
| tku-sister-17 巴黎第四大學 | 舊Paris-Sorbonne與2018合併母體、歷史Sorbonne教堂場址需分開；不將歷史點推成當期提名校區。 |
| tku-sister-15 弗朗士孔泰柏桑松大學 | 官方連OSM way32469535實際是Maison des sciences humaines et environnementales Claude Nicolas Ledoux研究建物9nodes；ODbL不解決programme campus，未採任意建物centroid。 |
| tku-sister-44 清州大學 | 命中Miss Korea、演員照片與歌手廣播等人物題材，韓文精確校名未命中校園照片。 |
| tku-programme-mainland-macau-kinmen-115-88b1b8ee97f6 上海交通大學 | 上海交大官方國際處contact頁已實讀，但本輪沒有可核對的命名校區數值點；不能以上海市中心或另一分校替代。 |

本輪到此停止新增候選。35校仍需適用来源、36校外部限制、10來源矛盾與41資產缺口保留精確原因／最低所需資訊；有新官方正文或校方澄清才繼續。
