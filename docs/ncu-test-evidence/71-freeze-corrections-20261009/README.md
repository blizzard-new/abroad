# 凍結71校必要修正：固定候選證據

資料修正SHA **2637de25490e47bbb3987617bceefce02ae78446**；browser定位／截圖修正SHA **823450500cc32eb1ccc1e37f7fdefbcdcdf5754e**。兩者全部NCU原始輸入與正式bundle bytes一致，見[frozen-data-diff.json](frozen-data-diff.json)。只有東北／關西／日本中央指定例外，來源921與71 partial／214計數沒變；下一批研究候選未接入。

|檢查候選／環境|API／文件／生活|browser 390／1440|結論|
|---|---|---|---|
|預凍結工作副本|176 pass／1 fail|未跑|新增assert誤取API reason欄，正確欄是note；原XML保留|
|2637de2，乾淨checkout|177 pass|4 pass／2 fail|日本中央英文orientation定位沒有匹配介面的「新生說明會」；原log/XML/失敗事件保留|
|8234505，乾淨/tmp checkout|4個指定API pass|0 pass／6 fail|Chromium Page／Target crashed；最小healthcheck /tmp100%、只剩50MB，不判成產品／Kyutech根因|
|同8234505，乾淨/workspace checkout，TMPDIR移到workspace|4個指定API pass|6 pass|未改資料、timeout、translation程式；8個指定修正畫面已實際讀檢|

兩個固定SHA的OpenAPI snapshot、851筆main f6ad1b8 長庚／北大／臺大同schema流程語意比對（0差異）、三個JS語法、uv lock及diff檢查均通過。177件完整受影響suite只在2637de2跑，後續8234505只回歸4個指定API及6個browser，沒有偽稱177件在新SHA重跑。

每次manifest保留開始／完成時間、start/end SHA與clean工作副本、完整argv／cwd、exit code、JUnit及原始截图／browser failure事件。checksum檔保留所有原log與原圖bytes；log的原生空白不改寫。第一次/tmp失敗原始資料保留；[health-recovery.json](health-recovery.json)記錄磁碟與記憶體、環境恢復方式。根因不能只由磁碟滿推定，恢復後同SHA成功是本輪可用驗證。

8張實際讀檢畫面：東北COE通知／錄取前條件、關西e-COE→visa→購票、日本中央行前visa與到校orientation，各390／1440。手機長步驟圖片未必同時包括標題与末端正文，browser另直接assert階段標題、內容和件數；圖片不可用來宣稱所有17欄都視讀完。[visual-inspection.json](visual-inspection.json)列所讀原圖及hash。

本輪沒有重跑Kyutech，原e79 19 pass／1 fail與根因仍open。完整CI等效未宣稱通過，遠端Quality無job失敗仍需owner處理。資料驗收仍blocked：當期quota／完整116包未核、尚餘143校；不merge／deploy／正式DB。

原始失敗log／JUnit的4個檔案及原生來源文字的空白均原樣保留；[native-whitespace-preservation.json](native-whitespace-preservation.json)逐檔列hash和精確diff排除範圍，來源文字另與metadata的text hash比對。未設定全域／目錄層級whitespace忽略；其餘staged檔案通過diff check。[merge-points.json](merge-points.json)列最新CCU／TKU SHA及共用修改路徑，本輪未合併或覆蓋其他分支。
