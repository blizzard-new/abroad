# 68 partial候選95b30ac的原始結果與失敗

固定SHA `95b30acbdfbfadb02ce8d97a4cd7ac4d686f279b`於2026-10-09 03:02:33–03:15:21 UTC執行，起迄同SHA且clean。305 NCU、193 shared＋2skip、65 gate、OpenAPI、main851流程同schema／multiset0差異、三個JS、lock與候選diff通過。20個來源範圍browser為 **14 passed／6 failed（431.81秒）**，`necessary_local_tests_passed=false`；不能稱本候選驗收通過。

新三校六個390／1440實際內容案例通過。東北兩個及北海道四個案例因新版人工閱讀註記優先序遮掉既有「原件57／83頁」閱讀範圍文字而失敗；不是以拉長timeout處理。後續改合併兩種明示範圍，新候選另驗證，不改寫本次原始失敗。

[原始manifest](candidate-95b30ac/manifest.json)、log與JUnit、20筆browser事件、42張原始PNG及6張failure PNG均保存。圖像ZIP逐檔SHA列於`checksum-manifest.json`。候選final畫面與original副本逐張bytes一致；原trace ZIP仍留/tmp，公開事件不含headers或response body。大JSON／失敗log／JUnit確定性gzip保留原bytes，沒有清洗原生空白。精確.log檔強制加入，未改全域ignore。

preview-v1僅工作樹預檢：42 passed／1 failed，Word年份被分成原生文字段而測試未合併空白。preview-v2修正單例1 passed，但browser六個全失敗：TCU403不是已取得文件、富山原文年份空格與測試不一致、福井人工範圍metadata未出現在UI。預檢原始失敗與六張failure圖另存，不冒充固定SHA結果。後續95實際新增來源區塊，再跑的六個新案例通過仍不能覆蓋整組20的六個回歸失敗。

95 GitHub Quality37877659259 failure／0 jobs，Supabase113649831142 skipped，combined pending；原始API讀取於03:06 UTC，與本機測試獨立保存。資料仍68／214 partial、146待整理、116全欄核准0。CI與資料驗收都未通過。

[合併點](merge-points.json)記錄main f6ad1b8、CCU5eadeb5交集15、TKU4133667交集20；只讀fetch與path比對，沒有merge或覆蓋他校。前一固定[2ce完整62 browser通過證據](../japan3-65-20261009/README.md)與[3b／9bf歷史失敗](../performance-20261009/README.md)保持獨立，沒有宣稱舊GPA5秒失敗根因已關閉。
