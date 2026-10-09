# TKU CI 逾時續查（2026-10-09 UTC）

固定候選 b455a18ce12ebf679f12c4f8ef4295f6546b2c60 的 PR run 37861005211（job 113596834594）及 push run 37861000761（job 113596801704）都結束為 cancelled。GitHub annotations 明示 exceeded the maximum execution time of 45m0s；不能猜為手動取消、配額或環境斷線。Web pytest 最後12%，已有 F，沒有完整統計／案例名稱；bundled資料未變動後檢查 skipped。安裝、uv lock、語法、frozen OpenAPI、31 migration解析、依賴稽核及隔離 Supabase runtime 有實際成功 log。原始證據177檔逐blob核對，已推送獨立證據commit [e33127d](https://github.com/blizzard-new/abroad/tree/e33127d413cd83dc15173c3f18d4cd5bd55228d5/docs/tku-acceptance-evidence/b455a18)。原89217e1證據1159874保持不變。

本地同SHA重現早期10案例：7通過、3失敗、141.18秒。手機期限案例捕捉到503，但登入完成前的catalogue hydration會另發請求覆蓋狀態；心得原文測試期待 I cooked，實際UI提供中文整理／官方來源提示；登出工作區案例在背景401清除DOM後仍fill，等滿30秒。獨立main f6ad1b8同10案例為8通過、2失敗、153.16秒，後兩項亦失敗；這只是對照，不構成驗收豁免。首次本地coverage約6.9秒、period options約5.8秒、若干translation約5.2秒，是觀測到的請求時間，不能冒稱全部遠端延遲因果已查明。初次本地诊斷忘記指定已下載browser路徑而10 errors，原錯誤保留，重設既有PLAYWRIGHT_BROWSERS_PATH後才取得有效結果。

有界修正保留所有實質斷言：期限案例等登入catalogue requests結束，再注入reload失敗；登出案例接受背景401先移除私人表單或本次寫入401，仍必須開啟登入、清除candidate與localStorage，另外直接核對隔離JSONL未保存過期寫入。修正後同10案例9通過／1失敗，134.21秒；心得原文差異仍保留失敗，未以改產品行為或刪除要求取得綠燈。正式API、資料、權限完全未因此改動。

CI依實際收集browser案例數按檔案分四組，module fixture不跨組；browser 73／73／74／73，其餘unit/integration放第0組。獨立collect-only核對原1757個node IDs與四組union完全相等，0漏項／0重複／0新增，原skip標記不變。fail-fast=false使某組失敗不取消其他組。逐案例名稱、phase、結果、耗時与失敗內容即時輸出，最後生成JUnit；不宣稱runner暫存JUnit已被上傳。資料未變動檢查使用always()，測試失敗仍檢查；逾時job中是否可執行以实际jobs為準。固定45分鐘上限、隔離DB20分鐘上限、permissions、secrets、actions pins、依賴版本都維持原值。9項workflow／dependency contract檢查及actionlint通過。

續查需要在新的精確SHA重跑本地10步驗收並取得新遠端四組終態，不能借用b455a18結果宣稱新SHA通過。新增共用整合點為quality.yml、scripts/run_web_quality_tests.py、兩個browser測試與workflow traceability斷言；清單同步在tku-shared-integration-risks-2026-10-08.json。沒有merge、部署、正式DB或憑證／存取／付款／安全設定變更。

## 4e6cabd 完整遠端失敗後續查

PR run 37866158645 四組均 failure 終態，非逾時取消，資料後檢四組成功。完整archive下載經 gh api 成功；gh run view 與connector第0組輸出不完整，不能以其1032案例子集當全集。完整1757唯一case為1675 passed／66 failed／16 skipped；第0組1470／51／16，其餘67／6、73／1、65／8。原始16.9MB第0組log按2000行分段，可逐bytes重組；241檔已推送artifact b0cb3b7124c10865ebfd58c0f8da6764e3942ef3，全部遠端blob SHA吻合，ZIP SHA256 ac7a5a5862214719c0848698ce7da1204fc8c4af7fe011edb491772ee721ce9a。兩個passing合成userinfo URL參數被GitHub遮罩，原收集清單另保留。原workflow沒有upload，因此runner回收後四份原始JUnit無法追回，不重建冒充原始JUnit。

四個TKU PDF render失敗均因runner缺pdftoppm；新workflow由Ubuntu官方apt安裝poppler-utils，保留視覺測試。新增固定SHA upload-artifact v4.6.2（GitHub官方tag解析ea165f8d65b6e75b540449e92b4886f43607fa02）保留每組原JUnit、pytest log、node清單、partition、退出碼30日；原三個action pins、permissions與secrets不改。

38個共用browser與24個既有API/UI失敗全部保存於scripts/tku_ci_prior_failures.json。同runner控制用immutable main f6ad runtime、原4e6測試原碼、相同interpreter/套件/Chromium/系統依賴，按原組別跑62項。TKU四PDF沒有main對照而保持候選必跑。控制JUnit、log、實際pytest退出碼與imported API路徑保留；普通main断言失敗是診斷結果，不作候選驗收豁免。控制資料與checkout位於upload目錄外，只上傳診斷產物，不上傳帳號或執行資料。

最小UI修正：恢復已實作工具在「其他工具」的入口；移除論壇隱藏返回控制的CSS，首頁依原history仍disabled；心得及生活資料的原始摘要在details明確展開後呈現並escape，pending翻譯明示未完成、不把原文當中文譯文。測試mobile先開真drawer，論壇走實際論壇→公共板，城市fixture同時控制官方profile（避免真實profile覆蓋測試城市），sticky tabs按左右rail實際幾何檢查遮擋，morph記錄真SVG d變化而非假設35ms frame。期限等待catalogue period promise，登入與初始頁等待真實loading/workspace結束；保留503、草稿、權限及私人清除斷言。

以上working tree probe不冒稱固定新SHA結果。新候選的完整unit/TKU/共用browser驗收與遠端四組JUnit將另保存；其餘目的地文字、舊UI選擇器、治理API及workspace失敗仍需依新結果分類，不因同main失敗宣稱可整合或安全。沒有部署、merge、正式DB或安全設定變更。

motion根因補記：原#dashboard-view > section選擇器漏掉application workspace重新parent後的favorites等巢狀頁面，DOM實測#favorites路由沒有可選root。改為可見巢狀section，15條路由含返回與日曆結果的實際WAAPI探測1/1通過，原未改測試／失敗DOM/PNG保留。action pins contract新增精確upload SHA，沒有放寬為任意action版本。

另保留35項working tree整組探測32通過／3失敗，383.91秒。motion於探測開始後才修正，故該整組結果仍保存失敗，不改原XML；後續motion1/1通過另存。剩兩項定位：社群debounce於280ms後讀可被feed同步重設的DOM value；改捕捉input當下query。route focus於rAF執行但可能搶走已移往FAQ的使用者焦點；加入路由與activeElement檢查。保持原鍵盤、搜尋、反應重試與作者刪除斷言，後續probe單獨保存，不預寫通過。

最後5項working tree探測（三尺寸dialog/FAQ、社群search→reply/reaction/retry/delete、15路由motion）5 passed，59.87秒，JUnit與log另存；不是新固定SHA驗收。準備提交後才執行完整驗收，不套用舊結果。

3ccbf7c 兩次 remote 第0分片在812案例後，Progress長longrepr輸出觸發非阻塞管線BlockingIOError、pytest exit3。各已收集1757，但只有1032實跑、725未跑；原始8份candidate JUnit與8份main-control JUnit都保留，不冒稱full suite。PR checkout merge d738f543與code3cc完全同tree。下一候選設stdout/stderr blocking維持完整byte/back-pressure，滿管線測試重現原錯誤與修正。新source/draft測試增加7nodes、3files，預期1764/182；以實際collect結果為準。所有原案例保留，無新增skip或排除；原始JUnit/collect/log仍always upload，main-control不豁免candidate失敗。
