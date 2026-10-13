# 第九續作：210合作位置，28筆來源閱讀

基於`128007852e7e6063b098237cb780ae0596142279`，沿用Draft PR11。202／214授權照片、199不同SHA不變；巴黎天主教大學rue d’Assas具名圖書館代表點核實後，209→210位置，中央母校另計。仍缺12圖4點，當期嚴格缺口3226／4066；全部214quota未知、agreement_only、pending_review、host提醒關閉，116接收校區未核准。

## 來源與實際閱讀範圍

完成28筆舊候選閱讀（8HTML、20PDF）。20份原生PDF逐頁已讀，保存相同SHA原始回應；其中31頁另外實際視讀，四份PDF所有頁均原生＋視覺全讀。包含一份與第六批相同位元的信州HTML，不把來源筆數當獨立內容數。721來源不灌增，閱讀337→365，原生全文59→75、圖文全文6→10，成功待讀293→265。剩餘265筆仍是本任務待辦，非外部阻礙；讀取導覽頁不等於讀完其附件。詳見reading-manifest.json、source-visuals及sources的resume-ninth-original-responses.json.gz。

十所host資料補充，人工紀錄仍120／214。關西大學原已於10/08有完整紀錄，本次先完整保留14欄、6初次文件及9文件階段，再補homestay，不重計新增學校。host-delta.json.gz保留逐校before/after。

- EM Normandie：2024／2025–26 welcome與2026–27雙聯18頁範圍分開；TOEIC785舊畢業門檻不套incoming。HUB是LOA後行政註冊。現行2026–27 Welcome p13明寫課程開始後最初兩週改課，修正原摘要「開課前」，保留舊版差異。51頁一般course offer仍僅前4頁讀取，不稱全文。
- EIGSI：2024–25 PDF內B2與B1、住宿不保證、月預算850EUR均保留來源年；La Rochelle與Casablanca分開，不能自行採較低門檻。
- Aschaffenburg：24頁指南含2025參考費用；Welcome Weeks與跨校區距離分開，既有2026–27資料保留。
- ZHAW：學士B2／碩士C1及分項語檢；2026秋Fully booked只指International Management Asia課，不推全部課程。春2027 Intensive週次矛盾保留，空白ECTS不補猜。
- Ca’ Foscari：2026–27三頁校曆全原生＋全視讀，院系學期與考期不同，不能套116。
- UdeM：2021英法填妥LA範例各一頁全讀；範例姓名不抄作空白文件，研究生6／9學分與英法文字差異保留，不覆蓋既有2027–28資訊。
- UF：四頁提名操作及七頁帳號指南；母校承辦、学生credential與提交申請分開。VetMed2024特定健康表與CDC資料明列排除，不能新增一般交換生Rabies／Tdap要求。
- 信州：2026春15頁完整原生讀、健康表p15視讀；Sheet3說明／4範例不用交，MMR強烈建議不當資格門檻，JASSO GPA只管獎學金。保留較新AY2027–28與2026秋原件區別。
- 關西：未標年五頁homestay，早餐晚餐／WiFi需確認／通勤30–60分鐘自付；未列價格或房源保證。
- Sungshin：15頁portal操作；p12實際截圖為Spring2021且韓文11/31／英文11/30矛盾，不當2027期限；p15無原生字但已視讀完成畫面，Save不同Final Submission。

## 位置與官方新表

法國國家圖書館CCFr的ICP Bibliothèque électronique條目，RCR751069905，21 rue d’Assas 75270 Paris，itemprop座標48.8481246／2.3295844；機構及icp.fr聯絡／館藏網站逐一核對，條目更新2021/12/16。只代表該圖書館位置，非Reims/Rouen或116交換校區。resume-ninth-location-review.json保留原文、SHA、國別、校區及推導；另保存失敗回應，沒有把故障當登入限定。

臺灣10/12 01:13:54再次實查中央入口及116簡章，SHA均未變，入口仍只連115校別表；沒有觀察到116名額新表。保存home-publication-recheck.json與原始回應，不能推論之後不公布；本次不改214名額／提醒。

## 驗證與限制

434項完整NCU／位置／記憶體回歸通過，包含從tracked來源重建bundle完全一致。瀏覽器與截圖實際結果見validation.json，使用隔離runtime、移除Supabase變數及系統Chromium；沒有部署、正式DB或安全設定變更。首輪三項舊斷言不符更新資料已修正並留log；browser舊模糊關西選校、地圖未完成及動態完整度面板使.first定位改變，均只修正測試定位／等待，未放寬資料條件或改matcher。

剩位置Reims、Mons、大阪公立、長安；第十批替代官方證據已在工作目錄，尚未納本批。12照片尚未有可採授權原件。原中斷任務未提交第五輪仍未轉移；本批不聲稱復原那些檔案。任務持續。
