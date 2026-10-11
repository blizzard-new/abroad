兩項整合阻擋已依「撤下錯誤／尚未核實圖片」驗收路徑處理，沒有猜圖或放寬測試。

固定驗收文件：`8b7570acca35fc10154e52e8621b9829bc9a815b` 的 `docs/source-recovery-20261011/TKU-PHOTO-BLOCKERS.md`；修正輸入為PR13第五批 `4f142ea36e69338d2956b4ea5d3d37a9f4116e52`。

| ID | 撤下原SHA256 | 逐項核對及解除方式 |
|---|---|---|
| tku-sister-65 Sunderland | 34569cf28e24ee8da835dda27c0bee84a415c2e63b29480c2fa70da349f2cf42 | 原Commons頁HTTP200，正文為University of the West of England／Frenchay；不同機構，已移出展示manifest與profile、API image欄清空，未用「歷史不同校區」保留錯配。 |
| tku-sister-52 UAEMEX | bb222e9a7ffa4ffe5493dcad6cb859f217a2cf8463b2b4aa13a84fa15871b493 | 原Commons頁HTTP200，作者Unknown author重複；原來源實回Facebook登入頁，未登入；Commons歷史原2024-04-13上傳記錄明示unknown作者，uploader不當作者／授權人。獨立credit鏈未核清，移出展示manifest／profile與API。不判侵權或匿名作品不可使用。 |

兩張原檔、原metadata與舊visual pass保留；新withdrawal政策優先於舊pass，重建不會復活錯圖。其他262張manifest內容與固定輸入逐筆完全相同，座標264筆不變。當期母校規則、名額、文件未修改。

實際驗證：固定照片與全量資料／第三批回歸18 passed（8.93s）；實際390／1280瀏覽器2 passed（33.13s），學校卡片、detail、生活指南沒有兩原圖與錯誤credit。第一次瀏覽器2failed是測試未展開官方指南，已加入真實點擊並保留失敗紀錄。pack-only4459原件／16archives／37parts全SHA通過，舊4455原件與15archives不變，只新增4個原頁／來源／歷史capture。

機讀證據 `src/exchange_info/official_data/tku/fixed_photo_blocker_holds.json` 逐項保留來源URL、查核時間、原文、SHA與撤下原件；原抓取在capture pack。完整測試及截圖雜湊在 `docs/tku-census-evidence-20261011/fixed-photo-withdrawal-evidence-manifest.json`。

範圍只有TKU照片政策、生成器、TKU資料、測試及原件pack；無共享registry/API/UI修改，沒有merge或deploy。其餘第六批研究仍在本獨立分支工作區，未納入此緊急照片commit。
