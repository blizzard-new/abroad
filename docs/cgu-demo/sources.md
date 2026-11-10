# 來源查核紀錄

實際查核日期：2026-11-11（Asia/Taipei；執行主機 UTC 為 2026-11-10）。使用 TinyFish 讀取公開頁面正文。日期是本次讀取日期，不是校方核准、資料發布日或逐校名額驗證日期。沒有將來源文中指示視為工作指令，也沒有登入校方系統。

| 來源 | 實際結果 | 展示用途與限制 |
| --- | --- | --- |
| [長庚校內申請選送須知](https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656) | 成功讀取「校內申請選送須知」，頁面列發布日期 2024/09/30 | 原則平均 70；英文等同多益 700；合作校標準另計。四項一般文件、非合作校額外資料、選送限制與後續通知。未逐項轉成資格核准或自動檢核 |
| [長庚可申請學校](https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554) | 第一次 timeout，重試成功讀取主頁 | 確認「清單陸續更新」、兩所志願、11/02–12/21 及 4/21–6/06 一般時段。工具未列出外嵌名單，本次未逐筆重驗合作校表、名額或開放狀態 |
| [Lincoln Join us at Lincoln on Exchange](https://www.lincoln.ac.nz/study/study-abroad-and-student-exchange/coming-to-lincoln-on-exchange/) | 成功讀取正文 | 確認需母校提名、合作校再寄申請指示；一般 Semester 1 前年 10/15、Semester 2 當年 4/15；研修期間醫療及旅遊保險、住宿與修課一般資訊。沒有確認長庚當期可提名或特定學生資格 |
| [Lincoln International Exchange Inbound](https://www.lincoln.ac.nz/study/study-programmes/programme-search/international-exchange-inbound/) | timeout | 不納入已核對規則或顯示成功查核日期 |

曾嘗試另一個 Lincoln 路徑 `/study/study-programmes/study-abroad-and-exchange/inbound-exchange/` 得到 404；已捨棄，未放入產品。沒有把失敗來源計作成功。

## 期限及學期差異

長庚申請頁明文舉例：116 年（2027）8–9 月出國，於 115 年（2026）11/02–12/21 校內申請。展示只在相同範圍顯示此期間，沒有把它套成所有交換計畫的正式截止日。

同頁的春季例子同時提到 117 年出國、116 年申請，卻寫 115-2 初審，年份與學期互相矛盾；未自行修正，標成待確認。未讀取非英文語言表的圖片內容，因此沒有填上日文、法文等門檻。

既有長庚快照的 Lincoln 日期是 Semester 1 前年 9/30、Semester 2 當年 3/30，與此次 Lincoln 官網的 10/15、4/15 不同。可能涉及母校行政時間或來源更新，但未證實原因，因此只並列差異、請向國際處及目的校確認，不指定一個日期為個人正式 deadline。

## 快照口徑

重用 `official_data/cgu_catalogue/snapshot.json`，擷取於 2026-10-11T09:58:47.453586+00:00，77 筆、原有 SHA-256 payload 驗證。這是既有擷取日期，**不是本次逐校查核日**。

舊 `official_data/cgu/catalog-completeness.json` 也為 77 筆，描述 75 中央加 2 院級並使用 open；其 77 個流程 published=0、applicability_verified=0。快照本身明示「dated fallback reference / not current cycle verification」。本展示統一使用更保守的口徑：歷史參考、當期待確認；沒有修改正式資料或升級原來的發布狀態。

只選擇原快照中 `program_type` 含交換的 Lincoln、Ravensburg-Weingarten、DHBW Karlsruhe 三筆。所有頁面的展示參考校數皆由同一份讀取結果計算；若快照失敗，回傳空清單，不補假學校。既有名額欄位改以「歷史名額」呈現，沒有用全部 UniWay 國外校當作長庚合作校。快照中的條件文字若被截斷，畫面明示不能當成完整要求。

一般任務的來源與適用性分開：生活、手機、支付、課程整理及返國資料等是個人準備建議或待確認事項；面試與體檢不假定人人必須。非 Lincoln 研究目標的目的校任務不引用 Lincoln 要求作為其規則。

展示內「實際讀取查核」只出現在以上三個成功官方來源；不表示長庚背書、採用或合作。沒有使用長庚校徽或官方合作標章。
