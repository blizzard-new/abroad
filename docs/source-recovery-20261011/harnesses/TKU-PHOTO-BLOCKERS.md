# TKU 第五批照片阻擋精確交接

固定输入：`4f142ea36e69338d2956b4ea5d3d37a9f4116e52`，PR13遠端head已核對。照片manifest與`1619ba890e3dc282bb26f92ebeeeece375e9ffe8`位元組完全相同。來源日期已核對不代表機構身分或署名鏈也完成；本文件列剩餘兩項，沒有要求照片總數維持264。

## 1. Sunderland 的圖片屬於 UWE

- [固定manifest第14464行](https://github.com/blizzard-new/abroad/blob/4f142ea36e69338d2956b4ea5d3d37a9f4116e52/src/exchange_info/official_data/tku/campus_asset_manifest.json#L14464)：`tku-sister-65`／桑德蘭大學。
- 本地圖：`src/exchange_info/static/assets/tku-campuses/tku-sister-65-alternative-deea7d07.jpg`。
- SHA256：`34569cf28e24ee8da835dda27c0bee84a415c2e63b29480c2fa70da349f2cf42`。
- [原照片頁](https://commons.wikimedia.org/wiki/File:Block_B,_University_of_the_West_of_England_-_geograph.org.uk_-_6031781.jpg)的標題、caption、identity_quote皆為University of the West of England；來源category為UWE Frenchay Campus。manifest的校方身分來源則為[淡江Sunderland條目](https://sister.tku.edu.tw/school-detail.asp?id=65)、Edinburgh Building Chester Road Sunderland SR1 3SD。
- 這是不同機構，不是同校兩校區；不能以歷史照片／非分配校區的限制語解除錯配。
- 驗收：換成有原件可核的Sunderland具名校區照片，保存原檔頁、機構／校區證據、作者／授權、拍攝年代與確切下載SHA，實視圖像，再同步manifest／census／前端credit並測試。若暫無安全候選，停用該錯圖並保留missing/pending也能解除錯誤展示；不得補假圖維持計數。

## 2. UAEMEX 的 CC BY 署名／授權來源尚未核清

- [固定manifest第14629行](https://github.com/blizzard-new/abroad/blob/4f142ea36e69338d2956b4ea5d3d37a9f4116e52/src/exchange_info/official_data/tku/campus_asset_manifest.json#L14629)：`tku-sister-52`／墨西哥州立自治大學。
- 本地圖：`src/exchange_info/static/assets/tku-campuses/tku-sister-52-alternative-e2537ab5.jpg`。
- SHA256：`bb222e9a7ffa4ffe5493dcad6cb859f217a2cf8463b2b4aa13a84fa15871b493`。
- [原照片頁](https://commons.wikimedia.org/wiki/File:EidicioA_FCPyS.jpg)：manifest license為CC BY4.0，author為`Unknown author Unknown author`。已可辨識UAEMEX FCPyS A棟，這項阻擋針對署名／授權人鏈，不是機構身分。
- 缺項：未有獨立原件證據支持可用的作者／授權人credit。此處沒有判定侵權，也沒有規定匿名作品必不可用；必須核清原頁所供的署名與授權來源，不能把重複Unknown字串當已完成署名驗收。
- 驗收：從原檔頁、原來源、上傳／授權聲明及歷史核實正確署名（匿名情況也須有可支持該授權與credit處理的紀錄），保存抓取時間與原文SHA，前端按原授權所供credit呈現。若仍不能核清，換可核來源或退missing/pending，不宣稱verified_asset。

機讀證據：同目錄`tku-fifth-photo-blocker-check.json`，完整舊manifest兩筆保留於`tku-fourth-photo-blocker-check.json`。整合者未修改TKU作者分支，且未納入這兩筆有阻擋的增量。
