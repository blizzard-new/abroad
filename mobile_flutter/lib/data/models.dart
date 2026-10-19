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

  String get boardTabLabel => shortName == '長庚' ? '長庚板' : '${_compactName}板';

  String get boardTitleLabel =>
      shortName == '長庚' ? '長庚討論板' : '${_compactName}討論板';
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
    coverageNote: '完整支援試點：已套用交換申請流程與 116 學年度三語組官方名額表。',
    academicScoreMinimum: 75.0,
    colleges: [
      '法律學院',
      '商學院',
      '公共事務學院',
      '社會科學學院',
      '人文學院',
      '電機資訊學院',
      '永續創新國際學院',
    ],
    aliases: [
      '國立臺北大學',
      '臺北大學',
      '台北大學',
      '北大',
      'NTPU',
      'National Taipei University',
    ],
  ),
  SupportedUniversity(
    id: 'ntu',
    schoolName: '國立臺灣大學',
    shortName: '臺大',
    englishName: 'National Taiwan University',
    officialUrl: 'https://studyabroad.ntu.edu.tw/',
    supportLevel: 'basic',
    partnerCount: 289,
    coverageNote: '已整理116-1校級甄選、文件、補助與289個合作項目；合作校本期名額與未核實條件標示待確認。',
    colleges: [
      '文學院',
      '理學院',
      '社會科學院',
      '醫學院',
      '工學院',
      '生物資源暨農學院',
      '管理學院',
      '公共衛生學院',
      '電機資訊學院',
      '法律學院',
      '生命科學院',
      '國際政經學院',
    ],
    aliases: [
      '國立臺灣大學',
      '國立台灣大學',
      '臺灣大學',
      '台灣大學',
      '臺大',
      '台大',
      'NTU',
      'National Taiwan University',
    ],
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
    aliases: [
      '國立中正大學',
      '中正大學',
      '中正',
      'CCU',
      'National Chung Cheng University',
    ],
  ),
  SupportedUniversity(
    id: 'ncu',
    schoolName: '國立中央大學',
    shortName: '中央',
    englishName: 'National Central University',
    officialUrl: 'https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw',
    supportLevel: 'basic',
    partnerCount: 214,
    coverageNote:
        '116學年度第一梯次簡章與2026/10/13最新交換姐妹校列表已公告（11/16開放線上申請）；外校當期條件逐項待核對。',
    colleges: [
      '文學院',
      '理學院',
      '工學院',
      '管理學院',
      '資訊電機學院',
      '地球科學學院',
      '客家學院',
      '生醫理工學院',
      '永續與綠能科技研究學院',
      '松濤全人學院',
    ],
    aliases: [
      '國立中央大學',
      '中央大學',
      '中央',
      '中大',
      'NCU',
      'National Central University',
    ],
  ),
  SupportedUniversity(
    id: 'tku',
    schoolName: '淡江大學',
    shortName: '淡江',
    englishName: 'Tamkang University',
    officialUrl: 'https://oieie.tku.edu.tw/',
    supportLevel: 'basic',
    partnerCount: 287,
    coverageNote:
        '部分支援：287校全量名錄／甄選機構聯集；2027–2028日語二甄4校7名已截止。新增第一梯25校50歷史名額，其他協議及一般原文列參考；新版、校區、期限與照片授權缺口逐校保存。',
    academicScoreMinimum: 75.0,
    colleges: [
      '文學院',
      '理學院',
      '工學院',
      '商管學院',
      '外國語文學院',
      '國際事務學院',
      '教育學院',
      'AI創智學院',
      '精準健康學院',
    ],
    aliases: ['淡江大學', '淡江', '淡大', 'TKU', 'Tamkang University'],
  ),
  SupportedUniversity(
    id: 'fju',
    schoolName: '天主教輔仁大學',
    shortName: '輔大',
    englishName: 'Fu Jen Catholic University',
    officialUrl: 'https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39',
    supportLevel: 'full',
    partnerCount: 234,
    coverageNote:
        '完整支援：已整理116-1說明會與甄選規定、234所姊妹校專頁條件，並附115-2及115-1名額表供規劃參考（116-1名額預計11月底公告、12月收件）。',
    academicScoreMinimum: 70.0,
    colleges: [
      '文學院',
      '藝術學院',
      '傳播學院',
      '教育與運動健康學院',
      '醫學院',
      '理工學院',
      '外語學院',
      '民生學院',
      '法律學院',
      '社會科學院',
      '管理學院',
      '織品服裝學院',
      '全人教育課程中心',
      '進修部',
    ],
    aliases: [
      '天主教輔仁大學',
      '輔仁大學',
      '輔仁',
      '輔大',
      'FJU',
      'Fu Jen Catholic University',
    ],
  ),
  SupportedUniversity(
    id: 'scu',
    schoolName: '東吳大學',
    shortName: '東吳',
    englishName: 'Soochow University',
    officialUrl: 'https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro',
    supportLevel: 'full',
    partnerCount: 191,
    coverageNote:
        '完整支援：116學年度校級赴境外（國外126校、大陸62校、英美自費研修3校，共191校）現正開放線上申請（2026/09/14–11/16 12:00截止）。',
    academicScoreMinimum: 65.0,
    colleges: ['人文社會學院', '外國語文學院', '理學院', '法學院', '商學院', '巨量資料管理學院'],
    aliases: [
      '東吳大學',
      '私立東吳大學',
      '東吳',
      'SCU',
      'Soochow University',
      'Soochow University (Taiwan)',
    ],
  ),
  SupportedUniversity(
    id: 'ntnu',
    schoolName: '國立臺灣師範大學',
    shortName: '臺師大',
    englishName: 'National Taiwan Normal University',
    officialUrl: 'https://bds.oia.ntnu.edu.tw/bds/web/OUT',
    supportLevel: 'full',
    partnerCount: 236,
    coverageNote:
        '完整支援：116-1（2027春季出國）甄選簡章與236所合作校名額表已公告（線上申請 2026/11/01–11/15），並整合174校歷屆交換心得與四語組條件。',
    academicScoreMinimum: 60.0,
    colleges: [
      '教育學院',
      '文學院',
      '理學院',
      '藝術學院',
      '科技與工程學院',
      '運動與休閒學院',
      '國際與社會科學學院',
      '音樂學院',
      '管理學院',
      '跨域科技產業創新研究學院',
    ],
    aliases: [
      '國立臺灣師範大學',
      '國立台灣師範大學',
      '臺灣師範大學',
      '台灣師範大學',
      '臺師大',
      '台師大',
      '師大',
      'NTNU',
      'National Taiwan Normal University',
    ],
  ),
  SupportedUniversity(
    id: 'cycu',
    schoolName: '中原大學',
    shortName: '中原',
    englishName: 'Chung Yuan Christian University',
    officialUrl: 'https://oia.cycu.edu.tw/?page_id=2956&lang=zh',
    supportLevel: 'full',
    partnerCount: 89,
    coverageNote: '完整支援：115-2（2027春季出國）國際暨兩岸交換計畫與89所合作校名額、Fact Sheet及36校歷屆交換心得已完整整合。',
    academicScoreMinimum: 75.0,
    colleges: [
      '理學院',
      '工學院',
      '商學院',
      '法學院',
      '設計學院',
      '人文與教育學院',
      '電機資訊學院',
      '智慧運算與量子資訊學院',
      '半導體產業學院',
    ],
    aliases: ['cycu', '中原大學', '中原', 'CYCU', 'Chung Yuan Christian University'],
  ),
  SupportedUniversity(
    id: 'ntust',
    schoolName: '國立臺灣科技大學',
    shortName: '臺科大',
    englishName: 'National Taiwan University of Science and Technology',
    officialUrl: 'https://www.oia.ntust.edu.tw/p/412-1060-8921.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 237,
    coverageNote: '完整支援：115-2（2027春季班）海外暨大陸交換生甄選簡章、237所合作校條件名額表及126校歷屆交換心得已完整整合。',
    academicScoreMinimum: 65.0,
    colleges: [
      '工程學院',
      '電資學院',
      '管理學院',
      '設計學院',
      '人文社會學院',
      '應用科技學院',
      '產學創新學院',
    ],
    aliases: [
      'ntust',
      '國立臺灣科技大學',
      '國立台灣科技大學',
      '臺灣科技大學',
      '台灣科技大學',
      '臺科大',
      '台科大',
      'NTUST',
      'Taiwan Tech',
      'National Taiwan University of Science and Technology',
    ],
  ),
  SupportedUniversity(
    id: 'yzu',
    schoolName: '元智大學',
    shortName: '元智',
    englishName: 'Yuan Ze University',
    officialUrl:
        'https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-51-28',
    supportLevel: 'full',
    partnerCount: 90,
    coverageNote:
        '完整支援：115-2（2027春季班）全球事務處校級、管理學院 OIP 院級及兩岸交換計畫共90所合作校名額、Fact Sheet與39校歷屆交換心得已完整整合。',
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
    coverageNote:
        '完整支援：115-1選送（2027春季班）與115-2選送（2027秋季班）出國研修系統（oiasap）共161所合作校名額、課程目錄與95校歷屆心得／錄取紀錄已完整整合。',
    academicScoreMinimum: 75.0,
    colleges: [
      '工程與科學學院',
      '商學院',
      '人文社會學院',
      '資訊電機學院',
      '建設學院',
      '金融學院',
      '國際科技與管理學院',
      '建築專業學院',
      '創能學院',
      '經營管理學院',
    ],
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
    coverageNote:
        '完整支援：2026–2027與2027–2028赴日本、其他國家與地區及中國大陸出國交換甄選簡章、218所合作校名額與Fact Sheet、西灣領航自動獎助及1,823篇歷屆交換心得與錄取名單已完整整合。',
    academicScoreMinimum: 70.0,
    colleges: [
      '文學院',
      '理學院',
      '工學院',
      '管理學院',
      '海洋科學學院',
      '社會科學院',
      '西灣學院',
      '醫學院',
      '半導體及重點科技研究學院',
      '國際金融研究學院',
    ],
    aliases: [
      'nsysu',
      '國立中山大學',
      '中山大學',
      '中山',
      'NSYSU',
      'National Sun Yat-sen University',
    ],
  ),
  SupportedUniversity(
    id: 'nchu',
    schoolName: '國立中興大學',
    shortName: '中興',
    englishName: 'National Chung Hsing University',
    officialUrl:
        'https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info',
    supportLevel: 'full',
    partnerCount: 226,
    coverageNote:
        '完整支援：116學年度第1學期（秋季班）出國交換甄選簡章、226所海外及大陸交換合作校名額與Fact Sheet、希望之橋暨學海系列獎學金、548篇學長姐交換心得影音及422人次錄取榜單已完整整合。',
    academicScoreMinimum: 60.0,
    colleges: [
      '文學院',
      '農業暨自然資源學院',
      '理學院',
      '工學院',
      '生命科學院',
      '獸醫學院',
      '管理學院',
      '法政學院',
      '電機資訊學院',
      '醫學院',
      '創新產業暨國際學院',
      '循環經濟研究學院',
    ],
    aliases: [
      'nchu',
      '國立中興大學',
      '中興大學',
      '中興',
      '興大',
      'NCHU',
      'National Chung Hsing University',
    ],
  ),
  SupportedUniversity(
    id: 'ntut',
    schoolName: '國立臺北科技大學',
    shortName: '北科大',
    englishName: 'National Taipei University of Technology',
    officialUrl: 'https://oia.ntut.edu.tw/p/412-1032-9242.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 206,
    coverageNote:
        '完整支援：115-1／115-2 出國交換校內甄選簡章與作業要點、206所海外及大陸港澳交換合作與雙聯學位學校、出國交換與雙聯學位暨教育部學海系列獎助學金、677篇學長姐交換心得報告與意見調查表及189人次錄取榜單已完整整合。',
    academicScoreMinimum: 70.0,
    colleges: [
      '機電學院',
      '電資學院',
      '工程學院',
      '管理學院',
      '設計學院',
      '人文與社會科學學院',
      '創新前瞻科技研究學院',
    ],
    aliases: [
      'ntut',
      '國立臺北科技大學',
      '國立台北科技大學',
      '臺北科技大學',
      '台北科技大學',
      '臺北科大',
      '台北科大',
      '北科大',
      '北科',
      'NTUT',
      'Taipei Tech',
      'National Taipei University of Technology',
    ],
  ),
  SupportedUniversity(
    id: 'nccu',
    schoolName: '國立政治大學',
    shortName: '政大',
    englishName: 'National Chengchi University',
    officialUrl: 'https://outbound.nccu.edu.tw/',
    supportLevel: 'full',
    partnerCount: 266,
    coverageNote:
        '完整支援：115-1／115-2 校級赴國外（八大語組）及赴大陸地區交換學生甄選簡章、266所合作姊妹校名額與語言門檻、6項赴外交換暨學海系列獎助學金及589篇歷屆學長姐交換心得報告已完整整合。',
    academicScoreMinimum: 70.0,
    colleges: [
      '文學院',
      '理學院',
      '社會科學學院',
      '法學院',
      '商學院',
      '外國語文學院',
      '傳播學院',
      '國際事務學院',
      '教育學院',
      '創新國際學院',
      '資訊學院',
      'X實驗學院',
      '國際金融學院',
    ],
    aliases: [
      'nccu',
      '國立政治大學',
      '政治大學',
      '政大',
      'NCCU',
      'Chengchi University',
      'National Chengchi University',
    ],
  ),
  SupportedUniversity(
    id: 'ncku',
    schoolName: '國立成功大學',
    shortName: '成大',
    englishName: 'National Cheng Kung University',
    officialUrl: 'https://oia.ncku.edu.tw/p/404-1032-227700.php?Lang=zh-tw',
    supportLevel: 'full',
    partnerCount: 211,
    coverageNote:
        '完整支援：116-1（2027秋季班）及115-1／115-2校級出國與赴大陸地區交換學生甄選簡章、211所合作姊妹校名額與語言門檻、6項赴外交換暨學海系列獎助學金及357篇歷屆學長姐交換心得報告已完整整合。',
    academicScoreMinimum: 77.0,
    colleges: [
      '文學院',
      '理學院',
      '工學院',
      '管理學院',
      '醫學院',
      '社會科學院',
      '電機資訊學院',
      '規劃與設計學院',
      '生物科學與科技學院',
      '智慧半導體及永續製造學院',
      '敏求智慧運算學院',
    ],
    aliases: [
      'ncku',
      '國立成功大學',
      '成功大學',
      '成大',
      'NCKU',
      'Cheng Kung University',
      'National Cheng Kung University',
    ],
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

  String get displayStudyPeriod => studentSummaryZh.studyPeriod.isNotEmpty
      ? studentSummaryZh.studyPeriod
      : studyPeriod;

  String get displayApplicationDeadline =>
      studentSummaryZh.applicationDeadline.isNotEmpty
      ? studentSummaryZh.applicationDeadline
      : applicationDeadline;

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
    );
  }

  String get searchableText => [
    schoolName,
    country,
    programType,
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

class AdvisorProfile {
  const AdvisorProfile({
    this.schoolName = '長庚大學',
    this.college = '',
    this.department = '',
    this.currentYear = '',
    this.degreeLevel = '',
    this.academicScore,
    this.languageTest = '',
    this.languageScore,
    this.targetTerm = '',
    this.preferredCountry = '',
    this.monthlyBudget,
    this.needsScholarship = false,
    this.question = '',
  });

  final String schoolName;
  final String college;
  final String department;
  final String currentYear;
  final String degreeLevel;
  final double? academicScore;
  final String languageTest;
  final double? languageScore;
  final String targetTerm;
  final String preferredCountry;
  final double? monthlyBudget;
  final bool needsScholarship;
  final String question;

  JsonMap toJson() => {
    'school_name': schoolName,
    if (college.isNotEmpty) 'college': college,
    if (department.isNotEmpty) 'department': department,
    if (currentYear.isNotEmpty) 'current_year': currentYear,
    if (degreeLevel.isNotEmpty) 'degree_level': degreeLevel,
    if (academicScore != null) 'academic_score': academicScore,
    if (languageTest.isNotEmpty) 'language_test': languageTest,
    if (languageScore != null) 'language_score': languageScore,
    if (targetTerm.isNotEmpty) 'target_term': targetTerm,
    if (preferredCountry.isNotEmpty) 'preferred_country': preferredCountry,
    if (monthlyBudget != null) 'monthly_budget': monthlyBudget,
    'needs_scholarship': needsScholarship,
    if (question.isNotEmpty) 'question': question,
  };
}

class AdvisorCitation {
  const AdvisorCitation({
    required this.title,
    required this.sourceUrl,
    required this.section,
    required this.publishedAt,
    required this.lastChecked,
  });

  factory AdvisorCitation.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorCitation(
      title: textValue(json['title'], '官方來源'),
      sourceUrl: textValue(json['source_url']),
      section: textValue(json['section']),
      publishedAt: textValue(json['published_at']),
      lastChecked: textValue(json['last_checked']),
    );
  }

  final String title;
  final String sourceUrl;
  final String section;
  final String publishedAt;
  final String lastChecked;
}

class AdvisorAnswer {
  const AdvisorAnswer({
    required this.question,
    required this.answer,
    required this.keyPoints,
    required this.sources,
    required this.evidenceStatus,
    required this.aiEnhanced,
  });

  factory AdvisorAnswer.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorAnswer(
      question: textValue(json['question']),
      answer: textValue(json['answer']),
      keyPoints: stringList(json['key_points']),
      sources: jsonMapList(
        json['sources'],
      ).map(AdvisorCitation.fromJson).toList(),
      evidenceStatus: textValue(json['evidence_status'], 'not_found'),
      aiEnhanced: json['ai_enhanced'] == true,
    );
  }

  final String question;
  final String answer;
  final List<String> keyPoints;
  final List<AdvisorCitation> sources;
  final String evidenceStatus;
  final bool aiEnhanced;
}

class AdvisorSchoolMatch {
  const AdvisorSchoolMatch({
    required this.schoolName,
    required this.country,
    required this.matchScore,
    required this.fitLabel,
    required this.reasons,
    required this.gaps,
    required this.sourceUrls,
    required this.imageUrl,
  });

  factory AdvisorSchoolMatch.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorSchoolMatch(
      schoolName: textValue(json['school_name']),
      country: textValue(json['country']),
      matchScore: intValue(json['match_score']),
      fitLabel: textValue(json['fit_label'], '待確認'),
      reasons: stringList(json['reasons']),
      gaps: stringList(json['gaps']),
      sourceUrls: stringList(json['source_urls']),
      imageUrl: textValue(json['image_url']),
    );
  }

  final String schoolName;
  final String country;
  final int matchScore;
  final String fitLabel;
  final List<String> reasons;
  final List<String> gaps;
  final List<String> sourceUrls;
  final String imageUrl;
}

class AdvisorTask {
  const AdvisorTask({
    required this.id,
    required this.title,
    required this.detail,
    required this.category,
    required this.priority,
    required this.dueDate,
    required this.daysRemaining,
    required this.sourceUrl,
  });

  factory AdvisorTask.fromJson(dynamic value) {
    final json = jsonMap(value);
    return AdvisorTask(
      id: textValue(json['id']),
      title: textValue(json['title']),
      detail: textValue(json['detail']),
      category: textValue(json['category'], 'other'),
      priority: textValue(json['priority'], 'medium'),
      dueDate: textValue(json['due_date']),
      daysRemaining: json['days_remaining'] == null
          ? null
          : intValue(json['days_remaining']),
      sourceUrl: textValue(json['source_url']),
    );
  }

  final String id;
  final String title;
  final String detail;
  final String category;
  final String priority;
  final String dueDate;
  final int? daysRemaining;
  final String sourceUrl;
}

class AdvisorPlan {
  const AdvisorPlan({
    required this.schoolName,
    required this.generatedAt,
    required this.mode,
    required this.summary,
    required this.qualification,
    required this.recommendations,
    required this.tasks,
    required this.answer,
    required this.disclaimer,
  });

  factory AdvisorPlan.fromJson(dynamic value) {
    final json = jsonMap(value);
    final answer = json['answer'];
    return AdvisorPlan(
      schoolName: textValue(json['school_name'], '長庚大學'),
      generatedAt: textValue(json['generated_at']),
      mode: textValue(json['mode'], 'source_grounded'),
      summary: textValue(json['summary']),
      qualification: stringList(json['qualification']),
      recommendations: jsonMapList(
        json['recommendations'],
      ).map(AdvisorSchoolMatch.fromJson).toList(),
      tasks: jsonMapList(json['tasks']).map(AdvisorTask.fromJson).toList(),
      answer: answer is Map ? AdvisorAnswer.fromJson(answer) : null,
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String schoolName;
  final String generatedAt;
  final String mode;
  final String summary;
  final List<String> qualification;
  final List<AdvisorSchoolMatch> recommendations;
  final List<AdvisorTask> tasks;
  final AdvisorAnswer? answer;
  final String disclaimer;
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
    required this.completenessScore,
    required this.checksPassed,
    required this.issues,
    required this.suggestions,
    required this.extractedPreview,
    required this.aiEnhanced,
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
      completenessScore: intValue(json['completeness_score']),
      checksPassed: stringList(json['checks_passed']),
      issues: jsonMapList(
        json['issues'],
      ).map(DocumentCheckIssue.fromJson).toList(),
      suggestions: stringList(json['suggestions']),
      extractedPreview: textValue(json['extracted_preview']),
      aiEnhanced: json['ai_enhanced'] == true,
      privacyNote: textValue(json['privacy_note']),
    );
  }

  final String fileName;
  final String documentType;
  final String summary;
  final int pageCount;
  final int characterCount;
  final int wordCount;
  final int completenessScore;
  final List<String> checksPassed;
  final List<DocumentCheckIssue> issues;
  final List<String> suggestions;
  final String extractedPreview;
  final bool aiEnhanced;
  final String privacyNote;
}

class DocumentRewriteResult {
  const DocumentRewriteResult({
    required this.action,
    required this.draft,
    required this.changes,
    required this.warnings,
    required this.aiEnhanced,
    required this.disclaimer,
  });

  factory DocumentRewriteResult.fromJson(dynamic value) {
    final json = jsonMap(value);
    return DocumentRewriteResult(
      action: textValue(json['action']),
      draft: textValue(json['draft']),
      changes: stringList(json['changes']),
      warnings: stringList(json['warnings']),
      aiEnhanced: json['ai_enhanced'] == true,
      disclaimer: textValue(json['disclaimer']),
    );
  }

  final String action;
  final String draft;
  final List<String> changes;
  final List<String> warnings;
  final bool aiEnhanced;
  final String disclaimer;
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
