# NUFS／熊本／龍谷固定候選複驗

資料候選 **bb806740e702892e78d358973cb2c54b739d3dbd**，整合基準 **012b580b9c38b20da0e52394eef1428c2ea90261**。三校全部接入後才固定SHA，沒有第四校。後續 **ae169b3698129264274ca0e2bc3976cb483df2d7**只修正本輪browser測試定位、補展開卡片／桌面資格欄與完整摘要；資料、shared runtime及API schema與bb806740位元組相同。兩個候選各在乾淨checkout執行，起迄SHA／argv／cwd／時間與原log／JUnit見各manifest。

[逐校來源coverage](source-coverage.json)：75新source attempts＝56凍結原件＋19補查；HTTP200為74、有效下載73、有文字72、每頁有文字71、完整閱讀73。207個native page／HTML／DOCX／sheet段與104張附件渲染圖分開。中央116適用核准仍0，名額None／agreement_only，當期host截止仍無提醒。整體74 partial／214，還有140校未完成逐欄整理，不能稱全校完成或可部署。

| 檢查 | 固定SHA | 結果 |
| --- | --- | --- |
| NCU API／文件／來源／生活／年度、過期與空值 | bb806740 | 332 pass，0 skip |
| 長庚／北大／臺大與共享回歸 | bb806740 | 209 pass、6既有Phase C skip |
| 北大／frontend contract／RAG既有gate | bb806740 | 65 pass |
| OpenAPI、71校凍結索引、3個JS syntax、scope whitespace | bb806740 | pass |
| 本輪三校API再核 | ae169b36（same data） | 14 pass |
| 手機390／桌面1440三校實頁內容 | ae169b36（same data） | 6 pass |
| OpenAPI、uv lock工作區cache、test-only diff | ae169b36 | pass |

6個skip均由既有root conftest的Phase C規則產生：4個CGU bundled／backfill、2個workflow cache／department override。未解除skip或稱這6個case已執行；全部name／reason在[bb manifest](candidate-bb806740/manifest.json)。CGU/NTPU/NTU bundle及shared runtime本輪未改，其他實際執行的相關API／條件／生活回歸照表列結果。

bb的browser原結果 **2 pass／4 fail**保留於[原manifest](candidate-bb806740/manifest.json)、log／JUnit與22張原截圖。4項因NUFS／龍谷locator仍寫orientation，但既有中文介面顯示新生說明會而找不到element；Aria snapshot已顯示對應內容。只修兩處title定位並加實際可見內容驗證，未改翻譯或提高timeout；ae的六案均讀完初次附件、source failure、COE／visa／購票／到校、生活頁。原Kyutech根因仍open，本輪未重跑。

bb的uv lock失敗因預設 `/home/agent/.cache/uv` 唯讀；ae用明列於script的工作區 `UV_CACHE_DIR` 同一份lock通過，未改依賴。沒有以舊結果覆蓋原failure或宣稱兩個SHA每一項都pass。

新40張截圖全部保存；其中[18張確實查看的圖](actual-browser-image-review.json)覆蓋三校手機卡片、桌面列表、摘要、生活頁與選定流程。完整overview圖在view tool有縮小，瀏覽器亦將其餘摘要details展開並以inner_text檢查，沒有稱另外22張圖已人工看過。[15個真實API回應與3個dashboard row](candidate-bb806740/actual-api/manifest.json)保留home7件與host分離、23項host參考件在三種錄取／住房狀態均需確認且無正式下載。

[精確commit scope](committed-scope.json)核對舊71手寫記錄、舊政策與1,380來源未改；211其他學校四份generated資料未改，partner research全部214未改。56來源凍結包、2637de2的71校索引、CGU／NTPU／NTU正式bundle原樣保留。新[三校小索引](../../ncu-review-index/next3-bb806740/README.md)以bb的Git原件回讀51欄／171原文定位，baseline明列012b580，沒有覆寫舊索引。

[並行合併點](integration-points.json)：main f6ad1b8、CCU 5eadeb56、TKU新5af863f5，整条NCU分支分別15／21個共用路徑。本輪三校delta與peer共用路徑交集0。只有列出，沒有合併或覆寫peer。

剩餘具體缺口見各校gaps與[來源README](../../../sources/ncu/next3-review-20261009/README.md)：116名額／學制／track、NUFS nomination／實際arrival package、熊本STEP承辦packet／校內宿舍system與新梯次指南、龍谷完整online欄位／住房另送表與條件矛盾；ISA403的response body未保存、龍谷動態syllabus只取得入口。只有NUFS春2027到達日與部分JPETS生效日等明文待定標官方未定，不把取得失敗當未公告。

不是full CI equivalence或當期資料驗收。851跨校workflow parity未重跑；遠端Quality狀態在最終push後另查，不以本機pass代稱遠端CI通過。未merge main／peer、deploy、正式DB、credentials/security或聯絡學校。保存檔案hash與原生空白精確排除清單另列，原件不trim。
