# 淡江第三輪續補交付（2026-10-11）

分支 `data/tku-completeness-20261011`、repository `blizzard-new/abroad`，沿用 [Draft PR #13](https://github.com/blizzard-new/abroad/pull/13)。本輪基於第二里程碑 `88bd00531d9a77fb98ba54dbfd8786cbde18db96`；最初最新 main 為 `59a20f27fcee00fb597abc79e75ec11778317422`，本輪交付前讀取仍一致。獨立 worktree；未修改臺大工作或其他校別資料、未合併及部署。

286筆姊妹校名錄與既有交換名單聯集仍為287所；153筆計畫保留原128筆，新增的25筆日本第一輪、50名額是已截止歷史。最新日語第二輪4校7名額，淡江2026/9/23–9/30中午（Asia/Taipei）校內期限已截止：**0筆新開放母校申請**。交換期2027/4–2028/3，不預設為2027秋。283所其餘名額仍149筆尚未核實新版、134筆參考；缺值不轉為0。英文組及陸港澳金門116新版仍是「尚未核實新版」，沒有官方明示尚未公告的新增證據。

| 項目 /287 | 第二里程碑 | 本輪 | 含義 |
|---|---:|---:|---|
| 可展示照片 | 264 | 264（91.99%） | 本輪全數具核對拍攝期、授權及實際校景 |
| 有來源座標 | 260 | 264（91.99%） | 9個命名實體點、255個代表點；非TKU分配校區 |
| 官方原文／精讀機構 | 139 | 189 | 2350段一般原文索引，未自動當本期規則 |
| 精讀正文機構／欄位 | 2 /26 | 20 /151 | 含未載年度一般參考 |
| 明確來源年期機構／欄位 | 2 /26 | 8 /85 | 包含歷史2026，不代表全為新版 |

## 正文、年期及計畫範圍

每個精讀欄位保存官方URL、實際原文／PDF實體頁碼、SHA256、適用年期、查核時間、接待角色與未核實TKU對應的限制。新增18所125欄，加原明治／日本女子26欄，共151欄。

| 精讀學校 | 欄位 | 年期已知欄 | 來源年期／適用限制 |
|---|---:|---:|---|
| 明治大學 | 14 | 14 | 2027 academic year; host incoming exchange only |
| 日本女子大學 | 12 | 12 | 2027–2028 host incoming programme; TKU nomination unverified |
| 巴塞隆納自治大學 | 10 | 10 | 2026/27 host incoming Fact Sheet, updated July 2026; not TKU 116 quota |
| 薩蘭大學 | 12 | 11 | 2027/28 Overseas exchange host Fact Sheet; TKU nomination unverified |
| 長崎外國語大學 | 12 | 12 | 2027 Spring NICS semester/year incoming; TKU nomination unverified |
| Vel Tech Dr.RR & Dr.SR科技大學 | 8 | 0 | undated incoming exchange FAQ; checked 2026-10-11; 2027 degree-admission footer excluded |
| 韓新傳播學院 | 3 | 0 | undated general hostel webpage; checked 2026-10-11; prices subject to change, exchange allocation unknown |
| 布蘭登大學 | 3 | 0 | undated host exchange/general admission policy; explicit TOEFL Jan2026 change kept separately; TKU cycle unverified |
| 慕尼黑大學 | 9 | 0 | undated Erasmus/UK/SEMP/LMUexchange host rules checked 2026-10-11; 2026 courses only examples |
| 穆爾西亞大學 | 1 | 0 | undated general SIU accommodation service checked 2026-10-11 |
| HZ應用科技大學 | 3 | 0 | undated general campus identity checked 2026-10-11 |
| 貝爾格拉諾大學 | 4 | 0 | undated incoming PEAL/PALAS semester programme; TKU track and current year unverified |
| 農業大學 | 5 | 0 | undated fee-paying Visiting Student KUSEP track; TKU bilateral fee waiver and programme mapping unverified |
| 土庫大學 | 10 | 0 | undated incoming exchange FAQ/health rules checked 2026-10-11; precise academic year and TKU nomination unverified |
| 哈西德佩大學 | 3 | 0 | undated Hacettepe bilateral visiting semester exchange rules checked 2026-10-11; TKU cycle unverified |
| 立命館大學 | 13 | 13 | 2027 Spring SKP official semester application guidelines; TKU nomination/track/quota unverified |
| 布魯塞爾自由大學 | 8 | 3 | undated VUB incoming exchange website; TKU nomination and specific academic year unverified |
| 津田塾大學 | 9 | 0 | undated Tsuda incoming exchange/general support webpages checked2026-10-11; TKU nomination and semester year unverified |
| 基輔大學 | 2 | 0 | undated general international-student housing page checked2026-10-11; current price year and TKU exchange allocation unverified |
| 北京航空航天大學 | 10 | 10 | 2026 Spring/Fall historical international General Scholar/Exchange page; TKU mainland programme route and2027 mapping unverified |

立命館SKP實讀2027春22頁指南與語言PDF，GPA、track／校區、10/22提名及11/2接待申請期限、課程、費用、獎學金、COE與住宿階段分開；不產生TKU新申請。長崎NICS實讀2027春8份附件及12欄，模板矛盾／未載年期保留；原14個profile段落不改，只在API附12個接待參考段落。UAB2026/27、VUB2026/27、北航2026歷史頁不是TKU116新版；Saar2027/28住宿頁仍未載年期。

土庫實讀語言Assessment DOC及兩種Learning Agreement DOCX。TOEFL頁標題ITP／內文iBT、Jan26切換日與其他校Jan21，以及學士可選碩士課年級差異留為待確認。津田1頁文件清單、5頁brochure與網站均實讀；N5是日語預備課豁免條件，不當全員統一門檻，2023課表只供歷史參考；指定Excel與online表須母校提供，未宣稱已取得。

遼寧DOC用已安裝LibreOffice讀到2026博士全學位獎學金，已排除。土庫與北航DOC在隔離臨時profile、巨集安全3及停用外連更新下轉出4份PDF，共7頁，原DOC與失敗解析捕捉不改。沒有文件內互動或提出網路操作；工具設定不是量測網路流量證據。北航實讀普通進修Form004及體檢PDF，排除高級進修Form005、語言研修Form006與四年本科10萬／12萬RMB財力表；國際General Scholar是否適用TKU陸港澳金門route仍未知。

2435次接待來源捕捉歷史中2080次HTTP200且沒有錯誤、355次失敗或非200（202×7、503×281、403×23、404×24、連線×17、412／500／302各1）。這包括重試與離線衍生捕捉，不等同2435份不同當期文件；HTTP200也不等於全文／年期精讀。126次附件捕捉實際magic與SHA通過，115個唯一URL、114個唯一原始SHA；離線衍生PDF4份另列。

## 照片與實體座標

原264張照片再查拍攝期：247張可核實，12張年份未知、5張日期矛盾先停止展示；取得15張合格替代。平成國際與巴拿馬拉丁仍因只有上傳日／無拍攝證據而隱藏，另外新增同塔與UAEMEX兩所合格校景，合计仍264張（53張逐校重用、211張新素材）。所有被拒／舊檔保留，只展示拍攝期與授權均核實者；授權與年份未知不展示。

新增CityU Macau氹仔、加拿大York Keele、韓新Cheras、Laurea Leppävaara命名點，區分實際地標與地圖視窗。ESIEA Laval同官方頁JSON-LD和命名地標經度矛盾暫不收；IACT粗點與現址不對應、OMU母體無點且醫院／高專不可替代。所有照片校區、代表點、實體點與TKU實際提名校區分開。

## 實際驗證

- 最終200項選定單元／離線/API／TKU、共用school/regions/fit、CGU與NTPU套件：**196 passed、4 skipped、0 failed／error，87.80秒**。4項是CGU既有`Phase C data reviewed`跳過；未當通過。
- 真實Chromium390及1280寬：**2 passed，40.77秒**，264張全部decode、授權與拍攝期狀態通過；264點、255代表點、無水平溢出及console错误。
- `git diff --check`、`node --check`、`export_openapi.py --check`通過。
- CGU3、NTPU12、NTU17、CCU1215、NCU13個官方檔逐位元組等於main基準；TKU原4份profile前綴相同。
- 僅靠26個傳輸分片還原4219份檔案，共198,927,161 bytes；分片、11個ZIP及每個成員SHA與bytes通過。第二里程碑3616檔／7包不變，只追加603檔／4包。
- 本輪初次4失敗／152通過，調整後1失敗／155通過，修正7例通過、後續156例全通過的XML均保留；最終擴充200例結果以上。profile建置命令曾因缺`PYTHONPATH=src`報ModuleNotFoundError，補設定重跑exit0；不隱藏實際錯誤。
- 沒有本輪全repo全綠宣稱。早期全repo latest-case accounting2643 passed／15 skipped／2 failed仍是歷史，兩項NTU測試硬編碼另一session缺失路徑；未修改臺大測試或建立該路徑。

## 合併界面与未解項

本輪production僅變更TKU獨立`tku_assets.py`與`tku-campus-assets.js`（年份展示門檻、NICS接待參考），資料與抓取／解析／驗收均校別獨立。本輪沒有新增共用核心修改。整份PR相對main需主整合者處理的共用檔為`api.py`（TKU條件資產／coverage）、`school_content.py`（TKUdispatch）、`static/index.html`（載入模組）、`static/regions.js`（臺灣拼字、巴拉圭／馬拉威）、`docs/api/openapi.json`（索引端點）及`test_fit_signals.py`／`test_school_completeness.py`數量斷言。registry、共用eligibility/documents/models沒有新增本期規則。

固定287×22＝6314欄仍逐校保留狀態，不以照片／一般原文當資格完成率。原4校63缺口、18矛盾未被新參考層掩蓋；院系舊時程與中央更正不猜合併。尚缺照片23、座標23，涉及39所，下列逐校理由的URL、原文、查核時間和SHA見[機讀缺口](../src/exchange_info/official_data/tku/milestone3_asset_gap_reviews.json)。

98所尚無可用官方索引欄位；20所共69個未讀候選（39國際目錄、9事件／人物、10可能全學位招生、6歷史教材、5計畫範圍待讀），完整清單與原捕捉見[剩餘triage](../src/exchange_info/official_data/tku/milestone3_remaining_triage.json)。此為尚未完成的讀取，不是官方尚未公告，也不保證候選含適用交換資料。

| 學校 | 尚缺照片的實際原因 | 尚缺座標的實際原因 |
|---|---|---|
| 閩南師範大學 | "闽南师范大学"：HTTP200、0檔；"闽南师范大学"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 已核對 |
| 河內國家大學所屬工業大學 | "VNU University of Engineering and Technology"：HTTP200、0檔；"Đại học Công nghệ" "Hà Nội"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 已核對 |
| 伊達爾戈州自治大學 | 已核對 | TKU地址Campo de Tiro與Wikidata中央La Garza座標不一致，需指定實體校區，不以行政舊址替代。 |
| 華美中醫學院 | "American College of Acupuncture"：HTTP200、0檔；"American College of Acupuncture and Oriental Medicine"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | ACAOM英名及精確百科名稱查無可核對實體點；官方acaom.edu HTTP200擷取無命名地圖連結或座標片段，仍需實體校舍數值來源。 |
| HZ應用科技大學 | 實際為HZ logo，沒有校園場景。 | 正確HZ機構Q2518381存在，但沒有座標；不猜補城市中心。 |
| 西貢國際大學 | 已核對 | 正確SIU母體有點但無官方網址，來源點與原Thao Dien地址／Lewis及Fleming照片場址未對應。 |
| 柬埔寨IIC 科技大學 | 實際為2008設校核准公函掃描、2014翻譯章，沒有校園景觀；不得當照片或交換表格。 | 已核對 |
| 阿得雷德大學 | 已核對 | 2026機構合併需核對現官方校區與保留歷史協議，不能自動轉為新大學。 |
| 卡拉薩琳根學院 | 實際內容為培訓活動海報與人物介紹；不能因檔名Kalasalingam University而當成校園照。 | 已核對 |
| 巴拉圭發展學院 | "Instituto Desarrollo" "Paraguay"：HTTP200、0檔；"Instituto Desarrollo" "Asunción"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | Instituto Desarrollo/Paraguay/Asunción查無可核對實體點；官方首頁及contacto HTTP200擷取均無命名地圖或座標片段，不以Asunción市中心補值。 |
| 西貢文郎大專學院 | "Van Lang Saigon College"：HTTP200、0檔；"Văn Lang Sài Gòn"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | Van Lang Saigon College英名／別名查無可核對實體點；官方英文站連線由proxy回403而失敗，不能改用Van Lang University母體座標。 |
| 巴黎歐洲商學院 | "European Business School Paris"：HTTP200、0檔；"EBS Paris"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 已核對 |
| 長安大學 | 已核對 | 正確長安大學母體Q5071561與Yanta分校命中，均無座標；不換用另一分校。 |
| 總統大學 | 精確名稱命中Nissar Ahmed人物與Venugopalaswamy寺廟銘文；不是Presidency Bangalore校園。 | 已核對 |
| 太原農林大學 | "Thai Nguyen University of Agriculture and Forestry"：HTTP200、0檔；"Đại học Nông Lâm" "Thái Nguyên"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 已核對 |
| 太原大學 | 已核對 | 正確母體Thai Nguyen University Q10841229已查得，但無座標；不得使用農林學院Q10829106的點。 |
| 里爾大學 | 已核對 | 里爾多個校区及歷史合併機構，不選第一座標。 |
| 阮必成大學 | 命中Color/Open Day活動、Hana Cam Tien人物及可移動隔間產品；沒有已核對的命名校舍外觀。 | 已核對 |
| 南十字星大學 | campus檢索無結果，Lismore候選為1944 RAAF飛機／軍人，不是Southern Cross大學。 | 已核對 |
| IACT學院 | "IACT College"：HTTP200、0檔；"IACT" "Malaysia"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 官方當前地址為VSQ@PJ City Centre；Q16253618唯一點3.1182,101.635精度0.009度且无P856，沒有與現行校舍對應的細點，不以粗點當命名校園。 |
| 商業突破大學 | 已核對 | Business Breakthrough University為大學母體；TKU Kenichi Ohmae Graduate School為研究所，尚未核對校區／學制對應。 |
| Vel Tech Dr.RR & Dr.SR科技大學 | Campus-vtu已實見為人物宣傳畫面而拒收；Vtmt1僅稱VTMT campus Avadi，未核實與DR.RR/DR.SR大學主體對應。 | 已核對 |
| 馬拉加大學 | 已核對 | 泛校級座標可能為市中心行政址，需官方地址／實體校區佐證。 |
| 巴黎第七大學 | 已核對 | TKU舊Paris Diderot与Paris Cité合併母體／校區未對應，不替換為巴黎笛卡爾校址。 |
| 聖路易斯大學 | 命中HUBrussel/Hogeschool-Universiteit Brussel照片及其他文獻／活動，非Université Saint-Louis Bruxelles。 | 已核對 |
| 法國高等計算機電子及自動化學校 | 已核對 | 同一官方Laval校区頁JSON-LD與其嵌入命名地標經度矛盾，暫不納入座標；地圖視窗也不是地標。 |
| 巴拿馬拉丁大學 | ULAT PA-2拍攝欄與EXIF拍攝時間皆空白。年份未核實，停止展示，保留舊圖與查核；新的精確名稱查詢未取得可替代照片。 | 官方TKU標籤巴拿馬但原地址Paso Canoas Costa Rica與巴拿馬機構不符，保留來源矛盾，不推定接待校區座標。 |
| 澳門大學 | 已核對 | 澳門大學新橫琴與舊氹仔兩點不能直接選首個，需官方新校區命名與行政地理區別。 |
| 大阪公立大學 | 已核對 | Q101579967大阪公立大學主體沒有P625；另兩命中分別為附屬醫院Q11440418與高專Q11441055，不能作校級代表點。舊osakafu-u官方端點兩次503歷史保留。 |
| 雲南大學 | 已核對 | 雲南大學東陸與呈貢多點，需官方校區對應。 |
| 安徽財經大學 | "Anhui University of Finance and Economics"：HTTP200、0檔；"安徽财经大学"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 已核對 |
| 江西財經大學 | 候選為現代經濟管理學院北門及校徽；前者與TKU名錄江西財經大學主體／地址對應未核實，後者不是校景。 | 已核對 |
| 平成國際大學 | Hiu-01拍攝欄只有2008原始上傳日、無相機拍攝日期。年份未核實，停止展示，保留舊圖與查核；新的精確名稱查詢未取得可替代照片。 | 已核對 |
| 英豪多媒體學院 | "IHM College" "Malaysia"：HTTP200、0檔；"In-House Multimedia College"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | IHM College及Malaysia別名／精確百科名稱未命中；官方ihmc.edu.my HTTP200擷取無命名地圖或座標片段，不用同名他國飯店管理學院的點。 |
| 韓新傳播學院 | "Hanxing"：HTTP200、0檔；"韩新学院"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 已核對 |
| 巴黎第四大學 | 已核對 | 舊Paris-Sorbonne與2018合併母體、歷史Sorbonne教堂場址需分開；不將歷史點推成當期提名校區。 |
| 弗朗士孔泰柏桑松大學 | 已核對 | Franche-Comté與Marie and Louis Pasteur新母體及官方域名已不同，先核實現官方校區／保留歷史機構。 |
| 清州大學 | 命中Miss Korea、演員照片與歌手廣播等人物題材，韓文精確校名未命中校園照片。 | 已核對 |
| 上海交通大學 | 已核對 | 上海交大官方國際處contact頁已實讀，但本輪沒有可核對的命名校區數值點；不能以上海市中心或另一分校替代。 |

[本輪結果JSON](tku-continuation-milestone3-20261011.json) · [287校完整度／來源](../src/exchange_info/official_data/tku/continuation_gap_closure.json) · [JUnit、瀏覽器畫面、雜湊清單及pack-only證據](tku-census-evidence-20261011/milestone3-evidence-manifest.json)。最終推送固定commit與PR head比對由交接回報與PR body提供；不合併或部署。
