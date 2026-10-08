# TKU 同 SHA 驗收證據：89217e1

程式候選 **`89217e19d55f3ff615964594e5f83eeb6156ba85`**；原分支 `data/tku-exchange-20261008`、[draft PR #2](https://github.com/blizzard-new/abroad/pull/2)。此證據分支只有本資料夾的新增檔，程式／資料與其 parent 候選完全相同。**沒有宣稱 artifact commit 本身另跑測試**；每份本輪結果標記候選 89217e1。舊 a6035e3 不混入此目錄。

實際 **1424 passed、39 failed、8 skipped**（1471 cases）；main f6ad 完整 unit 基準 1348／39／8，39 個失敗 ID 完全相同、沒有新增／消除。29 個 TKU unit／runner、47 個相關 browser（TKU 12、NTU 7、共用 28）通過。**Runner exit 1、all_checks_passed=false**；wrapper collection exit 2、lockfile exit 1 均照實保存。8 步全部執行，起訖 `89217e19d55f3ff615964594e5f83eeb6156ba85`、dirty 空字串；每步前後均有效。851 個原母校 workflow 內容雜湊無差異。Python unit＋browser 一次呼叫，沒有混用先前 focused 通過結果。

- [摘要](summary.json)、[完整機器報告](acceptance-results.json)、[runner 起訖／每步 SHA／dirty／退出碼](run.json)
- [本候選原始 JUnit](suite.xml)、[39 失敗與 skips 比對](pytest-comparison.json)、[wrapper 原始 collection error](wrapper.xml)
- [main f6ad 原始 JUnit](baseline-f6ad/suite.xml)、[原 runner 記錄](baseline-f6ad/run.json)、[851 個實際基準雜湊](baseline-f6ad/workflow-hashes.json)、[基準 wrapper](baseline-f6ad/wrapper.xml)
- [跨四母校切換及詳頁](switch.json)、[wheel 字型打包](packaging-check.json)、[候選推送及 CI](remote-evidence.json)
- [Python 原始執行 log](pytest-unit-and-browser.log)、[跨校 log](tku-switching-and-details.log)、[wrapper log](inherited-wrapper-collection.log)、[lockfile log](lockfile.log)

## 原 PDF 與可獨立目視的 PNG

僅合成測試資料：本機隔離 E2E 帳號、中文「隔離測試假資料」、日文「これはテスト用データです」。沒有真申請人個資、護照、成績單或身份文件。兩份都是平台準備稿，**不是官方格式**。實際 PDF 文字、中日文答案、內嵌字型、pdftoppm stderr、頁數、深色字形像素與重載保存都有斷言；8 頁原尺寸 render 隨檔保存。

| 模板／viewport | 下載 | 目視 render | 瀏覽器證據 |
|---|---|---|---|
| tku-autobiography-preparation / 390px | [原 PDF](browser/tku-autobiography-preparation-390.pdf) | [封面](browser/tku-autobiography-preparation-390-render-1.png) · [答案頁](browser/tku-autobiography-preparation-390-render-2.png) | [畫面](browser/tku-autobiography-preparation-390.png) · [逐案例 JSON](browser/tku-autobiography-preparation-390.json) |
| tku-autobiography-preparation / 1280px | [原 PDF](browser/tku-autobiography-preparation-1280.pdf) | [封面](browser/tku-autobiography-preparation-1280-render-1.png) · [答案頁](browser/tku-autobiography-preparation-1280-render-2.png) | [畫面](browser/tku-autobiography-preparation-1280.png) · [逐案例 JSON](browser/tku-autobiography-preparation-1280.json) |
| tku-study-plan-preparation / 390px | [原 PDF](browser/tku-study-plan-preparation-390.pdf) | [封面](browser/tku-study-plan-preparation-390-render-1.png) · [答案頁](browser/tku-study-plan-preparation-390-render-2.png) | [畫面](browser/tku-study-plan-preparation-390.png) · [逐案例 JSON](browser/tku-study-plan-preparation-390.json) |
| tku-study-plan-preparation / 1280px | [原 PDF](browser/tku-study-plan-preparation-1280.pdf) | [封面](browser/tku-study-plan-preparation-1280-render-1.png) · [答案頁](browser/tku-study-plan-preparation-1280-render-2.png) | [畫面](browser/tku-study-plan-preparation-1280.png) · [逐案例 JSON](browser/tku-study-plan-preparation-1280.json) |

[手機分享網址選校／導航／重載畫面](browser/shared-home-query-navigation-390.png) · [JSON](browser/shared-home-query-navigation-390.json)；[桌面畫面](browser/shared-home-query-navigation-1280.png) · [JSON](browser/shared-home-query-navigation-1280.json)。其他原截圖與逐案例紀錄都在 [browser](browser)。

## 適用範圍與未完成項目

128 計畫列只含當期可核實日語二甄 4 校／7 名，校內 9/30 已截止，0 個可新申請；124 舊列為參考。四校 152 格只有 85 verified（55.9%），不冒稱全年度完整。可開始有限 UI／來源人工驗收；不能宣稱完整申請或 release ready。英歐／中文新版、系所提前期限、長崎 NICS／研究生映射、UEC2027、13 來源矛盾、JLPT UI 仍待解。

8 skipped：7 個 root conftest `Phase C data reviewed`、1 個 Docker opt-in，逐 ID／原因在比對 JSON。其他未選 E2E、Ollama integration 沒有執行，不能算通過。原始基準 wrapper 亦實際 collection error。uv.lock 問題在兩邊實際重現，沒有改 lockfile。候選 [quality run 37850482294](https://github.com/blizzard-new/abroad/actions/runs/37850482294) failure／jobs0，Supabase Preview skipped；取 log 實際 exit1／log not found，原因未核實，CI 沒有通過。

[程式分支人工清單／重現命令](https://github.com/blizzard-new/abroad/blob/89217e19d55f3ff615964594e5f83eeb6156ba85/docs/tku-acceptance-2026-10-08.md)、[逐欄／逐文件來源缺口](https://github.com/blizzard-new/abroad/blob/89217e19d55f3ff615964594e5f83eeb6156ba85/src/exchange_info/official_data/tku/acceptance_gap_audit.json)。沒有 merge main、部署或匯入其他分支。

## 檔案完整性

[manifest.json](manifest.json) 保存本目錄證據的相對路徑、長度及 SHA256。下載 [acceptance-evidence.zip](acceptance-evidence.zip) 後可直接目視 PDFs／PNGs，或執行 `python verify-evidence.py`；exit0 只表示 checksum 相符，**不是整套測試綠燈**。ZIP 自身的雜湊另在 [archive-sha256.txt](archive-sha256.txt)。
