# NUFS／熊本／龍谷五組查核修正

五組資料修正在 **2159409cacb6d8ac36bbafcc3ca6f2925f860fc9**，基準 **bb4cecd8030946e59bed494509d206c356e5c210**。後續提交僅修正測試；最終保存驗證為 **f99644adf87da3e4571d1fdbdb04dafcb989c57b**。資料與共享 runtime 自 2159409c 起未改。仍為 **74 partial／214、140 尚未逐欄整理、116 外校完整核准 0**，不是 74 校當期資料已驗收完成。

| 修正 | 凍結原文定位 | 平台結果 |
|---|---|---|
| 龍谷初次四類缺件 | application 網頁文字第 128–129 行，Spring 2027 | 六份指定附件另加證件照、護照照片頁、正式成績單、JLPT 有則附，初次十項；JLPT 不改為全員必交 |
| 龍谷住宿／到校條件件 | guide-en 原 PDF 第 13 頁，文字第 7–15、35–40 行 | 住宿兩項 NASIC 日期回覆／本人簽 Pledge；入寮時無日本可用帳戶者的開戶表與在留卡影本另列到校兩項，表格本體未取得 |
| 熊本語言範圍 | 英頁第 130、141、147 行；日頁第 134–139 行 | 非英語母語者的成績提交、J 非日本學生與日頁外国籍資格分開；N2 語言能力分開，不加國籍／醫療自動判定 |
| 熊本保險頻率 | 同 SHA brochure 原 PDF 第 8 頁、英日原圖 | 可選私人保險約 15,000 日圓一次性付款（One-time payment／一括），補人工摘錄，不作 116 現價 |
| NUFS 課程限制 | Study Abroad 英日網頁第 28–30 行 | 特別聽講學生不能修 GJP 課程，與錄取後不能換方案分開 |

[七個精確來源定位](../../../sources/ncu/next3-review-20261009/five-corrections-source-ledger.json)包含官方 URL、原件 SHA、native 文字 hash、PDF 頁／文字行、原文、來源查核與本次更正時間；原始下載及 native 文字未修改。[三校小索引](../../ncu-review-index/next3-2159409c/README.md)按固定 Git 候選回讀：51 欄、172 原文定位、527 JSON，最大 41,001 bytes。舊 71 與 bb806740 索引及舊驗證包未覆寫。

home 七件與 host 分開。NUFS 初次 13 項、熊本 COE 4 項、龍谷 14 項參考件，共 31 項在三種錄取／住宿狀態均維持當期待確認及正式下載封鎖。龍谷後四件不列初次全員必繳；銀行帳戶情況明列為須人工確認，不增加新自動資格規則。個人 checklist 勾選保存的是**階段準備進度**；文件名稱與条件逐件顯示在待確認區，不表示正式送件、116 核准或解除封鎖。

## 分 SHA 驗證與原始失敗

| 候選 | 結果與範圍 |
|---|---|
| [2159409c](candidate-2159409c/manifest.json) | 342 NCU、209 CGU／NTPU／NTU 共享、65 契約 gate，共 616 pass；6 既有 Phase C skip 原因保留。三校 390／1440 阅读 6 pass；新增保存 2 fail，測試誤找啟用文件 link，實際參考件在待確認區 |
| [5d253653](candidate-5d253653/manifest.json) | 24 API pass／1 新測試 fail（planner 使用 NCU 簡寫查不到任務）；閱讀再 6 pass／保存 2 fail（勾選後正常重繪使截圖元素脫離 DOM）。僅兩個測試檔與資料候選不同 |
| [cc3c37c7](candidate-cc3c37c7/manifest.json) | 改用實際畫面的完整校名、phase 與明列文件；25 受影響 API pass，OpenAPI 與 whitespace pass。與 5d 僅單一 unit test 不同 |
| [e7b2a47b](candidate-e7b2a47b/manifest.json) | 保存 2 fail：前兩階段達已同步／勾選狀態，到校標題定位因 planner 保留 orientation 未匹配。與 cc3 僅 browser test 不同 |
| [f99644ad](candidate-f99644ad/manifest.json) | 改按明列文件名找階段；390／1440 保存 **2 pass**，六項已通過的閱讀案例未改且 AST hash 驗證相同。每個寬度的三階段 ready／application_progress 均由實際 account workspace 讀回，reload 後仍全部勾選 |
| [2159409c 額外來源畫面](source-browser-2159409c/manifest.json) | 3 browser pass，十張段落／原文截圖。檢查檔在固定 checkout 外，無資料覆寫；另列補充測試 hash 與執行環境，未捏造單獨的開跑 clean 檢查 |

各候選的原 log、JUnit、未更改的失敗紀錄及截圖分開保存；沒有把失敗 manifest 改成成功。[verification-summary.json](verification-summary.json)列最終驗證來源與資料／runtime 相同的 SHA 邊界。OpenAPI 在資料及後續測試候選均一致；uv lock 工作區 cache 通過；[13 份生成產物](rebuild-manifest.json)與固定 checkout 重建逐位元組相同。當年度、其他年度阻擋、空名額、原文來源及三種條件狀態均在 API 回歸中檢查。

原始 pytest 失敗 log／JUnit 含工具輸出的尾端空白，未清洗原件；[十二個精確路徑／SHA 例外](raw-whitespace-preservation.json)與其餘 staged whitespace check 分開。原 log 受 repo ignore 規則影響，已在此資料夾逐檔明確加入，沒有讓索引引用未提交的 log。

修正前基準以新測試覆蓋層獨立重播，五組缺陷皆重現：[有效原 log](pre-fix-corrected.log)、[JUnit](pre-fix-corrected.xml)、[覆蓋層與早期無效探針說明](pre-fix-manifest.json)。第一次探針用了不存在的 audit points 屬性、一次工作區測試於 bundle 尚未複製時執行，原紀錄另留，不作產品或固定候選通過證據。

## 可直接複核的畫面與資料

- [16 張確實查看的段落／checkbox 畫面](actual-browser-review.json)另與兩張僅查看版面之長圖區分；附件來源包原有 104 張 unique render 不因重看增加計數。
- [NUFS 課程限制](source-browser-2159409c/browser/nufs-corrected-summary-1.png)、[熊本語言範圍](source-browser-2159409c/browser/kumamoto-corrected-summary-1.png)、[熊本保險原 PDF 第 8 頁摘錄](source-browser-2159409c/browser/kumamoto-original-p8-insurance.png)。
- [龍谷初次摘要](source-browser-2159409c/browser/ryukoku-corrected-summary-1.png)、[住宿摘要](source-browser-2159409c/browser/ryukoku-corrected-summary-2.png)、[條件開戶摘要](source-browser-2159409c/browser/ryukoku-corrected-summary-3.png)。
- [手機三階段保存回應](candidate-f99644ad/browser/ryukoku-390-saved-checklist.json)、[桌面保存回應](candidate-f99644ad/browser/ryukoku-1440-saved-checklist.json)，不含帳號 token 或真實個資。
- [18 份實際 API payload 與 digest](candidate-2159409c/api/manifest.json)、[source coverage](source-coverage.json)、[精確修正範圍與並行合併点](committed-scope.json)。其他 211 校資料、71 其他手寫記錄、1,454 其他來源不變；唯一來源 metadata 差異為熊本同原件視覺摘錄補句。

來源仍是同一 75 attempts：73 完整閱讀、207 native parts、104 unique 附件圖、74 份保留 response bodies 已複驗。ISA 403 原採集只有 metadata、未保留正文；龍谷 syllabus 200 僅 JS 入口。這些與真正官方明列待定日期分開。未增加新學校或來源查核數。

具體當期缺口仍包括中央 116 名額／學制／track、NUFS nomination 表及 arrival package、熊本承辦 STEP packet／住宿 system／當期指南、龍谷 116 入口與財力／表格版本、NASIC 回覆／Pledge／開戶表本體與指定期限、床具及退宿矛盾。未取得不冒稱官方未公告。851 跨校 workflow parity 專項及既有 Kyutech 根因未於本輪結案，未聲稱 full CI equivalence。

main f6ad1b8（含 NTU daad399）維持；CCU 5eadeb56 與 TKU 工作期間先更新到 e1c551a8、推送後又更新到 3cbe9760。[最後合併點清單](integration-points-latest.json)刷新至此次遠端觀測：本輪修正交集均為 0，整支 NCU 分支仍有 15／21 個共用路徑須後續整合；舊提交時的 scope snapshot 另保留。沒有 merge、部署、正式 DB、權限／credential 修改或對學校聯絡。

[b08afce3 遠端核對](remote-verification-b08afce3.json)顯示 branch 已推送、工作樹乾淨；Quality run 37911910786 completed/failure、jobs 0，combined status pending、statuses 0。這項遠端 CI 缺口未修、不冒稱完整 CI 通過。

[09:16 UTC 環境 healthcheck](environment-healthcheck.json)確認原環境、分支与保存內容，先前測試都正常結束，未觀測到測試中斷；沒有新開 execution environment。
