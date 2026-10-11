# 淡江第四次交付：固定69候選正文與平台適配

Repository `blizzard-new/abroad`，分支 `data/tku-completeness-20261011`；延續已交付 `563fb9328c7ce15efc1ac3883d8c3d641df01e98`，main基準 `59a20f27fcee00fb597abc79e75ec11778317422`。仅同一 [Draft PR13](https://github.com/blizzard-new/abroad/pull/13)，固定交付SHA見最終回報／遠端分支；本報告在提交前生成。未merge／部署。

固定69個候選全數交代：68 HTTP200、1 HTTP404；64讀完完整可取得正文，4只有標題／JavaScript外殼，1未取得內容。HTTP200不等於讀到規則；capture mode允許已保存的immutable cache，沒有宣稱69個新GET。沿實際正文連結另外查22個來源，21 HTTP200、1 Lyon住房連線逾時。

新增8校45個逐欄正文參考，197校有官方參考；287校／153計畫／287profiles不變。一般2350段原文索引與精讀28校196欄分開。來源年期明確11校111欄包含歷史2026/27；上一批8校85欄、20校151欄逐項相同，沒有改稱淡江本期核實。最新4校7名額母校第二梯已截止，0筆新開放；其餘283校名額仍未核實当期。

## 新增內容與適用限制

| 機構 | 欄位數 | 已讀官方依據與限制 |
|---|---:|---|
| 巴拿馬科技大學 | 13 | [2027incoming網頁＋實載2026–2027的23頁Fact Sheet＋2份学年度空白DOCX。精確2027/1/14、7/1期限與PDF概略月份差異保留；B1–B2西語、最多5門／一院／三degree plans。容量不是TKU名額；宿舍未保證。](https://utp.ac.pa/movilidad-internacional-del-exterior-hacia-la-utp-estudiantes) |
| 波昂大學 | 12 | [Global Exchange Fact Sheet2026/27共9頁；公開臺灣partner只有臺大、政大，沒有淡江。這是該programme名單觀察，不證明無校級協議。醫牙排除、GPA、語言、期限與費用僅接待參考。](https://www.uni-bonn.de/en/studying/international-students/exchange-students/global-exchange-program/download/fact-sheet-global-exchange-program.pdf) |
| 里昂第三大學 | 8 | [SELF2026/27、DEUF2026秋分開；SELF頁與交換語言頁TOEFL版本矛盾待校方確認。DEUF2027春精確日期正文明示à venir，SELF已列2027春日期，不能混用；自費模板／截止排除。](https://www.univ-lyon3.fr/self-study-in-english-in-lyon-france) |
| 貴州大學 | 6 | [中／英舊brochure，正文2018統計、官方連結頁2019；一般國際生住房350／500／800RMB、保險及餐費是歷史未載學年度參考，不是2027報價。Degree HSK与degree／語言班截止不作交換規則。](https://cie.gzu.edu.cn/_upload/article/files/db/d1/77cee03846f4988c77bb24155a48/eeecdd54-cd0a-4adf-943b-06e778471bdc.pdf) |
| 普瓦捷大學 | 2 | [未載年份的交換站點迎接與SURIEE支援；不保證2027接送，辦公室不作授課校區。](https://www.univ-poitiers.fr/souvrir-a-linternational/lesprit-grand-ouvert/linternational-inscrit-dans-ladn-de-luniversite/) |
| 麗澤大學 | 2 | [RIFA及日語中心一般支援；2025活動135人不當名額，JLPT/BJT準備班不當入學門檻。](https://www.reitaku-u.ac.jp/en/global/conversation-partnership/) |
| 斯德哥爾摩大學 | 1 | [多數exchange由department執行；須另核對TKU全校／院系協議。](https://www.su.se/english/about-the-university/collaboration-and-societal-development/an-international-university) |
| 弗朗士孔泰柏桑松大學 | 1 | [現UMLP DREIF incoming支援；舊Franche-Comté協議承繼與校區尚未核實，不套用outgoing補助。](https://www.umlp.fr/taxonomy/term/294/) |

所有重要新欄保存URL、PDF實體頁碼／原文、SHA、適用期、來源角色與查核日；見 `milestone4_reviewed_host_facts.json`。表格已開啟且magic/SHA驗證，接待表未加入淡江母校application document catalog。UTP manuals頁明文禁止未經書面許可重製／分享，僅諮詢公開HTML，沒有下載或再發布該manual PDF。

## 測試與資料重建

最終選定測試：201 passed、4 skipped、0 failed/errors，79.726秒；CGU16、NTPU11通過已包含總數。跳過4項是CGU既有Phase C data reviewed，沒有宣稱全repo全綠。
真實Chromium390／1280：4 passed、0 failed，78.832秒。四校接待正文／來源年份卡片实际可展開，null名額與不可加入正式申請保留；264圖片全decode／授權／拍攝期与264座標（255代表）通過，無console錯誤／頁面溢出。
九個重建／audit／pack命令皆exit0，12個產物前後SHA完全相同。git diff --check、app.js與新模組node --check、OpenAPI export --check通過。CGU3/NTPU12/NTU17/CCU1215/NCU13官方檔與main基準逐位元組一致；原128計畫／4profile前綴、63缺口／18矛盾保留。
分片獨立還原：4326份檔案、12ZIP、29parts、220,426,072bytes；SHA／bytes逐檔通過。相對563只追加107檔／1ZIP／3parts，原4219檔／11ZIP不可變。
第一次focused1失敗4通過、第一次browser2失敗2通過、第一次廣測1失敗200通過4跳過的日誌／XML完整保留。Browser揭露中正renderer錯用與期限被隱藏；已用淡江模組修正。廣測失敗是JS測試未載新模組，改成載實際模組並斷言未核實≠未公告。PDF Unicode分行字元造成JSONL初次失敗，已以等價JSON escape保存，不改證據文字。

## 98校參考缺口逐校交接

上一批20校69候選：8校新增參考、12校已讀候選但無適用內容或正文取不到。上一批54個HTTP200機構中，47有可讀正文待定位incoming；7其實是挑戰、登入或無實質外殼。另24校沒有成功200，實際錯誤逐URL留存。合計仍90校無可用參考。
可讀未完成programme精讀與外部取得失敗分開；這份表沒有宣稱全網官方替代路徑耗盡。完整來源URL／時間／SHA／HTTP／錯誤見 `milestone4_remaining_source_limits.json`。

| 機構 | 上批組別 | 本輪結果 | 來源開啟／正文狀態 |
|---|---|---|---|
| 清奈理工學院 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 河內國家大學所屬工業大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP403 external_open_failure |
| 伊達爾戈州自治大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 華美中醫學院 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 西貢國際大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 柬埔寨IIC 科技大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 巴拉圭發展學院 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 麻州大學羅爾分校 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 西貢文郎大專學院 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTPNone external_open_failure |
| 金山大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 阿根廷企業大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 合肥工業大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 布達佩斯商學院 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 堪薩斯州立大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 太原大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure；HTTPNone external_open_failure |
| 國民經濟大學 | 54_http200_capture_schools_without_rule_candidate | 外部失敗／挑戰／登入／空殼 | HTTP200 empty_or_shell_body |
| 德州大學阿靈頓分校 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 威洛爾理工學院 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP403 external_open_failure |
| 重慶大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| SRM大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP403 external_open_failure |
| 泗水理工學院 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 羅馬大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 阮必成大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 華南理工大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 華中師範大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 蘇州大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP200 empty_or_shell_body |
| 香港科技專上書院 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 芝浦工業大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP404 external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 印度尼西亞大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 商業突破大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP404 external_open_failure |
| 滁州學院 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 宋卡王子大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTPNone external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 普瓦捷大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP404 external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 巴黎第七大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 聖路易斯大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTPNone external_open_failure |
| 貴州大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP503 external_open_failure |
| 國立歐亞大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP503 external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 德州大學聖安東尼奧分校 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 國立亞松森大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP200 empty_or_shell_body |
| 福建師範大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 國立金門大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 穆罕默迪大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 尼赫魯大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP404 external_open_failure |
| 雙威大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP404 external_open_failure；HTTPNone external_open_failure |
| 華僑大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP503 external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 巴拿馬拉丁大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTPNone external_open_failure |
| 漢陽大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP302 external_open_failure |
| 大阪公立大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP503 external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 雲南大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 馬來西亞拉曼大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 蒙古國立大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 蘭州大學   //  兰州大学 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP412 external_open_failure |
| 福岡女子大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 波莫納加州州立理工大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 卡斯蒂利亞拉曼恰大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP403 external_open_failure |
| 浙江大學 | 54_http200_capture_schools_without_rule_candidate | 外部失敗／挑戰／登入／空殼 | HTTP200 empty_or_shell_body |
| 中南財經政法大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTPNone external_open_failure |
| 安徽財經大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP403 external_open_failure |
| 美利堅大學 | 54_http200_capture_schools_without_rule_candidate | 外部失敗／挑戰／登入／空殼 | HTTP200 empty_or_shell_body |
| 巴比波里亞大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 巴拿馬大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP404 external_open_failure |
| 密西根大學福林特分校 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 會津大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 巴拿馬科技大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 平成國際大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 國際教養大學 | 54_http200_capture_schools_without_rule_candidate | 外部失敗／挑戰／登入／空殼 | HTTP200 empty_or_shell_body |
| 卡查馬達大學 | 54_http200_capture_schools_without_rule_candidate | 外部失敗／挑戰／登入／空殼 | HTTP200 login_body_not_public_rule |
| 英豪多媒體學院 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP403 external_open_failure |
| 武漢理工大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP200 empty_or_shell_body |
| 青山學院大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 北京大學 | 20_schools_69_candidates | 固定候選已讀完／取不到，無適用參考 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP503 external_open_failure |
| 華沙大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 賓州印第安那大學 | 54_http200_capture_schools_without_rule_candidate | 外部失敗／挑戰／登入／空殼 | HTTP200 empty_or_shell_body |
| 馬拉威大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 里昂第三大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTPNone external_open_failure；HTTP503 external_open_failure |
| 巴黎第四大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 亞瑟柏大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 波昂大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 美國三一學院 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 南京航空航天大學 | 54_http200_capture_schools_without_rule_candidate | 外部失敗／挑戰／登入／空殼 | HTTP200 empty_or_shell_body |
| 莫斯科國立語言大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 西北工業大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 墨西哥州立自治大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 遠東聯邦大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTPNone external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP403 external_open_failure |
| 斯德哥爾摩大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 弗朗士孔泰柏桑松大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 拿瓦拉大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 拉薩大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP403 external_open_failure |
| 清州大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP403 external_open_failure；HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 加州州立大學 (弗雷斯諾分校) | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 哥斯大黎加大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP503 external_open_failure；HTTPNone external_open_failure |
| 聖湯瑪士大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 麗澤大學 | 20_schools_69_candidates | 已補接待參考；TKU本期未核實 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP503 external_open_failure |
| 西佛羅里達大學 | 24_no_successful_http200_capture_schools | 外部失敗／挑戰／登入／空殼 | HTTP503 external_open_failure |
| 華盛頓州立大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed；HTTP403 external_open_failure |
| 檀國大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 亞細亞大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |
| 中央學院大學 | 54_http200_capture_schools_without_rule_candidate | 可讀正文；incoming定位／精讀未完成 | HTTP200 public_extracted_body_available_programme_scope_review_needed |

亞松森協議目錄HTTP200只回 `.::CONVENIO::.` JavaScript外殼；正常Chromium實際 `ERR_CERT_AUTHORITY_INVALID`，未停用HTTPS驗證。沒有宣稱讀到協議表或推定當期名額。

## 照片23／座標23：39校逐校實際安全來源限制

照片是在已保存的精確英／native名稱查詢、命名Commons分類與實見候選集合内無合格素材；不代表所有官方圖片沒有授權。未證明全網安全來源耗盡，也不需要無限重查已拒用素材。
座標23校的全部已保存Wikidata候選entity claims附於逐校JSON，14校身份／校區／合併矛盾、9校無可核對數值點。Adelaide官方命名公開uMap尚未實讀，安全來源沒有耗盡；合併機構適用仍須確認。ESIEA命名地標已讀，但官方JSON-LD與地標經度矛盾，保留缺值。

| 機構 | 照片：實際結果 | 座標：實際結果／仍可查項 |
|---|---|---|
| 閩南師範大學 | "闽南师范大学"：HTTP200、0檔；"闽南师范大学"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | — |
| 河內國家大學所屬工業大學 | "VNU University of Engineering and Technology"：HTTP200、0檔；"Đại học Công nghệ" "Hà Nội"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | — |
| 伊達爾戈州自治大學 | — | TKU地址Campo de Tiro與Wikidata中央La Garza座標不一致，需指定實體校區，不以行政舊址替代。 |
| 華美中醫學院 | "American College of Acupuncture"：HTTP200、0檔；"American College of Acupuncture and Oriental Medicine"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | ACAOM英名及精確百科名稱查無可核對實體點；官方acaom.edu HTTP200擷取無命名地圖連結或座標片段，仍需實體校舍數值來源。 |
| HZ應用科技大學 | 實際為HZ logo，沒有校園場景。 | 正確HZ機構Q2518381存在，但沒有座標；不猜補城市中心。 |
| 西貢國際大學 | — | 正確SIU母體有點但無官方網址，來源點與原Thao Dien地址／Lewis及Fleming照片場址未對應。 |
| 柬埔寨IIC 科技大學 | 實際為2008設校核准公函掃描、2014翻譯章，沒有校園景觀；不得當照片或交換表格。 | — |
| 阿得雷德大學 | — | 2026機構合併需核對現官方校區與保留歷史協議，不能自動轉為新大學。 Known public Adelaide named map not body-reviewed; institution merger already blocks automatic coordinate acceptance |
| 卡拉薩琳根學院 | 實際內容為培訓活動海報與人物介紹；不能因檔名Kalasalingam University而當成校園照。 | — |
| 巴拉圭發展學院 | "Instituto Desarrollo" "Paraguay"：HTTP200、0檔；"Instituto Desarrollo" "Asunción"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | Instituto Desarrollo/Paraguay/Asunción查無可核對實體點；官方首頁及contacto HTTP200擷取均無命名地圖或座標片段，不以Asunción市中心補值。 |
| 西貢文郎大專學院 | "Van Lang Saigon College"：HTTP200、0檔；"Văn Lang Sài Gòn"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | Van Lang Saigon College英名／別名查無可核對實體點；官方英文站連線由proxy回403而失敗，不能改用Van Lang University母體座標。 |
| 巴黎歐洲商學院 | "European Business School Paris"：HTTP200、0檔；"EBS Paris"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | — |
| 長安大學 | — | 正確長安大學母體Q5071561與Yanta分校命中，均無座標；不換用另一分校。 |
| 總統大學 | 精確名稱命中Nissar Ahmed人物與Venugopalaswamy寺廟銘文；不是Presidency Bangalore校園。 | — |
| 太原農林大學 | "Thai Nguyen University of Agriculture and Forestry"：HTTP200、0檔；"Đại học Nông Lâm" "Thái Nguyên"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | — |
| 太原大學 | — | 正確母體Thai Nguyen University Q10841229已查得，但無座標；不得使用農林學院Q10829106的點。 |
| 里爾大學 | — | 里爾多個校区及歷史合併機構，不選第一座標。 |
| 阮必成大學 | 命中Color/Open Day活動、Hana Cam Tien人物及可移動隔間產品；沒有已核對的命名校舍外觀。 | — |
| 南十字星大學 | campus檢索無結果，Lismore候選為1944 RAAF飛機／軍人，不是Southern Cross大學。 | — |
| IACT學院 | "IACT College"：HTTP200、0檔；"IACT" "Malaysia"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | 官方當前地址為VSQ@PJ City Centre；Q16253618唯一點3.1182,101.635精度0.009度且无P856，沒有與現行校舍對應的細點，不以粗點當命名校園。 |
| 商業突破大學 | — | Business Breakthrough University為大學母體；TKU Kenichi Ohmae Graduate School為研究所，尚未核對校區／學制對應。 |
| Vel Tech Dr.RR & Dr.SR科技大學 | Campus-vtu已實見為人物宣傳畫面而拒收；Vtmt1僅稱VTMT campus Avadi，未核實與DR.RR/DR.SR大學主體對應。 | — |
| 馬拉加大學 | — | 泛校級座標可能為市中心行政址，需官方地址／實體校區佐證。 |
| 巴黎第七大學 | — | TKU舊Paris Diderot与Paris Cité合併母體／校區未對應，不替換為巴黎笛卡爾校址。 |
| 聖路易斯大學 | 命中HUBrussel/Hogeschool-Universiteit Brussel照片及其他文獻／活動，非Université Saint-Louis Bruxelles。 | — |
| 法國高等計算機電子及自動化學校 | — | 同一官方Laval校区頁JSON-LD與其嵌入命名地標經度矛盾，暫不納入座標；地圖視窗也不是地標。 ESIEA named landmark read; numeric conflict retained in milestone3_geography_review.json |
| 巴拿馬拉丁大學 | ULAT PA-2拍攝欄與EXIF拍攝時間皆空白。年份未核實，停止展示，保留舊圖與查核；新的精確名稱查詢未取得可替代照片。 | 官方TKU標籤巴拿馬但原地址Paso Canoas Costa Rica與巴拿馬機構不符，保留來源矛盾，不推定接待校區座標。 |
| 澳門大學 | — | 澳門大學新橫琴與舊氹仔兩點不能直接選首個，需官方新校區命名與行政地理區別。 |
| 大阪公立大學 | — | Q101579967大阪公立大學主體沒有P625；另兩命中分別為附屬醫院Q11440418與高專Q11441055，不能作校級代表點。舊osakafu-u官方端點兩次503歷史保留。 |
| 雲南大學 | — | 雲南大學東陸與呈貢多點，需官方校區對應。 |
| 安徽財經大學 | "Anhui University of Finance and Economics"：HTTP200、0檔；"安徽财经大学"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | — |
| 江西財經大學 | 候選為現代經濟管理學院北門及校徽；前者與TKU名錄江西財經大學主體／地址對應未核實，後者不是校景。 | — |
| 平成國際大學 | Hiu-01拍攝欄只有2008原始上傳日、無相機拍攝日期。年份未核實，停止展示，保留舊圖與查核；新的精確名稱查詢未取得可替代照片。 | — |
| 英豪多媒體學院 | "IHM College" "Malaysia"：HTTP200、0檔；"In-House Multimedia College"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | IHM College及Malaysia別名／精確百科名稱未命中；官方ihmc.edu.my HTTP200擷取無命名地圖或座標片段，不用同名他國飯店管理學院的點。 |
| 韓新傳播學院 | "Hanxing"：HTTP200、0檔；"韩新学院"：HTTP200、0檔。本輪具體查詢未取得同時符合身份、校景、授權與拍攝年的可展示候選；不宣稱所有網站都沒有照片。 | — |
| 巴黎第四大學 | — | 舊Paris-Sorbonne與2018合併母體、歷史Sorbonne教堂場址需分開；不將歷史點推成當期提名校區。 |
| 弗朗士孔泰柏桑松大學 | — | Franche-Comté與Marie and Louis Pasteur新母體及官方域名已不同，先核實現官方校區／保留歷史機構。 |
| 清州大學 | 命中Miss Korea、演員照片與歌手廣播等人物題材，韓文精確校名未命中校園照片。 | — |
| 上海交通大學 | — | 上海交大官方國際處contact頁已實讀，但本輪沒有可核對的命名校區數值點；不能以上海市中心或另一分校替代。 |

每校實際Commons URL、查詢結果、visual拒用、拍攝期hold、官方地圖入口、Wikidata P625/P856/P17、來源SHA與查核時間皆在 `milestone4_asset_source_limits.json`。沒有以第一點、城市中心、醫院、高專、舊／新母體或其他分校替代。

## 合併所需共用檔變更

本輪 `static/app.js` 只加淡江分支：協議／名額「本期未核實」、接待來源renderer、保留完整profile指南，避開中正专用文案；`static/index.html`在app前載入新 `static/tku-partner-details.js`。`tests/test_tku_support.py`更新既有JS harness，載入真實淡江模組。學校資料及所有新查核／限制程式保持TKU獨立。
本輪沒有registry、API schema、共用資格／文件catalog規則、安全設定、憑證或權限變更。整份Draft先前的共用核心改動仍須由主session統一合併，見第三次報告；未動臺大或他校工作目錄。

機讀報告：`tku-continuation-milestone4-20261011.json`。每份XML、日誌、重建、pack-only、preservation與四校UI截圖雜湊：`tku-census-evidence-20261011/milestone4-evidence-manifest.json`。

原始失敗日誌／JUnit含尾端空白，staged whitespace檢查實際曾exit2。僅該4份log/XML（實際檔數以manifest為準）無損GZIP封裝，解壓逐byte／SHA等同原輸出，保留失敗歷史；沒有刪空白或重建覆蓋學校資料。2026-10-11 15:55:36 UTC最小git status與已保存報告讀取證明環境可用，檢查點另存。

追加交付檢查：API的版本化JS快取為24小時，故更新index.html的app.js版本至20261011-tku-host-references-1。實際TestClient GET首頁、版本化app.js及新TKU模組皆200；回傳app.js SHA與已完成201／4單元及4 browser測試的09f9235a固定檢查點完全一致，學校資料未改。cache smoke證據另存，總43份證據。
