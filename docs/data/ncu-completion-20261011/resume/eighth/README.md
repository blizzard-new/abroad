# 第八續作：209合作校位置，202授權照片

基於`2d1cefdf41dc8adc35b08624b9d3d915ff52acd9`，沿用同一Draft PR11。新增12個逐筆核對校區代表點，197→209／214；中央母校另計。照片維持202／214（199不同SHA）。剩12圖5點、3227／4066當期嚴格缺口。全部214quota未知／agreement_only、pending_review及host提醒關閉，不把具名校區當116已確認接收校區。

## 本批座標與身份證據

- **ncu-078 東芬蘭大學 University of Eastern Finland**：UEF官方聯絡頁分列Joensuu Yliopistonkatu2與Kuopio Yliopistonranta8；Joensuu校區頁嵌圖具名Aurora／Yliopistokatu2同址標記62.603993,29.7464351，作Joensuu校區建築代表。未取視窗62.60383375,29.74275855或混入Kuopio。
- **ncu-080 LAB應用科技大學 LAB University of Applied Sciences**：LAB官方campuses與Lahti頁明列Mukkulankatu19、Niemenkatu73，Lappeenranta另址。採具名LAB University of Applied Sciences／Mukkulankatu19／lab.fi的place；另一同址Institute of Design是院級候選，不取兩候選共同視窗61.00645745,25.6644006或旧Fellmanni。
- **ncu-094 賓格爾大學 Bingöl University**：Bingöl官方Address明列Selahaddin-i Eyyubi Mahallesi,Üniversite Caddesi No1及官方地圖嵌入。具名Bingol University place同址、官網與電話+904262160012核對，採38.8983846,40.4878521；不取另一街景嵌入或視窗38.8976333,40.4894047。
- **ncu-098 蘇萊曼德米雷爾大學 Suleyman Demirel University（SDU）**：土耳其SDU官方Kampüs Haritası實際轉到w3.sdu.edu.tr/harita，正確相對路徑birimler.js中Rektörlük／Rectorate Building明列lat37.82942927985227及long30.526324897363665、電話02462111000；map.js以konum.lat/long建L.marker。非setView中心37.82867934472972,30.530861571061358，亦非哈薩克SDU。先前錯誤主機路徑回HTML200，未當JS證據。
- **ncu-124 富山大學 University of Toyama**：富山官方Access及Gofuku頁同列3190Gofuku、9308555與電話0764456011。公開地圖cid8586140756614352700同校名／同址／同電話／官網為36.69803539999999,137.1882862；另一候選為2630Sugitani醫藥校區，不取兩校共同視窗36.68914755,137.16491515，亦非Takaoka藝術校區。
- **ncu-197 太歷國立大學 Tarlac State University**：TSU官方Contact與Telephone Directory明列Romulo Boulevard,San Vicente,Tarlac City,2300及+63456068110。採cid15058935515676340920：Tarlac State University(TSU)同RomuloBlvd、同電話與tsu.edu.ph地標15.4851578,120.587402。另一cid2781225065243396527只有2300RomuloBlvd近似地址，缺官方域名／電話佐證，距離不同且未採用；不採共同視窗。
- **ncu-025 瑪麗路易巴斯德大學 Université Marie et Louis Pasteur (UMLP)**：UMLP現行sciences.umlp.fr官方Accès / plans（更新2026/7/16）明列SiteBouloie／16route deGray，官方Google連結!3d47.2453008!4d5.9866834對應具名UFR Sciences et Techniques。原連結仍保留Franche-Comté舊校名，作Bouloie校區代表，不推成116接收學院；不用@47.2453008,5.9844947視窗，也不用另一附近UFR ST標記47.2448832,5.987693。
- **ncu-075 錫耶納外國人大學 University for Foreigners of Siena**：錫耶納外國人大學unistrasi.it現行頁列PiazzaCarloRosselli27/28,53100Siena；地圖University for Foreigners of Siena同27/28、官網unistrasi.it的place43.3313161,11.3217099，非另一Università di Siena或舊ViaPantaniceto校址。
- **ncu-214 胡志明市自然科學大學 VNUHCM-University of Science, Ho Chi Minh City (HCMUS)**：HCMUS資訊學院官方fit.hcmus.edu.vn頁分列227đườngNguyễnVănCừ／PhườngChợQuán及ĐôngHòa另一校區；公開地圖具名University of Science-VNUHCM、同227地址、電話02862884499與hcmus.edu.vn對應10.7628356,106.6824824。主站／英文站重新導向循環未規避，改用官方學院公開頁，不將故障稱需登入。既有2011照片Quận5是歷史稱呼，未把照片GPS自動當此標記。
- **ncu-205 艾爾朗加大學 Airlangga University**：UNAIR2026官方英文首頁明列Management Office Building,MERR C Mulyorejo Campus,Surabaya。地圖具名Universitas Airlangga Management Building／Mulyorejo／unair.ac.id為-7.2684209,112.7842303，作Campus C行政大樓代表，不借CampusA醫學或CampusB人文校區，也不保證交換都在C。
- **ncu-079 東南芬蘭應用科學大學 South-Eastern Finland University of Applied Sciences(XAMK)**：XAMK官方Mikkeli Campus頁、2026一頁校園圖及官方嵌入place共同定位Patteristonkatu校區。採官方embed的61.6801818,27.2568226校區代表，非pb視窗61.679544320731516,27.258857377905667。地圖標籤同時含A-building與Mikpoli/Patteristonkatu2；2026官方PDF把A與Mikpoli(M)分列，因此不聲稱此點精確為A樓、國際處(X)或校園服務台(D)，僅作該複合校區代表；Kotka/Kouvola/Savonlinna分開。
- **ncu-083 奧胡斯大學 Aarhus University School of Engineering**：AU Civil and Architectural Engineering官方Contact（2026/8/13更新）明列Navitas／IngeLehmannsGade10,8000AarhusC、樓號3210；公開地圖具名Navitas同地址place56.1586821,10.215553作共享大樓代表。另一候選為同樓INCUBA獨立機構，不當AU工程學院身份；Aarhus School of Marine and Technical Engineering亦為共用樓的另一機構，不混作AU。官方舊bldg連結轉總聯絡頁，未把AU總部NordreRinggade1代替Navitas。

UMLP配圖為Mégevand UFR SLHS而地圖為Bouloie；Airlangga配圖為Campus B而地圖為Campus C，介面明文分開，沒有冒稱照片就是地圖上的校區。

原始推導完整留在`resume-eighth-location-review.json`，學生介面只顯示校區與適用範圍；全部`current_exchange_campus_confirmed=false`。capture序號與115原表canonical來源列分開保存。UMLP使用現行sciences.umlp.fr交通頁；XAMK官方2026圖已實際視讀，A與Mikpoli不同樓的標籤矛盾不隱藏；Navitas共享樓不混淆不同學校。

`resume-eighth-visual-sourcepack.json.gz`保存69份receipt及67份原始回應，包括HTML、真正JavaScript、PDF、校園示意圖及失敗回應，原位元SHA核對；二進位原件base64保存。這些是地理身份研究，沒有灌入host規則閱讀計數；人工host120／214、721來源、337閱讀、59原生PDF全文及6圖文全文、293成功未讀候選維持。

## 驗證

完整429項回歸通過；最後精簡學生介面校區說明並重建後，再跑36項來源／API／全bundle可重建檢查通過。第一次428pass／1fail是修正一條來源故障說明後未重建provenance摘要，已修復並保留失敗log。最終Chromium3案例通過（10歷次案例deselected）：12校逐一在390及1280預覽、展開來源；中央母校＋209點地球、210選項含placeholder。無JS錯誤或橫向溢出。截圖與實際視讀範圍見validation；首次長版介面與最終學生版log分別留存。

未修改共用matcher、地球renderer或NCU hold優先規則。Mons仍needs_review且不顯示共享fallback座標。未merge、部署、改正式DB／Quality／安全設定、增憑證／權限或付費。

## 尚未完成

剩餘位置：ICP、Reims、Mons、大阪公立、長安。ICP主站／英文／ILCF重新導向循環，圖書館403；Reims及Mons官方頁503已有限重試；大阪公立Access為HTTP200官方大規模系統故障通知；长安Google候選使用旧xahu域名且東西／南校區未釐清。這些均未冒稱需登入或未公布；替代官方來源仍續查。第九批BnF及校方附件已在工作目錄取得，尚未寫入本檢查點。

116名額沿用臺灣10/12 00:01:03實查：入口仍115表與116簡章，未見116校別名額表。原中斷任務未提交第五輪檔案仍未轉移。293成功公開候選尚待閱讀，不列外部阻礙，任務持續。
