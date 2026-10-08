# CCU 公開動態來源補查與最終候選

接續第二十五輪限定段落處置，實際處理 Mapúa 與 UNINTER 兩個公開動態入口，追加 10 份保存來源；原 956 份 raw JSON 與附件不覆寫。

UNINTER 表單實際標題為 Autumn 2026 / Spring 2027，公開 Start now 後可讀 44 題至 Submit。沒有填寫或提交。已將實際官方 URL、表題、原文、hash、查核時間接到學生文件 API。問題中的短期、實習及多種交換期間選項不作各計畫／學制皆開放的證據，也不把開頭 Required 當全部 44 題必填。Learning Agreement 與 Image usage 等另行附件未核齊，整個 application_forms 欄仍待確認。API 的 official_form_verified 驗證下載附件 hash，因此線上入口仍為 false，與當期表單正文已核實分開。

Mapúa 實際展開 AY2026–2027 校曆內嵌 JPEG 並目視核讀：第三季註冊 2027-01-26 至 29、上課 02-01 至 04-24；第四季註冊 04-27 至 30、上課 05-03 至 07-17。保存影像及人工轉錄的指定日期；註冊日不當交換申請期限，不修改 factsheet 的 November 30, 2027 錯年矛盾。

從實際 ILRAD tab 取得 34 頁 International Handbook，正文版權 ©2026，費用注明 April 2026 估計。保存並閱讀全份抽取文字，但未聲稱每個圖像流程已核讀。第 18 實體頁 inbound 與第 14–16 頁 outbound/SGE 分開；第 19 頁提名區間未標年份／日，不猜 2027 春確切日期。第 32 頁外籍生抵達前、全停留有效的醫療／健康保險新增為待確認與 post_offer；第 22–23 頁不同幣別估計不自行換算為當期一致價格。非學位網頁 SSP／旅遊簽與手冊第 28 頁泛稱 9F，保留身分／國籍／停留別待核；此資料不適用於 AMU 的博士生專屬保險。

最終候選資料：104 所目錄、52 所非零名額、3 所名額空白、49 所灰字參考；55 所工作流程／概要。966 份保存來源。海外 935 欄為 307 current、334 pending、202 missing、71 conflict、20 reference、1 explicit_not_announced；39 校至少一項 current，0 校全 17 欄 current。文件 33 校／250 項：185 current、65 pending、59 conditional；清單完整性仍部分。概要 385 欄仍為 178 current、126 pending、61 missing、20 reference。

323 筆凍結佇列的分類不變：102 筆指定欄位映射、21 筆完全相同保存文字的指定映射承接、64 筆參考、60 筆範圍排除、69 筆索引、7 筆存取限制。149／149、174／174 都有可核對處置，不聲稱全政策已讀、所有公開來源窮盡，或任何新版官方尚未公告。兩個動態入口已處理，仍待核當期錯年、個別通知、未提供的附件模板及其他政策／圖像。

標準 Chromium 兩入口回傳 ERR_CERT_AUTHORITY_INVALID；一般 requests 保持 TLS 驗證，兩入口 HTTP200。以一次性 browser context 診斷公開內容，未更動系統／repo 安全或信任設定。來源記錄明載此方法。公開擷取程式 `scripts/fetch_ccu_public_renders.py` 只寫 clone 外、不判定年度、不輸入答案或提交；完整校別資料與 evidence 另人工核讀入模。

完整回歸在 `6ea9368` 找到 AMU 的博士生保險誤入一般交換欄位，該次中止並保留失敗證據；`d3b97d9` 恢復 AMU 保險 missing，同時明確保留龍谷當期索引的機構核章要求，沒有放寬舊測試。之後的完整結果只歸屬新的最終候選 SHA。舊 `77dfd84` 的 88 份父 session 核驗證據保持逐位元組不變。

`73cb7ca` 的完整候選檢查另找到 DNTU 生活摘要混入待核的頁尾時段，以及 wheel 少包八份公開 HTML 與一份 JPEG。保留該次中止證據；DNTU 摘要恢复先前保守內容，詳細時段矛盾仍在 research_note／逐條 evidence，不放寬既有測試。共用 `pyproject.toml` 只追加兩項中正專屬 `public_responses/*.html`、`*.jpg` package-data 規則，使來源檔隨 wheel 一起交付。

本輪新增程式、測試、資料與生成產物皆在 CCU 範圍。沒有額外共用 registry/API/UI/資格邏輯修改；新增共用打包設定及分支既有共享適配仍依交接清單由父 session 統一整合。未 merge、部署、聯絡學校、登入、提交申請或操作其他 session 的工作目錄。
