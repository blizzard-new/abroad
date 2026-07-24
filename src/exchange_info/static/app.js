const state = {
  dashboard: null,
  query: "",
  partnerQuery: "",
  country: "",
  college: "",
  degree: "",
  partnerLimit: window.matchMedia("(max-width: 820px)").matches ? 8 : 20,
  documentType: "全部",
  statusTimer: null,
  hasLoaded: false,
  activeSchool: null,
  experienceRequestId: 0,
  experienceCache: new Map(),
  workflowRequestId: 0,
  workflowCache: new Map(),
  destinationRequestId: 0,
  destinationCache: new Map(),
  communityRequestId: 0,
  communityCache: new Map(),
  communityView: "posts",
  anonymousIdentity: null,
  account: null,
  authToken: "",
  authProviders: [],
  authMode: "login",
  globalCommunityTopic: "",
  globalCommunityQuery: "",
  globalCommunityThreads: [],
  globalCommunityTimer: null,
  globalCommunityFeed: "all",
  theme: "light",
  homeSchool: "",
  selectedHomeSchool: "長庚大學",
  supportedUniversities: [],
  coverage: null,
  favorites: new Set(),
  applications: new Set(),
  applicationProgress: {},
  documentReadiness: {},
  eligibilityProfile: null,
  destinationProfiles: [],
  schoolImages: [],
  calendarEvents: [],
  calendarMonth: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  calendarSelectedDate: "",
  calendarAgendaMode: "upcoming",
  calendarSync: null,
  calendarSyncLoading: false,
  calendarProvider: "google",
  budgetPlans: {},
  budgetSchool: "",
  applicationTemplates: [],
  applicationContext: {
    school_name: "長庚大學",
    target_school: "",
    target_country: "",
    program_type: "exchange",
    academic_year: "",
    semester: "",
    flags: [],
  },
  applicationProfile: {},
  applicationProfileMemoryEnabled: false,
  applicationAnswers: {},
  applicationSelections: {},
  applicationFiles: {},
  activeApplicationTemplateId: "",
  applicationLoading: false,
  advisorPlan: null,
  advisorLoading: false,
  aiStatus: null,
  documentCheckResult: null,
  documentCheckLoading: false,
  writingAssistantResult: null,
  writingAssistantLoading: false,
  updateSeenAt: "",
  studentVerificationToken: "",
  verificationPreviewUrls: {},
  dashboardScrollY: 0,
  dashboardHash: "#overview",
  searchReturnHash: "#overview",
  onboardingReturnFocus: null,
  dialogReturnFocus: null,
  homeSchoolRequestId: 0,
};

const $ = (selector) => document.querySelector(selector);

const PUBLIC_COMMUNITY_BOARD = "公共留學板";
const LEGACY_PUBLIC_COMMUNITY_BOARD = "一般留學討論";
const CGU_COMMUNITY_BOARD = "長庚大學";
const NTPU_COMMUNITY_BOARD = "國立臺北大學";
const DEFAULT_HOME_SCHOOL = CGU_COMMUNITY_BOARD;
const UNIVERSITY_PAGE_ROUTES = new Set([
  "overview",
  "advisor",
  "partners",
  "favorites",
  "calendar",
  "deadlines",
  "scholarships",
  "budget",
  "eligibility",
  "application-center",
  "application-form",
  "document-check",
  "writing-assistant",
  "documents",
  "search",
]);
const UNIVERSITY_PAGE_TITLES = {
  overview: "我的交換計畫",
  advisor: "申請顧問",
  partners: "找交換學校",
  favorites: "收藏與比較",
  calendar: "申請日曆",
  deadlines: "官方截止日",
  scholarships: "補助資訊",
  budget: "交換預算",
  eligibility: "資格初判",
  "application-center": "申請文件",
  "application-form": "填寫申請文件",
  "document-check": "文件檢查",
  "writing-assistant": "文件改寫",
  documents: "文件庫",
  search: "搜尋結果",
};

const HIGHLIGHT_TERMS = [
  "截止日期",
  "申請期間",
  "成績門檻",
  "語言門檻",
  "補助金額",
  "補助額度",
  "補助限制",
  "不得同時",
  "不得重複",
  "返國義務",
  "70 分以上",
  "70分以上",
  "75 分以上",
  "75分以上",
  "多益 TOEIC 700",
  "多益 700",
  "IELTS 5.5",
  "TOEFL iBT 72",
  "Duolingo 105",
  "75,000",
  "150,000",
  "60,000",
  "120,000",
  "10,000 元",
  "一學期",
  "一學年",
  "申請表",
  "截止日",
  "GPA",
  "方案 A",
  "方案 B",
  "各單項不得低於",
  "不保證提供學生宿舍",
  "同意書",
  "計畫書",
  "聲明書",
  "心得報告",
  "領航者補助作業要點",
  "學海惜珠",
  "學海築夢",
];

const LANGUAGE_THRESHOLDS = {
  toeic: { label: "TOEIC", minimum: 700 },
  ielts: { label: "IELTS", minimum: 5.5 },
  toefl: { label: "TOEFL iBT", minimum: 72 },
  duolingo: { label: "Duolingo", minimum: 105 },
};

const STORAGE_KEYS = {
  homeSchool: "exchange-guide-home-school",
  favorites: "exchange-guide-favorites",
  applications: "exchange-guide-applications",
  progress: "exchange-guide-application-progress",
  documents: "exchange-guide-document-readiness",
  eligibility: "exchange-guide-eligibility-profile",
  communityIdentity: "exchange-guide-anonymous-identity",
  authToken: "exchange-guide-auth-token",
  calendarEvents: "exchange-guide-calendar-events",
  budgetPlans: "exchange-guide-budget-plans",
  applicationContext: "exchange-guide-application-context",
  applicationSelections: "exchange-guide-application-selections",
  applicationProfileMemory: "exchange-guide-application-profile-memory-v1",
  applicationProfileMemoryEnabled: "exchange-guide-application-profile-memory-enabled",
  updateSeenAt: "exchange-guide-update-seen-at",
};

const APPLICATION_SESSION_KEYS = {
  profile: "exchange-guide-application-profile-session",
  answers: "exchange-guide-application-answers-session",
};

const APPLICATION_REUSABLE_PROFILE_KEYS = new Set([
  "student_name_zh",
  "student_name_en",
  "student_id",
  "college",
  "department",
  "degree_level",
  "year_level",
  "email",
  "phone",
  "id_number",
  "birth_date",
  "passport_number",
  "mailing_address",
  "emergency_contact",
  "emergency_phone",
  "guardian_name",
  "guardian_relation",
  "guardian_id_number",
]);

const APPLICATION_PERSISTENT_PROFILE_KEYS = new Set(
  [...APPLICATION_REUSABLE_PROFILE_KEYS].filter((key) => ![
    "id_number",
    "birth_date",
    "passport_number",
    "guardian_id_number",
  ].includes(key)),
);

const APPLICATION_STAGE_ICONS = {
  "校內申請": "send",
  "校內初審通過後": "badge-check",
  "錄取後／出國前": "plane-takeoff",
  "補助核定後": "badge-dollar-sign",
  "抵達後 14 天內": "map-pin-check",
  "海外研修期間": "book-open-check",
  "返國後": "home",
  "短期課程申請": "calendar-plus",
  "短期課程返國後": "images",
};

const APPLICATION_DOCUMENT_STATUSES = [
  ["draft", "待填寫"],
  ["ready_to_print", "待列印"],
  ["pending_signature", "待簽名"],
  ["pending_department_stamp", "待系所核章"],
  ["pending_submission", "待送件"],
  ["completed", "已完成"],
];

function applicationDocumentStatus(templateId) {
  return state.applicationSelections[templateId]?.status || "draft";
}

function applicationDocumentStatusLabel(templateId) {
  const status = applicationDocumentStatus(templateId);
  return APPLICATION_DOCUMENT_STATUSES.find(([value]) => value === status)?.[1] || "待填寫";
}

function applicationDocumentNextStep(template) {
  const status = applicationDocumentStatus(template.id);
  if (status === "draft") return "先完成必填欄位，再產生列印版。";
  if (status === "ready_to_print") return "下載 PDF，依份數列印並核對附件。";
  if (status === "pending_signature") return template.signatures?.length ? `請完成：${template.signatures.join("、")}` : "確認是否需要親筆簽名。";
  if (status === "pending_department_stamp") return template.stamps?.length ? `請完成：${template.stamps.join("、")}` : "向承辦單位確認核章流程。";
  if (status === "pending_submission") return template.destinations?.length ? `交至：${template.destinations.join("、")}` : "依公告送件並保留副本。";
  return "保留已送件 PDF 與收件證明。";
}

const COMMUNITY_TOPICS = [
  ["", "全部"],
  ["application", "申請"],
  ["scholarship", "獎學金"],
  ["housing", "住宿"],
  ["cost", "生活費"],
  ["visa", "簽證"],
  ["academics", "課程"],
  ["life", "生活"],
  ["career", "就業"],
  ["warning", "避雷"],
];

const LIFE_SECTIONS = [
  { theme: "housing", label: "住宿與宿舍", icon: "bed-double", prompt: "住宿選項、申請時間、宿舍名額與通勤距離" },
  { theme: "cost", label: "每月生活預算", icon: "wallet-cards", prompt: "房租、水電、日用品與每月生活費範圍" },
  { theme: "food", label: "飲食與採買", icon: "utensils", prompt: "外食、校園餐廳、超市、自炊與價格" },
  { theme: "transport", label: "交通與地點", icon: "bus-front", prompt: "機場、市區、校園距離、通勤與夜間交通" },
  { theme: "academics", label: "課業與教學", icon: "book-open-check", prompt: "課程難度、英文授課、評量方式與出席要求" },
  { theme: "climate", label: "氣候與穿著", icon: "cloud-sun", prompt: "季節、降雨、溫度與行李準備" },
  { theme: "social", label: "校園活動與社交", icon: "users-round", prompt: "社團、活動、夜生活與認識同學的方式" },
  { theme: "safety", relatedThemes: ["safety", "support"], label: "安全、醫療與保險", icon: "heart-pulse", prompt: "治安、夜間移動、就醫、保險與緊急支援" },
  { theme: "campus_culture", relatedThemes: ["campus_culture", "challenges"], label: "文化適應與交朋友", icon: "messages-square", prompt: "文化差異、融入難易度、孤單與常見適應問題" },
  { theme: "travel", label: "旅行與周邊城市", icon: "map", prompt: "機場、週末旅行與周邊城市便利性" },
];

const APPLICATION_PROGRESS_STEPS = [
  { id: "eligibility", label: "確認資格與語言門檻" },
  { id: "compare", label: "比較課程、費用與生活" },
  { id: "documents", label: "備妥校內申請文件" },
  { id: "home-submit", label: "完成校內甄選送件" },
  { id: "partner-submit", label: "完成合作校線上申請" },
];

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightHtml(value) {
  const html = escapeHtml(value);
  const pattern = new RegExp(
    `(${[...HIGHLIGHT_TERMS]
      .sort((a, b) => b.length - a.length)
      .map(escapeRegExp)
      .join("|")})`,
    "g"
  );
  return html.replace(pattern, '<strong class="text-highlight">$1</strong>');
}

function normalize(value) {
  return String(value ?? "").toLowerCase().replace(/\s+/g, " ").trim();
}

function activeHomeSchool() {
  return state.homeSchool || DEFAULT_HOME_SCHOOL;
}

function isCurrentHomeSchool(schoolName) {
  return normalize(activeHomeSchool()) === normalize(schoolName);
}

function activeUniversityProfile() {
  return state.supportedUniversities.find(
    (item) => normalize(item.school_name) === normalize(activeHomeSchool())
  ) || {
    school_name: activeHomeSchool(),
    short_name: activeHomeSchool().replace(/大學$/, ""),
    hero_image: "/static/assets/cgu-campus.jpg",
  };
}

function academicMinimum() {
  return Number(state.dashboard?.academic_score_minimum) || 70;
}

function languageThreshold(test) {
  const minimum = state.dashboard?.language_score_minimums?.[test];
  if (Number.isFinite(Number(minimum))) {
    return { label: LANGUAGE_THRESHOLDS[test]?.label || test.toUpperCase(), minimum: Number(minimum) };
  }
  if (state.dashboard) return null;
  return LANGUAGE_THRESHOLDS[test] || null;
}

function truncate(value, max = 90) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > max ? `${text.slice(0, max - 1).trim()}…` : text;
}

function formatDate(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function initIcons() {
  if (window.lucide) {
    window.lucide.createIcons({ attrs: { "aria-hidden": "true" } });
  }
}

function applyTheme(theme, { persist = true } = {}) {
  const nextTheme = theme === "light" ? "light" : "dark";
  state.theme = nextTheme;
  document.documentElement.dataset.theme = nextTheme;
  document.documentElement.style.colorScheme = nextTheme;
  const meta = $("#theme-color");
  if (meta) meta.setAttribute("content", nextTheme === "dark" ? "#080a0d" : "#f5f5f7");
  const button = $("#theme-toggle");
  if (button) {
    const target = nextTheme === "dark" ? "淺色" : "深色";
    button.setAttribute("aria-label", `切換為${target}模式`);
    button.dataset.tooltip = `${target}模式`;
    button.innerHTML = `<i data-lucide="${nextTheme === "dark" ? "sun" : "moon"}" aria-hidden="true"></i>`;
  }
  if (persist) {
    try {
      window.localStorage.setItem("exchange-guide-theme", nextTheme);
    } catch (_) {
      // Theme still works when storage is unavailable.
    }
  }
  initIcons();
}

function initializeTheme() {
  let storedTheme = "";
  try {
    storedTheme = window.localStorage.getItem("exchange-guide-theme") || "";
  } catch (_) {
    storedTheme = "";
  }
  applyTheme(storedTheme || "light", { persist: false });
}

function readStoredState() {
  try {
    state.homeSchool = window.localStorage.getItem(STORAGE_KEYS.homeSchool) || "";
    state.selectedHomeSchool = state.homeSchool || DEFAULT_HOME_SCHOOL;
    state.favorites = new Set(JSON.parse(window.localStorage.getItem(STORAGE_KEYS.favorites) || "[]"));
    state.applications = new Set(JSON.parse(window.localStorage.getItem(STORAGE_KEYS.applications) || "[]"));
    state.applicationProgress = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.progress) || "{}");
    state.documentReadiness = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.documents) || "{}");
    state.eligibilityProfile = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.eligibility) || "null");
    state.anonymousIdentity = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.communityIdentity) || "null");
    state.authToken = window.localStorage.getItem(STORAGE_KEYS.authToken) || "";
    state.calendarEvents = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.calendarEvents) || "[]");
    state.budgetPlans = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.budgetPlans) || "{}");
    state.applicationContext = {
      ...state.applicationContext,
      ...JSON.parse(window.localStorage.getItem(STORAGE_KEYS.applicationContext) || "{}"),
    };
    state.applicationSelections = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.applicationSelections) || "{}");
    state.applicationProfileMemoryEnabled = window.localStorage.getItem(STORAGE_KEYS.applicationProfileMemoryEnabled) === "true";
    const rememberedApplicationProfile = state.applicationProfileMemoryEnabled
      ? JSON.parse(window.localStorage.getItem(STORAGE_KEYS.applicationProfileMemory) || "{}")
      : {};
    const sessionApplicationProfile = JSON.parse(window.sessionStorage.getItem(APPLICATION_SESSION_KEYS.profile) || "{}");
    state.applicationProfile = {
      ...sanitizeApplicationProfileForMemory(rememberedApplicationProfile),
      ...(sessionApplicationProfile && typeof sessionApplicationProfile === "object" && !Array.isArray(sessionApplicationProfile) ? sessionApplicationProfile : {}),
    };
    state.applicationAnswers = JSON.parse(window.sessionStorage.getItem(APPLICATION_SESSION_KEYS.answers) || "{}");
    state.updateSeenAt = window.localStorage.getItem(STORAGE_KEYS.updateSeenAt) || "";
    if (!Array.isArray(state.calendarEvents)) state.calendarEvents = [];
    if (!state.budgetPlans || Array.isArray(state.budgetPlans) || typeof state.budgetPlans !== "object") state.budgetPlans = {};
    if (!state.applicationSelections || Array.isArray(state.applicationSelections) || typeof state.applicationSelections !== "object") state.applicationSelections = {};
    if (!state.applicationProfile || Array.isArray(state.applicationProfile) || typeof state.applicationProfile !== "object") state.applicationProfile = {};
    if (!state.applicationAnswers || Array.isArray(state.applicationAnswers) || typeof state.applicationAnswers !== "object") state.applicationAnswers = {};
    state.applicationContext.school_name = activeHomeSchool();
    stripReusableApplicationAnswers();
  } catch (_) {
    state.homeSchool = "";
    state.selectedHomeSchool = DEFAULT_HOME_SCHOOL;
    state.favorites = new Set();
    state.applications = new Set();
    state.applicationProgress = {};
    state.documentReadiness = {};
    state.eligibilityProfile = null;
    state.anonymousIdentity = null;
    state.authToken = "";
    state.calendarEvents = [];
    state.budgetPlans = {};
    state.applicationProfile = {};
    state.applicationProfileMemoryEnabled = false;
    state.applicationAnswers = {};
    state.applicationSelections = {};
    state.applicationFiles = {};
    state.updateSeenAt = "";
  }
  updateSchoolContext();
}

async function loadSupportedUniversities() {
  try {
    state.supportedUniversities = await fetchJson("/universities");
  } catch (_) {
    state.supportedUniversities = [
      {
        id: "cgu",
        school_name: "長庚大學",
        short_name: "長庚",
        english_name: "Chang Gung University",
        supported: true,
        partner_count: 62,
        coverage_note: "第一階段已整理長庚大學交換資訊。",
      },
      {
        id: "ntpu",
        school_name: "國立臺北大學",
        short_name: "北大",
        english_name: "National Taipei University",
        hero_image: "/static/assets/ntpu-campus.jpg",
        official_url: "https://new.ntpu.edu.tw/oia",
        supported: true,
        partner_count: 155,
        coverage_note: "已整理 115 學年度赴外交換資訊。",
      },
    ];
  }
  renderSchoolOptions();
  updateSchoolContext();
}

async function loadCoverage({ homeSchool = activeHomeSchool() } = {}) {
  const requestedSchool = homeSchool;
  let coverage = null;
  try {
    coverage = await fetchJson(`/coverage?school=${encodeURIComponent(requestedSchool)}`);
  } catch (_) {
    if (!isCurrentHomeSchool(requestedSchool)) return false;
  }
  if (!isCurrentHomeSchool(requestedSchool)) return false;
  state.coverage = coverage;
  const total = state.coverage?.total_partner_schools || state.dashboard?.partner_universities?.length || 0;
  const imageCount = state.coverage?.image_count || 0;
  const websiteCount = state.coverage?.official_website_count || 0;
  const experienceCount = state.coverage?.experience_checked_count || 0;
  const workflowCount = state.coverage?.workflow_school_count || 0;
  const destinationCount = state.coverage?.destination_profile_count || 0;
  $("#image-coverage").textContent = total ? `${imageCount}/${total}` : "--";
  $("#website-coverage").textContent = total ? `${websiteCount}/${total}` : "--";
  $("#experience-coverage").textContent = total ? `${experienceCount}/${total}` : "--";
  $("#workflow-coverage").textContent = total ? `${workflowCount}/${total}` : "--";
  $("#destination-coverage").textContent = total ? `${destinationCount}/${total}` : "--";
  if (state.dashboard) renderPartnerTable();
  return true;
}

async function loadDestinationProfiles() {
  try {
    state.destinationProfiles = await fetchJson("/destination-profiles");
  } catch (_) {
    state.destinationProfiles = [];
  }
  if (state.dashboard) {
    renderPartnerTable();
    renderSearchResults();
    renderRecommendedMatches();
    renderBudgetPlanner();
  }
}

async function loadSchoolImages() {
  try {
    const payload = await fetchJson("/static/assets/school-images.json");
    state.schoolImages = Array.isArray(payload?.schools)
      ? payload.schools.filter((item) => item.status === "verified" && item.local_path)
      : [];
  } catch (_) {
    state.schoolImages = [];
  }
}

function schoolImageFor(schoolName) {
  return state.schoolImages.find(
    (item) => normalize(item.school_name) === normalize(schoolName)
  );
}

function renderSchoolPhoto(item, variant = "card") {
  const visual = schoolImageFor(item.school_name);
  const label = item.country || "交換學校";
  const fallback = `
    <span class="school-photo-fallback" aria-hidden="true">
      <i data-lucide="school"></i><span>${escapeHtml(label)}</span>
    </span>`;
  const loading = variant === "detail" ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"';
  const image = visual?.local_path
    ? `<img src="${escapeHtml(visual.local_path)}" alt="${escapeHtml(item.school_name)}官方照片" ${loading} decoding="async" onerror="this.remove()" />`
    : "";
  return `<span class="school-photo school-photo-${escapeHtml(variant)}">${fallback}${image}</span>`;
}

function destinationProfileForSchool(schoolName) {
  return state.destinationProfiles.find(
    (profile) => normalize(profile.school_name) === normalize(schoolName)
  );
}

function coverageForSchool(schoolName) {
  return state.coverage?.partners?.find(
    (item) => normalize(item.school_name) === normalize(schoolName)
  );
}

function renderCoverageBadges(item) {
  const coverage = coverageForSchool(item.school_name);
  if (!coverage) return '<span class="coverage-chip pending">資料待查核</span>';
  let image = '<span class="coverage-chip pending">照片待整理</span>';
  if (coverage.image_status === "verified") {
    image = '<span class="coverage-chip ready">官方照片已確認</span>';
  } else if (coverage.image_status === "missing") {
    image = '<span class="coverage-chip empty">官方照片待補</span>';
  } else if (coverage.image_status === "error") {
    image = '<span class="coverage-chip error">照片擷取失敗</span>';
  }
  let website = '<span class="coverage-chip pending">官網待查核</span>';
  if (coverage.official_website_status === "official_verified") {
    website = '<span class="coverage-chip ready">官網已確認</span>';
  } else if (coverage.official_website_status === "needs_review") {
    website = '<span class="coverage-chip pending">官網待人工複核</span>';
  } else if (coverage.official_website_status === "not_found") {
    website = '<span class="coverage-chip empty">已搜尋，官網未確認</span>';
  } else if (coverage.official_website_status === "error") {
    website = '<span class="coverage-chip error">官網搜尋失敗，待重試</span>';
  }
  let experience = '<span class="coverage-chip pending">心得待整理</span>';
  if (coverage.experience_status === "completed" && coverage.experience_source_count) {
    experience = `<span class="coverage-chip ready">${coverage.experience_source_count} 個心得來源</span>`;
  } else if (coverage.experience_status === "no_results") {
    experience = '<span class="coverage-chip empty">已搜尋，暫無可靠心得</span>';
  } else if (coverage.experience_status === "error") {
    experience = '<span class="coverage-chip error">心得搜尋失敗，待重試</span>';
  }
  let workflow = '<span class="coverage-chip pending">流程待查核</span>';
  if (coverage.workflow_status === "official_verified") {
    workflow = '<span class="coverage-chip ready">流程已查核</span>';
  } else if (coverage.workflow_status === "official_partial") {
    workflow = '<span class="coverage-chip pending">流程部分查核</span>';
  } else if (coverage.workflow_status === "not_found") {
    workflow = '<span class="coverage-chip empty">合作校流程頁待確認</span>';
  } else if (coverage.workflow_status === "error") {
    workflow = '<span class="coverage-chip error">流程查核失敗</span>';
  }
  let destination = '<span class="coverage-chip pending">生活資訊待查核</span>';
  if (coverage.destination_status === "official_verified") {
    destination = '<span class="coverage-chip ready">生活資訊已查核</span>';
  } else if (coverage.destination_status === "official_partial") {
    destination = '<span class="coverage-chip pending">生活資訊部分查核</span>';
  } else if (coverage.destination_status === "not_found") {
    destination = '<span class="coverage-chip empty">生活資訊暫無結果</span>';
  } else if (coverage.destination_status === "error") {
    destination = '<span class="coverage-chip error">生活資訊查核失敗</span>';
  }
  return `${image}${website}${experience}${workflow}${destination}`;
}

function renderSchoolOptions(query = "") {
  const container = $("#school-options");
  if (!container) return;
  const normalizedQuery = normalize(query);
  const universities = state.supportedUniversities.filter((item) => {
    const text = normalize([item.school_name, item.short_name, item.english_name].filter(Boolean).join(" "));
    return !normalizedQuery || text.includes(normalizedQuery);
  });
  $("#school-search-empty").hidden = universities.length > 0;
  container.innerHTML = universities
    .map(
      (item) => `
        <button type="button" class="school-option${item.school_name === state.selectedHomeSchool ? " selected" : ""}" data-home-school="${escapeHtml(item.school_name)}" role="option" aria-selected="${item.school_name === state.selectedHomeSchool}">
          <img src="${escapeHtml(item.hero_image || "/static/assets/cgu-campus.jpg")}" alt="${escapeHtml(item.school_name)}校園" />
          <span><strong>${escapeHtml(item.school_name)}</strong><small>${escapeHtml(item.coverage_note)}</small></span>
          <span class="school-option-status">${item.partner_count ? `${item.partner_count} 間合作校` : "資料建置中"}</span>
          <i data-lucide="${item.school_name === state.selectedHomeSchool ? "circle-check" : "circle"}" aria-hidden="true"></i>
        </button>`
    )
    .join("");
  initIcons();
}

function openSchoolOnboarding() {
  const onboarding = $("#school-onboarding");
  const activeElement = document.activeElement;
  state.onboardingReturnFocus = activeElement instanceof HTMLElement && activeElement !== document.body
    ? activeElement
    : null;
  onboarding.hidden = false;
  document.body.classList.add("onboarding-open");
  window.setTimeout(() => $("#school-search")?.focus(), 40);
}

function closeSchoolOnboarding() {
  $("#school-onboarding").hidden = true;
  document.body.classList.remove("onboarding-open");
  const returnFocus = state.onboardingReturnFocus;
  state.onboardingReturnFocus = null;
  if (returnFocus?.isConnected) window.setTimeout(() => returnFocus.focus(), 0);
}

function browseWithoutSchoolSelection() {
  const previousSchool = activeHomeSchool();
  try {
    window.sessionStorage.setItem("exchange-guide-browse-first", "1");
  } catch (_) {
    // Browsing still works when storage is unavailable.
  }
  state.homeSchool = "";
  state.selectedHomeSchool = DEFAULT_HOME_SCHOOL;
  state.applicationContext.school_name = DEFAULT_HOME_SCHOOL;
  updateSchoolContext();
  closeSchoolOnboarding();
  if (state.hasLoaded && normalize(previousSchool) !== normalize(DEFAULT_HOME_SCHOOL)) {
    refreshHomeUniversityData();
  }
}

function handleOnboardingKeydown(event) {
  const onboarding = $("#school-onboarding");
  if (onboarding.hidden) return;
  if (event.key === "Escape") {
    event.preventDefault();
    browseWithoutSchoolSelection();
    return;
  }
  if (event.key !== "Tab") return;
  const focusable = [...onboarding.querySelectorAll('button:not([disabled]), input:not([disabled])')]
    .filter((item) => item.getClientRects().length > 0);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function setHomeSchool(schoolName, { reload = true } = {}) {
  const nextSchool = schoolName || DEFAULT_HOME_SCHOOL;
  const changed = normalize(activeHomeSchool()) !== normalize(nextSchool);
  const dashboardMismatch = Boolean(state.dashboard?.school_name)
    && normalize(state.dashboard.school_name) !== normalize(nextSchool);
  const needsRefresh = changed || dashboardMismatch;
  state.homeSchool = nextSchool;
  state.selectedHomeSchool = nextSchool;
  state.applicationContext.school_name = nextSchool;
  if (needsRefresh) {
    state.applicationContext.target_school = "";
    state.applicationContext.target_country = "";
    state.coverage = null;
    state.advisorPlan = null;
    state.activeSchool = null;
    state.experienceCache.clear();
    state.workflowCache.clear();
    state.destinationCache.clear();
    state.communityCache.clear();
  }
  if (needsRefresh && window.location.hash.startsWith("#school=")) {
    window.history.replaceState({}, "", "#partners");
  }
  try {
    window.localStorage.setItem(STORAGE_KEYS.homeSchool, nextSchool);
  } catch (_) {
    // The selected school still applies for this session.
  }
  persistApplicationContext();
  updateSchoolContext();
  closeSchoolOnboarding();
  if (needsRefresh && reload) refreshHomeUniversityData();
}

function updateSchoolContext() {
  const selected = state.homeSchool || "";
  const profile = activeUniversityProfile();
  const contextSchool = profile.school_name;
  const shortName = profile.short_name || contextSchool.replace(/大學$/, "");
  const label = $("#school-switcher-label");
  if (label) label.textContent = selected || "選擇就讀學校";
  const mobileLabel = $("#mobile-school-label");
  if (mobileLabel) mobileLabel.textContent = selected || `${shortName}資料預覽`;
  const overviewContext = $("#overview-school-context");
  if (overviewContext) {
    overviewContext.textContent = selected ? `${contextSchool} · 個人化交換資訊` : `目前公開資料 · ${contextSchool}預覽`;
  }
  document.querySelectorAll("[data-home-school-name]").forEach((item) => { item.textContent = contextSchool; });
  document.querySelectorAll("[data-home-school-short]").forEach((item) => { item.textContent = shortName; });
  document.querySelectorAll("[data-home-school-board]").forEach((item) => { item.textContent = `${contextSchool}板`; });
  document.querySelectorAll("[data-home-school-discussion]").forEach((item) => { item.textContent = `${shortName}討論板`; });
  document.querySelectorAll("[data-home-school-link]").forEach((item) => { item.href = `#board=${encodeURIComponent(contextSchool)}`; });
  document.querySelectorAll("[data-home-school-follow]").forEach((item) => {
    item.dataset.followBoard = contextSchool;
    item.setAttribute("aria-label", `追蹤${contextSchool}板`);
  });
  document.querySelectorAll("[data-home-school-advisor-question]").forEach((item) => {
    item.dataset.advisorQuestion = `${contextSchool}交換申請的語言門檻是什麼？`;
  });
  const hero = $("#university-hero-image");
  if (hero) {
    hero.src = profile.hero_image || "/static/assets/cgu-campus.jpg";
    hero.alt = `${contextSchool}校園`;
  }
  const featuredImage = $("#featured-home-school-image");
  if (featuredImage) {
    featuredImage.src = profile.hero_image || "/static/assets/cgu-campus.jpg";
    featuredImage.alt = `${contextSchool}校園`;
  }
  const featuredDescription = $("#featured-home-school-description");
  if (featuredDescription) featuredDescription.textContent = `${shortName}學生的交換申請資訊與討論。`;
  document.querySelectorAll(".university-sidebar-nav, .university-mobile-nav").forEach((item) => {
    item.setAttribute("aria-label", `${contextSchool}板功能導覽`);
  });
  populateGlobalCommunitySchools();
  renderBoardFollowControls();
}

async function refreshHomeUniversityData() {
  const requestedSchool = activeHomeSchool();
  const requestId = ++state.homeSchoolRequestId;
  await Promise.all([
    loadDashboard({ homeSchool: requestedSchool }),
    loadApplicationTemplates({ homeSchool: requestedSchool }),
    loadCoverage({ homeSchool: requestedSchool }),
  ]);
  if (requestId !== state.homeSchoolRequestId || !isCurrentHomeSchool(requestedSchool)) return;
  applyAppRoute({ loadFeed: false, resetScroll: false });
  if (document.body.classList.contains("cgu-community-mode")) await loadGlobalCommunity();
  announce(`${activeHomeSchool()}資料已切換`, "success");
}

function initializeSchoolOnboarding() {
  let skippedForSession = false;
  try {
    skippedForSession = window.sessionStorage.getItem("exchange-guide-browse-first") === "1";
  } catch (_) {
    skippedForSession = false;
  }
  if (!state.homeSchool && !skippedForSession) openSchoolOnboarding();
}

async function fetchJson(url, options = {}) {
  const authHeaders = state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {};
  const response = await fetch(url, {
    ...options,
    cache: options.cache || "no-store",
    credentials: "same-origin",
    headers: { Accept: "application/json", ...authHeaders, ...(options.headers || {}) },
  });
  const data = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.detail || `伺服器回應 ${response.status}`);
  return data;
}

function storeAuthToken(token = "") {
  state.authToken = token;
  try {
    if (token) window.localStorage.setItem(STORAGE_KEYS.authToken, token);
    else window.localStorage.removeItem(STORAGE_KEYS.authToken);
  } catch (_) {
    // The secure cookie can still keep the session active.
  }
}

async function loadAuthProviders() {
  try {
    state.authProviders = await fetchJson("/auth/providers");
  } catch (_) {
    state.authProviders = [
      { provider: "email", enabled: true },
      { provider: "google", enabled: false },
      { provider: "facebook", enabled: false },
      { provider: "apple", enabled: false },
    ];
  }
  state.authProviders.forEach((provider) => {
    const button = document.querySelector(`[data-oauth-provider="${provider.provider}"]`);
    if (!button) return;
    button.dataset.providerEnabled = String(provider.enabled);
    if (!provider.enabled) button.title = provider.provider === "apple" ? "App 版啟用" : "設定平台金鑰後啟用";
  });
  updateAuthProviderAvailability();
}

function updateAuthProviderAvailability() {
  const needsVerification = state.authMode === "register" && !state.studentVerificationToken;
  document.querySelectorAll("[data-oauth-provider]").forEach((button) => {
    const enabled = button.dataset.providerEnabled === "true";
    button.disabled = !enabled || needsVerification;
    if (needsVerification && enabled) button.title = "先完成學生身分驗證";
    else if (enabled) button.removeAttribute("title");
  });
  const note = $("#oauth-verification-note");
  if (note) note.hidden = !needsVerification;
}

function setAuthMode(mode) {
  state.authMode = mode === "register" ? "register" : "login";
  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.authMode === state.authMode));
  });
  $("#login-form").hidden = state.authMode !== "login";
  $("#register-form").hidden = state.authMode !== "register";
  const title = $("#auth-title");
  if (title) title.textContent = state.authMode === "login" ? "把申請進度帶著走" : "建立你的交換檔案";
  updateAuthProviderAvailability();
}

function clearVerificationPreviews() {
  Object.values(state.verificationPreviewUrls).forEach((url) => URL.revokeObjectURL(url));
  state.verificationPreviewUrls = {};
  ["front", "back"].forEach((side) => {
    const preview = document.querySelector(`[data-card-preview="${side}"]`);
    if (!preview) return;
    preview.classList.remove("has-image");
    preview.innerHTML = side === "front"
      ? '<i data-lucide="scan-line" aria-hidden="true"></i><strong>學生證正面</strong><small>校名、姓名與學號需清楚</small>'
      : '<i data-lucide="credit-card" aria-hidden="true"></i><strong>學生證反面</strong><small>完整拍攝，不裁切卡片邊緣</small>';
  });
  initIcons();
}

function renderStudentCardPreview(input, side) {
  const file = input.files?.[0];
  const preview = document.querySelector(`[data-card-preview="${side}"]`);
  if (!file || !preview) return;
  if (state.verificationPreviewUrls[side]) URL.revokeObjectURL(state.verificationPreviewUrls[side]);
  const url = URL.createObjectURL(file);
  state.verificationPreviewUrls[side] = url;
  preview.classList.add("has-image");
  preview.innerHTML = `<img src="${escapeHtml(url)}" alt="學生證${side === "front" ? "正面" : "反面"}預覽" /><span><i data-lucide="check-circle-2" aria-hidden="true"></i><strong>${escapeHtml(file.name)}</strong><small>點擊可重新拍攝</small></span>`;
  initIcons();
}

function clearStudentCardFiles() {
  $("#student-card-front").value = "";
  $("#student-card-back").value = "";
  clearVerificationPreviews();
}

function resetStudentVerificationFlow() {
  state.studentVerificationToken = "";
  const form = $("#register-form");
  form.reset();
  form.elements.student_verification_token.value = "";
  $("#student-verification-step").hidden = false;
  $("#registration-account-step").hidden = true;
  $("#student-verification-status").textContent = "";
  clearVerificationPreviews();
  updateAuthProviderAvailability();
}

async function verifyStudentCard() {
  const front = $("#student-card-front").files?.[0];
  const back = $("#student-card-back").files?.[0];
  const consent = $("#student-verification-consent").checked;
  const status = $("#student-verification-status");
  const button = $("#verify-student-card");
  if (!front || !back) {
    status.textContent = "請拍攝學生證正面與反面。";
    return;
  }
  if (!consent) {
    status.textContent = "請先同意一次性辨識說明。";
    return;
  }
  const payload = new FormData();
  payload.append("front", front);
  payload.append("back", back);
  payload.append("school_name", activeHomeSchool());
  payload.append("consent", "true");
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  status.textContent = "正在安全辨識，原圖不會保存…";
  try {
    const result = await fetchJson("/auth/student-verification", { method: "POST", body: payload });
    state.studentVerificationToken = result.verification_token;
    $("#register-form").elements.student_verification_token.value = result.verification_token;
    $("#verified-student-label").textContent = `${result.school_name}學生身分已驗證 · ${result.expires_in_minutes} 分鐘內完成註冊`;
    clearStudentCardFiles();
    $("#student-verification-step").hidden = true;
    $("#registration-account-step").hidden = false;
    updateAuthProviderAvailability();
    window.setTimeout(() => $("#registration-account-step input[name='display_name']")?.focus(), 40);
    announce("學生身分已完成初步驗證", "success");
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

function openAuthDialog(mode = "login") {
  setAuthMode(mode);
  state.dialogReturnFocus = document.activeElement;
  $("#auth-dialog").hidden = false;
  document.body.classList.add("account-dialog-open");
  window.setTimeout(() => {
    const form = state.authMode === "login" ? $("#login-form") : $("#register-form");
    form?.querySelector("input")?.focus();
  }, 40);
}

function closeAuthDialog() {
  if (!state.studentVerificationToken) clearStudentCardFiles();
  $("#auth-dialog").hidden = true;
  document.body.classList.remove("account-dialog-open");
  state.dialogReturnFocus?.focus?.();
  state.dialogReturnFocus = null;
}

function openProfileDialog() {
  if (!state.account) {
    openAuthDialog();
    return;
  }
  const form = $("#profile-form");
  form.elements.display_name.value = state.account.display_name || "";
  form.elements.home_university.value = state.account.home_university || activeHomeSchool();
  form.elements.target_countries.value = (state.account.target_countries || []).join("、");
  form.elements.application_stage.value = state.account.application_stage || "exploring";
  $("#profile-email").textContent = state.account.email || "社群帳號";
  renderProfileAvatar();
  state.dialogReturnFocus = document.activeElement;
  $("#profile-dialog").hidden = false;
  document.body.classList.add("account-dialog-open");
  window.setTimeout(() => form.elements.display_name.focus(), 40);
}

function closeProfileDialog() {
  $("#profile-dialog").hidden = true;
  document.body.classList.remove("account-dialog-open");
  state.dialogReturnFocus?.focus?.();
  state.dialogReturnFocus = null;
}

function trapAccountDialogFocus(event) {
  if (event.key !== "Tab") return;
  const dialog = [$("#profile-dialog"), $("#auth-dialog")].find((item) => item && !item.hidden);
  if (!dialog) return;
  const focusable = [...dialog.querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])')]
    .filter((item) => !item.hidden && item.getClientRects().length > 0);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function renderProfileAvatar() {
  const avatar = $("#profile-avatar");
  if (!avatar) return;
  avatar.innerHTML = state.account?.avatar_url
    ? `<img src="${escapeHtml(state.account.avatar_url)}" alt="" referrerpolicy="no-referrer" />`
    : '<i data-lucide="user-round" aria-hidden="true"></i>';
  initIcons();
}

function renderAccountState() {
  const label = $("#account-button-label");
  if (label) label.textContent = state.account?.display_name || "登入";
  const avatar = $(".account-button-avatar");
  if (avatar) {
    avatar.innerHTML = state.account?.avatar_url
      ? `<img src="${escapeHtml(state.account.avatar_url)}" alt="" referrerpolicy="no-referrer" />`
      : '<i data-lucide="user-round" aria-hidden="true"></i>';
  }
  renderProfileAvatar();
  renderBoardFollowControls();
  renderCalendarSync();
  initIcons();
}

function acceptAccountSession(session) {
  state.account = session.profile;
  storeAuthToken(session.access_token || "");
  state.anonymousIdentity = null;
  try {
    window.localStorage.removeItem(STORAGE_KEYS.communityIdentity);
  } catch (_) {
    // The next authenticated community request will replace the old identity.
  }
  renderAccountState();
  loadCalendarSyncStatus();
  closeAuthDialog();
}

async function restoreAccount() {
  try {
    state.account = await fetchJson("/auth/session");
  } catch (_) {
    state.account = null;
    storeAuthToken("");
  }
  renderAccountState();
  await loadCalendarSyncStatus();
  if (window.location.hash === "#auth=success") {
    window.history.replaceState({}, "", "#home");
    if (state.account) announce("登入完成", "success");
  }
}

async function submitAccountForm(form, endpoint) {
  const status = form.id === "register-form"
    ? $("#registration-account-step .form-status")
    : form.querySelector(".form-status");
  const button = form.querySelector('button[type="submit"]');
  const values = new FormData(form);
  const payload = form.id === "register-form"
    ? {
        display_name: values.get("display_name"),
        email: values.get("email"),
        password: values.get("password"),
        student_verification_token: values.get("student_verification_token"),
        accept_terms: values.get("accept_terms") === "on",
      }
    : { email: values.get("email"), password: values.get("password") };
  button.disabled = true;
  status.textContent = "處理中…";
  try {
    const session = await fetchJson(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    acceptAccountSession(session);
    if (form.id === "register-form") resetStudentVerificationFlow();
    else form.reset();
    announce(endpoint.endsWith("register") ? "帳號已建立" : "登入完成", "success");
    await loadGlobalCommunity();
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function saveAccountProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = new FormData(form);
  const status = form.querySelector(".form-status");
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  status.textContent = "儲存中…";
  try {
    state.account = await fetchJson("/auth/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        display_name: values.get("display_name"),
        home_university: values.get("home_university"),
        target_countries: String(values.get("target_countries") || "").split(/[、,，]+/).map((item) => item.trim()).filter(Boolean),
        application_stage: values.get("application_stage"),
      }),
    });
    state.anonymousIdentity = null;
    try {
      window.localStorage.removeItem(STORAGE_KEYS.communityIdentity);
    } catch (_) {}
    renderAccountState();
    renderApplicationJourney();
    status.textContent = "已儲存";
    window.setTimeout(closeProfileDialog, 500);
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function logoutAccount() {
  try {
    await fetchJson("/auth/logout", { method: "POST" });
  } catch (_) {
    // Local logout still completes if the session already expired.
  }
  state.account = null;
  state.anonymousIdentity = null;
  storeAuthToken("");
  try {
    window.localStorage.removeItem(STORAGE_KEYS.communityIdentity);
  } catch (_) {}
  closeProfileDialog();
  renderAccountState();
  await loadGlobalCommunity();
  announce("已登出", "success");
}

async function deleteAccount() {
  if (!window.confirm("刪除後無法復原，確定要刪除帳號嗎？")) return;
  try {
    await fetchJson("/auth/me", { method: "DELETE" });
    state.account = null;
    state.anonymousIdentity = null;
    storeAuthToken("");
    try {
      window.localStorage.removeItem(STORAGE_KEYS.communityIdentity);
    } catch (_) {}
    closeProfileDialog();
    renderAccountState();
    await loadGlobalCommunity();
    announce("帳號已刪除", "success");
  } catch (error) {
    announce(error.message, "error", true);
  }
}

async function loadDashboard({ refreshed = false, homeSchool = activeHomeSchool() } = {}) {
  const requestedSchool = homeSchool;
  setLoadingState();
  try {
    const school = encodeURIComponent(requestedSchool);
    const dashboard = await fetchJson(`/student-dashboard?school=${school}`);
    if (!isCurrentHomeSchool(requestedSchool)) return false;
    state.dashboard = dashboard;
    renderDashboard();
    state.hasLoaded = true;
    if (refreshed) announce("資料已重新整理", "success");
    else clearAnnouncement();
    return true;
  } catch (error) {
    if (!isCurrentHomeSchool(requestedSchool)) return false;
    showLoadError(error);
    return false;
  } finally {
    if (isCurrentHomeSchool(requestedSchool)) setRefreshState(false);
  }
}

function setRefreshState(isLoading) {
  const button = $("#refresh-button");
  button.disabled = isLoading;
  button.classList.toggle("is-loading", isLoading);
  button.setAttribute("aria-busy", String(isLoading));
}

function setLoadingState() {
  setRefreshState(true);
  announce("正在取得最新整理資料…", "loading", true);
  $("#student-summary").innerHTML = `
    <div class="skeleton skeleton-stat"></div>
    <div class="skeleton skeleton-stat"></div>
    <div class="skeleton skeleton-stat"></div>`;
  $("#partner-table").innerHTML = '<div class="skeleton skeleton-table"></div>';
  $("#period-list").innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
  $("#scholarship-list").innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
  $("#documents-list").innerHTML = '<div class="skeleton skeleton-document"></div><div class="skeleton skeleton-document"></div>';
  ["#partner-table", "#period-list", "#scholarship-list", "#documents-list"].forEach((selector) => {
    $(selector).setAttribute("aria-busy", "true");
  });
}

function renderDashboard() {
  const data = state.dashboard;
  const lastChecked = formatDate(data.last_checked);
  const documents = data.document_explanations || data.rule_explanations || [];

  $("#coverage-rate").textContent = String(data.partner_universities.length);
  $("#source-count").textContent = String(data.sources.length);
  $("#last-checked").textContent = lastChecked.slice(0, 10);
  $("#top-updated").textContent = `資料更新：${lastChecked}`;
  $("#task-school-count").textContent = `${data.partner_universities.length} 所已整理`;
  $("#document-count").textContent = `${documents.length} 份`;

  renderSummary();
  renderPersonalPlanSnapshot();
  renderDecisionBrief();
  renderRecommendedMatches();
  renderApplicationJourney();
  renderDeadlinePreview();
  renderApplicationCalendar();
  renderCalendarSync();
  renderDocumentReadiness();
  renderPartnerFilters();
  renderPartnerTable();
  renderFavorites();
  renderDeadlines();
  renderScholarships();
  renderBudgetPlanner();
  renderApplicationCenter();
  renderDocumentFilters();
  renderDocuments();
  renderDocumentWorkspace();
  renderSources();
  renderEligibilityOptions();
  restoreEligibilityForm();
  renderAdvisorForm();
  renderSearchResults();
  updateFavoriteCounts();
  populateGlobalCommunitySchools();
  if (state.account && state.calendarSync?.enabled) syncCalendarEvents({ quiet: true });

  ["#partner-table", "#period-list", "#scholarship-list", "#documents-list"].forEach((selector) => {
    $(selector).setAttribute("aria-busy", "false");
  });
  initIcons();
}

function renderSummary() {
  const data = state.dashboard;
  const documentCount = (data.document_explanations || data.rule_explanations || []).length;
  $("#student-summary").innerHTML = `
    <div class="summary-stat"><strong>${data.partner_universities.length}</strong><span>可查學校</span><small>交換、研修與雙學位</small></div>
    <div class="summary-stat"><strong>${data.application_periods.length}</strong><span>申請時程</span><small>校內與短期課程</small></div>
    <div class="summary-stat"><strong>${documentCount}</strong><span>文件摘要</span><small>要點、表單與同意書</small></div>`;
}

function targetTermLabel(value) {
  return {
    "2027-spring": "2027 春季",
    "2027-fall": "2027 秋季",
    "2028-spring": "2028 春季",
    "2028-fall": "2028 秋季",
  }[value] || "尚未設定";
}

function readinessStatus(documentId) {
  const value = state.documentReadiness[documentId];
  if (value === true || value === "ready") return "ready";
  if (value === "preparing") return "preparing";
  return "todo";
}

function budgetPlanForSchool(schoolName) {
  return schoolName ? state.budgetPlans[schoolName] || null : null;
}

function nextPlanAction() {
  const profile = state.eligibilityProfile;
  const checklist = state.dashboard ? documentChecklistItems() : [];
  const applicationSchool = [...state.applications][0] || "";
  if (!profile) return { icon: "scan-search", title: "完成資格與目標設定", detail: "先填學院、學制與語言成績", href: "#eligibility" };
  if (!state.favorites.size) return { icon: "school", title: "先收藏候選學校", detail: "系統已可依你的條件排序", href: "#partners" };
  if (!state.applications.size) return { icon: "list-plus", title: "選定要申請的學校", detail: `從 ${state.favorites.size} 所收藏中縮小範圍`, href: "#favorites" };
  if (!budgetPlanForSchool(applicationSchool)?.savedAt) return { icon: "calculator", title: "完成交換預算", detail: applicationSchool, href: "#budget" };
  const forms = initialApplicationTemplates();
  if (forms.length) {
    const incompleteForms = forms.filter((template) => !applicationTemplateCompletion(template).ready);
    if (incompleteForms.length) return { icon: "file-pen-line", title: `填寫 ${incompleteForms[0].short_title}`, detail: `校內申請還有 ${incompleteForms.length} 份表單`, href: "#application-center" };
  } else {
    const incomplete = checklist.filter((item) => readinessStatus(item.id) !== "ready");
    if (incomplete.length) return { icon: "folder-check", title: `準備 ${incomplete[0].title}`, detail: `還有 ${incomplete.length} 項送件資料`, href: "#application-center" };
  }
  const deadline = upcomingDeadlines(1)[0];
  return deadline
    ? { icon: "calendar-clock", title: `留意 ${formatShortDate(deadline.date)} 截止`, detail: deadline.title, href: "#calendar" }
    : { icon: "circle-check", title: "申請準備已就緒", detail: "送件前再核對一次官方來源", href: "#calendar" };
}

function hasUnreadDataReview() {
  if (!state.dashboard?.last_checked) return false;
  const checked = new Date(state.dashboard.last_checked).getTime();
  const seen = new Date(state.updateSeenAt || 0).getTime();
  return Number.isFinite(checked) && checked > seen;
}

function markDataReviewSeen() {
  state.updateSeenAt = state.dashboard?.last_checked || new Date().toISOString();
  try {
    window.localStorage.setItem(STORAGE_KEYS.updateSeenAt, state.updateSeenAt);
  } catch (_) {
    // The badge can still update for this session.
  }
  renderPersonalPlanSnapshot();
}

function renderPersonalPlanSnapshot() {
  const container = $("#personal-plan-snapshot");
  if (!container || !state.dashboard) return;
  const profile = state.eligibilityProfile;
  const next = nextPlanAction();
  const unread = hasUnreadDataReview();
  const target = [targetTermLabel(profile?.targetTerm), profile?.preferredCountry].filter((value) => value && value !== "尚未設定").join(" · ") || "尚未設定交換目標";
  container.innerHTML = `
    <article class="plan-snapshot-card target">
      <span class="plan-snapshot-icon"><i data-lucide="goal" aria-hidden="true"></i></span>
      <span><small>我的目標</small><strong>${escapeHtml(target)}</strong><a href="#eligibility">${profile ? "調整條件" : "開始設定"}</a></span>
    </article>
    <article class="plan-snapshot-card next">
      <span class="plan-snapshot-icon"><i data-lucide="${next.icon}" aria-hidden="true"></i></span>
      <span><small>下一步</small><strong>${escapeHtml(next.title)}</strong><a href="${next.href}">${escapeHtml(truncate(next.detail, 44))}</a></span>
    </article>
    <article class="plan-snapshot-card update${unread ? " has-update" : ""}">
      <span class="plan-snapshot-icon"><i data-lucide="${unread ? "bell-dot" : "badge-check"}" aria-hidden="true"></i></span>
      <span><small>${unread ? "有新一輪資料" : "資料已確認"}</small><strong>${escapeHtml(formatDate(state.dashboard.last_checked).slice(0, 10))}</strong>${unread ? '<button type="button" data-mark-update-seen>標記已看過</button>' : '<a href="#deadlines">查看官方期限</a>'}</span>
    </article>`;
  initIcons();
}

function languageThresholdFromPartner(item, languageTest) {
  const text = partnerSummaryPoints(item, "eligibility_points").join(" ");
  const patterns = {
    toeic: /(?:TOEIC|多益)\s*(?:達|至少|總分|成績)?\s*(\d{3})/i,
    ielts: /IELTS\s*(?:總分|overall|達|至少)?\s*(\d(?:\.\d)?)/i,
    toefl: /TOEFL(?:\s*iBT)?\s*(?:總分|達|至少)?\s*(\d{2,3})/i,
    duolingo: /Duolingo\s*(?:達|至少)?\s*(\d{2,3})/i,
  };
  const match = text.match(patterns[languageTest]);
  return match ? Number(match[1]) : null;
}

function partnerMatch(item, profile = state.eligibilityProfile) {
  const reasons = [];
  const risks = [];
  let score = 0;
  if (!profile) {
    const coverage = coverageForSchool(item.school_name);
    score = (coverage?.workflow_status === "completed" ? 20 : 0) + (coverage?.experience_status === "completed" ? 10 : 0) + (destinationProfileForSchool(item.school_name) ? 10 : 0);
    return { score, tone: "setup", label: "設定條件後配對", reasons: ["申請與生活資料已整理"], risks: [] };
  }

  const collegePass = collegeMatches(item.colleges, profile.college);
  const degreePass = degreeMatches(item.degree_levels, profile.degree);
  if (collegePass) { score += 30; reasons.push("符合學院範圍"); } else risks.push("學院範圍不符");
  if (degreePass) { score += 20; reasons.push("符合目前學制"); } else risks.push("學制不符");
  if (profile.preferredCountry && item.country === profile.preferredCountry) { score += 15; reasons.push(`位於優先國家 ${item.country}`); }
  const threshold = languageThresholdFromPartner(item, profile.languageTest);
  if (threshold === null) {
    score += 8;
    risks.push("合作校語言門檻需另查");
  } else if (Number(profile.languageScore) >= threshold) {
    score += 20;
    reasons.push(`目前語言分數達公開門檻 ${threshold}`);
  } else {
    risks.push(`語言分數尚未達公開門檻 ${threshold}`);
  }
  const coverage = coverageForSchool(item.school_name);
  if (coverage?.workflow_status === "completed") { score += 8; reasons.push("申請流程已查核"); }
  if (destinationProfileForSchool(item.school_name)) score += 5;
  if (coverage?.experience_status === "completed") score += 2;
  const blocked = !collegePass || !degreePass || (threshold !== null && Number(profile.languageScore) < threshold);
  return {
    score,
    tone: blocked ? "blocked" : risks.length ? "review" : "strong",
    label: blocked ? "目前不優先" : score >= 78 ? "高度符合" : "值得查看",
    reasons: reasons.slice(0, 3),
    risks: risks.slice(0, 2),
  };
}

function rankedPartners() {
  if (!state.dashboard) return [];
  return state.dashboard.partner_universities
    .map((item) => ({ item, match: partnerMatch(item) }))
    .sort((left, right) => right.match.score - left.match.score || left.item.school_name.localeCompare(right.item.school_name, "zh-Hant"));
}

function renderRecommendedMatches() {
  const container = $("#recommended-match-list");
  if (!container || !state.dashboard) return;
  if (!state.eligibilityProfile) {
    container.innerHTML = `<div class="match-empty"><i data-lucide="scan-search" aria-hidden="true"></i><span><strong>先填一次基本條件</strong><small>系統才會把 ${state.dashboard.partner_universities.length} 所學校依符合程度排序。</small></span><a class="primary-button" href="#eligibility">開始配對</a></div>`;
    initIcons();
    return;
  }
  const matches = rankedPartners().filter(({ match }) => match.tone !== "blocked").slice(0, 3);
  container.innerHTML = matches.map(({ item, match }, index) => `
    <article class="recommended-match-card ${match.tone}">
      ${renderSchoolPhoto(item, "match")}
      <div class="recommended-match-copy">
        <span class="match-rank">${index + 1}</span><span class="match-label">${escapeHtml(match.label)}</span>
        <strong>${escapeHtml(item.school_name)}</strong><small>${escapeHtml(item.country || "未標示國家")}</small>
        <ul>${match.reasons.slice(0, 2).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
        ${match.risks[0] ? `<p><i data-lucide="info" aria-hidden="true"></i>${escapeHtml(match.risks[0])}</p>` : ""}
        <button type="button" class="text-action school-detail-trigger" data-school-name="${escapeHtml(item.school_name)}">查看學校<i data-lucide="arrow-right" aria-hidden="true"></i></button>
      </div>
    </article>`).join("");
  initIcons();
}

function renderApplicationJourney() {
  const container = $("#application-journey-steps");
  if (!container) return;
  const checklist = state.dashboard ? documentChecklistItems() : [];
  const forms = initialApplicationTemplates();
  const completedForms = forms.filter((template) => applicationTemplateCompletion(template).ready).length;
  const documentDone = forms.length
    ? completedForms === forms.length
    : checklist.length > 0 && checklist.every((item) => readinessStatus(item.id) === "ready");
  const stage = state.account?.application_stage || "";
  const applicationSchool = [...state.applications][0] || "";
  const steps = [
    {
      icon: "shield-check",
      label: "資格與目標",
      detail: state.eligibilityProfile ? targetTermLabel(state.eligibilityProfile.targetTerm) : "檢查成績、語言與學期",
      complete: Boolean(state.eligibilityProfile),
    },
    {
      icon: "search",
      label: "選定學校",
      detail: state.applications.size ? `申請 ${state.applications.size} 所` : state.favorites.size ? `已收藏 ${state.favorites.size} 所` : "比較適合的選項",
      complete: state.applications.size > 0,
    },
    {
      icon: "calculator",
      label: "預算與補助",
      detail: budgetPlanForSchool(applicationSchool)?.savedAt ? "已完成成本估算" : "估算生活費與補助",
      complete: Boolean(budgetPlanForSchool(applicationSchool)?.savedAt),
    },
    {
      icon: "files",
      label: "準備文件",
      detail: documentDone ? "校內表單可列印" : forms.length ? `${completedForms} / ${forms.length} 份可列印` : "整理申請資料",
      complete: documentDone || ["submitted", "accepted", "abroad", "returned"].includes(stage),
    },
    {
      icon: "send",
      label: "送出申請",
      detail: ["submitted", "accepted", "abroad", "returned"].includes(stage) ? "已完成送件" : "校內甄選與合作校",
      complete: ["submitted", "accepted", "abroad", "returned"].includes(stage),
    },
  ];
  const firstIncomplete = steps.findIndex((item) => !item.complete);
  const currentIndex = firstIncomplete >= 0 ? firstIncomplete : steps.length - 1;
  container.innerHTML = steps.map((step, index) => `
    <article class="journey-step${step.complete ? " is-complete" : ""}${index === currentIndex ? " is-current" : ""}">
      <span class="journey-step-icon"><i data-lucide="${step.complete ? "check" : step.icon}" aria-hidden="true"></i></span>
      <span><strong>${index + 1}. ${escapeHtml(step.label)}</strong><small>${escapeHtml(step.detail)}</small></span>
    </article>`).join("");
  initIcons();
}

function renderDecisionBrief() {
  const documents = state.dashboard.document_explanations || state.dashboard.rule_explanations || [];
  const recentRule = documents[0];
  const profile = state.eligibilityProfile;
  const eligibility = eligibilitySummary();
  const deadlines = upcomingDeadlines();
  const checklist = documentChecklistItems();
  const missingDocuments = checklist.filter((item) => !state.documentReadiness[item.id]);
  const applicationCount = state.applications.size;
  const items = [
    {
      icon: "calendar-clock",
      tone: "deadline",
      label: "近期截止",
      value: deadlines.length ? `${deadlines.length} 個期限要留意` : "目前沒有可推算期限",
      detail: deadlines[0] ? `${formatShortDate(deadlines[0].date)} · ${deadlines[0].title}` : "日期無法辨識時會保留官方原文，不自行猜測。",
      href: "#deadline-preview-title",
      action: "查看最近三個",
    },
    {
      icon: "school",
      tone: "school",
      label: "目前可優先查看",
      value: profile ? `${eligibility.likely} 間通過基本篩選` : "先完成資格初判",
      detail: profile ? `另有 ${eligibility.review} 間需確認學院、學制或語言條件。` : "輸入學院、學制、成績與語言分數後，縮小合作校範圍。",
      href: profile ? "#partners" : "#eligibility",
      action: profile ? "查看學校" : "開始初判",
    },
    {
      icon: "user-round-check",
      tone: "eligibility",
      label: "你的資格",
      value: eligibility.qualificationLabel,
      detail: profile ? `${profile.college} · ${profile.degree} · ${profile.languageLabel}` : "填一次資料，之後每間學校都會顯示初判狀態。",
      href: "#eligibility",
      action: profile ? "更新資料" : "開始檢查",
    },
    {
      icon: "files",
      tone: "document",
      label: "尚未準備的文件",
      value: checklist.length ? `${missingDocuments.length} / ${checklist.length} 項待完成` : "文件項目待整理",
      detail: checklist.length ? (missingDocuments[0]?.title || "目前列出的文件都已勾選完成。") : "先查看官方文件摘要與適用條件。",
      href: "#document-readiness-title",
      action: "打開準備清單",
    },
    {
      icon: "bookmark-check",
      tone: "application",
      label: "收藏與申請清單",
      value: `${state.favorites.size} 間收藏 · ${applicationCount} 間申請`,
      detail: applicationCount ? "從學校詳細頁繼續追蹤資格、文件與送件進度。" : "先收藏比較，再把確定的學校加入申請清單。",
      href: "#favorites",
      action: "查看候選學校",
    },
    {
      icon: "file-clock",
      tone: "rule",
      label: "最近更新的重要規定",
      value: recentRule?.title || "尚無文件摘要",
      detail: recentRule ? truncate(recentRule.summary, 72) : `${documents.length} 份文件待查核`,
      href: "#documents",
      action: "查看文件重點",
    },
  ];
  const conciseItems = [items[0], items[3], items[5]];
  $("#decision-brief-grid").innerHTML = conciseItems
    .map(
      (item) => `
        <article class="decision-brief-card ${item.tone}">
          <div class="decision-card-icon"><i data-lucide="${item.icon}" aria-hidden="true"></i></div>
          <span>${escapeHtml(item.label)}</span>
          <h3>${escapeHtml(item.value)}</h3>
          <p>${highlightHtml(item.detail)}</p>
          <a href="${item.href}"><span>${escapeHtml(item.action)}</span><i data-lucide="arrow-right" aria-hidden="true"></i></a>
        </article>`
    )
    .join("");
  initIcons();
}

function eligibilitySummary() {
  if (!state.dashboard || !state.eligibilityProfile) {
    return { likely: 0, review: state.dashboard?.partner_universities.length || 0, qualificationLabel: "尚未進行資格初判" };
  }
  const statuses = state.dashboard.partner_universities.map((item) => partnerMatch(item));
  const likely = statuses.filter((status) => status.tone !== "blocked").length;
  const review = statuses.length - likely;
  const profile = state.eligibilityProfile;
  const threshold = languageThreshold(profile.languageTest);
  const academicPass = profile.academicScore >= academicMinimum();
  const languagePass = threshold ? profile.languageScore >= threshold.minimum : false;
  return {
    likely,
    review,
    qualificationLabel: academicPass && languagePass ? `符合${activeUniversityProfile().short_name}基本門檻` : "仍有基本條件要確認",
  };
}

function dateCandidates(text, { onePerLine = false } = {}) {
  const value = String(text || "");
  const explicitYearMatch = value.match(/(20\d{2})\s*年?/);
  const explicitYear = explicitYearMatch ? Number(explicitYearMatch[1]) : null;
  const matches = [];
  const add = (month, day, index) => {
    const monthValue = Number(month);
    const dayValue = Number(day);
    if (monthValue < 1 || monthValue > 12 || dayValue < 1 || dayValue > 31) return;
    matches.push({ month: monthValue, day: dayValue, index });
  };
  for (const match of value.matchAll(/(\d{1,2})\s*月\s*(\d{1,2})\s*日/g)) add(match[1], match[2], match.index);
  for (const match of value.matchAll(/(?<!\d)(\d{1,2})\s*[\/.\-]\s*(\d{1,2})(?!\d)/g)) add(match[1], match[2], match.index);
  const monthNumbers = { jan: 1, january: 1, feb: 2, february: 2, mar: 3, march: 3, apr: 4, april: 4, may: 5, jun: 6, june: 6, jul: 7, july: 7, aug: 8, august: 8, sep: 9, sept: 9, september: 9, oct: 10, october: 10, nov: 11, november: 11, dec: 12, december: 12 };
  for (const match of value.matchAll(/(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\b/gi)) {
    add(monthNumbers[match[2].toLowerCase()], match[1], match.index);
  }
  const uniqueMatches = [...new Map(matches.map((item) => [`${item.month}-${item.day}-${item.index}`, item])).values()].sort((a, b) => a.index - b.index);
  const selected = onePerLine && uniqueMatches.length ? [uniqueMatches.at(-1)] : uniqueMatches;
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return selected.flatMap((item) => {
    let year = explicitYear || today.getFullYear();
    let date = new Date(year, item.month - 1, item.day);
    if (!explicitYear && date < today) date = new Date(year + 1, item.month - 1, item.day);
    if (explicitYear && date < today) return [];
    return [{ date, original: value }];
  });
}

function upcomingDeadlines(limit = 3) {
  if (!state.dashboard) return [];
  const rows = [];
  (state.dashboard.application_periods || []).forEach((period) => {
    (period.details || []).forEach((detail) => {
      dateCandidates(detail, { onePerLine: true }).forEach((candidate) => rows.push({
        ...candidate,
        title: period.title,
        scope: `${activeHomeSchool()}校內`,
        source: period.source,
      }));
    });
  });
  (state.dashboard.partner_universities || []).forEach((partner) => {
    dateCandidates(partner.application_deadline).forEach((candidate) => rows.push({
      ...candidate,
      title: partner.school_name,
      scope: "合作校公開期限",
      schoolName: partner.school_name,
      source: { source_url: partner.source_url },
    }));
  });
  const seen = new Set();
  return rows
    .sort((a, b) => a.date - b.date)
    .filter((item) => {
      const key = `${item.scope}|${item.title}|${item.date.toISOString().slice(0, 10)}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, limit);
}

function formatShortDate(date) {
  return new Intl.DateTimeFormat("zh-TW", { month: "numeric", day: "numeric" }).format(date);
}

const CALENDAR_CATEGORIES = {
  home: { label: "校內申請", icon: "landmark", tone: "blue" },
  partner: { label: "合作校申請", icon: "school", tone: "teal" },
  documents: { label: "文件準備", icon: "files", tone: "violet" },
  language: { label: "語言考試", icon: "languages", tone: "amber" },
  visa: { label: "簽證", icon: "stamp", tone: "rose" },
  housing: { label: "住宿", icon: "bed-double", tone: "green" },
  other: { label: "其他", icon: "circle-dot", tone: "gray" },
};

function localDateKey(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseLocalDate(value) {
  const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]), 12);
  return Number.isNaN(date.getTime()) ? null : date;
}

function officialCalendarEvents() {
  return upcomingDeadlines(500).map((item) => {
    const date = localDateKey(item.date);
    const scope = item.scope.endsWith("校內") ? "home" : "partner";
    return {
      id: `official-${scope}-${date}-${item.title}`,
      title: item.title,
      date,
      category: scope,
      reminderDays: 7,
      note: item.original || "請在送件前再次核對官方公告。",
      sourceUrl: item.source?.source_url || "",
      origin: "official",
    };
  });
}

function allApplicationCalendarEvents() {
  const combined = [...officialCalendarEvents(), ...state.calendarEvents]
    .filter((event) => parseLocalDate(event.date) && event.title)
    .sort((left, right) => left.date.localeCompare(right.date) || left.title.localeCompare(right.title, "zh-Hant"));
  const seen = new Set();
  return combined.filter((event) => {
    const key = `${event.origin}|${event.title}|${event.date}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function calendarCategory(category) {
  return CALENDAR_CATEGORIES[category] || CALENDAR_CATEGORIES.other;
}

function calendarDaysUntil(dateValue) {
  const target = parseLocalDate(dateValue);
  const today = parseLocalDate(localDateKey());
  return target && today ? Math.round((target - today) / 86400000) : null;
}

function calendarCountdownLabel(dateValue) {
  const days = calendarDaysUntil(dateValue);
  if (days === null) return "日期待確認";
  if (days < 0) return `${Math.abs(days)} 天前`;
  if (days === 0) return "今天";
  if (days === 1) return "明天";
  return `${days} 天後`;
}

function formatCalendarDate(dateValue, options = { month: "numeric", day: "numeric", weekday: "short" }) {
  const date = parseLocalDate(dateValue);
  return date ? new Intl.DateTimeFormat("zh-TW", options).format(date) : dateValue;
}

function calendarEventDescription(event) {
  const lines = [
    event.note || "留學申請時程",
    event.sourceUrl ? `官方來源：${event.sourceUrl}` : "",
    event.origin === "official" ? "提醒：日期可能調整，送件前請再次核對官方公告。" : "",
  ].filter(Boolean);
  return lines.join("\n");
}

function googleCalendarUrl(event) {
  const start = event.date.replaceAll("-", "");
  const endDate = parseLocalDate(event.date);
  endDate.setDate(endDate.getDate() + 1);
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: `[交換申請] ${event.title}`,
    dates: `${start}/${localDateKey(endDate).replaceAll("-", "")}`,
    details: calendarEventDescription(event),
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

function escapeIcs(value) {
  return String(value || "")
    .replaceAll("\\", "\\\\")
    .replaceAll("\n", "\\n")
    .replaceAll(",", "\\,")
    .replaceAll(";", "\\;");
}

function icsEvent(event) {
  const start = event.date.replaceAll("-", "");
  const endDate = parseLocalDate(event.date);
  endDate.setDate(endDate.getDate() + 1);
  const end = localDateKey(endDate).replaceAll("-", "");
  const reminder = Math.max(0, Number(event.reminderDays) || 0);
  const trigger = reminder ? `-P${reminder}D` : "PT0M";
  return [
    "BEGIN:VEVENT",
    `UID:${escapeIcs(event.id)}@exchange-guide.local`,
    `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "")}`,
    `DTSTART;VALUE=DATE:${start}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${escapeIcs(`[交換申請] ${event.title}`)}`,
    `DESCRIPTION:${escapeIcs(calendarEventDescription(event))}`,
    event.sourceUrl ? `URL:${escapeIcs(event.sourceUrl)}` : "",
    "BEGIN:VALARM",
    `TRIGGER:${trigger}`,
    "ACTION:DISPLAY",
    `DESCRIPTION:${escapeIcs(event.title)}`,
    "END:VALARM",
    "END:VEVENT",
  ].filter(Boolean).join("\r\n");
}

function downloadCalendarEvents(events, filename = "exchange-application-calendar.ics") {
  if (!events.length) {
    announce("目前沒有可以匯出的時程。", "error");
    return;
  }
  const content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Exchange Guide Taiwan//Application Calendar//ZH-TW",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    ...events.map(icsEvent),
    "END:VCALENDAR",
  ].join("\r\n");
  const url = URL.createObjectURL(new Blob([content], { type: "text/calendar;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderCalendarEvent(event) {
  const category = calendarCategory(event.category);
  const official = event.origin === "official";
  return `
    <article class="calendar-agenda-item tone-${category.tone}">
      <span class="calendar-agenda-icon"><i data-lucide="${category.icon}" aria-hidden="true"></i></span>
      <div class="calendar-agenda-copy">
        <span class="calendar-agenda-meta"><strong>${escapeHtml(category.label)}</strong><time datetime="${escapeHtml(event.date)}">${escapeHtml(formatCalendarDate(event.date))}</time><small>${escapeHtml(calendarCountdownLabel(event.date))}</small></span>
        <h3>${escapeHtml(event.title)}</h3>
        ${event.note ? `<p>${escapeHtml(truncate(event.note, 100))}</p>` : ""}
        <div class="calendar-agenda-actions">
          <a href="${escapeHtml(googleCalendarUrl(event))}" target="_blank" rel="noreferrer" class="calendar-action-link"><i data-lucide="calendar-plus" aria-hidden="true"></i><span>Google 日曆</span></a>
          <button type="button" class="calendar-action-link" data-download-calendar-event="${escapeHtml(event.id)}"><i data-lucide="download" aria-hidden="true"></i><span>Apple／其他</span></button>
          ${official && event.sourceUrl ? `<a href="${escapeHtml(event.sourceUrl)}" target="_blank" rel="noreferrer" class="calendar-action-link"><i data-lucide="external-link" aria-hidden="true"></i><span>來源</span></a>` : ""}
          ${official ? '<span class="official-event-label"><i data-lucide="badge-check" aria-hidden="true"></i>官方日期</span>' : `<button type="button" class="calendar-action-link danger" data-delete-calendar-event="${escapeHtml(event.id)}"><i data-lucide="trash-2" aria-hidden="true"></i><span>刪除</span></button>`}
        </div>
      </div>
    </article>`;
}

function renderApplicationCalendar() {
  const grid = $("#application-calendar-grid");
  if (!grid || !state.dashboard) return;
  const events = allApplicationCalendarEvents();
  const currentMonth = state.calendarMonth;
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const firstDay = new Date(year, month, 1);
  const gridStart = new Date(year, month, 1 - firstDay.getDay());
  const today = localDateKey();
  if (!parseLocalDate(state.calendarSelectedDate)) state.calendarSelectedDate = today;
  const eventMap = new Map();
  events.forEach((event) => {
    if (!eventMap.has(event.date)) eventMap.set(event.date, []);
    eventMap.get(event.date).push(event);
  });
  $("#calendar-month-label").textContent = new Intl.DateTimeFormat("zh-TW", { year: "numeric", month: "long" }).format(currentMonth);
  grid.innerHTML = Array.from({ length: 42 }, (_, index) => {
    const date = new Date(gridStart);
    date.setDate(gridStart.getDate() + index);
    const key = localDateKey(date);
    const dayEvents = eventMap.get(key) || [];
    const tones = dayEvents.slice(0, 3).map((event) => `<i class="calendar-event-dot tone-${calendarCategory(event.category).tone}"></i>`).join("");
    const outside = date.getMonth() !== month;
    const label = `${formatCalendarDate(key, { year: "numeric", month: "long", day: "numeric" })}${dayEvents.length ? `，${dayEvents.length} 個時程` : ""}`;
    return `<button type="button" role="gridcell" class="calendar-day${outside ? " is-outside" : ""}${key === today ? " is-today" : ""}${key === state.calendarSelectedDate ? " is-selected" : ""}" data-calendar-date="${key}" aria-label="${escapeHtml(label)}" aria-pressed="${key === state.calendarSelectedDate}"><span>${date.getDate()}</span><span class="calendar-event-dots" aria-hidden="true">${tones}</span></button>`;
  }).join("");

  const futureEvents = events.filter((event) => event.date >= today);
  const next = futureEvents[0];
  $("#calendar-next-summary").innerHTML = next
    ? `<span><i data-lucide="timer" aria-hidden="true"></i><strong>${escapeHtml(calendarCountdownLabel(next.date))}</strong><small>${escapeHtml(next.title)}</small></span>`
    : '<span><i data-lucide="calendar-plus" aria-hidden="true"></i><strong>尚未加入任務</strong><small>先建立第一個申請時程</small></span>';

  const selectedEvents = events.filter((event) => event.date === state.calendarSelectedDate);
  const agendaEvents = state.calendarAgendaMode === "selected" ? selectedEvents : futureEvents.slice(0, 6);
  $("#calendar-agenda-date").textContent = state.calendarAgendaMode === "selected"
    ? formatCalendarDate(state.calendarSelectedDate, { month: "long", day: "numeric", weekday: "long" })
    : `未來 ${Math.min(6, futureEvents.length)} 項`;
  $("#calendar-agenda-list").innerHTML = agendaEvents.length
    ? agendaEvents.map(renderCalendarEvent).join("")
    : `<div class="calendar-empty"><i data-lucide="calendar-check" aria-hidden="true"></i><strong>${state.calendarAgendaMode === "selected" ? "這天沒有安排" : "目前沒有近期時程"}</strong><span>點下方「新增自己的申請任務」開始規劃。</span></div>`;
  initIcons();
}

function persistCalendarEvents() {
  try {
    window.localStorage.setItem(STORAGE_KEYS.calendarEvents, JSON.stringify(state.calendarEvents));
  } catch (_) {
    announce("瀏覽器無法保存這個時程。", "error", true);
  }
  if (state.account && state.calendarSync?.enabled) syncCalendarEvents({ quiet: true });
}

function calendarSyncEventsPayload() {
  return allApplicationCalendarEvents().map((event) => ({
    id: String(event.id),
    title: event.title,
    date: event.date,
    category: event.category || "other",
    reminder_days: Number(event.reminderDays) || 0,
    note: event.note || "",
    source_url: event.sourceUrl || null,
    origin: event.origin === "official" ? "official" : "personal",
  }));
}

async function loadCalendarSyncStatus() {
  if (!state.account) {
    state.calendarSync = null;
    renderCalendarSync();
    return;
  }
  state.calendarSyncLoading = true;
  renderCalendarSync();
  try {
    state.calendarSync = await fetchJson("/calendar-sync");
  } catch (_) {
    state.calendarSync = null;
  } finally {
    state.calendarSyncLoading = false;
    renderCalendarSync();
  }
}

function renderCalendarSync() {
  const status = $("#calendar-sync-status");
  const actions = $("#calendar-subscription-actions");
  const summary = $("#calendar-sync-summary");
  if (!status || !actions || !summary) return;
  document.querySelectorAll("[data-calendar-provider]").forEach((button) => {
    const active = button.dataset.calendarProvider === state.calendarProvider;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  if (!state.account) {
    summary.textContent = "登入後可讓第三方日曆持續取得更新";
    status.innerHTML = '<span class="calendar-sync-state-icon"><i data-lucide="log-in" aria-hidden="true"></i></span><span><strong>登入後開啟訂閱同步</strong><small>你在系統新增或修改時程後，訂閱的日曆會持續取得更新。</small></span><button type="button" class="primary-button" data-open-auth>登入</button>';
    actions.replaceChildren();
    initIcons();
    return;
  }
  if (state.calendarSyncLoading) {
    summary.textContent = "正在檢查同步狀態";
    status.innerHTML = '<div class="skeleton skeleton-card"></div>';
    actions.replaceChildren();
    return;
  }
  const sync = state.calendarSync;
  if (!sync?.enabled) {
    summary.textContent = "尚未建立私人訂閱網址";
    status.innerHTML = '<span class="calendar-sync-state-icon"><i data-lucide="calendar-plus" aria-hidden="true"></i></span><span><strong>建立一次，後續自動更新</strong><small>將產生一組只有你能撤銷的私人日曆網址。</small></span><button type="button" class="primary-button" data-enable-calendar-sync>建立同步連結</button>';
    actions.replaceChildren();
    initIcons();
    return;
  }
  summary.textContent = `已同步 ${sync.event_count || 0} 項時程`;
  status.innerHTML = `<span class="calendar-sync-state-icon connected"><i data-lucide="calendar-check-2" aria-hidden="true"></i></span><span><strong>訂閱同步已開啟</strong><small>${sync.last_synced_at ? `最近同步 ${escapeHtml(formatDate(sync.last_synced_at))}` : "等待第一次同步"}</small></span><button type="button" class="secondary-button" data-calendar-sync-now><i data-lucide="refresh-cw" aria-hidden="true"></i><span>立即同步</span></button>`;
  const provider = state.calendarProvider;
  const providerCopy = {
    google: ["Google 日曆", "https://calendar.google.com/calendar/u/0/r/settings/addbyurl", "開啟 Google 設定"],
    apple: ["Apple 行事曆", sync.webcal_url || sync.subscription_url, "加入 Apple 行事曆"],
    outlook: ["Outlook", "https://outlook.live.com/calendar/0/addcalendar", "開啟 Outlook 設定"],
  }[provider];
  actions.innerHTML = `
    <div><span><strong>${escapeHtml(providerCopy[0])}</strong><small>${provider === "apple" ? "點一下即可訂閱" : "開啟設定後，選擇從網址訂閱並貼上私人連結"}</small></span><div><button type="button" class="secondary-button" data-copy-calendar-url><i data-lucide="copy" aria-hidden="true"></i><span>複製訂閱網址</span></button><a class="primary-button" href="${escapeHtml(providerCopy[1])}" target="_blank" rel="noreferrer"><span>${escapeHtml(providerCopy[2])}</span><i data-lucide="external-link" aria-hidden="true"></i></a></div></div>
    <button type="button" class="text-action danger" data-revoke-calendar-sync><i data-lucide="unlink" aria-hidden="true"></i><span>撤銷同步網址</span></button>`;
  initIcons();
}

async function enableCalendarSync() {
  if (!state.account) {
    openAuthDialog();
    return;
  }
  state.calendarSyncLoading = true;
  renderCalendarSync();
  try {
    state.calendarSync = await fetchJson("/calendar-sync/enable", { method: "POST" });
    await syncCalendarEvents({ quiet: true });
    announce("日曆同步連結已建立", "success");
  } catch (error) {
    announce(error.message, "error", true);
  } finally {
    state.calendarSyncLoading = false;
    renderCalendarSync();
  }
}

async function syncCalendarEvents({ quiet = false } = {}) {
  if (!state.account) return;
  try {
    state.calendarSync = await fetchJson("/calendar-sync/events", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: calendarSyncEventsPayload() }),
    });
    renderCalendarSync();
    if (!quiet) announce(`已同步 ${state.calendarSync.event_count || 0} 項時程`, "success");
  } catch (error) {
    if (!quiet) announce(error.message, "error", true);
  }
}

async function revokeCalendarSync() {
  if (!window.confirm("撤銷後，原本訂閱網址將失效。確定要繼續嗎？")) return;
  try {
    state.calendarSync = await fetchJson("/calendar-sync", { method: "DELETE" });
    renderCalendarSync();
    announce("同步網址已撤銷", "success");
  } catch (error) {
    announce(error.message, "error", true);
  }
}

async function copyCalendarSubscriptionUrl() {
  const url = state.calendarSync?.subscription_url;
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    announce("訂閱網址已複製", "success");
  } catch (_) {
    window.prompt("複製這組私人訂閱網址", url);
  }
}

function addCalendarEvent(form) {
  const values = new FormData(form);
  const title = String(values.get("title") || "").trim();
  const date = String(values.get("date") || "");
  const status = form.querySelector(".form-status");
  if (!title || !parseLocalDate(date)) {
    status.textContent = "請填寫任務名稱與日期。";
    return;
  }
  const id = window.crypto?.randomUUID?.() || `event-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  state.calendarEvents.push({
    id,
    title,
    date,
    category: String(values.get("category") || "other"),
    reminderDays: Number(values.get("reminder_days") || 0),
    note: String(values.get("note") || "").trim(),
    origin: "personal",
  });
  state.calendarSelectedDate = date;
  state.calendarAgendaMode = "selected";
  state.calendarMonth = new Date(parseLocalDate(date).getFullYear(), parseLocalDate(date).getMonth(), 1);
  persistCalendarEvents();
  form.reset();
  form.elements.date.value = date;
  status.textContent = "已加入你的申請日曆。";
  renderApplicationCalendar();
  announce("申請任務已加入", "success");
}

function deleteCalendarEvent(eventId) {
  const event = state.calendarEvents.find((item) => item.id === eventId);
  if (!event || !window.confirm(`刪除「${event.title}」？`)) return;
  state.calendarEvents = state.calendarEvents.filter((item) => item.id !== eventId);
  persistCalendarEvents();
  renderApplicationCalendar();
}

function renderDeadlinePreview() {
  const container = $("#deadline-preview-list");
  if (!container) return;
  const deadlines = upcomingDeadlines();
  if (!deadlines.length) {
    container.innerHTML = '<p class="workspace-empty">目前沒有可安全推算的未來日期，請以官方公告原文為準。</p>';
    return;
  }
  container.innerHTML = deadlines.map((item) => `
    <div class="deadline-preview-row">
      <time datetime="${item.date.toISOString().slice(0, 10)}"><strong>${escapeHtml(formatShortDate(item.date))}</strong><span>${escapeHtml(String(item.date.getFullYear()))}</span></time>
      <button type="button" class="deadline-preview-link ${item.schoolName ? "school-detail-trigger" : ""}" ${item.schoolName ? `data-school-name="${escapeHtml(item.schoolName)}"` : ""}>
        <span class="deadline-scope">${escapeHtml(item.scope)}</span><strong>${escapeHtml(item.title)}</strong>
      </button>
    </div>`).join("");
}

function documentChecklistItems() {
  if (!state.dashboard) return [];
  const items = [];
  (state.dashboard.required_documents || []).forEach((group) => {
    (group.details || []).forEach((detail) => {
      const separator = detail.search(/[：:]/);
      if (separator < 1 || separator > 42) return;
      const title = detail.slice(0, separator).trim();
      if (!/申請表|切結書|通報單|同意書|證明|文件/.test(title)) return;
      const conditional = /才須|役男|如適用|若|身分/.test(detail);
      const id = normalize(title).replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-");
      if (!items.some((item) => item.id === id)) items.push({ id, title, detail, conditional });
    });
  });
  return items.slice(0, 6);
}

function renderDocumentReadiness() {
  const container = $("#document-readiness-list");
  if (!container) return;
  const items = documentChecklistItems();
  if (!items.length) {
    container.innerHTML = '<p class="workspace-empty">目前沒有可建立清單的明確文件名稱，請查看文件庫。</p>';
    return;
  }
  const completed = items.filter((item) => readinessStatus(item.id) === "ready").length;
  container.innerHTML = `
    <div class="document-progress"><strong>${completed} / ${items.length} 已準備</strong><span>${items.filter((item) => readinessStatus(item.id) === "preparing").length} 項準備中</span></div>
    <div class="document-checklist">${items.map((item) => `
      <label>
        <input type="checkbox" class="document-readiness-checkbox" data-document-id="${escapeHtml(item.id)}" ${readinessStatus(item.id) === "ready" ? "checked" : ""} />
        <span><strong>${escapeHtml(item.title)}</strong>${item.conditional ? "<small>符合特定身分時才需要</small>" : ""}</span>
      </label>`).join("")}</div>`;
}

function updateDocumentReadiness(documentId, checked) {
  if (!documentId) return;
  state.documentReadiness[documentId] = checked ? "ready" : "todo";
  persistDocumentReadiness();
}

function updateDocumentStatus(documentId, status) {
  if (!documentId || !["todo", "preparing", "ready"].includes(status)) return;
  state.documentReadiness[documentId] = status;
  persistDocumentReadiness();
}

function persistDocumentReadiness() {
  try {
    window.localStorage.setItem(STORAGE_KEYS.documents, JSON.stringify(state.documentReadiness));
  } catch (_) {
    // Checklist remains available for this session.
  }
  renderDocumentReadiness();
  renderDocumentWorkspace();
  renderDecisionBrief();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
}

function renderDocumentWorkspace() {
  const container = $("#document-workspace-list");
  const progress = $("#document-workspace-progress");
  if (!container || !state.dashboard) return;
  const items = documentChecklistItems();
  if (!items.length) {
    container.innerHTML = '<p class="workspace-empty">目前沒有可追蹤的明確送件文件。</p>';
    if (progress) progress.textContent = "0 項";
    return;
  }
  const ready = items.filter((item) => readinessStatus(item.id) === "ready").length;
  const preparing = items.filter((item) => readinessStatus(item.id) === "preparing").length;
  if (progress) progress.textContent = `${ready} / ${items.length} 完成${preparing ? ` · ${preparing} 準備中` : ""}`;
  container.innerHTML = items.map((item) => `
    <article class="document-workspace-row status-${readinessStatus(item.id)}">
      <span class="document-workspace-icon"><i data-lucide="${readinessStatus(item.id) === "ready" ? "file-check-2" : readinessStatus(item.id) === "preparing" ? "file-clock" : "file"}" aria-hidden="true"></i></span>
      <details><summary><span><strong>${escapeHtml(item.title)}</strong>${item.conditional ? "<small>符合特定身分時才需要</small>" : ""}</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><p>${highlightHtml(item.detail)}</p></details>
      <label><span class="visually-hidden">${escapeHtml(item.title)}準備狀態</span><select data-document-status="${escapeHtml(item.id)}"><option value="todo" ${readinessStatus(item.id) === "todo" ? "selected" : ""}>未開始</option><option value="preparing" ${readinessStatus(item.id) === "preparing" ? "selected" : ""}>準備中</option><option value="ready" ${readinessStatus(item.id) === "ready" ? "selected" : ""}>已完成</option></select></label>
    </article>`).join("");
  initIcons();
}

function applicationValue(template, field) {
  if (field.reusable_profile_key) {
    const remembered = state.applicationProfile?.[field.reusable_profile_key];
    if (applicationValuePresent(remembered)) return remembered;
  }
  const answer = state.applicationAnswers?.[template.id]?.[field.id];
  if (applicationValuePresent(answer)) return answer;
  return answer ?? "";
}

function applicationValuePresent(value) {
  if (value === null || value === undefined || value === false) return false;
  if (typeof value === "string") return Boolean(value.trim());
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.keys(value).length > 0;
  return true;
}

function sanitizeApplicationProfileForMemory(profile) {
  if (!profile || Array.isArray(profile) || typeof profile !== "object") return {};
  return Object.fromEntries(
    Object.entries(profile).filter(([key, value]) => (
      APPLICATION_PERSISTENT_PROFILE_KEYS.has(key) && applicationValuePresent(value)
    )),
  );
}

function stripReusableApplicationAnswers() {
  Object.values(state.applicationAnswers || {}).forEach((documentAnswers) => {
    if (!documentAnswers || Array.isArray(documentAnswers) || typeof documentAnswers !== "object") return;
    APPLICATION_REUSABLE_PROFILE_KEYS.forEach((key) => {
      const value = documentAnswers[key];
      if (!applicationValuePresent(state.applicationProfile[key]) && applicationValuePresent(value)) {
        state.applicationProfile[key] = value;
      }
      delete documentAnswers[key];
    });
  });
}

function rememberedApplicationProfileCount() {
  return Object.keys(sanitizeApplicationProfileForMemory(state.applicationProfile)).length;
}

function persistApplicationProfileMemory() {
  try {
    if (!state.applicationProfileMemoryEnabled) {
      window.localStorage.removeItem(STORAGE_KEYS.applicationProfileMemory);
      window.localStorage.removeItem(STORAGE_KEYS.applicationProfileMemoryEnabled);
      return;
    }
    window.localStorage.setItem(STORAGE_KEYS.applicationProfileMemoryEnabled, "true");
    window.localStorage.setItem(
      STORAGE_KEYS.applicationProfileMemory,
      JSON.stringify(sanitizeApplicationProfileForMemory(state.applicationProfile)),
    );
  } catch (_) {
    // Session memory remains available when browser storage is blocked.
  }
}

function updateApplicationMemoryControls() {
  const toggle = $("#application-remember-profile");
  const clear = $("#clear-application-profile-memory");
  const status = $("#application-profile-memory-status");
  if (toggle) toggle.checked = state.applicationProfileMemoryEnabled;
  if (clear) clear.disabled = !state.applicationProfileMemoryEnabled;
  if (status) {
    const count = rememberedApplicationProfileCount();
    status.textContent = state.applicationProfileMemoryEnabled
      ? `已記住 ${count} 欄`
      : "僅保留本次使用";
  }
}

function setApplicationProfileMemory(enabled) {
  state.applicationProfileMemoryEnabled = Boolean(enabled);
  persistApplicationDraft();
  updateApplicationMemoryControls();
  announce(
    state.applicationProfileMemoryEnabled
      ? "已開啟裝置記憶，敏感證件欄位不會長期儲存"
      : "已關閉並清除這台裝置的表單記憶",
    "success",
  );
}

function clearApplicationProfileMemory() {
  state.applicationProfileMemoryEnabled = false;
  persistApplicationProfileMemory();
  updateApplicationMemoryControls();
  announce("已清除裝置記憶；目前分頁中的資料仍會保留", "success");
}

function rememberApplicationField(template, input) {
  const fieldId = input?.dataset?.applicationField;
  const field = template?.fields?.find((item) => item.id === fieldId);
  if (!field?.reusable_profile_key || field.field_type === "files") return;
  const value = field.field_type === "checkbox" ? Boolean(input.checked) : String(input.value || "").trim();
  if (applicationValuePresent(value)) state.applicationProfile[field.reusable_profile_key] = value;
  else delete state.applicationProfile[field.reusable_profile_key];
  if (state.applicationAnswers[template.id]) delete state.applicationAnswers[template.id][field.id];
  persistApplicationDraft();
  restoreApplicationProfileForm();
  renderApplicationAutofillStatus(template);
}

function applicationTemplateById(templateId) {
  return state.applicationTemplates.find((template) => template.id === templateId) || null;
}

function initialApplicationTemplates() {
  const stage = state.applicationContext.program_type === "short_term_credit" ? "短期課程申請" : "校內申請";
  return state.applicationTemplates.filter((template) => template.stage === stage);
}

function applicationFieldHasValue(template, field) {
  const value = applicationValue(template, field);
  if (field.field_type !== "files") return applicationValuePresent(value);
  const files = state.applicationFiles?.[template.id]?.[field.id] || [];
  const validFiles = files.filter((item) => typeof item?.data_url === "string" && item.data_url.startsWith("data:"));
  const minimum = Math.max(Number(field.min_files) || 0, field.required ? 1 : 0);
  return validFiles.length >= minimum;
}

function applicationTemplateCompletion(template) {
  const required = template.fields.filter((field) => field.required);
  if (!required.length) return { completed: 0, total: 0, percent: 100, ready: true };
  const completed = required.filter((field) => applicationFieldHasValue(template, field)).length;
  return {
    completed,
    total: required.length,
    percent: Math.round((completed / required.length) * 100),
    ready: completed === required.length,
  };
}

function applicationProfileCompletion() {
  const required = ["student_name_zh", "student_name_en", "student_id", "college", "department", "degree_level", "year_level", "email", "phone"];
  const completed = required.filter((key) => applicationValuePresent(state.applicationProfile[key])).length;
  return { completed, total: required.length, ready: completed === required.length };
}

function persistApplicationContext() {
  try {
    window.localStorage.setItem(STORAGE_KEYS.applicationContext, JSON.stringify(state.applicationContext));
    window.localStorage.setItem(STORAGE_KEYS.applicationSelections, JSON.stringify(state.applicationSelections));
  } catch (_) {
    // The current application setup remains available for this session.
  }
}

function applicationAnswersForSession() {
  const sanitized = JSON.parse(JSON.stringify(state.applicationAnswers || {}));
  Object.values(sanitized).forEach((documentAnswers) => {
    if (!documentAnswers || typeof documentAnswers !== "object") return;
    Object.entries(documentAnswers).forEach(([key, value]) => {
      if (!Array.isArray(value)) return;
      documentAnswers[key] = value.map((item) => (
        item && typeof item === "object"
          ? { name: item.name || "附件", type: item.type || "" }
          : item
      ));
    });
  });
  return sanitized;
}

function persistApplicationDraft() {
  stripReusableApplicationAnswers();
  try {
    window.sessionStorage.setItem(APPLICATION_SESSION_KEYS.profile, JSON.stringify(state.applicationProfile));
    window.sessionStorage.setItem(APPLICATION_SESSION_KEYS.answers, JSON.stringify(applicationAnswersForSession()));
  } catch (_) {
    // Sensitive form data remains in memory and is cleared when the page closes.
  }
  persistApplicationProfileMemory();
  persistApplicationContext();
}

function applicationFlagsFromForm(form) {
  return ["subsidy", "military_service", "full_year"].filter((name) => form.elements[name]?.checked);
}

function readApplicationContextForm() {
  const form = $("#application-context-form");
  if (!form) return state.applicationContext;
  const targetSchool = form.elements.target_school.value;
  const partner = state.dashboard?.partner_universities?.find((item) => item.school_name === targetSchool);
  state.applicationContext = {
    school_name: activeHomeSchool(),
    target_school: targetSchool,
    target_country: partner?.country || "",
    program_type: form.elements.program_type.value || "exchange",
    academic_year: form.elements.academic_year.value.trim(),
    semester: form.elements.semester.value,
    flags: applicationFlagsFromForm(form),
  };
  persistApplicationContext();
  return state.applicationContext;
}

function restoreApplicationContextForm() {
  const form = $("#application-context-form");
  if (!form) return;
  form.elements.program_type.value = state.applicationContext.program_type || "exchange";
  form.elements.academic_year.value = state.applicationContext.academic_year || "";
  form.elements.semester.value = state.applicationContext.semester || "";
  ["subsidy", "military_service", "full_year"].forEach((name) => {
    form.elements[name].checked = (state.applicationContext.flags || []).includes(name);
  });
  renderApplicationTargetSchools();
}

function renderApplicationTargetSchools() {
  const select = $("#application-target-school");
  if (!select || !state.dashboard) return;
  const selected = state.applicationContext.target_school || "";
  const schools = [...state.dashboard.partner_universities]
    .sort((left, right) => `${left.country || ""}${left.school_name}`.localeCompare(`${right.country || ""}${right.school_name}`, "zh-Hant"));
  select.innerHTML = [
    '<option value="">尚未決定</option>',
    ...schools.map((item) => `<option value="${escapeHtml(item.school_name)}">${escapeHtml(item.country || "未標示國家")} · ${escapeHtml(item.school_name)}</option>`),
  ].join("");
  select.value = schools.some((item) => item.school_name === selected) ? selected : "";
}

function restoreApplicationProfileForm() {
  const form = $("#application-profile-form");
  if (!form) return;
  [...form.elements].forEach((input) => {
    if (!input.name || input.type === "submit") return;
    input.value = state.applicationProfile[input.name] || (input.name === "email" ? state.account?.email || "" : "");
  });
  const completion = applicationProfileCompletion();
  const summary = $("#application-profile-summary");
  if (summary) {
    summary.textContent = completion.ready
      ? "共用資料已完成"
      : `${completion.completed} / ${completion.total} 欄已填`;
  }
  updateApplicationMemoryControls();
}

function initializeApplicationSelections() {
  state.applicationTemplates.forEach((template) => {
    const existing = state.applicationSelections[template.id] || {};
    state.applicationSelections[template.id] = {
      selected: Boolean(existing.selected),
      copies: Number(existing.copies) || template.default_copies,
      status: existing.status || "draft",
    };
  });
  persistApplicationContext();
}

async function loadApplicationTemplates({ homeSchool = activeHomeSchool() } = {}) {
  const requestedSchool = homeSchool;
  const container = $("#application-template-list");
  if (container) container.innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
  state.applicationLoading = true;
  try {
    const context = state.applicationContext;
    const params = new URLSearchParams({
      school: requestedSchool,
      program_type: context.program_type || "exchange",
    });
    if (context.flags?.length) params.set("flags", context.flags.join(","));
    const templates = await fetchJson(`/application-center/templates?${params}`);
    if (!isCurrentHomeSchool(requestedSchool)) return false;
    state.applicationTemplates = templates;
    initializeApplicationSelections();
    renderApplicationCenter();
    renderApplicationJourney();
    renderPersonalPlanSnapshot();
    const active = applicationTemplateById(state.activeApplicationTemplateId);
    if (active && window.location.hash.startsWith("#application-form=")) renderApplicationFormPage(active);
    return true;
  } catch (error) {
    if (!isCurrentHomeSchool(requestedSchool)) return false;
    if (container) renderEmpty("#application-template-list", "暫時無法取得申請文件", error.message);
    return false;
  } finally {
    if (isCurrentHomeSchool(requestedSchool)) state.applicationLoading = false;
  }
}

function applicationStageGroups() {
  const groups = [];
  state.applicationTemplates.forEach((template) => {
    let group = groups.find((item) => item.stage === template.stage);
    if (!group) {
      group = { stage: template.stage, templates: [] };
      groups.push(group);
    }
    group.templates.push(template);
  });
  return groups;
}

function renderApplicationTemplateCard(template) {
  const completion = applicationTemplateCompletion(template);
  const selected = state.applicationSelections[template.id]?.selected;
  return `
    <article class="application-template-card ${completion.ready ? "is-complete" : ""}">
      <span class="application-template-icon"><i data-lucide="${APPLICATION_STAGE_ICONS[template.stage] || "file-text"}" aria-hidden="true"></i></span>
      <div class="application-template-copy">
        <span class="application-template-meta"><span>${escapeHtml(template.category)}</span>${template.official_layout ? "<em>官方格式</em>" : ""}<span class="application-document-status status-${escapeHtml(applicationDocumentStatus(template.id))}">${escapeHtml(applicationDocumentStatusLabel(template.id))}</span>${selected ? "<span>已選取</span>" : ""}</span>
        <strong>${escapeHtml(template.short_title)}</strong>
        <span class="application-template-progress"><span><i style="width:${completion.percent}%"></i></span><b>${completion.percent}%</b><em>${template.default_copies} 份</em></span>
      </div>
      <button type="button" class="application-template-open" data-open-application-template="${escapeHtml(template.id)}" aria-label="填寫${escapeHtml(template.short_title)}"><i data-lucide="chevron-right" aria-hidden="true"></i></button>
    </article>`;
}

function renderApplicationTemplates() {
  const container = $("#application-template-list");
  const count = $("#application-template-count");
  if (!container) return;
  if (count) count.textContent = `${state.applicationTemplates.length} 份`;
  if (!state.applicationTemplates.length) {
    container.innerHTML = '<p class="workspace-empty">目前條件下沒有需要產生的文件。</p>';
    return;
  }
  container.innerHTML = applicationStageGroups().map((group) => `
    <section class="application-template-stage" aria-label="${escapeHtml(group.stage)}">
      <div class="application-template-stage-heading"><strong>${escapeHtml(group.stage)}</strong><small>${group.templates.length} 份</small></div>
      ${group.templates.map(renderApplicationTemplateCard).join("")}
    </section>`).join("");
}

function renderApplicationPacket() {
  const container = $("#application-packet-list");
  const total = $("#application-packet-total");
  const status = $("#application-packet-status");
  const button = $("#download-application-packet");
  if (!container) return;
  container.innerHTML = state.applicationTemplates.map((template) => {
    const selection = state.applicationSelections[template.id] || { selected: false, copies: template.default_copies };
    return `
      <label class="application-packet-row">
        <input type="checkbox" data-application-packet-template="${escapeHtml(template.id)}" ${selection.selected ? "checked" : ""} />
        <span><strong>${escapeHtml(template.short_title)}</strong><small>${escapeHtml(template.stage)} · ${escapeHtml(applicationDocumentStatusLabel(template.id))}</small></span>
        <input class="application-copy-input" type="number" min="1" max="10" value="${selection.copies || template.default_copies}" data-application-copy-template="${escapeHtml(template.id)}" aria-label="${escapeHtml(template.short_title)}列印份數" ${selection.selected ? "" : "disabled"} />
      </label>`;
  }).join("");
  const selectedTemplates = state.applicationTemplates.filter((template) => state.applicationSelections[template.id]?.selected);
  const copies = selectedTemplates.reduce((sum, template) => sum + Number(state.applicationSelections[template.id]?.copies || template.default_copies), 0);
  const incomplete = selectedTemplates.filter((template) => !applicationTemplateCompletion(template).ready);
  if (total) total.textContent = `${copies} 份`;
  if (status) {
    status.className = `application-packet-status ${incomplete.length ? "is-warning" : selectedTemplates.length ? "is-success" : ""}`;
    status.textContent = !selectedTemplates.length
      ? "尚未選取文件"
      : incomplete.length
        ? `${incomplete.length} 份尚未填完`
        : `可產生 ${copies} 份`;
  }
  if (button) button.disabled = !selectedTemplates.length || Boolean(incomplete.length) || state.applicationLoading;
}

function updateApplicationCenterSteps() {
  const steps = [...document.querySelectorAll(".application-center-steps li")];
  if (!steps.length) return;
  const profileReady = applicationProfileCompletion().ready;
  const completedCount = state.applicationTemplates.filter((template) => applicationTemplateCompletion(template).ready).length;
  const selected = state.applicationTemplates.filter((template) => state.applicationSelections[template.id]?.selected);
  const packageReady = selected.length > 0 && selected.every((template) => applicationTemplateCompletion(template).ready);
  [true, profileReady, completedCount > 0, packageReady].forEach((active, index) => steps[index]?.classList.toggle("is-active", active));
}

function renderApplicationCenter() {
  restoreApplicationContextForm();
  restoreApplicationProfileForm();
  renderApplicationTemplates();
  renderApplicationPacket();
  updateApplicationCenterSteps();
  initIcons();
}

function saveApplicationProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!form.reportValidity()) return;
  state.applicationProfile = Object.fromEntries(
    [...new FormData(form).entries()].map(([key, value]) => [key, String(value).trim()])
  );
  persistApplicationDraft();
  renderApplicationCenter();
  announce("共用資料已儲存", "success");
}

async function handleApplicationContextChange() {
  readApplicationContextForm();
  await loadApplicationTemplates();
}

function applicationFieldInput(template, field, inputId = "") {
  const value = applicationValue(template, field);
  const required = field.required ? "required" : "";
  const maxLength = field.max_length ? `maxlength="${field.max_length}"` : "";
  const placeholder = field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : "";
  const common = `id="${escapeHtml(inputId)}" name="${escapeHtml(field.id)}" data-application-field="${escapeHtml(field.id)}" ${required} ${maxLength} ${placeholder}`;
  if (field.field_type === "textarea") {
    return `<textarea ${common}>${escapeHtml(value || "")}</textarea>`;
  }
  if (field.field_type === "select") {
    return `<select ${common}><option value="">請選擇</option>${(field.options || []).map((option) => `<option value="${escapeHtml(option)}" ${String(value) === option ? "selected" : ""}>${escapeHtml(option)}</option>`).join("")}</select>`;
  }
  if (field.field_type === "checkbox") {
    return `<label class="application-checkbox-field"><input type="checkbox" ${common} ${value === true ? "checked" : ""} /><span>${escapeHtml(field.label)}</span></label>`;
  }
  if (field.field_type === "files") {
    const liveFiles = state.applicationFiles?.[template.id]?.[field.id] || [];
    const storedFiles = Array.isArray(value) ? value : [];
    const files = liveFiles.length ? liveFiles : storedFiles;
    const validFiles = liveFiles.filter((file) => typeof file?.data_url === "string" && file.data_url.startsWith("data:"));
    const minimum = Math.max(Number(field.min_files) || 0, field.required ? 1 : 0);
    const fileRequired = validFiles.length < minimum ? "required" : "";
    const accept = field.id.includes("photo") ? "image/jpeg,image/png" : "application/pdf,image/jpeg,image/png";
    const multiple = Number(field.max_files || 1) > 1 ? "multiple" : "";
    return `<label class="application-file-field"><i data-lucide="upload-cloud" aria-hidden="true"></i><strong>${escapeHtml(field.label)}</strong><input type="file" ${common.replace(required, fileRequired)} accept="${accept}" ${multiple} /><small>${escapeHtml(field.help_text || "可選擇 PDF 或圖片")}</small></label><div class="application-file-preview" data-application-file-preview="${escapeHtml(field.id)}">${files.map((file) => `<span>${escapeHtml(file.name || "附件")}</span>`).join("")}</div>`;
  }
  const inputType = ["email", "tel", "date", "number"].includes(field.field_type) ? field.field_type : "text";
  return `<input type="${inputType}" ${common} value="${escapeHtml(value || "")}" ${inputType === "number" ? 'step="any"' : ""} />`;
}

function renderApplicationAutofillStatus(template) {
  const status = $("#application-autofill-status");
  if (!status) return;
  const remembered = template.fields.filter((field) => (
    field.reusable_profile_key
    && applicationValuePresent(state.applicationProfile?.[field.reusable_profile_key])
  ));
  status.hidden = remembered.length === 0;
  status.innerHTML = remembered.length
    ? `<i data-lucide="sparkles" aria-hidden="true"></i><span>已帶入 ${remembered.length} 欄</span>`
    : "";
}

function renderApplicationFormPage(template) {
  state.activeApplicationTemplateId = template.id;
  $("#application-form-stage").textContent = template.stage;
  $("#application-form-title").textContent = template.title;
  $("#application-form-description").textContent = template.description;
  const badge = $("#application-form-official-badge");
  badge.className = `application-official-badge ${template.official_layout ? "" : "is-preparation"}`;
  badge.textContent = template.official_layout ? "官方格式" : "申請整理";
  $("#application-document-fields").innerHTML = template.fields.map((field) => {
    const inputId = `application-field-${field.id.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
    const showHeading = !["checkbox", "files"].includes(field.field_type);
    const help = field.help_text && field.field_type !== "files"
      ? `<details class="application-field-help"><summary aria-label="${escapeHtml(field.label)}填寫提示"><i data-lucide="circle-help" aria-hidden="true"></i></summary><p>${escapeHtml(field.help_text)}</p></details>`
      : "";
    return `
      <div class="application-document-field ${["textarea", "files"].includes(field.field_type) ? "is-wide" : ""} ${field.sensitive ? "is-sensitive" : ""}">
        ${showHeading ? `<div class="application-field-heading"><label for="${escapeHtml(inputId)}">${escapeHtml(field.label)}${field.required ? " *" : ""}</label>${help}</div>` : ""}
        ${applicationFieldInput(template, field, inputId)}
      </div>`;
  }).join("");
  renderApplicationAutofillStatus(template);
  const selection = state.applicationSelections[template.id] || { copies: template.default_copies };
  const list = (values) => values?.length ? values.join("、") : "不需要";
  $("#application-form-print-guide").innerHTML = `
    <h3>送件資訊</h3>
    <dl>
      <div><dt>份數</dt><dd>${selection.copies || template.default_copies} 份</dd></div>
      <div><dt>送件</dt><dd>${escapeHtml(list(template.destinations))}</dd></div>
      <div><dt>簽名</dt><dd>${escapeHtml(list(template.signatures))}</dd></div>
      <div><dt>核章</dt><dd>${escapeHtml(list(template.stamps))}</dd></div>
      <div><dt>下一步</dt><dd id="application-document-next-step">${escapeHtml(applicationDocumentNextStep(template))}</dd></div>
    </dl>
    <label class="application-status-control"><span>進度</span><select data-application-status-template="${escapeHtml(template.id)}">${APPLICATION_DOCUMENT_STATUSES.map(([value, label]) => `<option value="${value}" ${applicationDocumentStatus(template.id) === value ? "selected" : ""}>${label}</option>`).join("")}</select></label>
    ${template.conditional_note ? `<details class="application-compact-help"><summary><span><i data-lucide="info" aria-hidden="true"></i>注意事項</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><p>${escapeHtml(template.conditional_note)}</p></details>` : ""}`;
  const source = $("#application-form-source");
  source.href = template.source_url;
  const status = $("#application-document-form-status");
  status.textContent = "";
  initIcons();
}

function collectApplicationDocumentForm({ validate = true } = {}) {
  const template = applicationTemplateById(state.activeApplicationTemplateId);
  const form = $("#application-document-form");
  if (!template || !form) return false;
  if (validate && !form.reportValidity()) return false;
  const datePairs = [
    ["planned_start_date", "planned_end_date"],
    ["course_start_date", "course_end_date"],
  ];
  if (validate) {
    for (const [startId, endId] of datePairs) {
      const start = form.elements[startId];
      const end = form.elements[endId];
      if (!start || !end) continue;
      end.setCustomValidity(start.value && end.value && end.value < start.value ? "結束日期不可早於開始日期" : "");
      if (!end.reportValidity()) return false;
    }
    const missing = template.fields.filter((field) => field.required && field.field_type === "files" && !applicationFieldHasValue(template, field));
    if (missing.length) {
      const first = form.elements[missing[0].id];
      first?.focus();
      announce(`請完成：${missing.map((field) => field.label).join("、")}`, "error", true);
      return false;
    }
  }
  const values = {};
  template.fields.forEach((field) => {
    const input = form.elements[field.id];
    if (!input) return;
    let value = "";
    if (field.field_type === "checkbox") value = Boolean(input.checked);
    else if (field.field_type === "files") value = state.applicationFiles?.[template.id]?.[field.id] || state.applicationAnswers?.[template.id]?.[field.id] || [];
    else value = String(input.value || "").trim();
    if (field.reusable_profile_key) {
      if (applicationValuePresent(value)) state.applicationProfile[field.reusable_profile_key] = value;
      else delete state.applicationProfile[field.reusable_profile_key];
      return;
    }
    values[field.id] = value;
  });
  state.applicationAnswers[template.id] = values;
  state.applicationSelections[template.id] = {
    selected: true,
    copies: state.applicationSelections[template.id]?.copies || template.default_copies,
    status: applicationDocumentStatus(template.id) === "draft" ? "ready_to_print" : applicationDocumentStatus(template.id),
  };
  persistApplicationDraft();
  return true;
}

function saveApplicationDocument(event) {
  event.preventDefault();
  if (!collectApplicationDocumentForm()) return;
  const template = applicationTemplateById(state.activeApplicationTemplateId);
  const status = $("#application-document-form-status");
  status.textContent = "已儲存";
  restoreApplicationProfileForm();
  if (template) renderApplicationAutofillStatus(template);
  if (template) announce(`${template.short_title}已儲存`, "success");
  renderApplicationPacket();
  updateApplicationCenterSteps();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({ name: file.name, type: file.type, data_url: reader.result });
    reader.onerror = () => reject(new Error(`無法讀取 ${file.name}`));
    reader.readAsDataURL(file);
  });
}

async function handleApplicationFiles(input) {
  const template = applicationTemplateById(state.activeApplicationTemplateId);
  if (!template) return;
  const fieldId = input.dataset.applicationField;
  const field = template.fields.find((item) => item.id === fieldId);
  const maximum = Number(field?.max_files) || 6;
  const minimum = Math.max(Number(field?.min_files) || 0, field?.required ? 1 : 0);
  const selectedFiles = [...input.files];
  const files = selectedFiles.slice(0, maximum);
  if (selectedFiles.length > maximum) announce(`這個欄位最多選擇 ${maximum} 個檔案`, "error", true);
  if (files.some((file) => file.size > 8 * 1024 * 1024)) {
    input.value = "";
    announce("每個附件不可超過 8 MB", "error", true);
    return;
  }
  try {
    const encoded = await Promise.all(files.map(readFileAsDataUrl));
    state.applicationFiles[template.id] ||= {};
    state.applicationFiles[template.id][fieldId] = encoded;
    state.applicationAnswers[template.id] ||= {};
    state.applicationAnswers[template.id][fieldId] = encoded;
    input.setCustomValidity(encoded.length < minimum ? `請至少選擇 ${minimum} 個檔案` : "");
    const preview = document.querySelector(`[data-application-file-preview="${fieldId}"]`);
    if (preview) preview.innerHTML = encoded.map((file) => `<span>${escapeHtml(file.name)}</span>`).join("");
    persistApplicationDraft();
    if (encoded.length < minimum) input.reportValidity();
  } catch (error) {
    announce(error.message, "error", true);
  }
}

function applicationSelectionsPayload(singleTemplateId = "") {
  const templates = singleTemplateId
    ? state.applicationTemplates.filter((template) => template.id === singleTemplateId)
    : state.applicationTemplates.filter((template) => state.applicationSelections[template.id]?.selected);
  return templates.map((template) => ({
    template_id: template.id,
    copies: singleTemplateId ? 1 : Number(state.applicationSelections[template.id]?.copies || template.default_copies),
  }));
}

function applicationPacketPayload(singleTemplateId = "") {
  return {
    context: state.applicationContext,
    profile: state.applicationProfile,
    answers: state.applicationAnswers,
    selections: applicationSelectionsPayload(singleTemplateId),
  };
}

async function generateApplicationPdf(singleTemplateId = "") {
  if (singleTemplateId && !collectApplicationDocumentForm()) return;
  const payload = applicationPacketPayload(singleTemplateId);
  if (!payload.selections.length) {
    announce("請先選擇要加入列印包的文件", "error", true);
    return;
  }
  const button = singleTemplateId ? $("#download-single-application-document") : $("#download-application-packet");
  const original = button?.innerHTML;
  if (button) {
    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner" aria-hidden="true"></span><span>正在產生 PDF</span>';
  }
  try {
    const authHeaders = state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {};
    const response = await fetch("/application-center/pdf", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/pdf", ...authHeaders },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `PDF 產生失敗（${response.status}）`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const template = applicationTemplateById(singleTemplateId);
    link.href = url;
    link.download = `${template?.short_title || state.applicationContext.target_school || "交換申請"}-列印包.pdf`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1500);
    announce("PDF 已產生，請列印後完成親簽與核章", "success");
  } catch (error) {
    announce(error.message, "error", true);
  } finally {
    if (button) {
      button.innerHTML = original;
      button.disabled = false;
    }
    renderApplicationPacket();
    initIcons();
  }
}

function preferredBudgetSchool() {
  return state.budgetSchool
    || [...state.applications][0]
    || [...state.favorites][0]
    || state.dashboard?.partner_universities?.[0]?.school_name
    || "";
}

function budgetValuesFromForm() {
  const number = (selector) => Math.max(0, Number($(selector)?.value) || 0);
  return {
    schoolName: $("#budget-school")?.value || "",
    currency: $("#budget-currency")?.value || "TWD",
    months: Math.max(1, Math.min(24, number("#budget-months") || 5)),
    housing: number("#budget-housing"),
    food: number("#budget-food"),
    transport: number("#budget-transport"),
    other: number("#budget-other"),
    oneTime: number("#budget-onetime"),
    scholarship: number("#budget-scholarship"),
  };
}

function formatBudgetAmount(amount, currency) {
  return new Intl.NumberFormat("zh-TW", {
    style: "currency",
    currency: currency || "TWD",
    maximumFractionDigits: 0,
  }).format(Number(amount) || 0);
}

function updateBudgetResult() {
  const result = $("#budget-result");
  if (!result) return;
  const values = budgetValuesFromForm();
  const monthly = values.housing + values.food + values.transport + values.other;
  const total = monthly * values.months + values.oneTime;
  const net = Math.max(0, total - values.scholarship);
  const target = state.eligibilityProfile?.monthlyBudget || 0;
  const overTarget = values.currency === "TWD" && target > 0 && monthly > target;
  result.innerHTML = `
    <span class="budget-result-kicker">${escapeHtml(values.schoolName || "交換計畫")}</span>
    <div class="budget-result-total"><small>扣除預計補助後</small><strong>${formatBudgetAmount(net, values.currency)}</strong><span>總支出 ${formatBudgetAmount(total, values.currency)}</span></div>
    <dl><div><dt>每月生活</dt><dd>${formatBudgetAmount(monthly, values.currency)}</dd></div><div><dt>${values.months} 個月生活費</dt><dd>${formatBudgetAmount(monthly * values.months, values.currency)}</dd></div><div><dt>一次性支出</dt><dd>${formatBudgetAmount(values.oneTime, values.currency)}</dd></div><div><dt>預計補助</dt><dd>-${formatBudgetAmount(values.scholarship, values.currency)}</dd></div></dl>
    ${monthly === 0 ? '<p class="budget-result-note"><i data-lucide="info" aria-hidden="true"></i>先參考下方官方資料，再填入同一幣別的估算。</p>' : overTarget ? `<p class="budget-result-note warning"><i data-lucide="triangle-alert" aria-hidden="true"></i>每月估算高於你設定的 ${formatBudgetAmount(target, "TWD")} 預算。</p>` : '<p class="budget-result-note success"><i data-lucide="circle-check" aria-hidden="true"></i>已建立可比較的交換成本基準。</p>'}`;
  initIcons();
}

function renderBudgetSource(schoolName) {
  const container = $("#budget-source-summary");
  if (!container) return;
  const profile = destinationProfileForSchool(schoolName);
  if (!profile) {
    container.innerHTML = '<p>這間學校目前沒有足以安全換算的官方生活費資料，請自行輸入估算並查看學校來源。</p>';
    return;
  }
  container.innerHTML = `
    <span class="budget-source-city"><i data-lucide="map-pin" aria-hidden="true"></i>${escapeHtml(profile.city || profile.country || "目的地")}</span>
    <p>${highlightHtml(profile.cost_summary || "官方生活費待補充。")}</p>
    ${profile.housing_summary ? `<details><summary>住宿費用背景<i data-lucide="chevron-down" aria-hidden="true"></i></summary><p>${highlightHtml(profile.housing_summary)}</p></details>` : ""}
    <div class="budget-source-links">${(profile.sources || []).slice(0, 3).map((source) => `<a href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(source.title || "官方來源")}<i data-lucide="external-link" aria-hidden="true"></i></a>`).join("")}</div>
    <small>最後查核：${escapeHtml(formatDate(profile.last_checked).slice(0, 10))}</small>`;
  initIcons();
}

function populateBudgetForm(schoolName) {
  const plan = budgetPlanForSchool(schoolName) || {};
  state.budgetSchool = schoolName;
  $("#budget-school").value = schoolName;
  $("#budget-currency").value = plan.currency || "TWD";
  $("#budget-months").value = plan.months || 5;
  $("#budget-housing").value = plan.housing || 0;
  $("#budget-food").value = plan.food || 0;
  $("#budget-transport").value = plan.transport || 0;
  $("#budget-other").value = plan.other || 0;
  $("#budget-onetime").value = plan.oneTime || 0;
  $("#budget-scholarship").value = plan.scholarship || 0;
  renderBudgetSource(schoolName);
  updateBudgetResult();
}

function renderBudgetPlanner() {
  const select = $("#budget-school");
  if (!select || !state.dashboard) return;
  const schools = state.dashboard.partner_universities.map((item) => item.school_name);
  const selected = preferredBudgetSchool();
  fillSelect("#budget-school", schools, "請選擇學校", selected);
  if (selected) populateBudgetForm(selected);
}

function saveBudgetPlan(event) {
  event.preventDefault();
  const values = budgetValuesFromForm();
  if (!values.schoolName) {
    announce("請先選擇要估算的學校", "error");
    return;
  }
  state.budgetPlans[values.schoolName] = { ...values, savedAt: new Date().toISOString() };
  try {
    window.localStorage.setItem(STORAGE_KEYS.budgetPlans, JSON.stringify(state.budgetPlans));
  } catch (_) {
    announce("瀏覽器無法保存這份預算。", "error", true);
    return;
  }
  updateBudgetResult();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  announce("交換預算已保存", "success");
}

function renderPartnerFilters() {
  const partners = state.dashboard.partner_universities;
  const countries = unique(partners.map((item) => item.country));
  const colleges = unique(partners.flatMap((item) => splitOptions(item.colleges)));
  const degrees = unique(partners.flatMap((item) => splitOptions(item.degree_levels)));
  fillSelect("#country-filter", countries, "全部國家", state.country);
  fillSelect("#college-filter", colleges, "全部學院", state.college);
  fillSelect("#degree-filter", degrees, "全部學制", state.degree);
}

function filteredPartners() {
  if (!state.dashboard) return [];
  const query = normalize(state.partnerQuery);
  const partners = state.dashboard.partner_universities.filter((item) => {
    const destination = destinationProfileForSchool(item.school_name);
    const text = normalize(
      `${Object.values(item).join(" ")} ${JSON.stringify(item.student_summary_zh || {})} ${Object.values(destination || {}).join(" ")}`
    );
    return (
      (!query || text.includes(query)) &&
      (!state.country || item.country === state.country) &&
      (!state.college || collegeMatches(item.colleges, state.college)) &&
      (!state.degree || degreeMatches(item.degree_levels, state.degree))
    );
  });
  if (state.eligibilityProfile) {
    partners.sort((left, right) => partnerMatch(right).score - partnerMatch(left).score);
  }
  return partners;
}

function collegeMatches(value, selected) {
  const text = normalize(value);
  return text.includes(normalize(selected)) || text.includes("全校") || text.includes("四院皆可");
}

function degreeMatches(value, selected) {
  const text = normalize(value);
  const target = normalize(selected);
  if (target === "研究所") return /研究所|碩士|博士/.test(text);
  return text.includes(target);
}

function renderPartnerTable() {
  const partners = filteredPartners();
  const visible = partners.slice(0, state.partnerLimit);
  $("#partner-count").textContent = `${partners.length} 所`;

  if (!partners.length) {
    renderEmpty("#partner-table", "沒有符合的學校", "調整國家、學院、學制或關鍵字後再試一次。");
    $("#show-more-partners").hidden = true;
    return;
  }

  const tableRows = visible.map(renderPartnerTableRow).join("");
  const cards = visible.map(renderPartnerCard).join("");
  $("#partner-table").innerHTML = `
    <div class="desktop-partner-table">
      <table class="partner-table">
        <thead><tr><th>國家</th><th>學校</th><th>計畫</th><th>可申請身分</th><th>名額／期間</th><th>重點條件</th><th><span class="visually-hidden">收藏</span></th></tr></thead>
        <tbody>${tableRows}</tbody>
      </table>
    </div>
    <div class="mobile-partner-list">${cards}</div>`;

  const moreButton = $("#show-more-partners");
  const remaining = partners.length - visible.length;
  moreButton.hidden = remaining <= 0;
  moreButton.textContent = remaining > 0 ? `顯示更多學校（還有 ${remaining} 所）` : "";
  initIcons();
}

function renderPartnerTableRow(item) {
  const period = localizedPartnerValue(item, "study_period", "study_period");
  const deadline = localizedPartnerValue(item, "application_deadline", "application_deadline");
  const match = partnerMatch(item);
  return `
    <tr>
      <td>${escapeHtml(item.country || "--")}</td>
      <td>
        <div class="partner-school-cell">
          ${renderSchoolPhoto(item, "table")}
          <div>
            <button type="button" class="partner-name school-detail-trigger" data-school-name="${escapeHtml(item.school_name)}">
              ${escapeHtml(item.school_name)}
            </button>
            ${state.eligibilityProfile ? `<span class="match-pill ${match.tone}">${escapeHtml(match.label)}</span>` : ""}
            <div class="partner-links">${renderPartnerLinks(item)}</div>
            <div class="coverage-chips">${renderCoverageBadges(item)}</div>
          </div>
        </div>
      </td>
      <td>${escapeHtml(item.program_type || "--")}</td>
      <td>${escapeHtml([item.colleges, item.degree_levels].filter(Boolean).join("／") || "--")}</td>
      <td>${escapeHtml([item.quota, period, deadline].filter(Boolean).join("／") || "--")}</td>
      <td class="condition-cell">${renderStudentPointList(partnerSummaryPoints(item, "eligibility_points"), { limit: 3, compact: true })}</td>
      <td>${renderFavoriteButton(item, true)}</td>
    </tr>`;
}

function renderPartnerCard(item) {
  const meta = [item.program_type, item.colleges, item.degree_levels].filter(Boolean).join(" · ");
  const period = localizedPartnerValue(item, "study_period", "study_period");
  const deadline = localizedPartnerValue(item, "application_deadline", "application_deadline");
  const match = partnerMatch(item);
  return `
    <details class="partner-card">
      <summary>
        ${renderSchoolPhoto(item, "card")}
        <span class="partner-card-copy">
          <span class="partner-card-country">${escapeHtml(item.country || "未標示國家")}</span>
          <strong>${escapeHtml(item.school_name)}</strong>
          <small>${escapeHtml(truncate(meta, 72))}</small>
          ${state.eligibilityProfile ? `<span class="match-pill ${match.tone}">${escapeHtml(match.label)}</span>` : ""}
        </span>
        <i data-lucide="chevron-down" aria-hidden="true"></i>
      </summary>
      <div class="partner-card-content">
        <div class="coverage-chips">${renderCoverageBadges(item)}</div>
        <div class="partner-facts">
          <div class="partner-fact"><span>計畫</span><strong>${escapeHtml(item.program_type || "依公告")}</strong></div>
          <div class="partner-fact"><span>名額</span><strong>${escapeHtml(item.quota || "依公告")}</strong></div>
          <div class="partner-fact"><span>研修期間</span><strong>${escapeHtml(period)}</strong></div>
          <div class="partner-fact"><span>合作校截止日</span><strong>${highlightHtml(deadline)}</strong></div>
          <div class="partner-fact"><span>適用身分</span><strong>${escapeHtml([item.colleges, item.degree_levels].filter(Boolean).join("／") || "依公告")}</strong></div>
        </div>
        <div class="partner-card-summary"><strong>申請重點</strong>${renderStudentPointList(partnerSummaryPoints(item, "eligibility_points"), { limit: 3 })}</div>
        ${state.eligibilityProfile ? `<div class="partner-match-reasons"><strong>為什麼排在這裡</strong><ul>${match.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}${match.risks.map((risk) => `<li class="risk">${escapeHtml(risk)}</li>`).join("")}</ul></div>` : ""}
        <div class="partner-card-actions">
          <button type="button" class="primary-button school-detail-trigger" data-school-name="${escapeHtml(item.school_name)}">
            <i data-lucide="notebook-tabs" aria-hidden="true"></i><span>查看完整資訊</span>
          </button>
          ${renderFavoriteButton(item)}
        </div>
        <div class="partner-links">${renderPartnerLinks(item)}</div>
      </div>
    </details>`;
}

function partnerStudentSummary(item) {
  return item?.student_summary_zh || {};
}

function localizedPartnerValue(item, summaryKey, rawKey, fallback = "依公告") {
  const value = partnerStudentSummary(item)[summaryKey] || item?.[rawKey];
  return value || fallback;
}

function partnerSummaryPoints(item, key) {
  const points = partnerStudentSummary(item)[key];
  if (Array.isArray(points) && points.length) return points.filter(Boolean);
  return [];
}

function renderStudentPointList(points, { limit = 4, compact = false, fallback = "官方資料尚未提供可整理的重點。" } = {}) {
  const visible = (points || []).filter(Boolean).slice(0, limit);
  const values = visible.length ? visible : [fallback];
  return `<ul class="student-point-list${compact ? " compact" : ""}">${values
    .map((point) => `<li>${renderSummaryText(point)}</li>`)
    .join("")}</ul>`;
}

function renderSummaryText(value) {
  const text = String(value ?? "");
  const urlPattern = /https?:\/\/[^\s）)]+/gi;
  let cursor = 0;
  let html = "";
  for (const match of text.matchAll(urlPattern)) {
    html += highlightHtml(text.slice(cursor, match.index));
    const matchedUrl = match[0];
    const url = matchedUrl.replace(/[.,;。；，]+$/, "");
    const trailing = matchedUrl.slice(url.length);
    html += `<a class="summary-inline-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer"><span>官方連結</span><i data-lucide="external-link" aria-hidden="true"></i></a>${highlightHtml(trailing)}`;
    cursor = Number(match.index) + matchedUrl.length;
  }
  return html + highlightHtml(text.slice(cursor));
}

function renderPartnerLinks(item) {
  const website = item.website
    ? `<a href="${escapeHtml(item.website)}" target="_blank" rel="noreferrer">學校網站</a>`
    : "";
  const source = item.source_url
    ? `<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">官方來源</a>`
    : "";
  const visual = schoolImageFor(item.school_name);
  const imageSource = visual?.official_page_url
    ? `<a href="${escapeHtml(visual.official_page_url)}" target="_blank" rel="noreferrer">官方圖片來源</a>`
    : "";
  return [website, source, imageSource].filter(Boolean).join("");
}

function partnerByName(schoolName) {
  return state.dashboard?.partner_universities.find(
    (item) => normalize(item.school_name) === normalize(schoolName)
  );
}

function renderFavoriteButton(item, iconOnly = false) {
  const saved = state.favorites.has(item.school_name);
  return `
    <button type="button" class="${iconOnly ? "icon-button" : "secondary-button"} favorite-toggle${saved ? " saved" : ""}" data-school-name="${escapeHtml(item.school_name)}" aria-pressed="${saved}" aria-label="${saved ? "取消收藏" : "收藏"}${escapeHtml(item.school_name)}"${iconOnly ? ` data-tooltip="${saved ? "取消收藏" : "收藏"}"` : ""}>
      <i data-lucide="${saved ? "bookmark-check" : "bookmark"}" aria-hidden="true"></i>${iconOnly ? "" : `<span>${saved ? "已收藏" : "收藏"}</span>`}
    </button>`;
}

function toggleFavorite(schoolName) {
  if (!schoolName) return;
  if (state.favorites.has(schoolName)) state.favorites.delete(schoolName);
  else state.favorites.add(schoolName);
  try {
    window.localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify([...state.favorites]));
  } catch (_) {
    // Favorites still work for this session.
  }
  renderPartnerTable();
  renderFavorites();
  updateFavoriteCounts();
  renderDecisionBrief();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  if (state.activeSchool === schoolName) updateDetailFavoriteButton();
}

function updateFavoriteCounts() {
  const count = state.favorites.size;
  const countBadge = $("#favorite-count");
  if (countBadge) countBadge.textContent = `${count} 所`;
  const navCount = $("#nav-favorite-count");
  if (navCount) {
    navCount.textContent = String(count);
    navCount.hidden = count === 0;
  }
}

function renderFavorites() {
  const list = $("#favorite-list");
  const comparePanel = $("#compare-panel");
  if (!list || !state.dashboard) return;
  const favorites = state.dashboard.partner_universities.filter((item) => state.favorites.has(item.school_name));
  if (!favorites.length) {
    list.innerHTML = `
      <div class="empty-state favorite-empty">
        <i data-lucide="bookmark" aria-hidden="true"></i>
        <strong>還沒有收藏學校</strong>
        <span>在合作學校旁點選收藏，就能把候選學校集中比較。</span>
        <a class="secondary-button" href="#partners"><span>前往找學校</span><i data-lucide="arrow-right" aria-hidden="true"></i></a>
      </div>`;
    comparePanel.hidden = true;
    comparePanel.replaceChildren();
    initIcons();
    return;
  }
  list.innerHTML = favorites
    .map(
      (item) => `
        <details class="favorite-card">
          <summary>
            ${renderSchoolPhoto(item, "favorite")}
            <span class="favorite-card-heading"><span>${escapeHtml(item.country || "未標示國家")}</span><strong>${escapeHtml(item.school_name)}</strong></span>
            <i data-lucide="chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="favorite-card-content">
            <p>${highlightHtml(summarizePartnerCondition(item, 110))}</p>
            <div class="favorite-card-actions">
              <button type="button" class="primary-button school-detail-trigger" data-school-name="${escapeHtml(item.school_name)}"><span>查看資訊</span><i data-lucide="arrow-right" aria-hidden="true"></i></button>
              ${renderFavoriteButton(item, true)}
            </div>
          </div>
        </details>`
    )
    .join("");
  comparePanel.hidden = favorites.length < 2;
  comparePanel.innerHTML = favorites.length >= 2 ? renderComparison(favorites.slice(0, 3)) : "";
  initIcons();
}

function renderComparison(items) {
  const rows = [
    ["國家", (item) => item.country || "依公告"],
    ["名額", (item) => item.quota || "依公告"],
    ["研修期間", (item) => item.study_period || "依公告"],
    ["合作校截止日", (item) => item.application_deadline || "依公告"],
    ["適用身分", (item) => [item.colleges, item.degree_levels].filter(Boolean).join("／") || "依公告"],
  ];
  return `
    <div class="compare-heading"><div><span class="section-kicker">最多先比較 3 所</span><h3>候選學校差異</h3></div><span>${items.length} 所比較中</span></div>
    <div class="compare-scroll"><table class="compare-table"><thead><tr><th>比較項目</th>${items.map((item) => `<th>${escapeHtml(item.school_name)}</th>`).join("")}</tr></thead><tbody>${rows
      .map(([label, getter]) => `<tr><th>${escapeHtml(label)}</th>${items.map((item) => `<td>${highlightHtml(getter(item))}</td>`).join("")}</tr>`)
      .join("")}</tbody></table></div>`;
}

function openUniversityDetail(item, { updateHistory = true } = {}) {
  if (!item) return;
  if (!$("#dashboard-view").hidden) {
    state.dashboardScrollY = window.scrollY;
    state.dashboardHash = window.location.hash.startsWith("#school=")
      ? "#partners"
      : window.location.hash || "#overview";
  }
  state.activeSchool = item.school_name;
  state.experienceRequestId += 1;
  state.workflowRequestId += 1;
  state.destinationRequestId += 1;
  state.communityRequestId += 1;
  $("#dashboard-view").hidden = true;
  const detailView = $("#school-detail-view");
  detailView.hidden = false;
  setSchoolHeroProgress(detailView, 0);
  document.body.classList.add("school-detail-open");
  setActiveNavigation("partners");
  document.title = `${item.school_name} | 台灣大學生交換指南`;
  $("#school-detail-country").textContent = [item.country, item.program_type].filter(Boolean).join(" · ");
  $("#school-detail-title").textContent = item.school_name;
  $("#school-detail-photo").innerHTML = `${renderSchoolPhoto(item, "detail")}<div class="school-detail-photo-source">${renderPartnerLinks(item)}</div>`;
  $("#school-detail-summary").innerHTML = highlightHtml(summarizePartnerCondition(item, 110, 1));
  $("#school-detail-primary-facts").innerHTML = renderPrimaryFacts(item);
  $("#school-detail-content").innerHTML = renderUniversityOverview(item);
  activateDetailTab("detail-overview");
  updateDetailFavoriteButton();
  updateDetailApplicationButton();
  if (updateHistory) history.pushState({ school: item.school_name }, "", `#school=${encodeURIComponent(item.school_name)}`);
  window.scrollTo({ top: 0, behavior: "instant" });
  initIcons();
  window.requestAnimationFrame(updateSchoolHeroMotion);

  const cachedWorkflow = state.workflowCache.get(item.school_name);
  if (cachedWorkflow) renderApplicationWorkflow(cachedWorkflow);
  else loadApplicationWorkflow(item);

  const cachedExperience = state.experienceCache.get(item.school_name);
  if (cachedExperience) renderExperienceDigest(cachedExperience);
  else loadStudentExperiences(item);

  const cachedDestination = state.destinationCache.get(item.school_name);
  if (cachedDestination) renderDestinationProfile(item, cachedDestination);
  else loadDestinationProfile(item);

  const cachedCommunity = state.communityCache.get(item.school_name);
  if (cachedCommunity) renderCommunityThreads(cachedCommunity);
  else loadCommunityQuestions(item);
}

function closeUniversityDetail({ updateHistory = true } = {}) {
  state.activeSchool = null;
  state.experienceRequestId += 1;
  state.workflowRequestId += 1;
  state.destinationRequestId += 1;
  state.communityRequestId += 1;
  $("#school-detail-view").hidden = true;
  setSchoolHeroProgress($("#school-detail-view"), 0);
  $("#dashboard-view").hidden = false;
  document.body.classList.remove("school-detail-open");
  if (updateHistory) {
    history.pushState({}, "", state.dashboardHash || "#partners");
    applyAppRoute({ loadFeed: false, resetScroll: false });
  }
  window.setTimeout(() => {
    window.scrollTo({ top: state.dashboardScrollY || 0, behavior: "instant" });
    const returnPage = (state.dashboardHash || "#partners").slice(1);
    setActiveNavigation(UNIVERSITY_PAGE_ROUTES.has(returnPage) && returnPage !== "search" ? returnPage : "partners");
  }, 0);
}

let schoolHeroScrollFrame = 0;

function setSchoolHeroProgress(detailView, progress) {
  if (!detailView) return;
  const safeProgress = Math.min(1, Math.max(0, progress));
  detailView.style.setProperty("--hero-scroll-progress", safeProgress.toFixed(3));
  detailView.style.setProperty("--hero-photo-opacity", (1 - safeProgress).toFixed(3));
  detailView.style.setProperty("--hero-photo-shift", `${Math.round(safeProgress * -64)}px`);
  detailView.style.setProperty("--hero-photo-scale", (1 + safeProgress * 0.08).toFixed(3));
  detailView.style.setProperty("--hero-photo-blur", `${(safeProgress * 5).toFixed(2)}px`);
  detailView.style.setProperty("--hero-photo-saturation", (1 - safeProgress * 0.28).toFixed(3));
}

function updateSchoolHeroMotion() {
  schoolHeroScrollFrame = 0;
  const detailView = $("#school-detail-view");
  const header = detailView?.querySelector(".school-detail-header");
  if (!detailView || detailView.hidden || !header) return;
  const rect = header.getBoundingClientRect();
  const traveled = Math.max(0, 92 - rect.top);
  const range = Math.max(360, header.offsetHeight * 0.68);
  const progress = Math.min(1, traveled / range);
  setSchoolHeroProgress(detailView, progress);
}

function queueSchoolHeroMotion() {
  if (schoolHeroScrollFrame) return;
  schoolHeroScrollFrame = window.requestAnimationFrame(updateSchoolHeroMotion);
}

function updateDetailFavoriteButton() {
  const button = $("#detail-favorite-button");
  if (!button || !state.activeSchool) return;
  const saved = state.favorites.has(state.activeSchool);
  button.dataset.schoolName = state.activeSchool;
  button.setAttribute("aria-pressed", String(saved));
  button.classList.toggle("saved", saved);
  button.innerHTML = `<i data-lucide="${saved ? "bookmark-check" : "bookmark"}" aria-hidden="true"></i><span>${saved ? "已收藏" : "收藏"}</span>`;
  initIcons();
}

function updateDetailApplicationButton() {
  const button = $("#detail-application-button");
  if (!button || !state.activeSchool) return;
  const added = state.applications.has(state.activeSchool);
  button.dataset.schoolName = state.activeSchool;
  button.setAttribute("aria-pressed", String(added));
  button.classList.toggle("added", added);
  button.innerHTML = `<i data-lucide="${added ? "clipboard-check" : "clipboard-plus"}" aria-hidden="true"></i><span>${added ? "已加入清單" : "加入清單"}</span>`;
  initIcons();
}

function toggleApplication(schoolName) {
  if (!schoolName) return;
  if (state.applications.has(schoolName)) state.applications.delete(schoolName);
  else {
    state.applications.add(schoolName);
    state.favorites.add(schoolName);
  }
  try {
    window.localStorage.setItem(STORAGE_KEYS.applications, JSON.stringify([...state.applications]));
    window.localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify([...state.favorites]));
  } catch (_) {
    // The application list still works for this session.
  }
  updateDetailApplicationButton();
  renderFavorites();
  updateFavoriteCounts();
  renderDecisionBrief();
  renderDocumentReadiness();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  renderBudgetPlanner();
}

function renderPrimaryFacts(item, destinationProfile = state.destinationCache.get(item.school_name)) {
  const eligibility = partnerEligibilityStatus(item);
  return [
    ["我的資格", eligibility.label, eligibility.icon, eligibility.tone],
    ["合作校截止", localizedPartnerValue(item, "application_deadline", "application_deadline"), "calendar-clock", "deadline"],
    ["語言門檻", partnerLanguageRequirement(item), "languages", "language"],
    ["生活費參考", truncate(destinationProfile?.cost_summary || "官方費用待查核", 130), "wallet-cards", "cost"],
    ["交換名額", item.quota || "依公告", "users", "quota"],
    ["研修期間", localizedPartnerValue(item, "study_period", "study_period"), "calendar-range", "period"],
  ]
    .map(([label, value, icon, tone]) => `<div class="${tone || ""}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${escapeHtml(label)}</span><strong>${highlightHtml(value)}</strong></div>`)
    .join("");
}

function partnerEligibilityStatus(item) {
  const profile = state.eligibilityProfile;
  if (!profile) return { label: "尚未進行資格初判", icon: "circle-help", tone: "needs-check" };
  const match = partnerMatch(item, profile);
  if (match.tone === "strong") return { label: "高度符合目前條件，正式資格仍須核對", icon: "badge-check", tone: "likely-pass" };
  if (match.tone === "review") return { label: `${match.label}，${match.risks[0] || "個別條件仍須核對"}`, icon: "circle-help", tone: "needs-check" };
  return { label: `${match.risks.join("、") || "目前條件不符"}`, icon: "triangle-alert", tone: "needs-review" };
}

function partnerLanguageRequirement(item) {
  const parts = partnerSummaryPoints(item, "eligibility_points");
  const language = parts.filter((part) => /TOEIC|IELTS|TOEFL|Duolingo|英文|英語|語文|語言|CEFR|JLPT|TOPIK/i.test(part));
  const compact = language.slice(0, 2).map((point) =>
    point
      .replace(/https?:\/\/[^\s）)]+/gi, "")
      .replace(/\(\s*\)/g, "")
      .replace(
        /方案\s+([AB])\s+語言門檻：IELTS\s+總分\s+([\d.]+)，各單項不得低於\s+([\d.]+).*$/,
        "方案 $1：IELTS $2（單項 $3）"
      )
      .replace(/\s+/g, " ")
      .trim()
  );
  return truncate(compact.join("；") || "合作校未明確標示，請開啟官方來源", 110);
}

function renderProgramOptions(item) {
  const options = item.program_options || [];
  if (options.length <= 1) return "";
  return `
    <div class="program-options" aria-label="可申請方案">
      <div class="program-options-heading"><strong>這間學校有 ${options.length} 種申請方案</strong><span>請依學院、學制與名額選擇正確方案</span></div>
      <div class="program-option-list">
        ${options.map((option) => `
          <article class="program-option">
            <div><span class="program-option-type">${escapeHtml(option.program_type)}</span><h3>${escapeHtml([option.colleges, option.degree_levels].filter(Boolean).join(" · ") || "適用身分依公告")}</h3></div>
            <dl>
              <div><dt>名額</dt><dd>${escapeHtml(option.quota || "依公告")}</dd></div>
              <div><dt>研修期間</dt><dd>${escapeHtml(localizedPartnerValue(option, "study_period", "study_period"))}</dd></div>
              <div><dt>截止日</dt><dd>${highlightHtml(localizedPartnerValue(option, "application_deadline", "application_deadline"))}</dd></div>
            </dl>
            ${partnerSummaryPoints(option, "eligibility_points").length ? `<details><summary><span>查看此方案中文重點</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>${renderStudentPointList(partnerSummaryPoints(option, "eligibility_points"), { limit: 8 })}</details>` : ""}
            <a href="${escapeHtml(option.source_url)}" target="_blank" rel="noreferrer">查看${escapeHtml(activeUniversityProfile().short_name)}官方方案來源<i data-lucide="external-link" aria-hidden="true"></i></a>
          </article>`).join("")}
      </div>
    </div>`;
}

function renderPartnerStudentSummary(item) {
  const summary = partnerStudentSummary(item);
  const groups = [
    {
      label: "資格與語言重點",
      icon: "badge-check",
      points: partnerSummaryPoints(item, "eligibility_points"),
    },
    {
      label: "合作校申請步驟",
      icon: "list-checks",
      points: partnerSummaryPoints(item, "application_steps"),
    },
    {
      label: "費用提醒",
      icon: "wallet-cards",
      points: partnerSummaryPoints(item, "tuition_points"),
    },
  ].filter((group) => group.points.length);
  if (!groups.length) return "";
  return `
    <section class="partner-student-summary" aria-labelledby="partner-student-summary-title">
      <div class="partner-student-summary-heading">
        <div><span class="section-kicker">不用先讀英文原文</span><h3 id="partner-student-summary-title">學生版中文重點</h3></div>
        ${summary.translated_from_english ? '<span class="translation-status"><i data-lucide="languages" aria-hidden="true"></i>英文資料已翻成中文</span>' : ""}
      </div>
      <div class="partner-summary-groups">
        ${groups.map((group) => `
          <section class="partner-summary-group">
            <h4><i data-lucide="${group.icon}" aria-hidden="true"></i>${escapeHtml(group.label)}</h4>
            ${renderStudentPointList(group.points, { limit: 10 })}
          </section>`).join("")}
      </div>
      <p class="partner-summary-note">這裡是方便判斷的中文摘要；送件前請再開啟下方官方來源核對最新版本。</p>
    </section>`;
}

function renderUniversityOverview(item) {
  const tuitionPoints = partnerSummaryPoints(item, "tuition_points");
  const facts = [
    ["計畫類型", item.program_type || "依校方公告"],
    ["適用學院／學制", [item.colleges, item.degree_levels].filter(Boolean).join("／") || "依校方公告"],
    ["名額", item.quota || "依校方公告"],
    ["研修期間", localizedPartnerValue(item, "study_period", "study_period", "依校方公告")],
    ["合作校截止日", localizedPartnerValue(item, "application_deadline", "application_deadline", "依校方公告")],
    ["學費", tuitionPoints.slice(0, 2).join("；") || "依校方公告"],
    ["排名資訊", item.ranking_info || "未提供"],
  ];
  return `
    <div class="detail-main-column">
      <section id="detail-overview" class="detail-section university-overview" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-overview">
        <div class="overview-intro-grid">
          <div class="detail-section-heading"><span class="section-kicker">20 秒快速了解</span><h2 id="detail-overview-title">從${escapeHtml(activeUniversityProfile().short_name)}申請這間學校</h2><p>先分清楚${escapeHtml(activeUniversityProfile().short_name)}校內規定與合作校額外條件，再決定是否加入申請清單。</p></div>
          <div class="rule-scope-grid">
            <article class="rule-scope home-rule"><span><i data-lucide="building-2" aria-hidden="true"></i>${escapeHtml(activeHomeSchool())}規定</span><h3>校內甄選是第一關</h3><p>先確認${escapeHtml(activeUniversityProfile().short_name)}的成績、語言、學院與送件時程，通過校內甄選後才會進入合作校申請。</p></article>
            <article class="rule-scope partner-rule"><span><i data-lucide="globe-2" aria-hidden="true"></i>合作校規定</span><h3>提名後還要再申請</h3>${renderStudentPointList(partnerSummaryPoints(item, "eligibility_points"), { limit: 3, compact: true })}</article>
          </div>
        </div>
        <div id="quick-decision-fit">${renderQuickDecisionFit(item)}</div>
        ${renderProgramOptions(item)}
        <div class="university-facts">${facts.map(([label, value]) => `<div class="university-fact"><span>${escapeHtml(label)}</span><strong>${highlightHtml(value)}</strong></div>`).join("")}</div>
        ${renderPartnerStudentSummary(item)}
        <div class="partner-links detail-source-links">${renderPartnerLinks(item)}</div>
      </section>

      <section id="detail-application" class="detail-section workflow-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-application" hidden>
        <div class="detail-section-heading"><span class="section-kicker">從校內甄選到返國結案</span><h2 id="application-workflow-title">詳細申請流程</h2><p>每一步標示負責單位、期限、文件與官方入口，避免漏掉合作校提名後的第二階段。</p></div>
        <div id="workflow-content" aria-live="polite" aria-busy="true">${renderWorkflowLoading()}</div>
      </section>

      <section id="detail-life" class="detail-section life-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-life" hidden>
        <div class="detail-section-heading"><span class="section-kicker">食衣住行、課業與社交</span><h2 id="student-life-title">在這裡生活會是什麼樣子</h2><p>把公開心得依生活面向交叉整理；沒有足夠來源的項目會明確標示，不自行推測。</p></div>
        <div id="destination-official-content" class="destination-official" aria-live="polite" aria-busy="true"><div class="skeleton skeleton-card"></div></div>
        <div id="life-content" class="life-grid" aria-live="polite" aria-busy="true">${renderLifeLoading()}</div>
      </section>

      <section id="detail-experiences" class="detail-section experience-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-experiences" hidden>
        <div class="detail-section-heading"><span class="section-kicker">公開文章、Blog、影片與討論</span><h2 id="student-experience-title">其他學生去過的心得</h2><p>比較不同年份與學生背景的描述，摘要只幫你掌握重點，完整內容仍回到原始來源查看。</p></div>
        <div id="experience-content" aria-live="polite" aria-busy="true">${renderExperienceLoading()}</div>
      </section>

      <section id="detail-community" class="detail-section community-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-community" hidden>
        <div class="detail-section-heading"><span class="section-kicker">匿名交流與經驗投稿</span><h2 id="community-title">${escapeHtml(item.school_name)} 學生社群</h2><p>公開貼文與聊天室適合一起討論；私訊必須先由對方接受邀請，並可隨時封鎖或檢舉。</p></div>
        <div id="community-content" class="community-content" aria-live="polite" aria-busy="true">${renderCommunityLoading()}</div>
        ${renderCommunityContributionForms(item)}
      </section>
    </div>

    <aside class="detail-side-column" aria-label="申請準備進度與官方來源">
      <section class="application-tracker"><span class="section-kicker">只存在這台裝置</span><h2>我的申請進度</h2><div id="application-tracker">${renderApplicationTracker(item)}</div></section>
      <section class="decision-reminder"><i data-lucide="badge-check" aria-hidden="true"></i><div><strong>資訊最後仍以官方為準</strong><p>截止日與資格可能異動，送件前請再核對${escapeHtml(activeUniversityProfile().short_name)}國際處與合作校通知。</p></div></section>
    </aside>`;
}

function renderLifeLoading() {
  return LIFE_SECTIONS.map(() => '<div class="skeleton skeleton-life"></div>').join("");
}

function renderQuickDecisionFit(item, digest = state.experienceCache.get(item.school_name)) {
  const eligibility = partnerEligibilityStatus(item);
  const identity = [item.colleges, item.degree_levels].filter(Boolean).join("／") || "身分依合作校公告";
  const period = localizedPartnerValue(item, "study_period", "study_period");
  const deadline = localizedPartnerValue(item, "application_deadline", "application_deadline");
  const tuition = partnerSummaryPoints(item, "tuition_points")[0];
  const fitPoints = [
    `申請範圍：${identity}`,
    `${item.program_type || "交換計畫"}，研修期間 ${period}`,
    tuition ? `學費條件：${tuition}` : `名額：${item.quota || "依公告"}`,
  ];
  if (eligibility.tone === "likely-pass") fitPoints.unshift(`資格初判：${eligibility.label}`);

  const strengths = (digest?.common_strengths || []).slice(0, 2);
  const positivePoints = strengths.length
    ? strengths.map((insight) => `學生經驗（${insight.source_count} 個來源）：${truncate(insight.summary, 115)}`)
    : [digest ? "目前沒有至少兩個學生來源共同支持的明確優點" : "正在比對學生來源中的共同優點"];

  const challenge = (digest?.common_challenges || [])[0];
  const warningPoints = [];
  if (eligibility.tone === "needs-review") warningPoints.push(`資格初判：${truncate(eligibility.label, 68)}`);
  if (challenge) warningPoints.push(`學生提醒（${challenge.source_count} 個來源）：${truncate(challenge.summary, 68)}`);
  warningPoints.push(`合作校期限：${truncate(deadline, 62)}`);
  warningPoints.push(`語言條件：${truncate(partnerLanguageRequirement(item), 68)}`);

  const groups = [
    { label: "適合先列入候選，如果你…", icon: "badge-check", tone: "fit", source: "合作校公開條件", points: fitPoints.slice(0, 4) },
    { label: "學生常提到的優點", icon: "thumbs-up", tone: "positive", source: digest ? `${digest.total_sources} 個公開學生來源` : "學生來源整理中", points: positivePoints },
    { label: "申請前先確認", icon: "triangle-alert", tone: "caution", source: "官方條件與學生經驗分開標示", points: warningPoints.slice(0, 4) },
  ];
  return `
    <section class="quick-decision-fit" aria-labelledby="quick-decision-fit-title">
      <div class="quick-decision-heading"><div><span class="section-kicker">先判斷值不值得深入查</span><h3 id="quick-decision-fit-title">這間學校適合我嗎？</h3></div><span>摘要不取代正式資格審查</span></div>
      <div class="quick-decision-grid">
        ${groups.map((group) => `
          <article class="quick-decision-card ${group.tone}">
            <div><i data-lucide="${group.icon}" aria-hidden="true"></i><h4>${escapeHtml(group.label)}</h4></div>
            <small>${escapeHtml(group.source)}</small>
            <ul>${group.points.map((point) => `<li><strong>${renderSummaryText(point)}</strong></li>`).join("")}</ul>
          </article>`).join("")}
      </div>
    </section>`;
}

function updateQuickDecisionFit(digest) {
  const item = partnerByName(state.activeSchool);
  const container = $("#quick-decision-fit");
  if (!item || !container) return;
  container.innerHTML = renderQuickDecisionFit(item, digest);
  initIcons();
}

async function loadDestinationProfile(item) {
  const requestId = ++state.destinationRequestId;
  try {
    const profile = await fetchJson(`/destination-profile?school=${encodeURIComponent(item.school_name)}&home_school=${encodeURIComponent(activeHomeSchool())}`);
    if (requestId !== state.destinationRequestId || state.activeSchool !== item.school_name) return;
    state.destinationCache.set(item.school_name, profile);
    renderDestinationProfile(item, profile);
  } catch (error) {
    if (requestId !== state.destinationRequestId) return;
    const container = $("#destination-official-content");
    if (container) {
      container.setAttribute("aria-busy", "false");
      container.innerHTML = `<div class="destination-profile-status error"><i data-lucide="circle-alert" aria-hidden="true"></i><div><strong>官方生活資訊暫時無法載入</strong><p>${escapeHtml(error.message)}</p></div></div>`;
    }
    initIcons();
  }
}

function renderDestinationProfile(item, profile) {
  const container = $("#destination-official-content");
  if (!container) return;
  container.setAttribute("aria-busy", "false");
  $("#school-detail-primary-facts").innerHTML = renderPrimaryFacts(item, profile);
  if (profile.coverage_status === "not_collected") {
    container.innerHTML = `
      <div class="destination-profile-status pending">
        <i data-lucide="clock-3" aria-hidden="true"></i>
        <div><strong>官方生活資訊待查核</strong><p>目前先顯示學生公開心得；住宿與生活費數字尚未找到足夠的新官方來源。</p></div>
      </div>`;
    initIcons();
    return;
  }
  const facts = [
    ["所在地", profile.city],
    ["費用參考", profile.cost_summary],
    ["住宿", profile.housing_summary],
    ["交通", profile.transport_summary],
    ["校園生活", profile.campus_life_summary],
  ].filter(([, value]) => value);
  container.innerHTML = `
    <div class="destination-profile-status verified">
      <i data-lucide="badge-check" aria-hidden="true"></i>
      <div><strong>官方生活資訊已查核</strong><p>${escapeHtml(profile.coverage_note)}</p><small>最後查核：${escapeHtml(formatDate(profile.last_checked))}</small></div>
    </div>
    <div class="destination-facts">
      ${facts.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${highlightHtml(value)}</strong></div>`).join("")}
    </div>
    ${renderStudentSurvivalGuide(item, profile)}
    <details class="destination-source-library">
      <summary><span>查看本頁全部查核來源（${(profile.sources || []).length}）</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>
      <div class="destination-sources">
        ${(profile.sources || []).map((source) => `
          <article class="destination-source-card">
            <div><strong>${escapeHtml(source.title)}</strong><p>${source.summary ? highlightHtml(source.summary) : "此連結已收錄；若沒有足夠正文，不會把搜尋片段當成摘要。"}</p></div>
            <a href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer"><span>查看原始來源</span><i data-lucide="external-link" aria-hidden="true"></i></a>
          </article>`).join("")}
      </div>
    </details>`;
  initIcons();
}

const STUDENT_GUIDE_META = {
  courses_and_workload: { icon: "book-open-check", label: "課業" },
  faculty_and_teaching: { icon: "presentation", label: "師資" },
  housing_reality: { icon: "bed-double", label: "住宿" },
  neighborhood_and_daily_life: { icon: "store", label: "機能" },
  mobile_money_and_cards: { icon: "smartphone", label: "落地" },
  transport_and_arrival: { icon: "train-front", label: "交通" },
};

function guideEvidenceLabel(type) {
  return {
    official: "官方資料",
    student_experience: "學生心得",
    mixed: "官方＋心得",
    practical_inference: "實務建議",
  }[type] || "已查核資料";
}

function renderGuideSourceLinks(urls, profile, label = "查看依據") {
  const uniqueUrls = unique((urls || []).filter(Boolean));
  if (!uniqueUrls.length) return "";
  const sourceTitles = new Map((profile.sources || []).map((source) => [source.source_url, source.title]));
  return `<div class="student-guide-source-links" aria-label="${escapeHtml(label)}">${uniqueUrls.map((url, index) => `
    <a href="${escapeHtml(url)}" target="_blank" rel="noreferrer" title="${escapeHtml(sourceTitles.get(url) || `來源 ${index + 1}`)}">
      <span>${escapeHtml(label)} ${index + 1}</span><i data-lucide="external-link" aria-hidden="true"></i>
    </a>`).join("")}</div>`;
}

function renderGuideChecklist(items, profile) {
  return (items || []).map((entry, index) => `
    <li>
      <span class="student-guide-step-number">${index + 1}</span>
      <div>
        ${entry.timing ? `<small>${escapeHtml(entry.timing)}</small>` : ""}
        <strong>${escapeHtml(entry.title)}</strong>
        <p>${highlightHtml(entry.detail)}</p>
        <span class="student-guide-evidence">${escapeHtml(guideEvidenceLabel(entry.evidence_type))}</span>
        ${renderGuideSourceLinks(entry.source_urls, profile)}
      </div>
    </li>`).join("");
}

function renderStudentSurvivalGuide(item, profile) {
  const sections = profile.student_guide_sections || [];
  const dormPhotos = profile.guide_photos || [];
  const campusPhoto = item.image_url ? [{
    image_url: item.image_url,
    source_url: item.image_page_url || item.image_source_url || item.website,
    alt: `${item.school_name}校園照片`,
    caption: `${item.school_name}校園`,
    category: "campus",
  }] : [];
  const photos = [...campusPhoto, ...dormPhotos];
  const hasHousingPhoto = dormPhotos.some((photo) => photo.category === "housing");
  const photoHeading = hasHousingPhoto ? "校園與住宿照片" : "校園照片";
  const photoStatus = hasHousingPhoto
    ? `${photos.length} 張已附來源照片`
    : `${photos.length} 張已附來源校園照片 · 住宿照片待校方公開`;
  const firstHours = profile.first_72_hours || [];
  const bring = profile.packing_from_taiwan || [];
  const buyThere = profile.buy_after_arrival || [];
  if (!sections.length && !photos.length && !firstHours.length && !bring.length && !buyThere.length) return "";

  return `
    <section class="student-survival-guide" aria-labelledby="student-survival-title">
      <div class="student-guide-heading">
        <div><span class="section-kicker">給準備出發的交換生</span><h3 id="student-survival-title">交換生生存指南</h3></div>
        <p>把官方規則、可核對的學生心得與實務提醒分開標示；每個重點都可以回到原始來源。</p>
      </div>
      ${photos.length ? `
        <section class="student-guide-photo-section" aria-labelledby="student-guide-photos-title">
          <div class="student-guide-subheading"><div><i data-lucide="images" aria-hidden="true"></i><h4 id="student-guide-photos-title">${photoHeading}</h4></div><small>${photoStatus}</small></div>
          <div class="student-guide-photo-grid">
            ${photos.map((photo) => `
              <figure class="student-guide-photo ${escapeHtml(photo.category || "housing")}">
                <a href="${escapeHtml(photo.source_url || photo.image_url)}" target="_blank" rel="noreferrer">
                  <img src="${escapeHtml(photo.image_url)}" alt="${escapeHtml(photo.alt)}" loading="lazy" />
                  <span>${photo.category === "campus" ? "校園" : "住宿"}</span>
                </a>
                <figcaption>${escapeHtml(photo.caption)}</figcaption>
              </figure>`).join("")}
          </div>
        </section>` : ""}
      ${sections.length ? `
        <div class="student-guide-section-grid">
          ${sections.map((section) => {
            const meta = STUDENT_GUIDE_META[section.key] || { icon: "circle-help", label: "指南" };
            return `<article class="student-guide-section-card">
              <div class="student-guide-card-heading"><i data-lucide="${meta.icon}" aria-hidden="true"></i><div><span>${escapeHtml(meta.label)}</span><h4>${escapeHtml(section.title)}</h4></div></div>
              <p>${highlightHtml(section.summary)}</p>
              ${(section.points || []).length ? `<ul>${section.points.map((point) => `<li>${highlightHtml(point)}</li>`).join("")}</ul>` : ""}
              <div class="student-guide-card-footer"><span class="student-guide-evidence">${escapeHtml(guideEvidenceLabel(section.evidence_type))}</span>${section.caution ? `<small>${escapeHtml(section.caution)}</small>` : ""}</div>
              ${renderGuideSourceLinks(section.source_urls, profile)}
            </article>`;
          }).join("")}
        </div>` : ""}
      ${firstHours.length ? `
        <section class="student-guide-arrival" aria-labelledby="student-guide-arrival-title">
          <div class="student-guide-subheading"><div><i data-lucide="route" aria-hidden="true"></i><h4 id="student-guide-arrival-title">抵達後 72 小時</h4></div><small>照順序完成，先讓自己能通訊、付款、進校與選課</small></div>
          <ol>${renderGuideChecklist(firstHours, profile)}</ol>
        </section>` : ""}
      ${(bring.length || buyThere.length) ? `
        <section class="student-guide-packing" aria-labelledby="student-guide-packing-title">
          <div class="student-guide-subheading"><div><i data-lucide="luggage" aria-hidden="true"></i><h4 id="student-guide-packing-title">帶什麼去，什麼到當地再買</h4></div></div>
          <div class="student-guide-packing-grid">
            <article><div class="student-guide-packing-title"><i data-lucide="plane" aria-hidden="true"></i><h5>在臺灣先準備</h5></div><ol>${renderGuideChecklist(bring, profile)}</ol></article>
            <article><div class="student-guide-packing-title"><i data-lucide="shopping-bag" aria-hidden="true"></i><h5>抵達後再買</h5></div><ol>${renderGuideChecklist(buyThere, profile)}</ol></article>
          </div>
        </section>` : ""}
    </section>`;
}

function renderStudentLife(digest) {
  const container = $("#life-content");
  if (!container) return;
  container.setAttribute("aria-busy", "false");
  const rankedSections = LIFE_SECTIONS.map((section, index) => {
    const themes = section.relatedThemes || [section.theme];
    const highlight = (digest.highlights || []).find((item) => themes.includes(item.theme));
    return { section, highlight, index };
  }).sort((left, right) => {
    const leftRank = (left.highlight?.key_points || []).length ? 2 : Number(left.highlight?.source_count || 0) > 0 ? 1 : 0;
    const rightRank = (right.highlight?.key_points || []).length ? 2 : Number(right.highlight?.source_count || 0) > 0 ? 1 : 0;
    if (leftRank !== rightRank) return rightRank - leftRank;
    const sourceDifference = Number(right.highlight?.source_count || 0) - Number(left.highlight?.source_count || 0);
    return sourceDifference || left.index - right.index;
  });
  container.innerHTML = rankedSections.map(({ section, highlight }) => {
    const points = highlight ? buildLifeKeyPoints(highlight) : [];
    const hasConcretePoints = points.length > 0;
    return `
      <article class="life-card${highlight ? " has-sources" : " needs-sources"}">
        <div class="life-card-heading"><i data-lucide="${section.icon}" aria-hidden="true"></i><div><h3>${escapeHtml(section.label)}</h3><span>${highlight ? `${highlight.source_count} 個來源已整理` : "公開來源不足"}</span></div></div>
        ${
          highlight
            ? `${hasConcretePoints
                ? `<ul class="life-key-points">${points.map((point) => `<li><strong>${highlightHtml(point)}</strong></li>`).join("")}</ul>`
                : `<div class="life-extraction-pending"><strong>已嘗試讀取，但原文內容不足或受限</strong><p>這些連結目前沒有可核對的全文重點，因此只保留來源，不把搜尋片段當成摘要。</p></div>`}
               <details class="life-details"><summary><span>查看${hasConcretePoints ? "完整整理與" : "原始"}來源</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>${hasConcretePoints ? `<p>${highlightHtml(highlight.summary)}</p>` : ""}${renderLifeSourceLinks(highlight)}<small>學生經驗會因年份、科系與個人習慣不同。</small></details>`
            : `<ul class="life-key-points life-source-status"><li><strong>尚無足夠的公開學生來源</strong></li><li><strong>不以一般學校介紹代替真實經驗</strong></li></ul><p>目前無法可靠統整「${escapeHtml(section.prompt)}」。</p><small>找到可驗證的文章、影片或投稿後才會補入。</small>`
        }
      </article>`;
  }).join("");
  initIcons();
}

function experienceKeyPoints(summary) {
  const seen = new Set();
  return String(summary || "")
    .split(/[。；;]/)
    .map((point) => point.replace(/^\d+\s*個來源提到這個面向[，。]?/, "").trim())
    .filter((point) => point.length >= 8)
    .filter((point) => {
      const key = normalize(point);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 4);
}

function buildLifeKeyPoints(highlight) {
  const points = Array.isArray(highlight.key_points)
    ? highlight.key_points.map((point) => String(point || "").trim()).filter(Boolean)
    : experienceKeyPoints(highlight.summary).filter((point) => !/^(這個來源主要談到|這個公開來源|來源談到|\d+\s*個來源)/.test(point));
  return unique(points).slice(0, 4);
}

function renderLifeSourceLinks(highlight) {
  const links = (highlight.source_urls || []).slice(0, 4);
  if (!links.length) return "";
  return `<div class="life-source-links" aria-label="此生活面向的學生來源">${links
    .map((url, index) => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer"><span>查看學生來源 ${index + 1}</span><i data-lucide="external-link" aria-hidden="true"></i></a>`)
    .join("")}</div>`;
}

function activateDetailTab(targetId, { focus = false, scroll = false } = {}) {
  const tabs = [...document.querySelectorAll('.detail-tabs [role="tab"]')];
  const panels = [...document.querySelectorAll('#school-detail-content [role="tabpanel"]')];
  if (!tabs.some((tab) => tab.dataset.detailTarget === targetId)) return;

  tabs.forEach((tab) => {
    const selected = tab.dataset.detailTarget === targetId;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    if (selected && focus) tab.focus();
  });
  panels.forEach((panel) => {
    panel.hidden = panel.id !== targetId;
  });
  if (scroll) {
    $("#school-detail-content")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function renderApplicationTracker(item) {
  const schoolProgress = state.applicationProgress[item.school_name] || {};
  const completed = APPLICATION_PROGRESS_STEPS.filter((step) => schoolProgress[step.id]).length;
  const percentage = Math.round((completed / APPLICATION_PROGRESS_STEPS.length) * 100);
  return `
    <div class="tracker-progress"><div><strong>${percentage}%</strong><span>${completed} / ${APPLICATION_PROGRESS_STEPS.length} 已完成</span></div><div class="progress-track" aria-hidden="true"><span style="width:${percentage}%"></span></div></div>
    <div class="tracker-checklist">${APPLICATION_PROGRESS_STEPS.map((step) => `<label><input class="progress-checkbox" type="checkbox" data-progress-step="${step.id}" ${schoolProgress[step.id] ? "checked" : ""} /><span>${escapeHtml(step.label)}</span></label>`).join("")}</div>`;
}

function updateApplicationProgress(stepId, checked) {
  if (!state.activeSchool) return;
  const current = { ...(state.applicationProgress[state.activeSchool] || {}) };
  current[stepId] = checked;
  state.applicationProgress[state.activeSchool] = current;
  try {
    window.localStorage.setItem(STORAGE_KEYS.progress, JSON.stringify(state.applicationProgress));
  } catch (_) {
    // Progress still works for this session.
  }
  const item = partnerByName(state.activeSchool);
  if (item) $("#application-tracker").innerHTML = renderApplicationTracker(item);
}

function renderWorkflowLoading() {
  return `
    <div class="workflow-loading" role="status">
      <span>正在查核${escapeHtml(activeUniversityProfile().short_name)}與合作校官方申請流程…</span>
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
    </div>`;
}

async function loadApplicationWorkflow(item, { forceRefresh = false } = {}) {
  const requestId = ++state.workflowRequestId;
  const content = $("#workflow-content");
  if (!content) return;
  content.setAttribute("aria-busy", "true");
  content.innerHTML = renderWorkflowLoading();

  try {
    const school = encodeURIComponent(item.school_name);
    let workflow = forceRefresh
      ? await fetchJson(`/application-workflow/refresh?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`, { method: "POST" })
      : await fetchJson(`/application-workflow?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`);
    if (!forceRefresh && !workflow.steps?.length) {
      workflow = await fetchJson(`/application-workflow/refresh?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`, { method: "POST" });
    }
    if (requestId !== state.workflowRequestId || state.activeSchool !== item.school_name) return;
    state.workflowCache.set(item.school_name, workflow);
    renderApplicationWorkflow(workflow);
  } catch (error) {
    if (requestId !== state.workflowRequestId) return;
    content.setAttribute("aria-busy", "false");
    content.innerHTML = `
      <div class="experience-error">
        <strong>暫時無法查核官方申請流程</strong>
        <p>${escapeHtml(error.message)}</p>
        <button id="retry-workflow" type="button" class="secondary-button">重新查核</button>
      </div>`;
  }
  initIcons();
}

function renderApplicationWorkflow(workflow) {
  const content = $("#workflow-content");
  if (!content) return;
  content.setAttribute("aria-busy", "false");
  if (!workflow.steps?.length) {
    content.innerHTML = `
      <div class="empty-state">
        <i data-lucide="list-checks" aria-hidden="true"></i>
        <strong>尚未建立這所學校的官方流程</strong>
        <span>${escapeHtml(workflow.coverage_note)}</span>
        <button id="retry-workflow" type="button" class="secondary-button">立即查核官方資料</button>
      </div>`;
    initIcons();
    return;
  }

  content.innerHTML = `
    <div class="workflow-status ${workflow.coverage_status === "official_verified" ? "verified" : "partial"}">
      <i data-lucide="${workflow.coverage_status === "official_verified" ? "badge-check" : "triangle-alert"}" aria-hidden="true"></i>
      <div>
        <strong>${workflow.coverage_status === "official_verified" ? "官方來源已查核" : "部分細節需再確認"}</strong>
        <p>${escapeHtml(workflow.coverage_note)}</p>
        <small>最後查核：${escapeHtml(formatDate(workflow.last_checked))}</small>
      </div>
    </div>
    <div class="workflow-toolbar">
      <strong>共 ${workflow.steps.length} 個步驟</strong>
      <button id="refresh-workflow" type="button" class="secondary-button">
        <i data-lucide="refresh-cw" aria-hidden="true"></i><span>重新查核官方流程</span>
      </button>
    </div>
    <div class="workflow-timeline">
      ${workflow.steps.map(renderWorkflowStep).join("")}
    </div>
    <div class="workflow-sources">
      <strong>本流程使用的官方來源</strong>
      <div>
        ${(workflow.sources || [])
          .map(
            (source) => `<a href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer">
              <span>${escapeHtml(source.title)}</span><i data-lucide="external-link" aria-hidden="true"></i>
            </a>`
          )
          .join("")}
      </div>
      <p>${escapeHtml(workflow.disclaimer)}</p>
    </div>`;
  initIcons();
}

function renderWorkflowStep(step, index) {
  const visibleStepCount = window.matchMedia("(min-width: 821px)").matches ? 2 : 1;
  const expanded = index < visibleStepCount ? "open" : "";
  return `
    <details class="workflow-step${step.needs_confirmation ? " needs-confirmation" : ""}" ${expanded}>
      <summary>
        <span class="workflow-step-number" aria-hidden="true">${escapeHtml(step.order)}</span>
        <span class="workflow-step-title">
          <small>${escapeHtml(step.phase)} · ${escapeHtml(step.responsible_party)}</small>
          <strong>${escapeHtml(step.title)}</strong>
          ${step.timing ? `<span><i data-lucide="calendar-clock" aria-hidden="true"></i>${highlightHtml(step.timing)}</span>` : ""}
        </span>
        <i data-lucide="chevron-down" aria-hidden="true"></i>
      </summary>
      <div class="workflow-step-body">
        <p>${highlightHtml(step.summary)}</p>
        ${step.needs_confirmation ? `<div class="workflow-warning"><i data-lucide="triangle-alert" aria-hidden="true"></i><strong>此步驟有日期或規定差異，送件前必須向官方確認。</strong></div>` : ""}
        ${step.details?.length ? `<div><h4>具體要做</h4><ul>${step.details.map((detail) => `<li>${highlightHtml(detail)}</li>`).join("")}</ul></div>` : ""}
        ${step.required_documents?.length ? `<div><h4>這一步要準備</h4><ul class="workflow-documents">${step.required_documents.map((document) => `<li><i data-lucide="file-check-2" aria-hidden="true"></i><span>${highlightHtml(document)}</span></li>`).join("")}</ul></div>` : ""}
        ${step.action_url ? `<a class="official-link workflow-action" href="${escapeHtml(step.action_url)}" target="_blank" rel="noreferrer"><span>開啟這一步的官方頁面</span><i data-lucide="external-link" aria-hidden="true"></i></a>` : ""}
      </div>
    </details>`;
}

function renderExperienceLoading() {
  return `
    <div class="experience-loading" role="status">
      <span>正在整理公開學生文章與影片…</span>
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
    </div>`;
}

async function loadStudentExperiences(item, { forceRefresh = false } = {}) {
  const requestId = ++state.experienceRequestId;
  const content = $("#experience-content");
  if (!content) return;
  content.setAttribute("aria-busy", "true");
  content.innerHTML = renderExperienceLoading();

  try {
    const school = encodeURIComponent(item.school_name);
    let digest = forceRefresh
      ? await fetchJson(`/student-experiences/refresh?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`, { method: "POST" })
      : await fetchJson(`/student-experiences?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`);
    if (requestId !== state.experienceRequestId || state.activeSchool !== item.school_name) return;
    state.experienceCache.set(item.school_name, digest);
    renderExperienceDigest(digest);
  } catch (error) {
    if (requestId !== state.experienceRequestId) return;
    renderStudentLife({ highlights: [] });
    content.setAttribute("aria-busy", "false");
    content.innerHTML = `
      <div class="experience-error">
        <strong>暫時無法取得學生心得</strong>
        <p>${escapeHtml(error.message)}</p>
        <button id="retry-experiences" type="button" class="secondary-button">重新嘗試</button>
      </div>`;
  }
  initIcons();
}

function renderExperienceDigest(digest) {
  const content = $("#experience-content");
  if (!content) return;
  updateQuickDecisionFit(digest);
  renderStudentLife(digest);
  content.setAttribute("aria-busy", "false");
  if (!digest.total_sources) {
    content.innerHTML = `
      <div class="empty-state">
        <i data-lucide="search-x" aria-hidden="true"></i>
        <strong>目前沒有足夠相關的公開心得</strong>
        <span>${escapeHtml(digest.coverage_note)}</span>
        <button id="retry-experiences" type="button" class="secondary-button">重新搜尋公開來源</button>
      </div>`;
    initIcons();
    return;
  }

  content.innerHTML = `
    <div class="experience-counts" aria-label="心得來源統計">
      <span>${digest.total_sources} 個來源</span>
      <span>${digest.article_count} 篇文章</span>
      <span>${digest.video_count} 部影片</span>
      <span>${digest.community_count} 則社群討論</span>
    </div>
    <div class="experience-disclaimer">
      <i data-lucide="info" aria-hidden="true"></i>
      <p>${escapeHtml(digest.coverage_note)} ${escapeHtml(digest.disclaimer)}</p>
    </div>
    ${renderExperienceDecisionSummary(digest)}
    <div class="experience-highlights">
      ${digest.highlights
        .map(
          (highlight) => `
            <article class="experience-highlight">
              <span>${highlight.source_count} 個來源</span>
              <h4>${escapeHtml(highlight.title)}</h4>
              <p>${highlightHtml(highlight.summary)}</p>
            </article>`
        )
        .join("")}
    </div>
    <div class="experience-source-heading">
      <h4>心得文章與影片</h4>
      <button id="refresh-experiences" type="button" class="secondary-button">
        <i data-lucide="refresh-cw" aria-hidden="true"></i><span>重新搜尋</span>
      </button>
    </div>
    <div class="experience-source-grid">
      ${digest.sources.map(renderExperienceSource).join("")}
    </div>`;
  initIcons();
}

function renderExperienceDecisionSummary(digest) {
  const groups = [
    { key: "common_strengths", label: "大家常提到的優點", icon: "thumbs-up", tone: "positive", empty: "目前沒有至少兩個來源共同支持的明確優點。" },
    { key: "common_challenges", label: "缺點與踩雷提醒", icon: "triangle-alert", tone: "challenge", empty: "目前沒有足夠來源支持明確的踩雷提醒。" },
    { key: "mixed_opinions", label: "看法分歧的地方", icon: "split", tone: "mixed", empty: "目前沒有同時出現正反描述的生活面向。" },
  ];
  const years = digest.source_years?.length ? digest.source_years.join("、") : "未標示年份";
  return `
    <section class="experience-decision-summary" aria-label="學生心得決策摘要">
      <div class="experience-years"><i data-lucide="calendar-search" aria-hidden="true"></i><span>目前來源年份：<strong>${escapeHtml(years)}</strong></span></div>
      <div class="experience-insight-grid">
        ${groups.map((group) => {
          const insights = digest[group.key] || [];
          return `<article class="experience-insight ${group.tone}">
            <div class="experience-insight-heading"><i data-lucide="${group.icon}" aria-hidden="true"></i><h4>${escapeHtml(group.label)}</h4></div>
            ${insights.length ? `<ul>${insights.slice(0, 3).map((item) => `<li><strong>${escapeHtml(item.title.replace(/^常見優點：|^常見提醒：|^看法分歧：/, ""))}</strong><span>${highlightHtml(truncate(item.summary, 180))}</span><small>${item.source_count} 個來源統整</small>${(item.source_urls || []).length ? `<div class="experience-insight-sources">${item.source_urls.slice(0, 4).map((url, index) => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer"><span>依據 ${index + 1}</span><i data-lucide="external-link" aria-hidden="true"></i></a>`).join("")}</div>` : ""}</li>`).join("")}</ul>` : `<p>${escapeHtml(group.empty)}</p>`}
          </article>`;
        }).join("")}
      </div>
    </section>`;
}

function renderCommunityLoading() {
  return `<div class="community-loading" role="status"><span>正在載入校友社群…</span><div class="skeleton skeleton-card"></div></div>`;
}

function communityAuthHeaders() {
  if (!state.anonymousIdentity) return {};
  return {
    "X-Anonymous-ID": state.anonymousIdentity.id,
    "X-Anonymous-Token": state.anonymousIdentity.access_token,
  };
}

async function ensureAnonymousIdentity() {
  if (state.anonymousIdentity?.id && state.anonymousIdentity?.access_token) return state.anonymousIdentity;
  if (!state.account) {
    openAuthDialog();
    throw new Error("登入後才能發文、留言或使用私訊。");
  }
  const session = await fetchJson("/auth/community-identity", { method: "POST" });
  state.anonymousIdentity = session;
  try {
    window.localStorage.setItem(STORAGE_KEYS.communityIdentity, JSON.stringify(session));
  } catch (_) {
    // The anonymous session remains available until this tab is closed.
  }
  return session;
}

async function fetchCommunityAuth(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {}),
      ...communityAuthHeaders(),
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `伺服器回應 ${response.status}`);
  return data;
}

async function loadCommunityQuestions(item) {
  const requestId = ++state.communityRequestId;
  const content = $("#community-content");
  if (!content) return;
  content.setAttribute("aria-busy", "true");
  content.innerHTML = renderCommunityLoading();
  try {
    const school = encodeURIComponent(item.school_name);
    if (state.account) await ensureAnonymousIdentity();
    const [questions, posts, chat, conversations] = await Promise.all([
      fetchJson(`/community/questions?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`),
      fetchJson(`/community/posts?school=${school}`),
      fetchJson(`/community/chat?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`),
      state.account ? fetchCommunityAuth("/community/conversations") : Promise.resolve([]),
    ]);
    const conversationMessages = await Promise.all(
      conversations.map(async (conversation) => [
        conversation.id,
        await fetchCommunityAuth(`/community/conversations/${encodeURIComponent(conversation.id)}/messages`),
      ])
    );
    if (requestId !== state.communityRequestId || state.activeSchool !== item.school_name) return;
    const hub = { questions, posts, chat, conversations, messages: Object.fromEntries(conversationMessages) };
    state.communityCache.set(item.school_name, hub);
    renderCommunityThreads(hub);
  } catch (error) {
    if (requestId !== state.communityRequestId) return;
    content.setAttribute("aria-busy", "false");
    content.innerHTML = `<div class="experience-error"><strong>暫時無法載入校友社群</strong><p>${escapeHtml(error.message)}</p><button type="button" id="retry-community" class="secondary-button">重新載入</button></div>`;
  }
  initIcons();
}

function renderCommunityThreads(hub) {
  const content = $("#community-content");
  if (!content) return;
  content.setAttribute("aria-busy", "false");
  const data = Array.isArray(hub)
    ? { questions: hub, posts: [], chat: [], conversations: [], messages: {} }
    : hub;
  const identity = state.anonymousIdentity;
  content.innerHTML = `
    <div class="community-identity-bar">
      <span><i data-lucide="shield-check" aria-hidden="true"></i><strong>${escapeHtml(identity?.display_name || "訪客瀏覽")}</strong></span>
      <small>${state.account ? "公開只顯示暱稱；請勿張貼聯絡方式或個資。" : "登入後可以發文、留言與使用邀請制私訊。"}</small>
    </div>
    <div class="community-mode-switch" role="tablist" aria-label="社群功能">
      ${[
        ["posts", "動態貼文", "layout-list"],
        ["chat", "公開聊天室", "messages-square"],
        ["messages", "私訊", "mail"],
      ].map(([view, label, icon]) => `<button type="button" role="tab" data-community-view="${view}" aria-selected="${state.communityView === view}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${label}</span></button>`).join("")}
    </div>
    <section class="community-pane" data-community-pane="posts" ${state.communityView === "posts" ? "" : "hidden"}>
      ${state.account ? renderCommunityPostComposer() : '<button type="button" class="secondary-button" data-open-auth><i data-lucide="log-in" aria-hidden="true"></i><span>登入後參與討論</span></button>'}
      <div class="community-post-list">${data.posts.length ? data.posts.map(renderCommunityPostThread).join("") : renderCommunityEmpty("還沒有公開貼文", "分享申請問題、住宿情報或實際交換經驗，其他學生就能一起補充。")}</div>
      ${data.questions.length ? `<details class="legacy-community-questions"><summary><span>查看既有公開問答</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div class="community-thread-list">${data.questions.map(renderCommunityThread).join("")}</div></details>` : ""}
    </section>
    <section class="community-pane" data-community-pane="chat" ${state.communityView === "chat" ? "" : "hidden"}>
      <div class="public-chat-stream">${data.chat.length ? data.chat.map(renderPublicChatMessage).join("") : renderCommunityEmpty("聊天室還沒有訊息", "可以先詢問是否有人正在申請同一間學校。")}</div>
      ${state.account ? '<form id="public-chat-form" class="community-inline-composer"><label class="sr-only" for="public-chat-body">公開訊息</label><input id="public-chat-body" name="body" minlength="2" maxlength="500" required placeholder="公開詢問這間學校的申請或生活…" /><button type="submit" class="primary-button" aria-label="送出公開訊息"><i data-lucide="send" aria-hidden="true"></i><span>送出</span></button><div class="form-status" role="status"></div></form>' : '<button type="button" class="secondary-button" data-open-auth>登入後加入聊天</button>'}
    </section>
    <section class="community-pane" data-community-pane="messages" ${state.communityView === "messages" ? "" : "hidden"}>
      ${state.account ? '<form id="private-invite-form" class="private-invite-form" hidden><div><span class="section-kicker">私訊邀請</span><strong id="private-invite-name">匿名學生</strong></div><input type="hidden" name="recipient_id" /><label><span>先說明想請教的事情</span><textarea name="initial_message" minlength="5" maxlength="500" required placeholder="對方接受邀請後，才能繼續私訊。"></textarea></label><div class="community-form-footer"><button type="button" class="secondary-button" data-cancel-invite>取消</button><button type="submit" class="primary-button"><i data-lucide="mail-plus" aria-hidden="true"></i><span>送出邀請</span></button><div class="form-status" role="status"></div></div></form>' : ""}
      <div class="private-conversation-list">${state.account ? (data.conversations.length ? data.conversations.map((conversation) => renderPrivateConversation(conversation, data.messages[conversation.id] || [])).join("") : renderCommunityEmpty("目前沒有私訊", "從公開貼文或聊天室點選「邀請私訊」，對方接受後才能對話。")) : renderCommunityEmpty("登入後使用私訊", "雙方同意後才能開始對話，也可以隨時封鎖與檢舉。")}</div>
    </section>`;
  initIcons();
}

function renderCommunityEmpty(title, detail) {
  return `<div class="community-empty"><i data-lucide="message-circle" aria-hidden="true"></i><div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(detail)}</p></div></div>`;
}

function renderCommunityPostComposer() {
  return `<details class="community-post-composer"><summary><span><i data-lucide="square-pen" aria-hidden="true"></i><strong>發一篇匿名貼文</strong><small>提問、討論或分享交換經驗</small></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><form id="community-post-form" class="community-form"><label><span>貼文類型</span><select name="post_type"><option value="discussion">討論</option><option value="question">提問</option><option value="experience">經驗分享</option></select></label><label><span>標題</span><input name="title" minlength="4" maxlength="120" required placeholder="讓其他學生一眼看懂你想討論什麼" /></label><label><span>內容</span><textarea name="body" minlength="10" maxlength="1600" required placeholder="提供年份、學期或具體情境，會更容易獲得有用回覆。"></textarea></label><div class="community-form-footer"><div class="form-status" role="status"></div><button type="submit" class="primary-button"><i data-lucide="send" aria-hidden="true"></i><span>立即發布</span></button></div></form></details>`;
}

function renderCommunityPostThread(thread, { global = false } = {}) {
  const post = thread.post;
  const comments = thread.comments || [];
  const canInvite = !global && state.account && post.author_id !== state.anonymousIdentity?.id;
  const meta = [
    communityTopicLabel(post.topic),
    post.country,
    post.academic_year,
    applicationStageLabel(post.application_stage),
  ].filter(Boolean);
  const publicBoard = [PUBLIC_COMMUNITY_BOARD, LEGACY_PUBLIC_COMMUNITY_BOARD].includes(post.school_name);
  const universityBoard = state.supportedUniversities.some(
    (item) => normalize(item.school_name) === normalize(post.school_name)
  );
  let schoolAction = `<span><i data-lucide="globe-2" aria-hidden="true"></i>${PUBLIC_COMMUNITY_BOARD}</span>`;
  if (universityBoard) {
    schoolAction = `<a class="text-action post-board-link" href="#board=${encodeURIComponent(post.school_name)}"><i data-lucide="graduation-cap" aria-hidden="true"></i><span>${escapeHtml(post.school_name)}板</span></a>`;
  } else if (global && !publicBoard) {
    schoolAction = `<button type="button" class="text-action school-detail-trigger" data-school-name="${escapeHtml(post.school_name)}"><i data-lucide="school" aria-hidden="true"></i><span>${escapeHtml(post.school_name)}</span></button>`;
  }
  const commentComposer = state.account
    ? `<form class="community-inline-composer post-comment-form" data-post-id="${escapeHtml(post.id)}"><label class="sr-only">回覆內容</label><input name="body" minlength="2" maxlength="800" required placeholder="補充具體資訊…" /><button type="submit" class="secondary-button"><i data-lucide="reply" aria-hidden="true"></i><span>回覆</span></button><div class="form-status" role="status"></div></form>`
    : '<button type="button" class="secondary-button" data-open-auth><i data-lucide="log-in" aria-hidden="true"></i><span>登入後回覆</span></button>';
  return `<article class="community-post-card" data-community-school="${escapeHtml(post.school_name)}">
    <div class="community-post-meta"><span>${escapeHtml({ discussion: "討論", question: "請益", experience: "經驗" }[post.post_type] || "貼文")}</span><span>${escapeHtml(meta.join(" · "))}</span><time>${escapeHtml(formatDate(post.created_at))}</time></div>
    <h3>${escapeHtml(post.title)}</h3><p>${escapeHtml(post.body)}</p>
    <div class="community-post-context">${schoolAction}</div>
    <div class="community-author-row"><strong>${escapeHtml(post.display_name)}</strong><div>${canInvite ? `<button type="button" class="text-action" data-invite-recipient="${escapeHtml(post.author_id)}" data-recipient-name="${escapeHtml(post.display_name)}"><i data-lucide="mail-plus" aria-hidden="true"></i><span>邀請私訊</span></button>` : ""}<button type="button" class="icon-action" data-report-resource="post" data-resource-id="${escapeHtml(post.id)}" aria-label="檢舉這篇貼文"><i data-lucide="flag" aria-hidden="true"></i></button></div></div>
    <details class="community-comments"><summary><span>${comments.length} 則回覆</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div>${comments.map((comment) => `<article><strong>${escapeHtml(comment.display_name)}</strong><p>${escapeHtml(comment.body)}</p></article>`).join("") || '<p class="no-answer">還沒有回覆。</p>'}${commentComposer}</div></details>
  </article>`;
}

function renderPublicChatMessage(message) {
  const canInvite = message.author_id !== state.anonymousIdentity?.id;
  return `<article class="public-chat-message"><div><strong>${escapeHtml(message.display_name)}</strong><time>${escapeHtml(formatDate(message.created_at))}</time></div><p>${escapeHtml(message.body)}</p><div class="chat-message-actions">${canInvite ? `<button type="button" class="text-action" data-invite-recipient="${escapeHtml(message.author_id)}" data-recipient-name="${escapeHtml(message.display_name)}"><i data-lucide="mail-plus" aria-hidden="true"></i><span>邀請私訊</span></button>` : ""}<button type="button" class="icon-action" data-report-resource="chat" data-resource-id="${escapeHtml(message.id)}" aria-label="檢舉這則訊息"><i data-lucide="flag" aria-hidden="true"></i></button></div></article>`;
}

function renderPrivateConversation(conversation, messages) {
  const me = state.anonymousIdentity?.id;
  const otherId = conversation.sender_id === me ? conversation.recipient_id : conversation.sender_id;
  const otherName = conversation.sender_id === me ? conversation.recipient_name : conversation.sender_name;
  const isRecipient = conversation.recipient_id === me;
  const accepted = conversation.status === "accepted";
  return `<details class="private-conversation" ${accepted ? "" : "open"}><summary><span><strong>${escapeHtml(otherName)}</strong><small>${accepted ? "私訊中" : isRecipient ? "等待你接受邀請" : "等待對方接受"}</small></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div class="private-conversation-body"><div class="private-message-stream">${messages.map((message) => `<article class="${message.author_id === me ? "is-mine" : ""}"><strong>${escapeHtml(message.display_name)}</strong><p>${escapeHtml(message.body)}</p><time>${escapeHtml(formatDate(message.created_at))}</time></article>`).join("")}</div>${!accepted && isRecipient ? `<button type="button" class="primary-button" data-accept-conversation="${escapeHtml(conversation.id)}"><i data-lucide="check" aria-hidden="true"></i><span>接受私訊邀請</span></button>` : ""}${accepted ? `<form class="community-inline-composer private-message-form" data-conversation-id="${escapeHtml(conversation.id)}"><label class="sr-only">私訊內容</label><input name="body" minlength="2" maxlength="1000" required placeholder="輸入私訊…" /><button type="submit" class="primary-button" aria-label="傳送私訊"><i data-lucide="send" aria-hidden="true"></i><span>傳送</span></button><div class="form-status" role="status"></div></form>` : ""}<button type="button" class="text-action danger" data-block-identity="${escapeHtml(otherId)}"><i data-lucide="ban" aria-hidden="true"></i><span>封鎖</span></button></div></details>`;
}

function renderCommunityThread(thread) {
  const question = thread.question;
  const answers = thread.answers || [];
  return `
    <details class="community-thread">
      <summary>
        <span><small>${escapeHtml(communityTopicLabel(question.topic))} · ${escapeHtml(question.home_university)}</small><strong>${escapeHtml(question.title)}</strong><span>${answers.length} 個公開回答</span></span>
        <i data-lucide="chevron-down" aria-hidden="true"></i>
      </summary>
      <div class="community-thread-body">
        <p>${escapeHtml(question.body)}</p>
        <small>${escapeHtml(question.display_name)} · ${escapeHtml(formatDate(question.created_at))}</small>
        <div class="community-answers">${answers.length ? answers.map((answer) => `<article><div><strong>${escapeHtml(answer.display_name)}</strong>${answer.exchange_year ? `<span>${escapeHtml(answer.exchange_year)} 交換</span>` : ""}${answer.verified_experience ? '<span class="verified-label">經驗已驗證</span>' : ""}</div><p>${escapeHtml(answer.body)}</p></article>`).join("") : '<p class="no-answer">目前還沒有公開回答。</p>'}</div>
        <details class="answer-contribution"><summary><span>分享你的經驗回答</span><i data-lucide="message-square-reply" aria-hidden="true"></i></summary>
          <form class="community-form answer-form" data-question-id="${escapeHtml(question.id)}">
            <label><span>回答內容</span><textarea name="body" minlength="10" maxlength="1500" required placeholder="請提供具體年份、情境與實際經驗，避免只寫好或不好。"></textarea></label>
            <div class="form-row"><label><span>顯示名稱</span><input name="display_name" value="匿名學長姐" minlength="2" maxlength="30" required /></label><label><span>交換年份</span><input name="exchange_year" inputmode="numeric" maxlength="20" placeholder="例如 2025" /></label></div>
            <label class="consent-check"><input name="accept_rules" type="checkbox" required /><span>我不會填寫 Email、電話、社群帳號或他人個資，並同意內容先經審核。</span></label>
            <div class="community-form-footer"><div class="form-status" role="status"></div><button type="submit" class="primary-button"><span>送出回答</span><i data-lucide="send" aria-hidden="true"></i></button></div>
          </form>
        </details>
      </div>
    </details>`;
}

function renderCommunityContributionForms(item) {
  const themes = [
    ["housing", "住宿"], ["cost", "生活費"], ["transport", "交通"], ["academics", "課業"],
    ["social", "社交"], ["support", "醫療／支援"], ["travel", "旅行"], ["challenges", "踩雷提醒"],
  ];
  return `
    <div class="community-contribution-grid">
      <details class="contribution-panel" open>
        <summary><span><i data-lucide="circle-help" aria-hidden="true"></i><strong>我要問問題</strong><small>公開問答，不交換私人聯絡方式</small></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>
        <form id="question-form" class="community-form">
          <label><span>問題分類</span><select name="topic" required><option value="application">申請</option><option value="housing">住宿</option><option value="academics">課業</option><option value="life">生活</option><option value="pre_departure">行前準備</option></select></label>
          <label><span>問題標題</span><input name="title" minlength="4" maxlength="120" required placeholder="例如：宿舍通常什麼時候開始申請？" /></label>
          <label><span>想問的具體情況</span><textarea name="body" minlength="10" maxlength="1000" required placeholder="寫出你想申請的學期與真正卡住的地方，回答會更有幫助。"></textarea></label>
          <label><span>顯示名稱</span><input name="display_name" value="匿名學生" minlength="2" maxlength="30" required /></label>
          <label class="consent-check"><input name="accept_rules" type="checkbox" required /><span>我不會填寫 Email、電話、社群帳號或他人個資，並同意問題先經審核。</span></label>
          <div class="community-form-footer"><div class="form-status" role="status"></div><button type="submit" class="primary-button"><span>送出問題</span><i data-lucide="send" aria-hidden="true"></i></button></div>
        </form>
      </details>
      <details class="contribution-panel">
        <summary><span><i data-lucide="notebook-pen" aria-hidden="true"></i><strong>投稿交換經驗</strong><small>提供實際年份與情境，審核後加入心得整理</small></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>
        <form id="experience-submission-form" class="community-form">
          <div class="form-row"><label><span>心得標題</span><input name="title" minlength="4" maxlength="120" required placeholder="例如：2025 林肯大學住宿與交通" /></label><label><span>交換年份</span><input name="exchange_year" minlength="4" maxlength="20" required placeholder="例如 2025" /></label></div>
          <label><span>經驗摘要</span><textarea name="summary" minlength="20" maxlength="2000" required placeholder="建議寫出住宿方式、每月花費、交通、課程與你最想提醒學弟妹的事。"></textarea></label>
          <fieldset><legend>內容包含哪些面向</legend><div class="submission-themes">${themes.map(([value, label]) => `<label><input type="checkbox" name="themes" value="${value}" /><span>${label}</span></label>`).join("")}</div></fieldset>
          <label><span>原始文章或影片連結（選填）</span><input name="source_url" type="url" maxlength="500" placeholder="https://" /></label>
          <label><span>顯示名稱</span><input name="display_name" value="匿名投稿者" minlength="2" maxlength="30" required /></label>
          <label class="consent-check"><input name="consent_to_publish" type="checkbox" required /><span>這是我的經驗或我有權提供的內容；我同意審核後以摘要方式公開並保留來源。</span></label>
          <div class="community-form-footer"><div class="form-status" role="status"></div><button type="submit" class="primary-button"><span>送出投稿</span><i data-lucide="send" aria-hidden="true"></i></button></div>
        </form>
      </details>
    </div>`;
}

function communityTopicLabel(topic) {
  return { application: "申請", scholarship: "獎學金", housing: "住宿", cost: "生活費", visa: "簽證", academics: "課業", life: "生活", career: "就業", warning: "避雷", pre_departure: "行前準備" }[topic] || topic;
}

function applicationStageLabel(stage) {
  return { exploring: "探索中", preparing: "準備申請", eligibility: "確認資格", documents: "準備文件", submitted: "已送件", accepted: "已錄取", abroad: "正在海外", returned: "已返台" }[stage] || "";
}

function followedBoardSet() {
  return new Set(state.account?.followed_boards || []);
}

function renderBoardFollowControls() {
  const followedBoards = followedBoardSet();
  document.querySelectorAll("[data-follow-board]").forEach((button) => {
    const boardName = button.dataset.followBoard;
    const followed = followedBoards.has(boardName);
    button.classList.toggle("is-following", followed);
    button.setAttribute("aria-pressed", String(followed));
    button.setAttribute("aria-label", followed ? `取消追蹤${boardName}板` : `追蹤${boardName}板`);
    const label = button.querySelector("span");
    if (label) label.textContent = followed ? "已追蹤" : "追蹤";
    const icon = button.querySelector("svg, i");
    if (icon) {
      icon.setAttribute("data-lucide", followed ? "check" : "plus");
      icon.replaceChildren();
    }
  });
  initIcons();
}

async function toggleBoardFollow(boardName) {
  if (!state.account) {
    openAuthDialog("register");
    return;
  }
  const followed = followedBoardSet();
  if (followed.has(boardName)) followed.delete(boardName);
  else followed.add(boardName);
  try {
    state.account = await fetchJson("/auth/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ followed_boards: [...followed] }),
    });
    renderAccountState();
    if (state.globalCommunityFeed === "following") await loadGlobalCommunity();
    announce(followed.has(boardName) ? `已追蹤${boardName}板` : `已取消追蹤${boardName}板`, "success");
  } catch (error) {
    announce(error.message, "error", true);
  }
}

function renderGlobalCommunityNavigation() {
  const labels = {
    all: "全部留學貼文",
    following: "我的追蹤",
    public: "公共留學板",
    cgu: "長庚大學板貼文",
    university: `${activeHomeSchool()}板貼文`,
  };
  document.querySelectorAll("[data-community-route]").forEach((item) => {
    const active = item.dataset.communityRoute === state.globalCommunityFeed;
    item.classList.toggle("active", active);
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
  const label = $("#global-topbar-label");
  if (label) label.textContent = labels[state.globalCommunityFeed] || labels.all;
}

function renderCommunityPageContext(isUniversityBoard = false) {
  const kicker = $("#community-home-kicker");
  const title = $("#community-hub-title");
  const description = $("#community-home-description");
  const school = activeHomeSchool();
  if (kicker) kicker.textContent = isUniversityBoard ? `${school}板` : "全台學生共同交流";
  if (title) title.textContent = isUniversityBoard ? `${school}討論板` : "留學首頁";
  if (description) {
    description.textContent = isUniversityBoard
      ? `只顯示發布到${school}板的交換申請與校內討論。`
      : "看申請、交換生活、住宿與獎學金的最新討論。";
  }
}

function renderGlobalCommunityTopics() {
  const container = $("#global-community-topics");
  if (!container) return;
  container.innerHTML = COMMUNITY_TOPICS.map(([value, label]) => `
    <button type="button" data-global-community-topic="${escapeHtml(value)}" aria-pressed="${state.globalCommunityTopic === value}">${escapeHtml(label)}</button>`).join("");
}

function populateGlobalCommunitySchools() {
  const select = $("#global-community-school");
  if (!select) return;
  const current = select.value || PUBLIC_COMMUNITY_BOARD;
  select.innerHTML = [
    `<option value="${PUBLIC_COMMUNITY_BOARD}">${PUBLIC_COMMUNITY_BOARD}</option>`,
    ...state.supportedUniversities.map((item) => `<option value="${escapeHtml(item.school_name)}">${escapeHtml(item.school_name)}板</option>`),
  ].join("");
  if ([...select.options].some((option) => option.value === current)) select.value = current;
}

async function loadGlobalCommunity() {
  const feed = $("#global-community-feed");
  if (!feed) return;
  feed.setAttribute("aria-busy", "true");
  feed.innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
  const params = new URLSearchParams();
  if (state.globalCommunityTopic) params.set("topic", state.globalCommunityTopic);
  if (state.globalCommunityQuery) params.set("q", state.globalCommunityQuery);
  try {
    if (state.globalCommunityFeed === "public") {
      params.set("school", PUBLIC_COMMUNITY_BOARD);
      state.globalCommunityThreads = await fetchJson(`/community/posts?${params.toString()}`);
    } else if (state.globalCommunityFeed === "cgu") {
      params.set("school", CGU_COMMUNITY_BOARD);
      state.globalCommunityThreads = await fetchJson(`/community/posts?${params.toString()}`);
    } else if (state.globalCommunityFeed === "university") {
      params.set("school", activeHomeSchool());
      state.globalCommunityThreads = await fetchJson(`/community/posts?${params.toString()}`);
    } else if (state.globalCommunityFeed === "following") {
      const boards = [...followedBoardSet()];
      if (!state.account || !boards.length) {
        state.globalCommunityThreads = [];
      } else {
        const boardThreads = await Promise.all(
          boards.map((board) => {
            const boardParams = new URLSearchParams(params);
            boardParams.set("school", board);
            return fetchJson(`/community/posts?${boardParams.toString()}`);
          })
        );
        state.globalCommunityThreads = boardThreads
          .flat()
          .filter((thread, index, rows) => rows.findIndex((row) => row.post.id === thread.post.id) === index)
          .sort((left, right) => new Date(right.post.created_at) - new Date(left.post.created_at));
      }
    } else {
      state.globalCommunityThreads = await fetchJson(`/community/posts?${params.toString()}`);
    }
    if (state.account) await ensureAnonymousIdentity();
    renderGlobalCommunityFeed();
  } catch (error) {
    feed.innerHTML = `<div class="community-empty"><i data-lucide="circle-alert" aria-hidden="true"></i><div><strong>社群暫時無法載入</strong><p>${escapeHtml(error.message)}</p></div></div>`;
  } finally {
    feed.setAttribute("aria-busy", "false");
    initIcons();
  }
}

function renderGlobalCommunityFeed() {
  const feed = $("#global-community-feed");
  if (!feed) return;
  if (state.globalCommunityFeed === "following" && !state.account) {
    feed.innerHTML = `<div class="community-empty"><i data-lucide="log-in" aria-hidden="true"></i><div><strong>登入後查看追蹤動態</strong><p>追蹤學校看板後，該板的新文章會集中顯示在這裡。</p><button type="button" class="primary-button" data-open-auth>登入或建立帳號</button></div></div>`;
  } else if (state.globalCommunityFeed === "following" && !followedBoardSet().size) {
    feed.innerHTML = `<div class="community-empty"><i data-lucide="rss" aria-hidden="true"></i><div><strong>還沒有追蹤任何看板</strong><p>先追蹤${escapeHtml(activeHomeSchool())}板，就能在這裡看到板內的新文章。</p><button type="button" class="secondary-button" data-follow-board="${escapeHtml(activeHomeSchool())}"><i data-lucide="plus" aria-hidden="true"></i><span>追蹤${escapeHtml(activeHomeSchool())}板</span></button></div></div>`;
  } else if (state.globalCommunityFeed === "following" && !state.globalCommunityThreads.length) {
    feed.innerHTML = `<div class="community-empty"><i data-lucide="message-circle" aria-hidden="true"></i><div><strong>追蹤看板目前沒有新文章</strong><p>追蹤學校的新貼文會自動出現在這裡。</p></div></div>`;
  } else if (!state.globalCommunityThreads.length) {
    feed.innerHTML = `<div class="community-empty"><i data-lucide="messages-square" aria-hidden="true"></i><div><strong>這個主題還沒有文章</strong><p>成為第一位提出具體問題或分享交換經驗的同學。</p>${state.account ? "" : '<button type="button" class="secondary-button" data-open-auth>登入後發文</button>'}</div></div>`;
  } else {
    feed.innerHTML = state.globalCommunityThreads.map((thread) => renderCommunityPostThread(thread, { global: true })).join("");
  }
  initIcons();
}

function openGlobalCommunityComposer() {
  if (!state.account) {
    openAuthDialog("register");
    return;
  }
  const form = $("#global-community-form");
  form.hidden = false;
  const boardSelect = form.elements.school_name;
  if (["cgu", "university"].includes(state.globalCommunityFeed) || document.body.classList.contains("cgu-community-mode")) {
    boardSelect.value = state.globalCommunityFeed === "cgu" ? CGU_COMMUNITY_BOARD : activeHomeSchool();
  } else if (state.globalCommunityFeed === "public") {
    boardSelect.value = PUBLIC_COMMUNITY_BOARD;
  }
  form.scrollIntoView({ behavior: "smooth", block: "center" });
  window.setTimeout(() => form.elements.title.focus(), 300);
}

async function submitGlobalCommunityPost(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = new FormData(form);
  const status = form.querySelector(".form-status");
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  status.textContent = "發布中…";
  try {
    await ensureAnonymousIdentity();
    await submitCommunityJson("/community/posts", {
      school_name: values.get("school_name"),
      post_type: values.get("post_type"),
      topic: values.get("topic"),
      country: values.get("country") || null,
      academic_year: values.get("academic_year") || null,
      application_stage: values.get("application_stage") || null,
      title: values.get("title"),
      body: values.get("body"),
    });
    form.reset();
    form.hidden = true;
    status.textContent = "";
    state.globalCommunityTopic = "";
    state.globalCommunityQuery = "";
    $("#global-community-search").value = "";
    renderGlobalCommunityTopics();
    await loadGlobalCommunity();
    announce("文章已發布", "success");
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function reportCommunityResource(button) {
  if (!state.account) {
    openAuthDialog();
    return;
  }
  const reason = window.prompt("請簡短說明檢舉原因。", "內容可能含有不實、過時或不適合公開的資訊");
  if (!reason) return;
  try {
    await ensureAnonymousIdentity();
    await submitCommunityJson("/community/reports", {
      resource_type: button.dataset.reportResource,
      resource_id: button.dataset.resourceId,
      reason,
    });
    announce("已送出檢舉，內容將進入審核。", "success");
  } catch (error) {
    announce(error.message, "error", true);
  }
}

async function submitJson(url, payload) {
  return fetchJson(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function submitCommunityJson(url, payload, method = "POST") {
  return fetchCommunityAuth(url, { method, body: JSON.stringify(payload) });
}

async function refreshCommunityHub(view = state.communityView) {
  if (!state.activeSchool) return;
  state.communityView = view;
  const item = partnerByName(state.activeSchool);
  if (!item) return;
  state.communityCache.delete(item.school_name);
  await loadCommunityQuestions(item);
}

function selectCommunityView(view) {
  state.communityView = view;
  document.querySelectorAll("[data-community-view]").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.communityView === view));
  });
  document.querySelectorAll("[data-community-pane]").forEach((pane) => {
    pane.hidden = pane.dataset.communityPane !== view;
  });
}

function openPrivateInvite(recipientId, recipientName) {
  selectCommunityView("messages");
  const form = $("#private-invite-form");
  if (!form) return;
  form.hidden = false;
  form.elements.recipient_id.value = recipientId;
  $("#private-invite-name").textContent = recipientName;
  form.elements.initial_message.focus();
}

async function submitCommunityPostForm(form) {
  const values = new FormData(form);
  return submitCommunityJson("/community/posts", {
    school_name: state.activeSchool,
    post_type: values.get("post_type"),
    title: values.get("title"),
    body: values.get("body"),
  });
}

async function submitPostCommentForm(form) {
  const values = new FormData(form);
  return submitCommunityJson(`/community/posts/${encodeURIComponent(form.dataset.postId)}/comments`, {
    body: values.get("body"),
  });
}

async function submitPublicChatForm(form) {
  const values = new FormData(form);
  return submitCommunityJson("/community/chat", {
    school_name: state.activeSchool,
    body: values.get("body"),
  });
}

async function submitPrivateInviteForm(form) {
  const values = new FormData(form);
  return submitCommunityJson("/community/conversations", {
    school_name: state.activeSchool,
    recipient_id: values.get("recipient_id"),
    initial_message: values.get("initial_message"),
  });
}

async function submitPrivateMessageForm(form) {
  const values = new FormData(form);
  return submitCommunityJson(`/community/conversations/${encodeURIComponent(form.dataset.conversationId)}/messages`, {
    body: values.get("body"),
  });
}

async function submitQuestionForm(form) {
  const values = new FormData(form);
  return submitJson("/community/questions", {
    school_name: state.activeSchool,
    home_university: activeHomeSchool(),
    topic: values.get("topic"),
    title: values.get("title"),
    body: values.get("body"),
    display_name: values.get("display_name"),
    accept_rules: values.get("accept_rules") === "on",
  });
}

async function submitAnswerForm(form) {
  const values = new FormData(form);
  return submitJson(`/community/questions/${encodeURIComponent(form.dataset.questionId)}/answers`, {
    body: values.get("body"),
    display_name: values.get("display_name"),
    exchange_year: values.get("exchange_year") || null,
    accept_rules: values.get("accept_rules") === "on",
  });
}

async function submitExperienceForm(form) {
  const values = new FormData(form);
  return submitJson("/experience-submissions", {
    school_name: state.activeSchool,
    home_university: activeHomeSchool(),
    title: values.get("title"),
    summary: values.get("summary"),
    exchange_year: values.get("exchange_year"),
    themes: values.getAll("themes"),
    source_url: values.get("source_url") || null,
    display_name: values.get("display_name"),
    consent_to_publish: values.get("consent_to_publish") === "on",
  });
}

async function handleCommunityFormSubmit(form, submitter, successMessage) {
  const button = form.querySelector('button[type="submit"]');
  const status = form.querySelector(".form-status");
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  status.className = "form-status is-loading";
  status.textContent = "正在送出…";
  try {
    await submitter(form);
    form.reset();
    status.className = "form-status is-success";
    status.textContent = successMessage;
    return true;
  } catch (error) {
    status.className = "form-status is-error";
    status.textContent = error.message;
    return false;
  } finally {
    button.disabled = false;
    button.setAttribute("aria-busy", "false");
  }
}

function renderExperienceSource(source) {
  const typeLabel = source.source_type === "video" ? "影片" : source.source_type === "community" ? "社群討論" : "文章";
  const perspectiveLabels = {
    community_discussion: "公開討論",
    student_created: "學生創作",
    official_student_story: "校方學生故事",
    independent: "外部來源",
  };
  const actionLabel = source.source_type === "video" ? "觀看原始影片" : "閱讀完整來源";
  const contentLabels = {
    full_text: "已讀取全文摘要",
    metadata_only: source.source_type === "video" ? "依影片公開描述整理" : "依公開描述整理",
    unavailable: "原文讀取受限",
  };
  return `
    <article class="experience-source-card">
      <div class="experience-source-meta">
        <span>${escapeHtml(typeLabel)}</span>
        <span>${escapeHtml(source.platform)}</span>
        ${source.author_name ? `<span>${escapeHtml(source.author_name)}</span>` : ""}
        <span>${escapeHtml(perspectiveLabels[source.perspective] || "公開來源")}</span>
        <span>${escapeHtml(contentLabels[source.content_status] || "摘要來源待確認")}</span>
        <span>${escapeHtml(String(source.language || "unknown").toUpperCase())}</span>
        ${source.published_at ? `<span>${escapeHtml(source.published_at)}</span>` : ""}
      </div>
      <h5>${escapeHtml(source.title)}</h5>
      <p>${highlightHtml(source.summary)}</p>
      <div class="tag-row">${(source.themes || []).map((theme) => `<span class="tag">${escapeHtml(experienceThemeLabel(theme))}</span>`).join("")}</div>
      <a class="official-link" href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer">
        <span>${escapeHtml(actionLabel)}</span><i data-lucide="external-link" aria-hidden="true"></i>
      </a>
    </article>`;
}

function experienceThemeLabel(theme) {
  const labels = {
    academics: "課業與教學",
    campus_culture: "校園風氣",
    housing: "住宿",
    cost: "生活成本",
    food: "飲食與採買",
    transport: "交通與地點",
    climate: "氣候與穿著",
    travel: "旅行與周邊城市",
    safety: "安全與醫療",
    social: "社交與社團",
    support: "國際生支援",
    career: "實作與職涯",
    challenges: "可能的挑戰",
  };
  return labels[theme] || theme;
}

function summarizePartnerCondition(item, max = 150, pointLimit = 3) {
  const eligibility = partnerSummaryPoints(item, "eligibility_points");
  const application = partnerSummaryPoints(item, "application_steps");
  const points = [...eligibility, ...application].slice(0, pointLimit);
  if (!points.length) return "官方資料尚未提供可整理的中文重點，請開啟來源確認。";
  return truncate(points.join("；"), max);
}

function renderDeadlines() {
  const periods = state.dashboard.application_periods || [];
  if (!periods.length) {
    renderEmpty("#period-list", "目前沒有可顯示的時程", "請查看官方公告或稍後重新整理。");
    return;
  }

  $("#period-list").innerHTML = periods
    .map((item) => {
      const details = item.details || [];
      return `
        <details class="deadline-card">
          <summary>
            <span><strong>${escapeHtml(item.title)}</strong>${details[0] ? `<span class="deadline-date">${highlightHtml(truncate(details[0], 58))}</span>` : ""}</span>
            <i data-lucide="chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="deadline-card-content">
            ${details.length ? `<ul class="deadline-details">${details.map((detail) => `<li>${highlightHtml(detail)}</li>`).join("")}</ul>` : ""}
            ${renderSourceLink(item.source)}
          </div>
        </details>`;
    })
    .join("");
}

function scholarshipItems() {
  const rules = state.dashboard.document_explanations || state.dashboard.rule_explanations || [];
  const ruleItems = rules.filter((rule) => /補助|學海|領航者/.test(`${rule.title} ${rule.document_type}`));
  const genericItems = (state.dashboard.scholarship_info || []).map((item) => ({
    title: item.title,
    summary: item.details?.[0] || "",
    key_points: item.details || [],
    source: item.source,
    document_type: "補助資訊",
  }));
  const uniqueItems = [];
  const seen = new Set();
  [...ruleItems, ...genericItems].forEach((item) => {
    if (!seen.has(item.title)) {
      seen.add(item.title);
      uniqueItems.push(item);
    }
  });
  return uniqueItems;
}

function scholarshipMatch(item) {
  const profile = state.eligibilityProfile;
  if (!profile) return { tone: "setup", label: "尚未比對", note: "先完成資格初判，再依成績與需求提示。" };
  const text = `${item.title} ${item.summary} ${(item.key_points || []).join(" ")}`;
  const minimum = academicMinimum();
  if (profile.academicScore < minimum && /70\s*分|75\s*分|歷年學業成績|領航者|學海/.test(text)) {
    return { tone: "blocked", label: "目前有門檻", note: `平均成績尚未達公開的 ${minimum} 分參考門檻。` };
  }
  if (/惜珠|低收入|中低收入|經濟/.test(text)) {
    return { tone: "review", label: "需確認身分", note: "需要另外核對經濟或身分證明，不能只用成績判定。" };
  }
  if (profile.scholarshipNeeded) {
    return { tone: "likely", label: "優先查看", note: "你已標示需要補助；請再核對金額、重複領取限制與返國義務。" };
  }
  return { tone: "review", label: "可能適用", note: "基本成績條件可繼續核對，正式資格仍以當年度公告為準。" };
}

function renderScholarships() {
  const items = scholarshipItems();
  if (!items.length) {
    renderEmpty("#scholarship-list", "目前沒有補助摘要", "請稍後重新整理或查看官方來源。");
    return;
  }

  const summary = $("#scholarship-match-summary");
  if (summary) {
    const prioritized = items.filter((item) => ["likely", "review"].includes(scholarshipMatch(item).tone)).length;
    summary.innerHTML = state.eligibilityProfile
      ? `<span class="scholarship-match-icon"><i data-lucide="badge-check" aria-hidden="true"></i></span><span><strong>${prioritized} 項值得進一步核對</strong><small>${state.eligibilityProfile.scholarshipNeeded ? "已依你的補助需求優先標示" : "正式資格仍以當年度官方公告為準"}</small></span><a href="#eligibility">調整個人條件</a>`
      : '<span class="scholarship-match-icon"><i data-lucide="scan-search" aria-hidden="true"></i></span><span><strong>尚未進行個人比對</strong><small>填入成績與補助需求後，會顯示優先順序。</small></span><a href="#eligibility">開始比對</a>';
  }

  $("#scholarship-list").innerHTML = items
    .slice(0, 6)
    .map(
      (item) => {
        const match = scholarshipMatch(item);
        return `
        <details class="scholarship-card">
          <summary>
            <span><span class="scholarship-match-pill ${match.tone}">${escapeHtml(match.label)}</span><strong>${escapeHtml(item.title)}</strong></span>
            <i data-lucide="chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="scholarship-content">
            <p class="scholarship-personal-note"><i data-lucide="user-round-check" aria-hidden="true"></i>${escapeHtml(match.note)}</p>
            <p>${highlightHtml(item.summary)}</p>
            <ul class="compact-list">${(item.key_points || []).slice(0, 5).map((point) => `<li>${highlightHtml(point)}</li>`).join("")}</ul>
            <div class="document-actions">
              ${renderSourceLink(item.source, "查看官方說明")}
              ${item.document_url ? renderOfficialDocumentLink(item.document_url) : ""}
            </div>
          </div>
        </details>`;
      }
    )
    .join("");
}

function renderDocumentFilters() {
  const rules = state.dashboard.document_explanations || state.dashboard.rule_explanations || [];
  const types = ["全部", ...unique(rules.map((rule) => rule.document_type || "其他文件"))];
  $("#document-filters").innerHTML = types
    .map(
      (type) => `<button type="button" class="chip-button ${state.documentType === type ? "active" : ""}" data-document-type="${escapeHtml(type)}" aria-pressed="${state.documentType === type}">${escapeHtml(type)}</button>`
    )
    .join("");
}

function renderDocuments() {
  const rules = state.dashboard.document_explanations || state.dashboard.rule_explanations || [];
  const filtered = state.documentType === "全部"
    ? rules
    : rules.filter((rule) => (rule.document_type || "其他文件") === state.documentType);
  $("#document-count").textContent = `${filtered.length} 份`;

  if (!filtered.length) {
    renderEmpty("#documents-list", "這個分類目前沒有文件", "改選其他文件類型即可查看摘要。");
    return;
  }

  $("#documents-list").innerHTML = filtered.map(renderDocumentCard).join("");
  initIcons();
}

function renderDocumentCard(rule) {
  const type = rule.document_type || "官方文件";
  return `
    <details class="document-card">
      <summary>
        <span>
          <span class="document-type">${escapeHtml(type)}</span>
          <strong>${escapeHtml(rule.title)}</strong>
        </span>
        <i data-lucide="chevron-down" aria-hidden="true"></i>
      </summary>
      <div class="document-content">
        <p>${highlightHtml(rule.summary)}</p>
        <div class="tag-row">${(rule.applies_to || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>
        <ul class="document-points">${(rule.key_points || []).map((point) => `<li>${highlightHtml(point)}</li>`).join("")}</ul>
        <div class="document-actions">
          ${rule.document_url ? renderOfficialDocumentLink(rule.document_url) : ""}
          ${renderSourceLink(rule.source, "查看來源頁")}
        </div>
      </div>
    </details>`;
}

function renderEligibilityOptions() {
  const partners = state.dashboard.partner_universities;
  const colleges = unique(partners.flatMap((item) => splitOptions(item.colleges)).filter((item) => !/全校|四院皆可/.test(item)));
  const countries = unique(partners.map((item) => item.country).filter(Boolean));
  fillSelect("#eligibility-college", colleges, "請選擇學院");
  fillSelect("#eligibility-degree", ["大學部", "研究所"], "請選擇學制");
  fillSelect("#preferred-country", countries, "不限國家", state.eligibilityProfile?.preferredCountry || "");
}

function restoreEligibilityForm() {
  const profile = state.eligibilityProfile;
  if (!profile) return;
  $("#eligibility-college").value = profile.college || "";
  $("#eligibility-degree").value = profile.degree || "";
  $("#academic-score").value = profile.academicScore ?? "";
  $("#language-test").value = profile.languageTest || "";
  $("#language-score").value = profile.languageScore ?? "";
  $("#target-term").value = profile.targetTerm || "";
  $("#preferred-country").value = profile.preferredCountry || "";
  $("#monthly-budget").value = profile.monthlyBudget || "";
  $("#scholarship-needed").checked = Boolean(profile.scholarshipNeeded);
  $("#clear-saved-eligibility").hidden = false;
}

function checkEligibility(event) {
  event.preventDefault();
  const college = $("#eligibility-college").value;
  const degree = $("#eligibility-degree").value;
  const academicScore = Number($("#academic-score").value);
  const languageTest = $("#language-test").value;
  const languageScore = Number($("#language-score").value);
  const targetTerm = $("#target-term").value;
  const preferredCountry = $("#preferred-country").value;
  const monthlyBudget = Number($("#monthly-budget").value) || 0;
  const scholarshipNeeded = $("#scholarship-needed").checked;
  const result = $("#eligibility-result");

  if (!college || !degree || !Number.isFinite(academicScore) || !languageTest) {
    announce("請完成所有必填欄位", "error");
    return;
  }

  const minimum = academicMinimum();
  const academicPass = academicScore >= minimum;
  const threshold = languageThreshold(languageTest);
  const languageNeedsReview = !threshold || !Number.isFinite(languageScore) || languageScore <= 0;
  const languagePass = threshold ? languageScore >= threshold.minimum : false;
  const ready = academicPass && languagePass;
  state.eligibilityProfile = {
    college,
    degree,
    academicScore,
    languageTest,
    languageScore,
    languageLabel: threshold ? `${threshold.label} ${languageScore || "待補"}` : "語言能力待確認",
    targetTerm,
    preferredCountry,
    monthlyBudget,
    scholarshipNeeded,
  };
  const ranked = rankedPartners();
  const eligibleMatches = ranked.filter(({ match }) => match.tone !== "blocked");
  const matchedCount = eligibleMatches.length;
  try {
    window.localStorage.setItem(STORAGE_KEYS.eligibility, JSON.stringify(state.eligibilityProfile));
  } catch (_) {
    // The profile still applies for this session.
  }
  $("#clear-saved-eligibility").hidden = false;

  result.className = `eligibility-result ${ready ? "is-pass" : "is-warning"}`;
  result.innerHTML = `
    <h3>${ready ? "符合校內基本門檻" : "目前仍有條件需要確認"}</h3>
    <p>${ready ? "可繼續查看符合學院與學制的合作學校。" : "補齊下列條件後，再核對各合作學校的個別規定。"}</p>
    <div class="eligibility-checks">
      ${renderCheckRow(academicPass ? "pass" : "fail", academicPass ? `平均成績 ${academicScore}：達到 ${minimum} 分基本門檻` : `平均成績 ${academicScore}：未達 ${minimum} 分基本門檻`)}
      ${renderCheckRow(languageNeedsReview ? "review" : languagePass ? "pass" : "fail", languageNeedsReview ? "語言檢定：需依申請國家與合作學校另行確認" : `${threshold.label} ${languageScore}：${languagePass ? "達到" : "未達"}校內參考門檻 ${threshold.minimum}`)}
      ${renderCheckRow("review", `${college}／${degree}目前可查看 ${matchedCount} 所相關學校；各校可能有更高門檻`)}
    </div>
    <div class="eligibility-match-preview">
      <strong>目前最值得先看的學校</strong>
      ${eligibleMatches.slice(0, 3).map(({ item, match }) => `<button type="button" class="eligibility-match-row school-detail-trigger" data-school-name="${escapeHtml(item.school_name)}"><span><b>${escapeHtml(item.school_name)}</b><small>${escapeHtml(match.reasons.slice(0, 2).join(" · ") || "公開資料仍需核對")}</small></span><em>${escapeHtml(match.label)}</em><i data-lucide="chevron-right" aria-hidden="true"></i></button>`).join("") || '<p>目前沒有同時符合學院、學制與已知語言門檻的學校。</p>'}
    </div>
    <div class="eligibility-actions">
      <button id="view-matched-schools" type="button" class="primary-button">查看 ${matchedCount} 所相關學校</button>
    </div>`;
  initIcons();
  renderDecisionBrief();
  renderDeadlinePreview();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  renderRecommendedMatches();
  renderPartnerTable();
  renderScholarships();
  renderBudgetPlanner();

  $("#view-matched-schools").addEventListener("click", () => {
    state.college = college;
    state.degree = degree;
    state.partnerLimit = window.matchMedia("(max-width: 820px)").matches ? 8 : 20;
    renderPartnerFilters();
    renderPartnerTable();
    window.location.hash = "#partners";
  });
}

function clearEligibilityProfile() {
  state.eligibilityProfile = null;
  try {
    window.localStorage.removeItem(STORAGE_KEYS.eligibility);
  } catch (_) {
    // The current session can still be reset.
  }
  $("#eligibility-form").reset();
  $("#clear-saved-eligibility").hidden = true;
  const result = $("#eligibility-result");
  result.className = "eligibility-result";
  result.innerHTML = '<div class="result-placeholder"><i data-lucide="clipboard-check" aria-hidden="true"></i><strong>還沒開始檢查</strong><span>填入資料後，系統會比對校內基本門檻與合作校公開條件。</span></div>';
  state.college = "";
  state.degree = "";
  renderDecisionBrief();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  renderRecommendedMatches();
  renderPartnerFilters();
  renderPartnerTable();
  renderScholarships();
  initIcons();
  announce("資格初判資料已清除", "success");
}

function renderCheckRow(type, text) {
  const icon = type === "pass" ? "circle-check" : type === "fail" ? "circle-alert" : "info";
  return `<div class="check-row ${type}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${escapeHtml(text)}</span></div>`;
}

function renderAdvisorForm() {
  if (!state.dashboard) return;
  const profile = state.eligibilityProfile || {};
  const partners = state.dashboard.partner_universities || [];
  const colleges = unique(partners.flatMap((item) => splitOptions(item.colleges)).filter((item) => !/全校|四院皆可/.test(item)));
  const countries = unique(partners.map((item) => item.country).filter(Boolean));
  fillSelect("#advisor-college", colleges, "尚未設定", profile.college || "");
  fillSelect("#advisor-country", countries, "不限國家", profile.preferredCountry || "");
  $("#advisor-degree").value = profile.degree || "";
  $("#advisor-department").value = profile.department || "";
  $("#advisor-current-year").value = profile.currentYear || "";
  $("#advisor-academic-score").value = profile.academicScore ?? "";
  $("#advisor-language-test").value = profile.languageTest || "";
  $("#advisor-language-score").value = profile.languageScore ?? "";
  $("#advisor-target-term").value = profile.targetTerm || "";
  $("#advisor-monthly-budget").value = profile.monthlyBudget || "";
  $("#advisor-scholarship").checked = Boolean(profile.scholarshipNeeded);
  $("#advisor-profile-status").textContent = state.eligibilityProfile ? "已帶入資格初判" : "尚未設定";
}

async function loadAdvisorStatus() {
  const element = $("#advisor-index-status");
  try {
    state.aiStatus = await fetchJson("/ai/status");
    const index = state.aiStatus?.rag_index || {};
    if (!index.source_count) {
      element.hidden = true;
      return;
    }
    const mode = index.embedded_count > 0 ? "語意檢索已啟用" : "來源檢索已啟用";
    element.innerHTML = `<i data-lucide="database-zap" aria-hidden="true"></i>${Number(index.source_count)} 份官方來源 · ${mode}`;
    element.hidden = false;
    initIcons();
  } catch (_) {
    element.hidden = true;
  }
}

function optionalNumber(value) {
  if (value === "" || value === null || value === undefined) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

async function submitAdvisorPlan(event) {
  event.preventDefault();
  if (state.advisorLoading) return;
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = {
    school_name: activeHomeSchool(),
    college: formData.get("college") || null,
    department: formData.get("department") || null,
    current_year: formData.get("current_year") || null,
    degree_level: formData.get("degree_level") || null,
    academic_score: optionalNumber(formData.get("academic_score")),
    language_test: formData.get("language_test") || null,
    language_score: optionalNumber(formData.get("language_score")),
    target_term: formData.get("target_term") || null,
    preferred_country: formData.get("preferred_country") || null,
    monthly_budget: optionalNumber(formData.get("monthly_budget")),
    needs_scholarship: formData.get("needs_scholarship") === "on",
    question: String(formData.get("question") || "").trim() || null,
  };
  const button = $("#advisor-submit");
  state.advisorLoading = true;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  $("#advisor-result").innerHTML = '<div class="advisor-loading"><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div></div>';
  try {
    state.advisorPlan = await fetchJson("/advisor/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (payload.college && payload.degree_level && payload.academic_score !== null && payload.language_test) {
      const threshold = languageThreshold(payload.language_test);
      state.eligibilityProfile = {
        college: payload.college,
        department: payload.department || "",
        currentYear: payload.current_year || "",
        degree: payload.degree_level,
        academicScore: payload.academic_score,
        languageTest: payload.language_test,
        languageScore: payload.language_score || 0,
        languageLabel: threshold ? `${threshold.label} ${payload.language_score || "待補"}` : "語言能力待確認",
        targetTerm: payload.target_term || "",
        preferredCountry: payload.preferred_country || "",
        monthlyBudget: payload.monthly_budget || 0,
        scholarshipNeeded: payload.needs_scholarship,
      };
      try {
        window.localStorage.setItem(STORAGE_KEYS.eligibility, JSON.stringify(state.eligibilityProfile));
      } catch (_) {
        // The advisor result still applies for this session.
      }
      restoreEligibilityForm();
      $("#advisor-profile-status").textContent = "已保存條件";
      renderPersonalPlanSnapshot();
      renderRecommendedMatches();
    }
    renderAdvisorResult(state.advisorPlan);
  } catch (error) {
    $("#advisor-result").innerHTML = `<div class="advisor-error"><i data-lucide="circle-alert" aria-hidden="true"></i><strong>暫時無法產生方案</strong><span>${escapeHtml(error.message)}</span><button type="button" class="secondary-button" data-retry-advisor>重新嘗試</button></div>`;
    initIcons();
  } finally {
    state.advisorLoading = false;
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

function advisorTaskAction(task) {
  if (task.due_date) return `<button type="button" class="secondary-button" data-advisor-calendar="${escapeHtml(task.id)}"><i data-lucide="calendar-plus" aria-hidden="true"></i><span>加入日曆</span></button>`;
  const routes = { profile: "#advisor", eligibility: "#eligibility", language: "#eligibility", documents: "#application-center", scholarship: "#scholarships" };
  return `<a class="secondary-button" href="${routes[task.category] || "#overview"}"><span>前往處理</span><i data-lucide="arrow-right" aria-hidden="true"></i></a>`;
}

function renderAdvisorResult(plan) {
  const container = $("#advisor-result");
  if (!plan) return;
  const recommendations = plan.recommendations || [];
  const tasks = plan.tasks || [];
  const answer = plan.answer;
  const modeLabel = plan.mode === "ai_enhanced" ? "AI 依來源整理" : "規則整理";
  container.innerHTML = `
    <section class="advisor-summary-card glass-panel">
      <div><span class="advisor-mode"><i data-lucide="badge-check" aria-hidden="true"></i>系統資格比對</span><h3>${escapeHtml(plan.summary)}</h3></div>
      <div class="advisor-qualification">${(plan.qualification || []).map((item) => `<span><i data-lucide="check" aria-hidden="true"></i>${escapeHtml(item)}</span>`).join("")}</div>
    </section>
    <section class="advisor-result-section">
      <div class="concise-heading"><div><span class="section-kicker">系統依公開條件排序</span><h3>優先候選</h3></div><a href="#partners">查看全部 ${recommendations.length} 所</a></div>
      <div class="advisor-school-list">${recommendations.slice(0, 5).map((item) => `
        <article class="advisor-school-card">
          <div class="advisor-school-photo">${item.image_url ? `<img src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.school_name)}校園" loading="lazy" />` : '<span><i data-lucide="school" aria-hidden="true"></i></span>'}</div>
          <div class="advisor-school-copy"><span>${escapeHtml(item.country || "未標示國家")}</span><strong>${escapeHtml(item.school_name)}</strong><small>${escapeHtml(item.fit_label)}</small><div>${(item.reasons || []).slice(0, 2).map((reason) => `<em>${escapeHtml(reason)}</em>`).join("")}</div></div>
          <div class="advisor-match-score"><strong>${item.match_score}</strong><small>符合度</small></div>
          <button type="button" class="icon-button school-detail-trigger" data-school-name="${escapeHtml(item.school_name)}" aria-label="查看${escapeHtml(item.school_name)}"><i data-lucide="chevron-right" aria-hidden="true"></i></button>
          ${(item.gaps || []).length ? `<details><summary><span>待確認 ${(item.gaps || []).length} 項</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><ul>${item.gaps.map((gap) => `<li>${escapeHtml(gap)}</li>`).join("")}</ul>${item.source_urls?.[0] ? `<a href="${escapeHtml(item.source_urls[0])}" target="_blank" rel="noreferrer">官方來源<i data-lucide="external-link" aria-hidden="true"></i></a>` : ""}</details>` : ""}
        </article>`).join("") || '<div class="advisor-empty"><strong>尚無可排序學校</strong><small>補齊條件後再試一次。</small></div>'}</div>
    </section>
    <section class="advisor-result-section">
      <div class="concise-heading"><div><span class="section-kicker">先做最重要的事</span><h3>我的下一步</h3></div><a href="#calendar">查看日曆</a></div>
      <div class="advisor-task-list">${tasks.map((task) => `
        <article class="advisor-task ${escapeHtml(task.priority)}">
          <span class="advisor-task-icon"><i data-lucide="${task.category === "deadline" ? "clock-3" : task.category === "documents" ? "files" : task.category === "language" ? "languages" : task.category === "scholarship" ? "badge-dollar-sign" : "circle-check-big"}" aria-hidden="true"></i></span>
          <div><span>${task.priority === "high" ? "優先" : task.due_date ? escapeHtml(formatCalendarDate(task.due_date)) : "待辦"}</span><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.detail)}</small></div>
          ${advisorTaskAction(task)}
        </article>`).join("") || '<div class="advisor-empty"><strong>目前沒有待辦</strong><small>送件前仍請核對官方公告。</small></div>'}</div>
    </section>
    ${answer ? `<section class="advisor-answer glass-panel"><div class="concise-heading"><div><span class="section-kicker">官方資料回答 · ${escapeHtml(modeLabel)}</span><h3>${escapeHtml(answer.question)}</h3></div><span class="advisor-evidence-status ${escapeHtml(answer.evidence_status)}">${answer.evidence_status === "grounded" ? "來源充足" : answer.evidence_status === "limited" ? "資料有限" : "無資料"}</span></div><p>${escapeHtml(answer.answer)}</p><ul>${(answer.key_points || []).map((point) => `<li>${highlightHtml(point)}</li>`).join("")}</ul><details><summary><span><i data-lucide="book-open-check" aria-hidden="true"></i><strong>官方來源 ${(answer.sources || []).length}</strong></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div>${(answer.sources || []).map((source) => `<a href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer"><span><strong>${escapeHtml(source.title)}</strong><small>${escapeHtml(advisorCitationMeta(source))}</small></span><i data-lucide="external-link" aria-hidden="true"></i></a>`).join("")}</div></details></section>` : ""}
    <small class="advisor-disclaimer"><i data-lucide="info" aria-hidden="true"></i>${escapeHtml(plan.disclaimer)}</small>`;
  initIcons();
}

function advisorCitationMeta(source) {
  const rows = [source.section || "官方資料"];
  if (source.published_at) rows.push(`發布 ${formatSourceDate(source.published_at)}`);
  if (source.last_checked) rows.push(`查核 ${formatSourceDate(source.last_checked)}`);
  return rows.join(" · ");
}

function formatSourceDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("zh-TW", { year: "numeric", month: "numeric", day: "numeric" }).format(date);
}

function addAdvisorTaskToCalendar(taskId) {
  const task = state.advisorPlan?.tasks?.find((item) => item.id === taskId);
  if (!task?.due_date) return;
  if (state.calendarEvents.some((item) => item.id === `advisor-${task.id}`)) {
    announce("這項任務已在日曆中", "success");
    return;
  }
  state.calendarEvents.push({
    id: `advisor-${task.id}`,
    title: task.title,
    date: task.due_date,
    category: task.category === "deadline" ? "home" : task.category || "other",
    reminderDays: 7,
    note: task.detail,
    sourceUrl: task.source_url || "",
    origin: "personal",
  });
  persistCalendarEvents();
  renderApplicationCalendar();
  announce("已加入申請日曆", "success");
}

async function submitDocumentCheck(event) {
  event.preventDefault();
  if (state.documentCheckLoading) return;
  const form = event.currentTarget;
  const file = $("#document-check-file").files?.[0];
  if (!file) {
    announce("請先選擇文件", "error");
    return;
  }
  const data = new FormData(form);
  if (!String(data.get("expected_word_limit") || "").trim()) data.delete("expected_word_limit");
  const button = $("#document-check-submit");
  state.documentCheckLoading = true;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  $("#document-check-status").textContent = "正在讀取文件…";
  $("#document-check-result").innerHTML = '<div class="advisor-loading"><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div></div>';
  try {
    state.documentCheckResult = await fetchJson("/document-check", { method: "POST", body: data });
    renderDocumentCheckResult(state.documentCheckResult);
    $("#document-check-status").textContent = "檢查完成";
  } catch (error) {
    $("#document-check-result").innerHTML = `<div class="advisor-error"><i data-lucide="circle-alert" aria-hidden="true"></i><strong>無法檢查這份文件</strong><span>${escapeHtml(error.message)}</span></div>`;
    $("#document-check-status").textContent = error.message;
    initIcons();
  } finally {
    state.documentCheckLoading = false;
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

function documentTypeLabel(type) {
  return { study_plan: "讀書計畫", recommendation: "推薦信", resume: "履歷", application_form: "申請表", other: "其他文件" }[type] || "申請文件";
}

function renderDocumentCheckResult(result) {
  const issues = result.issues || [];
  const errors = issues.filter((item) => item.severity === "error").length;
  const warnings = issues.filter((item) => item.severity === "warning").length;
  $("#document-check-result").innerHTML = `
    <section class="document-check-summary glass-panel ${errors ? "has-error" : warnings ? "has-warning" : "is-ready"}">
      <span class="document-check-summary-icon"><i data-lucide="${errors ? "circle-x" : warnings ? "triangle-alert" : "circle-check-big"}" aria-hidden="true"></i></span>
      <div><span>${escapeHtml(documentTypeLabel(result.document_type))}</span><h3>${escapeHtml(result.summary)}</h3><small>完整度 ${Number(result.completeness_score || 0)}% · ${result.page_count} 頁 · 約 ${result.word_count} 字${result.ai_enhanced ? " · AI 深度檢查" : ""}</small></div>
    </section>
    <section class="document-check-findings">
      <div class="concise-heading"><h3>需要處理</h3><small>${issues.length} 項</small></div>
      <div>${issues.map((issue) => `<details class="document-issue ${escapeHtml(issue.severity)}"><summary><span><i data-lucide="${issue.severity === "error" ? "circle-x" : issue.severity === "warning" ? "triangle-alert" : "info"}" aria-hidden="true"></i></span><strong>${escapeHtml(issue.title)}</strong><i data-lucide="chevron-down" aria-hidden="true"></i></summary><p>${escapeHtml(issue.detail)}</p></details>`).join("") || '<div class="document-check-clear"><i data-lucide="badge-check" aria-hidden="true"></i><span><strong>未發現明顯缺漏</strong><small>送件前再對照官方最新版。</small></span></div>'}</div>
    </section>
    ${(result.suggestions || []).length ? `<details class="document-check-suggestions glass-panel"><summary><span><i data-lucide="list-todo" aria-hidden="true"></i><strong>修改建議 ${(result.suggestions || []).length} 項</strong></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><ul>${result.suggestions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></details>` : ""}
    <details class="document-check-details"><summary><span><i data-lucide="list-checks" aria-hidden="true"></i><strong>檢查明細</strong></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div><ul>${(result.checks_passed || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>尚無通過項目</li>"}</ul>${result.extracted_preview ? `<p>${escapeHtml(result.extracted_preview)}</p>` : ""}</div></details>
    <small class="document-privacy-result"><i data-lucide="shield-check" aria-hidden="true"></i>${escapeHtml(result.privacy_note)}</small>`;
  initIcons();
}

async function submitWritingAssistant(event) {
  event.preventDefault();
  if (state.writingAssistantLoading) return;
  const form = event.currentTarget;
  const data = new FormData(form);
  const payload = {
    text: String(data.get("text") || "").trim(),
    action: data.get("action"),
    document_type: data.get("document_type"),
    target_word_limit: optionalNumber(data.get("target_word_limit")),
    school_context: String(data.get("school_context") || "").trim() || null,
  };
  const button = $("#writing-assistant-submit");
  state.writingAssistantLoading = true;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  $("#writing-assistant-status").textContent = "正在整理…";
  $("#writing-assistant-result").innerHTML = '<div class="advisor-loading"><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div></div>';
  try {
    state.writingAssistantResult = await fetchJson("/ai/rewrite-document", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderWritingAssistantResult(state.writingAssistantResult);
    $("#writing-assistant-status").textContent = "建議稿已完成";
  } catch (error) {
    $("#writing-assistant-result").innerHTML = `<div class="advisor-error"><i data-lucide="circle-alert" aria-hidden="true"></i><strong>目前無法產生建議稿</strong><span>${escapeHtml(error.message)}</span></div>`;
    $("#writing-assistant-status").textContent = error.message;
    initIcons();
  } finally {
    state.writingAssistantLoading = false;
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

function renderWritingAssistantResult(result) {
  const actionLabel = { formalize: "正式語氣", translate_en: "英文翻譯", shorten: "精簡版本", grammar: "文法修正" }[result.action] || "建議稿";
  $("#writing-assistant-result").innerHTML = `
    <section class="writing-draft glass-panel">
      <div class="concise-heading"><div><span class="section-kicker">AI 建議稿</span><h3>${escapeHtml(actionLabel)}</h3></div><button type="button" class="secondary-button" data-copy-writing-draft><i data-lucide="copy" aria-hidden="true"></i><span>複製</span></button></div>
      <div class="writing-draft-copy">${escapeHtml(result.draft)}</div>
    </section>
    ${(result.warnings || []).length ? `<details class="document-check-suggestions writing-warning" open><summary><span><i data-lucide="triangle-alert" aria-hidden="true"></i><strong>送出前確認</strong></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><ul>${result.warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></details>` : ""}
    ${(result.changes || []).length ? `<details class="document-check-details"><summary><span><i data-lucide="list-checks" aria-hidden="true"></i><strong>調整內容</strong></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div><ul>${result.changes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div></details>` : ""}
    <small class="document-privacy-result"><i data-lucide="info" aria-hidden="true"></i>${escapeHtml(result.disclaimer)}</small>`;
  initIcons();
}

function runSearch(query) {
  state.query = query.trim();
  if (!state.query) {
    announce("請輸入學校、國家、補助或文件名稱", "error");
    $("#search-input").focus();
    return;
  }
  state.searchReturnHash = isUniversityBoardRoute() && window.location.hash !== "#search"
    ? window.location.hash
    : "#overview";
  renderSearchResults();
  if (window.location.hash === "#search") applyAppRoute({ loadFeed: false });
  else window.location.hash = "#search";
  initIcons();
}

function renderSearchResults() {
  if (!state.dashboard || !state.query) return;
  const query = normalize(state.query);
  const information = [
    ...state.dashboard.application_periods,
    ...state.dashboard.program_overview,
    ...state.dashboard.eligibility,
    ...state.dashboard.language_requirements,
    ...state.dashboard.required_documents,
    ...state.dashboard.scholarship_info,
  ];
  const rules = state.dashboard.document_explanations || state.dashboard.rule_explanations || [];

  const rows = [];
  state.dashboard.partner_universities.forEach((item) => {
    const destination = destinationProfileForSchool(item.school_name);
    const searchable = normalize(`${Object.values(item).join(" ")} ${Object.values(destination || {}).join(" ")}`);
    if (searchable.includes(query)) {
      rows.push({
        title: item.school_name,
        detail: [item.country, destination?.city, item.program_type, item.colleges, item.degree_levels, item.application_deadline].filter(Boolean).join("／"),
        type: "合作學校",
        source: { source_url: item.source_url },
      });
    }
  });
  information.forEach((item) => {
    if (normalize(`${item.title} ${(item.details || []).join(" ")}`).includes(query)) {
      rows.push({ title: item.title, detail: (item.details || []).slice(0, 2).join("；"), type: "申請資訊", source: item.source });
    }
  });
  rules.forEach((rule) => {
    if (normalize(`${rule.title} ${rule.summary} ${(rule.key_points || []).join(" ")}`).includes(query)) {
      rows.push({ title: rule.title, detail: rule.summary, type: rule.document_type || "官方文件", source: rule.source });
    }
  });

  $("#search-status").textContent = `「${state.query}」找到 ${rows.length} 筆整理資料`;
  if (!rows.length) {
    renderEmpty("#search-results", "找不到符合的資料", "可改用國家、學校中文名稱、補助或文件類型搜尋。");
    return;
  }
  $("#search-results").innerHTML = rows
    .slice(0, 24)
    .map(
      (row) => `
        <details class="search-result-card">
          <summary>
            <span><span class="document-type">${escapeHtml(row.type)}</span><strong>${escapeHtml(row.title)}</strong></span>
            <i data-lucide="chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="search-result-content">
            <p>${highlightHtml(truncate(row.detail, 130))}</p>
            ${renderSourceLink(row.source, "查看官方來源")}
          </div>
        </details>`
    )
    .join("");
}

function renderSources() {
  const sources = state.dashboard.sources || [];
  $("#source-list").innerHTML = sources
    .map(
      (source) => `
        <article class="source-row">
          <strong>${escapeHtml(source.title)}</strong>
          <a href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(source.source_url)}</a>
        </article>`
    )
    .join("");
}

function renderSourceLink(source, label = "官方來源") {
  if (!source?.source_url) return "";
  return `<a class="evidence-link" href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer"><span>${escapeHtml(label)}</span><i data-lucide="external-link" aria-hidden="true"></i></a>`;
}

function renderOfficialDocumentLink(url) {
  return `<a class="official-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer"><span>開啟完整文件</span><i data-lucide="file-down" aria-hidden="true"></i></a>`;
}

function fillSelect(selector, values, placeholder, selected = "") {
  const element = $(selector);
  const current = selected || element.value;
  element.innerHTML = [
    `<option value="">${escapeHtml(placeholder)}</option>`,
    ...values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`),
  ].join("");
  if ([...element.options].some((option) => option.value === current)) element.value = current;
}

function splitOptions(value) {
  return String(value || "")
    .split(/[、,，/／;；]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function unique(values) {
  return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, "zh-Hant")
  );
}

function renderEmpty(selector, title, message) {
  const template = $("#empty-template");
  const node = template.content.firstElementChild.cloneNode(true);
  node.querySelector("strong").textContent = title;
  node.querySelector("span").textContent = message;
  $(selector).replaceChildren(node);
  initIcons();
}

function announce(message, type = "loading", persist = false) {
  window.clearTimeout(state.statusTimer);
  const icon = type === "error" ? "circle-alert" : type === "success" ? "circle-check" : "loader-circle";
  $("#page-status").innerHTML = `<div class="status-message ${escapeHtml(type)}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${escapeHtml(message)}</span>${type === "error" ? '<button id="retry-load" type="button" class="secondary-button">重試</button>' : ""}</div>`;
  initIcons();
  if (!persist && type !== "error") {
    state.statusTimer = window.setTimeout(clearAnnouncement, 2600);
  }
}

function clearAnnouncement() {
  window.clearTimeout(state.statusTimer);
  $("#page-status").replaceChildren();
}

function showLoadError(error) {
  announce(`資料載入失敗：${error.message}`, "error", true);
  renderEmpty("#partner-table", "暫時無法取得學校資料", "請確認 API 已啟動後重新嘗試。");
  renderEmpty("#period-list", "暫時無法取得截止日期", "重新整理後再試一次。");
  renderEmpty("#scholarship-list", "暫時無法取得補助資料", "重新整理後再試一次。");
  renderEmpty("#documents-list", "暫時無法取得文件摘要", "重新整理後再試一次。");
}

function setActiveNavigation(sectionId) {
  document.querySelectorAll("[data-section]").forEach((item) => {
    const active = item.dataset.section === sectionId;
    item.classList.toggle("active", active);
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
  const mobileSection = { advisor: "overview", "document-check": "application-center", "writing-assistant": "application-center" }[sectionId] || sectionId;
  document.querySelectorAll(".university-mobile-nav [data-section]").forEach((item) => {
    const active = item.dataset.section === mobileSection;
    item.classList.toggle("active", active);
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
}

function resetRouteScroll() {
  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "instant" });
  scrollToTop();
  window.requestAnimationFrame(scrollToTop);
}

function showUniversityPage(pageId, { resetScroll = true, focusHeading = true } = {}) {
  const activePage = UNIVERSITY_PAGE_ROUTES.has(pageId) ? pageId : null;
  const pageNodes = [...document.querySelectorAll("[data-university-page]")];
  pageNodes.forEach((node) => {
    node.hidden = !activePage || node.dataset.universityPage !== activePage;
  });

  if (!activePage) {
    delete document.body.dataset.activeUniversityPage;
    return null;
  }

  document.body.dataset.activeUniversityPage = activePage;
  setActiveNavigation(activePage === "search" ? "" : activePage === "application-form" ? "application-center" : activePage);
  document.title = `${UNIVERSITY_PAGE_TITLES[activePage]} | 台灣大學生交換指南`;

  if (resetScroll) resetRouteScroll();
  if (focusHeading) {
    window.requestAnimationFrame(() => {
      const page = pageNodes.find((node) => node.dataset.universityPage === activePage && !node.hidden);
      const heading = page?.querySelector("h1, h2");
      if (!heading) return;
      heading.setAttribute("tabindex", "-1");
      heading.focus({ preventScroll: true });
    });
  }
  return activePage;
}

function globalFeedForHash(hash = window.location.hash) {
  return {
    "#home": "all",
    "#following": "following",
    "#public-board": "public",
    "#cgu-feed": "cgu",
    "#university-feed": "university",
  }[hash] || null;
}

function isUniversityBoardRoute(hash = window.location.hash) {
  return /^#board=/.test(hash)
    || hash === "#cgu-posts"
    || hash === "#university-posts"
    || /^#school=/.test(hash)
    || /^#application-form=/.test(hash)
    || ["#overview", "#advisor", "#partners", "#favorites", "#calendar", "#deadlines", "#scholarships", "#budget", "#eligibility", "#application-center", "#document-check", "#writing-assistant", "#documents", "#search"].includes(hash);
}

function applyAppRoute({ loadFeed = true, resetScroll = true } = {}) {
  const hash = window.location.hash || "#home";
  const globalFeed = globalFeedForHash(hash);
  const isUniversityPosts = hash === "#cgu-posts" || hash === "#university-posts";
  document.body.classList.toggle("global-home-mode", Boolean(globalFeed));
  document.body.classList.toggle("university-board-mode", !globalFeed);
  document.body.classList.toggle("cgu-community-mode", isUniversityPosts);

  if (globalFeed) {
    showUniversityPage(null, { resetScroll: false, focusHeading: false });
    state.globalCommunityFeed = globalFeed;
    renderCommunityPageContext(false);
    renderGlobalCommunityNavigation();
    setActiveNavigation("");
    document.title = `${globalFeed === "following" ? "我的追蹤" : globalFeed === "public" ? "公共留學板" : globalFeed === "cgu" ? "長庚大學貼文" : globalFeed === "university" ? `${activeHomeSchool()}貼文` : "留學首頁"} | 台灣大學生交換指南`;
    if (!state.activeSchool) {
      $("#dashboard-view").hidden = false;
      $("#school-detail-view").hidden = true;
    }
    if (resetScroll) resetRouteScroll();
    if (loadFeed) loadGlobalCommunity();
    return;
  }

  if (isUniversityPosts) {
    showUniversityPage(null, { resetScroll: false, focusHeading: false });
    state.globalCommunityFeed = hash === "#cgu-posts" ? "cgu" : "university";
    renderCommunityPageContext(true);
    setActiveNavigation("university-posts");
    document.title = `${activeHomeSchool()}討論板 | 台灣大學生交換指南`;
    if (resetScroll) resetRouteScroll();
    if (loadFeed) loadGlobalCommunity();
    return;
  }

  if (hash.startsWith("#board=")) {
    const boardName = decodeURIComponent(hash.slice("#board=".length));
    setHomeSchool(boardName);
    showUniversityPage("overview", { resetScroll, focusHeading: resetScroll });
    return;
  }

  const applicationFormRoute = hash.match(/^#application-form=(.+)$/);
  if (applicationFormRoute) {
    const templateId = decodeURIComponent(applicationFormRoute[1]);
    state.activeApplicationTemplateId = templateId;
    showUniversityPage("application-form", { resetScroll, focusHeading: false });
    const template = applicationTemplateById(templateId);
    if (template) renderApplicationFormPage(template);
    else {
      $("#application-form-title").textContent = "正在載入申請文件";
      $("#application-form-description").textContent = "系統正在核對這份文件的欄位、份數與送件要求。";
    }
    return;
  }

  const sectionId = hash.slice(1) || "overview";
  showUniversityPage(UNIVERSITY_PAGE_ROUTES.has(sectionId) ? sectionId : "overview", {
    resetScroll,
    focusHeading: resetScroll,
  });
}

function handleLocationRoute() {
  const route = window.location.hash.match(/^#school=(.+)$/);
  if (route && state.dashboard) {
    document.body.classList.remove("global-home-mode", "cgu-community-mode");
    document.body.classList.add("university-board-mode");
    const item = partnerByName(decodeURIComponent(route[1]));
    if (item && state.activeSchool !== item.school_name) {
      openUniversityDetail(item, { updateHistory: false });
    }
    return;
  }
  if (state.activeSchool) closeUniversityDetail({ updateHistory: false });
  applyAppRoute();
}

function bindEvents() {
  $("#account-button").addEventListener("click", () => state.account ? openProfileDialog() : openAuthDialog());
  $("#mobile-account-button")?.addEventListener("click", () => state.account ? openProfileDialog() : openAuthDialog());
  $("#global-mobile-account-button").addEventListener("click", () => state.account ? openProfileDialog() : openAuthDialog());
  document.querySelectorAll("[data-close-auth]").forEach((button) => button.addEventListener("click", closeAuthDialog));
  document.querySelectorAll("[data-close-profile]").forEach((button) => button.addEventListener("click", closeProfileDialog));
  document.querySelectorAll("[data-auth-mode]").forEach((button) => button.addEventListener("click", () => setAuthMode(button.dataset.authMode)));
  document.querySelectorAll("[data-oauth-provider]").forEach((button) => button.addEventListener("click", () => {
    if (button.disabled) return;
    const params = new URLSearchParams();
    if (state.authMode === "register" && state.studentVerificationToken) {
      params.set("student_verification_token", state.studentVerificationToken);
    }
    const suffix = params.toString() ? `?${params}` : "";
    window.location.href = `/auth/oauth/${encodeURIComponent(button.dataset.oauthProvider)}/start${suffix}`;
  }));
  $("#student-card-front").addEventListener("change", (event) => renderStudentCardPreview(event.currentTarget, "front"));
  $("#student-card-back").addEventListener("change", (event) => renderStudentCardPreview(event.currentTarget, "back"));
  $("#verify-student-card").addEventListener("click", verifyStudentCard);
  $("#login-form").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAccountForm(event.currentTarget, "/auth/login");
  });
  $("#register-form").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAccountForm(event.currentTarget, "/auth/register");
  });
  $("#profile-form").addEventListener("submit", saveAccountProfile);
  $("#logout-button").addEventListener("click", logoutAccount);
  $("#delete-account-button").addEventListener("click", deleteAccount);
  document.addEventListener("keydown", (event) => {
    trapAccountDialogFocus(event);
    if (event.key === "Escape") {
      if (!$("#auth-dialog").hidden) closeAuthDialog();
      if (!$("#profile-dialog").hidden) closeProfileDialog();
    }
  });

  $("#global-community-compose").addEventListener("click", openGlobalCommunityComposer);
  $("#sidebar-community-compose").addEventListener("click", openGlobalCommunityComposer);
  $("#global-mobile-compose").addEventListener("click", openGlobalCommunityComposer);
  $("#global-community-form").addEventListener("submit", submitGlobalCommunityPost);
  $("#global-community-form").addEventListener("click", (event) => {
    if (event.target.closest("[data-cancel-global-post]")) event.currentTarget.hidden = true;
  });
  $("#global-community-topics").addEventListener("click", (event) => {
    const button = event.target.closest("[data-global-community-topic]");
    if (!button) return;
    state.globalCommunityTopic = button.dataset.globalCommunityTopic;
    renderGlobalCommunityTopics();
    loadGlobalCommunity();
  });
  $("#global-community-search").addEventListener("input", (event) => {
    window.clearTimeout(state.globalCommunityTimer);
    state.globalCommunityTimer = window.setTimeout(() => {
      state.globalCommunityQuery = event.target.value.trim();
      loadGlobalCommunity();
    }, 280);
  });
  $("#global-community-feed").addEventListener("submit", async (event) => {
    const form = event.target.closest(".post-comment-form");
    if (!form) return;
    event.preventDefault();
    if (await handleCommunityFormSubmit(form, submitPostCommentForm, "回覆已發布。")) await loadGlobalCommunity();
  });
  $("#global-community-feed").addEventListener("click", async (event) => {
    const report = event.target.closest("[data-report-resource]");
    if (report) await reportCommunityResource(report);
  });

  $("#search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    runSearch($("#search-input").value);
  });

  $("#refresh-button").addEventListener("click", async () => {
    if (document.body.classList.contains("global-home-mode") || document.body.classList.contains("cgu-community-mode")) {
      await loadGlobalCommunity();
    } else {
      await Promise.all([
        loadDashboard({ refreshed: true }),
        loadCoverage(),
        loadDestinationProfiles(),
      ]);
      applyAppRoute({ loadFeed: false, resetScroll: false });
    }
  });
  $("#school-switcher").addEventListener("click", openSchoolOnboarding);
  $("#theme-toggle").addEventListener("click", () => {
    applyTheme(state.theme === "dark" ? "light" : "dark");
  });

  $("#school-search").addEventListener("input", (event) => renderSchoolOptions(event.target.value));
  $("#school-options").addEventListener("click", (event) => {
    const option = event.target.closest("[data-home-school]");
    if (!option) return;
    state.selectedHomeSchool = option.dataset.homeSchool;
    renderSchoolOptions($("#school-search").value);
  });
  $("#confirm-school").addEventListener("click", () => setHomeSchool(state.selectedHomeSchool));
  $("#browse-first").addEventListener("click", browseWithoutSchoolSelection);
  document.addEventListener("keydown", handleOnboardingKeydown);

  $("#partner-search").addEventListener("input", (event) => {
    state.partnerQuery = event.target.value;
    state.partnerLimit = window.matchMedia("(max-width: 820px)").matches ? 8 : 20;
    renderPartnerTable();
  });

  ["country", "college", "degree"].forEach((name) => {
    $(`#${name}-filter`).addEventListener("change", (event) => {
      state[name] = event.target.value;
      state.partnerLimit = window.matchMedia("(max-width: 820px)").matches ? 8 : 20;
      renderPartnerTable();
    });
  });

  $("#clear-partner-filters").addEventListener("click", () => {
    state.partnerQuery = "";
    state.country = "";
    state.college = "";
    state.degree = "";
    state.partnerLimit = window.matchMedia("(max-width: 820px)").matches ? 8 : 20;
    $("#partner-search").value = "";
    renderPartnerFilters();
    renderPartnerTable();
  });

  $("#show-more-partners").addEventListener("click", () => {
    state.partnerLimit += window.matchMedia("(max-width: 820px)").matches ? 8 : 20;
    renderPartnerTable();
  });

  $("#calendar-event-form").elements.date.value = localDateKey();
  $("#calendar-event-form").addEventListener("submit", (event) => {
    event.preventDefault();
    addCalendarEvent(event.currentTarget);
    event.currentTarget.closest("details")?.removeAttribute("open");
  });
  $("#calendar-previous-month").addEventListener("click", () => {
    state.calendarMonth = new Date(state.calendarMonth.getFullYear(), state.calendarMonth.getMonth() - 1, 1);
    renderApplicationCalendar();
  });
  $("#calendar-next-month").addEventListener("click", () => {
    state.calendarMonth = new Date(state.calendarMonth.getFullYear(), state.calendarMonth.getMonth() + 1, 1);
    renderApplicationCalendar();
  });
  $("#calendar-today").addEventListener("click", () => {
    const today = new Date();
    state.calendarMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    state.calendarSelectedDate = localDateKey(today);
    state.calendarAgendaMode = "selected";
    renderApplicationCalendar();
  });
  $("#calendar-sync-button").addEventListener("click", () => {
    $("#calendar-sync-panel").open = true;
    $("#calendar-sync-panel").scrollIntoView({ behavior: "smooth", block: "center" });
  });
  $("#calendar").addEventListener("click", (event) => {
    const provider = event.target.closest("[data-calendar-provider]");
    if (provider) {
      state.calendarProvider = provider.dataset.calendarProvider;
      renderCalendarSync();
      return;
    }
    if (event.target.closest("[data-enable-calendar-sync]")) {
      enableCalendarSync();
      return;
    }
    if (event.target.closest("[data-calendar-sync-now]")) {
      syncCalendarEvents();
      return;
    }
    if (event.target.closest("[data-copy-calendar-url]")) {
      copyCalendarSubscriptionUrl();
      return;
    }
    if (event.target.closest("[data-revoke-calendar-sync]")) {
      revokeCalendarSync();
      return;
    }
    const dateButton = event.target.closest("[data-calendar-date]");
    if (dateButton) {
      state.calendarSelectedDate = dateButton.dataset.calendarDate;
      state.calendarAgendaMode = "selected";
      renderApplicationCalendar();
      return;
    }
    const download = event.target.closest("[data-download-calendar-event]");
    if (download) {
      const item = allApplicationCalendarEvents().find((row) => row.id === download.dataset.downloadCalendarEvent);
      if (item) downloadCalendarEvents([item], `${item.date}-${item.title.replace(/[^\p{L}\p{N}-]+/gu, "-")}.ics`);
      return;
    }
    const remove = event.target.closest("[data-delete-calendar-event]");
    if (remove) deleteCalendarEvent(remove.dataset.deleteCalendarEvent);
  });

  $("#eligibility-form").addEventListener("submit", checkEligibility);
  $("#clear-saved-eligibility").addEventListener("click", clearEligibilityProfile);
  $("#advisor-form").addEventListener("submit", submitAdvisorPlan);
  $("#advisor-form").addEventListener("click", (event) => {
    const prompt = event.target.closest("[data-advisor-question]");
    if (!prompt) return;
    $("#advisor-question").value = prompt.dataset.advisorQuestion;
    $("#advisor-question").focus();
  });
  $("#document-check-form").addEventListener("submit", submitDocumentCheck);
  $("#document-check-file").addEventListener("change", (event) => {
    const file = event.currentTarget.files?.[0];
    $("#document-upload-title").textContent = file?.name || "選擇申請文件";
    $("#document-upload-meta").textContent = file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : "PDF、DOCX 或 TXT，10 MB 以內";
  });
  $("#writing-assistant-form").addEventListener("submit", submitWritingAssistant);
  $("#writing-assistant-result").addEventListener("click", async (event) => {
    if (!event.target.closest("[data-copy-writing-draft]") || !state.writingAssistantResult?.draft) return;
    try {
      await navigator.clipboard.writeText(state.writingAssistantResult.draft);
      announce("建議稿已複製", "success");
    } catch (_) {
      announce("瀏覽器無法存取剪貼簿", "error");
    }
  });

  $("#budget-form").addEventListener("submit", saveBudgetPlan);
  $("#budget-form").addEventListener("input", updateBudgetResult);
  $("#budget-currency").addEventListener("change", updateBudgetResult);
  $("#budget-school").addEventListener("change", (event) => populateBudgetForm(event.target.value));

  $("#application-context-form").addEventListener("submit", (event) => event.preventDefault());
  $("#application-context-form").addEventListener("change", handleApplicationContextChange);
  $("#application-profile-form").addEventListener("submit", saveApplicationProfile);
  $("#application-remember-profile").addEventListener("change", (event) => setApplicationProfileMemory(event.target.checked));
  $("#clear-application-profile-memory").addEventListener("click", clearApplicationProfileMemory);
  $("#application-template-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-open-application-template]");
    if (!button) return;
    window.location.hash = `#application-form=${encodeURIComponent(button.dataset.openApplicationTemplate)}`;
  });
  $("#application-packet-list").addEventListener("change", (event) => {
    const checkbox = event.target.closest("[data-application-packet-template]");
    if (checkbox) {
      const template = applicationTemplateById(checkbox.dataset.applicationPacketTemplate);
      if (!template) return;
      state.applicationSelections[template.id] = {
        selected: checkbox.checked,
        copies: state.applicationSelections[template.id]?.copies || template.default_copies,
        status: applicationDocumentStatus(template.id),
      };
      persistApplicationContext();
      renderApplicationTemplates();
      renderApplicationPacket();
      updateApplicationCenterSteps();
      initIcons();
      return;
    }
    const copies = event.target.closest("[data-application-copy-template]");
    if (copies) {
      const template = applicationTemplateById(copies.dataset.applicationCopyTemplate);
      if (!template) return;
      const value = Math.max(1, Math.min(10, Number(copies.value) || template.default_copies));
      state.applicationSelections[template.id] = { selected: true, copies: value, status: applicationDocumentStatus(template.id) };
      persistApplicationContext();
      renderApplicationPacket();
    }
  });
  $("#download-application-packet").addEventListener("click", () => generateApplicationPdf());
  $("#back-to-application-center").addEventListener("click", () => { window.location.hash = "#application-center"; });
  $("#application-document-form").addEventListener("submit", saveApplicationDocument);
  $("#application-document-form").addEventListener("change", (event) => {
    const statusSelect = event.target.closest("[data-application-status-template]");
    if (statusSelect) {
      const template = applicationTemplateById(statusSelect.dataset.applicationStatusTemplate);
      if (!template) return;
      const existing = state.applicationSelections[template.id] || { selected: false, copies: template.default_copies };
      state.applicationSelections[template.id] = { ...existing, status: statusSelect.value };
      persistApplicationContext();
      const next = $("#application-document-next-step");
      if (next) next.textContent = applicationDocumentNextStep(template);
      return;
    }
    const input = event.target.closest('input[type="file"][data-application-field]');
    if (input) {
      handleApplicationFiles(input);
      return;
    }
    const sharedInput = event.target.closest("[data-application-field]");
    if (sharedInput) {
      const template = applicationTemplateById(state.activeApplicationTemplateId);
      if (template) rememberApplicationField(template, sharedInput);
    }
  });
  $("#application-form-print-guide").addEventListener("change", (event) => {
    const statusSelect = event.target.closest("[data-application-status-template]");
    if (!statusSelect) return;
    const template = applicationTemplateById(statusSelect.dataset.applicationStatusTemplate);
    if (!template) return;
    const existing = state.applicationSelections[template.id] || { selected: false, copies: template.default_copies };
    state.applicationSelections[template.id] = { ...existing, status: statusSelect.value };
    persistApplicationContext();
    const next = $("#application-document-next-step");
    if (next) next.textContent = applicationDocumentNextStep(template);
  });
  $("#download-single-application-document").addEventListener("click", () => generateApplicationPdf(state.activeApplicationTemplateId));

  $("#document-filters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-document-type]");
    if (!button) return;
    state.documentType = button.dataset.documentType;
    renderDocumentFilters();
    renderDocuments();
  });

  $("#close-search").addEventListener("click", () => {
    window.location.hash = state.searchReturnHash || "#overview";
  });

  $("#back-to-schools").addEventListener("click", () => closeUniversityDetail());
  window.addEventListener("scroll", queueSchoolHeroMotion, { passive: true });
  window.addEventListener("resize", queueSchoolHeroMotion, { passive: true });
  $(".detail-tabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-detail-target]");
    if (!button) return;
    activateDetailTab(button.dataset.detailTarget, { scroll: true });
  });
  $(".detail-tabs").addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const tabs = [...event.currentTarget.querySelectorAll('[role="tab"]')];
    const current = tabs.indexOf(event.target.closest('[role="tab"]'));
    if (current < 0) return;
    event.preventDefault();
    let next = current;
    if (event.key === "ArrowRight") next = (current + 1) % tabs.length;
    if (event.key === "ArrowLeft") next = (current - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    activateDetailTab(tabs[next].dataset.detailTarget, { focus: true, scroll: true });
  });
  $("#school-detail-content").addEventListener("click", async (event) => {
    const communityView = event.target.closest("[data-community-view]");
    if (communityView) {
      selectCommunityView(communityView.dataset.communityView);
      return;
    }
    const invite = event.target.closest("[data-invite-recipient]");
    if (invite) {
      openPrivateInvite(invite.dataset.inviteRecipient, invite.dataset.recipientName);
      return;
    }
    if (event.target.closest("[data-cancel-invite]")) {
      const form = $("#private-invite-form");
      if (form) form.hidden = true;
      return;
    }
    const acceptConversation = event.target.closest("[data-accept-conversation]");
    if (acceptConversation) {
      acceptConversation.disabled = true;
      try {
        await submitCommunityJson(`/community/conversations/${encodeURIComponent(acceptConversation.dataset.acceptConversation)}/accept`, {});
        await refreshCommunityHub("messages");
      } catch (error) {
        announce(error.message, "error", true);
        acceptConversation.disabled = false;
      }
      return;
    }
    const report = event.target.closest("[data-report-resource]");
    if (report) {
      await reportCommunityResource(report);
      return;
    }
    const block = event.target.closest("[data-block-identity]");
    if (block) {
      if (!window.confirm("封鎖後，雙方將無法繼續這段私訊。確定封鎖嗎？")) return;
      try {
        await submitCommunityJson("/community/blocks", { target_id: block.dataset.blockIdentity });
        await refreshCommunityHub("messages");
      } catch (error) {
        announce(error.message, "error", true);
      }
      return;
    }
    const communityRetry = event.target.closest("#retry-community");
    if (communityRetry && state.activeSchool) {
      const item = partnerByName(state.activeSchool);
      if (item) loadCommunityQuestions(item);
      return;
    }
    const workflowRefresh = event.target.closest("#refresh-workflow, #retry-workflow");
    if (workflowRefresh && state.activeSchool) {
      const item = partnerByName(state.activeSchool);
      if (item) loadApplicationWorkflow(item, { forceRefresh: true });
      return;
    }
    const refresh = event.target.closest("#refresh-experiences, #retry-experiences");
    if (!refresh || !state.activeSchool) return;
    const item = partnerByName(state.activeSchool);
    if (item) loadStudentExperiences(item, { forceRefresh: true });
  });
  $("#school-detail-content").addEventListener("change", (event) => {
    const checkbox = event.target.closest(".progress-checkbox");
    if (checkbox) updateApplicationProgress(checkbox.dataset.progressStep, checkbox.checked);
  });
  $("#school-detail-content").addEventListener("submit", async (event) => {
    const form = event.target.closest("form");
    if (!form) return;
    if (form.id === "community-post-form") {
      event.preventDefault();
      if (await handleCommunityFormSubmit(form, submitCommunityPostForm, "貼文已發布。")) await refreshCommunityHub("posts");
      return;
    }
    if (form.classList.contains("post-comment-form")) {
      event.preventDefault();
      if (await handleCommunityFormSubmit(form, submitPostCommentForm, "回覆已發布。")) await refreshCommunityHub("posts");
      return;
    }
    if (form.id === "public-chat-form") {
      event.preventDefault();
      if (await handleCommunityFormSubmit(form, submitPublicChatForm, "訊息已送出。")) await refreshCommunityHub("chat");
      return;
    }
    if (form.id === "private-invite-form") {
      event.preventDefault();
      if (await handleCommunityFormSubmit(form, submitPrivateInviteForm, "邀請已送出。")) await refreshCommunityHub("messages");
      return;
    }
    if (form.classList.contains("private-message-form")) {
      event.preventDefault();
      if (await handleCommunityFormSubmit(form, submitPrivateMessageForm, "私訊已送出。")) await refreshCommunityHub("messages");
      return;
    }
    if (form.id === "question-form") {
      event.preventDefault();
      handleCommunityFormSubmit(form, submitQuestionForm, "問題已送出，審核後會出現在公開問答。 ");
      return;
    }
    if (form.id === "experience-submission-form") {
      event.preventDefault();
      handleCommunityFormSubmit(form, submitExperienceForm, "心得已送出，審核後會加入統整並保留來源。 ");
      return;
    }
    if (form.classList.contains("answer-form")) {
      event.preventDefault();
      handleCommunityFormSubmit(form, submitAnswerForm, "回答已送出，審核後公開。 ");
    }
  });

  document.body.addEventListener("click", (event) => {
    const advisorCalendar = event.target.closest("[data-advisor-calendar]");
    if (advisorCalendar) {
      addAdvisorTaskToCalendar(advisorCalendar.dataset.advisorCalendar);
      return;
    }
    if (event.target.closest("[data-retry-advisor]")) {
      $("#advisor-form").requestSubmit();
      return;
    }
    if (event.target.closest("[data-mark-update-seen]")) {
      markDataReviewSeen();
      return;
    }
    if (event.target.closest("[data-open-auth]")) {
      openAuthDialog();
      return;
    }
    const followBoard = event.target.closest("[data-follow-board]");
    if (followBoard?.dataset.followBoard) {
      toggleBoardFollow(followBoard.dataset.followBoard);
      return;
    }
    const application = event.target.closest(".application-toggle");
    if (application?.dataset.schoolName) {
      toggleApplication(application.dataset.schoolName);
      return;
    }
    const favorite = event.target.closest(".favorite-toggle");
    if (favorite?.dataset.schoolName) {
      toggleFavorite(favorite.dataset.schoolName);
      return;
    }
    const trigger = event.target.closest(".school-detail-trigger");
    if (trigger?.dataset.schoolName) openUniversityDetail(partnerByName(trigger.dataset.schoolName));
  });
  document.body.addEventListener("change", (event) => {
    const status = event.target.closest("[data-document-status]");
    if (status) {
      updateDocumentStatus(status.dataset.documentStatus, status.value);
      return;
    }
    const checkbox = event.target.closest(".document-readiness-checkbox");
    if (checkbox) updateDocumentReadiness(checkbox.dataset.documentId, checkbox.checked);
  });

  $("#page-status").addEventListener("click", (event) => {
    if (event.target.closest("#retry-load")) loadDashboard({ refreshed: true });
  });

  document.querySelectorAll("[data-section]").forEach((link) => {
    link.addEventListener("click", () => {
      setActiveNavigation(link.dataset.section);
      if (window.location.hash === link.getAttribute("href")) {
        applyAppRoute({ loadFeed: false });
      }
    });
  });

  window.addEventListener("popstate", handleLocationRoute);
  window.addEventListener("hashchange", handleLocationRoute);
}

async function boot() {
  if (!window.location.hash || window.location.hash === "#community-hub") {
    window.history.replaceState({}, "", "#home");
  }
  initializeTheme();
  readStoredState();
  applyAppRoute({ loadFeed: false, resetScroll: false });
  bindEvents();
  renderGlobalCommunityTopics();
  initIcons();
  await Promise.all([loadSupportedUniversities(), loadAuthProviders(), restoreAccount(), loadSchoolImages(), loadAdvisorStatus()]);
  await loadDashboard();
  await loadApplicationTemplates();
  applyAppRoute({ loadFeed: false, resetScroll: false });
  if (isUniversityBoardRoute() && !state.homeSchool) initializeSchoolOnboarding();
  await loadGlobalCommunity();
  await Promise.all([loadCoverage(), loadDestinationProfiles()]);
  const route = window.location.hash.match(/^#school=(.+)$/);
  if (route) {
    const item = partnerByName(decodeURIComponent(route[1]));
    if (item) openUniversityDetail(item, { updateHistory: false });
  }
}

boot();
