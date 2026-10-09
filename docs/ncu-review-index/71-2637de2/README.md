# 71校逐校小檔索引

資料凍結候選：`2637de25490e47bbb3987617bceefce02ae78446`，只有使用者指定的東北／關西／日本中央修正例外；原71校基準資料 `224284f` 保留於Git。71 partial／214；116外校完整核實0；尚餘143校。下一批研究候選不在此索引。

每校有17個獨立欄位檔、文件階段索引、逐步原始workflow與policy、来源映射和未解問題。home／host以作者明示的rule namespace分開；學制、校區、track、建議與硬門檻沒有用regex重判。靜岡126／137、南洋160／161等合併歷史列，另外列出未有獨立manual record的來源列，不表示各track都完整查核。

原始大檔未刪減：每段原文保留source URL／頁碼／sheet／archive member／適用期／checked_at，另以精確Git候選位置、字數及SHA256讀回；共享來源metadata去重，長頁文字仍存原gzip。source的下載、提取、全文閱讀、圖片閱讀、錯誤與當期適用狀態照原件保留。

讀單校單欄（不需載入整個dashboard）：

```bash
python scripts/build_ncu_review_index.py --output-dir docs/ncu-review-index/71-2637de2 --school ncu-122 --field visa
# 加 --original 可由凍結Git候選精確還原該欄全部原文並核對hash。
python scripts/build_ncu_review_index.py --output-dir docs/ncu-review-index/71-2637de2 --check
```

完整性檢查：71校／1207欄位／3255原文定位已核，1003個共享來源metadata有版本定位；workflow、policy、read_sources及unretrieved_sources與凍結候選一致。JSON共8695個（含驗證報告），最大41235 bytes；大部分為單欄、單步或單頁metadata。這是便於審阅的索引，不提升來源核准或解鎖文件／提醒。

|學校|17欄入口|文件階段|來源|未解問題|
|---|---|---|---|---|
|西雪梨大學 Western Sydney University|[ncu-001](schools/ncu-001/index.json)|[documents](schools/ncu-001/documents.json)|[sources](schools/ncu-001/sources.json)|[gaps](schools/ncu-001/gaps.json)|
|國立高等應用電子學院 Ecole Nationale Superieure de l'Electronique et de ses Applications ( ENSEA )|[ncu-008](schools/ncu-008/index.json)|[documents](schools/ncu-008/documents.json)|[sources](schools/ncu-008/sources.json)|[gaps](schools/ncu-008/gaps.json)|
|航太工程高等學院 Institute of Polytechnic Science and Aeronautics(IPSA)|[ncu-018](schools/ncu-018/index.json)|[documents](schools/ncu-018/documents.json)|[sources](schools/ncu-018/sources.json)|[gaps](schools/ncu-018/gaps.json)|
|史特拉斯堡大學 Universite de Strasbourg|[ncu-028](schools/ncu-028/index.json)|[documents](schools/ncu-028/documents.json)|[sources](schools/ncu-028/sources.json)|[gaps](schools/ncu-028/gaps.json)|
|圖爾庫大學 University of Turku|[ncu-081](schools/ncu-081/index.json)|[documents](schools/ncu-081/documents.json)|[sources](schools/ncu-081/sources.json)|[gaps](schools/ncu-081/gaps.json)|
|奧胡斯大學 Aarhus University School of Engineering|[ncu-083](schools/ncu-083/index.json)|[documents](schools/ncu-083/documents.json)|[sources](schools/ncu-083/sources.json)|[gaps](schools/ncu-083/gaps.json)|
|阿拉尼亞阿拉丁凱庫巴德大學 Alanya Alaaddin Keykubat University (ALKU)|[ncu-097](schools/ncu-097/index.json)|[documents](schools/ncu-097/documents.json)|[sources](schools/ncu-097/sources.json)|[gaps](schools/ncu-097/gaps.json)|
|蘇萊曼德米雷爾大學 Suleyman Demirel University（SDU）|[ncu-098](schools/ncu-098/index.json)|[documents](schools/ncu-098/documents.json)|[sources](schools/ncu-098/sources.json)|[gaps](schools/ncu-098/gaps.json)|
|曼尼托巴大學 University of Manitoba|[ncu-101](schools/ncu-101/index.json)|[documents](schools/ncu-101/documents.json)|[sources](schools/ncu-101/sources.json)|[gaps](schools/ncu-101/gaps.json)|
|莫瑞州立大學（自費） Murray State University（自費）|[ncu-112](schools/ncu-112/index.json)|[documents](schools/ncu-112/documents.json)|[sources](schools/ncu-112/sources.json)|[gaps](schools/ncu-112/gaps.json)|
|廣島大學 Hiroshima University|[ncu-115](schools/ncu-115/index.json)|[documents](schools/ncu-115/documents.json)|[sources](schools/ncu-115/sources.json)|[gaps](schools/ncu-115/gaps.json)|
|北海道大學(院級) Hokkaido University（院級）|[ncu-116](schools/ncu-116/index.json)|[documents](schools/ncu-116/documents.json)|[sources](schools/ncu-116/sources.json)|[gaps](schools/ncu-116/gaps.json)|
|北海道大學(校級) Hokkaido University（校級）|[ncu-117](schools/ncu-117/index.json)|[documents](schools/ncu-117/documents.json)|[sources](schools/ncu-117/sources.json)|[gaps](schools/ncu-117/gaps.json)|
|關西國際大學 Kansai University of International Studies|[ncu-118](schools/ncu-118/index.json)|[documents](schools/ncu-118/documents.json)|[sources](schools/ncu-118/sources.json)|[gaps](schools/ncu-118/gaps.json)|
|駒澤大學 Komazawa University|[ncu-119](schools/ncu-119/index.json)|[documents](schools/ncu-119/documents.json)|[sources](schools/ncu-119/sources.json)|[gaps](schools/ncu-119/gaps.json)|
|東京芝浦工業大學 SHIBAURA INSTITUTE OF TECHNOLOGY|[ncu-120](schools/ncu-120/index.json)|[documents](schools/ncu-120/documents.json)|[sources](schools/ncu-120/sources.json)|[gaps](schools/ncu-120/gaps.json)|
|信州大學 Shinshu University|[ncu-121](schools/ncu-121/index.json)|[documents](schools/ncu-121/documents.json)|[sources](schools/ncu-121/sources.json)|[gaps](schools/ncu-121/gaps.json)|
|東北大學 Tohoku University|[ncu-122](schools/ncu-122/index.json)|[documents](schools/ncu-122/documents.json)|[sources](schools/ncu-122/sources.json)|[gaps](schools/ncu-122/gaps.json)|
|東京都市大學 Tokyo City University|[ncu-123](schools/ncu-123/index.json)|[documents](schools/ncu-123/documents.json)|[sources](schools/ncu-123/sources.json)|[gaps](schools/ncu-123/gaps.json)|
|富山大學 University of Toyama|[ncu-124](schools/ncu-124/index.json)|[documents](schools/ncu-124/documents.json)|[sources](schools/ncu-124/sources.json)|[gaps](schools/ncu-124/gaps.json)|
|福井大學 University of Fukui|[ncu-125](schools/ncu-125/index.json)|[documents](schools/ncu-125/documents.json)|[sources](schools/ncu-125/sources.json)|[gaps](schools/ncu-125/gaps.json)|
|靜岡大學 Shizuoka University|[ncu-126](schools/ncu-126/index.json)|[documents](schools/ncu-126/documents.json)|[sources](schools/ncu-126/sources.json)|[gaps](schools/ncu-126/gaps.json)|
|千葉大學 Chiba University|[ncu-127](schools/ncu-127/index.json)|[documents](schools/ncu-127/documents.json)|[sources](schools/ncu-127/sources.json)|[gaps](schools/ncu-127/gaps.json)|
|日本中央大學 Chuo University|[ncu-128](schools/ncu-128/index.json)|[documents](schools/ncu-128/documents.json)|[sources](schools/ncu-128/sources.json)|[gaps](schools/ncu-128/gaps.json)|
|關西大學 Kansai University|[ncu-129](schools/ncu-129/index.json)|[documents](schools/ncu-129/documents.json)|[sources](schools/ncu-129/sources.json)|[gaps](schools/ncu-129/gaps.json)|
|新潟大學 Niigata University|[ncu-131](schools/ncu-131/index.json)|[documents](schools/ncu-131/documents.json)|[sources](schools/ncu-131/sources.json)|[gaps](schools/ncu-131/gaps.json)|
|大阪公立大學 Osaka Metropolitan University|[ncu-132](schools/ncu-132/index.json)|[documents](schools/ncu-132/documents.json)|[sources](schools/ncu-132/sources.json)|[gaps](schools/ncu-132/gaps.json)|
|東京科學大學 Institute of Science Tokyo|[ncu-133](schools/ncu-133/index.json)|[documents](schools/ncu-133/documents.json)|[sources](schools/ncu-133/sources.json)|[gaps](schools/ncu-133/gaps.json)|
|九州工業大學 Kyushu Institute of Technology|[ncu-140](schools/ncu-140/index.json)|[documents](schools/ncu-140/documents.json)|[sources](schools/ncu-140/sources.json)|[gaps](schools/ncu-140/gaps.json)|
|釜慶大學 Pukyong National University|[ncu-150](schools/ncu-150/index.json)|[documents](schools/ncu-150/documents.json)|[sources](schools/ncu-150/sources.json)|[gaps](schools/ncu-150/gaps.json)|
|首爾市立大學 University of Seoul|[ncu-156](schools/ncu-156/index.json)|[documents](schools/ncu-156/documents.json)|[sources](schools/ncu-156/sources.json)|[gaps](schools/ncu-156/gaps.json)|
|南洋理工大學 Nanyang Technological University（NTU）|[ncu-160](schools/ncu-160/index.json)|[documents](schools/ncu-160/documents.json)|[sources](schools/ncu-160/sources.json)|[gaps](schools/ncu-160/gaps.json)|
|上海大學 Shanghai University|[ncu-167](schools/ncu-167/index.json)|[documents](schools/ncu-167/documents.json)|[sources](schools/ncu-167/sources.json)|[gaps](schools/ncu-167/gaps.json)|
|上海交通大學 Shanghai Jiao Tong University|[ncu-168](schools/ncu-168/index.json)|[documents](schools/ncu-168/documents.json)|[sources](schools/ncu-168/sources.json)|[gaps](schools/ncu-168/gaps.json)|
|上海東華大學 Donghua University|[ncu-169](schools/ncu-169/index.json)|[documents](schools/ncu-169/documents.json)|[sources](schools/ncu-169/sources.json)|[gaps](schools/ncu-169/gaps.json)|
|上海財經大學 Shanghai University of Fiance and Economics|[ncu-170](schools/ncu-170/index.json)|[documents](schools/ncu-170/documents.json)|[sources](schools/ncu-170/sources.json)|[gaps](schools/ncu-170/gaps.json)|
|上海同濟大學 Tongji University|[ncu-171](schools/ncu-171/index.json)|[documents](schools/ncu-171/documents.json)|[sources](schools/ncu-171/sources.json)|[gaps](schools/ncu-171/gaps.json)|
|復旦大學 Fudan University|[ncu-172](schools/ncu-172/index.json)|[documents](schools/ncu-172/documents.json)|[sources](schools/ncu-172/sources.json)|[gaps](schools/ncu-172/gaps.json)|
|大連理工大學 Dalian University of Technology|[ncu-173](schools/ncu-173/index.json)|[documents](schools/ncu-173/documents.json)|[sources](schools/ncu-173/sources.json)|[gaps](schools/ncu-173/gaps.json)|
|天津大學 Tianjin University|[ncu-174](schools/ncu-174/index.json)|[documents](schools/ncu-174/documents.json)|[sources](schools/ncu-174/sources.json)|[gaps](schools/ncu-174/gaps.json)|
|北京師範大學 Beijing Normal University|[ncu-175](schools/ncu-175/index.json)|[documents](schools/ncu-175/documents.json)|[sources](schools/ncu-175/sources.json)|[gaps](schools/ncu-175/gaps.json)|
|北京郵電大學 Beijing University of Posts and Telecommunications|[ncu-176](schools/ncu-176/index.json)|[documents](schools/ncu-176/documents.json)|[sources](schools/ncu-176/sources.json)|[gaps](schools/ncu-176/gaps.json)|
|吉林大學 Jilin University|[ncu-177](schools/ncu-177/index.json)|[documents](schools/ncu-177/documents.json)|[sources](schools/ncu-177/sources.json)|[gaps](schools/ncu-177/gaps.json)|
|西安交通大學 Xian Jiaotong University|[ncu-178](schools/ncu-178/index.json)|[documents](schools/ncu-178/documents.json)|[sources](schools/ncu-178/sources.json)|[gaps](schools/ncu-178/gaps.json)|
|西南大學 SOUTHWEST UNIVERSITY|[ncu-179](schools/ncu-179/index.json)|[documents](schools/ncu-179/documents.json)|[sources](schools/ncu-179/sources.json)|[gaps](schools/ncu-179/gaps.json)|
|東南大學 Southeast University|[ncu-180](schools/ncu-180/index.json)|[documents](schools/ncu-180/documents.json)|[sources](schools/ncu-180/sources.json)|[gaps](schools/ncu-180/gaps.json)|
|東北林業大學 NORTHEAST FORESTRY UNIVERSITY|[ncu-181](schools/ncu-181/index.json)|[documents](schools/ncu-181/documents.json)|[sources](schools/ncu-181/sources.json)|[gaps](schools/ncu-181/gaps.json)|
|武漢大學 Wuhan University|[ncu-182](schools/ncu-182/index.json)|[documents](schools/ncu-182/documents.json)|[sources](schools/ncu-182/sources.json)|[gaps](schools/ncu-182/gaps.json)|
|長安大學 Changan University|[ncu-183](schools/ncu-183/index.json)|[documents](schools/ncu-183/documents.json)|[sources](schools/ncu-183/sources.json)|[gaps](schools/ncu-183/gaps.json)|
|南京大學 Nanjing University|[ncu-184](schools/ncu-184/index.json)|[documents](schools/ncu-184/documents.json)|[sources](schools/ncu-184/sources.json)|[gaps](schools/ncu-184/gaps.json)|
|西交利物浦大學 Xi'an Jiaotong-Liverpool University|[ncu-185](schools/ncu-185/index.json)|[documents](schools/ncu-185/documents.json)|[sources](schools/ncu-185/sources.json)|[gaps](schools/ncu-185/gaps.json)|
|南京信息工程大學 Nanjing University of Information Science and Technology|[ncu-186](schools/ncu-186/index.json)|[documents](schools/ncu-186/documents.json)|[sources](schools/ncu-186/sources.json)|[gaps](schools/ncu-186/gaps.json)|
|重慶大學 Chongqing University|[ncu-187](schools/ncu-187/index.json)|[documents](schools/ncu-187/documents.json)|[sources](schools/ncu-187/sources.json)|[gaps](schools/ncu-187/gaps.json)|
|浙江大學 Zhejiang University|[ncu-188](schools/ncu-188/index.json)|[documents](schools/ncu-188/documents.json)|[sources](schools/ncu-188/sources.json)|[gaps](schools/ncu-188/gaps.json)|
|華中師範大學 Central China Normal University|[ncu-189](schools/ncu-189/index.json)|[documents](schools/ncu-189/documents.json)|[sources](schools/ncu-189/sources.json)|[gaps](schools/ncu-189/gaps.json)|
|華中科技大學 Huazhong University of Science and Technology|[ncu-190](schools/ncu-190/index.json)|[documents](schools/ncu-190/documents.json)|[sources](schools/ncu-190/sources.json)|[gaps](schools/ncu-190/gaps.json)|
|華南理工大學 South China University of Technology|[ncu-191](schools/ncu-191/index.json)|[documents](schools/ncu-191/documents.json)|[sources](schools/ncu-191/sources.json)|[gaps](schools/ncu-191/gaps.json)|
|廈門大學 Xiamen University|[ncu-192](schools/ncu-192/index.json)|[documents](schools/ncu-192/documents.json)|[sources](schools/ncu-192/sources.json)|[gaps](schools/ncu-192/gaps.json)|
|廣西大學 Guangxi University|[ncu-193](schools/ncu-193/index.json)|[documents](schools/ncu-193/documents.json)|[sources](schools/ncu-193/sources.json)|[gaps](schools/ncu-193/gaps.json)|
|鄭州大學 Zhengzhou University|[ncu-194](schools/ncu-194/index.json)|[documents](schools/ncu-194/documents.json)|[sources](schools/ncu-194/sources.json)|[gaps](schools/ncu-194/gaps.json)|
|貴州大學 Guizhou University|[ncu-195](schools/ncu-195/index.json)|[documents](schools/ncu-195/documents.json)|[sources](schools/ncu-195/sources.json)|[gaps](schools/ncu-195/gaps.json)|
|濟南大學 University of Jinan|[ncu-196](schools/ncu-196/index.json)|[documents](schools/ncu-196/documents.json)|[sources](schools/ncu-196/sources.json)|[gaps](schools/ncu-196/gaps.json)|
|太歷國立大學 Tarlac State University|[ncu-199](schools/ncu-199/index.json)|[documents](schools/ncu-199/documents.json)|[sources](schools/ncu-199/sources.json)|[gaps](schools/ncu-199/gaps.json)|
|沃瑪德瓦大學 Universitas Warmadewa|[ncu-206](schools/ncu-206/index.json)|[documents](schools/ncu-206/documents.json)|[sources](schools/ncu-206/sources.json)|[gaps](schools/ncu-206/gaps.json)|
|日惹國立大學 Universitas Negeri Yogyakarta|[ncu-208](schools/ncu-208/index.json)|[documents](schools/ncu-208/documents.json)|[sources](schools/ncu-208/sources.json)|[gaps](schools/ncu-208/gaps.json)|
|迪波內戈羅大學 Universitas Diponegoro|[ncu-209](schools/ncu-209/index.json)|[documents](schools/ncu-209/documents.json)|[sources](schools/ncu-209/sources.json)|[gaps](schools/ncu-209/gaps.json)|
|蘇門答臘理工學院 Institut Teknologi Sumatera (ITERA)|[ncu-211](schools/ncu-211/index.json)|[documents](schools/ncu-211/documents.json)|[sources](schools/ncu-211/sources.json)|[gaps](schools/ncu-211/gaps.json)|
|太原農林大學 THAI NGUYEN UNIVERSITY OF AGRICULTURE AND FORESTRY (TUAF)|[ncu-213](schools/ncu-213/index.json)|[documents](schools/ncu-213/documents.json)|[sources](schools/ncu-213/sources.json)|[gaps](schools/ncu-213/gaps.json)|
|胡志明市科技師範大學 Ho Chi Min City University of Technology and Education|[ncu-214](schools/ncu-214/index.json)|[documents](schools/ncu-214/documents.json)|[sources](schools/ncu-214/sources.json)|[gaps](schools/ncu-214/gaps.json)|
|胡志明市國際大學 International University, Viet Nam National University|[ncu-215](schools/ncu-215/index.json)|[documents](schools/ncu-215/documents.json)|[sources](schools/ncu-215/sources.json)|[gaps](schools/ncu-215/gaps.json)|
|胡志明市自然科學大學 VNUHCM-University of Science, Ho Chi Minh City (HCMUS)|[ncu-216](schools/ncu-216/index.json)|[documents](schools/ncu-216/documents.json)|[sources](schools/ncu-216/sources.json)|[gaps](schools/ncu-216/gaps.json)|
