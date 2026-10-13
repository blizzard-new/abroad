# 第七續作：202授權照片、197合作校區代表點

基於`d11a98bf7bf1634dec36ac3c3d3e7e2dc821ce5d`，同一Draft PR11。200→202照片（199不同SHA）、188→197合作位置，中央母校另計；剩12圖17點、3239／4066當期嚴格缺口。照片／地理來源不計作外校申請条件已讀，host人工120／214、721來源、337閱讀、59原生PDF全文／6圖文全文及293成功未讀候選維持。

## 兩張可追溯原作者校景

- ITERA：Fandiamendra本人Own work、2019/5/8上傳、self CC BY-SA4.0三者一致。照片實際為印尼南楠榜校園湖畔夕景，拍攝2019/4/29，不是同搜尋內的天文星雲圖。
- HCMUS：trungydang的2011/6/11照片；校門直接可讀「227」、Nguyễn Văn Cừ、Quận5與自然科學大學校名。Panoramio原photo54267350/user5317517與2016/11/28授權檢查確認CC BY3.0，非前批三張缺原作者grant的新聞搬圖。Linh Trung另校區，HCMUTE與HCMIU另機構；沒有把照片GPS自動公開為地圖座標。

兩張原圖均實際視讀；Commons縮圖原位元未改，原作者、署名、授權連結、拍攝日、歷史校景／116接收校區未定於介面呈現。研究過程排除理由留在review，學生圖說只呈現校區與年份。

## 九處逐項具名位置

- Douglas：官方地址與嵌圖的New Westminster／700RoyalAvenue地點標記49.2035681,-122.9126894，非pb視窗49.203683,-122.912784。既有照片另Coquitlam，Anvil／Surrey另址。
- VSB Ostrava：官方Poruba main／17.listopadu2172/15→Mapy addr9112126同址GPS49.8336878,18.1636011，不取x/y視窗、宿舍或FAST／FBI校區。
- UCLy：BnF國家圖書館CCFr/RCR693822301的Henri de Lubac/CampusCarnot／23placeCarnot，對照校方現址；45.75146489999999,4.8269687為該校區圖書館代表，不借Saint-Paul10placeArchives。
- Mendel：校方Rektorát Zemědělská1665/1Brno，Mapy機構191599同校名／官方域名／同址／電話与GPS49.2099189,16.6161261逐件核對，非Lednice或Zemědělská810/3。
- UHasselt：官方CampusHasselt／Martelarenlaan42，公開地址地圖building標記50.9335855,5.3423056，非Diepenbeek。校方v1embed403另取無key公開地圖，未新增憑證或規避存取。
- EM Normandie：官方LeHavre頁明列2020啟用及20QuaiFrissard，官方embed實際place標記49.48938099999999,0.125063已是新址；舊pb仍含0.101705的舊视窗不可用。不是由同校名猜新校區。
- NEOMA：官方Rouen／1RueMaréchalJuin,Mont-Saint-Aignan與embed具名標記49.4631981,1.0639311，非Reims／Paris或視窗中心。
- IDRAC：官方Lyon／47rueSergentMichelBerthet，連結13校共用CampusRenéCassin的!3d/!4d地點45.7684193,4.8058812，非@視窗4.8010103或同名AvenueRenéCassin街景。
- ITB：官方Contact分列Tamansari辦公室、Ganesha10、Jatinangor／Cirebon；地圖具名Ganesha10／itb.ac.id的-6.8903617,107.6101912只作Ganesha代表。此前petakampus TLS失敗未繞過。

UCLy既有照片為Saint-Paul、地圖代表Carnot；NEOMA既有照片為Reims、地圖代表Rouen，各自具名而不作同一校區聲明。全數代表點`current_exchange_campus_confirmed=false`，來源／地址／精度／日期／SHA／原文定位可追溯。NCU明示needs_review優先共享fallback不動，Mons仍hold。主matcher與地球renderer不改。

`resume-seventh-visual-sourcepack.json.gz`完整保存65回應receipt、58份HTML/JSON原始內容（含失敗）；兩張原圖存在本地static並核SHA。`resume-seventh-location-review.json`、`resume-seventh-photo-review.json`及總photo-review有每筆canonical來源列、校別國別與採用／拒用原因。capture序號不等於115原表列號。

## 驗證與未解事項

完整426項回歸通過；最後僅精簡兩張圖說、重建後，再跑32項API／來源／照片與SHA檢查通過。最終Chromium四案例通過（10歷次deselected）：2照片的390／1280實際載入、作者／授權／校區；9新位置逐一地圖選校及展開來源；中央母校與197地球、選單198含placeholder。無overflow或JS錯誤。截圖、實際command、前次通過log及最終log分開保留。沒有把只視讀的部分截圖宣稱全部已視讀，範圍見validation。

官方116名額狀態沿用本日臺灣10/12 00:01:03實查，入口仍115表＋116簡章，沒有新名額表。全部214quota未知／agreement_only、pending_review及host提醒關閉。未merge、部署、改正式DB／Quality／安全、憑證、權限或付費。

仍有12圖17點及293成功公開候選，待讀不是外部阻礙，任務持續。第八批官方交通與校區原件另在工作目錄取得，未計入本檢查點；原中斷任務未提交第五輪檔案仍未轉移。
