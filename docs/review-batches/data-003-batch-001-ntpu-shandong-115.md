# DATA-003-BATCH-001：臺北大學 × 山東大學 115 學年度來源適用性

- 狀態：已備妥官方證據，等待兩位真人內容管理者逐頁查核
- 系統狀態：尚未建立正式 pending revision、尚未核准、尚未發布
- 母校：國立臺北大學
- 合作校：山東大學
- 計畫：交換合作協議
- 流程學年度：115
- 流程梯次：秋季／全學年梯次、春季梯次
- workflow_id：`workflow-6889039f2433b41365efba62`
- 證據整理日：2026-08-13
- 機器可讀候選：`docs/review-batches/data-003-batch-001-source-candidates.json`

這份批次只整理可供真人審查的證據，不代表核准結果。內容管理者仍須親自開啟每個官方頁面，確認頁面未變更，再從 `/admin/content-review` 建立待審版本並逐筆勾選。Codex 不代替審查者 A 或 B。

2026-08-13 重新查核時，山東大學官方交換生列表已列出 `SHANDONG UNIVERSITY EXCHANGE PROGRAM（AY2026-2027）`。列表原始連結指向校內 HTTP IP，但同一檔名在 `www.istudy.sdu.edu.cn` 官方網域已有可下載的 HTTPS PDF；本次取得 8 頁、SHA-256 為 `3d05004cdd7f119ec330df33f59055b45805ce8eb77ce5fb6b2f2160fc9645e0`。這只建立「強候選」，不自動證明它與列表項目、臺北大學提名校區或現有每條規定完全相符。

## 逐來源處置

| # | 官方來源 | 可證明的適用範圍 | 待審建議 | 仍有限制 |
| ---: | --- | --- | --- | --- |
| 1 | [國立臺北大學 115 學年度赴外交換公告](https://new.ntpu.edu.tw/news/68d5e81963f5a608851f74c1) | 明列 115 學年度、校內申請期間與校內流程 | 真人確認後可填 `effective_academic_year=115` | 不能單獨證明山東大學各校區、合作校提名或申請期限 |
| 2 | [國立臺北大學 2026–2027 Outbound Exchange Program Guidelines](https://cms-carrier.ntpu.edu.tw/uploads/2026_2027_Academic_Year_Outbound_Exchange_Program_Guidelines_1e5870e83d.pdf) | 明列 2026–2027／115 學年度校內規則 | 真人確認後可填 `effective_academic_year=115` | 仍須搭配當期名額表及合作校通知 |
| 3 | [臺北大學國際事務處檔案下載](https://new.ntpu.edu.tw/oia/files) | 一般檔案索引 | 保持年度空白 | 索引頁本身不能證明某一檔案適用 115 學年度 |
| 4 | [Shandong University Exchange Student Programs](https://www.istudy.sdu.edu.cn/English/Programs/Non_Degree_Programs/Exchange_Student_Programs.htm) | 官方列表明列 `AY2026-2027` 交換計畫 | 真人確認後可填 `effective_academic_year=115` | 不能單獨證明臺北大學已獲該梯次名額或完成提名 |
| 5 | [School of Economics Exchange Program 2026–2027](https://www.soe.sdu.edu.cn/info/1077/1531.htm) | 經濟學院 2026–2027 秋、春季提名與申請資訊 | 真人確認後可填 `effective_academic_year=115` | 頁面列出的合作夥伴未直接列出臺北大學，只能作學院程序參考 |
| 6 | [Shandong University, Weihai 2026 Fall Information Sheet](https://ipo.wh.sdu.edu.cn/enistudy/info/1049/2341.htm) | 明列 2026 秋季、提名 2026-05-15、申請 2026-05-30 | 真人確認後可填 `effective_academic_year=115` | 僅限威海校區與 2026 秋季；尚未證明臺北大學學生會被提名到該校區，因此不得先建立學生提醒 |
| 7 | [Shandong University Exchange Program Information Sheet](https://www.istudy.sdu.edu.cn/__local/C/1B/28/02857EA761292B8A6B2A4F8025C_BFE025DD_28DAE.pdf) | PDF 內文明列 2022–2023 Academic Year | 不得填 115；待真人確認後，候選替代為 [2026–2027 官方 HTTPS PDF](https://www.istudy.sdu.edu.cn/PDF/251201jiaohuanshengzhaoshengjianzhangxianshangban.pdf) | 新 PDF 明列 2026 秋季／2027 春季、提名與申請日、資格及文件，但仍須確認實際提名校區與逐條引用；未確認前舊 PDF 仍是發布阻擋 |
| 8 | [山東大學首頁](https://www.sdu.edu.cn/) | 學校官方身分與一般入口 | 保持年度空白 | 一般首頁不能證明交換梯次、文件或期限 |

## 預期候選結果

- 流程層級維持 115 學年度。
- 原先最多只能確認 5／8 個來源。若兩位真人確認第 7 筆可由 2026–2027 HTTPS PDF 等價替換，最多可進到 6／8；第 3、8 筆仍必須保持年度空白。
- `applicability_status` 必須維持 `needs_confirmation`，不可顯示為全部適用性已核對。
- 不得把山東大學經濟學院或威海校區期限直接套給所有申請山東大學的臺北大學學生。
- 不得建立精確期限提醒；需先由臺北大學確認實際提名校區、合作單位及該生適用梯次。
- 建立或修改 pending revision 後，核准數必須為 0／2；兩位真人重新核准前不得發布。

## 工作台操作

1. 內容管理者 A 登入後，在「既有流程待納入雙審」搜尋「山東大學」。
2. 核對母校、計畫與 workflow_id 後建立待審版本。
3. 展開「補正適用學年度與來源證據」，親自逐頁開啟上表來源。
4. 只勾選當次實際核對且適用範圍清楚的來源；不得勾選一般索引、首頁或 2022–2023 舊 PDF。
5. 修正說明須寫明校內 115 學年度、山東大學校區限制與舊 PDF 阻擋。
6. 儲存後載入版本對照，確認未勾選來源仍空白、公開學生內容未變、核准為 0／2。
7. 內容管理者 A、B 分別再次開啟官方來源並留下獨立說明；過期來源未處理前，兩人都不得核准發布。
