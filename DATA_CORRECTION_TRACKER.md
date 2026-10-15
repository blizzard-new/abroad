# Uniway 資料不一致問題修正追蹤表（DATA_CORRECTION_TRACKER）

> **更新日期**：`2026-10-15`  
> **追蹤原則**：每一筆經官方第一手證據確認之平台資料錯誤、過期或內部不一致問題，均對應至獨立之 GitHub Pull Request（**PR #29 – #33**），並與 [`DATA_VERIFICATION_DETAILS.csv`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/DATA_VERIFICATION_DETAILS.csv) 之 `Record ID` 雙向連結。

---

## 一、已建立修正 PR 之問題總表（21 項問題群組，涵蓋 324 筆錯誤/過期紀錄）

| 問題代號 | 優先級 | 所屬學校 / 模組 | 問題摘要 | 影響紀錄筆數 | 官方來源網址與公告日期 | 修正狀態 | 對應 GitHub PR |
|---|---|---|---|---:|---|---|---|
| **`CGU-001`** | **P0** | 長庚大學 (`cgu`) | `student_view.py` 誤將教育部 TEEP「全球優秀青年學子來臺蹲點計畫」（外國學生來臺實習）列為長庚學生出國交換計畫與獎學金 | `1` 項計畫 / `7` 筆關聯紀錄 | `https://www.cgu.edu.tw/oia-ch/Contents?nodeId=19081` (2026-01-29) | 已建立 PR 待審 | [PR #29](https://github.com/blizzard-new/abroad/pull/29) |
| **`CGU-003`** | **P2** | 長庚大學 (`cgu`) | 法國雷恩商學院（Rennes School of Business）管院參考連結指向已停機之舊伺服器 `id2.cgu.edu.tw`（連線逾時）與失效外校路徑（HTTP 404） | `2` 筆 (`CGU-PARTNER-063`, `RULE-CGU-RENNES-REF-LINK`) | `https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554` & `https://www.rennes-sb.com/programmes/undergraduate-programme/exchange-programme/` | 已建立 PR 待審 | [PR #29](https://github.com/blizzard-new/abroad/pull/29) |
| **`NTPU-001`** | **P0** | 國立臺北大學 (`ntpu`) | 116 學年度中文組全數 **21 所大陸姊妹校**（合計 64 名額）因 PDF 解析器漏擷取名額欄，全部誤顯示為「當期名額表未列明人數」 | `21` 校 (`NTPU-PARTNER-001` 等) | `https://cms-carrier.ntpu.edu.tw/uploads/116_6524fec218.pdf` (2026-09-24) | 已建立 PR 待審 | [PR #30](https://github.com/blizzard-new/abroad/pull/30) |
| **`NTPU-002`** | **P1** | 國立臺北大學 (`ntpu`) | 英語組、日語組與中文組共 **22 所姊妹校**之 `school_name` 誤將右欄申請資格或年級限制文字串接吸入，並污染 `ntpu/*.jsonl` | `22` 校 (`NTPU-PARTNER-*`) | `https://cms-carrier.ntpu.edu.tw/uploads/116_0924_da1dafe9d0.pdf` & `116_1003_707639a7d6.pdf` (2026-09-24 / 10-03) | 已建立 PR 待審 | [PR #30](https://github.com/blizzard-new/abroad/pull/30) |
| **`NTPU-003`** | **P0** | 國立臺北大學 (`ntpu`) | 英語組 **9 所姊妹校**（`#42 UCI`, `#44 UC Berkeley`, `#60 BCU`, `#65 FS`, `#68 Regensburg`, `#69 Cologne`, `#70 Mannheim`, `#98 UAB`, `#118 HUFS`）名額或交換期間切分錯位 | `9` 校 (`NTPU-PARTNER-*`) | `https://cms-carrier.ntpu.edu.tw/uploads/116_0924_da1dafe9d0.pdf` (2026-09-24) | 已建立 PR 待審 | [PR #30](https://github.com/blizzard-new/abroad/pull/30) |
| **`NTPU-004`** | **P1** | 國立臺北大學 (`ntpu`) | PDF 頁尾注意事項混入表格文字，導致明知大學等 **9 所姊妹校**之 `colleges` 與 `eligibility` 欄位被頁尾文字污染 | `9` 校 (`NTPU-PARTNER-*`) | `https://cms-carrier.ntpu.edu.tw/uploads/116_0924_da1dafe9d0.pdf` (2026-09-24) | 已建立 PR 待審 | [PR #30](https://github.com/blizzard-new/abroad/pull/30) |
| **`NTPU-005`** | **P1** | 國立臺北大學 (`ntpu`) | `NTPU_EXCHANGE_GUIDELINES_URL` 仍指向 115-2 舊版簡章（`115_2_2c7cb4c171.pdf`），未更新為 116 最新簡章（`116_16e535159d.pdf`） | `1` 筆 (`RULE-NTPU-GUIDELINES-URL`) | `https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf` (2026-09-24) | 已建立 PR 待審 | [PR #30](https://github.com/blizzard-new/abroad/pull/30) |
| **`NTPU-006`** | **P2** | 國立臺北大學 (`ntpu`) | `_NTPU_COMMON_TITLES` 缺少 116 學年度中英文簡章與三語組學校一覽表標題 | `1` 筆 (`RULE-NTPU-COMMON-TITLES`) | `https://new.ntpu.edu.tw/oia/files?tag=%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F` (2026-09-24) | 已建立 PR 待審 | [PR #30](https://github.com/blizzard-new/abroad/pull/30) |
| **`NTPU-008`** | **P0** | 國立臺北大學 (`ntpu`) | 116-1 申請截止時間為 `2026-10-23 17:00`（正確），惟面試時程原僅寫「11月下旬」，缺少簡章第 2 頁公告之確切面試日期（英語組 `11/23、11/25`；中日語組 `11/27`；12 月下旬公告結果） | `1` 筆 (`RULE-NTPU-DEADLINES`) | `https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf` (2026-09-24) | 已建立 PR 待審 | [PR #30](https://github.com/blizzard-new/abroad/pull/30) |
| **`NTU-001`** | **P0** | 國立臺灣大學 (`ntu`) | 臺大國合處 `school.list` 截至 2026/10/15 已公布 **20 所姊妹校**之 116-1 確定名額（43 學年名額 / 最多 81 人次），`main` 分支仍全數標為 `尚未確定 (pending)` | `20` 校 (`NTU-PARTNER-SN*`) | `https://oia.ntu.edu.tw/outgoing/school.list` (2026-10-14 ~ 2026-10-15) | 已建立 PR 待審 | [PR #31](https://github.com/blizzard-new/abroad/pull/31) |
| **`NTU-002`** | **P0** | 國立臺灣大學 (`ntu`) | 加拿大女王大學（`#599`）於 116-1 官網已更新為 `一學期 0 名；一學年 0 名（不開放申請）`，`main` 分支仍標為 `pending / open` | `1` 校 (`NTU-PARTNER-SN0599`) | `https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/599` (2026-10-15) | 已建立 PR 待審 | [PR #31](https://github.com/blizzard-new/abroad/pull/31) |
| **`NTU-003`** | **P1** | 國立臺灣大學 (`ntu`) | 澳洲 **11 所合作大學**（Portal ID: `92, 93, 94, 95, 96, 97, 206, 210, 313, 1109, 1307`）細目頁新增 Subclass 500 學生簽證審查提醒（建議提前 4 個月申請），`main` 分支尚未收錄 | `11` 校 (`NTU-PARTNER-SN*`) | `https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/92` 等 11 頁 (2026-10-14) | 已建立 PR 待審 | [PR #31](https://github.com/blizzard-new/abroad/pull/31) |
| **`NTU-004`** | **P1** | 國立臺灣大學 (`ntu`) | 加拿大英屬哥倫比亞大學（`#1`）細目頁上架 2027/28 最新 Fact Sheet PDF 連結 | `1` 校 (`NTU-PARTNER-SN0001`) | `https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/1` (2026-10-14) | 已建立 PR 待審 | [PR #31](https://github.com/blizzard-new/abroad/pull/31) |
| **`NTU-005`** | **P1** | 國立臺灣大學 (`ntu`) | 美國夏威夷大學希羅分校（`#369`）官網已由「夏威夷大學大島分校」正名為「夏威夷大學希羅分校」並上架 2027–2028 要項 PDF | `1` 校 (`NTU-PARTNER-SN0369`) | `https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/369` (2026-10-15) | 已建立 PR 待審 | [PR #31](https://github.com/blizzard-new/abroad/pull/31) |
| **`NTU-006`** | **P1** | 國立臺灣大學 (`ntu`) | 迪肯大學（`#95`）、筑波大學（`#107`）、亞琛工業大學（`#247`）、夏威夷大學馬諾阿分校（`#14`）、明斯特大學（`#1200`）、慕尼黑大學（`#391`）、伯恩大學（`#371`）等細目頁參考資訊更新 | `7` 校 (`NTU-PARTNER-SN*`) | `https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/95` 等 (2026-10-14 ~ 10-15) | 已建立 PR 待審 | [PR #31](https://github.com/blizzard-new/abroad/pull/31) |
| **`NTU-007`** | **P1** | 國立臺灣大學 (`ntu`) | 臺大管理學院於 2026/10/01 發布 116 學年度院級出國交換獎學金申請簡章與續領申請表 PDF，`college_programmes.json` 尚未收錄 | `1` 筆 (`RULE-NTU-SCHOLARSHIPS-COM-116`) | `https://management.ntu.edu.tw/ia/outbound/scholarship` (2026-10-01) | 已建立 PR 待審 | [PR #31](https://github.com/blizzard-new/abroad/pull/31) |
| **`NCU-001`** | **P0 / P1** | 國立中央大學 (`ncu`) | 中央國合處已於 **2026/10/13** 公告 `116exchangeschoollist-1013.pdf`（215 筆，較 115 舊表新增 6 校、移除 7 校、正名羅馬尼亞美利堅大學並更新 3 校限制），`main` 分支仍使用 115 舊表且寫「名額預定2026/10/12公告」 | `222` 筆 (`UNIV-NCU-PROFILE` + `221` 筆姊妹校紀錄) | `https://oia.ncu.edu.tw/var/file/26/1026/img/272/116exchangeschoollist-1013.pdf` (2026-10-13) | 已建立 PR 待審 | [PR #32](https://github.com/blizzard-new/abroad/pull/32) |
| **`NCU-002`** | **P1** | 國立中央大學 (`ncu`) | 舊版出國申請系統 `https://abroad.oia.ncu.edu.tw/student/` 因系統改版升級返回 HTTP 404，平台未附國合處系統升級期間改採紙本與 Email 辦理之公告 | `1` 筆 (`RULE-NCU-PORTAL-UPGRADE-URL`) | `https://oia.ncu.edu.tw/p/406-1026-13073,r18.php?Lang=zh-tw` (2026-09-10) | 已建立 PR 待審 | [PR #32](https://github.com/blizzard-new/abroad/pull/32) |
| **`NCU-003`** | **P2** | 國立中央大學 (`ncu`) | 缺少國合處 2026/10/01 公告之 116-1 出國交換申請說明會（`2026/11/10 12:00–13:30`）資訊 | `1` 筆 (`RULE-NCU-INFO-SESSION-116-1`) | `https://oia.ncu.edu.tw/p/406-1026-14170,r18.php?Lang=zh-tw` (2026-10-01) | 已建立 PR 待審 | [PR #32](https://github.com/blizzard-new/abroad/pull/32) |
| **`MAINT-001`** | **P0 / P1** | 維護子系統 & PostgreSQL (`maintenance`) | `build_default_maintenance_router()` 於本地 `store.change_sets` 為空時自動產生展示用名額/期限變更集（`cs_ntu_116_quota_and_deadline` 等）並標記為 `SOURCE_CHANGE`「官方來源更新」（目前僅確認程式碼有此風險，正式站 DB `exchange_maint_change_sets` 為 `0` 筆尚未受影響；後台勿核准無原始公告支持之變更） | `2` 筆 (`MAINT-001-CS-DEMO-DEADLINE`, `MAINT-001-CS-DEMO-CONFLICT`) | `https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/sem1-20272028ay-selection-timeline/` (2026-10-15) | 已建立 PR 待審 | [PR #33](https://github.com/blizzard-new/abroad/pull/33) |
| **`MAINT-002`** | **P1** | 維護子系統 & PostgreSQL (`maintenance`) | `load_six_school_shadow_summary()` 對 CCU 僅匯入 55 筆（應為 104 筆）、對 TKU 僅匯入 4 筆（應為 287 筆）、對 NTPU 重複匯入 409 筆（應為 206 筆）、對 CGU 匯入含 TEEP 之 154 筆 | `4` 項子系統匯入基準 (`MAINT-002-SHADOW-*`) | 各校 `official_data/` 權威基準檔 | 已建立 PR 待審 | [PR #33](https://github.com/blizzard-new/abroad/pull/33) |

---

## 二、既有未合併 PR（#24、#28）補充證據說明與保留建議

| 既有 PR 編號 | 分支名稱 | 內含之補充證據與獨立價值 | 建議處置方式 |
|---|---|---|---|
| **[PR #24](https://github.com/blizzard-new/abroad/pull/24)** | `data/ntu-official-update-20261014` | 包含 2026/10/14 抓取之原始網頁與附件備份壓縮檔 `sources/ntu/reviewed-source-bodies-2026-10-14.zip` 以及 `#998, #1302, #1103, #71, #72, #69` 等細目頁補充更新內容 | **請勿直接關閉 PR #24**：建議保留其原始網頁備份與細目頁補充證據，與 **[PR #31](https://github.com/blizzard-new/abroad/pull/31)** 交叉對照審查 |
| **[PR #28](https://github.com/blizzard-new/abroad/pull/28)** | `data/ntu-official-update-20261015` | 包含 `docs/ntu-official-update-20261015/` 完整稽核報告與附件雜湊比對紀錄（含日本筑波大學 `#107` CoE Web Application System Guide PDF 更新證據） | **請勿直接關閉 PR #28**：建議保留其 `docs/ntu-official-update-20261015/` 補充查證報告，與 **[PR #31](https://github.com/blizzard-new/abroad/pull/31)** 一併對照審查 |

---

## 三、重點修正項目明細表（節錄 P0 名額與校名修正）

### 1. 國立臺北大學 116 學年度中文組 21 校名額補齊明細（[PR #30](https://github.com/blizzard-new/abroad/pull/30)，`NTPU-001`）

| 編號 | 姊妹校名稱 | 所在城市 | 修正前平台顯示名額 | 修正後官方確切名額（`116_6524fec218.pdf`） |
|---:|---|---|---|---|
| 1 | 上海立信會計金融學院 | 上海 | 當期名額表未列明人數 | **2 名上限** |
| 2 | 中國政法大學 | 北京 | 當期名額表未列明人數 | **5 名上限** |
| 3 | 中央財經大學 | 北京 | 當期名額表未列明人數 | **2 名上限** |
| 4 | 北京師範大學 | 北京 | 當期名額表未列明人數 | **2 名上限** |
| 5 | 北京理工大學 | 北京 | 當期名額表未列明人數 | **3 名上限** |
| 6 | 天津大學 | 天津 | 當期名額表未列明人數 | **2 名上限** |
| 7 | 南開大學 | 天津 | 當期名額表未列明人數 | **3 名上限** |
| 8 | 吉林大學 | 長春 | 當期名額表未列明人數 | **3 名上限** |
| 9 | 東北師範大學 | 長春 | 當期名額表未列明人數 | **5 名上限** |
| 10 | 同濟大學 | 上海 | 當期名額表未列明人數 | **2 名上限** |
| 11 | 華東師範大學 | 上海 | 當期名額表未列明人數 | **2 名上限** |
| 12 | 華東政法大學 | 上海 | 當期名額表未列明人數 | **6 名上限** |
| 13 | 南京大學 | 南京 | 當期名額表未列明人數 | **2 名上限** |
| 14 | 東南大學 | 南京 | 當期名額表未列明人數 | **5 名上限** |
| 15 | 蘇州大學 | 蘇州 | 當期名額表未列明人數 | **3 名上限** |
| 16 | 江南大學 | 無錫 | 當期名額表未列明人數 | **2 名上限** |
| 17 | 山東大學 | 濟南 | 當期名額表未列明人數 | **3 名上限** |
| 18 | 武漢大學 | 武漢 | 當期名額表未列明人數 | **2 名上限** |
| 19 | 中南財經政法大學 | 武漢 | 當期名額表未列明人數 | **5 名上限** |
| 20 | 四川大學 | 成都 | 當期名額表未列明人數 | **2 名上限** |
| 21 | 西南財經大學 | 成都 | 當期名額表未列明人數 | **3 名上限** |

### 2. 國立臺灣大學 116-1 最新公布之 20 校甄選名額與女王大學 0 名額明細（[PR #31](https://github.com/blizzard-new/abroad/pull/31)，`NTU-001` & `NTU-002`）

| 學校編號 (`sn`) | 國家 | 姊妹校名稱 | 修正前狀態 (`main`) | 修正後 116-1 官方甄選名額 (`oia.ntu.edu.tw/outgoing/school.list`) |
|---:|---|---|---|---|
| `#998` | 奧地利 | 維也納大學 University of Vienna | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#620` | 奧地利 | 格拉茲大學 University of Graz | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#9` | 澳洲 | 昆士蘭大學 The University of Queensland | 尚未確定 (`pending`) | **2 學年名額（最多 3 人次）** |
| `#10` | 澳洲 | 雪梨科技大學 University of Technology Sydney | 尚未確定 (`pending`) | **2 學年名額（最多 4 人次）** |
| `#297` | 澳洲 | 新南威爾斯大學 UNSW Sydney | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#298` | 澳洲 | 墨爾本大學 The University of Melbourne | 尚未確定 (`pending`) | **2 學年名額（最多 4 人次）** |
| `#537` | 澳洲 | 澳洲國立大學 The Australian National University | 尚未確定 (`pending`) | **2 學年名額（最多 4 人次）** |
| `#557` | 澳洲 | 西澳大學 The University of Western Australia | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#725` | 澳洲 | 蒙納許大學 Monash University | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#1188` | 澳洲 | 阿德雷德大學 Adelaide University | 尚未確定 (`pending`) | **1.5 學年名額（最多 3 人次）** |
| `#252` | 英國 | 布里斯托大學 University of Bristol | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#253` | 英國 | 愛丁堡大學 The University of Edinburgh | 尚未確定 (`pending`) | **9 學年名額（最多 18 人次）** |
| `#256` | 英國 | 格拉斯哥大學 University of Glasgow | 尚未確定 (`pending`) | **2 學年名額（最多 4 人次）** |
| `#257` | 英國 | 曼徹斯特大學 The University of Manchester | 尚未確定 (`pending`) | **3 學年名額（最多 6 人次）** |
| `#258` | 英國 | 華威大學 The University of Warwick | 尚未確定 (`pending`) | **1 學年名額（最多 1 人次，限交換一學年）** |
| `#259` | 英國 | 南安普敦大學 University of Southampton | 尚未確定 (`pending`) | **6 學年名額（最多 11 人次）** |
| `#386` | 英國 | 謝菲爾德大學 The University of Sheffield | 尚未確定 (`pending`) | **2 學年名額（最多 4 人次）** |
| `#549` | 英國 | 倫敦國王學院 King's College London | 尚未確定 (`pending`) | **1.5 學年名額（最多 3 人次）** |
| `#568` | 英國 | 諾丁漢大學 University of Nottingham | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#622` | 加拿大 | 卡爾加里大學 University of Calgary | 尚未確定 (`pending`) | **1 學年名額（最多 2 人次）** |
| `#599` | 加拿大 | 女王大學 Queen's University | 尚未確定 (`pending / open`) | **一學期 0 名；一學年 0 名（本學期不開放申請，`zero / closed`）** |
