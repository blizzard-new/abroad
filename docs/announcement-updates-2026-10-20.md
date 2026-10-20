# 2026-10-20 上午 13 校官方交換公告與名額查核紀錄

- **查核時間**：2026-10-20 上午（Asia/Taipei）
- **查核學校數**：13 所（有核實更新 3 所、已查核範圍未見更新／部分補建基準 8 所、關鍵範圍仍未查完 2 所）
- **結構化查核帳本**：[`sources/audit/2026-10-20-morning-13-schools.json`](../sources/audit/2026-10-20-morning-13-schools.json)
- **查核邊界原則**：只在已查範圍內判斷；未完整核對之表單、需校內登入（SharePoint / O365 / Google Drive）之個別合作校資料、以及無昨日快照之表單狀態，均不算「沒有更新」或「今日才變更」。

---

## 一、有核實更新（3 校）

### 1. 國立臺灣大學（NTU）｜116-1／2027–2028
- **官方交換學校列表**：`https://oia.ntu.edu.tw/outgoing/school.list`
- **新增公布名額之 8 所合作校**（原本名額欄空白，今日列表公布名額與人數上限）：
  1. `sn/1092` 奈梅亨大學／拉德堡大學（Radboud University）：`1 名`（最多 `2 名`）
  2. `sn/187` 阿姆斯特丹自由大學（Vrije Universiteit Amsterdam）：`3 名`（最多 `4 名`）
  3. `sn/80` 烏特列茲大學／烏特列支大學（Utrecht University）：`3 名`（最多 `6 名`）
  4. `sn/82` 奧斯陸大學（University of Oslo）：`2 名`（最多 `4 名`）
  5. `sn/1291` 杜倫大學（Durham University）：`2 名`（最多 `2 名`）
  6. `sn/1093` 肯特大學（University of Kent）：`1 名`（最多 `2 名`）
  7. `sn/604` 愛丁堡大學（University of Edinburgh）：`0.5 名`（最多 `1 名`）
  8. `sn/90` 南安普頓大學（University of Southampton）：`1 名`（最多 `2 名`）
- **詳細頁變更之 6 所合作校**（全數 289 校詳細頁已查完，6 頁改變、283 頁相同；英國四校 `1291`、`1093`、`604`、`90` 僅列表補上名額，詳細頁無新改動）：
  1. **拉德堡（`sn/1092`）**：移除待確認警示；交換期間由一學期改為「可選擇交換一學期或一學年，限於本校第一學期出國交換」；新增「此校開放予第二次出國交換之同學選填」；新增新制 `TOEFL iBT 4.0 (不接受 Home Edition)`；新增「不接受法律學院之學生申請（NOT open to exchange students: Faculty of Law）」。
  2. **阿姆斯特丹自由（`sn/187`）**：移除待確認警示；年度名額單位 `2 → 3`（最多 4 人：限定交換一學年人數 2 人、限定交換第一學期人數 2 人）；年級限制由「大二/大三」放寬至「本校大二以上(僅限大學部)學生」；新增新制 `TOEFL iBT 5.0 (不接受 Home Edition)`；更新 2027–2028 學期日期（`Semester 1: 30/08/2027- 28/01/2028`、`Semester 2: 31/01/2028- 23/06/2028`）及生活費明細。
  3. **奧斯陸（`sn/82`）**：移除待確認警示；年度名額單位 `1 → 2`（最多 4 人，可選擇交換一學期或一學年）；新增新制 TOEFL 門檻（學士生 `TOEFL iBT 4.0 (接受 Home Edition)`、研究生 `TOEFL iBT 4.5 (接受 Home Edition)`）。
  4. **烏特列支（`sn/80`）**：移除待確認警示；新增新制 `TOEFL iBT 4.5 (讀 4.5 聽 4.5 說 4.5 寫 4.5 不接受 Home Edition)`；注意事項新增提醒生物／生醫課程名額有限（`Some departments have limited availability for exchange students, like biology and biomedical sciences.`）。
  5. **近畿（`sn/1187`）**：移除待確認警示；列表名額仍空白；詳細頁名額改為第一學期、僅一學期（日語組一學期 1 名、一般組一學期 1 名，均限定交換第一學期人數 1 人），一般組 Programme A 新增 `TOEFL iBT 4.5 (不接受 Home Edition)`。
  6. **兵庫縣立（`sn/978`）**：移除待確認警示；列表名額仍空白；詳細頁申請資格新增「本校大一/大二學生」字樣，但與臺大中央甄選簡章的大二以上要求衝突，不能據此認定大一可申請（`hyogo_freshman_eligibility_accepted = False`）。
- **平台落檔**：[`sources/ntu/2026-10-20-official/`](../sources/ntu/2026-10-20-official/)、[`sources/ntu/2026-10-20-official-update.json`](../sources/ntu/2026-10-20-official-update.json)、[`src/exchange_info/ntu_oct20_updates.py`](../src/exchange_info/ntu_oct20_updates.py)。

### 2. 淡江大學（TKU）｜新增兩則公告
- **官方來源**：`https://oieie.tku.edu.tw/` 及 `https://enroll.tku.edu.tw/course.aspx?cid=auix1106`
- **核實內容**（昨日保存的首頁沒有，今日已取得正文；其中說明會公告日期為 10/19）：
  1. **2027–28 交換甄選說明會**：2026/11/06（五）18:00–19:30 於驚聲國際會議廳舉行（正取 170 人），報名截止為 2026/11/05（四）17:00。此為說明會報名，不是交換生申請截止日。
  2. **2027 第一期日本台灣交流協會短期獎學金**：校內收件截止 2026/10/30（送交驚聲大樓 T1006 室），每月日幣 8 萬圓（最長一年）。限具台灣籍且未滿 35 歲、日本相關研究、前一學年成績評價係數達 2.30 以上及 2027 年 4–8 月開始赴日交換等條件者，不是所有赴日交換生都適用。公告與四份 PDF 附件已完整核對。
- **平台落檔**：[`sources/tku/2026-10-20-official/`](../sources/tku/2026-10-20-official/)、[`sources/tku/2026-10-20-official-update.json`](../sources/tku/2026-10-20-official-update.json)、[`src/exchange_info/tku_oct20_updates.py`](../src/exchange_info/tku_oct20_updates.py)。

### 3. 天主教輔仁大學（FJU）｜新增 116-1／2027 秋申請公告
- **官方來源**：`https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14`
- **核實內容**：
  1. 今日（10/20）公告提供甄選說明會簡報（`file=1344`，39 頁）、申請表（`file=1345`，2 頁）、非日語組（`file=1346`，4 頁）及日語組（`file=1347`，5 頁）姊妹校申請資格一覽表。
  2. **收件時間與網路限制**：雖然公告標題寫「即日起開始收件至12月24日16:30止!」，正文載明線上申請系統（`http://outgoing.oie.fju.edu.tw/`，有鎖校外 IP 連線，限校內網路使用）開放及收件期間為 **`2026/11/01 至 2026/12/24 16:30`**。
  3. **紙本與電子文件雙軌規範**：
     - `A.紙本文件`：僅須繳交「赴姐妹校交換生申請表（A4 雙面列印、電腦打字輸入）」，完成家長簽章與系所／院／雙主修輔系學程核章後送交耕莘樓 A113 室。
     - `B.電子文件`（單檔 <= 20MB）：（1）書審資料合併 PDF（含中文簡歷兩頁為限、中文讀書計畫只需中文版不需英文版且至少 500 字兩頁為限、其他表現與清寒證明）；（2）中文歷年成績單 PDF（含截至 114-2 歷年班排名）；（3）語測證明 PDF（英檢須為 2024/12/24 以後考取；日語組可先交網路成績並於 2027/01/31 前補齊證明後，於 1 月中旬以 Email 通知選填志願序）。
  4. **重要邊界**：學校及名額仍會在 11 月陸續更新（附表標示「通常名額 (參考用)」），不能當成最終版（`final_partner_list_and_quotas_confirmed = False`）。需要 M365 登入的個別學校資料未查。
- **平台落檔**：[`sources/fju/2026-10-20-official-update.json`](../sources/fju/2026-10-20-official-update.json)、[`src/exchange_info/fju_oct20_updates.py`](../src/exchange_info/fju_oct20_updates.py)、[`src/exchange_info/application_writing_guidance.py`](../src/exchange_info/application_writing_guidance.py)、[`src/exchange_info/verified_window_deadlines.py`](../src/exchange_info/verified_window_deadlines.py)。

---

## 二、已查核範圍未見更新／部分補建基準（8 校）

4. **長庚大學（CGU）**：申請規則、64 筆合作校名單相同。Google 表單目前關閉，但沒有昨天的表單快照，不能說是今天才關閉（`https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656`）。
5. **國立中央大學（NCU）**：完整簡章、名額表相同；QA 與表單補建基準，Google Drive 個別校資料未全查（`https://oia.ncu.edu.tw/tw/international/230/%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A8%88%E7%95%AB/352-%E7%94%B3%E8%AB%8B%E8%B3%87%E8%A8%8A`）。
6. **國立中正大學（CCU）**：2027 春公告與 121 頁合作校 PDF 相同；額外表單未讀完（`https://oia.ccu.edu.tw/p/406-1008-93586,r1714.php?Lang=zh-tw`）。
7. **東吳大學（SCU）**：赴國外與赴陸規則、兩份合作校名單相同；個別學校附件未全查（`https://icae.scu.edu.tw/zh-hant/outbound-exchange`）。
8. **元智大學（YZU）**：既有頁面相同；今天另讀完 55 頁簡報補建基準，不能算今日更新（`https://gao.yzu.edu.tw/index.php/tw/news-tw`）。
9. **中原大學（CYCU）**：115-2 二輪公告、20 校名額表及合作校頁相同；個別學校附件未全查（`https://oia.cycu.edu.tw/article/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E7%94%9F/`）。
10. **國立臺灣師範大學（NTNU）**：285 筆名額條目與昨天相同；動態公告與 23 頁申請須知今天補讀，不能算今日更新，個別外校附件未全查（`https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist`）。
11. **逢甲大學（FCU）**：公開頁面相同；另讀到公開查詢表 148 筆與 9 頁簡章，屬補建基準，O365 內網資料仍未查（`https://oia.fcu.edu.tw/sap/introduction/`）。

---

## 三、關鍵範圍仍未查完（2 校）

12. **國立臺北大學（NTPU）**：僅核對入口頁、FAQ 與經驗分享，正式簡章與合作校名額表仍未取得，不能判為沒有更新（`https://oia.ntpu.edu.tw/outgoing-2`）。
13. **國立臺灣科技大學（NTUST）**：公開時程表未變，但公告內頁與完整合作校條件仍無法穩定讀取，不能判為沒有更新（`https://www.oia.ntust.edu.tw/p/412-1060-8919.php?Lang=zh-tw`）。
