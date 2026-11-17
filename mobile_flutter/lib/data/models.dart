import 'dart:convert';
import 'dart:typed_data';

typedef JsonMap = Map<String, dynamic>;

JsonMap jsonMap(dynamic value) => value is Map<String, dynamic> ? value : {};

List<JsonMap> jsonMapList(dynamic value) => value is List
    ? value
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList()
    : const [];

List<String> stringList(dynamic value) => value is List
    ? value
          .where((item) => item != null && item.toString().trim().isNotEmpty)
          .map((item) => item.toString().trim())
          .toList()
    : const [];

String textValue(dynamic value, [String fallback = '']) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int intValue(dynamic value, [int fallback = 0]) =>
    value is int ? value : int.tryParse(value?.toString() ?? '') ?? fallback;

const defaultHomeUniversity = '長庚大學';

class SupportedUniversity {
  const SupportedUniversity({
    required this.id,
    required this.schoolName,
    required this.shortName,
    required this.englishName,
    required this.officialUrl,
    this.supportLevel = 'live',
    this.partnerCount = 0,
    this.coverageNote = '',
    this.academicScoreMinimum,
    this.colleges = const [],
    this.aliases = const [],
  });

  factory SupportedUniversity.fromJson(dynamic value) {
    final json = jsonMap(value);
    final rawId = textValue(json['id']);
    final rawSchoolName = textValue(json['school_name']);
    final fallback = tryResolveSupportedUniversity(
      rawId.isNotEmpty ? rawId : rawSchoolName,
    );
    final rawMin = json['academic_score_minimum'];
    final parsedMin = rawMin is num
        ? rawMin.toDouble()
        : double.tryParse(textValue(rawMin));
    final parsedColleges = stringList(json['colleges']);
    final resolvedSchoolName = rawSchoolName.isEmpty
        ? (fallback?.schoolName ?? defaultHomeUniversity)
        : rawSchoolName;
    return SupportedUniversity(
      id: rawId.isEmpty ? (fallback?.id ?? resolvedSchoolName) : rawId,
      schoolName: resolvedSchoolName,
      shortName: textValue(json['short_name']).isEmpty
          ? (fallback?.shortName ?? resolvedSchoolName)
          : textValue(json['short_name']),
      englishName: textValue(json['english_name']).isEmpty
          ? (fallback?.englishName ?? '')
          : textValue(json['english_name']),
      officialUrl: textValue(json['official_url']).isEmpty
          ? (fallback?.officialUrl ?? '')
          : textValue(json['official_url']),
      supportLevel: textValue(json['support_level']).isEmpty
          ? (fallback?.supportLevel ?? 'live')
          : textValue(json['support_level']),
      partnerCount: intValue(json['partner_count']) > 0
          ? intValue(json['partner_count'])
          : (fallback?.partnerCount ?? 0),
      coverageNote: textValue(json['coverage_note']).isEmpty
          ? (fallback?.coverageNote ?? '')
          : textValue(json['coverage_note']),
      academicScoreMinimum: parsedMin ?? fallback?.academicScoreMinimum,
      colleges: parsedColleges.isNotEmpty
          ? parsedColleges
          : (fallback?.colleges ?? const []),
      aliases: fallback?.aliases ?? const [],
    );
  }

  final String id;
  final String schoolName;
  final String shortName;
  final String englishName;
  final String officialUrl;
  final String supportLevel;
  final int partnerCount;
  final String coverageNote;
  final double? academicScoreMinimum;
  final List<String> colleges;
  final List<String> aliases;

  String get _compactName =>
      shortName.endsWith('大學') && shortName.length > 2
      ? shortName.substring(0, shortName.length - 2)
      : shortName;

  String get boardTabLabel => shortName == '長庚' ? '長庚板' : '$_compactName板';

  String get boardTitleLabel =>
      shortName == '長庚' ? '長庚討論板' : '$_compactName討論板';
}

const List<SupportedUniversity> defaultSupportedUniversities = [
  SupportedUniversity(
    id: 'cgu',
    schoolName: '長庚大學',
    shortName: '長庚',
    englishName: 'Chang Gung University',
    officialUrl: 'https://www.cgu.edu.tw/oia-ch',
    supportLevel: 'full',
    partnerCount: 75,
    coverageNote: '完整支援試點：已整理長庚大學交換、補助、文件與合作校申請流程。',
    academicScoreMinimum: 70.0,
    colleges: ['醫學院', '工學院', '管理學院', '智慧運算學院'],
    aliases: ['長庚大學', '長庚', 'CGU', 'Chang Gung University'],
  ),
  SupportedUniversity(
    id: 'ntpu',
    schoolName: '國立臺北大學',
    shortName: '臺北大學',
    englishName: 'National Taipei University',
    officialUrl: 'https://new.ntpu.edu.tw/oia',
    supportLevel: 'full',
    partnerCount: 169,
    coverageNote: '完整支援試點：已套用交換申請流程、116 學年度三語組官方名額表（校內申請 10/23 17:00 已截止）、2026/10/22 學海飛颺與惜珠甄選辦法修正公告及 10/12 法國 EFREI 交換說明會；法律學院院級交換（10/30 11:00 截止，僅適用法律院）與校級預告／商院公告讀取缺口分開標示。',
    academicScoreMinimum: 75.0,
    colleges: ['法律學院', '商學院', '公共事務學院', '社會科學學院', '人文學院', '電機資訊學院', '永續創新國際學院'],
    aliases: ['國立臺北大學', '臺北大學', '台北大學', '北大', 'NTPU', 'National Taipei University'],
  ),
  SupportedUniversity(
    id: 'ntu',
    schoolName: '國立臺灣大學',
    shortName: '臺大',
    englishName: 'National Taiwan University',
    officialUrl: 'https://studyabroad.ntu.edu.tw/',
    supportLevel: 'basic',
    partnerCount: 289,
    coverageNote: '已整理116-1校級甄選時程（11/3 10:00–11/9 16:00線上報名、12/2成績公布、12/7一階志願截止）、文件、補助、289個合作項目與德國哥廷根大學交換說明會（頁尾10/30–10/31維護通知經核實為2022舊版彈窗；OIA正式列表oia.ntu.edu.tw/outgoing/school.list與9個候選詳頁讀取異常時保留10/22成功基準，不等於名額恢復）；合作校本期名額與未核實條件標示待確認。',
    colleges: ['文學院', '理學院', '社會科學院', '醫學院', '工學院', '生物資源暨農學院', '管理學院', '公共衛生學院', '電機資訊學院', '法律學院', '生命科學院', '國際政經學院'],
    aliases: ['國立臺灣大學', '國立台灣大學', '臺灣大學', '台灣大學', '臺大', '台大', 'NTU', 'National Taiwan University'],
  ),
  SupportedUniversity(
    id: 'ccu',
    schoolName: '國立中正大學',
    shortName: '中正大學',
    englishName: 'National Chung Cheng University',
    officialUrl: 'https://oia.ccu.edu.tw/',
    supportLevel: 'basic',
    partnerCount: 52,
    coverageNote: '已核對2027春季校級薦外交換；灰字參考與空白名額分開，三梯次校內收件已截止。',
    academicScoreMinimum: 70.0,
    colleges: ['文學院', '理學院', '社會科學院', '工學院', '管理學院', '法學院', '教育學院'],
    aliases: ['國立中正大學', '中正大學', '中正', 'CCU', 'National Chung Cheng University'],
  ),
  SupportedUniversity(
    id: 'ncu',
    schoolName: '國立中央大學',
    shortName: '中央',
    englishName: 'National Central University',
    officialUrl: 'https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw',
    supportLevel: 'basic',
    partnerCount: 214,
    coverageNote: '116學年度第一梯次簡章（2026-09-05公告，11/16 09:00開放線上申請至12/04 12:00）與2026/10/22最新交換姐妹校列表（116exchangeschoollist-1022.pdf，較10/13版移除北方高等商業學院EDHEC後共214列）已公告；外校當期條件逐項待核對。',
    colleges: ['文學院', '理學院', '工學院', '管理學院', '資訊電機學院', '地球科學學院', '客家學院', '生醫理工學院', '永續與綠能科技研究學院', '松濤全人學院'],
    aliases: ['國立中央大學', '中央大學', '中央', '中大', 'NCU', 'National Central University'],
  ),
  SupportedUniversity(
    id: 'tku',
    schoolName: '淡江大學',
    shortName: '淡江',
    englishName: 'Tamkang University',
    officialUrl: 'https://oieie.tku.edu.tw/',
    supportLevel: 'basic',
    partnerCount: 287,
    coverageNote: '部分支援：287校全量名錄／甄選機構聯集；2027–2028日語二甄4校7名已截止，11/6說明會（cid=auix1106）額滿可候補非交換名額額滿。新增第一梯25校50歷史名額，其他協議及一般原文列參考；新版、校區、期限與照片授權缺口逐校保存。',
    academicScoreMinimum: 75.0,
    colleges: ['文學院', '理學院', '工學院', '商管學院', '外國語文學院', '國際事務學院', '教育學院', 'AI創智學院', '精準健康學院'],
    aliases: ['淡江大學', '淡江', '淡大', 'TKU', 'Tamkang University'],
  ),
  SupportedUniversity(
    id: 'fju',
    schoolName: '天主教輔仁大學',
    shortName: '輔大',
    englishName: 'Fu Jen Catholic University',
    officialUrl: 'https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39',
    supportLevel: 'full',
    partnerCount: 237,
    coverageNote: '已整理116-1公告、申請表及237筆合作校／交換方案。附表名額與條件供規劃參考，當期開放及接待校要求仍須逐項確認；116-1名額預計11月底公告。',
    academicScoreMinimum: 70.0,
    colleges: ['文學院', '藝術學院', '傳播學院', '教育與運動健康學院', '醫學院', '理工學院', '外語學院', '民生學院', '法律學院', '社會科學院', '管理學院', '織品服裝學院', '全人教育課程中心', '進修部'],
    aliases: ['天主教輔仁大學', '輔仁大學', '輔仁', '輔大', 'FJU', 'Fu Jen Catholic University'],
  ),
  SupportedUniversity(
    id: 'scu',
    schoolName: '東吳大學',
    shortName: '東吳',
    englishName: 'Soochow University',
    officialUrl: 'https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro',
    supportLevel: 'full',
    partnerCount: 191,
    coverageNote: '完整支援：116學年度校級赴境外（國外126校、大陸62校、英美自費研修3校，共191校）現正開放線上申請（2026/09/14–11/16 12:00截止）。',
    colleges: ['人文社會學院', '外國語文學院', '理學院', '法學院', '商學院', '巨量資料管理學院'],
    aliases: ['東吳大學', '私立東吳大學', '東吳', 'SCU', 'Soochow University', 'Soochow University (Taiwan)'],
  ),
  SupportedUniversity(
    id: 'ntnu',
    schoolName: '國立臺灣師範大學',
    shortName: '臺師大',
    englishName: 'National Taiwan Normal University',
    officialUrl: 'https://bds.oia.ntnu.edu.tw/bds/web/OUT',
    supportLevel: 'full',
    partnerCount: 236,
    coverageNote: '完整支援：116-1（2027春季出國）甄選簡章與236所合作校名額表（29頁／285條目／96學程）已公告（線上申請 2026/11/01–11/15，赴外交換專區入口 bds.oia.ntnu.edu.tw/bds/web/OUT 與 outgoing-apply 正常運作；若由國際處主網巡查未尋獲子系統入口或遇短暫連線異常時保留已核實基準），並整合174校歷屆交換心得與四語組條件；院級公告正文截斷，不將院級名額併入校級。',
    colleges: ['教育學院', '文學院', '理學院', '藝術學院', '科技與工程學院', '運動與休閒學院', '國際與社會科學學院', '音樂學院', '管理學院', '跨域科技產業創新研究學院'],
    aliases: ['國立臺灣師範大學', '國立台灣師範大學', '臺灣師範大學', '台灣師範大學', '臺師大', '台師大', '師大', 'NTNU', 'National Taiwan Normal University'],
  ),
  SupportedUniversity(
    id: 'cycu',
    schoolName: '中原大學',
    shortName: '中原',
    englishName: 'Chung Yuan Christian University',
    officialUrl: 'https://oia.cycu.edu.tw/?p=6336',
    supportLevel: 'full',
    partnerCount: 89,
    coverageNote: '完整支援：出國交換介紹頁（?p=6336，未列發布日期、名額或截止日）仍連結「115-2 (2027春季班)赴國際姊妹校交換 第二梯次遴選公告」（?p=9903，20校共50名、GPA 3.0以上，9/24開放填表、10/7 12:00截止收紙本、10/14面試，與已截止紀錄無衝突），最新公告頁（?page_id=99，諮詢公告正文首次建檔僅作基準）另載 2026-10-21「教育部選送學生出國研修或國外專業實習補助要點（學海計畫）說明會」（校內師生可自行報名，列表未寫日期細節），頁面上尚未出現 116-1（2027秋季班）遴選公告；連同赴大陸交換共89所合作校、Fact Sheet及36校歷屆交換心得已完整整合。',
    colleges: ['理學院', '工學院', '商學院', '法學院', '設計學院', '人文與教育學院', '電機資訊學院', '智慧運算與量子資訊學院', '半導體產業學院'],
    aliases: ['cycu', '中原大學', '中原', 'CYCU', 'Chung Yuan Christian University'],
  ),
  SupportedUniversity(
    id: 'ntust',
    schoolName: '國立臺灣科技大學',
    shortName: '臺科大',
    englishName: 'National Taiwan University of Science and Technology',
    officialUrl: 'https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 237,
    coverageNote: '完整支援：116-1（2027秋季班）赴海外交換學生計畫甄選簡章（_中文_20260915.pdf，歐美亞〔不含中國大陸〕澳姐妹校，線上申請 2026/12/03 10:00–12/07 15:00；報名主系統 stu88/fall2027 恢復讀取且與10/22基準一致，當期正式名額待開放期間核對）與 115-2（2027春季班）海外暨大陸參考簡章、237所合作校條件名額表及126校歷屆交換心得已完整整合。',
    colleges: ['工程學院', '電資學院', '管理學院', '設計學院', '人文社會學院', '應用科技學院', '產學創新學院'],
    aliases: ['ntust', '國立臺灣科技大學', '國立台灣科技大學', '臺灣科技大學', '台灣科技大學', '臺科大', '台科大', 'NTUST', 'Taiwan Tech', 'National Taiwan University of Science and Technology'],
  ),
  SupportedUniversity(
    id: 'yzu',
    schoolName: '元智大學',
    shortName: '元智',
    englishName: 'Yuan Ze University',
    officialUrl: 'https://gao.yzu.edu.tw/index.php/tw/guo-ji-jiao-liu2/fu-wai-jiao-huan',
    supportLevel: 'full',
    partnerCount: 90,
    coverageNote: '收錄90校交換參考資料；母校指定規則部分查核，正式Google名額表讀取失敗時保留10/21最後成功基準（不推論今日名額無變），個別接待校及其餘內容仍待確認。',
    academicScoreMinimum: 70.0,
    colleges: ['工程學院', '電機通訊學院', '資訊學院', '管理學院', '人文社會學院', '醫護學院'],
    aliases: ['yzu', '元智大學', '私立元智大學', '元智', 'YZU', 'Yuan Ze University'],
  ),
  SupportedUniversity(
    id: 'fcu',
    schoolName: '逢甲大學',
    shortName: '逢甲',
    englishName: 'Feng Chia University',
    officialUrl: 'https://oia.fcu.edu.tw/sap/introduction/',
    supportLevel: 'full',
    partnerCount: 161,
    coverageNote: '完整支援：115-1選送（2027春季班）與115-2選送（2027秋季班）出國研修系統（oiasap）共161所合作校名額、課程目錄與95校歷屆心得／錄取紀錄已完整整合；日台獎學金2026/10/27 10:00校內期限已到（列表移除、詳頁變空，保留10/26核實基準不推論取消或改期）。',
    colleges: ['工程與科學學院', '商學院', '人文社會學院', '資訊電機學院', '建設學院', '金融學院', '國際科技與管理學院', '建築專業學院', '創能學院', '經營管理學院'],
    aliases: ['fcu', '逢甲大學', '私立逢甲大學', '逢甲', 'FCU', 'Feng Chia University'],
  ),
  SupportedUniversity(
    id: 'nsysu',
    schoolName: '國立中山大學',
    shortName: '中山',
    englishName: 'National Sun Yat-sen University',
    officialUrl: 'https://oia.nsysu.edu.tw/p/412-1308-20539.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 218,
    coverageNote: '完整支援：國際處最新公告列表已發布正式簡章「2027-2028 其他國家與地區出國交換甄選簡章」（p/405-1308-384608,c20621.php，列表日期標2026/10/21、內頁未標日期；同日另有甄選時程&4場線上說明會公告384613：10/29、10/31 20:00–21:30及11/4、11/5 12:00–13:30）：系統申請 2026/11/03 09:00 至 11/17 17:00，審核及補正至 11/20 17:00，甄選結果預計 2027 年 1 月第 2 週公告；名額載明「以國際處最新簡章公告為準」，交換校資訊和志願表 10/29 公布（待 10/29 公布後核對，以各校官方公告為準）；附件為依 115/10/07 修正之甄選要點（438775412.pdf）與有利審查資料表、研修計畫書等空白表格，連同赴日本、大陸簡章、218所合作校Fact Sheet、西灣領航獎助及1,823篇歷屆交換心得已完整整合。',
    colleges: ['文學院', '理學院', '工學院', '管理學院', '海洋科學學院', '社會科學院', '西灣學院', '醫學院', '半導體及重點科技研究學院', '國際金融研究學院'],
    aliases: ['nsysu', '國立中山大學', '中山大學', '中山', 'NSYSU', 'National Sun Yat-sen University'],
  ),
  SupportedUniversity(
    id: 'nchu',
    schoolName: '國立中興大學',
    shortName: '中興',
    englishName: 'National Chung Hsing University',
    officialUrl: 'https://www.oia.nchu.edu.tw/index.php/zh/5-global-mobility-tw/5-1-exchange-student-program-tw/5-1-1-application-guildeline-tw',
    supportLevel: 'full',
    partnerCount: 226,
    coverageNote: '完整支援：116學年度第1學期（Fall 2027秋季班）出國交換甄選簡章（第一步學生線上申請 2026/09/23–10/23 12:00 已截止；第二步指導教授／導師線上推薦信 10/30 12:00 截止、退補件 11/06 23:59 截止）、226所海外及大陸交換合作校名額與Fact Sheet、希望之橋暨學海系列獎學金、548篇學長姐交換心得影音及422人次錄取榜單已完整整合。',
    academicScoreMinimum: 60.0,
    colleges: ['文學院', '農業暨自然資源學院', '理學院', '工學院', '生命科學院', '獸醫學院', '管理學院', '法政學院', '電機資訊學院', '醫學院', '創新產業暨國際學院', '循環經濟研究學院'],
    aliases: ['nchu', '國立中興大學', '中興大學', '中興', '興大', 'NCHU', 'National Chung Hsing University'],
  ),
  SupportedUniversity(
    id: 'ntut',
    schoolName: '國立臺北科技大學',
    shortName: '北科大',
    englishName: 'National Taipei University of Technology',
    officialUrl: 'https://oia.ntut.edu.tw/p/412-1032-9242.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 206,
    coverageNote: '已收錄206筆合作方案及10/29出國交換說明會（p/406-1032-157886,r2255.php）；母校指定條文部分查核，116正式簡章、逐校現行名額、收件期限、資格、生活與來源仍待核對。',
    colleges: ['機電學院', '電資學院', '工程學院', '管理學院', '設計學院', '人文與社會科學學院', '創新前瞻科技研究學院'],
    aliases: ['ntut', '國立臺北科技大學', '國立台北科技大學', '臺北科技大學', '台北科技大學', '臺北科大', '台北科大', '北科大', '北科', 'NTUT', 'Taipei Tech', 'National Taipei University of Technology'],
  ),
  SupportedUniversity(
    id: 'nccu',
    schoolName: '國立政治大學',
    shortName: '政大',
    englishName: 'National Chengchi University',
    officialUrl: 'https://outbound.nccu.edu.tw/',
    supportLevel: 'full',
    partnerCount: 266,
    coverageNote: '完整支援：115-1／115-2 校級赴國外（八大語組，10/31口試公告post/118、11/2 16:00語檢上傳截止；動態公告目錄保留10/25之39筆成功基準）及赴大陸地區交換學生甄選簡章、266所合作姊妹校名額與語言門檻、6項赴外交換暨學海系列獎助學金及589篇歷屆學長姐交換心得報告已完整整合。',
    colleges: ['文學院', '理學院', '社會科學學院', '法學院', '商學院', '外國語文學院', '傳播學院', '國際事務學院', '教育學院', '創新國際學院', '資訊學院', 'X實驗學院', '國際金融學院'],
    aliases: ['nccu', '國立政治大學', '政治大學', '政大', 'NCCU', 'Chengchi University', 'National Chengchi University'],
  ),
  SupportedUniversity(
    id: 'ncku',
    schoolName: '國立成功大學',
    shortName: '成大',
    englishName: 'National Cheng Kung University',
    officialUrl: 'https://oia.ncku.edu.tw/p/404-1032-229870.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 211,
    coverageNote: '已核對 116-1 簡章（107138261.pdf，2026/10/30–11/19 16:00 線上申請）與當期校級一覽表（97 筆當期開放、92 筆舊資料待重查）；赴外交換生專區已改版為 404-1032-229870.php，116-1 甄選公告（406-1032-306703,r3333.php，2026/10/16 更新）另載 2026/10/23 說明暨分享會（芬蘭圖爾庫大學、奧地利因斯布魯克大學、日本東北大學返國學長姐分享）。',
    academicScoreMinimum: 77.0,
    colleges: ['文學院', '理學院', '工學院', '管理學院', '醫學院', '社會科學院', '電機資訊學院', '規劃與設計學院', '生物科學與科技學院', '智慧半導體及永續製造學院', '敏求智慧運算學院'],
    aliases: ['ncku', '國立成功大學', '成功大學', '成大', 'NCKU', 'Cheng Kung University', 'National Cheng Kung University'],
  ),
  SupportedUniversity(
    id: 'nycu',
    schoolName: '國立陽明交通大學',
    shortName: '陽明交大',
    englishName: 'National Yang Ming Chiao Tung University',
    officialUrl: 'https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0006&id=286',
    supportLevel: 'full',
    partnerCount: 243,
    coverageNote: '已核對國際處出國交換申請公告列表（module=nycu0006&id=286）：2026/10/07 公告「116年度第一梯次臺灣聯合大學系統（UST）交換學生計畫」校內收件至 2026/12/31（週四）16:00 截止（PDF 寄至 ex-out@nycu.edu.tw）；2026/10/13 轉知政大辦理「2027 臺灣與阿拉伯聯合大公國（阿聯）青年交流計畫」遴選（全額補助機票及食宿）；116 學年度校級出國交換簡章尚未公布（最新校級為 115-2，已於 2026/07/10 截止）。243 筆合作資料中 182 筆對上 115-2 已截止名額表、4 筆對上 116 台聯大第一梯次方案。',
    colleges: ['人文藝術與社會學院', '工學院', '工程生物科學學院', '牙醫學院', '生命科學院', '生物醫學暨工程學院', '光電學院', '科技法律學院', '客家文化學院', '理學院', '產學創新研究學院', '國際半導體產業學院', '智慧科學暨綠能學院', '電機學院', '資訊學院', '管理學院', '醫學院', '藥物科學院', '護理學院', '博雅書苑'],
    aliases: ['nycu', '國立陽明交通大學', '陽明交通大學', '陽明交大', 'NYCU', '國立交通大學', '國立陽明大學', 'NCTU', 'YM', 'Yang Ming Chiao Tung University', 'National Yang Ming Chiao Tung University'],
  ),
  SupportedUniversity(
    id: 'nthu',
    schoolName: '國立清華大學',
    shortName: '清大',
    englishName: 'National Tsing Hua University',
    officialUrl: 'https://oga.site.nthu.edu.tw/p/412-1524-18680.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 176,
    coverageNote: '完整支援：2027秋／2028春校級海外及赴陸港澳出國交換暨116-1台灣聯合大學系統交換計畫簡章、176所合作姊妹校（含A/B/C/D第一志願熱門程度分級、動態表142條目puid/11521及九州大學、大阪工業大學詳頁基準，不同名額單位分列不混加）名額與門檻、5項出國交換暨學海系列獎助學金及328篇歷屆學長姐返國成果報告書已完整整合。',
    colleges: ['理學院', '工學院', '原子科學院', '人文社會學院', '生命科學暨醫學院', '電機資訊學院', '科技管理學院', '竹師教育學院', '藝術學院', '台北政經學院', '永續學院', '半導體研究學院', '清華學院'],
    aliases: ['nthu', '國立清華大學', '清華大學', '清大', 'NTHU', 'Tsing Hua University', 'National Tsing Hua University'],
  ),
  SupportedUniversity(
    id: 'pccu',
    schoolName: '中國文化大學',
    shortName: '文大',
    englishName: 'Chinese Culture University',
    officialUrl: 'https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw',
    supportLevel: 'basic',
    partnerCount: 135,
    coverageNote: '已部分核對各甄選管道、國合組47筆參考名額與大陸文教處2027春季班赴大陸交換生甄選第二階段公告（https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw 、列表頁 https://mccd.pccu.edu.tw/p/16-1300-147944.php?Lang=zh-tw ，報名至2026/11/03 17:00，正文115-2／PDF 115-1矛盾保留待確認；國合部RPage入口 https://oima.pccu.edu.tw/p/412-1008-14612.php?Lang=zh-tw ，舊版靜態入口 oima.pccu.edu.tw/exchanges.htm 與 en/study-abroad-detail5.htm 不含當期收件表單或讀取失敗）；135筆合作方案的個別接待校條件及生活資料仍待核實。',
    colleges: ['文學院', '國際暨外語學院', '理工學院', '法學院', '社會科學院', '環境規劃暨生物資源學院', '商學院', '新聞暨傳播學院', '藝術學院', '教育學院', '體育運動健康學院', '永續創新學院'],
    aliases: ['pccu', '中國文化大學', '文化大學', '文化', '文大', 'PCCU', 'Chinese Culture University'],
  ),
  SupportedUniversity(
    id: 'wzu',
    schoolName: '文藻外語大學',
    shortName: '文藻',
    englishName: 'Wenzao Ursuline University of Languages',
    officialUrl: 'https://d020.wzu.edu.tw/article/530752',
    supportLevel: 'full',
    partnerCount: 147,
    coverageNote: '已核對115-2一招與2026/10/05 10:07公告之二招簡章（一般組 d020 article/530752、c015 article/530796；語言學習組 d020 article/530751、c015 article/530797，報名延後至 2026/10/13 23:59 截止）及《二招-115-2交換學生招收名額一覽表（一般組）》（持續更新，含匈牙利布達佩斯城市大學與韓國啟明大學資訊更新），並收錄首頁 2026/10/14 發布「(二招)115-2 校級交換生報名成功名單」（article/530925，內容為報名成功名單／初步資格審核，非錄取結果，最後由接待校決定是否錄取）、2026/10/05 國合處公告「115年度第2次教育部學海飛颺獎助學金開放系級交換生申請」（article/530756，2026/11/16 截止）與 10/20 轉知政大 2027 臺阿聯青年交流計畫（article/531074）；首頁尚無 116-1 一招公告。128筆對上官方名單校名，個別名額、學費與語檢仍待逐校核實；147筆舊衍生卡片停用。',
    colleges: ['國際文教暨涉外事務學院', '歐亞語文學院', '新媒體暨管理學院', '華語學院', '吳甦樂人文學院'],
    aliases: ['wzu', '文藻外語大學', '文藻外語學院', '文藻外大', '文藻', 'WZU', 'Wenzao Ursuline University of Languages', 'Wenzao'],
  ),
  SupportedUniversity(
    id: 'nkust',
    schoolName: '國立高雄科技大學',
    shortName: '高科大',
    englishName: 'National Kaohsiung University of Science and Technology',
    officialUrl: 'https://oia.nkust.edu.tw/unit-4-374-21.html',
    supportLevel: 'basic',
    partnerCount: 107,
    coverageNote: '已核對赴外交換生專頁（unit-4-374-21.html）116學年度校級出國交換甄選時程（2026/11/09 12:00–12/01 16:00 線上申請、12/27 16:00 補繳正式語檢、2027/02/01–02/12 甄選審查、02/22 16:00 公告結果、02/26 16:00 意願確認；2026/10/28 建工校區出國研修說明會）及115校級簡章：97筆僅對應115校級或2023院系表校名與參考欄位（116交換校資料陸續更新中）；學海飛颺名額視當年度補助經費而定（無固定名額）。',
    colleges: ['工學院', '智慧機電學院', '電機與資訊學院', '海事學院', '水圈學院', '商業智慧學院', '管理學院', '海洋商務學院', '財務金融學院', '創新設計學院', '外語學院', '共同教育學院'],
    aliases: ['nkust', '國立高雄科技大學', '高雄科技大學', '高科大', 'NKUST', 'National Kaohsiung University of Science and Technology'],
  ),
  SupportedUniversity(
    id: 'yuntech',
    schoolName: '國立雲林科技大學',
    shortName: '雲科大',
    englishName: 'National Yunlin University of Science and Technology',
    officialUrl: 'https://tdx.yuntech.edu.tw/',
    supportLevel: 'basic',
    partnerCount: 112,
    coverageNote: '112筆合作紀錄；母校規則及108筆115-2校名對應部分核對，個別接待校、生活資訊與其他欄位待查，不能宣稱完整核實。',
    colleges: ['工程學院', '管理學院', '設計學院', '人文與科學學院', '未來學院'],
    aliases: ['yuntech', 'nyust', '國立雲林科技大學', '雲林科技大學', '雲科大', 'YunTech', 'YUNTECH', 'NYUST', 'National Yunlin University of Science and Technology'],
  ),
  SupportedUniversity(
    id: 'ntou',
    schoolName: '國立臺灣海洋大學',
    shortName: '海大',
    englishName: 'National Taiwan Ocean University',
    officialUrl: 'https://oia.ntou.edu.tw/p/412-1022-6958.php?Lang=zh-tw',
    supportLevel: 'basic',
    partnerCount: 123,
    coverageNote: '123筆合作紀錄；母校規則及45筆已截止名單中文校名部分核對，個別接待校、生活資訊與其餘欄位待查，不是完整驗證。',
    colleges: ['海運暨管理學院', '生命科學院', '海洋科學與資源學院', '工學院', '電機資訊學院', '人文社會科學院', '海洋法律與政策學院', '國際學院'],
    aliases: ['ntou', '國立臺灣海洋大學', '國立台灣海洋大學', '臺灣海洋大學', '台灣海洋大學', '海洋大學', '海大', 'NTOU', 'National Taiwan Ocean University'],
  ),
  SupportedUniversity(
    id: 'ncue',
    schoolName: '國立彰化師範大學',
    shortName: '彰師大',
    englishName: 'National Changhua University of Education',
    officialUrl: 'https://oicaweb.ncue.edu.tw/p/412-1019-1171.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 108,
    coverageNote: '完整支援：國際暨兩岸事務處（有效RPage站台代碼1019：出國交換總覽 p/412-1019-1171.php、非大陸交換 p/412-1019-1220.php、大陸港澳交換 p/412-1019-1219.php）116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠甄選簡章、2027年春季班（115-2學期）及 115-1 赴大陸及港澳地區姊妹校交換計畫、跨國雙聯學制與全球共 108 所合作姊妹校（23 個國家與地區）名額與語檢門檻、教育部學海系列獎補助暨 409 篇學長姐返國交換心得已完整整合。',
    academicScoreMinimum: 70.0,
    colleges: ['教育學院', '理學院', '工學院', '管理學院', '社會科學暨體育學院', '文學院', '技術及職業教育學院'],
    aliases: ['ncue', '國立彰化師範大學', '彰化師範大學', '彰化師大', '彰師大', '彰師', 'NCUE', 'National Changhua University of Education'],
  ),
  SupportedUniversity(
    id: 'nknu',
    schoolName: '國立高雄師範大學',
    shortName: '高師大',
    englishName: 'National Kaohsiung Normal University',
    officialUrl: 'https://oia.nknu.edu.tw/exchange-programs.php',
    supportLevel: 'full',
    partnerCount: 143,
    coverageNote: '已整合國際事務處首頁（https://oia.nknu.edu.tw/）與赴外交換專頁（exchange-programs.php）：（1）首頁 2026-10-01 公告「大陸地區（含港澳地區）姊妹校2027年春季班交換申請資訊（1001更新）」（news-detail.php?id=460，校內收件至 2026/10/16 已截止），首頁／公告標題列出北京師範大學、香港教育大學、澳門城市大學、西南大學、華中師範大學、華東師範大學、南京師範大學、東北師範大學等 8 校，惟內文編號 1–8 及附件第 7 項實列「南京大學（2 名，10/13 截止）」而非「南京師範大學」（平台同步標註標題與內文校名差異）；（2）exchange-programs.php 目前僅放 115 年說明會簡報與手冊（檔名日期 20251027／20251029，簡報載 115 年 11/11–12/31 線上申請，甄選作業流程 PDF 另載每年 12/15 前，頁面本身未直接寫出每年 11/11–12/31 或姊妹校數量），尚未放上 116 年說明會資料（2026-10-21 已公告 116 年學海計畫說明會 news-detail.php?id=496：11/18 和平校區活動中心二樓演講廳、11/20 燕巢校區寰宇大樓二樓會議室，報名 https://reurl.cc/DYQVXQ）；（3）143 所合作姊妹校名冊彙整自《姊妹校一覽》（sister-schools.php，五大洲／地區分頁共 161 筆條目去重後 143 校，含 115 手冊表列 23 所海外交換校與陸港澳／雙聯共 36 所重點校及 107 所締約校）。',
    academicScoreMinimum: 70.0,
    colleges: ['教育學院', '文學院', '理學院', '科技學院', '藝術學院'],
    aliases: ['nknu', '國立高雄師範大學', '高雄師範大學', '高雄師大', '高師大', '高師', 'NKNU', 'National Kaohsiung Normal University'],
  ),
  SupportedUniversity(
    id: 'tmu',
    schoolName: '臺北醫學大學',
    shortName: '北醫大',
    englishName: 'Taipei Medical University',
    officialUrl: 'https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81/tmu-student-outbound-exchange/',
    supportLevel: 'full',
    partnerCount: 201,
    coverageNote: '已依臺北醫學大學國際事務處《在學期間出國交流指南》（tmu-student-outbound-exchange）及《盟校一覽》（partners-list）核實：指南頁表列教育部學海飛颺／惜珠與學海築夢／新南向學海築夢校內收件期限均為每年 1 月 15 日（115 年度專題簡報與二次徵求 PDF 另載第一梯次 1/16、第二梯次 9/7，均已截止）、校內《境外研修暨見實習獎勵辦法》收件期限為每年 1 月 15 日及 5 月 15 日（最新獎學金訊息停留在 2026-08-25 AIT 留學美國教育展）；指南頁內對學海飛颺／惜珠出國期程存在「總表列三個月以上、同頁 FAQ 寫一個月以上（學海築夢反之）」之文字不一致；雙聯學位依指南頁 FAQ 為「超過 30 個」（雙聯專頁細目共 33 項）；201 所國際盟校名冊係彙整自《盟校一覽》（partners-list）專頁。',
    academicScoreMinimum: 75.0,
    colleges: ['醫學院', '口腔醫學院', '藥學院', '護理學院', '公共衛生學院', '醫學科技學院', '人文暨社會科學院', '管理學院', '醫學工程學院', '營養學院', '跨領域學院'],
    aliases: ['tmu', '臺北醫學大學', '台北醫學大學', '北醫大', '北醫', '臺北醫大', '台北醫大', 'TMU', 'Taipei Medical University'],
  ),
  SupportedUniversity(
    id: 'csmu',
    schoolName: '中山醫學大學',
    shortName: '中山醫',
    englishName: 'Chung Shan Medical University',
    officialUrl: 'https://oia.csmu.edu.tw/?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 124,
    coverageNote: '完整支援：國際事務處 116 學年度（2027–2028）赴美國聖馬丁大學（每學期 3 名免學費）、美國密西根州奧克蘭大學（每年 15 名 ASAP 交換暨生物學 4+1/4+2 學碩連讀）、日本德島文理大學（每學期 2 名免學費＋PP 升學研究所計畫 1 名免學費）甄選（2026/10/22 17:00 收件截止，2026/11/02–11/06 面試）、2026/10/26 首頁公告「2026 海外交換生研修心得分享座談會」（10 月共 6 場，開放報名中）、「教育部學海計畫說明會」與「116 年 Young 飛全球行動計畫培訓營」（首頁未標發布日期、截止日或名額）、教育部 116 年度學海飛颺／惜珠獎學金（2027/01/06 截止，每人補助 5萬–30萬元）、2027春季美國路易斯安那州立大學醫學中心（LSUHSC）研究獎學金（每月 USD 2,500）、跨國雙聯學位與全球共 124 所合作姊妹校及教學醫院語檢門檻、書審配分（40%/35%/20%/5%）暨 31 篇歷屆海外研修心得報告已完整整合。',
    academicScoreMinimum: 75.0,
    colleges: ['醫學院', '口腔醫學院', '醫學科技學院', '健康管理學院'],
    aliases: ['csmu', '中山醫學大學', '中山醫大', '中山醫', 'CSMU', 'Chung Shan Medical University'],
  ),
  SupportedUniversity(
    id: 'cmu',
    schoolName: '中國醫藥大學',
    shortName: '中醫大',
    englishName: 'China Medical University',
    officialUrl: 'https://cmucia.cmu.edu.tw/s_exchange.html',
    supportLevel: 'full',
    partnerCount: 174,
    coverageNote: '已整合國際事務處首頁（https://cmucia.cmu.edu.tw/）、「交換學生」專頁（https://cmucia.cmu.edu.tw/s_exchange.html）、表格下載《2023日本交換學生說明會簡報》（https://cmucia.cmu.edu.tw/doc/202212281100421.pdf，載於 download.php?Page=3 本國學生分類）與中醫大法規資料庫：（1）國際事務處首頁與最新消息第 1 頁（10 則，最近一則為 2026-10-16）均為僑外生、華語測驗等轉知，尚無 115–116 學年度出國交換、雙聯或學海計畫最新甄選公告；（2）「交換學生」頁（s_exchange.html）為舊版靜態頁，僅列北見工業大學（每年最多 3 名）與香港教育大學（每年最多 4 名），期限一年，參與人數統計至 2011–2018 年（共 21 名），並連結《中國醫藥大學補助交換學生出國實施辦法》（statute_detail.php?sn=622）與申請表（doc/exchange/exchange_attach.odt），該頁本身未提北海道大學、補助金額、資格或當期截止日；（3）平台所列「日本北海道大學每年 5 名（大學部修滿 2 學年、IELTS 6.5 或 TOEFL iBT 79）」實際出自國際處表格下載之《2023日本交換學生說明會簡報》（doc/202212281100421.pdf），而來回經濟艙機票＋每月 NT\$5,000 生活費補助（全校每年至多 12 名、每學院至多 2 名）、大學部每學期至少修 2 門課且滿 4 學分及返國 2 週內繳交心得報告等規定則出自法規《補助交換學生出國實施辦法》（sn=622，115.04.09 修正）；（4）跨國雙聯學位（母法 sn=616，含 USC、杜蘭、喬治亞州立、南卡羅萊納、格里菲斯、紐卡索、南達科塔州立等雙聯獎助細則）及物治系 115-1 海外臨床實習（cmupt.cmu.edu.tw/news/753，10/12 17:00 報名截止、2027/01/10–01/30 實習）等 174 所合作機構資料均附實際法規與院系來源連結。',
    academicScoreMinimum: 80.0,
    colleges: ['醫學院', '中醫學院', '藥學院', '公共衛生學院', '健康照護學院', '生命科學院', '牙醫學院', '醫學工程學院', '人文與科技學院'],
    aliases: ['cmu', '中國醫藥大學', '中醫大', '中國醫大', '中國醫', 'CMU', 'China Medical University'],
  ),
  SupportedUniversity(
    id: 'kmu',
    schoolName: '高雄醫學大學',
    shortName: '高醫大',
    englishName: 'Kaohsiung Medical University',
    officialUrl: 'https://ciae2.kmu.edu.tw/index.php/zh-tw',
    supportLevel: 'full',
    partnerCount: 188,
    coverageNote: '完整支援：國際事務處首頁（ciae2.kmu.edu.tw，2026/10/28 巡檢）收錄「116 年教育部學海計畫說明會」（未標日期；內頁南區場 11/13 於高醫大第一教學大樓 B1）、「2027 日本台灣交流協會獎學金（短期生）」（截止 2026/11/05）、「教育部補助學生赴海外參加國際學術及技能競賽（2026 下學期）」（校內截止 2026/11/10）、「校內徵件：教育部青年百億海外圓夢基金（116 年第 2 梯次）」、「歐盟聯合碩士學位（EMJM）獎學金說明會」、教育部「2027 人文及社會科學領域海外研修人才培育計畫」申請公告（標題未寫日期）、「2027 臺灣與阿拉伯聯合大公國青年交流計畫」（11/02 截止）、TaiwanGPS 海外經驗分享與留學推廣線上說明會（10/14、10/22）、2026 青年百億海外圓夢基金成果展（10/30–11/01 高雄展覽館 N1）、AIT 留學美國教育展轉知與「教育部海外留學獎學金及相關資源」資訊分享（另有 TEEP 構想徵求截止 2026/10/30，屬外籍生來臺計畫而非出國交換），並整合醫學院網站（cmed.kmu.edu.tw）公告之 2027 海外臨床見實習（21 校 64+ 名）、校級赴日本順天堂大學長期交換生計畫、10 校跨國雙聯學位、各學院海外見實習、115 年度博士生千里馬出國研究計畫與全球共 188 所合作姊妹校及教學醫院語檢門檻暨 56 篇歷屆師生海外研修心得報告。',
    academicScoreMinimum: 60.0,
    colleges: ['醫學院', '口腔醫學院', '藥學院', '護理學院', '健康科學院', '生命科學院', '人文社會科學院'],
    aliases: ['kmu', '高雄醫學大學', '高醫大', '高醫', '高雄醫大', 'KMU', 'Kaohsiung Medical University'],
  ),
  SupportedUniversity(
    id: 'mcu',
    schoolName: '銘傳大學',
    shortName: '銘傳',
    englishName: 'Ming Chuan University',
    officialUrl: 'https://iee.mcu.edu.tw/',
    supportLevel: 'full',
    partnerCount: 202,
    coverageNote: '完整支援：國際教育交流處首頁（https://iee.mcu.edu.tw/）近期公告「海外留學說明會」（2026-10-20 發布，分類：出國交換與留學）、「2027 臺灣與阿拉伯聯合大公國青年交流計畫」（2026-10-14）與「2026 韓國首爾嘉泉大學冬季韓語營」（2026-10-05），並整合 116 學年度（2027秋季／2028春季）海外交換學生計畫（65 所開放姊妹校，依 2027–2028 姊妹校名冊 PDF 載明秋季班 2027/03/03、春季班 2027/09/20 截止）、10 校 14 個跨國雙學位項目、2027 春季班赴大陸頂尖大學交換計畫（42 所高校，第三次公告已於 2026/10/23 12:00 截止、預計 10/27 放榜）、教育部 116 學海飛颺／惜珠獎學金與全球共 202 所合作姊妹校語檢門檻、保證金 NT\$5,000 與家長同意書公證規定暨 126 篇歷屆學長姐返國研修心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['管理學院', '傳播學院', '法律學院', '金融科技學院', '電機資訊學院', '設計學院', '人文社會科學暨教育學院', '觀光學院', '健康暨醫學工程學院', '國際學院'],
    aliases: ['mcu', '銘傳大學', '銘傳', '北銘', '桃銘', 'MCU', 'Ming Chuan University'],
  ),
  SupportedUniversity(
    id: 'ntub',
    schoolName: '國立臺北商業大學',
    shortName: '北商大',
    englishName: 'National Taipei University of Business',
    officialUrl: 'https://oia.ntub.edu.tw/p/405-1006-57507,c3152.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 93,
    coverageNote: '已整合國立臺北商業大學國際事務處「出國交換學生」、「雙聯學位」、「交換學生獎補助金申請辦法」與「法規專區」官方資料：（1）甄選梯次與說明會：〈姊妹校交換作業辦法〉頁（p/405-1006-57507,c3152.php，115.10.12 更新懶人包）載明每年分兩梯次收件——11 月梯次（11/1–11/30 收件，遇例假日順延一天，於申請之隔年度出國交換一學期或一學年，實際交換期間依接待學校之學期起迄時間為主；官網未寫「8–9 月或 2 月出發」）、5 月梯次（5/1–5/31 收件，開放 11 月梯次剩餘名額，二技及研究所學生優先，於申請之隔年度第 2 學期出國交換一學期）；「116 學年度交換生申請說明會」已於 115/10/12（一）12:10–13:20 舉辦（臺北校區圖書館 B1 國際行銷講堂、桃園校區 Google Meet 同步，線上表單報名，p/406-1006-120272,r1.php）。（2）申請資格與甄選配分：申請人須為研究所、二技一年級第二學期以上、四技二年級以上或五專四年級以上之學生，且符合下列其中一項——①在校學業總平均 80 分以上，且前一學年每學期操性（操行）成績都在 A 以上；②歷年班級名次在前 70%，且前一學年每學期操性（操行）成績都在 A 以上；外語成績須在 2 年內有效且只接受托福（TOEFL iBT）或雅思（IELTS）；〈交換生甄選作業辦法〉頁（p/406-1006-77262,r134.php）僅放一份 PDF（檔名含 1081114），頁面本身無配分條文，而「海外組：外語成績 60%＋歷年學業平均 20%＋歷年班級名次百分比 20%；大陸組：學業平均 50%＋班級名次百分比 50%」配分比例係出自《學生申請交換生及雙聯學位生作業要點》（p/406-1006-91803,r134.php 附件 PDF 第七點）與 115.10.12 交換懶人包簡報（337014036.pptx）。（3）姊妹校與雙聯學位：〈姐妹校名單及交換名額〉頁（p/405-1006-57515,c3152.php）共 49 列（美國峽谷學院列 2 次：一般課程、銜接課程，實際 48 所當期交換校、分布 20 國，並註明「交換生甄選名額於每年 11 月重新計算」），連同〈雙聯學位〉5 校及〈海外合作學校名錄〉（p/405-1006-57536,c3159.php）其餘 42 所正式締約姊妹校，全庫共 93 所合作校。（4）獎助學金與最新消息：〈交換學生獎補助金申請辦法〉頁（p/405-1006-57516,c3152.php）列學海飛颺（110.08.26，238565761.pdf）與學海惜珠（115.07.23，562348656.pdf）兩份審查要點（頁面未直接印出金額），《王春滿清寒短期研修交流助學金》（115.05.26 修正，每人補助 NT\$ 25,000）出自〈法規專區〉（937380972.pdf）；最新消息尚無 11 月梯次甄選公告，新公告有「10/20 舊金山州立大學 3+1+1 學碩士雙聯學制說明會」（120031）及兩則冬季交流活動轉知（全北大學冬令營 120605、卡加利大學 120600，皆非交換甄選公告）。',
    academicScoreMinimum: 80.0,
    colleges: ['財經學院', '管理學院', '國際行銷學院', '創新設計與經營學院'],
    aliases: ['ntub', '國立臺北商業大學', '國立台北商業大學', '臺北商業大學', '台北商業大學', '北商大', '北商', '臺北商大', '台北商大', 'NTUB', 'National Taipei University of Business'],
  ),
  SupportedUniversity(
    id: 'ncnu',
    schoolName: '國立暨南國際大學',
    shortName: '暨大',
    englishName: 'National Chi Nan University',
    officialUrl: 'https://oia.ncnu.edu.tw/p/412-1017-269.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 212,
    coverageNote: '完整支援：已整合國立暨南國際大學國際及兩岸事務處「海外姊妹校交換生申請流程」、「姊妹校交換生申請截止日期」、「赴大陸及港澳地區交換生」、「跨國雙聯學位」、「出國獎學金（教育部學海計畫、校內補助）」與「法規及表單下載」官方資料：（1）甄選梯次與積分制度：海外交換分秋季班（每年 2–3 月校內收件提名）與春季班（每年 9–10 月校內收件提名），大陸港澳交換分春季班（9–11 月）與秋季班（2–4 月，香港教育大學僅 4 月開放）；校內甄選依《選送學生出國研修積分計算要點》（112.06.14 修正通過，滿分 30 分）採計主要語言 10 分（B2 為 8 分、B1 為 5 分、A2 為 2 分）、次要語言 3 分、學業成績 10 分（10 × [100% − 班排%]）、院推薦排序加分 1–4 分與國際學伴／社團 3 分。（2）合作姊妹校與雙聯學位：完整收錄《姊妹校交換生資訊》總表 142 所海外開放交換校、20 所大陸港澳交換姊妹校、4 所跨國雙聯學位合作校（美國加州大學河濱分校 UCR 3+1+MS、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學）及全球締約姊妹校地圖 KML 50 所參考校，全庫共 212 所合作姊妹校（橫跨 38 國／地區）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》／《學海惜珠》、校內《選送優秀學生出國補助要點》（114.07.22 修正，歐美最高 10 萬、亞太最高 7 萬）、雙聯學位 10 萬元完業獎勵金、《國外學分換算表》（2 ECTS = 1 學分、4 CATS = 1 學分）及 29 所合作大學共 100 篇歷屆學長姐交換心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['人文學院', '管理學院', '科技學院', '教育學院', '水沙連學院', '護理暨健康福祉學院'],
    aliases: ['ncnu', '國立暨南國際大學', '國立暨南大學', '暨南國際大學', '暨南大學', '暨南', '暨大', 'NCNU', 'National Chi Nan University'],
  ),
  SupportedUniversity(
    id: 'ndhu',
    schoolName: '國立東華大學',
    shortName: '東華',
    englishName: 'National Dong Hwa University',
    officialUrl: 'https://oia.ndhu.edu.tw/p/412-1027-21499.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 163,
    coverageNote: '完整支援：已整合國立東華大學國際事務處「出國交換計畫（甄選簡章及說明會、出國交換補助、申請系統及交換學校一覽表、校內甄選後程序、交換出返國程序、交換心得&影片、Q&A）」、「雙聯學位（校級、院系級、新南向專班）」與「規章辦法」官方資料：（1）甄選時程與審查配分：每年分兩次辦理校內甄選——第一次甄選於秋季學期初辦理（2027年第一次甄選線上申請為 2026/08/17 17:00 至 2026/10/05 17:00，申請 115-2 春季班及 116-1 秋季班出國交換；因出國交換申請系統 ias.ndhu.edu.tw 進行 PHP 資安漏洞修補維護，校內推薦結果公告由 2026/10/27 12:00 順延至 2026/10/30 12:00）、第二次甄選於春季學期初辦理（申請同年秋季班剩餘名額）；申請人須於出國就讀時為二年級（含）以上在學學位生且前一學期或歷年 GPA 達 2.5（滿分 4.5）以上，最少選填 2 個、最多 6 個志願，以首次申請出國交換者優先分發；校內書面審查總成績＝學業表現 20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%，另具國際處接待義工證明加 1 分、修畢全球研究與國際事務學程加 1 分。（2）合作姊妹校、先鋒計畫與雙聯學位：完整收錄 163 所全球與大陸合作姊妹校（橫跨 22 國，含 10 校「國際移動力先鋒計畫」免學費暨高額獎學金重點校、19 校校院級雙聯學位合作校及 41 所大陸交換姊妹校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》／《學海惜珠》、校內《國際交換學生出國計畫作業辦法》出國交換獎助學金（依當年度經費提供 1萬–15萬元不等，申請資格為歷年 GPA 達 3.3 以上且具外語檢定證明）、《學生出國選修課程實施辦法》（歐洲 ECTS × 1/2、英國 CATS × 1/4、美日陸 1:1 折算）及 92 所合作大學共 496 篇歷屆學長姐交換與海外研修心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['人文社會科學學院', '理工學院', '管理學院', '花師教育學院', '藝術學院', '原住民民族學院', '環境暨海洋學院', '洄瀾學院'],
    aliases: ['ndhu', '國立東華大學', '東華大學', '東華', 'NDHU', 'National Dong Hwa University'],
  ),
  SupportedUniversity(
    id: 'thu',
    schoolName: '東海大學',
    shortName: '東海',
    englishName: 'Tunghai University',
    officialUrl: 'https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_1_Qualifica?lang=tw',
    supportLevel: 'full',
    partnerCount: 274,
    coverageNote: '完整支援：已整合東海大學國際暨兩岸合作處（OIR）《2027年春學期／2026年秋學期赴全球姊妹校交換甄試簡章》、《交換甄選辦法重大更新通知（2025.11.18）》、《國際暨兩岸姊妹校名錄》、《國際合作協議資料庫》與《赴海外雙聯學位》官方資料：（1）甄試時程、分組與取消口試量化計分新制：每年春、秋兩學期初辦理校內長期交換甄試（春季班於每年 9–10 月辦理，如 2027 春學期甄試為 2026/09/07–10/05 報名、10/15 唱名選填學校、10/15–10/23 繳交推薦資格確認書與 10,000 元保證金；秋季班於每年 2–3 月辦理，如 2026 秋學期甄試為 2026/02/23–03/13 報名、03/27 唱名選校）。申請人須為修業滿一學期之在學學生（不含碩士在職專班），報名時分「全球暨港澳組（歷年 GPA 2.5 以上）」及「大陸組（歷年 GPA 2.0 以上）」兩組計分，自 2026 秋學期甄試起取消口試項目，總成績＝歷年學期班排名百分比平均 20%＋外語能力 30%（依 Level A 30% 至 Level G 4% 計分表擇最優採計，大陸組不計分）＋歷年學期 GPA 平均 15%＋學行優良表現 35%（含國際交流活動、國際接待志工、修習 EMI 課程占比達 30%/40%/50%、培力英檢 BESTEP 成績證明），完成基本勞作教育達畢業門檻者另加總分 5 分；依總分高低現場唱名當場決定選填學校。（2）合作姊妹校與雙聯學位：完整收錄 274 所全球與兩岸合作姊妹校（橫跨 31 國與地區，含 130 所當期開放申請之全球／大陸交換姊妹校與雙聯合作校、13 所美國名校跨國雙聯學位［天普、羅德島、北帕克、SUNY ESF、安得烈、艾克朗、UT Dallas、羅格斯、UIUC、南佛羅里達、密西根弗林特、聖湯瑪士、聖荷西州立］及 ACUCA／UMAP／Erasmus+ 交換專案）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（2026/10/12–11/16）、《學海惜珠》（每年 3/10、9/15）、《高等教育深耕計畫國際移動力活動獎補助（國際移動躍升計畫）》（每年 3月、9月兩梯次）、《學生參加英語檢定考試補助辦法》（最高補助 NT\$ 15,000）及 31 所合作大學共 80 篇歷屆學長姐交換與雙聯心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['文學院', '理學院', '工學院', '管理學院', '社會科學院', '農業暨健康學院', '創意設計暨藝術學院', '法律學院', '國際學院'],
    aliases: ['thu', '東海大學', '東海', 'THU', 'Tunghai University', 'Tunghai'],
  ),
  SupportedUniversity(
    id: 'shu',
    schoolName: '世新大學',
    shortName: '世新',
    englishName: 'Shih Hsin University',
    officialUrl: 'https://global.web.shu.edu.tw/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81-%e8%b5%b4%e5%a4%96%e7%a0%94%e4%bf%ae/',
    supportLevel: 'full',
    partnerCount: 177,
    coverageNote: '完整支援：已整合世新大學國際暨兩岸事務處（Global Affairs Office）與兩岸事務處（OCSE）《2027春季班／2026秋季班赴外及赴陸交換甄選簡章》、《2027春季班外國姊妹校交換申請手冊》、《世新大學選送學生出國研修甄選辦法》、《學生出國選修課程實施辦法》與《雙聯學制專區》官方資料：（1）甄選時程與雙軌窗口：國際處每年辦理兩梯次赴國外（非大陸地區）交換甄選（春季班於前一年 9–10 月報名、秋季班於當年 2–3 月報名），兩岸事務處同步辦理赴大陸及港澳地區交換生甄選；申請人須為本校在學滿一學期以上之學士班及碩博士班學生，赴國外交換一般須歷年平均 75 分（GPA 3.0）或班排前 50%、赴大陸交換一般須歷年平均 70 分以上且操行 80 分以上。（2）合作姊妹校與雙聯學位：完整收錄 177 所全球與兩岸合作姊妹校（橫跨 29 國與地區，含 58 所當期開放申請之國外及大陸交換／雙聯合作校、英國蘇塞克斯大學／西英格蘭大學及美國威斯康辛大學河瀑分校等跨國雙聯學位）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《選送學生出國研修獎助學金》及 49 所合作大學共 244 篇歷屆學長姐交換與雙聯心得報告。',
    academicScoreMinimum: 75.0,
    colleges: ['新聞傳播學院', '管理學院', '人文社會學院', '法律學院'],
    aliases: ['shu', '世新大學', '世新', 'SHU', 'Shih Hsin University', 'Shih Hsin'],
  ),
  SupportedUniversity(
    id: 'pu',
    schoolName: '靜宜大學',
    shortName: '靜宜',
    englishName: 'Providence University',
    officialUrl: 'https://411.pu.edu.tw/p/426-1073-4.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 275,
    coverageNote: '完整支援：已整合靜宜大學國際暨兩岸事務處（OIA）與 411 遊留學中心（出國研修組）《各洲別交換學校一覽表（15 個地區專頁）》、《跨國雙聯學制專區（16 校）》、《ISEP 國際交換學生計畫》、《五大洲締約姊妹校名錄 Excel》、《學生出國研修辦法》、《遴選交換學生作業要點》與《出國交換學生學分換算準則》官方資料：（1）三梯次校內初審、免繳雜費與強制抵免規定：每學期分三梯次辦理出國研修校內初審（春季班出國於前一年 8月／9月／10月辦理，如 115-2 為 2026/08/03–08/23、08/24–09/20、09/21–10/11，初審通過者於 10/30 前繳交《境外研修同意書》；秋季班出國於當年 2月底／3月底／4月底辦理；雙聯學制秋季班 3/31 截止；ISEP 秋季班 1 月中、春季班 7 月底截止）。大一新生可於大一下申請、大二上出國（延畢生亦得申請互惠交換），在學期間出國交換須繳交靜宜全額學費、免繳雜費；返國後次學期開學 2 個月內強制規定「至少須抵免一科（至少 1 學分）」（換算準則：美日陸 1:1、歐洲 ECTS÷2、英國 CATS÷4）。（2）合作姊妹校、ISEP 與 16 校雙聯學位：完整收錄 275 所全球與大陸合作姊妹校（橫跨 5 大洲 48 個國家與地區，含 230 所當期開放申請之交換與雙聯合作校、ISEP 全球逾 300 校互惠食宿交換，以及美、英、德、法、日、澳 16 所跨國雙聯學位合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《E.A.G.L.E. 築夢基金》（亞洲上限 2 萬／非亞上限 3 萬）、《學生出國研修獎助學金辦法》及 118 所合作大學共 299 篇歷屆學長姐交換與研修心得報告 PDF。',
    academicScoreMinimum: 70.0,
    colleges: ['外語暨人文創意學院', '社會科學院', '理學院', '管理學院', '資訊學院', '國際學院'],
    aliases: ['pu', '靜宜大學', '靜宜', 'PU', 'Providence University', 'Providence'],
  ),
  SupportedUniversity(
    id: 'usc',
    schoolName: '實踐大學',
    shortName: '實踐',
    englishName: 'Shih Chien University',
    officialUrl: 'https://uscoia.usc.edu.tw/p/412-1049-1331.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 125,
    coverageNote: '完整支援：已整合實踐大學國際暨兩岸事務處（OIA）《115學年度第2學期出國交換、雙聯學制暨海外自費研修簡章（含中國大陸地區交換）》、《交換及海外自費研修學校一覽表（125 校）》、《雙聯學制學校一覽表（20 校 28 學程）》、《實踐大學出國交換學生報名系統（oia-exchange.vercel.app）》、《辦理學生赴境外大學研修要點》、《與境外大學辦理雙聯學制實施辦法》與《出國留學獎學金辦法》官方資料：（1）兩階段校內甄選、在學學費與最低修習學分規定：每學期分兩階段於線上報名系統（oia-exchange.vercel.app）收件（春季班出國於前一年 9–10月辦理，如 115-2 第一階段 2026/09/01–10/01、第二階段 2026/10/19–10/29 17:00，陸港澳僅限第一階段；秋季班出國於當年 2–3月辦理），申請人須填寫 3 個志願並完成系主任與院長（或國際學程主任）核章。大一、大二及大三上可申請學士班交換（大四申請須簽署延畢切結書），歷年學業總平均須達 75 分以上或班排名前 50%、歷年操行平均 80 分以上；出國期間須辦理實踐大學註冊並繳交全額學雜費，每學期至少修習相當於實踐 6 學分（研究所至少 1 科 3 學分）且至少 1 門須為所屬學系專業課程（學分換算：美日韓陸 1:1、歐洲 ECTS×0.5、英國 CATS×0.25）。（2）合作姊妹校與 20 校 28 項雙聯學制：完整收錄 125 所全球與大陸合作姊妹校（橫跨 27 個國家與地區，含 101 所海外交換／雙聯／自費研修校與 24 所大陸地區交換姊妹校，以及英、美、加、澳、法、德、奧、瑞士、日、韓、馬、泰 20 所跨國雙聯學位合作大學共 28 個 3+1／2+2／1+1 雙聯學程）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《出國留學獎學金》（生活費補助、最高可加碼全額學雜費減免）及 74 所合作大學共 288 篇歷屆學長姐出國交換與雙聯研修心得報告 PDF。',
    academicScoreMinimum: 75.0,
    colleges: ['民生學院', '設計學院', '管理學院', '法學院', '國際學程', '商學與資訊學院', '文化與創意學院'],
    aliases: ['usc', '實踐大學', '實踐', 'USC', 'Shih Chien University', 'Shih Chien'],
  ),
  SupportedUniversity(
    id: 'nuk',
    schoolName: '國立高雄大學',
    shortName: '高大',
    englishName: 'National University of Kaohsiung',
    officialUrl: 'https://dia.nuk.edu.tw/p/412-1034-4130.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 280,
    coverageNote: '完整支援：已整合國立高雄大學國際事務處（DIA）《2027春季與2026秋季出國交換說明會簡報》、《出國交換名額表與申請條件一覽表》、《交換學生甄選作業要點》、《選送優秀學生出國研修之語文能力證明標準》、《33國國際姊妹校統計與名錄》、《跨國雙聯學制（8校）》與《教育部學海飛颺／惜珠獎學金語文標準》官方資料：（1）兩梯次校內甄選、百分制評分與語檢補件規定：每年分兩次辦理出國交換校內甄選（秋季班暨教育部學海飛颺／惜珠第一次申請於前一年 12 月底至 1 月初收件、2 月中旬語檢補件、3 月底前公布薦送名單；春季班於前一年 6 月底至 7 月初收件，如 115-2 為 2026/06/25–07/07、08/11–08/18 語檢補件、9 月底前公布薦送名單）。限非當學期畢業且申請／出國就讀時為大二（含）以上之高大日間學制學士班、碩士班、博士班在學學生（轉學生須於高大有 2 學期以上成績）。校內甄選依大學部「歷年班排 65%＋自傳研修計畫與有利審查資料 35%」、研究所「歷年班排 35%＋自傳研修計畫 35%＋指導教授推薦函 30%」評分，總分達 70 分（含）以上始獲考慮薦送資格（交換期限最長一年，不得申請延長）。（2）合作姊妹校與 8 校雙聯學制：完整收錄 280 所全球與大陸合作姊妹校（橫跨 33 個國家與地區，含 169 所當期開放申請之交換與雙聯合作校，以及美國密西根大學迪爾伯恩分校、美國肯恩大學、英國丹地大學、英國羅浮堡大學、英國亞伯丁大學、印尼丹戎布拉大學、蒙古新蒙古科技大學、中國福州大學共 8 所跨國雙聯學位合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、JASSO／GKS 與姊妹校住宿減免及 35 所合作大學共 58 篇歷屆學長姐返國心得報告與校內薦送紀錄。',
    academicScoreMinimum: 70.0,
    colleges: ['人文社會科學院', '法學院', '管理學院', '理學院', '工學院', '創新學院'],
    aliases: ['nuk', '國立高雄大學', '高雄大學', '高大', 'NUK', 'National University of Kaohsiung'],
  ),
  SupportedUniversity(
    id: 'ncyu',
    schoolName: '國立嘉義大學',
    shortName: '嘉大',
    englishName: 'National Chiayi University',
    officialUrl: 'https://www.ncyu.edu.tw/oia/Contents?nodeId=57877',
    supportLevel: 'full',
    partnerCount: 140,
    coverageNote: '完整支援：已整合國立嘉義大學國際事務處（OIA）《114學年度交換學生計畫說明會簡報（2026秋季／2027春季）》、《國立嘉義大學薦外交換學生審查要點》、《薦外姊妹校交換學生獎補助金發放要點》、《2026海外研修手冊》、《2026薦外交換生手冊》、《英語能力檢定測驗門檻對照表》、《國外締約學校一覽表（140校）》與《雙聯學位推動現況（8校13專案）》官方資料：（1）兩梯次校內甄選、量化計分與系所務會議認證規定：每年分兩梯次辦理薦外交換校內甄選（秋季班出國於前一年 12月收件、次年 2–3月公布錄取；春季班出國於前一年 5–6月收件，如 2027春季班為 2026/05/01–06/15 收件、09–10月公布錄取）。限學士班二年級以上、碩士班一年級以上、博士班一年級以上在學學生（轉學生須於嘉大修滿一學期且具成績），在校成績須達全班前 20% 以內，或學期平均大學部 75 分（含）以上、研究生 80 分（含）以上；每人至多選填 2 志願學校，進修課程規劃須檢附系、所務會議同意之會議紀錄。審查計分：非華語地區為「班級排名百分比 40%＋語言能力 40%（A級 40%、B級 36%、C級 32%、D級 24%）＋讀書計畫 20%」，華語地區免附語檢（班排 80%＋讀書計畫 20%）。（2）合作姊妹校與 8 校 13 專案雙聯學制：完整收錄 140 所全球與大陸合作姊妹校（橫跨 25 國與地區，含 48 所當期開放申請之交換與雙聯合作校，以及美國堪薩斯州立大學、楊斯鎮州立大學、斯托克頓大學、英國亞伯丁大學、日本尾道市立大學、香川大學、泰國湄州大學、印尼布勞爪哇大學共 8 所跨國雙聯學位合作校 13 個院系專案）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《薦外姊妹校交換學生獎補助金》、日本 JASSO 與韓國姊妹校學宿費減免，以及 20 所合作大學共 95 篇歷屆學長姐返國交換與海外研修心得報告。',
    academicScoreMinimum: 75.0,
    colleges: ['師範學院', '人文藝術學院', '管理學院', '農學院', '理工學院', '生命科學院', '獸醫學院'],
    aliases: ['ncyu', '國立嘉義大學', '嘉義大學', '嘉大', 'NCYU', 'National Chiayi University'],
  ),
  SupportedUniversity(
    id: 'nutc',
    schoolName: '國立臺中科技大學',
    shortName: '中科大',
    englishName: 'National Taichung University of Science and Technology',
    officialUrl: 'https://oia.nutc.edu.tw/p/412-1026-8514.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 140,
    coverageNote: '完整支援：已整合國立臺中科技大學國際事務處（OIA）《六大區域合作姊妹校名冊（140校）》、《2026/2027春秋季班日本與韓國姊妹校交換留學簡章》、《學生赴大陸地區協議學校研習申請簡章》、《114/115年度教育部選送優秀學生赴國外研修／專業實習學海系列計畫校內申請作業公告》、《學生申請教育部學海系列計畫審查要點》、《教師申請學海築夢計畫及新南向學海築夢計畫審查要點》與《高教深耕計畫國際專章補助國際交流活動要點》官方資料：（1）兩梯次出國交換甄選、五專部四五年級與學碩士班資格及返國志願服務規定：每年分春季班（前一年 9–10月收件，如 2027春季班為 2026/09/14–10/30 收件）與秋季班（當年 3–5月收件）辦理出國交換留學甄選，並於每年 1–3月初辦理教育部學海飛颺／惜珠／築夢校內甄選（115年度為 01/07 說明會、01/08–03/02 學院初審、03/04 國際處收件截止）。限已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含五專 1–3 年級生、延修生及在職專班生），國外交換各科成績須達 70 分以上且操行 80 分以上（赴大陸協議學校歷年學業總平均及操行均須達 80 分以上）；交換期間於中科大註冊繳費保留學籍並享姊妹校學費互免，赴日韓交換生於留學期間須投稿國際處粉專（1學期5篇、1學年10篇），返國後須繳交心得報告並完成國際處志願服務 20 小時。（2）六大區域 140 所合作姊妹校與英國雙聯學位：完整收錄日本 20 校、韓國 5 校、東南亞與南亞 33 校、歐美 23 校、大洋洲 4 校、大陸與澳門 55 校共 140 所合作姊妹校（橫跨 19 個國家與地區，含 39 所當期開放申請之交換與雙聯合作校，以及英國西蘇格蘭大學 UWS 1 年制榮譽學士／碩士雙聯學位與瑞士 BHMS 帶薪實習專案）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（每人補助 5 萬至 30 萬元）、《學海惜珠》、《學海築夢／新南向學海築夢》、高教深耕國際專章、日本 JASSO 及 8 所合作大學共 31 篇歷屆學長姐返國交換心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['商學院', '設計學院', '資訊與流通學院', '智慧產業學院', '語文學院', '中護健康學院'],
    aliases: ['nutc', '國立臺中科技大學', '國立台中科技大學', '臺中科技大學', '台中科技大學', '中科大', '臺中科大', '台中科大', 'NUTC', 'National Taichung University of Science and Technology'],
  ),
  SupportedUniversity(
    id: 'nfu',
    schoolName: '國立虎尾科技大學',
    shortName: '虎科大',
    englishName: 'National Formosa University',
    officialUrl: 'https://oia.nfu.edu.tw/zh-tw/ia/out/outexchange/out-exchangeschools',
    supportLevel: 'full',
    partnerCount: 152,
    coverageNote: '完整支援：已整合國立虎尾科技大學國際事務處（OIA）《亞洲／歐洲／美洲／大洋洲海外姊妹校名冊（152校）》、《國立虎尾科技大學海外姊妹校交換學生一覽表（115.06）》、《115學年度第2學期選送優秀學生出國研修（交換學生／學海飛颺／學海惜珠）甄選簡章》、《3+1+1雙聯學制專區》、《甄選學生赴國外研修作業要點》、《學生出國研修獎助要點》與《CEF與各項英檢對照表》官方資料：（1）兩梯次校內甄選、學業及語文門檻與每學期9學分修課規定：每年分兩梯次（春季班於前一年9月收件、秋季班於當年3–4月收件，如115-2春季班於115/09/30截止收件、115/10/14面試、115/10/16放榜；115-2學海惜珠於115/07/01截止收件）辦理校內甄選，限在學非應屆畢業生（大一至大三學士生、碩一碩士生、博一至博二博士生，不含在職專班生、大陸籍學生及外籍學生，交換期間不得辦理畢業），前學年學業總平均成績須達75分以上或班排名前50%且操行成績平均達80分以上，語文能力須達CEFR B1以上（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 457 / IELTS 4.0，或日檢N1–N4、韓檢TOPIK 3級）且面試成績須達70分以上；出國交換期間於虎科大完成註冊選課保留學籍並享姊妹校學費互免，每學期至少須選修9學分（或18 ECTS）以上專業課程，返國後一個月內繳交國外修讀學分抵免申請表及研修心得報告並配合國際處宣導活動。（2）四大洲 152 所合作姊妹校與雙聯學制：完整收錄亞洲 118 校（日本 33 校、越南 28 校、印尼 14 校、韓國 10 校、泰國 9 校、馬來西亞 7 校、印度 6 校、菲律賓 6 校、以色列 2 校、香港／土耳其／蒙古各 1 校）、歐洲 20 校（德國 7 校、法國 5 校、捷克 3 校、俄羅斯 2 校、西班牙／奧地利／羅馬尼亞各 1 校）、美洲 11 校（美國 8 校、加拿大 2 校、祕魯 1 校）與大洋洲 3 校（澳洲 3 校）共 152 所姊妹校（橫跨 28 個國家與地區，含 30 所當期開放申請之交換及美國密西根大學迪爾伯恩分校 UM-Dearborn、羅德島大學 URI 3+1+1 學碩雙聯學位與 UNLV 暑期研習合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》、虎科大《學生出國研修獎助要點》校內機票與生活費獎助學金，以及 12 所合作姊妹校共 13 篇歷屆學長姐返國研修心得與分享會紀錄。',
    academicScoreMinimum: 75.0,
    colleges: ['工程學院', '電機資訊學院', '管理學院', '文理學院', '航空學院'],
    aliases: ['nfu', '國立虎尾科技大學', '虎尾科技大學', '虎尾科大', '虎科大', 'NFU', 'National Formosa University'],
  ),
  SupportedUniversity(
    id: 'utaipei',
    schoolName: '臺北市立大學',
    shortName: '北市大',
    englishName: 'University of Taipei',
    officialUrl: 'https://international.utaipei.edu.tw/p/412-1006-6691.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 226,
    coverageNote: '完整支援：已整合臺北市立大學國際事務處（OIA）全球教育交流組《海外姊妹校一覽表（226校）》、《116學年度第1學期赴外姊妹校交換學生甄選簡章（86校）》、《115學年度第2學期赴外姊妹校交換學生甄選簡章（84校）》、《境外雙聯學位專區（11校24系）》、《學生赴外研修甄選暨獎補助要點》、《學生出國選修課程實施要點》、《辦理教育部學海系列計畫審查作業要點》與《各項英檢與CEFR架構對照表》官方資料：（1）兩梯次校內甄選、A/B/C/D四類優先順序与每學期6學分修課規定：每年分兩梯次（春季班於前一年4月收件、秋季班於前一年10月收件，如116-1秋季班於2026/10/05 14:00至2026/10/30 17:00收件、2026/12/31前放榜、2027/01/29放棄截止；115-2春季班於2026/04/10至04/30收件並錄取48名）辦理甄選，限於本校就讀一學期以上之在學學士班（出國時須為大二以上）及碩博士班（非當學期畢業）學生（不含在職專班及休學生），前一學期操行成績須達80分以上且無申誡以上處分及違反性平法／重大違法紀錄（須簽署行為確認聲明書），依A類（前一學期班排前40%）、B類（專業著作／重要展演／全國或國際競賽獲獎）、C類（一般申請者）、D類（同一學制第二次申請者）四類優先順序及總成績（書審40%＋面試60%）分發（至多填5志願）；非華語國家外語能力須達CEFR B1以上（GEPT中級 / TOEIC 550 / TOEFL iBT 42［新制3分］ / TOEFL ITP 433 / IELTS 4.0 / Duolingo 60，或日檢JLPT N1–N3、韓檢TOPIK 2–4級；中國大陸免附外語檢定）；交換期間於北市大完成註冊繳費並免繳姊妹校學費，每學期至少修習相當於本校6學分課程（暑期3學分；歐洲2 ECTS折算1學分，累計上限畢業總學分1/4）。（2）全球41國／地區226所合作姊妹校與11校24系雙聯學制：完整收錄中國大陸62校、美國23校、韓國20校、日本19校、馬來西亞9校、法國9校、波蘭7校、德國6校、捷克6校、泰國5校、越南5校、印尼5校、英國4校等共226所合作大學（含92所當期開放申請之交換與雙聯合作校，以及美國SWOSU/IUP/Troy、英國University of Essex［12系所］/Trinity Laban/Nottingham、紐西蘭奧克蘭大學、泰國朱拉隆功大學、馬來西亞馬來亞大學、哈薩克Satbayev、加拿大Western共11校24個雙聯學位學程）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（含本校最少20%配合款）、《學海惜珠》、《學海築夢／新南向學海築夢》、北市大《返國生活獎補助》（亞洲最高NT\$15,000、非亞洲最高NT\$30,000，依8級優先順序核給），以及66所合作大學共421篇歷年出國交換學生研修心得報告與錄取紀錄。',
    colleges: ['教育學院', '人文藝術學院', '理學院', '體育學院', '市政管理學院'],
    aliases: ['utaipei', 'ut', '臺北市立大學', '台北市立大學', '北市大', 'UTaipei', 'UT', 'University of Taipei'],
  ),
  SupportedUniversity(
    id: 'ntcu',
    schoolName: '國立臺中教育大學',
    shortName: '中教大',
    englishName: 'National Taichung University of Education',
    officialUrl: 'https://oia.ntcu.edu.tw/data/15',
    supportLevel: 'full',
    partnerCount: 263,
    coverageNote: '完整支援：已整合國立臺中教育大學國際及兩岸事務暨研究發展處（OIA）《締結姐妹校名單（263校）》、《交換學校名額表》、《116學年度與115學年度第3次選送學生出國研修簡章》、《甄選學生出國研修要點》、《補助學生赴外國大學（機構）選修課程要點》、《與外國大學校院辦理雙聯學制辦法》、《教育部學海飛颺／惜珠甄選簡章》及歷年出國研修心得報告。',
    colleges: ['教育學院', '人文學院', '理學院', '管理學院'],
    aliases: ['ntcu', '國立臺中教育大學', '國立台中教育大學', '臺中教育大學', '台中教育大學', '中教大', 'NTCU', 'National Taichung University of Education'],
  ),
  SupportedUniversity(
    id: 'tnua',
    schoolName: '國立臺北藝術大學',
    shortName: '北藝大',
    englishName: 'Taipei National University of the Arts',
    officialUrl: 'https://oia.tnua.edu.tw/',
    supportLevel: 'full',
    partnerCount: 90,
    coverageNote: '完整支援：已整合國立臺北藝術大學國際事務處（OIA）《四大洲姊妹校申請資訊表（90校）》、《116學年度姊妹校交換學生甄選簡章》、《選送學生出國進修與交流甄選辦法》、《選送學生赴外交換行政契約書》、《Shared Campus 校園共享專案》、《UMAP 亞太大學交流會》、《學海飛颺暨學海惜珠補助甄選作業流程》及 106–114 學年度共 130 篇出國交換研修心得報告。',
    colleges: ['音樂學院', '美術學院', '戲劇學院', '舞蹈學院', '電影與新媒體學院', '文化資源學院', '人文學院'],
    aliases: ['tnua', '國立臺北藝術大學', '國立台北藝術大學', '臺北藝術大學', '台北藝術大學', '北藝大', 'TNUA', 'Taipei National University of the Arts'],
  ),
  SupportedUniversity(
    id: 'ntua',
    schoolName: '國立臺灣藝術大學',
    shortName: '臺藝大',
    englishName: 'National Taiwan University of Arts',
    officialUrl: 'https://international.ntua.edu.tw/',
    supportLevel: 'full',
    partnerCount: 102,
    coverageNote: '完整支援：已整合國立臺灣藝術大學國際事務處（OIA）《交換學校一覽表（102校）》、《116學年度第1學期交換學生計畫甄選簡章》、《國立臺灣藝術大學交換學生甄選要點》、《辦理教育部學海系列計畫補助作業要點》、《與境外大學合作辦理雙聯學制實施辦法》及 102–113 學年度共 56 校 345 篇出國交換研修心得報告。',
    academicScoreMinimum: 80.0,
    colleges: ['美術學院', '設計學院', '傳播學院', '表演藝術學院', '人文學院'],
    aliases: ['ntua', '國立臺灣藝術大學', '國立台灣藝術大學', '臺灣藝術大學', '台灣藝術大學', '臺藝大', '台藝大', '臺藝', '台藝', 'NTUA', 'National Taiwan University of Arts'],
  ),
  SupportedUniversity(
    id: 'ntue',
    schoolName: '國立臺北教育大學',
    shortName: '國北教大',
    englishName: 'National Taipei University of Education',
    officialUrl: 'https://oia.ntue.edu.tw/p/412-1066-2258.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 143,
    coverageNote: '完整支援：已整合國立臺北教育大學研發處國際事務組（OIA）《海外姊妹校一覽表（143校）》、《115學年度赴海外姊妹校交換生甄選簡章（69校）》、《114學年度赴海外姊妹校大學交換甄選簡章》、《113學年度赴海外姊妹校大學交換甄選簡章》、《學生赴境外大學修讀雙聯學位實施要點》、《日本兵庫教育大學碩士班雙聯學位甄選簡章》、《法國社會科學高等學院（EHESS）博士雙聯學位計畫》、《學生出國選修課程實施要點》、《115年度教育部學海惜珠甄選簡章》、《應具語言能力參考標準》與《NTUE薦外交換心得專區（233篇）》官方資料：（1）七大語組甄選制度、學業及語文門檻與每學期2門課／6學分規定：每年11月公告簡章、12月收件（如115學年度於114/12/01至12/12 16:00收件並繳交報名費NT\$500，115/01/06筆試40%［含英文或各語組2題申論題］、115/01/07–01/08面試60%［含書審及學業成績］，總成績未滿60分不予錄取，115/02/23前公告錄取名單、115/03/02 16:00前截止申請更改交換期間或放棄；116學年度出國交換系列說明會於2026/09/29線上及2026/11/03實體舉辦），限本校大學部二年級以上（大一及轉學生尚未有本校成績者除外）及研究所碩博士班在學學生（不含在職專班生及領有臺灣獎學金者；公費生須經師資培育處、分發縣市政府及教育部同意展延分發並暫停公費；應屆畢業生須經系所主管同意且符合延畢規定），歷年在校成績總平均須達75分（含）以上或GPA 3.0以上（學海惜珠另須班級排名前50%，成績單須註明班級排名），分為英文組、日文組、韓文組、越文組、法文組、德文組、中文組共7組（每人限擇一組報考，德瑞奧9校標註▲者由英文組及德文組共用名額）；非華語組須具備英文CEFR B1（TOEFL iBT 42–71 / IELTS 4.0–5.5 / TOEIC 550–750）、日檢JLPT N3（部分學校N2/N1，常磐大學秋季班N5）、韓檢TOPIK 2–3級、法檢DELF B1–B2、德檢TestDaF TDN3 / B1–B2或越檢IVPT A/B級；交換期間須完成國北教大註冊選課並免繳姊妹校學費（部分學校如法蘭克福大學需自付雜費、法國巴黎索邦大學需自費法語密集班、韓國部分學校需修讀韓語課程），每學期至少修習2門課或6學分且不得超過畢業學分1/3。（2）全球25國／地區143所合作姊妹校與雙聯學位：完整收錄日本29校、中國大陸20校、美國17校、越南14校、韓國10校、馬來西亞7校、德國6校、印尼6校、捷克4校、奧地利4校、法國4校、泰國4校、新加坡3校、菲律賓2校、波蘭2校、澳洲2校、瑞士2校及英國／立陶宛／西班牙／芬蘭／俄羅斯／智利／加拿大各1校共143所合作大學（含69所當期開放交換申請之姊妹校，以及日本兵庫教育大學碩士班雙聯學位、法國社會科學高等學院EHESS博士雙聯學位）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、國北教大國際交流獎助學金（依地區與期限補助NT\$10,000至NT\$80,000）及芝山博愛獎助學金，以及橫跨12國共233篇歷屆學長姐返國交換心得報告（102–113學年度）。',
    academicScoreMinimum: 75.0,
    colleges: ['教育學院', '人文藝術學院', '理學院', '國際學位學程'],
    aliases: ['ntue', '國立臺北教育大學', '國立台北教育大學', '臺北教育大學', '台北教育大學', '國北教大', '國北教', '國北師', '北教大', 'NTUE', 'National Taipei University of Education'],
  ),
  SupportedUniversity(
    id: 'ncut',
    schoolName: '國立勤益科技大學',
    shortName: '勤益科大',
    englishName: 'National Chin-Yi University of Technology',
    officialUrl: 'https://oia.ncut.edu.tw/p/412-1030-6648.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 134,
    coverageNote: '完整支援：已整合國立勤益科技大學國際事務處（OIA）國際合作組《海外姊妹校締約一覽表（134校）》、《選送學生出國交換研修申請簡章與姊妹校名額表（33校）》、《雙聯學制合作專區（日本國立東北大學、國立岩手大學、加拿大皇家大學 RRU、越南大南大學）》、《選送學生出國研修辦法》、《辦理學生抵免學分辦法》、《推動學生參與國際化多元學習補助要點》與《學海計畫暨校內出國補助 Q&A》官方資料：（1）兩梯次校內甄選、學業操行門檻與每學期修課規定：每年分兩梯次（春季班於前一年9–10月收件、秋季班於當年度2–3月收件，如115-1秋季班第一梯次於2026/03/20截止、第二梯次延長至2026/03/31 12:00截止；115-2春季班於2026/09–10月收件）辦理甄選，限於本校就讀滿一學期以上之具正式學籍在學四技、二技及碩博士班學生（不含在職專班及休學生），歷年學業成績總平均須達70分（或GPA 2.5）以上、操行成績平均達80分以上且無小過以上處分紀錄；外語能力依各姊妹校規定須達英語CEFR B1–B2（TOEIC 550–785 / TOEFL iBT 42–80 / TOEFL ITP 457–543 / IELTS 4.0–6.0 / GEPT中級以上）、日檢JLPT N1–N5或韓檢TOPIK 2–3級以上（中國大陸姊妹校免附外語檢定）；交換期間於勤益科大完成註冊繳費並免繳姊妹校學費，每學期至少修習2門或6學分專業課程。（2）全球20國／地區134所合作姊妹校與4校跨國雙聯學制：完整收錄越南28校、日本23校、中國大陸22校、印尼17校、美國9校、韓國9校、印度6校、馬來西亞5校、菲律賓4校等共134所合作大學（含33所當期開放申請之出國交換與雙聯合作校，以及日本國立東北大學材料科學雙聯博士、國立岩手大學理工學府雙聯碩士、加拿大皇家大學 RRU 2+2 雙聯學士、越南大南大學雙聯碩士）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》、勤益科大《推動學生參與國際化多元學習補助》（含生活費與來回機票補助），以及23所合作大學共41篇歷年出國交換學生研修心得報告、影片與錄取紀錄。',
    academicScoreMinimum: 70.0,
    colleges: ['工程學院', '電資學院', '管理學院', '人文創意學院', '通識教育學院'],
    aliases: ['ncut', '國立勤益科技大學', '勤益科技大學', '勤益科大', '國立勤益科大', '勤益', 'NCUT', 'National Chin-Yi University of Technology', 'Chin-Yi University of Technology'],
  ),
  SupportedUniversity(
    id: 'npust',
    schoolName: '國立屏東科技大學',
    shortName: '屏科大',
    englishName: 'National Pingtung University of Science and Technology',
    officialUrl: 'https://oia2.npust.edu.tw/go-abroad/',
    supportLevel: 'full',
    partnerCount: 309,
    coverageNote: '完整支援：已整合國立屏東科技大學國際事務處（OIA）《本國生出國專區》、《學生赴國外姊妹校交換與研習申請審查作業要點（114.12.18修正）》、《出國雙聯學位制名冊》、《國外姊妹校及大陸港澳合作學校一覽表》及教務處《辦理跨國雙聯學位制實施辦法（114.12.01修正）》官方資料：（1）校內甄選時程與資格：每學期初受理次學期赴外交換申請（秋季班每年 3 月底前送國際處、春季班每年 9 月底前送國際處），限大二（含）以上或碩博班在學學生（不含在職專班），操行成績平均 80 分以上、歷年學業成績平均 70 分以上或班排名前 50%，並具備相當全民英檢中級初試、TOEIC 550、TOEFL iBT 42、IELTS 4.0、JLPT N2 或姊妹校指定語檢門檻；審查採書面審查 30%（自傳、出國學習計畫、成績單及英外語證明）與面試 70%（含英外語能力、學習規劃及溝通反應）。（2）合作姊妹校與雙聯學位：完整收錄 309 所全球及兩岸港澳合作大學（橫跨 49 國與地區，含 30 所當期開放申請之出國交換與跨國雙聯學位姊妹校［日、韓、德、法、捷克、義、西、泰、馬、印尼、越、陸及美加英澳雙聯校］及 279 所簽署學術合作 MOU 之姊妹校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠／築夢／新南向學海築夢》、《校內學生出國交換與研習獎助學金》（亞洲最高 NT\$35,000、歐美澳非最高 NT\$70,000）及 32 所合作大學共 37 篇歷屆學長姐赴外交換與實習心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['農學院', '工學院', '管理學院', '人文暨社會科學院', '國際學院', '獸醫學院', '達人學院'],
    aliases: ['npust', '國立屏東科技大學', '屏東科技大學', '屏科大', '屏東科大', 'NPUST', 'National Pingtung University of Science and Technology'],
  ),
  SupportedUniversity(
    id: 'cjcu',
    schoolName: '長榮大學',
    shortName: '長大',
    englishName: 'Chang Jung Christian University',
    officialUrl: 'https://dweb.cjcu.edu.tw/oia/article/3030',
    supportLevel: 'full',
    partnerCount: 193,
    coverageNote: '完整支援：已整合長榮大學國際處國際合作組（OIA）《115學年度校級國際交換生甄選簡章》、《校級國際交換生學校一覽表（79校）》、《海外雙聯學位學校列表（8校12學程）》、《全球與兩岸締約姊妹校名錄（193校）》、《長榮大學赴外研修生作業要點》、《長榮大學學生出國期間學業及學籍處理要點》、《長榮大學海外雙聯學制實施辦法》、《長榮大學推展學生國際學術交流獎補助辦法》与《長榮大學短期交流補助作業要點》官方資料：（1）校內甄選時程、資格與四組配分：115學年度校級國際交換生甄選自 2026/10/01 至 2026/11/27 17:00 受理（10/02 12:10 舉辦說明會、12/04 公告面試時間表、12/11 辦理分組面試、12/16 公告第一階段錄取名單、12/21 第一階段錄取確認截止、12/31 公告最終錄取名單），申請人出國就讀時須於本校修業滿一學年（含）以上且前一學年度學業平均成績達 70 分（含）以上；評比採「面試 40%」（英韓組、英語組、中文組、日語組）＋「書面資料 60%」（前一學年度操行成績 10%＋前一學年度學業成績 10%＋自傳及讀書計畫 15%＋語文證明 10%＋其他相關資料 15%），錄取生（除日語組與中國地區外）須參加並通過語文教育中心「交換生英語加強課程」（第 1–9 週），交換期間每學期至少修習相當本校 9 學分或 3 門課程（不含體育課）且至少 6 學分或 2 門課程及格。（2）全球 26 國與地區 193 所合作姊妹校與 8 校跨國雙聯學位：完整收錄 88 所常態開放申請之校級交換與雙聯學位學校（含日本鎮西學院大學、創價大學與韓國韓信大學「免學費＋免住宿費」，印尼蘇吉甲普拉納塔天主教大學印尼政府獎學金，以及英國女王大學 QUB、諾丁漢特倫特大學 NTU、法國雷恩商學院、澳洲西雪梨大學、美國北德州大學 UNT、馬來西亞砂拉越科技大學 UTS、泰國清邁皇家大學 CMRU 等雙聯學位）及 105 所正式締約姊妹校。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠》（前學年平均達 75 分或班排前 25%）、《長榮大學推展學生國際學術交流獎補助金》（前學年平均及格或班排前 50%）、《短期交流補助》（每人最高 NT\$40,000），以及 42 所合作大學共 145 篇歷屆學長姐返國交換心得報告與 35 份官方 Fact Sheet。',
    academicScoreMinimum: 70.0,
    colleges: ['管理學院', '健康科學學院', '人文社會學院', '資訊暨設計學院', '安全衛生科學學院', '永續教育學院', '環境教育國際實驗學院', '神學院', 'PLUS學院', '博雅教育學部'],
    aliases: ['cjcu', '長榮大學', '長榮', '長大', 'CJCU', 'Chang Jung Christian University'],
  ),
  SupportedUniversity(
    id: 'nqu',
    schoolName: '國立金門大學',
    shortName: '金大',
    englishName: 'National Quemoy University',
    officialUrl: 'https://oica.nqu.edu.tw/',
    supportLevel: 'full',
    partnerCount: 64,
    coverageNote: '完整支援：已整合國立金門大學國際暨兩岸事務處（OICA）與教務處註冊組《國際交換學校一覽表（39校）》、《大陸地區交換學校一覽表與姊妹校名冊（25校）》、《115學年度第一／二階段國際交換學生甄選簡章》、《2027春季班（115-2）赴國內及大陸地區交換學生甄選簡章》、《國立金門大學學生國際交流甄選要點》、《國立金門大學學生出國交換實施要點》、《國立金門大學科目學分抵免辦法》、《115年度教育部學海飛颺及學海惜珠計畫甄選簡章》及 31 校共 317 篇歷屆赴外與赴大陸交換學生心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['人文社會學院', '管理學院', '理工學院', '健康護理學院'],
    aliases: ['nqu', '國立金門大學', '金門大學', '金大', '國立金門技術學院', '金門技術學院', 'NQU', 'National Quemoy University'],
  ),
  SupportedUniversity(
    id: 'isu',
    schoolName: '義守大學',
    shortName: '義大',
    englishName: 'I-Shou University',
    officialUrl: 'https://oica.isu.edu.tw/page/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B-NlHq3RuLdDcK',
    supportLevel: 'full',
    partnerCount: 181,
    coverageNote: '完整支援：已整合義守大學國際及兩岸事務處（OICA）《出國交換暨雙聯學位專區》、《交換姐妹校名冊》、《雙聯學位學校列表（11 校）》、《全球與兩岸合作姐妹校名錄》、《海外交換費用參考表》、《義守大學學生赴境外交換研修甄選辦法》、《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》、《義守大學學海助學金設置及甄選作業辦法》、《義守大學赴大陸校際交換獎學金辦法》與《義守大學學文助學金設置及甄選作業辦法》官方資料：（1）校內甄選時程與資格：每年 2 月開放第一梯次（秋季班出國交換一學期或一學年）及每年 8 月開放第二梯次（春季班出國交換一學期）校內甄選，限大二以上或碩一以上在學學生，出國期間維持本校學籍並繳交義守大學全額學雜費，每學期修習至少 9 學分（大陸研修團至少 16 學分），外語能力應符合交流學校規定或通過本校英語畢業資格檢定標準（CEFR B1 / TOEIC 550 / TOEFL iBT 42 / IELTS 4.0）。（2）合作姐妹校與雙聯學位：完整收錄 181 所全球及兩岸港澳有效締約姐妹校（橫跨 33 國與地區，含英、美、港、日、韓、陸 11 所跨國雙聯學位合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠》（系前 40% 或班前 30%）、《義守大學學海助學金》、《赴大陸校際交換獎學金》、《義守大學學文助學金》（交流團、暑期學習團公費／部分公費與一學期大陸研修團）、《歐盟 Erasmus+ 獎學金》及 13 所合作大學共 18 篇歷屆學長姐交換心得報告与 12 份官方 Fact Sheet。',
    academicScoreMinimum: 60.0,
    colleges: ['智慧科技學院', '工學院', '管理學院', '傳播與設計學院', '國際學院', '觀光餐旅學院', '醫學院', '醫學科技學院', '原住民族學院', '通識教育中心'],
    aliases: ['isu', '義守大學', '義大', '義守', 'ISU', 'I-Shou University', 'IShou University'],
  ),
  SupportedUniversity(
    id: 'fgu',
    schoolName: '佛光大學',
    shortName: '佛大',
    englishName: 'Fo Guang University',
    officialUrl: 'https://oica.fgu.edu.tw/zh_tw/exchange/20',
    supportLevel: 'full',
    partnerCount: 52,
    coverageNote: '完整支援：已整合佛光大學國際暨兩岸事務處（OICA，雲起樓 112 室）《115學年度第一學期交換生／雙學位甄選說明會簡報》、《認識 2+2 Program（佛光山系統大學美國西來大學 University of the West 台美雙學位）》、《英國國立密德薩斯大學 Middlesex University 3+1／1+1 雙聯學位說明會簡報》、《佛光大學赴中國大陸以外國家及地區交換學生甄選辦法（A06-004）》、《佛光大學赴大陸交換學生甄選辦法（A06-005）》、《佛光大學學生參與西來大學 2+2 計畫實施辦法》、《佛光大學林陸素琦女士海外留學獎勵基金設置與管理辦法》、《佛光大學學海無涯國際交流獎助學金設置與管理辦法》、《佛光大學辦理國內外學校學生交流學習執行要點》與《歷屆海外交換及台美雙學位甄選錄取榜單與分享會簡報》官方資料：（1）兩梯次校內甄選時程、75分／全班前50%學業門檻與圖書館 EASY TEST iBT 測驗規定：每學期初（9–10月及2–3月）辦理次學期赴海外及大陸交換生暨雙聯學位校內甄選（如 115-1 甄選說明會於 2026/09/23 舉辦、申請文件繳交截止日為 2026/10/08），限具本校正式學籍之在學學生（大學部大二以上或碩博班碩一以上，大一下可報名大二交換，大一／大二可報名西來大學 2+2 雙學位），前一學期學業平均成績須達 75 分（約 GPA 3.0）以上且操行成績達 80 分以上（申請中國人民大學、南京大學、東南大學、四川大學、北京交通大學等大陸 985/211 重點名校須達全班排名前 20% 以內）；報名海外交換或雙學位者須於校內甄選前先完成圖書館線上英文模擬測驗「EASY TEST iBT 托福題型」並繳交成績單，外語能力依姊妹校規定須達英語 TOEFL iBT 61–80 / IELTS 5.5–6.5 / TOEIC 550–750、日檢 JLPT N3–N2 或韓檢 TOPIK 2–3 級（大陸姊妹校免附外語檢定）；交換期間於佛光大學完成註冊繳費並免繳姊妹校學費（日本花園大學與韓國金剛大學另提供免住宿費、美國西來大學交換生每學期最高獎助 US\$3,500、2+2 雙學位生每學期最高獎助 US\$7,500）。（2）全球 13 國／地區 52 所合作姊妹校與佛光山教團系統大學：完整收錄美國 3 校（西來大學、休士頓大學清湖分校、春山學院）、英國 1 校（國立密德薩斯大學）、德國 1 校（漢堡大學）、澳洲 1 校（南天大學）、紐西蘭 1 校（奧塔哥大學）、日本 2 校（龍谷大學、花園大學）、韓國 12 校（京畿大學、東國大學首爾校區、東國大學 WISE 校區、慶尚國立大學、金剛大學、東明大學、昌原國立大學、威德大學、新羅大學、中央僧伽大學、建國大學、京東大學）、泰國 2 校（正大管理學院、ม่โจ้大學 Maejo University）、馬來西亞 1 校（拉曼大學）、菲律賓 2 校（拉普拉普宿霧國際大學、光明大學）、印度 1 校（德里大學）、緬甸 1 校（龐道烏國際大學）、香港 1 校（香港教育大學）及中國大陸 23 校（中國人民大學、南京大學、北京交通大學、上海大學、四川大學、深圳大學、華中師範大學、鄭州大學、西北師範大學、陽光學院、東南大學、煙台大學、揚州大學、合肥工業大學、集美大學、廣東海洋大學、福建技術師範學院、海南大學、南京理工大學、濟南大學、陝西師範大學、雲南大學、青海民族大學）共 52 所合作大學（含 50 所當期開放申請之交換與雙聯合作校）。（3）四大獎助學金體系與學長姐經驗傳承：涵蓋教育部《學海飛颺／學海惜珠》、《林陸素琦女士海外留學獎勵基金》、《學海無涯國際交流獎助學金》與《西來大學 2+2 計畫獎學金》，以及 26 所合作大學共 30 篇歷屆交換生與雙學位生錄取榜單及分享會心得紀錄。',
    academicScoreMinimum: 75.0,
    colleges: ['人文學院', '社會科學院', '管理學院', '創意與科技學院', '樂活產業學院', '佛教學院'],
    aliases: ['fgu', '佛光大學', '佛大', '佛光', 'FGU', 'Fo Guang University'],
  ),
  SupportedUniversity(
    id: 'nkuht',
    schoolName: '國立高雄餐旅大學',
    shortName: '高餐大',
    englishName: 'National Kaohsiung University of Hospitality and Tourism',
    officialUrl: 'https://iao.nkuht.edu.tw/p/412-1005-857.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 40,
    coverageNote: '完整支援：已整合國立高雄餐旅大學國際事務處（OIA）《海外留學交換平台（2027-28 交換學生與雙聯學位簡章）》、《辦理學生海外實習及留學補充規定（113.06.05修正）》、《115年度教育部學海飛颺及學海惜珠計畫甄選簡章》及《遠航圓夢助學金實施辦法》官方資料：（1）校內甄選時程與資格：免學費交換生為三年級出國交換一學年、自費交換生及 1+1 雙聯碩士為三年級或研究所出國一學年，115-1 起跑（2026/09/17 留學說明會、2026/10–12 校內報名收件、2027/02–03 國際處公告錄取名單與姊妹校提名），歷年操行成績須無小過以上紀錄、學業成績總平均達 75 分以上（或班排名前 20%–30%），並具備多益、托福、雅思、全民英檢、日檢 JLPT N2–N3 或韓檢 TOPIK 等語檢證明。（2）合作姊妹校與雙聯學位：完整收錄 40 所海外餐旅觀光名校（橫跨 15 國，含 31 所 2027-28 開放申請之免學費交換、自費交換與瑞士 SHMS／César Ritz、英國 UCB、美國天普大學及南卡羅來納大學 1+1 雙聯碩士合作校，以及 9 所重點海外合作大學）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／學海惜珠》（歐洲最高補助 NT\$120,000、美加最高 NT\$150,000）、《高餐大遠航圓夢助學金》（最高 NT\$200,000）及 17 所合作大學共 19 篇歷屆學長姐赴外交換與雙聯實習心得報告。',
    academicScoreMinimum: 75.0,
    colleges: ['餐旅學院', '觀光學院', '廚藝學院', '國際學院', '全人教育學院'],
    aliases: ['nkuht', '國立高雄餐旅大學', '高雄餐旅大學', '高餐大', '高餐', 'NKUHT', 'National Kaohsiung University of Hospitality and Tourism'],
  ),
  SupportedUniversity(
    id: 'nuu',
    schoolName: '國立聯合大學',
    shortName: '聯大',
    englishName: 'National United University',
    officialUrl: 'https://oia.nuu.edu.tw/p/412-1068-1242.php',
    supportLevel: 'full',
    partnerCount: 128,
    coverageNote: '完整支援：已整合國立聯合大學研究發展處國際及兩岸事務組（OIA）《國際交換學生作業要點（109.03.03修正）》、《國際學術交流實施辦法（110.05.25修正）》、《雙聯學制實施辦法（106.02.18）》、《學生赴國外研修留學國語言能力參考標準》、《補助學生參與境外學術交流及研習服務經費管理要點》、《「學海系列計畫」甄選作業要點（114.01.16修正）》、《學生於締約學校修讀課程學分與成績轉換參考表》、《交換學校一覽表（128校）》及《全球締約姊妹校名錄》官方資料：（1）兩梯次校內甄選、「出國交換當時」年級系所認定、分組配分與NT\$ 3,000保證金規定：每年1月（第一梯次，結合12/15–2/14教育部學海飛颺／惜珠期程，得申請一學期或一學年）及8月（第二梯次春季班，僅得申請一學期）辦理校內甄選，具本校大學部及研究所學籍之在學學生（不含在職生）皆可申請，惟各姊妹校之年級與系所限制以「出國交換當時」之學籍身分與年級為準；甄選採計總分未達60分不予推薦（赴大陸以外地區大學部採計在校成績50%＋外語20%＋自傳10%＋讀書計畫15%＋其他5%、研究所採計在校成績30%＋外語20%＋自傳20%＋讀書計畫25%＋其他5%；赴大陸地區免計外語，大學部採計在校成績60%＋自傳15%＋讀書計畫20%＋其他5%、研究所採計在校成績40%＋自傳25%＋讀書計畫30%＋其他5%）；錄取後20日內須繳交保證金NT\$ 3,000，交換期間每學期大學部至少修讀3門課程及格、研究所至少修讀1門課程及格，返國後14日內繳交返國程序單與中英文心得並完成20小時國際組服務後全額退還。（2）全球21國／地區128所合作姊妹校、日本國立高專（NIT）聯盟與6校美法加雙聯學位：完整收錄128所合作姊妹校（含29所常態開放申請之交換、雙聯與日本高專暑期研習合作校，涵蓋日本宇部、高知、新居濱、阿南、木更津、明石、小山、釧路等國立高專及甲南大學、愛知教育大學，韓國仁荷大學、昌原國立大學、高麗網路大學，美國霜堡州立大學 FSU 2+2、佛羅里達理工學院 FIT 2+2、樹城州立大學 Boise State 2+2、南猶他大學 SUU、明尼蘇達州立大學曼卡托分校，加拿大安大略理工大學、卡加利大學，法國南特理工大學、薩瓦勃朗峰大學，德國馬德堡大學，馬來西亞拉曼大學 UTAR，泰國吞武里蒙庫國王科技大學 KMUTT，越南胡志明市經濟大學 UEH，印尼總統大學、迪波內戈羅大學及蒙古全球領袖大學）。（3）獎助學金體系：涵蓋教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》、聯大《補助學生參與境外學術交流經費》（亞太最高NT\$ 15,000、歐美最高NT\$ 25,000–35,000、團隊最高NT\$ 100,000）、日本JASSO獎學金及美國雙聯學位獎學金（FSU每學期USD 3,000、FIT每學期USD 5,000–7,000、SUU USD 4,250）。',
    academicScoreMinimum: 60.0,
    colleges: ['理工學院', '電機資訊學院', '管理學院', '客家研究學院', '人文與社會學院', '設計學院'],
    aliases: ['nuu', '國立聯合大學', '聯合大學', '聯大', 'NUU', 'National United University'],
  ),
  SupportedUniversity(
    id: 'tnnua',
    schoolName: '國立臺南藝術大學',
    shortName: '南藝大',
    englishName: 'Tainan National University of the Arts',
    officialUrl: 'https://oia.tnnua.edu.tw/p/412-1007-1052.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 63,
    coverageNote: '完整支援：已整合國立臺南藝術大學國際事務處（OIA）《海外姊妹校締約一覽表（63校）》、《115學年度第一學期赴國外及大陸地區姊妹校交換生甄選公告》、《國立臺南藝術大學選送學生出國研修與交流甄選辦法（113.06.03修正）》、《學生修讀國外與港澳地區雙聯學位實施辦法（112.01.03修正）》、《辦理教育部學海飛颺、學海惜珠及學海築夢補助作業要點》、《選送學生赴國外研修獎助學金審查原則》與《海外研修暨學海築夢經驗分享（38篇）》官方資料：（1）兩階段校內甄選、系所書審與外語口試門檻：每年分兩學期（秋季班於前一年9–10月、春季班於當年度2–4月，如115-1秋季班於2025/09/17公告、10/14截止收件、10/29面試，115-2春季班於2026/02/13啟動春季提名）辦理甄選，限本校日間學制大學部二年級以上、七年一貫制學士班五年級以上及碩博士班就讀一學期以上之在學學生（不含碩士班在職專班、休學生及外籍學位生）；第一階段「系所書面初審」（占50%，含歷年成績與研修計畫30%、專業作品與成就20%）須經系所會議通過且初審成績達40分（滿分50分）以上始得進入複審，第二階段「校內口試複審」（占50%，含面試表現30%、語言能力含1–2分鐘擬赴國家語言自我介紹20%），兩階段總成績須達80分（含）以上始得錄取；外語能力依《外國語文能力對照表》建議達英語 TOEFL iBT 79 / IELTS 6.0、日檢 JLPT N2、韓檢 TOPIK 3級、法語 DELF/TCF B1、德語 B1 / TestDaF TDN3 或西語 DELE B1 以上（中國大陸姊妹校免附外語檢定）；交換期間須完成南藝大註冊繳費並免繳姊妹校學費，每學期至少修習1門專業課程。（2）全球21國／地區63所合作姊妹校與跨國雙聯學位：完整收錄中國大陸25校、美國6校、日本4校、印尼4校、韓國3校、法國3校、奧地利2校、捷克2校、新加坡2校、泰國2校及德、義、西、瑞士、波蘭、愛沙尼亞、保加利亞、澳洲、越南、哈薩克各1校共63所合作藝術與綜合大學（含29所開放學期交換與雙聯學位之姊妹校，以及美國舊金山藝術學院 SFAI 雙聯學位與《學生修讀國外與港澳地區雙聯學位實施辦法》）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（學業總平均80分／GPA 3.0以上）、《學海惜珠》、《學海築夢／新南向學海築夢》及南藝大《選送學生赴國外研修獎助學金審查原則》，以及18所合作大學與海外博物館／古物修復機構共38篇歷屆學長姐出國交換與學海築夢實習心得報告。',
    academicScoreMinimum: 80.0,
    colleges: ['音樂學院', '視覺藝術學院', '音像藝術學院', '文博學院', '跨域創生學院'],
    aliases: ['tnnua', '國立臺南藝術大學', '國立台南藝術大學', '臺南藝術大學', '台南藝術大學', '南藝大', '南藝', 'TNNUA', 'Tainan National University of the Arts'],
  ),
  SupportedUniversity(
    id: 'tpcu',
    schoolName: '臺北城市科技大學',
    shortName: '城市科大',
    englishName: 'Taipei City University of Science and Technology',
    officialUrl: 'https://ieec.tpcu.edu.tw/',
    supportLevel: 'full',
    partnerCount: 18,
    coverageNote: '完整支援：已整合臺北城市科技大學國際事務處（國際交流中心）、商管學院、民生學院、工程學院與研究發展處《海外留學姊妹校總表》、《學生出國研修辦法（106.06.19修訂）》、《與境外大學辦理雙聯學制實施辦法（105.09.14教育部備查）》、《教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠校內甄選辦法（108.01.21修訂）》、《教育部獎助大專校院國外專業實習計畫—學海築夢及新南向學海築夢校內甄選辦法（115.01.05修訂）》及《學生海外實習及研習輔導要點（106.10.30修訂）》官方資料：（1）校內甄選資格、錄取確認與修課抵免：申請出國交換研修者須為就讀本校滿一學年以上且非當學期畢業之在學學生（不含境外碩士專班；學海計畫須在學滿一學期以上且不含在職專班生），無小過以上處分紀錄，前一學年學業平均總成績達 60 分以上、操行平均總成績達 75 分以上；錄取生於公告隔天至國際事務處報到、1 週內繳交錄取確認書；海外研習一學期上課總學分不得少於 10 學分，返國後當學期開學 1 週內辦理學分抵免。（2）海外合作姊妹校與跨國雙聯學制：完整收錄 18 所日、韓、紐、英、美官方合作姊妹校（含日本城西國際大學、神戶國際大學、鹿兒島國際大學、國立琉球大學、日本經濟大學、北海道星槎道都大學、國立德島大學、十文字學園女子大學、國立宇都宮大學、昭和音樂大學；韓國信韓大學、富川大學；紐西蘭國際太平洋大學 IPU New Zealand；英國伯明翰大學學院 UCB；美國加州峽谷大學、曼徹普利敦州立大學、聖保羅學院、明州西南州立大學，其中 11 校提供 2+2／3+1／1 年雙聯學位）。（3）獎助學金與留學榜單：涵蓋教育部《學海飛颺／惜珠》（補助 NT\$50,000–300,000）、《學海築夢／新南向學海築夢》海外實習獎助及 18 所合作大學共 38 篇歷屆交換雙聯榜單與研修紀錄。',
    academicScoreMinimum: 60.0,
    colleges: ['工程學院', '商管學院', '民生學院'],
    aliases: ['tpcu', '臺北城市科技大學', '台北城市科技大學', '城市科大', '北城科大', '臺北城市科大', '台北城市科大', '城市大學', '北台科大', '北台科學技術學院', '光武工專', 'TPCU', 'Taipei City University of Science and Technology'],
  ),
  SupportedUniversity(
    id: 'au',
    schoolName: '真理大學',
    shortName: '真理',
    englishName: 'Aletheia University',
    officialUrl: 'https://cia.au.edu.tw/p/403-1022-109353.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 80,
    coverageNote: '完整支援：已整合真理大學國際事務中心（CIA）《交換計畫專區》、《雙聯學制專區》、《短期研修專區》、《姐妹校一覽》、《法規與獎學金辦法》與《學海計畫專區》官方資料：（1）校內甄選時程與資格：依《真理大學交換學生出國甄選辦法（教-P-806）》、《2027春季／2026秋季國外姐妹校交換學生實施計畫》與《2026~2027日本姐妹校交換生實施計畫》，限就讀滿一學年以上之大學部與研究所在學學生（大二、碩二以上），前一學期學業成績全班前 50% 為原則且操行 80 分以上，報名繳交 NT\$3,000 行政處理費，交換期間繳交真理大學全額學雜費且每學期修習至少 9 學分；日本交換組要求三年內通過 JLPT N2 以上（日本多摩大學可憑 JLPT N2 或 TOEIC 600 申請）。（2）合作姐妹校與雙聯學位：完整收錄 80 所全球及兩岸港澳有效締約姐妹校（橫跨 14 國與地區，含 31 所當期開放申請之出國交換與雙聯學位合作校，涵蓋英國密德薩斯大學、英國西英格蘭大學 UWE Bristol 及西班牙赫羅納大學觀光學院 EUHT StPOL 雙聯學制）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠／築夢／新南向學海築夢》、《真理大學交換學生出國獎學金辦法（P-01-510）》、《外國語言遊學獎助學金（P-01-509）》、《國際志工服務獎助學金（P-01-513）》、《特殊貢獻獎助學金（P-01-526）》及 14 所合作大學共 88 篇歷屆學長姐返國交換心得報告。',
    academicScoreMinimum: 60.0,
    colleges: ['人文學院', '觀光休閒與運動學院', '管理與資訊學院', '財經學院', '通識教育中心'],
    aliases: ['au', '真理大學', '真理', '真大', 'AU', 'Aletheia University', 'Oxford College Tamsui'],
  ),
  SupportedUniversity(
    id: 'knu',
    schoolName: '開南大學',
    shortName: '開南',
    englishName: 'Kainan University',
    officialUrl: 'https://knuoica.knu.edu.tw/p/406-1004-59525,r30.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 88,
    coverageNote: '完整支援：已整合開南大學國際及兩岸事務處（OICA）《海外交換、日本交換、大陸交換與跨國雙聯學位簡章》、《全球姊妹校名冊（88校）》、《開南大學與境外大學校院辦理跨國雙學位制實施辦法》、《開南大學選派優秀學生赴國外研修獎助學金執行要點》及《海外研修與雙聯學位學生心得專區（43校121篇）》官方資料：（1）兩階段校內甄選、學業與語言門檻：每年分兩梯次（秋季班 9～10 月初、春季班 2～3 月中旬；大陸交換秋季班 3～4 月、春季班 10～11 月）辦理甄選，限大學部日間部及進修學士班 1～3 年級、碩士班 1 年級在學學生（轉學生須於本校就讀滿一學年；不含碩士在職專班及應屆畢業生），一般海外、日本及大陸交換歷年每學期學業平均達 75 分（GPA 2.75）以上，雙聯學位（富山、札幌國際、威斯康辛河瀑）與教育部學海系列獎學金須達 80 分（GPA 3.0）以上且操行成績達 82 分以上（佛羅倫斯美國大學 AUF 雙聯門檻為 GPA 2.5）；語言能力須達英語組 TOEIC 500 / IELTS 4.5 / TOEFL iBT 61 / ITP 500（日本全英授課須 TOEIC 600 / IELTS 5.0，AIU 須 TOEIC 785 / iBT 71）、日語組 JLPT N3～N1（島根、德島、愛媛、弘前、山口、名櫻、神戶國際、星城可 N3，多數國立與私立名校須 N2，御茶水女子大學及富山雙聯須 N1）或韓語組 TOPIK 3 級（大陸交換免附外語檢定）；採第一階段書面審查與第二階段面試。（2）全球 15 國／地區 88 所姊妹校與 5 校跨國雙聯學位：完整收錄 70 所常態開放交換與雙聯學校及 18 所學術合作姊妹校，日本高達 42 校（含御茶水女子大學、奈良女子大學、東京海洋大學、富山大學、弘前大學、山形大學、島根大學、山口大學、香川大學、愛媛大學、德島大學、琉球大學等 12 所日本國立大學及秋田國際教養大學 AIU、北九州市立大學、名櫻大學、尾道市立大學等 6 所公立名校），並提供日本國立富山大學（2+2 雙學士，免繳日方學費！）、日本札幌國際大學（2+2／1+1 雙學士）、美國威斯康辛大學河瀑分校 UW-River Falls（2+2 雙學士）、美國密蘇里科技大學 Missouri S&T（3+1.5 學碩雙聯）及義大利佛羅倫斯美國大學 AUF（2+2／3+1 雙學士，觀光餐旅直抵 69 學分且首學期減免學費）等 5 校雙聯學位。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠》、《開南大學選派優秀學生赴國外研修獎助學金》及 43 所合作大學共 121 篇歷屆學長姐出國交換與雙聯研修心得報告。',
    academicScoreMinimum: 75.0,
    colleges: ['商學院', '觀光運輸學院', '資訊媒體學院', '人文社會學院', '健康照護管理學院', '法律學院'],
    aliases: ['knu', '開南大學', '開南', 'KNU', 'Kainan University'],
  ),
  SupportedUniversity(
    id: 'nutn',
    schoolName: '國立臺南大學',
    shortName: '南大',
    englishName: 'National University of Tainan',
    officialUrl: 'https://oia.nutn.edu.tw/?page_id=971',
    supportLevel: 'full',
    partnerCount: 114,
    coverageNote: '完整支援：已整合國立臺南大學國際事務處國際事務組（OIA，府城校區誠正大樓 3 樓 B302 室）《116學年度出國交換學生甄選簡章》、《115學年度第1、2學期出國交換學生甄選簡章》、《2026-2027美國天普大學（Temple University）3+2學碩雙聯學位申請公告與Fact Sheet》、《四大洲締約姊妹校名錄（114校）》、《國立臺南大學選送學生出國研修辦法》、《國立臺南大學選送優秀學生出國研修獎學金審查作業要點》、《高教深耕計畫補助學生赴國外進行國際交流實施要點》、《學生進行國外教育見習教育實習及國際史懷哲計畫要點》與《海外教育計畫網站（ESA）暨南大新聞電子報海外交流報導（33校49篇）》官方資料：（1）兩梯次校內甄選、100%書面審查與全班前50%獎學金同步核定機制：每年分兩梯次（第1梯次11月15日至11月30日受理次學年度秋季班／全學年交換、第2梯次4月1日至4月20日受理當學年度春季班交換）於海外教育計畫網站（ESA）線上填報並送交紙本至B302室，限大學部一年級（含）以上、碩博士班一年級（含）以上之在學學生（含進修部；出國就讀時須在本校就讀至少一學期，修業年限內限交換一次，下學年將順利畢業者不得申請）；採100%書面審查（在校成績及名次百分比、外語檢定證明、1,000–1,500字中文自傳與讀書計畫、最多5項優良表現，至多填3志願），凡在校學業成績平均達全班前50%且具CEFR B1以上外語證明者，無須另備文件即由甄選委員會一併審查校內交換生獎學金及教育部學海飛颺／惜珠獎學金。（2）全球19國／地區114所合作姊妹校與美國天普大學3+2雙聯學位：完整收錄25所最新簡章開放申請之交換與雙聯合作校及89所正式締約姊妹校，日本涵蓋大阪公立大學、北海道大學、岡山大學、埼玉大學、長崎大學、順天堂大學（N2或iBT 72）及獨協大學、金澤星稜大學（日語密集課程JLPT N5即可申請！），韓國東國、崇實、天主教關東、德成女子大學與捷克赫拉德茨克拉洛韋大學、波蘭歐波蘭大學採計英語CEFR B1（TOEIC 550 / iBT 42 / IELTS 4.0）或TOPIK 3級，美國中央阿肯色大學UCA（iBT 79，音樂系可附個人演奏曲目免英檢！）、奧特本大學、密蘇里大學堪薩斯分校UMKC及美國天普大學（Temple University）3+2學碩雙聯學位（DBMD，大三以上GPA 3.0、免GRE、享最高USD 10,000獎學金）。（3）四大獎助學金體系與海外實踐報導：涵蓋《校內交換學生獎學金》（亞洲每學期最高NT\$25,000、非亞洲每學期最高NT\$40,000）、教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》、《高教深耕國際交流與公開展演競試補助》（最高NT\$30,000）及《國外教育見習與國際史懷哲計畫》，並收錄33所合作大學共49篇歷屆海外交流報導與研修指南。',
    academicScoreMinimum: 75.0,
    colleges: ['教育學院', '人文學院', '理工學院', '環境與生態學院', '藝術學院', '管理學院'],
    aliases: ['nutn', '國立臺南大學', '國立台南大學', '臺南大學', '台南大學', '南大', '國立臺南師範學院', '臺南師範學院', '南師', 'NUTN', 'National University of Tainan'],
  ),
  SupportedUniversity(
    id: 'niu',
    schoolName: '國立宜蘭大學',
    shortName: '宜大',
    englishName: 'National Ilan University',
    officialUrl: 'https://oia.niu.edu.tw/p/404-1014-9618.php',
    supportLevel: 'full',
    partnerCount: 97,
    coverageNote: '完整支援：已整合國立宜蘭大學國際事務處（OIA，行政大樓 5 樓）《學生赴境外研習暨交換申請資訊簡章》、《美國密西根大學迪爾伯恩分校 UM-Dearborn 3+2／1+1 雙聯學位專頁》、《學生境外學習手冊（Students Go Global Guidebook）》、《四大洲及大陸地區締約姊妹校名錄（97校）》、《國立宜蘭大學學生赴境外研修甄選作業要點》、《國立宜蘭大學與境外大學辦理雙聯學制實施辦法》、《國立宜蘭大學學生赴境外研修獎補助要點》、《國立宜蘭大學學海系列方案甄選及補助要點》與《國立宜蘭大學學生參與國際性活動獎補助要點》官方資料：（1）兩梯次校內甄選、大學部全班前 60%／研究生 75 分門檻與每學期 4 學分或 2 門課規定：每年分兩梯次（秋季班 2 月初至 3 月底、春季班 9 月初至 10 月底）受理次學期赴境外（含大陸）交換甄選，限具本校學籍之日間學制學生（非中華民國籍學生不得交換至原屬國家），大學部前一學期學業成績須為全班前 60%、研究生學業成績平均達 75 分以上，且前一學期操行成績達 75 分以上無重大違紀事件；外語能力依各姊妹校規定（英語組 TOEIC 500–785 / IELTS 5.0–6.0 / TOEFL iBT 70–80、日語組 JLPT N5–N1、韓語組 TOPIK 3 級、大陸地區免外語檢定）；交換期間繳交宜大學雜費、免繳姊妹校學雜費，每學期至少修讀 4 學分或 2 門課程，抵達姊妹校 14 天內回報國外聯絡方式，返國後 1 個月內繳交至少 3 頁中文心得報告電子檔並配合經驗分享會及接待來校交換生。（2）全球 19 國／地區 97 所合作姊妹校與 9 校跨國雙聯學位：完整收錄 84 所常態開放申請之交換、雙聯與自費研修合作校及 13 所正式締約姊妹校，涵蓋美國密西根大學迪爾伯恩分校（UM-Dearborn 3+2 學碩／1+1 雙碩士，GPA 3.0、iBT 80–84 / IELTS 6.5，享本州生 1.2 倍學費減免）、美國伊利諾大學香檳分校（UIUC 環工／化材雙聯）、加拿大英屬哥倫比亞大學（UBC 森資系 2+2 雙學士）、瑞士 SHMS 瑞士酒店管理大學與 César Ritz 凱撒里茲酒店管理大學（休健系 3+1／2+1+1／3+2 雙聯含 4–6 個月有薪實習）、印尼日惹大學（UGM 雙聯）與阿瑪加雅大學（UAJY 建研所 1+1 雙碩士）、越南胡志明市理工大學（HCMUT 化工雙聯）及大陸福州大學（經管學院 1+1 雙碩士）等 9 校雙聯學位。（3）四大獎助學金體系與返國心得：涵蓋教育部《學海飛颺／學海惜珠》（大學部前 40%、研究生 80 分以上，補助 NT\$50,000–450,000）、《學海築夢／新南向學海築夢》、《校內學生赴境外研修獎補助》（歐美非最高 NT\$30,000、紐澳 NT\$25,000、亞洲 NT\$15,000、大陸港澳 NT\$10,000，另加重點學校獎助 NT\$3,000–5,000 與語文成績獎助最高 NT\$4,000）及《參與國際性活動獎補助》，並收錄 22 所合作大學共 38 篇歷屆學長姐出國交換與雙聯學位心得分享紀錄。',
    academicScoreMinimum: 75.0,
    colleges: ['人文及管理學院', '工學院', '生物資源學院', '電機資訊學院', '博雅學部'],
    aliases: ['niu', '國立宜蘭大學', '宜蘭大學', '宜大', '國立宜蘭技術學院', '國立宜蘭農工專科學校', '宜蘭農專', '宜蘭農校', 'NIU', 'National Ilan University'],
  ),
  SupportedUniversity(
    id: 'nptu',
    schoolName: '國立屏東大學',
    shortName: '屏大',
    englishName: 'National Pingtung University',
    officialUrl: 'https://ccd.nptu.edu.tw/p/412-1091-12234.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 172,
    coverageNote: '完整支援：已整合國立屏東大學國際事務處（OIA，下設國際合作組與大陸事務組）《115年出國交換甄選簡章》、《116學年度出國交換／實習三校區說明會公告（2026/12/08–12/10，報名至 11/30 17:00）》、《115年第1次教育部學海築夢及新南向學海築夢甄選簡章》、《跨國雙聯學位專區（英、美、捷、日、泰 7 校）》、《學生出國有關學業及學籍處理要點（114.03.27修正）》、《與境外大學校院辦理雙聯學制實施辦法（114.05.22修正）》、《學生抵免學分要點（115.10.22修正）》、《與外國學制學分轉換準則》、《學海計畫學生生活費核銷支給數額標準表》及《出國交換學生心得分享專區（20校61篇）》官方資料：（1）四大推薦計畫、語檢門檻與雙軌送件：每年 12 月舉辦三校區說明會、1–2 月收件、2 月下旬 17:00 截止、3 月初面試，分為【教育部學海飛颺】（本國籍就讀滿一學期一般生、歷年成績班排前 50% 內、操行平均 80 分以上且無申誡以上處分）、【教育部學海惜珠】（同飛颺條件並具低收／中低收／特殊境遇／身障等資格）、【本校「菁英育才」補助（校友捐款）】（無班排前 50% 限制，惟「每學期」操行皆須達 80 分以上，補助生活費每月 NT\$10,000 最高 5 個月＋機票費最高 NT\$30,000，合計最高 NT\$80,000）及【自費交換】（含在職生與進修生）；非日語組須達 CEFR B1（TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0 / GEPT 中級初試），日語組須達 JLPT N2（校內甄選時得先以非日語 B1＋師長簽署《日本語力評價表》替代）；至多填寫 5 所志願學校，紙本送交屏商行政大樓 3F 國際合作組並將合併 PDF 寄至 vida2022@mail.nptu.edu.tw；交換期間於屏大完成註冊且大學部每學期至少修 1 門課（姬路獨協大學須修 7 門課以上），返國次學期期末考前一次辦理學分抵免（1 NPTU＝2 ECTS＝4 CATS＝4 澳洲學分）。（2）全球 24 國／地區 172 所合作姊妹校與 7 校跨國雙聯學位：完整收錄 41 所常態開放申請之交換與雙聯合作校（含日本宮崎大學、弘前大學、大阪教育大學、兵庫教育大學、室蘭工業大學、和歌山大學、鹿兒島大學、香川大學、山形大學、信州大學等 10 所日本國立大學與麗澤、姬路獨協、廣島修道、山陽學園、日本經濟大學，捷克 UHK 10 名、TBU、TUL、CTU，德國 ASH Berlin，義大利帕維亞大學，韓國外國語大學 HUFS，馬來亞大學 UM，以及泰國程逸皇家大學等 4 校「免學費＋免住宿費」優惠）及英國密德薩斯大學（3+1／1+1）、美國北阿拉巴馬大學（3+1／2+2／1+1）、美國西來大學（2+2／1+1）、捷克 UHK（1+1）、捷克 TBU（1+1）、泰國宋卡王子大學（2+2）、泰國蒙庫國王科技大學 KMUTT（1+1）等 7 校雙聯學位。（3）返國心得：完整收錄 20 所合作大學共 61 篇歷屆學長姐出國交換與海外研修心得報告。',
    academicScoreMinimum: 60.0,
    colleges: ['管理學院', '資訊學院', '教育學院', '人文社會學院', '理學院', '國際學院', '大武山學院'],
    aliases: ['nptu', '國立屏東大學', '屏東大學', '屏大', '國立屏東教育大學', '屏東教育大學', '屏教大', '國立屏東商業技術學院', '屏東商業技術學院', '屏商技', '屏商', '屏師', 'NPTU', 'National Pingtung University'],
  ),
  SupportedUniversity(
    id: 'npu',
    schoolName: '國立澎湖科技大學',
    shortName: '澎科大',
    englishName: 'National Penghu University of Science and Technology',
    officialUrl: 'https://www.npu.edu.tw/content.aspx?id=273',
    supportLevel: 'full',
    partnerCount: 37,
    coverageNote: '完整支援：已整合國立澎湖科技大學研究發展處國際事務組（ORD International Affairs Section）《交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法（108.09.19修正通過）》、《辦理教育部鼓勵大專校院選送學生出國研修（學海飛颺、學海惜珠）審查要點（115.03.25通過）》、《辦理教育部鼓勵大專校院選送學生國外專業實習（學海築夢、新南向學海築夢）審查要點（115.03.25通過）》、《獎助學生境外研修及參訪辦法（108.12.19修正通過）》、《辦理雙聯學制實施辦法（104.11.30教育部備查）》、《國際合作姊妹校一覽表》、《與本校簽訂學生交流協議書清冊》及各姊妹校交換入學簡章官方資料：（1）兩梯次校內選薦、40%/40%/20% 量化評分與系務會議課程認可規定：每年分秋季班（3月1日至3月31日校內收件，5月15日／5月30日前向姊妹校完成提名）與春季班（9月1日至9月30日校內收件，11月15日／11月30日前向姊妹校完成提名）辦理出國交換甄選，並於每年 2–3 月辦理教育部學海系列計畫校內甄選；限已就讀本校一學期以上且非當學期畢業之在學學生（含四技、二技、五專部專四及專五、碩士班，不含國內及境外在職專班生），擬進修課程須先檢附所屬系所課程委員會或系務會議同意之會議紀錄；由研發長召集教務長及各學院委員組成「學術合作審查小組」，依「在校成績 40%、語文能力 40%、讀書計畫 20%」評分，總分達 70 分（含）以上始得由校長名義寄發推薦函；外語能力須符合交換學校或本校自訂標準（英文 TOEIC 550 / IELTS 4.0 / TOEFL ITP 457 / iBT 42，日文 JLPT N4 / J.TEST E 級；學海築夢實習為 TOEIC 400 / GEPT 中級 / JLPT N4 且操行平均 80 分以上；大陸地區交換免附外語能力證明）。（2）全球與大陸 12 國／地區 37 所高等教育合作姊妹校與 3 校跨國雙聯學位：完整收錄 18 所簽署學生交流協議與雙聯學位之常態開放申請學校（日本國立琉球大學、馬來西亞拉曼大學 UTAR、越南峴港大學、越南孫德勝大學、泰國湄州大學、泰國朱拉隆功大學、菲律賓甲米地州立大學、美國匹茲堡州立大學，以及大陸中國海洋大學、上海海洋大學、浙江海洋大學、集美大學、汕頭大學、龍岩學院、浙江越秀外國語學院、黎明職業大學、廣州航海學院、深圳職業技術大學）與 19 所學術合作備忘錄（MOU）姊妹校（含日本長崎大學、菲律賓大學系統、印尼亞齊大學、瑞士教育集團 SEG、馬紹爾群島學院、貝里斯大學等），並提供美國匹茲堡州立大學（2+2 雙學士）、越南孫德勝大學（觀休、海運雙聯學士）及泰國湄州大學（雙聯學位）跨國雙聯通道（學士累計修業滿 32 個月、碩士滿 12 個月）。（3）獎助學金與研修指南：涵蓋教育部《學海飛颺／學海惜珠》（每人平均獎助 NT\$ 50,000–300,000，含本校 20% 配合款）、《學海築夢／新南向學海築夢》、校內《獎助學生境外研修及參訪辦法》（每人補助 NT\$ 5,000–15,000）及 13 所合作大學共 13 篇海外研修指南與交流紀錄。',
    academicScoreMinimum: 70.0,
    colleges: ['海洋資源暨工程學院', '觀光休閒學院', '人文暨管理學院', '博雅教育學院'],
    aliases: ['npu', '國立澎湖科技大學', '澎湖科技大學', '澎科大', '澎湖科大', 'NPU', 'National Penghu University of Science and Technology'],
  ),
  SupportedUniversity(
    id: 'ntunhs',
    schoolName: '國立臺北護理健康大學',
    shortName: '國北護',
    englishName: 'National Taipei University of Nursing and Health Sciences',
    officialUrl: 'https://icsed-rnd.ntunhs.edu.tw/',
    supportLevel: 'full',
    partnerCount: 84,
    coverageNote: '完整支援：已整合國立臺北護理健康大學研究發展處國際暨兩岸教育中心《雙聯學制專區（英美澳6校9學程）》、《海外長短期交換專區》、《教育部學海飛颺／惜珠／築夢專區》、《五大洲締約姊妹校名錄（84校）》、《學生出國期間有關學業及學籍處理要點（112.11.01修正）》、《學生抵免學分處理辦法（115.06.24修正）》及《歷屆雙聯、交換與海外實習心得報告（24校33篇）》官方資料：（1）校內甄選資格、臨床實習同意與在學註冊規定：限日間部四技（2～4年級）、二技、學士後護理系、碩士班及博士班在學學生（不含在職專班），在校歷年平均達 GPA 2.0（百分制 70 分）以上，申請教育部學海飛颺／惜珠獎學金以班排前 50% 及操行 80 分以上無懲戒紀錄優先；因考量各系專業必修與醫院臨床實習排程，交換生及雙聯生皆須經所屬系所同意始得出國，出國進修以二年為限且交換期間須維持北護在學註冊學籍（不得休學）；校內甄選採書面審查（40%–60%，曾任國際學伴 International Buddy 者加分）與中英文面試（40%–60%）。（2）全球 21 國／地區 84 所合作姊妹校與英美澳 6 校 9 學程雙聯學位：完整收錄 37 所常態開放雙聯、長短期交換與海外實習合作校及 47 所五大洲締約姊妹校，涵蓋澳洲昆士蘭大學 UQ（護理雙學士／護理碩士／聽力學碩士／社工碩士雙聯，IELTS 7.0）、美國奧本大學 Auburn（護理 MSN 碩士暨 PhD 博士雙聯，IELTS 6.5）、英國西英格蘭大學 UWE（護理雙學士 IELTS 6.5、資管 3+1 雙學士 IELTS 6.0）、澳洲昆士蘭科技大學 QUT（資管 2+2 雙學士 IELTS 6.5）、澳洲迪肯大學 Deakin（健管 3.5+1.5 MBA 醫療管理雙聯 IELTS 6.5）及澳洲墨爾本威廉安格利斯學院 WAI（休健航空空服／旅遊管理雙聯 IELTS 6.0），以及捷克奧斯特拉瓦大學醫學院、立陶宛 KVK、日本名古屋市立大學、縣立廣島大學、東京都立大學 HIIP（免費荒川校區宿舍）、紐西蘭梅西大學、韓國大邱保健大學（免費雙人房宿舍）等。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠／築夢／新南向學海築夢》及 24 所合作大學共 33 篇歷屆學長姐心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['護理學院', '健康科技學院', '人類發展與健康學院', '智慧健康照護跨領域學院'],
    aliases: ['ntunhs', '國立臺北護理健康大學', '國立台北護理健康大學', '臺北護理健康大學', '台北護理健康大學', '國北護', '北護', '北護大', '國立臺北護理學院', 'NTUNHS', 'National Taipei University of Nursing and Health Sciences'],
  ),
  SupportedUniversity(
    id: 'nttu',
    schoolName: '國立臺東大學',
    shortName: '東大',
    englishName: 'National Taitung University',
    officialUrl: 'https://rd.nttu.edu.tw/p/412-1007-9902.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 59,
    coverageNote: '完整支援：已整合國立臺東大學研究發展處國際事務中心（COIA）《2025–2027 赴境外姊妹校交換生暨雙聯學位甄選簡章與名額一覽表》、《國際暨大陸地區締約姊妹校名錄（59校）》、《辦理學生申請出國進修或交換作業要點》、《學生出國進修獎助學金要點（含附件一 CEFR B1/B2 語言基準表）》、《與境外大學校院辦理雙聯學制實施辦法》、《學生出國期間有關學業及學籍處理辦法》、《學生抵免學分要點》及《出國交換生暨學海築夢心得分享專區（12校58篇）》官方資料：（1）校內甄選時程、在學資格與評分權重：每學期分兩梯次（春季班於前一年 9 月中旬截止，如 2027 春季班於 2026/09/15 中午 12:00 截止、10/15 放榜；秋季班於當年 3 月中旬截止，如 2026 秋季班於 2026/03/20 中午 12:00 截止）受理報名，限本校二年級（含）以上之在學學位生（含學士班大二至大四、碩士班、博士班；不含大一新生、當學期畢業生、延畢生及在職專班學生；大四申請交換以一學期為限），採「書面資料審查 50%＋面試（含外語口試）50%」擇優錄取。（2）全球 15 國／地區 59 所合作姊妹校與日本 2 校跨國雙聯學士學位：完整收錄 15 所當期開放申請之國際與大陸重點交換及雙聯姊妹校（含美國加州西來大學［每期 15 名，至多 12 學分學費半價減免］、日本仙台大學［交換 4–6 名＋2.5+2 雙聯學士 2 名］、日本琵琶湖成蹊體育運動大學［春季班 1.5+2+1 雙聯學士 1 名］、日本天理大學［1 名，免學費、免宿舍費且免水電瓦斯費！］、韓國國立順天大學［2–4 名，免韓檢］、韓國高神大學［1–2 名，免韓檢］、韓國釜山教育大學［3 名，TOPIK 2 級］、捷克茲林托馬斯巴塔大學［5 名，CEFR B2，保證提供低廉宿舍］，以及大陸華東師範大學、蘭州大學、華中師範大學、西南大學、東北師範大學、中央民族大學、鄭州大學等 7 所 985/211 重點名校）及 44 所正式締約姊妹校。（3）最高 30 萬元出國進修獎助學金與教育部學海計畫：涵蓋校內《學生出國進修獎助學金》（攻讀雙聯學位或交換生每人每年最高補助 NT\$300,000、短期修讀學分最高 NT\$80,000、短期語言進修最高 NT\$20,000；學士班須各學期班排前 50% 且具 CEFR B1 外語證明，碩博士班須系所推薦且具 CEFR B2 外語證明）、教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》及 12 所合作大學共 58 篇歷屆學長姐交換、雙聯與海外實習心得報告。',
    academicScoreMinimum: 70.0,
    colleges: ['人文學院', '師範學院', '理工學院', '跨領域學位學程'],
    aliases: ['nttu', '國立臺東大學', '國立台東大學', '臺東大學', '台東大學', '東大', 'NTTU', 'National Taitung University'],
  ),
  SupportedUniversity(
    id: 'asia',
    schoolName: '亞洲大學',
    shortName: '亞大',
    englishName: 'Asia University',
    officialUrl: 'https://oia.asia.edu.tw/p/412-1008-258.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 106,
    coverageNote: '完整支援：已整合亞洲大學國際事務處（OIA）《2026–2027 出國交換學生甄選簡章與學校一覽表（Fact Sheet）》、《全球合作姊妹校名錄（29 國 106 校）》、《亞洲大學學生出國交換生實施辦法》、《亞洲大學與國外大學辦理雙聯學制實施辦法》、《亞洲大學雙聯學位獎助學金辦法》、《亞洲大學 318 國際交流亮點計畫補助要點》、《亞洲大學學海計畫-選送優秀學生出國研修助學金審查要點》、《學生出國期間有關學業及學籍處理要點》、《學生抵免學分要點》及《出國交換暨學海計畫學生心得報告（12 校 14 篇）》官方資料：（1）校內甄選時程與資格門檻：每學期定期公告學期交換甄選（如 2027 春季班於 2026/10/19 截止收件、2026 秋季班於 2026/02/26 截止收件），限本校具中華民國國籍且修業滿一學期以上之全職在學學生（不含在職專班、延修生及休學生），在校學業總平均須達 75 分以上或名列全系（所）前 50%、操行成績 80 分以上，並具備目標姊妹校要求之外語檢定證明（英語組 TOEFL iBT 60–90 / IELTS 5.5–6.5 / TOEIC 550–800、日語組 JLPT N2–N4、韓語組 TOPIK 2–3 級）。（2）全球 29 國 106 所合作姊妹校與 9 校歐美亞跨國雙聯學位：完整收錄 40 所當期開放申請之學期交換與雙聯學位重點盟校（含加拿大維多利亞大學 UVic 3+1+1、美國北伊利諾大學 NIU 雙聯、美國蒙clair州立大學、瑞士 BHMS 飯店與商業管理學院雙聯、法國蒙彼利埃商學院 MBS 雙聯、英國西蘇格蘭大學 UWS 雙聯、捷克馬薩里克大學與奧斯特拉瓦大學、波蘭華沙經濟大學 SGH、義大利天主教聖心大學、日本近畿大學、日本亞細亞大學、日本關西國際大學、韓國成均館大學 SKKU、韓國慶熙大學、韓國外國語大學 HUFS、新加坡南洋理工大學 NTU、馬來西亞拉曼大學 UTAR 等）及 66 所正式締約姊妹校。（3）多元出國獎助學金與經驗傳承：涵蓋《亞大 318 國際交流亮點計畫》（依地區與天數定額補助機票與生活費）、《雙聯學位獎助學金》（每名最高補助 NT\$200,000）、教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》及 12 所歐美日韓新馬姊妹校共 14 篇歷屆學長姐研修心得。',
    academicScoreMinimum: 75.0,
    colleges: ['醫學暨健康學院', '資訊電機學院', '管理學院', '人文社會學院', '創意設計學院', '護理學院', '國際學院'],
    aliases: ['asia', '亞洲大學', '亞大', '臺中健康暨管理學院', '台中健康暨管理學院', 'ASIA', 'Asia University', 'Asia University Taiwan', 'Asia University, Taiwan'],
  ),
  SupportedUniversity(
    id: 'ttu',
    schoolName: '大同大學',
    shortName: '大同',
    englishName: 'Tatung University',
    officialUrl: 'https://oia.ttu.edu.tw/',
    supportLevel: 'full',
    partnerCount: 104,
    coverageNote: '完整支援：已整合大同大學國際暨兩岸事務處《2027 春季／2026 秋季／2026 春季／2025 秋季赴外交換及雙聯學位甄選公告》、《115 年度教育部學海飛颺與學海惜珠簡章及候補申請公告》、《全球與兩岸締約姊妹校名錄（104校）》、《交換學生計畫實施辦法（rid=1049）》、《與境外大學校院辦理雙聯學制實施辦法（rid=232）》、《學生出國期間有關學業及學籍處理要點（rid=225）》、《學生抵免學分辦法（rid=224）》、《校友捐助國際交流專案獎助學金辦法（rid=1124）》、《鼓勵學生出國交換研修助學金辦法（rid=1045）》、《學生暑期赴境外語言學習助學金辦法（rid=1129）》及《人在他鄉大同人（痞客邦官方交換網誌 28 校 146 篇）》官方資料：（1）兩階段校內甄選、量化評分與至多 2 志願規定：每學期分第一階段与第二階段收件（秋季班約 2 月下旬／3 月上旬 16:00 截止；春季班約 9 月上旬／10 月中旬 16:00 截止），每人每階段至多選填 2 個志願；申請人須為本校正式學籍在學學生（不含在職專班），實際出國時須在大同大學就讀滿一學年以上（即大二以上、碩士班或博士班），歷年學業總平均達 GPA 3.0（百分制約 75 分）以上（英國倫敦布魯內爾大學 Brunel 1+1／4+1 雙聯達 70 分以上即可）；校內甄選採量化審查「在校成績 40% + 語文能力 40% + 讀書計畫 20%」，總分達 70 分以上始得推薦，第一階段獲推薦者不得放棄並改申請第二階段，簽署家長同意書及本人聲明書後無故放棄者兩年內不得再申請；交換期間須維持大同在學註冊並繳交全額學雜費（免繳接待校學費）。（2）全球 20 國／地區 104 所合作姊妹校與英美德法澳日 9 校跨國雙聯學位：完整收錄 53 所常態開放申請之交換與雙聯合作校（含日本京都工藝纖維大學、千葉大學、東京都市大學、芝浦工業大學、東京電機大學、長岡造形大學、札幌市立大學、東北工業大學、岡山大學、熊本大學、琉球大學、縣立廣島大學、同志社大學、專修大學等 22 所日本名校，德國斯圖加特應用科技大學 HFT Stuttgart、奧斯納布魯克應用科技大學、德根多夫應用科技大學 DIT、巴登符騰堡雙元制大學 DHBW、卡爾斯魯厄應用科技大學 HKA，芬蘭東南芬蘭應用科技大學 Xamk，法國貢比涅科技大學 UTC，韓國仁川大學，泰國法政大學 SIIT，美國匹茲堡州立大學 PSU 及大陸 12 所重點高校），以及美國愛荷華州立大學 ISU（1+1／3.5+1.5）、韋恩州立大學 WSU（1+1 碩士，每名大同生享 USD 3,000/學期獎學金）、拉瑪大學 Lamar（1+1 免 GRE）、英國密德薩斯大學 Middlesex（3+1／1+1／3+1.5）、倫敦布魯內爾大學 Brunel（1+1／4+1 數位設計與 AI，每年 10 名享 15% 學費減免）、德國 HFT Stuttgart（1+1 雙碩士）、法國 ESIEE-Amiens / UniLaSalle（1+1 雙碩士）、澳洲紐卡索大學（1+1 雙碩士）與日本千葉大學雙聯學位。（3）豐厚校友捐助獎助與返國心得：涵蓋教育部《學海飛颺／惜珠》（申請學海自動聯審《大同大學校友捐助國際交流獎助學金》）、電機系 66 級校友捐助《鼓勵學生出國交換研修助學金》（最高 NT\$100,000）、《暑期赴境外語言學習助學金》（最高 NT\$50,000），並收錄《人在他鄉大同人》官方網誌 28 所合作大學共 146 篇歷屆學長姐交換與雙聯心得報告。',
    academicScoreMinimum: 75.0,
    colleges: ['工程學院', '電機資訊學院', '經營學院', '設計學院', '國際學院'],
    aliases: ['ttu', '大同大學', '大同', '私立大同大學', '大同工學院', 'TTU', 'Tatung University', 'Tatung'],
  ),
  SupportedUniversity(
    id: 'tcu',
    schoolName: '慈濟大學',
    shortName: '慈大',
    englishName: 'Tzu Chi University',
    officialUrl: 'https://oga.tcu.edu.tw/outbound-exchange-student-program/',
    supportLevel: 'full',
    partnerCount: 50,
    coverageNote: '完整支援：已整合慈濟大學全球事務處（Office of Global Affairs, OGA，原國際暨兩岸事務處 OIA）交流組《出國交換學生計畫（outbound-exchange-student-program）》、《跨國雙聯與三聯學位計畫（dual-double-degree-program / a-double-degree）》、《大陸地區學生交換研習申請資訊》、《全球合作姊妹校名錄（sister-schools-3，50校）》、《與境外學校辦理雙聯學制實施辦法（1070508教育部備查版）》、《英語主要檢測參考對照表暨 CEFR B1（含）級以上或同等語言能力對照表》、《學生海外交流補助辦法》、《教育部學海系列獎助計畫》及《經驗分享與學生故事專區（15校16篇）》官方資料：（1）校內甄選時程、在學資格與成績門檻：每年 11 月公告次學年度出國交換生甄選簡章、12 月中旬起更新姊妹校名額至 12 月 31 日截止收件，限本校在學全職學位生（大學部二年級（含）以上、碩士班、博士班在學學生；大一新生於大一下學期得申請大二赴外交換；不含在職專班、延畢生及休學生），歷年學業成績排名須達全班前 50%（約折合平均 75 分或 GPA 2.5 以上；美國加州州立大學海峽群島分校明訂 GPA 2.5+）且操行優良，外語能力須符合《CEFR B1（含）級以上語言能力對照表》（TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0）及各接待校門檻。（2）全球 17 國／地區 50 所合作姊妹校與跨洲際三聯／英美泰雙聯學位：完整收錄 25 所當期開放申請之國際交換、大陸交換與雙聯／三聯合作校及 25 所正式締約代表性姊妹校，涵蓋德墨臺「跨洲際全球研究三聯碩士學位（TRIM，與德國卡爾斯魯厄應用科技大學 HKA 及墨西哥蒙特雷大學 UDEM 共同授位）」、英國倫敦密德薩斯大學 3+1 雙學士（限公衛、生科、分遺、外語、國管學程）、美國安德魯斯大學 1+1 MBA 雙碩士（全校各科系適用）、泰國瑪希敦大學與納黎萱大學醫學科學研究所博士雙聯，以及日本京都佛教大學、奈良天理大學、熊本尚絅大學（限女生）與大陸蘭州大學「學雜費及住宿費雙全免」交換專案。（3）三大獎助體系與學長姐心得：涵蓋教育部《學海飛颺／惜珠／築夢／新南向學海築夢》（第一階段每年 2–3 月、第二階段每年 8 月）、校內《學生海外交流活動補助》（暑期 3/1–3/15、5/1–5/15；寒假 12/1–12/15；學期中出發前 1 個月；依計畫完整性 40%、含服務學習時數之學習成效 40%、交流風險性 20% 評定）及 15 所合作大學共 16 篇歷屆學長姐交換與雙聯心得報告。',
    academicScoreMinimum: 75.0,
    colleges: ['醫學院', '護理學院', '工程科技學院', '人文傳播暨社會科學院', '智慧永續管理學院', '國際學院'],
    aliases: ['tcu', '慈濟大學', '慈大', '慈濟', '慈濟醫學院', '慈濟技術學院', '慈濟科技大學', 'TCU', 'Tzu Chi University', 'Tzu Chi University, Taiwan', 'Tzu-Chi University'],
  ),
  SupportedUniversity(
    id: 'mcut',
    schoolName: '明志科技大學',
    shortName: '明志',
    englishName: 'Ming Chi University of Technology',
    officialUrl: 'https://oia.mcut.edu.tw/?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 130,
    coverageNote: '完整支援：已整合明志科技大學國際事務處全球交流組（OIA）《2026–2027 學年度海外交換學習計畫甄選簡章（59所當期開放校）》、《跨國碩士雙聯學位甄選公告（美國辛辛那提大學 UC、北伊利諾大學 NIU、舊金山州立大學 SFSU、西班牙巴塞隆納高等設計學院 ELISAVA、法國 ESIEE Paris、希臘雅典 ALBA 商學院）》、《全球暨兩岸合作姊妹校名錄（130校）》、《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008，114.08.12修訂）》、《大學部海外交換學習課程實施辦法（A2Q1060001，大三工讀實習海外交換抵免）》、《學生出國短期研習實施及補助辦法（A2Q1030010）》、《各類語言檢定證照等級對照表（CEFR A1–C2）》及《出國交換暨雙聯學位心得報告專區（13校48篇）》官方資料：（1）校內甄選時程、GPA 3.0 門檻與大三工讀實習抵免制度：交換生每年 1 月公告、2 月初截止（2026–2027 學年於 2026/02/06 17:00 截止；春季班補充收件依辦法第 5 條於 10/31 前），碩士雙聯分春季班（9/24 17:00 截止）與秋季班（2/6 17:00 截止）兩梯次；限日間部大二、大三及碩博士班在學學生（不含大一及在職專班；僅大二升大三擬以海外交換抵免大三全學年「工讀實務實習」課程［上學期 16 學分、下學期 18 學分］者可申請一學年交換，每學期至少修讀 6 學分［歐洲 2 ECTS = 1 學分］並每三個月繳交四階段學習報告，其餘以一學期為原則），歷年 GPA 須達 3.0（百分制約 75 分；NIU、ELISAVA、ESIEE、ALBA 雙聯為 GPA 2.75）以上、操行平均 80 分以上無記過，且語言達 CEFR B1（TOEIC 550 / TOEFL iBT 42 / IELTS 4.0 / JLPT N3 / TOPIK 3級）或雙聯指定門檻（iBT 72–100 / IELTS 5.5–6.5），每人限填 1 所志願校。（2）全球 21 國／地區 130 所合作姊妹校與 12 所雙聯合作校：完整收錄 59 所當期開放申請之歐美日韓東南亞及大陸交換與雙聯合作校及 71 所正式締約姊妹校。（3）雙聯最高 24 萬／交換最高 16 萬元校內補助與學海計畫：涵蓋校內雙聯補助（非亞洲區一學年最高 NT\$240,000、亞洲區最高 NT\$150,000；美國 UC 另享校友「鹿江基金會」專屬獎學金）、校內交換補助（非亞洲區一學期最高 NT\$80,000／一學年最高 NT\$160,000、亞洲區一學期最高 NT\$50,000／一學年最高 NT\$100,000）、短期研習補助（最高 NT\$47,000）、教育部《學海飛颺／惜珠／築夢》（每人 5 萬至 30 萬元）及 13 校 48 篇歷屆學長姐心得報告。',
    academicScoreMinimum: 75.0,
    colleges: ['工程學院', '環境資源學院', '管理暨設計學院'],
    aliases: ['mcut', '明志科技大學', '明志科大', '明志工專', '明志', 'MCUT', 'Ming Chi University of Technology'],
  ),
  SupportedUniversity(
    id: 'cyut',
    schoolName: '朝陽科技大學',
    shortName: '朝陽',
    englishName: 'Chaoyang University of Technology',
    officialUrl: 'https://icsc.cyut.edu.tw/',
    supportLevel: 'full',
    partnerCount: 70,
    coverageNote: '完整支援：已整合朝陽科技大學國際事務處（OIA，原國際暨兩岸合作處，下設學術交流組、學生服務組、國際專修部及國際學生就業輔導中心）《115學年度赴亞洲（日韓）及歐美墨姊妹校交換學生甄選簡章》、《跨國雙聯學位甄選簡章（英美澳日德 12 校）》、《選送優秀學生寒暑假赴海外姐妹校英語研習營甄選簡章（菲律賓拉普拉普宿霧國際大學 LCIC）》、《與境外大學辦理交換學生實施要點》、《學生赴國外姐妹校交換學習補助要點》、《跨國雙聯學位獎助學金實施要點》、《千人海外體驗計畫補助要點》、《辦理學生抵免學分要點》及《全球 40 國姊妹校名錄與海外學習成果專區》官方資料：（1）校內甄選時程、在學資格與最低修課規範：每學期分兩梯次（秋季班於當年 3 月中旬截止，如 115-1 於 2026/03/13 17:00 截止；春季班於前一年 10 月中旬截止，如 115-2 於 2026/10/16 17:00 截止；寒暑假菲律賓英語研習營分別於 11/09 及 12/14 17:00 截止）受理報名，交換生限日間部四技（修滿 1–2 年）、二技及碩博士班（修滿 1 年）在學學生（不含延修生），歷年學業總平均達 70 分（GPA 2.7）或班排前 50%、操行達 80 分以上，交換期間每學期至少應修習 2 門（或 6 學分）以上科目，錄取後繳交保證金 NT\$5,000（返國完成心得報告無息退還）。（2）70 所全球與兩岸合作姊妹校（含 34 所當期開放申請合作校）：涵蓋日本芝浦工業大學（三明治交換與研究交流）、岩手縣立大學、會津大學、長野大學、公立函館未來大學；韓國東義大學（免學費且免收校內宿舍住宿費！）、三育大學、水原大學、龍仁大學、國立順天大學、忠清大學；歐洲捷克馬薩里克大學、丹麥維亞大學（ETEN 歐洲教師教育網絡重點夥伴）、丹麥哥本哈根應用科學大學（UCC）、德國東巴伐利亞雷根斯堡應用科學大學（OTH Regensburg）、德國烏茲堡應用科學大學（THWS）、德國帕紹大學、荷蘭格羅寧根漢斯應用科學大學（Hanze）、海牙應用科學大學（THUAS）、漢恩應用科學大學（HAN）、比利時天主教林堡大學（UCLL）、西班牙蒙德拉貢大學、維克大學、俄羅斯秋明大學；墨西哥蒙特雷科技大學；以及英國密德薩斯大學、德蒙福特大學、桑德蘭大學、西蘇格蘭大學、澳洲南十字星大學、西雪梨大學、美國明州西南州立大學、漢弗萊斯大學等 3+1／2+2 雙學士與 1+1／1.5+1 雙碩士名校。（3）四大海外學習補助與教育部學海計畫：通過校內交換甄選即補助經濟艙來回機票（亞洲上限 NT\$18,000–20,000、歐美上限 NT\$45,000）、雙聯學位機票與獎助金（NT\$15,000–50,000）、菲律賓 LCIC 英語研習營（補助 50% 研習費上限 NT\$30,000＋機票上限 NT\$10,000）及教育部《學海飛颺》（每人 6–24 萬元）、《學海惜珠》、《學海築夢／新南向學海築夢》，並收錄 15 校 19 篇官方錄取與海外研修實錄。',
    academicScoreMinimum: 70.0,
    colleges: ['管理學院', '理工學院', '設計學院', '人文暨社會學院', '資訊學院', '航空學院'],
    aliases: ['cyut', '朝陽科技大學', '朝陽科大', '朝陽', 'CYUT', 'Chaoyang University of Technology'],
  ),
];

SupportedUniversity? tryResolveSupportedUniversity(
  String? value, [
  Iterable<SupportedUniversity> candidates = defaultSupportedUniversities,
]) {
  final raw = value?.trim() ?? '';
  if (raw.isEmpty) return null;
  final normalized = raw.toLowerCase();
  for (final item in candidates) {
    if (item.id.toLowerCase() == normalized ||
        item.schoolName.toLowerCase() == normalized ||
        item.shortName.toLowerCase() == normalized ||
        item.englishName.toLowerCase() == normalized ||
        item.aliases.any((alias) => alias.toLowerCase() == normalized)) {
      return item;
    }
  }
  for (final item in defaultSupportedUniversities) {
    if (item.id.toLowerCase() == normalized ||
        item.schoolName.toLowerCase() == normalized ||
        item.shortName.toLowerCase() == normalized ||
        item.englishName.toLowerCase() == normalized ||
        item.aliases.any((alias) => alias.toLowerCase() == normalized)) {
      return item;
    }
  }
  return null;
}

SupportedUniversity resolveSupportedUniversity(
  String? value, [
  Iterable<SupportedUniversity> candidates = defaultSupportedUniversities,
]) =>
    tryResolveSupportedUniversity(value, candidates) ??
    (candidates.isNotEmpty
        ? candidates.first
        : defaultSupportedUniversities.first);

class AuthProviderStatus {
  const AuthProviderStatus({
    required this.provider,
    required this.enabled,
    required this.label,
  });

  factory AuthProviderStatus.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AuthProviderStatus(
      provider: textValue(json['provider']),
      enabled: json['enabled'] == true,
      label: textValue(json['label']),
    );
  }

  final String provider;
  final bool enabled;
  final String label;
}

class StudentVerificationResult {
  const StudentVerificationResult({
    required this.verificationToken,
    required this.schoolName,
    required this.checks,
    required this.expiresAt,
    required this.imagesRetained,
  });

  factory StudentVerificationResult.fromJson(dynamic value) {
    final json = jsonMap(value);
    return StudentVerificationResult(
      verificationToken: textValue(json['verification_token']),
      schoolName: textValue(json['school_name']),
      checks: stringList(json['checks']),
      expiresAt: textValue(json['expires_at']),
      imagesRetained: json['images_retained'] == true,
    );
  }

  final String verificationToken;
  final String schoolName;
  final List<String> checks;
  final String expiresAt;
  final bool imagesRetained;
}


enum ProductAccessTier {
  guest('guest'),
  free('free'),
  subscription('subscription'),
  communityModerator('community_moderator'),
  platformAdmin('platform_admin'),
  developer('developer');

  const ProductAccessTier(this.apiValue);
  final String apiValue;

  static ProductAccessTier parse(dynamic value) =>
      ProductAccessTier.values.firstWhere(
        (tier) => tier.apiValue == value?.toString(),
        orElse: () => ProductAccessTier.guest,
      );
}

class AccountProfile {
  const AccountProfile({
    required this.id,
    required this.email,
    required this.displayName,
    required this.avatarUrl,
    required this.homeUniversity,
    required this.targetCountries,
    required this.applicationStage,
    required this.schoolEmailVerified,
    required this.studentStatusVerified,
    required this.verifiedUniversity,
    required this.studentVerifiedAt,
    required this.providers,
    required this.followedBoards,
    this.productTier = ProductAccessTier.free,
    this.emailVerified = false,
  });

  factory AccountProfile.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AccountProfile(
      id: textValue(json['id']),
      email: textValue(json['email']),
      displayName: textValue(json['display_name'], '交換學生'),
      avatarUrl: textValue(json['avatar_url']),
      homeUniversity: textValue(json['home_university'], '未定大學'),
      targetCountries: stringList(json['target_countries']),
      applicationStage: textValue(json['application_stage'], 'exploring'),
      schoolEmailVerified: json['school_email_verified'] == true,
      studentStatusVerified: json['student_status_verified'] == true,
      verifiedUniversity: textValue(json['verified_university']),
      studentVerifiedAt: textValue(json['student_verified_at']),
      providers: stringList(json['providers']),
      followedBoards: stringList(json['followed_boards']),
      productTier: ProductAccessTier.parse(json['product_tier'] ?? 'free'),
      emailVerified: json['email_verified'] == true,
    );
  }

  final String id;
  final String email;
  final String displayName;
  final String avatarUrl;
  final String homeUniversity;
  final List<String> targetCountries;
  final String applicationStage;
  final bool schoolEmailVerified;
  final bool studentStatusVerified;
  final String verifiedUniversity;
  final String studentVerifiedAt;
  final List<String> providers;
  final List<String> followedBoards;
  final ProductAccessTier productTier;
  final bool emailVerified;
}

class AccountSession {
  const AccountSession({
    required this.accessToken,
    required this.expiresAt,
    required this.profile,
  });

  factory AccountSession.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AccountSession(
      accessToken: textValue(json['access_token']),
      expiresAt: textValue(json['expires_at']),
      profile: AccountProfile.fromJson(json['profile']),
    );
  }

  final String accessToken;
  final String expiresAt;
  final AccountProfile profile;
}

class SourceReference {
  const SourceReference({
    required this.title,
    required this.sourceUrl,
    this.category = '',
  });

  factory SourceReference.fromJson(dynamic value) {
    final json = jsonMap(value);
    return SourceReference(
      title: textValue(json['title'], '官方來源'),
      sourceUrl: textValue(json['source_url']),
      category: textValue(json['category']),
    );
  }

  final String title;
  final String sourceUrl;
  final String category;
}

class StudentInfoItem {
  const StudentInfoItem({
    required this.title,
    required this.details,
    this.source,
  });

  factory StudentInfoItem.fromJson(dynamic value) {
    final json = jsonMap(value);
    final source = json['source'];
    return StudentInfoItem(
      title: textValue(json['title']),
      details: stringList(json['details']),
      source: source == null ? null : SourceReference.fromJson(source),
    );
  }

  final String title;
  final List<String> details;
  final SourceReference? source;
}

class RuleExplanation {
  const RuleExplanation({
    required this.title,
    required this.summary,
    required this.keyPoints,
    required this.appliesTo,
    required this.source,
    required this.documentUrl,
    required this.fullTextExtracted,
  });

  factory RuleExplanation.fromJson(dynamic value) {
    final json = jsonMap(value);
    return RuleExplanation(
      title: textValue(json['title']),
      summary: textValue(json['summary']),
      keyPoints: stringList(json['key_points']),
      appliesTo: stringList(json['applies_to']),
      source: SourceReference.fromJson(json['source']),
      documentUrl: textValue(json['document_url']),
      fullTextExtracted: json['full_text_extracted'] == true,
    );
  }

  final String title;
  final String summary;
  final List<String> keyPoints;
  final List<String> appliesTo;
  final SourceReference source;
  final String documentUrl;
  final bool fullTextExtracted;
}

class PartnerStudentSummary {
  const PartnerStudentSummary({
    required this.studyPeriod,
    required this.applicationDeadline,
    required this.eligibilityPoints,
    required this.applicationSteps,
    required this.tuitionPoints,
    required this.translatedFromEnglish,
  });

  const PartnerStudentSummary.empty()
    : studyPeriod = '',
      applicationDeadline = '',
      eligibilityPoints = const [],
      applicationSteps = const [],
      tuitionPoints = const [],
      translatedFromEnglish = false;

  factory PartnerStudentSummary.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PartnerStudentSummary(
      studyPeriod: textValue(json['study_period']),
      applicationDeadline: textValue(json['application_deadline']),
      eligibilityPoints: stringList(json['eligibility_points']),
      applicationSteps: stringList(json['application_steps']),
      tuitionPoints: stringList(json['tuition_points']),
      translatedFromEnglish: json['translated_from_english'] == true,
    );
  }

  final String studyPeriod;
  final String applicationDeadline;
  final List<String> eligibilityPoints;
  final List<String> applicationSteps;
  final List<String> tuitionPoints;
  final bool translatedFromEnglish;
}

class PartnerLanguageCondition {
  const PartnerLanguageCondition({
    required this.test,
    this.testVariant = '',
    this.minimumScore,
    this.requirementLevel = 'required',
    this.degreeLevels = const [],
    this.teachingLanguage = '',
  });

  factory PartnerLanguageCondition.fromJson(dynamic value) {
    final json = jsonMap(value);
    final rawScore = json['minimum_score'];
    final score = rawScore is num
        ? rawScore.toDouble()
        : double.tryParse(textValue(rawScore));
    return PartnerLanguageCondition(
      test: textValue(json['test']),
      testVariant: textValue(json['test_variant']),
      minimumScore: score,
      requirementLevel: textValue(json['requirement_level'], 'required'),
      degreeLevels: stringList(json['degree_levels']),
      teachingLanguage: textValue(json['teaching_language']),
    );
  }

  final String test;
  final String testVariant;
  final double? minimumScore;
  final String requirementLevel;
  final List<String> degreeLevels;
  final String teachingLanguage;

  String get displayLabel {
    final formattedTest = switch (test.trim().toLowerCase()) {
      'toeic' => 'TOEIC',
      'toefl' => 'TOEFL',
      'toefl_ibt' => 'TOEFL iBT',
      'toefl_itp' => 'TOEFL ITP',
      'ielts' => 'IELTS',
      'jlpt' => 'JLPT',
      'gept' => 'GEPT',
      'cefr' => 'CEFR',
      'delf' => 'DELF',
      'topik' => 'TOPIK',
      'testdaf' => 'TestDaF',
      _ => test.trim(),
    };
    final name = [formattedTest, testVariant.trim()]
        .where((s) => s.isNotEmpty)
        .join(' ');
    if (minimumScore == null) {
      return name.isEmpty ? '依官方規定' : name;
    }
    final scoreStr = minimumScore == minimumScore!.roundToDouble()
        ? minimumScore!.toInt().toString()
        : minimumScore!.toStringAsFixed(1);
    return '$name $scoreStr'.trim();
  }
}

class PartnerUniversity {
  const PartnerUniversity({
    required this.schoolName,
    required this.country,
    required this.programType,
    required this.colleges,
    required this.degreeLevels,
    required this.website,
    required this.studyPeriod,
    required this.quota,
    required this.eligibility,
    required this.applicationDeadline,
    required this.applicationInfo,
    required this.tuitionInfo,
    required this.rankingInfo,
    required this.sourceUrl,
    required this.imageUrl,
    required this.imageSourceUrl,
    required this.imagePageUrl,
    required this.imageStatus,
    required this.studentSummaryZh,
    this.availabilityStatus = 'open',
    this.availabilityNote = '',
    this.quotaStatus = '',
    this.applicationWindowStatus = '',
    this.languageRequirement = '',
    this.languageConditions = const [],
  });

  factory PartnerUniversity.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PartnerUniversity(
      schoolName: textValue(json['school_name'], '合作學校'),
      country: textValue(json['country'], '國家待確認'),
      programType: textValue(json['program_type'], '交換學生'),
      colleges: textValue(json['colleges']),
      degreeLevels: textValue(json['degree_levels']),
      website: textValue(json['website']),
      studyPeriod: textValue(json['study_period']),
      quota: textValue(json['quota']),
      eligibility: textValue(json['eligibility']),
      applicationDeadline: textValue(json['application_deadline']),
      applicationInfo: textValue(json['application_info']),
      tuitionInfo: textValue(json['tuition_info']),
      rankingInfo: textValue(json['ranking_info']),
      sourceUrl: textValue(json['source_url']),
      imageUrl: textValue(
        json['image_url'] ?? json['photo_url'] ?? json['og_image_url'],
      ),
      imageSourceUrl: textValue(json['image_source_url']),
      imagePageUrl: textValue(json['image_page_url']),
      imageStatus: textValue(json['image_status'], 'missing'),
      studentSummaryZh: PartnerStudentSummary.fromJson(
        json['student_summary_zh'],
      ),
      availabilityStatus: textValue(json['availability_status'], 'open'),
      availabilityNote: textValue(json['availability_note']),
      quotaStatus: textValue(json['quota_status']),
      applicationWindowStatus: textValue(json['application_window_status']),
      languageRequirement: textValue(json['language_requirement']),
      languageConditions: jsonMapList(
        json['language_conditions'],
      ).map(PartnerLanguageCondition.fromJson).toList(),
    );
  }

  final String schoolName;
  final String country;
  final String programType;
  final String colleges;
  final String degreeLevels;
  final String website;
  final String studyPeriod;
  final String quota;
  final String eligibility;
  final String applicationDeadline;
  final String applicationInfo;
  final String tuitionInfo;
  final String rankingInfo;
  final String sourceUrl;
  final String imageUrl;
  final String imageSourceUrl;
  final String imagePageUrl;
  final String imageStatus;
  final PartnerStudentSummary studentSummaryZh;
  final String availabilityStatus;
  final String availabilityNote;
  final String quotaStatus;
  final String applicationWindowStatus;
  final String languageRequirement;
  final List<PartnerLanguageCondition> languageConditions;

  bool get isOpenThisCycle => availabilityStatus == 'open';

  bool get isReferenceOnly => const {
    'agreement_only',
    'reference_only',
    'departmental_reference',
  }.contains(availabilityStatus);

  String get availabilityLabel => switch (availabilityStatus) {
    'open' => '本期開放',
    'agreement_only' ||
    'reference_only' ||
    'departmental_reference' => '合作備查',
    'quota_unconfirmed' || 'needs_confirmation' => '名額未定',
    'zero_quota' || 'not_open' || 'closed' => '暫不開放',
    'fee_paying' => '自費研修',
    _ => '待確認',
  };

  String get displayQuota {
    if (quota.trim().isNotEmpty) return quota.trim();
    return switch (quotaStatus) {
      'zero' => '0 名',
      'reference_only' => '歷年參考',
      'fee_paying' => '自費',
      'not_published' => '未公告',
      _ => isReferenceOnly ? '僅列協議' : '依公告',
    };
  }

  String get displayStudyPeriod => studentSummaryZh.studyPeriod.isNotEmpty
      ? studentSummaryZh.studyPeriod
      : studyPeriod;

  String get displayApplicationDeadline =>
      studentSummaryZh.applicationDeadline.isNotEmpty
      ? studentSummaryZh.applicationDeadline
      : applicationDeadline;

  String get displayDeadlineSummary {
    final text = displayApplicationDeadline.trim();
    if (text.isNotEmpty) return text;
    return switch (applicationWindowStatus) {
      'closed' => '本期已截止',
      'upcoming' => '即將開放',
      _ => isReferenceOnly ? '無當期梯次' : '依校內公告',
    };
  }

  String get displayScopeAndLanguage {
    if (languageConditions.isNotEmpty) {
      final top = languageConditions
          .map((item) => item.displayLabel)
          .where((item) => item.isNotEmpty)
          .take(2)
          .join(' / ');
      if (top.isNotEmpty) return top;
    }
    if (languageRequirement.trim().isNotEmpty) {
      return languageRequirement.trim();
    }
    final scope = [
      degreeLevels.trim(),
      colleges.trim(),
    ].where((s) => s.isNotEmpty).join(' · ');
    if (scope.isNotEmpty) return scope;
    if (eligibilityPoints.isNotEmpty) return eligibilityPoints.first;
    return '依官方簡章';
  }

  List<String> get eligibilityPoints =>
      studentSummaryZh.eligibilityPoints.isNotEmpty
      ? studentSummaryZh.eligibilityPoints
      : [if (eligibility.isNotEmpty) eligibility];

  List<String> get applicationSteps =>
      studentSummaryZh.applicationSteps.isNotEmpty
      ? studentSummaryZh.applicationSteps
      : [if (applicationInfo.isNotEmpty) applicationInfo];

  List<String> get tuitionPoints => studentSummaryZh.tuitionPoints.isNotEmpty
      ? studentSummaryZh.tuitionPoints
      : [if (tuitionInfo.isNotEmpty) tuitionInfo];

  String get mobileListSummary => [
    programType,
    colleges,
    degreeLevels,
  ].where((item) => item.trim().isNotEmpty).join(' · ');

  PartnerUniversity withVisual(SchoolVisual visual, String imageUrl) {
    return PartnerUniversity(
      schoolName: schoolName,
      country: country,
      programType: programType,
      colleges: colleges,
      degreeLevels: degreeLevels,
      website: website,
      studyPeriod: studyPeriod,
      quota: quota,
      eligibility: eligibility,
      applicationDeadline: applicationDeadline,
      applicationInfo: applicationInfo,
      tuitionInfo: tuitionInfo,
      rankingInfo: rankingInfo,
      sourceUrl: sourceUrl,
      imageUrl: imageUrl,
      imageSourceUrl: visual.imageSourceUrl,
      imagePageUrl: visual.officialPageUrl,
      imageStatus: visual.status,
      studentSummaryZh: studentSummaryZh,
      availabilityStatus: availabilityStatus,
      availabilityNote: availabilityNote,
      quotaStatus: quotaStatus,
      applicationWindowStatus: applicationWindowStatus,
      languageRequirement: languageRequirement,
      languageConditions: languageConditions,
    );
  }

  String get searchableText => [
    schoolName,
    country,
    programType,
    colleges,
    degreeLevels,
    availabilityLabel,
    languageRequirement,
    ...languageConditions.map((item) => item.displayLabel),
    eligibility,
    displayApplicationDeadline,
    ...eligibilityPoints,
  ].join(' ').toLowerCase();
}

class SchoolVisual {
  const SchoolVisual({
    required this.schoolName,
    required this.officialPageUrl,
    required this.imageSourceUrl,
    required this.localPath,
    required this.status,
  });

  factory SchoolVisual.fromJson(dynamic value) {
    final json = jsonMap(value);
    return SchoolVisual(
      schoolName: textValue(json['school_name']),
      officialPageUrl: textValue(json['official_page_url']),
      imageSourceUrl: textValue(json['image_source_url']),
      localPath: textValue(json['local_path']),
      status: textValue(json['status'], 'missing'),
    );
  }

  final String schoolName;
  final String officialPageUrl;
  final String imageSourceUrl;
  final String localPath;
  final String status;
}

class StudentDashboard {
  const StudentDashboard({
    required this.schoolName,
    required this.lastChecked,
    required this.applicationPeriods,
    required this.programOverview,
    required this.eligibility,
    required this.languageRequirements,
    required this.requiredDocuments,
    required this.scholarshipInfo,
    required this.ruleExplanations,
    required this.partnerUniversities,
    required this.sources,
    this.shortName = '',
    this.supportLevel = 'live',
    this.coverageNote = '',
    this.officialNotice = '',
  });

  factory StudentDashboard.fromJson(dynamic value) {
    final json = jsonMap(value);
    List<StudentInfoItem> items(String key) =>
        jsonMapList(json[key]).map(StudentInfoItem.fromJson).toList();
    final rules = [
      ...jsonMapList(json['rule_explanations']),
      ...jsonMapList(json['document_explanations']),
    ];
    final schoolName = textValue(json['school_name'], defaultHomeUniversity);
    final resolved = resolveSupportedUniversity(schoolName);
    return StudentDashboard(
      schoolName: schoolName,
      shortName: textValue(json['short_name'], resolved.shortName),
      supportLevel: textValue(json['support_level'], resolved.supportLevel),
      coverageNote: textValue(json['coverage_note'], resolved.coverageNote),
      officialNotice: textValue(json['official_notice']),
      lastChecked: textValue(json['last_checked']),
      applicationPeriods: items('application_periods'),
      programOverview: items('program_overview'),
      eligibility: items('eligibility'),
      languageRequirements: items('language_requirements'),
      requiredDocuments: items('required_documents'),
      scholarshipInfo: items('scholarship_info'),
      ruleExplanations: rules.map(RuleExplanation.fromJson).toList(),
      partnerUniversities: jsonMapList(
        json['partner_universities'],
      ).map(PartnerUniversity.fromJson).toList(),
      sources: jsonMapList(
        json['sources'],
      ).map(SourceReference.fromJson).toList(),
    );
  }

  final String schoolName;
  final String shortName;
  final String supportLevel;
  final String coverageNote;
  final String officialNotice;
  final String lastChecked;
  final List<StudentInfoItem> applicationPeriods;
  final List<StudentInfoItem> programOverview;
  final List<StudentInfoItem> eligibility;
  final List<StudentInfoItem> languageRequirements;
  final List<StudentInfoItem> requiredDocuments;
  final List<StudentInfoItem> scholarshipInfo;
  final List<RuleExplanation> ruleExplanations;
  final List<PartnerUniversity> partnerUniversities;
  final List<SourceReference> sources;

  StudentDashboard withSchoolVisuals(
    Map<String, SchoolVisual> visuals,
    String Function(String) resolveUrl,
  ) {
    return StudentDashboard(
      schoolName: schoolName,
      shortName: shortName,
      supportLevel: supportLevel,
      coverageNote: coverageNote,
      officialNotice: officialNotice,
      lastChecked: lastChecked,
      applicationPeriods: applicationPeriods,
      programOverview: programOverview,
      eligibility: eligibility,
      languageRequirements: languageRequirements,
      requiredDocuments: requiredDocuments,
      scholarshipInfo: scholarshipInfo,
      ruleExplanations: ruleExplanations,
      partnerUniversities: partnerUniversities.map((school) {
        final visual = visuals[school.schoolName];
        if (visual == null ||
            visual.status != 'verified' ||
            visual.localPath.isEmpty) {
          return school;
        }
        return school.withVisual(visual, resolveUrl(visual.localPath));
      }).toList(),
      sources: sources,
    );
  }
}

class DocumentCheckIssue {
  const DocumentCheckIssue({
    required this.severity,
    required this.code,
    required this.title,
    required this.detail,
  });

  factory DocumentCheckIssue.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DocumentCheckIssue(
      severity: textValue(json['severity'], 'info'),
      code: textValue(json['code']),
      title: textValue(json['title']),
      detail: textValue(json['detail']),
    );
  }

  final String severity;
  final String code;
  final String title;
  final String detail;
}

class DocumentCheckResult {
  const DocumentCheckResult({
    required this.fileName,
    required this.documentType,
    required this.summary,
    required this.pageCount,
    required this.characterCount,
    required this.wordCount,
    required this.checksPassed,
    required this.issues,
    required this.suggestions,
    required this.extractedPreview,
    required this.privacyNote,
  });

  factory DocumentCheckResult.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DocumentCheckResult(
      fileName: textValue(json['file_name']),
      documentType: textValue(json['document_type']),
      summary: textValue(json['summary']),
      pageCount: intValue(json['page_count'], 1),
      characterCount: intValue(json['character_count']),
      wordCount: intValue(json['word_count']),
      checksPassed: stringList(json['checks_passed']),
      issues: jsonMapList(
        json['issues'],
      ).map(DocumentCheckIssue.fromJson).toList(),
      suggestions: stringList(json['suggestions']),
      extractedPreview: textValue(json['extracted_preview']),
      privacyNote: textValue(json['privacy_note']),
    );
  }

  final String fileName;
  final String documentType;
  final String summary;
  final int pageCount;
  final int characterCount;
  final int wordCount;
  final List<String> checksPassed;
  final List<DocumentCheckIssue> issues;
  final List<String> suggestions;
  final String extractedPreview;
  final String privacyNote;
}

class DeadlineRecord {
  const DeadlineRecord({
    required this.title,
    required this.sourceUrl,
    required this.publishedAt,
    required this.category,
    required this.snippets,
  });

  factory DeadlineRecord.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DeadlineRecord(
      title: textValue(json['title'], '申請時程'),
      sourceUrl: textValue(json['source_url']),
      publishedAt: textValue(json['published_at']),
      category: textValue(json['category'], 'deadline'),
      snippets: stringList(json['snippets']),
    );
  }

  final String title;
  final String sourceUrl;
  final String publishedAt;
  final String category;
  final List<String> snippets;
}

class ApplicationStep {
  const ApplicationStep({
    required this.order,
    required this.phase,
    required this.title,
    required this.responsibleParty,
    required this.timing,
    required this.summary,
    required this.details,
    required this.requiredDocuments,
    required this.actionUrl,
    required this.sourceUrls,
    required this.needsConfirmation,
  });

  factory ApplicationStep.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationStep(
      order: json['order'] is int ? json['order'] as int : 0,
      phase: textValue(json['phase']),
      title: textValue(json['title']),
      responsibleParty: textValue(json['responsible_party']),
      timing: textValue(json['timing']),
      summary: textValue(json['summary']),
      details: stringList(json['details']),
      requiredDocuments: stringList(json['required_documents']),
      actionUrl: textValue(json['action_url']),
      sourceUrls: stringList(json['source_urls']),
      needsConfirmation: json['needs_confirmation'] == true,
    );
  }

  final int order;
  final String phase;
  final String title;
  final String responsibleParty;
  final String timing;
  final String summary;
  final List<String> details;
  final List<String> requiredDocuments;
  final String actionUrl;
  final List<String> sourceUrls;
  final bool needsConfirmation;
}

class ApplicationWorkflow {
  const ApplicationWorkflow({
    required this.schoolName,
    required this.country,
    required this.programType,
    required this.steps,
    required this.lastChecked,
    required this.coverageStatus,
    required this.coverageNote,
    required this.disclaimer,
  });

  factory ApplicationWorkflow.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationWorkflow(
      schoolName: textValue(json['school_name']),
      country: textValue(json['country']),
      programType: textValue(json['program_type']),
      steps: jsonMapList(json['steps']).map(ApplicationStep.fromJson).toList()
        ..sort((a, b) => a.order.compareTo(b.order)),
      lastChecked: textValue(json['last_checked']),
      coverageStatus: textValue(json['coverage_status']),
      coverageNote: textValue(json['coverage_note']),
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String schoolName;
  final String country;
  final String programType;
  final List<ApplicationStep> steps;
  final String lastChecked;
  final String coverageStatus;
  final String coverageNote;
  final String disclaimer;
}

class ExperienceHighlight {
  const ExperienceHighlight({
    required this.theme,
    required this.title,
    required this.summary,
    required this.sourceCount,
    required this.keyPoints,
    required this.sourceUrls,
  });

  factory ExperienceHighlight.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ExperienceHighlight(
      theme: textValue(json['theme']),
      title: textValue(json['title']),
      summary: textValue(json['summary']),
      sourceCount: json['source_count'] is int
          ? json['source_count'] as int
          : 0,
      keyPoints: stringList(json['key_points']),
      sourceUrls: stringList(json['source_urls']),
    );
  }

  final String theme;
  final String title;
  final String summary;
  final int sourceCount;
  final List<String> keyPoints;
  final List<String> sourceUrls;

  bool get hasConcreteSummary => keyPoints.isNotEmpty;
}

class ExperienceSource {
  const ExperienceSource({
    required this.title,
    required this.sourceUrl,
    required this.sourceType,
    required this.platform,
    required this.summary,
    required this.themes,
  });

  factory ExperienceSource.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ExperienceSource(
      title: textValue(json['title'], '學生分享'),
      sourceUrl: textValue(json['source_url']),
      sourceType: textValue(json['source_type'], 'article'),
      platform: textValue(json['platform']),
      summary: textValue(json['summary']),
      themes: stringList(json['themes']),
    );
  }

  final String title;
  final String sourceUrl;
  final String sourceType;
  final String platform;
  final String summary;
  final List<String> themes;
}

class ExperienceDigest {
  const ExperienceDigest({
    required this.schoolName,
    required this.totalSources,
    required this.articleCount,
    required this.videoCount,
    required this.communityCount,
    required this.highlights,
    required this.sources,
    required this.coverageNote,
    required this.disclaimer,
  });

  factory ExperienceDigest.fromJson(dynamic value) {
    final json = jsonMap(value);
    final highlights =
        jsonMapList(
          json['highlights'],
        ).map(ExperienceHighlight.fromJson).toList()..sort((a, b) {
          final aRank = a.hasConcreteSummary ? 2 : (a.sourceCount > 0 ? 1 : 0);
          final bRank = b.hasConcreteSummary ? 2 : (b.sourceCount > 0 ? 1 : 0);
          final rank = bRank.compareTo(aRank);
          return rank != 0 ? rank : b.sourceCount.compareTo(a.sourceCount);
        });
    return ExperienceDigest(
      schoolName: textValue(json['school_name']),
      totalSources: json['total_sources'] is int
          ? json['total_sources'] as int
          : 0,
      articleCount: json['article_count'] is int
          ? json['article_count'] as int
          : 0,
      videoCount: json['video_count'] is int ? json['video_count'] as int : 0,
      communityCount: json['community_count'] is int
          ? json['community_count'] as int
          : 0,
      highlights: highlights,
      sources: jsonMapList(
        json['sources'],
      ).map(ExperienceSource.fromJson).toList(),
      coverageNote: textValue(json['coverage_note']),
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String schoolName;
  final int totalSources;
  final int articleCount;
  final int videoCount;
  final int communityCount;
  final List<ExperienceHighlight> highlights;
  final List<ExperienceSource> sources;
  final String coverageNote;
  final String disclaimer;
}

class AnonymousIdentity {
  const AnonymousIdentity({
    required this.id,
    required this.displayName,
    required this.accessToken,
    this.accountId = '',
  });

  factory AnonymousIdentity.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AnonymousIdentity(
      id: textValue(json['id']),
      displayName: textValue(json['display_name']),
      accessToken: textValue(json['access_token']),
      accountId: textValue(json['account_id']),
    );
  }

  final String id;
  final String displayName;
  final String accessToken;
  final String accountId;
}

class CommunityPost {
  const CommunityPost({
    required this.id,
    required this.schoolName,
    required this.authorId,
    required this.displayName,
    required this.postType,
    required this.topic,
    required this.country,
    required this.academicYear,
    required this.applicationStage,
    required this.title,
    required this.body,
    required this.commentCount,
    required this.createdAt,
  });

  factory CommunityPost.fromJson(dynamic value) {
    final json = jsonMap(value);
    return CommunityPost(
      id: textValue(json['id']),
      schoolName: textValue(json['school_name']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      postType: textValue(json['post_type'], 'discussion'),
      topic: textValue(json['topic'], 'application'),
      country: textValue(json['country']),
      academicYear: textValue(json['academic_year']),
      applicationStage: textValue(json['application_stage']),
      title: textValue(json['title']),
      body: textValue(json['body']),
      commentCount: json['comment_count'] is int
          ? json['comment_count'] as int
          : 0,
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String schoolName;
  final String authorId;
  final String displayName;
  final String postType;
  final String topic;
  final String country;
  final String academicYear;
  final String applicationStage;
  final String title;
  final String body;
  final int commentCount;
  final String createdAt;
}

class CommunityComment {
  const CommunityComment({
    required this.id,
    required this.postId,
    required this.authorId,
    required this.displayName,
    required this.body,
    required this.createdAt,
  });

  factory CommunityComment.fromJson(dynamic value) {
    final json = jsonMap(value);
    return CommunityComment(
      id: textValue(json['id']),
      postId: textValue(json['post_id']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      body: textValue(json['body']),
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String postId;
  final String authorId;
  final String displayName;
  final String body;
  final String createdAt;
}

class CommunityThread {
  const CommunityThread({required this.post, required this.comments});

  factory CommunityThread.fromJson(dynamic value) {
    final json = jsonMap(value);
    return CommunityThread(
      post: CommunityPost.fromJson(json['post']),
      comments: jsonMapList(
        json['comments'],
      ).map(CommunityComment.fromJson).toList(),
    );
  }

  final CommunityPost post;
  final List<CommunityComment> comments;
}

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.schoolName,
    required this.authorId,
    required this.displayName,
    required this.body,
    required this.createdAt,
  });

  factory ChatMessage.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ChatMessage(
      id: textValue(json['id']),
      schoolName: textValue(json['school_name']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      body: textValue(json['body']),
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String schoolName;
  final String authorId;
  final String displayName;
  final String body;
  final String createdAt;
}

class PrivateConversation {
  const PrivateConversation({
    required this.id,
    required this.schoolName,
    required this.senderId,
    required this.senderName,
    required this.recipientId,
    required this.recipientName,
    required this.status,
    required this.updatedAt,
  });

  factory PrivateConversation.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PrivateConversation(
      id: textValue(json['id']),
      schoolName: textValue(json['school_name']),
      senderId: textValue(json['sender_id']),
      senderName: textValue(json['sender_name'], '匿名同學'),
      recipientId: textValue(json['recipient_id']),
      recipientName: textValue(json['recipient_name'], '匿名同學'),
      status: textValue(json['status'], 'pending'),
      updatedAt: textValue(json['updated_at']),
    );
  }

  final String id;
  final String schoolName;
  final String senderId;
  final String senderName;
  final String recipientId;
  final String recipientName;
  final String status;
  final String updatedAt;

  String otherName(String identityId) =>
      senderId == identityId ? recipientName : senderName;

  String statusLabel(String identityId) {
    if (status == 'accepted') return '已接受 · 可以傳送訊息';
    if (status == 'declined') {
      return recipientId == identityId ? '已婉拒邀請' : '對方已婉拒邀請';
    }
    return '等待接受邀請';
  }
}

class PrivateMessage {
  const PrivateMessage({
    required this.id,
    required this.conversationId,
    required this.authorId,
    required this.displayName,
    required this.body,
    required this.createdAt,
  });

  factory PrivateMessage.fromJson(dynamic value) {
    final json = jsonMap(value);
    return PrivateMessage(
      id: textValue(json['id']),
      conversationId: textValue(json['conversation_id']),
      authorId: textValue(json['author_id']),
      displayName: textValue(json['display_name'], '匿名同學'),
      body: textValue(json['body']),
      createdAt: textValue(json['created_at']),
    );
  }

  final String id;
  final String conversationId;
  final String authorId;
  final String displayName;
  final String body;
  final String createdAt;
}

enum ApplicationFieldKind {
  text,
  email,
  tel,
  date,
  number,
  textarea,
  select,
  checkbox,
  files,
}

ApplicationFieldKind applicationFieldKind(dynamic value) =>
    ApplicationFieldKind.values.firstWhere(
      (kind) => kind.name == value?.toString(),
      orElse: () => ApplicationFieldKind.text,
    );

class ApplicationFormField {
  const ApplicationFormField({
    required this.id,
    required this.label,
    required this.kind,
    required this.required,
    required this.options,
    required this.sensitive,
    required this.minFiles,
    required this.maxFiles,
    this.reusableProfileKey = '',
    this.placeholder = '',
    this.helpText = '',
    this.maxLength,
  });

  factory ApplicationFormField.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationFormField(
      id: textValue(json['id']),
      label: textValue(json['label']),
      kind: applicationFieldKind(json['field_type']),
      required: json['required'] == true,
      reusableProfileKey: textValue(json['reusable_profile_key']),
      placeholder: textValue(json['placeholder']),
      helpText: textValue(json['help_text']),
      options: stringList(json['options']),
      sensitive: json['sensitive'] == true,
      maxLength: json['max_length'] == null
          ? null
          : intValue(json['max_length']),
      minFiles: intValue(json['min_files']),
      maxFiles: intValue(json['max_files'], 6).clamp(1, 12),
    );
  }

  final String id;
  final String label;
  final ApplicationFieldKind kind;
  final bool required;
  final String reusableProfileKey;
  final String placeholder;
  final String helpText;
  final List<String> options;
  final bool sensitive;
  final int? maxLength;
  final int minFiles;
  final int maxFiles;
}

class ApplicationDocumentTemplate {
  const ApplicationDocumentTemplate({
    required this.id,
    required this.title,
    required this.shortTitle,
    required this.category,
    required this.stage,
    required this.description,
    required this.fields,
    required this.defaultCopies,
    required this.destinations,
    required this.signatures,
    required this.stamps,
    required this.programTypes,
    required this.conditionFlags,
    required this.officialLayout,
    required this.sourceUrl,
    required this.sourceCheckedAt,
    required this.version,
    this.conditionalNote = '',
    this.officialFormNumber = '',
    this.officialFileName = '',
  });

  factory ApplicationDocumentTemplate.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationDocumentTemplate(
      id: textValue(json['id']),
      title: textValue(json['title']),
      shortTitle: textValue(json['short_title']),
      category: textValue(json['category']),
      stage: textValue(json['stage']),
      description: textValue(json['description']),
      fields: jsonMapList(
        json['fields'],
      ).map(ApplicationFormField.fromJson).toList(),
      defaultCopies: intValue(json['default_copies'], 1).clamp(1, 10),
      destinations: stringList(json['destinations']),
      signatures: stringList(json['signatures']),
      stamps: stringList(json['stamps']),
      programTypes: stringList(json['program_types']),
      conditionFlags: stringList(json['condition_flags']),
      conditionalNote: textValue(json['conditional_note']),
      officialLayout: json['official_layout'] == true,
      officialFormNumber: textValue(json['official_form_number']),
      officialFileName: textValue(json['official_file_name']),
      sourceUrl: textValue(json['source_url']),
      sourceCheckedAt: textValue(json['source_checked_at']),
      version: textValue(json['version']),
    );
  }

  final String id;
  final String title;
  final String shortTitle;
  final String category;
  final String stage;
  final String description;
  final List<ApplicationFormField> fields;
  final int defaultCopies;
  final List<String> destinations;
  final List<String> signatures;
  final List<String> stamps;
  final List<String> programTypes;
  final List<String> conditionFlags;
  final String conditionalNote;
  final bool officialLayout;
  final String officialFormNumber;
  final String officialFileName;
  final String sourceUrl;
  final String sourceCheckedAt;
  final String version;
}

class ApplicationCenterContext {
  const ApplicationCenterContext({
    this.schoolName = '長庚大學',
    this.targetSchool = '',
    this.targetCountry = '',
    this.programType = 'exchange',
    this.academicYear = '',
    this.semester = '',
    this.flags = const [],
  });

  factory ApplicationCenterContext.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationCenterContext(
      schoolName: textValue(json['school_name'], '長庚大學'),
      targetSchool: textValue(json['target_school']),
      targetCountry: textValue(json['target_country']),
      programType: textValue(json['program_type'], 'exchange'),
      academicYear: textValue(json['academic_year']),
      semester: textValue(json['semester']),
      flags: stringList(json['flags']),
    );
  }

  final String schoolName;
  final String targetSchool;
  final String targetCountry;
  final String programType;
  final String academicYear;
  final String semester;
  final List<String> flags;

  ApplicationCenterContext copyWith({
    String? schoolName,
    String? targetSchool,
    String? targetCountry,
    String? programType,
    String? academicYear,
    String? semester,
    List<String>? flags,
  }) => ApplicationCenterContext(
    schoolName: schoolName ?? this.schoolName,
    targetSchool: targetSchool ?? this.targetSchool,
    targetCountry: targetCountry ?? this.targetCountry,
    programType: programType ?? this.programType,
    academicYear: academicYear ?? this.academicYear,
    semester: semester ?? this.semester,
    flags: flags ?? this.flags,
  );

  JsonMap toJson() => {
    'school_name': schoolName,
    'target_school': targetSchool.isEmpty ? null : targetSchool,
    'target_country': targetCountry.isEmpty ? null : targetCountry,
    'program_type': programType,
    'academic_year': academicYear.isEmpty ? null : academicYear,
    'semester': semester.isEmpty ? null : semester,
    'flags': flags,
  };
}

class ApplicationUpload {
  const ApplicationUpload({
    required this.name,
    required this.mimeType,
    required this.bytes,
  });

  final String name;
  final String mimeType;
  final Uint8List bytes;

  JsonMap toJson() => {
    'name': name,
    'type': mimeType,
    'data_url': 'data:$mimeType;base64,${base64Encode(bytes)}',
  };
}

enum ApplicationDocumentProgress {
  draft('draft', '待填寫'),
  readyToPrint('ready_to_print', '待列印'),
  pendingSignature('pending_signature', '待簽名'),
  pendingDepartmentStamp('pending_department_stamp', '待系所核章'),
  pendingSubmission('pending_submission', '待送件'),
  completed('completed', '已完成');

  const ApplicationDocumentProgress(this.apiValue, this.label);

  final String apiValue;
  final String label;

  static ApplicationDocumentProgress parse(dynamic value) =>
      ApplicationDocumentProgress.values.firstWhere(
        (status) => status.apiValue == value?.toString(),
        orElse: () => ApplicationDocumentProgress.draft,
      );
}

class ApplicationDocumentSelectionState {
  const ApplicationDocumentSelectionState({
    required this.selected,
    required this.copies,
    required this.status,
  });

  factory ApplicationDocumentSelectionState.initial(int copies) =>
      ApplicationDocumentSelectionState(
        selected: false,
        copies: copies.clamp(1, 10),
        status: ApplicationDocumentProgress.draft,
      );

  factory ApplicationDocumentSelectionState.fromJson(dynamic value) {
    final json = jsonMap(value);
    return ApplicationDocumentSelectionState(
      selected: json['selected'] == true,
      copies: intValue(json['copies'], 1).clamp(1, 10),
      status: ApplicationDocumentProgress.parse(json['status']),
    );
  }

  final bool selected;
  final int copies;
  final ApplicationDocumentProgress status;

  ApplicationDocumentSelectionState copyWith({
    bool? selected,
    int? copies,
    ApplicationDocumentProgress? status,
  }) => ApplicationDocumentSelectionState(
    selected: selected ?? this.selected,
    copies: (copies ?? this.copies).clamp(1, 10),
    status: status ?? this.status,
  );

  JsonMap toJson() => {
    'selected': selected,
    'copies': copies,
    'status': status.apiValue,
  };
}

class ApplicationFormCompletion {
  const ApplicationFormCompletion({
    required this.completed,
    required this.total,
  });

  final int completed;
  final int total;

  bool get ready => completed == total;
  int get percent => total == 0 ? 100 : ((completed / total) * 100).round();
}

class AccountSubmissionProgress {
  const AccountSubmissionProgress({
    required this.title,
    required this.method,
    required this.status,
    required this.allowedActions,
    this.responsibleUnit = '',
    this.sendByAt = '',
    this.arrivalDeadlineAt = '',
    this.proofMetadata,
    this.recordedBy = 'student',
    this.platformSubmitted = false,
    this.note = '',
    this.updatedAt = '',
  });

  factory AccountSubmissionProgress.fromJson(dynamic value) {
    final json = jsonMap(value);
    final rawProof = json['proof_metadata'];
    return AccountSubmissionProgress(
      title: textValue(json['title']),
      method: textValue(json['method'], 'unknown'),
      status: textValue(json['status'], 'not_started'),
      allowedActions: stringList(json['allowed_actions']),
      responsibleUnit: textValue(json['responsible_unit']),
      sendByAt: textValue(json['send_by_at']),
      arrivalDeadlineAt: textValue(json['arrival_deadline_at']),
      proofMetadata: rawProof is Map<String, dynamic>
          ? Map<String, dynamic>.from(rawProof)
          : null,
      recordedBy: textValue(json['recorded_by'], 'student'),
      platformSubmitted: json['platform_submitted'] == true,
      note: textValue(json['note']),
      updatedAt: textValue(json['updated_at']),
    );
  }

  final String title;
  final String method;
  final String status;
  final List<String> allowedActions;
  final String responsibleUnit;
  final String sendByAt;
  final String arrivalDeadlineAt;
  final JsonMap? proofMetadata;
  final String recordedBy;
  final bool platformSubmitted;
  final String note;
  final String updatedAt;

  bool canPerform(String action) => allowedActions.contains(action);
}
