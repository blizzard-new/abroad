# 臺大 PR #1 二次查核修正

2026-10-08在原分支 `codex/add-ntu-third-university` 接續，起始與推送前遠端 head 均為 `230629ce526ed1ccfaf0223509d13b3496567915`；工作区起始乾淨，未偵測新提交。未找到 repo 或 `/workspace` 上層的 `AGENTS.md`，也沒有此 repo 自訂 `.agents/skills`。未修改 CCU/TKU 分支。

## 修正與來源

1. **288校學生摘要**：`ntu_partner_summary.py` 將資格、申請及繳費原文接到 `student_summary_zh`；建置輸出和 `/student-dashboard` 均有資料，`ntu_student_view.py` 亦補齊傳入合作校資料的摘要。年度／身分／待確認限制保留，來源連結可點閱；英文原文未冒稱完成翻譯。`app.js` 有臺大原文 fallback。比對原始來源快照確認288校名稱、國家、資格及註冊繳費原文未改；名額仍282待公告、6零名額。來源為每筆合作校的 [臺大官方內頁](https://oia.ntu.edu.tw/outgoing/school.list/semester/1)，並保留個別補充來源。

2. **筑波截止衝突**：`verification_status.json` portal ID 107 的 `deadlines.status=conflict`，候選日與來源分別保存；`confirmed_deadline_at=null`、`reminder_eligible=false`。原合作校／生活資料的補充說明同樣更新。2027年10月入學的[官方主頁](https://www.tsukuba.ac.jp/en/academics/international-exchange-students/programs/)列2027/3/5，[2027/28指南PDF第3頁](https://www.tsukuba.ac.jp/en/academics/international-exchange-students/programs/application-guide.pdf)列2027/3/6；另一輪2027春的10/9與10/10差異也保留為參考。尚須兩校確認，沒有確定日提醒。

3. **Helsinki停開scope**：portal ID 62 新增2027–2028 Medicine交換修課無課程供應。`affected_programme=Medicine`、`activity=exchange_course_offer`；不泛化到全校、Psychology、Translational Medicine或研究實習，也未保證其他計畫當期必定開課。[Meilahti官方頁](https://studies.helsinki.fi/instructions/article/courses-exchange-students-meilahti-campus)的其他課表仍有2026/27版本；新年度其他計畫須另核對。

4. **文件工具語檢**：`application_documents.py` 新增語組及國際學位生欄位，GEPT/BESTEP與兩種TOEFL量尺分開；一般中語組可留白，國際學位生中語組要求TOCFL/HSK；日語組採JLPT或須先洽國際處的替代證明。語組選單、必填判斷、逐欄預覽、完成度與下一步導覽前後端一致。英語實際考試日期不得早於2025-05-01或填未來日期；預計取得日獨立保存，不能填補實際日期。TOEIC／Duolingo不列作臺大校內英語證明。host incoming可接受的測驗仍獨立保留，未混成臺大門檻。依據[116-1甄選簡章第4個PDF頁（印刷頁3）](https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf)。CGU/NTPU既有欄位與選單保留。

5. **exchange-info語組**：`exchange_info.json` 和 `/exchange-info` 按一般、日、德、法、韓、西、中語組逐列保留範圍；中語國際學位生例外、英語有效考試日與替代證明限制一起列出，沒有全校免語檢的措辭。依據同一份[臺大正式簡章](https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf)。

6. **UNCG保險來源差異**：portal ID 1202，`insurance_visa`及`cost`標為`source_scope_difference`；partners與destination cost summary並列兩份來源。[2027/28 incoming factsheet](https://global.uncg.edu/wp-content/uploads/2026/06/UNCG-IN-fact-sheet-web-version-27-28-US-Letter-1.pdf) Student Blue USD1616估價保留；[SHS現行2026/27頁](https://shs.uncg.edu/student-insurance/)按F-1→Student Blue、J-1→Global Solutions分流。2027/28 J-1方案、保費與waiver期限尚待確認，沒有認定估價錯誤或替學生確認Student Blue。2026秋9/10只列為該年參考。

## 補充資料與仍待確認事項

- **MSU（1306）**：[Incoming Exchange申請頁](https://www.montana.edu/international/studyabroad/incomingexchange/IncomingHowtoApply.html)已讀取Direct Exchange財力、英語證明、短文、正式成績單、護照、擬修課與兩封推薦信；ISEP例外分開，錄取後MMR與TB表另列。網頁無年度，標`reviewed_current_reference_cycle_unconfirmed`；2027/28提名後系統細節仍待確認。
- **岡山（38）**：[2027–2028 EPOK線上指示PDF](https://intl.okayama-u.ac.jp/master/wp-content/uploads/2026/09/Online-Instruction-2027-2028.pdf)第1–4頁實際讀取，補齊目的陳述、健康表、推薦信、護照、正式成績單、照片及條件式英語證明。2027秋5/15與2027春2026/11/15分開；沒有虛構截止時分，仍須確認臺大提名、EPOK適用性、表格簽署與系統規定。
- **UdeM（115）**：[Application documents現行頁](https://international.umontreal.ca/english/international-students/choosing-udem/student-exchange-program/application-documents/)已讀取學習協議、1頁動機信、成績單單一PDF及當期修課PDF，出生證明限錄取後；法語／英語、作品集、音檔及推薦信依學程列為條件文件。網頁無年度，標現行參考未確認當期，不聲稱2027/28學程文件完整。
- **希望出航**：[116-1母校申請公告PDF](https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/09/116學年度第1學期-國立臺灣大學希望出航出國交換學生獎學金-申請公告.pdf)第1–3、5–6頁核實，補入`scholarships.json`、dashboard及exchange-info。包含12/2經濟證明、12/10 16:00獲獎公告、12/29 16:00契約三份、證明12/31有效，一般學生放棄首輪學校（含改走第二階段）撤銷與經濟不利例外，未繳核銷文件三個月／休退學等兩個月全額返還、未按時入學／取消延遲資格規則及核撥月份。範圍為116-1校級公告；院級不自動套用。公告只列日期或月份者未補造日／時分。

**完整度沒有升格**：288校名單比對不是全部資料完整；文件欄位仍180校`not_confirmed_no_text_evidence`、96校官方參考未確認當期、2校現行無年度參考、3校當期部分核實、1校前期參考、6校缺欄位。`fully_verified_current_cycle_count=0`。缺來源或尚未取得新版不等於官方未公告。流程仍`pending_review`／`published_at=null`，沒有為衝突或未核實的host期限建立確定提醒。

## 重建與測試

新增`sources/ntu/2026-10-08-audit.json`與`2026-10-08-audit-evidence.json.gz`，`build_ntu_catalog.py`將補充套用於原快照，provenance保存補充JSON SHA-256。原始資格／繳費資料保留；重建逐檔一致。部分臺大PDF本地HTTP503，但已由瀏覽工具取得官方PDF內容，來源回執保留兩種讀取結果，不推論未公告。

API契約加上條件式欄位資訊，版本`2026-10-08.3`，快照已刷新。沒有修改憑證、安全設定、正式Supabase、migration或部署。

| 檢查 | 結果 |
| --- | --- |
| NTU audit／原整合、Advisor、資格、文件API、文件目錄、任務文件、流程快取、地區（9模組） | 125 passed |
| 儀表板、帳號條件同步、NTU migration靜態版本、流程context（4模組） | 22 passed, 1 skipped（隔離Docker PostgreSQL整合需明確opt-in，本次未啟用） |
| API、申請plan、時程API、校園位置（4模組） | 21 passed, 1 skipped |
| 最新補充provenance重建與NTU audit再次檢查 | 64 passed（與前列重疊，不相加） |
| Chromium臺大手機／桌面摘要、推薦／規劃／保存、既有兩校新制TOEFL、條件語檢表單 | 7 passed |
| Chromium既有文件產生、公開選校、規劃工作區與待確認日期阻擋 | 15 passed |
| JavaScript、Python編譯、Git空白與OpenAPI快照 | passed |

原有三個契約模組在修改前`230629ce`及修改後均為**20 failed, 60 passed**，失敗identifier集合完全相同；詳見[`ntu-second-audit-baseline.json`](ntu-second-audit-baseline.json)。未冒稱全套測試或CI通過。此環境的結果與上一輪21失敗紀錄有一项差異，因此以本次實測為準。

```bash
.venv/bin/python scripts/build_ntu_catalog.py --output-dir /tmp/ntu-rebuild
.venv/bin/python -m pytest tests/test_ntu_audit.py tests/test_ntu_integration.py -q
PLAYWRIGHT_BROWSERS_PATH=/workspace/.abroad-cloud-tools/ms-playwright .venv/bin/python -m pytest tests/e2e/test_ntu_school.py -q
.venv/bin/python scripts/export_openapi.py --check
```

Chromium截圖本地保存於`/tmp/ntu-audit/browser/ntu-summary-{390,1440}.png`與`ntu-language-form-{390,1440}.png`。起始head的[Actions run 37721659862](https://github.com/blizzard-new/abroad/actions/runs/37721659862)是failure，jobs為0；推送後遠端結果另行回報。
