# 淡江大學校級交換資料與平台整合交接

查核日：2026-10-08（UTC）；校內期限保留臺北時區，外校期限保留外校時區。
Repository：`blizzard-new/abroad`；獨立工作目錄：`/workspace/abroad-tku`；分支：`data/tku-exchange-20261008`。
初始 main 為 `f741d540f546d6ddbbf3174c9a34b5ef103c8816`；交付重新基於最新讀取的 main `293546e807294dc0812f390b240a4cfb68e86cd0`。
未修改其他 session 的 `/workspace/abroad`。查找 `/`、`/workspace` 及 repo，未找到適用的 `AGENTS.md` 或本地 `.agents/skills`。

## 可整合的交付

- `src/exchange_info/official_data/tku/partners_current.jsonl`：4 筆最新核實日語二甄計畫。
- `partners_reference.jsonl`：124 筆舊期參考，89 英歐語組及 35 中文聯合甄選；不注入當期選校 API。
- `sources.json`：29 筆官方證據，保留 URL、內容、頁碼／表格／儲存格、角色、適用年度、查核日期、HTTP 與 SHA-256。
- 11 份官方原附件（PDF/DOCX/XLSX）；另記錄原日語公告的 1 個舊附件 404。更新附件已下載並核對內文。不能宣稱所有舊連結有效。
- `rounds.json`、`conflicts.json`、`integrity.json`：年度梯次、7 組待確認事項、資料校驗。
- `application_workflows.jsonl`：4 個結構化流程，每個 6 步；維持 `legacy`／未發布，均不產生截止提醒。
- `destination_profiles.jsonl`：4 個部分官方生活資料；不捏造交通、宿舍床位或未核實價目。
- 校別獨立的 `tku_data.py`、`tku_student_view.py`、`tku_eligibility.py`、`tku_documents.py`、`tku_university.py`，及抓取／離線重建程式。
- `tests/test_tku_support.py`、本交接、來源查核 CSV 及測試證據 JSON。

128 是「計畫列」，不是 128 個不同實體學校；原文名稱去重為 119 個，跨語組／計畫重複是合理的。記錄 ID 依梯次與原表位置區分，無重複 ID。

## 當期適用範圍

以 [國際處公告索引](https://oieie.tku.edu.tw/oieie/?page_id=55)、首頁及赴外頁核對，最新可核實校級日語第二次聯合甄選是 **2027–2028**，不用臺大或其他學校的年度轉換規則。
以 `jp-revision` 更正公告及其更新附件為準；學生校內申請 **2026/9/23 09:00 至 9/30 12:00（臺北）**，查核時已截止。

| 2027–2028 日語二甄表列學校 | 名額 | 課程語言／表列特別條件 |
| --- | ---: | --- |
| 立命館大學 | 1 | 日文；大學部／碩士；JLPT N1、GPA 3.0、母校至少一學年 |
| 長崎外國語大學 | 2 | 日文；大學部／碩士；額外条件未明示；原表連結錯指城西國際大學 |
| 成蹊大學 | 1 | 日文；大學部／碩士；GPA 2.5、母校至少一學期 |
| 電氣通信大學 | 3 | 英文 JUSST；電機／資工優先；平均 80、GPA 3.0；表寫 iBT 67「及」IELTS 6.0；學制欄未明示 |

依據：[更新名額表 PDF p.1](https://oieie.tku.edu.tw/oieie/wp-content/uploads/2026/09/更新2027-2028日語組第二次甄選姊妹校一覽表.pdf)。合計 **4 校、7 名**；查核時 **0 個可新申請選項**，平台皆顯示 `closed`，已獲推薦者依外校期限續辦。
交換期間表列 **2027.4–2028.3**，實際依外校行事曆。名額表的正名額與「今天可否校內新申請」分開。

校內正文資格為大三、研究所一二年級、學業總平均 75、系所院推荐。大學部日語課程 JLPT N2，研究所 N1；立命館另加嚴 N1。研究所英語課 N1 豁免未明示。學業平均 75 與書審／面試合計錄取 70 分不能混用。
依據：[更新簡章](https://oieie.tku.edu.tw/oieie/wp-content/uploads/2026/09/更新2027-28日語組二甄簡章.pdf) p.2、p.5、p.18；附錄前 40% 替代條件的矛盾見下表。

校內文件 p.3–4：線上表列印本人／系主任簽名、中文歷年成績單正本（碩一另附大學四年成績）、語言證明影本或網路成績、授課老師推薦函一封、中日文自傳、中日文研習計畫、切結書、有則附其他證明。A4 單面最多 16 頁、不裝訂、L 型套；面試驗語言原本；最多 5 志願。切結書 p.14、修正表 p.15；後者截止日期有舊值，不自行修改成正式表單。
平台只提供兩種中日文準備稿，`official_layout=false`；不製作偽官方申請表或切結書。

## 舊期與其他計畫

| 資料 | 已核對的內文年度與數量 | 本次處理 |
| --- | --- | --- |
| 英歐語組第一輪 | 2026–2027／115；XLSX 英語 70、法德 10、西俄 9，共 89 計畫列 | 舊期參考；2027–2028 新版尚未核實 |
| 英歐第二輪 | 2026–2027；僅第一輪未獲分發者，2025/12/24 17:00 截止 | 不當作新年度開放名單 |
| 大陸／澳門／金門中文組 | 115，2026 秋季或 2027 春季；35 列、118 名 | 舊期參考；新版尚未核實；含總數與澳門學期矛盾 |
| 姊妹校目錄 | 一般合作協議目錄，未標本梯次名額 | 只作目錄證據，不全部轉成當期可選 |
| 院系大三出國 | 外語六系、國企、資工、觀光、政經等；簡章 p.17 Q&A3 區分 | 與國際處互惠交換不同；未核實各系新期名單，不併入校級選校 |

「新版尚未核實」表示未找到並核對可用新版，**不等於官方明示尚未公告**。來源頁沒有這項明示，資料未填 `not_announced`。
舊英歐校內期限：2025/11/12 09:00–11/26 17:00，系所 11/27 17:00；學業 75 **或**系前 40%，二三年級／碩士不含在職專班；英語 iBT70 或 Academic IELTS5.5、法西 B1、德俄 A2，各校可加嚴。
舊中文校內期限：2026/2/23 08:00–3/2 17:00，系所 3/3 17:00；學業 75 或前 40%；大三只可大四上出國；國籍、年級、科系限制逐列保留。
這些舊截止沒有放進當期提醒或文件清單。英歐 19 列 TBC 名額保留原字串，數值為 null；109 列為數字。原資料沒有零或空白名額，但 schema／parser 明確區分 `numeric`、`zero`、`blank`、`provisional`。不把 TBC 轉成零、不以旁列填未合併空格。

## 外校 incoming 資料

每個欄位 evidence 分 `home_outbound`、`host_incoming`、`directory_reference`，不把外校 incoming 門檻當作淡江 outbound 資格。

- 立命館：核對 [2027 Spring SKP 官方 PDF](https://en.ritsumei.ac.jp/skp-e/apply/pdf/Application_Guidelines_ENG.pdf) 全文 22 頁。p.2 申請 2026/10/2 10:00–11/2 09:00 **JST**，僅已由母校推薦者；COE 另辦。p.4 自 2027 春所有 SKP 含交換生收 JPY50,000 Student Support Fee，RUSSES 結束、JASSO 不保證。選 study track／校區与學院課程依 p.3–7；住宿頁是一般規定，2027 床位與價目未核實，標參考。
- 成蹊：核對 [2027 Spring factsheet](https://www.seikei.ac.jp/gakuen/siis/intl/%E2%97%8FInformation%20sheet%20Spring2027%28Seikei%20University%29_updated0827.pdf) 6 頁。p.1–2 春季提名 10/1、申請 10/15（未載時刻），母校承辦送件；較低外校入門日語門檻不能取代淡江 N2/N1。p.2 專業課不保證、學士課 N1、至少 6 門、體育／師培等不開放。p.3–4 至 2027/8 兩宿舍 JPY93,000/月但包含費用不同；2027/9 搬 MICHI，JPY120,000/月含餐寢具水電網路、無押金；不以舊租金覆蓋全學年。
- 電氣通信：只核實 JUSST 一般 [申請](https://www.fedu.uec.ac.jp/en/future_students/jusst/application/) 及 [費用](https://www.fedu.uec.ac.jp/en/future_students/jusst/costs/) 頁（更新 2025）。宿舍約 JPY25,000 原文未載計費單位，不聲稱月租；保險約 JPY26,000 可變；April 入學 October31 為一般重複時程，未轉成 2027 exact deadline。2027 專屬表格、價目與期限未核實。
- 長崎：正確交換頁、2027 外校期限、住宿費用、課程及進一步資格未核實，不引用錯連城西資料。

淡江全額學雜費及外校主要學費互惠免繳保留在獨立 `home_costs`；與外校支援費、住宿、保險分開。床位、獎學金、課程抵免均不保證。

## 未解矛盾與缺口

| ID | 官方依據／矛盾 | 處理與待確認 |
| --- | --- | --- |
| jp-stale-dates | 更正公告；簡章 p.3 星期、p.6 9/17、p.3 2025 日期、p.15 9/17 | 學生申請採更正日期；系所送國際處與修正作業新截止未明示 |
| jp-academic-rank-alternative | p.2 平均 75；p.18 Q&A 75 或前 40% | 本期不能自動採前 40% 替代 |
| jp-departure-before-start | p.7 2027/3/31 前出國／許可；名額表 2027.4 開始 | 可能提早入境，向承辦確認，不擅判錯字 |
| nagasaki-wrong-url | 名額表長崎列 jiu.ac.jp | URL null，不把城西條件填進長崎 |
| uec-language-conjunction | TKU「及」雙英語條件、80 且 GPA3；外校一般頁等值選擇 | 分角色保留；研究所 N1 豁免、2027 JUSST 條件待確認 |
| mainland-school-count | 35 明細、118 名；合計文字若照字面為 33 校 | 保留全部明細，不為合計文字刪列 |
| macau-wrong-semester | 名額表 114-2；正文 115-2／2027 春 | 舊期參考並留矛盾，不猜選哪個值 |

資料完整度以欄位狀態計數，不能解讀為申請保證：當期 4 列共 **84 個欄位，53 verified（63.1%）、16 missing_in_source、9 needs_confirmation、6 reference_only**。全資料 2316 欄位：53 verified、664 missing、9 needs_confirmation、1590 reference_only。缺值保留 null 與來源位置；schema 必填的是「欄位狀態」，並非猜出每個值。
英歐／中文新版、各系所提前截止、長崎外校資料、UEC 2027 版本與上述矛盾仍需要官方後續文件或承辦澄清；本 session 未向承辦發信。

## 共用檔必要適配（合併時集中處理）

| 共用檔 | 必要變更 |
| --- | --- |
| university_registry.py | 匯入校別 PROFILE、登錄 TKU 與別名；support_level=basic |
| models.py | PartnerUniversity availability 增加 closed／reference_only／quota_unconfirmed；既有預設不變 |
| api.py | TKU 的選校、頁面、info、dashboard 分派；按請求重算時窗，避免快取把已截止資料留成開放 |
| storage.py | 讀 TKU bundled workflow／destination；仍按母校分流 |
| application_documents.py | 讀兩份 TKU 準備稿；不同年度／梯次返回空；TKU 查核日期獨立 |
| static/app.js | 新狀態提示與 blocked；TKU 資格總結要求語組／學制確認；通用開放標籤移除固定 115 年度 |
| static/index.html | 增加三種狀態篩選；保留最新 main 地區篩選與資產版本 |
| pyproject.toml | 打包官方 DOCX／XLSX 原附件 |

這 8 處可由統一整合 session 按現有新增學校機制整理，不必併改其他校別檔案。此分支沒有 NTU 資料或 NTU 適配。
CGU/NTPU 資料相對交付基準 main 沒有修改；繼承 main 更新。CGU 最新 116 流程 77 個目的地（75 校級+2 院級參考），另保留 115 的 77 個；NTPU 206（169 開放+37 協議參考）。

## 重建與查核

```bash
UV_CACHE_DIR=/tmp/tku-uv-cache uv sync --frozen --extra dev
.venv/bin/python scripts/build_tku_catalog.py
.venv/bin/python scripts/refresh_tku_sources.py --output /tmp/tku-new-evidence
.venv/bin/python scripts/refresh_tku_sources.py --manifest src/exchange_info/official_data/tku/sources.json --output /tmp/tku-refetched-evidence
.venv/bin/python -m pytest tests/test_tku_support.py -q
node --check src/exchange_info/static/app.js
git diff --check
```

抓取輸出必須是不存在的新目錄；只產生候選證據，不自動覆蓋已審查 bundle。`--manifest` 保留 source ID，涵蓋母校與外校來源，但輸出只保存「之前適用年度」且標 `requires_content_review`；須核對新內容後人工審查年度、梯次與衝突才能提升。
離線 builder 依原 PDF 人工核實的 4 列，及 XLSX/DOCX 原儲存格生成資料；測試驗證重建逐位元相同。

初始 HTTPS git 認證失敗已如實回報；後續找到環境既有 gh 認證，使用單次 credential helper，未改憑證或 git 全域設定。
`uv sync --locked --extra dev` 遇現有 lockfile 不一致；改用 `--frozen` 成功，未更新 lockfile。

測試實際數量及既有失敗比較見 `tku-validation-2026-10-08.json`。初始基準 f741d54 的擴展回歸為 118 passed／9 failed／4 skipped；9 個失敗均在未修改基準重現（8 前端舊文字 contract、1 NTPU destination coverage），沒有用「全部通過」描述。最新基準重新驗證結果另存證據。
未執行合併 main 或部署；流程未進行發布審查。
