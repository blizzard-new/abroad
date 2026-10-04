# 圖片來源

本專案的新版網頁首頁與社群頁面使用下列 Unsplash 公開照片。照片僅作為交換留學資訊 MVP 的介面素材，使用方式依 [Unsplash License](https://unsplash.com/license) 辦理。

| 檔案 | 攝影／來源頁面 | 用途 |
| --- | --- | --- |
| `destination-tokyo.jpg` | [Unsplash 原始圖片](https://images.unsplash.com/photo-1540959733332-eab4deabeeaf) | 日本交換目的地與 App 日本合作校卡片 |
| `destination-sydney.jpg` | [Unsplash 原始圖片](https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9) | 澳洲交換目的地與 App 澳洲合作校卡片 |
| `destination-europe.jpg` | [Unsplash 原始圖片](https://images.unsplash.com/photo-1516550893923-42d28e5677af) | 歐洲交換目的地與 App 歐洲合作校卡片 |
| `community-students.jpg` | [Unsplash 原始圖片](https://images.unsplash.com/photo-1523240795612-9a054b0db644) | 留學社群首頁及尚無實景圖的合作校中性備用圖 |
| `ntpu-campus.jpg` | [國立臺北大學官方網站](https://new.ntpu.edu.tw/) | 國立臺北大學選校卡、校級看板與交換首頁主視覺 |

正式商業發布前，仍應逐一重新確認來源頁面、授權條款與適用範圍，並保留本檔作為素材清冊。

## 合作學校官方照片

合作學校清單主要使用各校官方網站公開的校園、校舍或校園生活照片。完整素材清冊（含校名別名）位於
`src/exchange_info/static/assets/school-images.json`，每筆包含學校名稱、官方來源頁、原始圖片網址、
查核時間與內容雜湊。網頁會提供「圖片來源」連結。

這些照片目前只用於內部 MVP 預覽。官方網站公開顯示不代表已授權商業再利用；正式公開或收費上線前，
應向各校確認素材授權，或改用各校提供的媒體素材庫與已授權照片。

### 2026-09-29 補圖

新增 14 張人工核對的校園／校園生活照片，另補上 4 個同校名稱別名。Toulouse INP 使用其所屬 ENSEEIHT 校區的官方照片，並在清冊註明校區；VSB 使用原有同校素材，未混用 University of Ostrava。

華沙醫學大學教學中心照片來自 [Wikimedia Commons 原始檔案頁](https://commons.wikimedia.org/wiki/File:Centrum_Dydaktyczne_Warszawskiego_Uniwersytetu_Medycznego.jpg)，作者為華沙醫學大學（Warszawski Uniwersytet Medyczny），2013 年拍攝，採 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) 授權。本地版本裁切為 16:9，沿用同一授權；網站圖片來源區與校園照片說明保留作者、裁切說明與授權連結。其餘新增照片的官方來源及原圖網址逐筆保留於清冊。
