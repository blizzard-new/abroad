# 九州工業有界診斷（2026/10/9）

原候選e79e0ba50cd247284f8a61b86f6fb5ff4c9a6409的20個browser為19通過／1失敗，必要本機驗收仍false；本資料夾不改標結果。所有實驗皆使用同一乾淨固定checkout，沒有改產品、原斷言或timeout。未merge、部署或正式DB操作。

原1440 workflow Chromium requestStart 0.205ms、responseStart7385.139ms、responseEnd7397.792ms：等待首位元組7384.934ms，下載12.653ms。Playwright callback兩端差7663.42ms受回呼排程影響，不當成精確server處理時間。destination-profile同時開始、同時200，等待首位元組7392.303ms，下載3.785ms。原390在同一46495 server先通過，workflow首位元組1258.247ms，因此「第一次冷快取」不足以單獨解釋後來1440失敗。1440記錄80次public-translations請求，39081次；沒有payload、server cache token、thread queue或handler timing，不能推定翻譯是根因。無pageerror/requestfailed亦不表示內容在原5秒內準備完成。

兩次有界browser儀表執行在04:17:45–04:20:36 UTC。第一次原斷言pass，但插件誤掛到duplicate conftest，server-events只有diagnostic_start，量測無效。第二次正確掛到e2e.conftest，並行cProfile啟用引發ValueError: Another profiling tool is already active及HTTP500；這是診斷插件引入的失敗，不是產品重現。兩次原生log/XML/事件保留，停止browser複跑。第二次的queue紀錄不能作原失敗的handler時間證據。scripts/server-diagnostic-v2.py為第二次實際插件，第一版插件未另存；run-v1.py保留第一次實際driver。

另做一次最多3請求的隔離ASGI並行組：workflow200、4284.337ms（Server-Timing4277.968）；destination-profile200、493.768ms；完整度200、5293.267ms。workflow handler4259.487ms／thread CPU3788.488ms，該handler read_jsonl六次累計1934.775ms／CPU1632.238ms；完整度的_cached_workflows等待3828.787ms／CPU0.301ms。嵌套span不可相加當总處理時間。這個冷資料目錄組沒有browser boot、translation及font載入，不能視為原1440暖頁重現。

目前可驗證假說：流程catalog signature失效／建構等待，或詳情同時的workflow、完整度、profile、翻譯及字型工作造成CPU/GIL或server排程壓力。下一次有理由觸發診斷時，先用不啟用cProfile的純ASGI／handler monotonic timing，再記錄cache signature、cache hit/build/wait分段，維持原1440操作與斷言；對照同module先390後1440。先驗證實際fixture模組與四個handler皆完成200，儀表500立即停止，不靠pass結案。

根因仍open；已有一次純重跑pass也不關閉根因。本次不再執行browser診斷，接續三校公開資料查核。checksums.json可對原始與保存內容驗證；失敗原log/XML保留native trailing whitespace，只有這些原始證據檔可個別排除diff空白檢查，未改全域規則。
