# 關西初次六件：API note限定收尾

資料／測試候選 **a2578f853d6b16184689b9d29b25ff5f44810d8b**，基準 **c8b02117654d16db46587aae3a7532a2cae7864f**。只同步六筆 `ncu-129-host-initial-reference` 的 `confirmation_note`；source／正式bundle各六筆，import provenance僅更新這個輸入hash。名稱、source URLs／版本／查核日、requires flags、scope note、當期verified全部保留；workflow／摘要／生活／field audit／921來源／71 partial／214計數不變。下一三校候選、2637de2凍結索引及全部舊證據位元組未改。[精確scope](committed-scope.json)、[policy前後文](policy-diff.json)、[生成比對](generated-diff.json)。

申請頁原文 **“Only documents issued within 3 months are valid.”** 保留；其對護照等文件的適用範圍標示待兩校確認，不以護照發照日期自動拒收。健康表的胸片六個月與文件發出三個月分開，不互相取代。護照未備妥的官方姓名證件替代／不免除visa護照、medical information條件與116封鎖保留。這是平台的待確認說明，沒有宣稱校方已核准護照效期豁免。

3項官方來源用正常TLS重取，原始response SHA与既有application／FAQ／health原件逐一一致；沒有insecure重試，也沒有寫回core source checks或改舊查核日期。[重取manifest](source-recheck/manifest.json)与原件保留。

第一版新增API test用「初次」prefix誤把研究所／宿舍／JPETS條件件算成9項，3個selection-error結果保留；不是產品缺陷證據。改以實際workflow的指定rule_id取六件後，仍舊bundle與c8 Git blob一致、只新增工作副本test時，3個準備狀態均因API note仍含「所有發出三月內」失敗。[修正前manifest](pre-fix-manifest.json)保留test與runtime policy hash、非clean候選範圍；原log／XML未改寫。

前端既有 `documentApplicabilityMarkup` 直接顯示API的 `result.note`；本輪沒有改共享runtime／前端／OpenAPI schema，沒有重跑browser或Kyutech。8234505的6 browser結果只屬該歷史SHA；原Kyutech根因仍open。沒有接入三校、merge、deploy、正式DB、credentials/security或對外學校聯繫。

固定a2578f8乾淨checkout的 **180 API／文件／生活全部pass**（原177加新3），OpenAPI snapshot與c8→a257 scoped diff均pass；manifest保留開始／完成時間、起迄SHA與clean狀態、argv／cwd／exit code及原始log／JUnit。[候選manifest](candidate-a2578f8/manifest.json)、[實際API三份完整回應](candidate-a2578f8/actual-api-catalog-responses.json)。每份六筆初次note均含原句、護照範圍待確認與不以發照日期拒收、胸片六個月另列；passport FAQ替代及medical information附註保留。

本輪未重跑或重標851 workflow parity、JS／lock與browser歷史結果。只有note資料與API assertion改變，schema／共享實作不變。當期資料验收仍blocked、Quality遠端狀態待最新推送查詢，不能以180本機pass稱full CI equivalence通過。

原始log／JUnit的2個檔案保留native空白，精確排除列表与hash見[native-whitespace-preservation.json](native-whitespace-preservation.json)；其餘staged路徑通過diff check。原證據未trim，未設定全域／目錄層級忽略。
