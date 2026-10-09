// TKU registration directory; programme eligibility is checked separately.
window.UniWayAcademicUnits ||= {};
window.UniWayAcademicUnits["淡江大學"] = {
  "sourceUrl": "https://www.tku.edu.tw/acad.asp",
  "checkedAt": "2026-10-08T20:08:42.648443+00:00",
  "colleges": {
    "文學院": [
      "中國文學學系",
      "歷史學系",
      "資訊與圖書館學系",
      "大眾傳播學系",
      "資訊傳播學系"
    ],
    "理學院": [
      "應用數學與數據科學學系",
      "物理學系",
      "化學學系",
      "尖端材料科學學士學位學程",
      "理學院應用科學博士班"
    ],
    "工學院": [
      "建築學系",
      "土木工程學系",
      "水資源及環境工程學系",
      "機械與機電工程學系",
      "化學工程與材料工程學系",
      "電機工程學系",
      "資訊工程學系",
      "航空太空工程學系"
    ],
    "商管學院": [
      "國際企業學系",
      "財務金融學系",
      "風險管理與保險學系",
      "經濟學系",
      "企業管理學系",
      "會計學系",
      "統計與資料科學學系",
      "資訊管理學系",
      "運輸管理學系",
      "公共行政暨法律學系",
      "管理科學學系",
      "商管碩士在職專班",
      "淡江大學暨澳洲昆士蘭理工大學財金全英語雙碩士學位學程"
    ],
    "外國語文學院": [
      "英文學系",
      "日本語文學系",
      "歐洲語文學系"
    ],
    "國際事務學院": [
      "國際事務與戰略研究所",
      "外交與國際關係學系",
      "國際觀光管理學系",
      "全球政治經濟學系"
    ],
    "教育學院": [
      "教育科技學系",
      "教育與未來設計學系",
      "教育心理與諮商研究所"
    ],
    "AI創智學院": [
      "人工智慧學系"
    ],
    "精準健康學院": [
      "高齡健康管理學研究所",
      "智慧照護產業學研究所"
    ]
  }
};
window.UniWayTKU = {
  applicationYears(periods) {
    const years = periods.map(row => Number(String(row.academic_year || '').split('-')[0])).filter(year => year >= 2000);
    const first = years.length ? Math.max(...years) : new Date().getFullYear() + 1;
    return [first, first + 1, first + 2].map(year => `${year}-${year + 1}`);
  }
};
