# 4133667 小檔閱讀索引與原 bytes 分塊

只處理已合法持有的原證據，不新增下載或改寫原始结果。[原固定commit 14a7a45](https://github.com/blizzard-new/abroad/tree/14a7a459d02dc6e8495aed7139a419d4b603a87c/docs/tku-acceptance-evidence/4133667/)的XML、collect、result、main-control與96MB ZIP全部不變。此資料夾每個檔案均小於500,000bytes。

先讀summary.json；pr/push各有candidate-all-nodes.json（完整1764逐node，無長failure正文）、main-control-all-nodes.json（62逐node）、各shard索引與每100個node的小組。groups.json列順序、counts與SHA；各node保留原artifact ID、狀態、XML時間及失敗索引，完整列出passed/failed/skipped，不排除或改狀態。兩輪均1717P/31F/16S；PR main控制1P61F、push4P58F，不作豁免。

pr/failures與push/failures各31個case-NN.json可讀原message開頭1500字，明示是否截斷並連到完整原文。完整檔保存XML解碼後的原attributes/text，沒有改正文。小於200KB直接存case-NN-original.json；超大正文以原UTF8 JSON bytes分塊並附SHA/重組順序。原始XML自身保持原bytes，可獨立重組核對。

xml-parts有4個超大XML（兩輪第0片candidate與main-control）；raw固定150000bytes，base64文字約200001bytes，最後一片較短。reassembly.json列原XML路徑/原SHA256、每片offset/bytes/SHA及次序。base64可避免UTF8字符切半被文字介面改寫；依sequence解碼拼回，SHA必須等於原始XML。reassemble.py只用stdlib/本地檔，無網路讀取。例如python reassemble.py xml-parts/pr-candidate-shard-0/reassembly.json /tmp/pr-original-suite.xml。

這是閱讀用衍生索引與可逆原bytes表示，沒有重建或冒充原JUnit，沒有新測試或改寫舊驗收；原code candidate4133667、PR synthetic merge a8c48c3保持分開。manifest.json逐檔SHA/大小，沒有任何>500KB檔。
