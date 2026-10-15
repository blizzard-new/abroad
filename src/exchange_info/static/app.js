const state = {
  dashboard: null,
  query: "",
  partnerQuery: "",
  partnerView: "list",
  partnerDataLoading: false,
  partnerDataError: false,
  availability: "",
  region: "",
  country: "",
  college: "",
  degree: "",
  partnerSort: "match",
  partnerQuota: "",
  partnerFit: "",
  partnerLimit: window.matchMedia("(max-width: 820px)").matches ? 20 : 30,
  documentType: "全部",
  statusTimer: null,
  statusRevision: 0,
  hasLoaded: false,
  activeSchool: null,
  experienceRequestId: 0,
  experienceCache: new Map(),
  workflowRequestId: 0,
  workflowCache: new Map(),
  activeWorkflow: null,
  workflowIssueReportContext: null,
  workflowIssueReportMutationId: "",
  workflowIssueReportPayloadKey: "",
  workflowIssueReportSubmitting: false,
  workflowIssueReportPending: null,
  workflowIssueReportRequestId: 0,
  workflowIssueReportAbortController: null,
  calendarWorkflowAttempts: new Set(),
  destinationRequestId: 0,
  destinationCache: new Map(),
  completenessCache: new Map(),
  completenessRequestId: 0,
  lifeContextCache: new Map(),
  lifeContextLoading: new Set(),
  communityRequestId: 0,
  communityCache: new Map(),
  communityView: "posts",
  anonymousIdentity: null,
  communityIdentityOptions: null,
  account: null,
  notifications: [],
  notificationUnreadCount: 0,
  notificationLoading: false,
  notificationRequestId: 0,
  entitlements: null,
  accountWorkspaceLoadedSchool: "",
  accountWorkspaceSyncTimer: null,
  accountWorkspaceSyncSuspended: false,
  accountWorkspaceRevisions: {},
  accountWorkspaceBases: {},
  accountWorkspacePending: {},
  accountWorkspaceSyncLanes: {},
  accountWorkspaceLoadingCount: 0,
  accountWorkspaceRetryTimer: null,
  accountWorkspaceSyncAccountId: "",
  accountWorkspaceSyncErrors: {},
  accountWorkspaceHasSynced: false,
  authSessionEpoch: 0,
  authRestoreState: "pending",
  authRestoreRequestId: 0,
  profileFilledFor: "",
  quarantinedAccountOwnerId: "",
  authProviders: [],
  authMode: "login",
  globalCommunityTopic: "",
  globalCommunityQuery: "",
  globalCommunityThreads: [],
  communityBoards: [],
  globalCommunityTimer: null,
  globalCommunityFeed: "all",
  theme: "light",
  themePreference: "light",
  homeSchool: "",
  selectedHomeSchool: "長庚大學",
  chooseSchoolForAccount: false,
  choosingSchool: false,
  pendingSchoolPrompt: false,
  supportedUniversities: [],
  coverage: null,
  guestComparisons: new Set(),
  favorites: new Set(),
  applications: new Set(),
  applicationProgress: {},
  documentReadiness: {},
  eligibilityProfile: null,
  applicationPeriodOptions: null,
  applicationPeriodRequestId: 0,
  personalApplicationPlan: null,
  destinationProfiles: [],
  schoolImages: [],
  ncuSchoolImages: [],
  calendarEvents: [],
  preparationTasks: {},
  planningAvailability: null,
  calendarMonth: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  calendarSelectedDate: "",
  calendarAgendaMode: "upcoming",
  calendarSync: null,
  calendarSyncLoading: false,
  calendarProvider: "google",
  calendarConflictReport: null,
  calendarConflictLoading: false,
  calendarConflictError: "",
  calendarConflictRequestSequence: 0,
  calendarConflictTimer: null,
  calendarTaskScheduleReport: null,
  calendarTaskScheduleLoading: false,
  calendarTaskScheduleError: "",
  calendarTaskScheduleRequestSequence: 0,
  calendarTaskScheduleTimer: null,
  budgetPlans: {},
  budgetSchool: "",
  pendingBudgetDraft: null,
  applicationTemplates: [],
  applicationDocumentCatalog: null,
  applicationDocumentCatalogError: "",
  applicationDocumentCatalogContextKey: "",
  applicationTemplateRequestId: 0,
  applicationContext: {
    school_name: "長庚大學",
    target_school: "",
    target_country: "",
    program_type: "exchange",
    college: "",
    department: "",
    degree_level: "",
    academic_year: "",
    application_round: "",
    semester: "",
    flags: [],
  },
  applicationProfile: {},
  applicationProfileMemoryEnabled: false,
  applicationAnswers: {},
  applicationFormDrafts: {},
  applicationFormDraftLoadedSchool: "",
  applicationFormDraftSyncTimer: null,
  applicationFormDraftSyncSuspended: false,
  applicationFormDraftPending: {},
  applicationFileVaultLinks: {},
  applicationFileConsentCandidate: null,
  applicationDownloadSummary: null,
  applicationPreviews: {},
  applicationPreviewTimers: {},
  applicationPreviewRequestIds: {},
  applicationSelections: {},
  submissionProgress: {},
  applicationFiles: {},
  activeApplicationTemplateId: "",
  applicationLoading: false,
  homeSchoolLoading: false,
  advisorPlan: null,
  planningPreview: null,
  planningRequestId: 0,
  planningLoading: false,
  planningRecommendationKey: "",
  planningPlanProfileKey: "",
  advisorLoading: false,
  conditionsRequestId: 0,
  aiStatus: null,
  documentCheckResult: null,
  documentCheckLoading: false,
  documentCheckRequestId: 0,
  documentCheckGeneratedCandidate: null,
  documentCheckProvenance: null,
  documentCheckAbortController: null,
  privateVault: { items: [], total_bytes: 0, max_file_bytes: 20 * 1024 * 1024 },
  privateVaultLoading: false,
  privateVaultRequestId: 0,
  privateVaultError: "",
  privateVaultEditingDocumentId: "",
  privateVaultFormRevision: 0,
  generatedVaultCandidate: null,
  useGeneratedVaultCandidate: false,
  updateSeenAt: "",
  emailVerificationToken: "",
  emailVerificationAddress: "",
  dashboardScrollY: 0,
  dashboardHash: "#overview",
  searchReturnHash: "#overview",
  onboardingReturnFocus: null,
  dialogReturnFocus: null,
  homeSchoolRequestId: 0,
  schoolContextVersion: 0,
  schoolDataRequestIds: {},
};

const $ = (selector) => document.querySelector(selector);

const PUBLIC_COMMUNITY_BOARD = "公共留學板";
const LEGACY_PUBLIC_COMMUNITY_BOARD = "一般留學討論";
const LANGUAGE_SCHOOL_COMMUNITY_BOARD = "語言學校板";
const PUBLIC_COMMUNITY_BOARD_ID = "public-study-abroad";
const LANGUAGE_SCHOOL_COMMUNITY_BOARD_ID = "language-school";
const PUBLIC_COMMUNITY_BOARDS = [
  PUBLIC_COMMUNITY_BOARD,
  LEGACY_PUBLIC_COMMUNITY_BOARD,
  LANGUAGE_SCHOOL_COMMUNITY_BOARD,
];
const CGU_COMMUNITY_BOARD = "長庚大學";
const NTPU_COMMUNITY_BOARD = "國立臺北大學";
const DEFAULT_HOME_SCHOOL = CGU_COMMUNITY_BOARD;
const WORKFLOW_SUBMISSION_LABELS = {
  paper: "紙本送件",
  online: "線上申請／上傳",
  email: "電子郵件 送件",
  in_person: "親自送件",
  mixed: "混合送件",
  unknown: "送件方式待確認",
};
const APPLICATION_COPY_TYPE_LABELS = {
  original: "正本",
  copy: "影本",
  original_and_copy: "正本＋影本",
  digital: "電子檔",
  unspecified: "形式待確認",
};
const SUBMISSION_PROGRESS_STATUS_LABELS = {
  not_started: "尚未開始",
  preparing: "準備中",
  submitted: "已由我送出",
  receipt_confirmed: "我已記錄收件",
  completed: "我已標記完成",
};
const SUBMISSION_PROOF_LABELS = {
  tracking: "物流追蹤紀錄",
  submission_receipt: "系統送出回條",
  confirmation_email: "收件確認 電子郵件",
  in_person_receipt: "親送收據",
  other: "其他收件證明",
};
const WORKFLOW_COPY_LABELS = {
  original: "正本",
  copy: "影本",
  original_and_copy: "正本＋影本",
  digital: "電子檔",
  unspecified: "文件形式待確認",
};
const WORKFLOW_SOURCE_LABELS = {
  home_official_notice: "母校當期正式公告",
  home_academic_unit: "母校承辦單位／學系公告",
  nomination_notice: "提名或個人通知",
  partner_official: "合作校官方資訊",
  community_experience: "經驗補充",
};
const UNIVERSITY_PAGE_ROUTES = new Set([
  "home",
  "guide",
  "profile",
  "feedback",
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
  home: "首頁",
  guide: "申請指南",
  profile: "個人中心",
  feedback: "用戶評價",
  overview: "我的申請",
  advisor: "選校規劃",
  partners: "找交換學校",
  favorites: "收藏與比較",
  calendar: "申請日曆",
  deadlines: "官方截止日",
  scholarships: "補助資訊",
  budget: "交換預算",
  eligibility: "資格與志願",
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
  planningAvailability: "exchange-guide-planning-availability",
  preparationTasks: "exchange-guide-preparation-tasks",
  budgetPlans: "exchange-guide-budget-plans",
  applicationContext: "exchange-guide-application-context",
  applicationSelections: "exchange-guide-application-selections",
  submissionProgress: "exchange-guide-submission-progress",
  workspaceSync: "exchange-guide-workspace-sync-v1",
  applicationProfileMemory: "exchange-guide-application-profile-memory-v1",
  applicationProfileMemoryEnabled: "exchange-guide-application-profile-memory-enabled",
  updateSeenAt: "exchange-guide-update-seen-at",
};

const APPLICATION_SESSION_KEYS = {
  profile: "exchange-guide-application-profile-session",
  answers: "exchange-guide-application-answers-session",
  accountDeletionMutation: "exchange-guide-account-deletion-mutation-v1",
  workflowIssueReportPending: "exchange-guide-workflow-issue-report-pending-v1",
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

const APPLICATION_FILE_CATEGORY_LABELS = {
  application_form: "申請附件",
  passport: "護照",
  transcript: "成績單",
  student_id: "學生證",
  financial_proof: "財力證明",
  recommendation: "推薦信",
  study_plan: "讀書計畫",
  other: "其他私人文件",
};

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

function applicationTemplateReviewed(template) {
  const selection = state.applicationSelections[template.id];
  const preview = state.applicationPreviews[template.id];
  return Boolean(
    selection?.reviewed_version === template.version
    && selection?.reviewed_content_sha256
    && preview?.review_content_sha256 === selection.reviewed_content_sha256
    && !(preview?.missing_required_fields || []).length
    && !(preview?.invalid_attachment_fields || []).length
  );
}

function applicationPrintSidesLabel(template) {
  return {
    single_sided: "單面列印",
    double_sided: "雙面列印",
    confirm_official: "待確認官方單雙面規定",
  }[template.print_sides] || "待確認官方單雙面規定";
}

function applicationAttachmentOrder(template) {
  const fileFields = (template.fields || []).filter((field) => field.field_type === "files");
  const byId = new Map(fileFields.map((field) => [field.id, field]));
  const orderedIds = template.attachment_field_order?.length
    ? template.attachment_field_order
    : fileFields.map((field) => field.id);
  return orderedIds.map((fieldId) => byId.get(fieldId)?.label).filter(Boolean);
}

function applicationAttachmentLabel(attachment) {
  const pages = attachment.page_count ? ` · ${attachment.page_count} 頁` : "";
  const placement = attachment.placement === "inside_document" ? " · 排入文件內" : " · 接在文件後";
  return `${attachment.order}. ${attachment.field_label}：${attachment.file_name}${pages}${placement}`;
}

function applicationPrintSummary(template) {
  return `${template.paper_size || "A4"} · ${applicationPrintSidesLabel(template)}`;
}

function invalidateApplicationReview(templateId, { persist = true, render = true } = {}) {
  const existing = state.applicationSelections[templateId];
  if (
    !existing?.reviewed_version
    && !existing?.reviewed_content_sha256
    && !existing?.reviewed_at
  ) return false;
  state.applicationSelections[templateId] = {
    ...existing,
    status: "draft",
    reviewed_version: null,
    reviewed_content_sha256: null,
    reviewed_at: null,
  };
  if (persist) persistApplicationContext();
  const template = applicationTemplateById(templateId);
  if (template && state.activeApplicationTemplateId === templateId) {
    const review = document.querySelector(`[data-application-review-template="${templateId}"]`);
    if (review) review.checked = false;
    const download = $("#download-single-application-document");
    if (download) download.disabled = true;
    const next = $("#application-document-next-step");
    if (next) next.textContent = applicationDocumentNextStep(template);
    const status = $("#application-document-form-status");
    if (status) status.textContent = "內容已變更，請重新核對。";
    const progress = $("#application-form-print-guide")?.querySelector(
      `[data-application-status-template="${templateId}"]`,
    );
    if (progress) progress.value = "draft";
  }
  if (render) {
    renderApplicationTemplates();
    renderApplicationPacket();
    updateApplicationCenterSteps();
  }
  return true;
}

function invalidateAllApplicationReviews() {
  let changed = false;
  Object.keys(state.applicationSelections).forEach((templateId) => {
    changed = invalidateApplicationReview(templateId, { persist: false, render: false }) || changed;
  });
  if (!changed) return;
  persistApplicationContext();
  renderApplicationTemplates();
  renderApplicationPacket();
  updateApplicationCenterSteps();
}

function applicationDocumentNextStep(template) {
  const status = applicationDocumentStatus(template.id);
  if (applicationTemplateCompletion(template).ready && !applicationTemplateReviewed(template)) {
    return "逐欄核對內容、份數、簽名、核章與送件單位。";
  }
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
  return state.homeSchool || state.account?.catalog_home_university || DEFAULT_HOME_SCHOOL;
}

// Every school's catalogue is public; an account only decides which one opens first.
function canAccessPartnerCatalog() {
  return true;
}

function accountNeedsSchool() {
  return Boolean(state.account && !state.account.is_platform_admin && !state.account.catalog_home_university);
}

function alignAccountSchool() {
  const accountSchool = !state.account?.is_platform_admin && state.account?.catalog_home_university;
  if (accountSchool) {
    const url = new URL(window.location.href);
    const sharedHome = url.searchParams.get("home");
    const school = state.supportedUniversities.some((item) => item.school_name === sharedHome)
      ? sharedHome : accountSchool;
    state.homeSchool = school;
    state.selectedHomeSchool = school;
    state.applicationContext.school_name = school;
    // A valid shared choice selects a public catalogue, not an account identity.
    // During boot the registry may still be loading; leave the incoming query
    // intact so boot can validate it after both account and registry resolve.
    if (!sharedHome) {
      url.searchParams.set("home", school);
      window.UniWayNavigation.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    }
  }
  updateSchoolContext();
  renderSchoolOptions();
}

function clearProtectedCatalog() {
  window.UniWayDocumentWorkbench?.reset();
  state.dashboard = null;
  state.applicationPeriodOptions = null;
  state.applicationPeriodRequestId += 1;
  renderApplicationPeriodOptions();
  state.coverage = null;
  state.destinationProfiles = [];
  state.applicationTemplates = [];
  state.activeWorkflow = null;
  state.advisorPlan = null;
  state.planningRecommendationKey = "";
  state.planningPreview = null;
  state.planningLoading = false;
  state.planningRequestId += 1;
  state.hasLoaded = false;
  state.partnerDataLoading = false;
  state.partnerDataError = false;
  state.experienceRequestId += 1;
  state.workflowRequestId += 1;
  state.destinationRequestId += 1;
  [state.experienceCache, state.workflowCache, state.destinationCache, state.completenessCache, state.lifeContextCache, state.communityCache].forEach((cache) => cache.clear());
  state.calendarWorkflowAttempts.clear();
  partnerMapGeneration += 1;
  partnerMapController?.destroy();
  partnerMapController = null;
  partnerMapLoadPromise = null;
  partnerMapLoadFailed = false;
  if (state.activeSchool) closeUniversityDetail({ updateHistory: false });
  state.activeSchool = null;
  ["#partner-table", "#partner-map-preview", "#school-detail-content", "#school-detail-photo",
    "#school-detail-summary", "#school-detail-primary-facts", "#period-list",
    "#scholarship-list", "#documents-list", "#application-template-list", "#advisor-result-content",
    "#selection-workspace", "#favorite-list", "#compare-panel", "#search-results"].forEach((selector) => $(selector)?.replaceChildren());
  syncPartnerView();
}

function renderCatalogAccessGate() {
  const section = $("#partners");
  if (!section) return;
  const locked = !canAccessPartnerCatalog();
  section.dataset.catalogLocked = String(locked);
  let gate = $("#partner-access-gate");
  if (!gate) {
    gate = document.createElement("div");
    gate.id = "partner-access-gate";
    gate.className = "empty-state";
    section.prepend(gate);
  }
  gate.hidden = !locked;
  if (!locked) return;
  gate.innerHTML = `<h2>${state.account ? "選擇學校後查看本校名單" : "登入後查看本校交換機會"}</h2><button type="button" class="primary-button" data-catalog-login>${state.account ? "選擇學校" : "登入"}</button>`;
  gate.querySelector("button").addEventListener("click", () => state.account ? openProfileDialog() : openAuthDialog("login"));
}

function isCurrentHomeSchool(schoolName) {
  return normalize(activeHomeSchool()) === normalize(schoolName);
}

function captureSchoolContext(homeSchool = activeHomeSchool()) {
  return { homeSchool, version: state.schoolContextVersion };
}

function schoolContextIsCurrent(context) {
  return context.version === state.schoolContextVersion && isCurrentHomeSchool(context.homeSchool);
}

function beginSchoolDataRequest(kind, homeSchool = activeHomeSchool()) {
  const id = (state.schoolDataRequestIds[kind] || 0) + 1;
  state.schoolDataRequestIds[kind] = id;
  return { ...captureSchoolContext(homeSchool), kind, id };
}

function schoolDataRequestIsCurrent(request) {
  return schoolContextIsCurrent(request) && state.schoolDataRequestIds[request.kind] === request.id;
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
  if (homeSelectionRules().academic_policy === "gpa_or_rank") return null;
  return state.dashboard?.academic_score_minimum == null ? null : Number(state.dashboard.academic_score_minimum);
}

function homeSelectionRules() {
  return state.dashboard?.selection_rules || {};
}

function homeAcademicPass(profile) {
  const rules = homeSelectionRules();
  if (rules.academic_policy === "gpa_or_rank") {
    if (rules.exclude_in_service && /在職/.test(profile.degree || "")) return false;
    if (rules.graduate_academic_exempt && /研究所|研究生|碩士|博士|碩一|博一/.test(profile.degree || "")) return true;
    return /大學部|學士|大二|大三|大四/.test(profile.degree || "") && (
      (profile.academicGpa != null && profile.academicGpa >= rules.undergraduate_gpa_minimum) ||
      (profile.classRankPercent > 0 && profile.classRankPercent <= rules.undergraduate_rank_maximum)
    );
  }
  if (Object.keys(rules.degree_score_minimums || {}).length) {
    const degree = profile.degree || "";
    const undergraduate = ["大學部","學士","學士班","大一","大二","大三","大四","大五","大六"].includes(degree);
    if (undergraduate && (rules.excluded_undergraduate_years || []).includes(profile.currentYear || degree)) return false;
    if (undergraduate && !profile.currentYear) return false;
    const minimum = rules.degree_score_minimums[degree];
    return minimum != null && profile.academicScore != null && profile.academicScore >= minimum;
  }
  const minimum = academicMinimum();
  return minimum != null && profile.academicScore != null && profile.academicScore >= minimum
    && (state.dashboard?.academic_gpa_minimum == null || (profile.academicGpa != null && profile.academicGpa >= state.dashboard.academic_gpa_minimum));
}

function renderAcademicFields() {
  const ntu = homeSelectionRules().academic_policy === "gpa_or_rank";
  const ncu = activeHomeSchool() === "國立中央大學";
  for (const [selector, values] of [["#advisor-degree", ["在職碩士班"]], ["#advisor-current-year", ["大五", "大六"]]]) {
    const select = $(selector);
    if (ncu) {
      for (const value of values) if (!Array.from(select.options).some(option => option.value === value)) {
        const option = new Option(value, value);
        option.dataset.ncuOption = "true";
        select.add(option);
      }
    } else select.querySelectorAll("[data-ncu-option]").forEach(option => option.remove());
  }
  $("#advisor-percent-field").hidden = ntu;
  $("#advisor-academic-score").disabled = ntu;
  document.querySelectorAll("[data-ntu-academic-field]").forEach((label) => {
    label.hidden = !ntu;
    label.querySelector("input").disabled = !ntu;
  });
  const ccu = state.dashboard?.academic_gpa_minimum != null;
  const gpa = $("#advisor-academic-gpa");
  $("#advisor-gpa-field").hidden = !(ntu || ccu);
  gpa.disabled = !(ntu || ccu);
  gpa.max = "4.3";
  gpa.placeholder = ccu ? "中正須至少 3.0" : "例如 2.44；與排名擇一";
  $("#advisor-gpa-label").textContent = ccu ? "歷年 GPA" : "適用學年GPA（4.3制）";
  $("#advisor-academic-rule").hidden = !state.dashboard?.academic_score_rule;
  if (state.dashboard?.academic_score_rule) $("#advisor-academic-rule").textContent = state.dashboard.academic_score_rule;
}

function homeCollegeOptions() {
  // Partner eligibility scopes include notes and departments, not a college directory.
  const colleges = activeUniversityProfile().colleges;
  return Array.isArray(colleges) ? colleges.filter((value) => typeof value === "string" && value.trim()) : [];
}

function homeCollegeValue(value) {
  return homeCollegeOptions().includes(value) ? value : "";
}

function departmentField(prefix) {
  return $(`#${prefix}-department-text`)?.hidden === false ? $(`#${prefix}-department-text`) : $(`#${prefix}-department`);
}

function renderDepartmentOptions(prefix, selected = "") {
  const college = $(`#${prefix}-college`)?.value || "";
  const select = $(`#${prefix}-department`);
  const input = $(`#${prefix}-department-text`);
  if (!select) return;
  const directory = window.UniWayAcademicUnits?.[activeHomeSchool()];
  // A student may enter the exact registered unit when a directory is unavailable.
  select.hidden = !directory;
  if (input) { input.hidden = Boolean(directory); input.disabled = Boolean(directory) || !college; }
  if (!directory) {
    select.disabled = true;
    if (input) input.value = selected;
    const note = $(`#${prefix}-department-note`);
    if (note) note.textContent = "請依學籍填寫系所或學位學程；可申請範圍仍須核對合作校規定。";
    const link = $(`#${prefix}-department-source`);
    if (link) link.hidden = true;
    return;
  }
  const options = directory?.colleges?.[college] || [];
  // Recognize saved shorthand only when it resolves to an entry in the directory.
  const canonical = options.find((option) => option === selected || option.replace(/學系$/, "系") === selected) || "";
  fillSelect(`#${prefix}-department`, options, college ? "請選擇系所／學位學程" : "請先選擇學院", canonical);
  select.disabled = !options.length;
  const note = $(`#${prefix}-department-note`);
  if (note) {
    note.textContent = !college ? "選擇學院後顯示所屬系所。" : options.length ? "依官方系所名單；沒有你的系所可查看來源。" : "此學院系所名單尚待確認，請查看官方來源。";
    const link = $(`#${prefix}-department-source`);
    if (link) {
      link.hidden = !directory;
      link.href = directory?.sourceUrl || "#";
    }
  }
}

function languageThreshold(test) {
  const minimum = state.dashboard?.language_score_minimums?.[test];
  if (Number.isFinite(Number(minimum))) {
    return { label: LANGUAGE_THRESHOLDS[test]?.label || test.toUpperCase(), minimum: Number(minimum) };
  }
  if (state.dashboard) return null;
  return LANGUAGE_THRESHOLDS[test] || null;
}

function selectionLanguageLabel(test, score) {
  const threshold = languageThreshold(test);
  if (threshold) return `${threshold.label} ${score ?? "待補"}`;
  if (activeHomeSchool() === "國立中央大學" && test) {
    const label = LANGUAGE_THRESHOLDS[test]?.label || test.toUpperCase();
    return `${label} ${score ?? "待補"}`;
  }
  return "語言能力待確認";
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

function formatDateOnly(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function initIcons() {
  if (window.lucide) {
    // Replacing a rendered SVG between pointerdown and pointerup discards the
    // click. Background form/catalogue renders must preserve existing targets.
    let pending = false;
    document.querySelectorAll("[data-lucide]").forEach((element) => {
      const name = element.getAttribute("data-lucide");
      if (element.tagName.toLowerCase() === "svg" && element.classList.contains(`lucide-${name}`)) return;
      element.setAttribute("data-lucide-pending", name);
      pending = true;
    });
    if (!pending) return;
    try {
      window.lucide.createIcons({ nameAttr: "data-lucide-pending", attrs: { "aria-hidden": "true" } });
    } finally {
      document.querySelectorAll("[data-lucide-pending]").forEach((element) => element.removeAttribute("data-lucide-pending"));
    }
  }
}

// The saved choice is "light", "dark" or "system". "system" follows the device (prefers-color-scheme) and keeps following it
// when it changes; state.theme and data-theme always hold the colours actually shown ("light" or "dark").
const systemThemeQuery = typeof window.matchMedia === "function" ? window.matchMedia("(prefers-color-scheme: dark)") : null;

function resolveTheme(preference) {
  if (preference === "light" || preference === "dark") return preference;
  return systemThemeQuery?.matches ? "dark" : "light";
}

function applyTheme(preference, { persist = true } = {}) {
  const choice = ["light", "dark", "system"].includes(preference) ? preference : "dark";
  const nextTheme = resolveTheme(choice);
  state.themePreference = choice;
  state.theme = nextTheme;
  document.documentElement.dataset.theme = nextTheme;
  document.documentElement.dataset.themePreference = choice;
  document.documentElement.style.colorScheme = nextTheme;
  const meta = $("#theme-color");
  if (meta) meta.setAttribute("content", nextTheme === "dark" ? "#080a0d" : "#f5f5f7");
  const button = $("#theme-toggle");
  if (button) {
    const target = nextTheme === "dark" ? "淺色" : "深色";
    button.setAttribute("aria-label", `切換為${target}模式`);
    button.dataset.tooltip = `${target}模式`;
    button.innerHTML = `<i data-lucide="${nextTheme === "dark" ? "sun" : "moon"}" aria-hidden="true"></i><span class="rail-action-label">${target}模式</span>`;
  }
  if (persist) {
    try {
      window.localStorage.setItem("exchange-guide-theme", choice);
    } catch (_) {
      // Theme still works when storage is unavailable.
    }
  }
  window.UniWayProfile?.refreshTheme();
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
  systemThemeQuery?.addEventListener?.("change", () => {
    if (state.themePreference === "system") applyTheme("system", { persist: false });
  });
}

function parseStoredJson(storage, key, fallback) {
  try {
    const raw = storage.getItem(key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch (_) {
    return fallback;
  }
}

function storedRecord(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function clearStoredAuthenticatedState({ preserveWorkflowIssueReportPending = false } = {}) {
  if (!preserveWorkflowIssueReportPending) state.workflowIssueReportPending = null;
  try {
    [
      STORAGE_KEYS.authToken,
      STORAGE_KEYS.favorites,
      STORAGE_KEYS.applications,
      STORAGE_KEYS.progress,
      STORAGE_KEYS.documents,
      STORAGE_KEYS.eligibility,
      STORAGE_KEYS.communityIdentity,
      STORAGE_KEYS.calendarEvents,
      STORAGE_KEYS.planningAvailability,
      STORAGE_KEYS.preparationTasks,
      STORAGE_KEYS.budgetPlans,
      STORAGE_KEYS.applicationContext,
      STORAGE_KEYS.applicationSelections,
      STORAGE_KEYS.submissionProgress,
      STORAGE_KEYS.workspaceSync,
      STORAGE_KEYS.applicationProfileMemory,
      STORAGE_KEYS.applicationProfileMemoryEnabled,
      STORAGE_KEYS.updateSeenAt,
    ].forEach((key) => window.localStorage.removeItem(key));
    Object.entries(APPLICATION_SESSION_KEYS).forEach(([name, key]) => {
      if (name === "workflowIssueReportPending" && preserveWorkflowIssueReportPending) return;
      window.sessionStorage.removeItem(key);
    });
  } catch (_) {
    // In-memory isolation remains active when browser storage is unavailable.
  }
}

function readStoredAuthenticatedState(accountId) {
  const expectedAccountId = String(accountId || "");
  const quarantinedAccountId = String(state.quarantinedAccountOwnerId || "");
  const workspaceSync = storedRecord(
    parseStoredJson(window.localStorage, STORAGE_KEYS.workspaceSync, {}),
  );
  const storedAccountId = String(workspaceSync.account_id || "");
  state.quarantinedAccountOwnerId = "";
  if (
    !expectedAccountId
    || !quarantinedAccountId
    || quarantinedAccountId !== expectedAccountId
    || storedAccountId !== quarantinedAccountId
  ) {
    clearStoredAuthenticatedState({
      preserveWorkflowIssueReportPending: Boolean(
        expectedAccountId && readWorkflowIssueReportPending(),
      ),
    });
    return false;
  }

  const favorites = parseStoredJson(window.localStorage, STORAGE_KEYS.favorites, []);
  const applications = parseStoredJson(window.localStorage, STORAGE_KEYS.applications, []);
  state.favorites = new Set(Array.isArray(favorites) ? favorites : []);
  state.applications = new Set(Array.isArray(applications) ? applications : []);
  const communityIdentity = storedRecord(
    parseStoredJson(window.localStorage, STORAGE_KEYS.communityIdentity, {}),
  );
  state.anonymousIdentity = communityIdentity.id ? communityIdentity : null;
  state.applicationProgress = storedRecord(
    parseStoredJson(window.localStorage, STORAGE_KEYS.progress, {}),
  );
  state.documentReadiness = storedRecord(
    parseStoredJson(window.localStorage, STORAGE_KEYS.documents, {}),
  );
  const storedContext = storedRecord(parseStoredJson(window.localStorage, STORAGE_KEYS.applicationContext, {}));
  const eligibility = normalize(storedContext.school_name) === normalize(activeHomeSchool())
    ? parseStoredJson(window.localStorage, STORAGE_KEYS.eligibility, null) : null;
  state.eligibilityProfile = storedRecord(eligibility);
  if (!Object.keys(state.eligibilityProfile).length) state.eligibilityProfile = null;
  const calendarEvents = parseStoredJson(window.localStorage, STORAGE_KEYS.calendarEvents, []);
  state.planningAvailability = window.UniWayJourney.sanitizeAvailability(parseStoredJson(window.localStorage, STORAGE_KEYS.planningAvailability, null));
  state.preparationTasks = window.UniWayMultiPlan.sanitizeSettings(parseStoredJson(window.localStorage, STORAGE_KEYS.preparationTasks, {}));
  state.calendarEvents = (Array.isArray(calendarEvents) ? calendarEvents : []).map((event) => ({
    ...event,
    preparationDays: Math.min(90, Math.max(0, Number(event.preparationDays ?? event.preparation_days) || 0)),
    status: ["todo", "preparing", "ready"].includes(event.status) ? event.status : "todo",
    generatedFromEventId: event.generatedFromEventId || event.generated_from_event_id || "",
  }));
  state.budgetPlans = storedRecord(
    parseStoredJson(window.localStorage, STORAGE_KEYS.budgetPlans, {}),
  );
  state.applicationContext = {
    ...state.applicationContext,
    ...storedContext,
    school_name: activeHomeSchool(),
  };
  state.applicationSelections = storedRecord(
    parseStoredJson(window.localStorage, STORAGE_KEYS.applicationSelections, {}),
  );
  state.submissionProgress = storedRecord(
    parseStoredJson(window.localStorage, STORAGE_KEYS.submissionProgress, {}),
  );
  state.accountWorkspaceRevisions = storedRecord(workspaceSync.revisions);
  state.accountWorkspaceBases = storedRecord(workspaceSync.bases);
  state.accountWorkspacePending = storedRecord(workspaceSync.pending);
  state.accountWorkspaceSyncAccountId = storedAccountId;
  state.applicationProfileMemoryEnabled = window.localStorage.getItem(
    STORAGE_KEYS.applicationProfileMemoryEnabled,
  ) === "true";
  const rememberedApplicationProfile = state.applicationProfileMemoryEnabled
    ? storedRecord(parseStoredJson(window.localStorage, STORAGE_KEYS.applicationProfileMemory, {}))
    : {};
  const sessionApplicationProfile = storedRecord(
    parseStoredJson(window.sessionStorage, APPLICATION_SESSION_KEYS.profile, {}),
  );
  state.applicationProfile = {
    ...sanitizeApplicationProfileForMemory(rememberedApplicationProfile),
    ...sessionApplicationProfile,
  };
  state.applicationAnswers = storedRecord(
    parseStoredJson(window.sessionStorage, APPLICATION_SESSION_KEYS.answers, {}),
  );
  state.updateSeenAt = window.localStorage.getItem(STORAGE_KEYS.updateSeenAt) || "";
  stripReusableApplicationAnswers();
  return true;
}

function readStoredState() {
  try {
    state.homeSchool = window.localStorage.getItem(STORAGE_KEYS.homeSchool) || "";
    state.selectedHomeSchool = state.homeSchool || DEFAULT_HOME_SCHOOL;
    state.anonymousIdentity = null;
    const workspaceSync = storedRecord(
      parseStoredJson(window.localStorage, STORAGE_KEYS.workspaceSync, {}),
    );
    state.quarantinedAccountOwnerId = String(workspaceSync.account_id || "");
    window.localStorage.removeItem(STORAGE_KEYS.authToken);
  } catch (_) {
    state.homeSchool = "";
    state.selectedHomeSchool = DEFAULT_HOME_SCHOOL;
    state.anonymousIdentity = null;
    state.quarantinedAccountOwnerId = "";
  }
  state.authRestoreState = "pending";
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
        partner_count: 75,
        coverage_note: "完整支援試點：已整理長庚大學交換、補助、文件與合作校申請流程。",
      },
      {
        id: "ntpu",
        school_name: "國立臺北大學",
        short_name: "北大",
        english_name: "National Taipei University",
        hero_image: "/static/assets/ntpu-campus.jpg",
        official_url: "https://new.ntpu.edu.tw/oia",
        supported: true,
        partner_count: 206,
        coverage_note: "116學年度三語組官方名額表：169項開放，37項合作校備查。",
      },
      {
        id: "ntu", school_name: "國立臺灣大學", short_name: "臺大",
        aliases: ["台大", "台灣大學", "國立台灣大學"],
        english_name: "National Taiwan University", hero_image: "/static/assets/ntu-campus.svg",
        official_url: "https://studyabroad.ntu.edu.tw/", supported: true,
        partner_count: 288, coverage_note: "116-1校級甄選、文件與補助；282項名額待公布，6項零名額。",
      },
      {id:"ncu",school_name:"國立中央大學",short_name:"中央",english_name:"National Central University",hero_image:"/static/assets/ncu-campus.svg",official_url:"https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw",supported:true,partner_count:214,coverage_note:"116-1簡章已公告，名額預定2026/10/12公告；214項115目錄僅供參考。"},
    ];
  }
  renderSchoolOptions();
  updateSchoolContext();
}

async function loadCoverage({ homeSchool = activeHomeSchool() } = {}) {
  if (!canAccessPartnerCatalog()) return false;
  const requestedSchool = homeSchool;
  const request = beginSchoolDataRequest("coverage", requestedSchool);
  let coverage = null;
  try {
    coverage = await fetchJson(`/coverage?school=${encodeURIComponent(requestedSchool)}`);
  } catch (_) {
    if (!schoolDataRequestIsCurrent(request)) return false;
  }
  if (!schoolDataRequestIsCurrent(request)) return false;
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

async function loadDestinationProfiles({ homeSchool = activeHomeSchool() } = {}) {
  if (!canAccessPartnerCatalog()) return false;
  const requestedSchool = homeSchool;
  const request = beginSchoolDataRequest("destinations", requestedSchool);
  let profiles = [];
  try {
    profiles = await fetchJson(
      `/destination-profiles?home_school=${encodeURIComponent(requestedSchool)}&compact=true`
    );
  } catch (_) {
    if (!schoolDataRequestIsCurrent(request)) return false;
  }
  if (!schoolDataRequestIsCurrent(request)) return false;
  state.destinationProfiles = profiles;
  if (state.dashboard) {
    renderPartnerTable();
    renderSearchResults();
    renderRecommendedMatches();
    renderBudgetPlanner();
  }
  return true;
}

async function loadSchoolImages() {
  try {
    const payload = await fetchJson("/static/assets/school-images.json?v=20261011-integration-1");
    state.schoolImages = Array.isArray(payload?.schools)
      ? payload.schools.filter((item) => item && item.school_name)
      : [];
  } catch (_) {
    state.schoolImages = [];
  }
  try {
    const payload = await fetchJson("/static/assets/ncu-school-images.json?v=20261011-ncu-campus-2");
    state.ncuSchoolImages = Array.isArray(payload?.schools)
      ? payload.schools.filter((item) => item.status === "verified" && item.local_path)
      : [];
  } catch (_) {
    state.ncuSchoolImages = [];
  }
}

function visualSchoolIdentity(value, loose = false) {
  let name = String(value ?? "").normalize("NFKC").replace(/\s+/g, " ").trim();
  name = name.replace(/\s*黑龍江省哈爾\s*濱市\s*$/, "").trim();
  name = name.replace(/\s*\([^()]*(?:交換學生計畫|訪問學生計畫)[^()]*\)\s*$/, "").trim();
  const english = name.search(/[A-Za-z]/);
  name = (english < 0 ? name : name.slice(english)).replace(/^[ ()（）\[\]【】,，;；]+|[ ()（）\[\]【】,，;；]+$/g, "").toLowerCase().replace(/ß/g, "ss").replace(/ς/g, "σ");
  return loose ? name.normalize("NFKD").replace(/\p{M}/gu, "").replace(/[^\p{L}\p{N}]/gu, "") : name;
}

function visualCountryIdentity(value) {
  const country = String(value || "").trim();
  return ({ "南韓": "韓國", "台灣": "臺灣", "中國": "中國大陸", "大陸地區": "中國大陸" })[country] || country;
}

function visualSchoolAliases(value) {
  const aliases = [visualSchoolIdentity(value, true)];
  let name = String(value ?? "").normalize("NFKC").replace(/\s+/g, " ").trim();
  name = name.replace(/\s*\([^()]*(?:交換學生計畫|訪問學生計畫)[^()]*\)\s*$/, "").trim();
  const english = name.search(/[A-Za-z]/);
  const scoped = /校區|分校|研究所|研究科|學部|大學.*學院|大学.*学院|\bcampus\b|\bfaculty\b|\bdepartment\b|\bschool of\b|\bcollege of\b/i.test(name);
  const trim = (s) => s.replace(/^[ ()（）\[\]【】,，;；]+|[ ()（）\[\]【】,，;；]+$/g, "");
  const institution = /^[\u3400-\u9fff ]{2,}(?:大學|大学|學院|学院|技術院|技术院)$/;
  if (english >= 0 && !scoped) {
    const prefix = trim(name.slice(0, english)), suffix = name.slice(english);
    const chinese = suffix.search(/[\u3400-\u9fff]/);
    if (chinese >= 0 && institution.test(trim(suffix.slice(chinese)))) {
      aliases.push(visualSchoolIdentity(suffix.slice(0, chinese), true), visualSchoolIdentity(trim(suffix.slice(chinese)), true));
    }
    if (institution.test(prefix)) aliases.push(visualSchoolIdentity(prefix, true));
  }
  return [...new Set(aliases.filter(Boolean))];
}

let schoolVisualSource = null, schoolVisualExact = new Map(), schoolVisualAliases = new Map();
function schoolVisualRecordFor(schoolName, country = null) {
  const home = state.dashboard?.school_name;
  if (home === "國立中央大學") {
    return state.ncuSchoolImages.find(row => visualSchoolIdentity(row.school_name) === visualSchoolIdentity(schoolName)
      && visualCountryIdentity(row.country) === visualCountryIdentity(country)) || { status: "license_unverified" };
  }
  if (home === "淡江大學") {
    const partner = state.dashboard.partner_universities.find(row => visualSchoolIdentity(row.school_name) === visualSchoolIdentity(schoolName)
      && visualCountryIdentity(row.country) === visualCountryIdentity(country));
    const evidence = partner?.reference_data;
    return partner?.image_status === "verified" && partner.image_url && evidence?.campus_photo_author
      ? { status: "verified", local_path: partner.image_url, official_page_url: partner.image_page_url,
          license_name: evidence.campus_photo_license, license_url: evidence.campus_photo_license_url,
          note: `攝影：${evidence.campus_photo_author} · ${evidence.campus_photo_license}` }
      : { status: "missing" };
  }
  if (home === "國立中正大學") {
    const partner = state.dashboard.partner_universities.find(row => visualSchoolIdentity(row.school_name) === visualSchoolIdentity(schoolName)
      && visualCountryIdentity(row.country) === visualCountryIdentity(country));
    if (partner?.reference_data?.ccu_completion) {
      let photo;
      try { photo = JSON.parse(partner.reference_data.ccu_campus_assets || "{}").photo; } catch (_) { /* Attribution stays absent. */ }
      return photo && partner.image_status === "verified" ? { status: "verified", local_path: partner.image_url,
        license_name: photo.license_name, license_url: photo.license_url,
        note: `攝影：${photo.artist} · ${photo.license_name} · ${photo.campus_caption}` } : { status: "missing" };
    }
  }
  if (schoolVisualSource !== state.schoolImages) {
    schoolVisualSource = state.schoolImages;
    schoolVisualExact = new Map(); schoolVisualAliases = new Map();
    for (const row of state.schoolImages) schoolVisualExact.set(JSON.stringify([visualSchoolIdentity(row.school_name), row.country || ""]), row);
    for (const row of schoolVisualExact.values()) {
      for (const name of visualSchoolAliases(row.school_name)) {
        const key = JSON.stringify([name, visualCountryIdentity(row.country)]);
        if (!schoolVisualAliases.has(key)) schoolVisualAliases.set(key, new Set());
        schoolVisualAliases.get(key).add(row);
      }
    }
  }
  const exact = schoolVisualExact.get(JSON.stringify([visualSchoolIdentity(schoolName), country || ""]));
  if (exact) return exact; // Preserve explicit needs_review/missing decisions.
  for (const name of visualSchoolAliases(schoolName)) {
    const matches = schoolVisualAliases.get(JSON.stringify([name, visualCountryIdentity(country)]));
    if (matches?.size) return matches.size === 1 ? [...matches][0] : null;
  }
  return null;
}

function schoolImageFor(schoolName, country = null) {
  const visual = schoolVisualRecordFor(schoolName, country);
  return visual?.status === "verified" && visual.local_path ? visual : null;
}

function renderSchoolPhoto(item, variant = "card") {
  const record = schoolVisualRecordFor(item.school_name, item.country);
  const visual = schoolImageFor(item.school_name, item.country)
    || (!record && item.image_status === "verified" && item.image_url ? { local_path: item.image_url } : null);
  const status = record?.status || item.image_status;
  const label = visual ? "照片暫時無法載入" : status === "needs_review" ? "照片待核對" : status === "error" ? "照片擷取失敗" : "照片待補";
  const fallback = `
    <span class="school-photo-fallback" ${visual ? 'aria-hidden="true"' : 'role="img"'} aria-label="${escapeHtml(item.school_name)}：${escapeHtml(label)}">
      <i data-lucide="school"></i><span>${escapeHtml(label)}</span>
    </span>`;
  const loading = variant === "detail" ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"';
  const image = visual?.local_path
    ? `<img src="${escapeHtml(visual.local_path)}" alt="${escapeHtml(item.school_name)}校園照片" ${loading} decoding="async" data-remove-on-error="true" />`
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
    image = '<span class="coverage-chip ready">校園照片已核對</span>';
  } else if (coverage.image_status === "missing") {
    image = '<span class="coverage-chip empty">校園照片待補</span>';
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

// The mark in front of each school's name. Official emblems go in SCHOOL_EMBLEM_FILES, {school name: image path}, once the
// school has agreed to their use; until then a two-character mark in the school's own tint stands in.
const SCHOOL_BADGES = {
  "長庚大學": { text: "長庚", tint: 172 },
  "國立臺北大學": { text: "北大", tint: 215 },
  "國立臺灣大學": { text: "臺大", tint: 140 },
  "國立中正大學": { text: "中正", tint: 8 },
  "國立中央大學": { text: "中央", tint: 235 },
  "淡江大學": { text: "淡江", tint: 35 },
};
const SCHOOL_EMBLEM_FILES = {};

function schoolBadge(item) {
  const preset = SCHOOL_BADGES[item.school_name];
  const text = preset?.text || String(item.short_name || item.school_name || "").replace(/^國立/, "").slice(0, 2);
  const emblem = SCHOOL_EMBLEM_FILES[item.school_name];
  const inner = emblem ? `<img src="${escapeHtml(emblem)}" alt="" decoding="async" />` : escapeHtml(text);
  return { tint: preset?.tint ?? 200, text, html: `<span class="school-emblem" aria-hidden="true">${inner}</span>` };
}

function renderSchoolOptions(query = "") {
  if (window.UniWaySchoolPicker) {
    window.UniWaySchoolPicker.update({
      schools: state.supportedUniversities.map(item => {
        const badge = schoolBadge(item);
        return { ...item, badgeText: badge.text, badgeTint: badge.tint };
      }),
      selectedSchool: state.selectedHomeSchool,
      normalize,
    });
    return;
  }
  const container = $("#school-options");
  if (!container) return;
  const normalizedQuery = normalize(query);
  const universities = state.supportedUniversities.filter((item) => {
    const text = normalize([item.school_name, item.short_name, item.english_name, ...(item.aliases || [])].filter(Boolean).join(" "));
    return !normalizedQuery || text.includes(normalizedQuery);
  });
  $("#school-search-empty").hidden = universities.length > 0;
  container.innerHTML = universities
    .map((item) => {
      const badge = schoolBadge(item);
      const isSelected = item.school_name === state.selectedHomeSchool;
      return `
        <button type="button" class="school-option${isSelected ? " selected" : ""}" data-home-school="${escapeHtml(item.school_name)}" role="option" aria-selected="${isSelected}" style="--school-tint:${badge.tint}">
          ${badge.html}
          <span class="school-option-name">${escapeHtml(item.school_name)}</span>
          <span class="school-option-status">${item.partner_count ? `${item.partner_count} 間合作校` : "資料建置中"}</span>
          <i class="school-option-go" data-lucide="arrow-right" aria-hidden="true"></i>
        </button>`;
    })
    .join("");
  initIcons();
}

function openSchoolOnboarding() {
  renderSchoolOptions();
  const onboarding = $("#school-onboarding");
  const activeElement = document.activeElement;
  state.onboardingReturnFocus = activeElement instanceof HTMLElement && activeElement !== document.body
    ? activeElement
    : null;
  onboarding.hidden = false;
  $("#school-switcher")?.setAttribute("aria-expanded", "true");
  document.body.classList.add("onboarding-open");
  if (window.UniWaySchoolPicker) {
    window.UniWaySchoolPicker.open({
      accountChoice: Boolean(state.account && state.chooseSchoolForAccount),
      onChoose: chooseHomeSchool,
      onDismiss: dismissSchoolOnboarding,
    });
    return;
  }
  $("#onboarding-lock-note").hidden = !(state.account && state.chooseSchoolForAccount);
  window.setTimeout(() => $("#school-search")?.focus(), 40);
}

// A Google account whose address does not name a school picks one right after signing in.
function promptForAccountSchool() {
  if (!accountNeedsSchool()) return;
  state.chooseSchoolForAccount = true;
  if (state.homeSchool) state.selectedHomeSchool = state.homeSchool;
  openSchoolOnboarding();
}

async function saveAccountSchool(school) {
  state.chooseSchoolForAccount = false;
  if (!state.account) return;
  const requestController = new AbortController();
  const requestTimeout = window.setTimeout(() => requestController.abort(), 20_000);
  try {
    state.account = await fetchJson("/auth/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ home_university: school }),
      signal: requestController.signal,
    });
    renderAccountState();
    window.UniWayAnalytics?.track("school_choose", { school: state.account.catalog_home_university || "other", via: "signup" });
  } catch (_) {
    announce(requestController.signal.aborted
      ? "學校資料保存逾時，請重新整理確認是否已保存；目前先顯示這所學校的公開資料。"
      : "學校暫時無法存到帳號，下次登入時可以再選一次。", "info", true);
  } finally {
    window.clearTimeout(requestTimeout);
  }
}

function closeSchoolOnboarding() {
  window.UniWaySchoolPicker?.close();
  $("#school-onboarding").hidden = true;
  $("#school-switcher")?.setAttribute("aria-expanded", "false");
  document.body.classList.remove("onboarding-open");
  const returnFocus = state.onboardingReturnFocus;
  state.onboardingReturnFocus = null;
  if (returnFocus?.isConnected) window.setTimeout(() => returnFocus.focus(), 0);
}

function dismissSchoolOnboarding() {
  if (state.choosingSchool) return;
  state.chooseSchoolForAccount = false;
  state.pendingPersonalizedHash = "";
  if (state.homeSchool) closeSchoolOnboarding();
  else browseWithoutSchoolSelection();
}

async function chooseHomeSchool(school) {
  if (state.choosingSchool || !state.supportedUniversities.some(item => item.school_name === school)) return;
  state.choosingSchool = true;
  state.selectedHomeSchool = school;
  window.UniWaySchoolPicker?.setBusy(true);
  try {
    if (state.chooseSchoolForAccount) await saveAccountSchool(school);
    setHomeSchool(school);
  } finally {
    state.choosingSchool = false;
    window.UniWaySchoolPicker?.setBusy(false);
  }
}

function browseWithoutSchoolSelection() {
  state.chooseSchoolForAccount = false;
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
  state.pendingPersonalizedHash = "";
  if (state.hasLoaded && normalize(previousSchool) !== normalize(DEFAULT_HOME_SCHOOL)) {
    refreshHomeUniversityData();
  }
}

function handleOnboardingKeydown(event) {
  if (window.UniWaySchoolPicker) return;
  const onboarding = $("#school-onboarding");
  if (onboarding.hidden) return;
  if (event.key === "Escape") {
    event.preventDefault();
    dismissSchoolOnboarding();
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
  const previousSchool = activeHomeSchool();
  const changed = normalize(activeHomeSchool()) !== normalize(nextSchool);
  const dashboardMismatch = Boolean(state.dashboard?.school_name)
    && normalize(state.dashboard.school_name) !== normalize(nextSchool);
  const needsRefresh = changed || dashboardMismatch;
  if (needsRefresh && (state.activeSchool || !$("#school-detail-view")?.hidden)) {
    closeUniversityDetail({ updateHistory: false });
  }
  if (changed) {
    state.schoolContextVersion += 1;
    state.pendingBudgetDraft = null;
    window.UniWayAnalytics?.track("home_school_change", { from: previousSchool, to: nextSchool });
  }
  if (changed && state.account) {
    const previousWorkspace = accountWorkspacePayload(previousSchool);
    saveAccountWorkspace({ homeSchool: previousSchool, payload: previousWorkspace });
    const nextKey = accountWorkspaceKey(nextSchool);
    applyAccountWorkspace(state.accountWorkspacePending[nextKey]
      || state.accountWorkspaceBases[nextKey]
      || emptyAccountWorkspace(nextSchool));
  }
  state.homeSchool = nextSchool;
  state.selectedHomeSchool = nextSchool;
  state.applicationContext.school_name = nextSchool;
  // A shared catalogue URL must follow an explicit school choice. Otherwise
  // the next hash navigation re-applies the previous ?home= school.
  const sharedUrl = new URL(window.location.href);
  if (sharedUrl.searchParams.has("home") && sharedUrl.searchParams.get("home") !== nextSchool) {
    sharedUrl.searchParams.set("home", nextSchool);
    window.UniWayNavigation.replaceState({}, "", sharedUrl.href);
    partnerUrlSearch = window.location.search;
  }
  if (needsRefresh) {
    // Invalidate even an A → B → A response before the next school load starts.
    state.applicationTemplateRequestId += 1;
    state.applicationTemplates = [];
    state.applicationDocumentCatalog = null;
    state.applicationDocumentCatalogError = "";
    state.applicationDocumentCatalogContextKey = "";
    state.applicationLoading = false;
    state.applicationContext.target_school = "";
    state.applicationContext.target_country = "";
    state.coverage = null;
    state.destinationProfiles = [];
    state.applicationTemplates = [];
    state.applicationDocumentCatalog = null;
    state.applicationDocumentCatalogError = "";
    state.activeApplicationTemplateId = "";
    state.activeWorkflow = null;
    state.advisorPlan = null;
    state.planningRecommendationKey = "";
    state.planningPreview = null;
    state.planningLoading = false;
    state.planningRequestId += 1;
    setAdvisorAssistantState("idle");
    $("#advisor-result-content")?.replaceChildren();
    state.activeSchool = null;
    state.experienceCache.clear();
    state.workflowCache.clear();
    state.destinationCache.clear();
    state.completenessCache.clear();
    state.communityCache.clear();
  }
  if (needsRefresh && window.location.hash.startsWith("#school=")) {
    window.UniWayNavigation.replaceState({}, "", "#partners");
  }
  if (needsRefresh && window.location.hash.startsWith("#application-form=")) {
    window.UniWayNavigation.replaceState({}, "", "#application-center");
    applyAppRoute({ loadFeed: false, resetScroll: false });
  }
  try {
    window.localStorage.setItem(STORAGE_KEYS.homeSchool, nextSchool);
  } catch (_) {
    // The selected school still applies for this session.
  }
  // A school switch is a load, not an instruction to overwrite its remote workspace.
  persistApplicationContext({ sync: !changed });
  updateSchoolContext();
  closeSchoolOnboarding();
  const pendingPersonalizedHash = state.pendingPersonalizedHash || "";
  state.pendingPersonalizedHash = "";
  if (pendingPersonalizedHash && window.location.hash !== pendingPersonalizedHash) {
    window.location.hash = pendingPersonalizedHash;
  }
  if (needsRefresh && reload) refreshHomeUniversityData();
}

function updateSchoolContext() {
  renderAcademicFields();
  const selected = state.homeSchool || "";
  document.body.dataset.schoolSelected = selected ? "true" : "false";
  const profile = activeUniversityProfile();
  const contextSchool = profile.school_name;
  const shortName = profile.short_name || contextSchool.replace(/大學$/, "");
  const label = $("#school-switcher-label");
  const switcher = $("#school-switcher");
  if (switcher) switcher.disabled = false;
  if (label) label.textContent = selected || "選擇就讀學校";
  const mobileLabel = $("#mobile-school-label");
  if (mobileLabel) mobileLabel.textContent = selected || `${shortName}資料預覽`;
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
  const featuredDescription = $("#featured-home-school-description");
  if (featuredDescription) featuredDescription.textContent = `${shortName}學生的交換申請資訊與討論。`;
  document.querySelectorAll(".university-sidebar-nav, .university-mobile-nav").forEach((item) => {
    item.setAttribute("aria-label", `${contextSchool}板功能導覽`);
  });
  populateGlobalCommunitySchools();
  renderBoardFollowControls();
  window.UniWayHome?.render();
}

async function refreshHomeUniversityData() {
  if (!canAccessPartnerCatalog()) { renderCatalogAccessGate(); return; }
  const requestedSchool = activeHomeSchool();
  const requestId = ++state.homeSchoolRequestId;
  state.homeSchoolLoading = true;
  startPageLoading("school-switch", `正在切換至${requestedSchool}的資料`);
  try {
    await Promise.all([
      loadDashboard({ homeSchool: requestedSchool }),
      loadApplicationTemplates({ homeSchool: requestedSchool }),
      loadCoverage({ homeSchool: requestedSchool }),
      loadDestinationProfiles({ homeSchool: requestedSchool }),
    ]);
    if (requestId !== state.homeSchoolRequestId || !isCurrentHomeSchool(requestedSchool)) return;
    if (state.account) {
      await loadAccountWorkspace({ homeSchool: requestedSchool });
    }
    if (requestId !== state.homeSchoolRequestId || !isCurrentHomeSchool(requestedSchool)) return;
    applyAppRoute({ loadFeed: false, resetScroll: false });
    if (document.body.classList.contains("cgu-community-mode")) await loadGlobalCommunity();
    announce(`${activeHomeSchool()}資料已切換`, "success");
  } finally {
    if (requestId === state.homeSchoolRequestId) state.homeSchoolLoading = false;
    stopPageLoading("school-switch");
  }
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
  const requestContext = captureAuthenticatedRequestContext();
  const requestHadAccount = Boolean(requestContext.accountId);
  let response;
  try {
    response = await fetch(url, {
      ...options,
      cache: options.cache || "no-store",
      credentials: "same-origin",
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
  } catch (error) {
    assertAuthenticatedRequestCurrent(requestContext);
    throw error;
  }
  const data = response.status === 204 ? null : await response.json().catch(() => ({}));
  assertAuthenticatedRequestCurrent(requestContext);
  if (!response.ok) {
    const sessionExpired = response.status === 401
      && requestHadAccount
      && Boolean(state.account)
      && url !== "/auth/logout";
    if (sessionExpired) handleExpiredAccountSession();
    const detail = data?.detail;
    const message = sessionExpired
      ? "登入已過期，請重新登入。"
      : typeof detail === "string"
      ? detail
      : detail?.message || `伺服器回應 ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.payload = data;
    error.sessionExpired = sessionExpired;
    throw error;
  }
  const localized = window.UniWayChinese ? await window.UniWayChinese.localize(url, data) : data;
  assertAuthenticatedRequestCurrent(requestContext);
  return localized;
}

function captureAuthenticatedRequestContext() {
  return {
    accountId: String(state.account?.id || ""),
    epoch: state.authSessionEpoch,
  };
}

function authenticatedRequestContextIsCurrent(context) {
  if (!context?.accountId) return !state.account;
  return context.epoch === state.authSessionEpoch
    && context.accountId === String(state.account?.id || "");
}

function assertAuthenticatedRequestCurrent(context) {
  if (!context?.accountId) return;
  if (authenticatedRequestContextIsCurrent(context)) return;
  const error = new Error("登入狀態已變更，已忽略先前的請求。");
  error.staleSession = true;
  throw error;
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
    if (!provider.enabled) button.title = provider.provider === "apple" ? "行動版啟用" : "設定平台金鑰後啟用";
  });
  updateAuthProviderAvailability();
}

function updateAuthProviderAvailability() {
  document.querySelectorAll("[data-oauth-provider]").forEach((button) => {
    const enabled = button.dataset.providerEnabled === "true";
    button.disabled = !enabled;
    if (enabled) button.removeAttribute("title");
  });
  const emailEnabled = authEmailEnabled();
  // With Google as the one sign-in method nothing else is offered, so no dead buttons or forms.
  document.querySelectorAll("[data-oauth-provider]").forEach((button) => {
    const enabled = button.dataset.providerEnabled === "true";
    button.hidden = !emailEnabled && !enabled && button.dataset.oauthProvider !== "google";
  });
  document.querySelector(".auth-mode-switch")?.toggleAttribute("hidden", !emailEnabled);
  document.querySelector("#auth-dialog .auth-divider")?.toggleAttribute("hidden", !emailEnabled);
  $("#login-form").hidden = !emailEnabled || state.authMode !== "login";
  $("#register-form").hidden = !emailEnabled || state.authMode !== "register";
}

function authEmailEnabled() {
  return (state.authProviders || []).some((provider) => provider.provider === "email" && provider.enabled);
}

function setAuthMode(mode) {
  state.authMode = mode === "register" ? "register" : "login";
  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.authMode === state.authMode));
  });
  $("#login-form").hidden = !authEmailEnabled() || state.authMode !== "login";
  $("#register-form").hidden = !authEmailEnabled() || state.authMode !== "register";
  const title = $("#auth-title");
  if (title) title.textContent = state.authMode === "login" ? "把申請進度帶著走" : "建立你的交換檔案";
  updateAuthProviderAvailability();
}

function resetEmailVerificationFlow({ resetForm = false } = {}) {
  state.emailVerificationToken = "";
  state.emailVerificationAddress = "";
  const form = $("#register-form");
  if (resetForm) form.reset();
  form.elements.email_verification_token.value = "";
  $("#email-verification-code").value = "";
  $("#email-verification-step").hidden = true;
  $("#email-verification-status").textContent = "";
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  submit.querySelector("span").textContent = "完成 電子郵件 驗證後建立帳號";
}

async function requestEmailVerification() {
  const emailInput = $("#registration-email");
  const button = $("#request-email-verification");
  const status = $("#email-verification-status");
  if (!emailInput.reportValidity()) return;
  resetEmailVerificationFlow();
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  status.textContent = "正在寄送驗證碼…";
  try {
    const result = await fetchJson("/auth/email-verification/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailInput.value }),
    });
    state.emailVerificationAddress = emailInput.value.trim().toLowerCase();
    $("#email-verification-step").hidden = false;
    status.textContent = result.development_code
      ? `本機開發驗證碼：${result.development_code}（正式環境只會寄到 ${result.email_hint}）`
      : `驗證碼已寄到 ${result.email_hint}，15 分鐘內有效。`;
    $("#email-verification-code").focus();
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

async function confirmEmailVerification() {
  const email = $("#registration-email").value.trim().toLowerCase();
  const codeInput = $("#email-verification-code");
  const button = $("#confirm-email-verification");
  const status = $("#email-verification-status");
  if (email !== state.emailVerificationAddress) {
    resetEmailVerificationFlow();
    status.textContent = "電子郵件 已變更，請重新寄送驗證碼。";
    return;
  }
  if (!codeInput.reportValidity() || !/^\d{6}$/.test(codeInput.value)) {
    status.textContent = "請輸入六位數驗證碼。";
    return;
  }
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  status.textContent = "正在確認…";
  try {
    const result = await fetchJson("/auth/email-verification/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code: codeInput.value }),
    });
    state.emailVerificationToken = result.verification_token;
    $("#register-form").elements.email_verification_token.value = result.verification_token;
    const submit = $("#register-form").querySelector('button[type="submit"]');
    submit.disabled = false;
    submit.querySelector("span").textContent = "建立帳號";
    status.textContent = "電子郵件 已驗證，可以建立帳號。";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

async function requestProfileEmailVerification() {
  if (!state.account?.email) return;
  const button = $("#request-profile-email-verification");
  const status = $("#profile-email-verification-status");
  button.disabled = true;
  status.textContent = "正在寄送驗證碼…";
  try {
    const result = await fetchJson("/auth/email-verification/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: state.account.email }),
    });
    state.emailVerificationAddress = state.account.email.trim().toLowerCase();
    $("#profile-email-verification-step").hidden = false;
    status.textContent = result.development_code
      ? `本機開發驗證碼：${result.development_code}`
      : `驗證碼已寄到 ${result.email_hint}。`;
    $("#profile-email-verification-code").focus();
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function confirmProfileEmailVerification() {
  if (!state.account?.email) return;
  const input = $("#profile-email-verification-code");
  const button = $("#confirm-profile-email-verification");
  const status = $("#profile-email-verification-status");
  if (!input.reportValidity() || !/^\d{6}$/.test(input.value)) {
    status.textContent = "請輸入六位數驗證碼。";
    return;
  }
  button.disabled = true;
  status.textContent = "正在確認…";
  try {
    const result = await fetchJson("/auth/email-verification/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: state.account.email, code: input.value }),
    });
    if (!result.account_verified) throw new Error("電子郵件 驗證未套用到目前帳號。");
    state.account = await fetchJson("/auth/me");
    renderProfileVerificationSummary();
    await loadCommunityBoards();
    populateGlobalCommunitySchools();
    announce("電子郵件 已完成驗證", "success");
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

const TERMS_STORAGE_KEY = "uniway-terms-accepted";

function rememberAcceptedTerms(version) {
  try { window.localStorage.setItem(TERMS_STORAGE_KEY, version); } catch (_) { /* private mode: the tick just is not remembered */ }
}

// A returning visitor on the same browser finds the box already ticked for the version they accepted; a new version of the
// terms starts unticked again.
function syncTermsConsent({ remind = false } = {}) {
  const consent = $("#terms-consent");
  if (!consent) return;
  let remembered = null;
  try { remembered = window.localStorage.getItem(TERMS_STORAGE_KEY); } catch (_) { remembered = null; }
  consent.checked = remembered !== null && remembered === consent.dataset.termsVersion;
  $("#terms-consent-hint").hidden = !(remind && !consent.checked);
}

function openAuthDialog(mode = "login", { remindTerms = false } = {}) {
  renderDiscoveryRecents();
  setAuthMode(mode);
  syncTermsConsent({ remind: remindTerms });
  state.dialogReturnFocus = document.activeElement;
  $("#auth-dialog").hidden = false;
  document.body.classList.add("account-dialog-open");
  window.setTimeout(() => {
    const dialog = $("#auth-dialog");
    if (dialog.hidden || dialog.contains(document.activeElement)) return;
    const form = state.authMode === "login" ? $("#login-form") : $("#register-form");
    form?.querySelector("input")?.focus();
  }, 40);
}

function requireAccountForPrivateAction(message) {
  if (state.account) return true;
  if (state.authRestoreState === "pending") {
    announce("正在驗證登入狀態；完成前不會顯示或修改私人資料。", "info", true);
    return false;
  }
  if (state.authRestoreState === "unavailable") {
    announce("目前無法驗證登入狀態；私人資料已隱藏，恢復連線後會自動重試。", "info", true);
    return false;
  }
  announce(message, "info", true);
  openAuthDialog("register");
  return false;
}

function closeAuthDialog() {
  $("#auth-dialog").hidden = true;
  document.body.classList.remove("account-dialog-open");
  state.dialogReturnFocus?.focus?.();
  state.dialogReturnFocus = null;
}

// The account's settings are a full page (#profile). Every place that used to open the old dialog still calls this.
function openProfileDialog() {
  renderDiscoveryRecents();
  if (!state.account) {
    openAuthDialog();
    return;
  }
  if (window.location.hash === "#profile") {
    applyAppRoute({ loadFeed: false, resetScroll: true });
    return;
  }
  window.location.hash = "#profile";
}

function fillProfileForm() {
  renderDiscoveryRecents();
  const form = $("#profile-form");
  form.elements.display_name.value = state.account.display_name || "";
  // "Not chosen yet" shows blank. A picked school cannot be changed again for 3 days (the server enforces it too).
  form.elements.home_university.value = state.account.catalog_home_university
    || (state.account.home_university === "尚未選擇" ? "" : state.account.home_university)
    || "";
  const lockedUntil = schoolLockedUntil();
  form.elements.home_university.disabled = Boolean(lockedUntil);
  $("#profile-school-note").textContent = lockedUntil
    ? `學校選定後 3 天內不能更換，${formatSchoolLock(lockedUntil)} 之後才能修改。`
    : "學校會顯示在你的帳號與貼文上，選定後 3 天內不能更換。";
  form.elements.target_countries.value = (state.account.target_countries || []).join("、");
  form.elements.application_stage.value = state.account.application_stage || "exploring";
  const notifications = state.account.notification_preferences || {};
  form.elements.web_notifications.checked = notifications.web_enabled !== false;
  form.elements.email_notifications.checked = notifications.email_enabled === true;
  form.elements.content_updates.checked = notifications.content_updates_enabled !== false;
  const reminderDays = new Set(notifications.deadline_reminder_days || [30, 14, 7, 3, 1]);
  form.querySelectorAll('input[name="reminder_days"]').forEach((input) => {
    input.checked = reminderDays.has(Number(input.value));
  });
  form.querySelector(".form-status").textContent = "";
  state.profileFilledFor = state.account.id;
  $("#profile-email").textContent = state.account.email || "社群帳號";
  renderProfileVerificationSummary();
  renderProfileAvatar();
  window.UniWayProfile?.refresh();
}

// A deep link to #profile may load before the session is known, and a sign-out can happen while the page is open.
function syncProfileRoute() {
  if (window.location.hash !== "#profile" || state.authRestoreState === "pending") return;
  if (!state.account) applyAppRoute({ loadFeed: false, resetScroll: false });
  else if (state.profileFilledFor !== state.account.id) fillProfileForm();
}

function schoolLockedUntil() {
  const raw = state.account?.school_change_locked_until;
  const until = raw ? new Date(raw) : null;
  return until && until.getTime() > Date.now() ? until : null;
}

function formatSchoolLock(until) {
  return until.toLocaleString("zh-TW", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false });
}

function renderProfileVerificationSummary() {
  const summary = $("#profile-verification-summary");
  if (!summary || !state.account) return;
  const emailVerified = state.account.email_verified === true;
  const chosenSchool = state.account.catalog_home_university;
  const lockedUntil = schoolLockedUntil();
  const schoolLabel = chosenSchool
    ? `${chosenSchool}${state.account.school_basis === "school_email" ? " · 依校內信箱判斷" : ""}${lockedUntil ? ` · ${formatSchoolLock(lockedUntil)} 前不能更換` : ""}`
    : "尚未選擇學校";
  summary.innerHTML = `
    <span class="${emailVerified ? "is-verified" : "is-pending"}"><i data-lucide="${emailVerified ? "badge-check" : "circle-alert"}" aria-hidden="true"></i>${emailVerified ? "電子郵件 已驗證" : "電子郵件 待驗證"}</span>
    <span class="${chosenSchool ? "is-verified" : "is-optional"}"><i data-lucide="school" aria-hidden="true"></i>${escapeHtml(schoolLabel)}</span>`;
  const emailPanel = $("#profile-email-verification");
  emailPanel.hidden = emailVerified;
  $("#profile-email-verification-address").textContent = state.account.email || "";
  if (emailVerified) {
    $("#profile-email-verification-step").hidden = true;
    $("#profile-email-verification-status").textContent = "";
  }
  initIcons();
}

function notificationActionUrl(item) {
  const value = String(item?.action_url || "");
  if ((value.startsWith("/") && !value.startsWith("//") && !value.startsWith("/\\")) || value.startsWith("#")) {
    return value;
  }
  return "/#deadlines";
}

function notificationOfficialSourceUrl(item) {
  const value = String(item?.source_url || "").trim();
  if (!value) return "";
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "";
  } catch (_) {
    return "";
  }
}

function renderNotificationCenter() {
  const button = $("#notification-button");
  const badge = $("#notification-badge");
  if (button) {
    button.hidden = !state.account;
    button.setAttribute(
      "aria-label",
      state.notificationUnreadCount
        ? `開啟通知中心，${state.notificationUnreadCount} 則未讀`
        : "開啟通知中心",
    );
  }
  if (badge) {
    badge.hidden = state.notificationUnreadCount < 1;
  }
  const list = $("#notification-center-list");
  const status = $("#notification-center-status");
  const readAll = $("#notification-read-all");
  const deleteAll = $("#notification-delete-all");
  if (!list || !status || !readAll || !deleteAll) return;
  readAll.disabled = state.notificationUnreadCount < 1 || state.notificationLoading;
  deleteAll.disabled = state.notifications.length < 1 || state.notificationLoading;
  if (state.notificationLoading) {
    status.textContent = "正在整理你的通知…";
    list.innerHTML = '<div class="notification-center-loading"><span></span><span></span><span></span></div>';
    return;
  }
  status.textContent = state.notificationUnreadCount
    ? `${state.notificationUnreadCount} 則未讀通知`
    : "目前沒有未讀通知";
  if (!state.notifications.length) {
    list.innerHTML = '<div class="notification-center-empty"><i data-lucide="bell-ring" aria-hidden="true"></i><strong>目前沒有通知</strong><p>系統會提醒截止日、人工確認發布的官方規定，以及合作校來源更新。</p></div>';
    initIcons();
    return;
  }
  list.innerHTML = state.notifications.map((item) => {
    const unread = !item.read_at;
    const contentUpdate = item.kind === "content_update";
    const catalogueUpdate = item.kind === "catalogue_update";
    const smartStart = String(item.source_key || "").startsWith("calendar-start:");
    const sourceUrl = contentUpdate || catalogueUpdate ? notificationOfficialSourceUrl(item) : "";
    return `
      <article class="notification-center-item ${unread ? "is-unread" : ""}">
        <div class="notification-center-item-icon"><i data-lucide="${contentUpdate ? "file-clock" : catalogueUpdate ? "database-zap" : smartStart ? "play" : "calendar-clock"}" aria-hidden="true"></i></div>
        <div class="notification-center-item-content">
          <div class="notification-center-item-meta"><span>${contentUpdate ? "官方規定更新" : catalogueUpdate ? "合作校來源更新" : smartStart ? "建議開始準備日" : `截止前 ${escapeHtml(item.reminder_days)} 天`}</span><time datetime="${escapeHtml(item.created_at)}">${escapeHtml(formatDate(item.created_at))}</time></div>
          <h2>${escapeHtml(item.title)}</h2>
          <p>${escapeHtml(item.body)}</p>
          ${contentUpdate ? `<button type="button" class="text-action" data-notification-changes="${escapeHtml(item.id)}" aria-expanded="false">查看逐項變更</button><section class="notification-changes" aria-label="這次規定變更" aria-live="polite" hidden></section>` : ""}
          <div class="notification-center-item-actions">
            <a href="${escapeHtml(notificationActionUrl(item))}" data-open-notification="${escapeHtml(item.id)}">${contentUpdate ? "查看這所學校" : catalogueUpdate ? "查看合作學校" : smartStart ? "查看任務安排" : "查看申請時程"}</a>
            ${sourceUrl ? `<a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer" class="notification-official-source">查看官方來源<i data-lucide="external-link" aria-hidden="true"></i></a>` : ""}
            ${unread ? `<button type="button" class="text-action" data-read-notification="${escapeHtml(item.id)}">標為已讀</button>` : '<span class="notification-read-label"><i data-lucide="check" aria-hidden="true"></i>已讀</span>'}
            <button type="button" class="text-action notification-delete" data-delete-notification="${escapeHtml(item.id)}" aria-label="刪除通知：${escapeHtml(item.title)}"><i data-lucide="trash-2" aria-hidden="true"></i>刪除</button>
          </div>
        </div>
      </article>`;
  }).join("");
  initIcons();
}

function resetNotificationState() {
  state.notificationRequestId += 1;
  state.notifications = [];
  state.notificationUnreadCount = 0;
  state.notificationLoading = false;
  renderNotificationCenter();
}

function renderNotificationChanges(result) {
  if (!result.matches_current_plan) return '<p>目前志願或適用年度已不同；請先確認目前的申請背景，再核對這則歷史通知。</p>';
  if (!result.has_base) return '<p>舊版本來源無法取得，目前不能產生可靠對照。請查看官方來源。</p>';
  const values = (rows) => rows.map(change=>`<div class="notification-change-row"><strong>${escapeHtml(change.label)}</strong><div><span>原規定</span><p>${escapeHtml(change.before ?? "未提供")}</p></div><div><span>新規定</span><p>${escapeHtml(change.after ?? "已移除")}</p></div></div>`).join("");
  const steps = (result.step_changes || []).map(step=>`<details open><summary>${escapeHtml(step.title)} · ${escapeHtml({added:"新增",removed:"移除",changed:"調整"}[step.change_type] || "變更")}</summary>${values(step.changes || [])}</details>`).join("");
  const sources = (result.source_changes || []).map(source=>`<details><summary>來源：${escapeHtml(source.title)}</summary>${values(source.changes || [])}</details>`).join("");
  const actionLabels = {recheck_completed:"請重新確認已完成的工作", review_progress:"需重新核對", new_task:"新增工作", retired_task:"已從清單移除"};
  const impacts = result.affected_tasks || [];
  const affected = impacts.length ? `<section class="notification-affected-tasks" aria-label="受影響的準備工作"><h4>這次變更影響你的 ${impacts.length} 項準備工作</h4><ul>${impacts.map(row=>`<li data-affected-action="${escapeHtml(row.action)}"><strong>${escapeHtml(row.step_title)}</strong><span class="notification-affected-badge">${escapeHtml(actionLabels[row.action] || "需核對")}</span>${row.deadline_changed ? '<span class="notification-affected-badge warning">期限或送件方式有變</span>' : ""}${row.documents_changed ? '<span class="notification-affected-badge">文件要求有變</span>' : ""}<p>${escapeHtml(row.guidance)}</p>${row.document_template_ids?.length && applicationTemplateById(row.document_template_ids[0]) ? `<button type="button" class="text-action" data-journey-document="${escapeHtml(row.document_template_ids[0])}" data-journey-document-school="${escapeHtml(result.school_name)}">開啟對應文件</button>` : ""}</li>`).join("")}</ul><p class="notification-affected-note">系統只標出受影響的項目，不會自動修改你的進度、工時或個人期限。</p></section>` : "";
  return `<p class="notification-change-context">${escapeHtml(result.home_university)} → ${escapeHtml(result.school_name)} · 第 ${escapeHtml(result.from_version)} 版 → 第 ${escapeHtml(result.to_version)} 版</p><p>以下列出與目前申請背景相符的規定變更；已完成工作及個人排程會保留，請核對後再調整。</p>${affected}${values(result.workflow_changes || [])}${steps}${sources}${!steps && !(result.workflow_changes || []).length && !sources ? '<p>目前沒有與你的校系相符的逐欄變更。</p>' : ""}`;
}

async function showNotificationChanges(button) {
  const container = button.parentElement.querySelector(".notification-changes");
  if (!container || button.disabled) return;
  if (!container.hidden) { container.hidden = true; button.setAttribute("aria-expanded", "false"); button.textContent = "查看逐項變更"; return; }
  container.hidden = false;
  button.setAttribute("aria-expanded", "true");
  button.textContent = "收合逐項變更";
  if (container.dataset.loaded) return;
  const context = captureAuthenticatedRequestContext();
  const requestId = state.notificationRequestId;
  button.disabled = true;
  container.textContent = "正在讀取已發布版本的變更…";
  try {
    const result = await fetchJson(`/account/notifications/${encodeURIComponent(button.dataset.notificationChanges)}/changes`);
    if (!authenticatedRequestContextIsCurrent(context) || requestId !== state.notificationRequestId || !container.isConnected) return;
    container.innerHTML = renderNotificationChanges(result);
    const schoolLink = button.parentElement.querySelector("[data-open-notification]");
    if (schoolLink && result.action_url) schoolLink.setAttribute("href", notificationActionUrl(result));
    container.dataset.loaded = "true";
  } catch (error) {
    if (!authenticatedRequestContextIsCurrent(context) || requestId !== state.notificationRequestId || !container.isConnected) return;
    container.textContent = `${error.message} 收合後再展開即可重試。`;
  } finally {
    if (button.isConnected && authenticatedRequestContextIsCurrent(context)) button.disabled = false;
  }
}

async function loadNotifications({ quiet = false } = {}) {
  if (!state.account) {
    resetNotificationState();
    return;
  }
  state.notificationLoading = true;
  const requestId = ++state.notificationRequestId;
  const context = captureAuthenticatedRequestContext();
  renderNotificationCenter();
  try {
    const center = await fetchJson("/account/notifications?limit=50");
    if (requestId !== state.notificationRequestId || !authenticatedRequestContextIsCurrent(context)) return;
    state.notifications = center.items || [];
    state.notificationUnreadCount = center.unread_count || 0;
  } catch (error) {
    if (requestId !== state.notificationRequestId || !authenticatedRequestContextIsCurrent(context)) return;
    if (!quiet) announce(`通知暫時無法載入：${error.message}`, "error");
  } finally {
    if (requestId === state.notificationRequestId && authenticatedRequestContextIsCurrent(context)) {
      state.notificationLoading = false;
      renderNotificationCenter();
    }
  }
}

async function openNotificationDialog() {
  if (!state.account) {
    openAuthDialog();
    return;
  }
  state.dialogReturnFocus = document.activeElement;
  $("#notification-dialog").hidden = false;
  document.body.classList.add("account-dialog-open");
  await loadNotifications({ quiet: true });
  window.setTimeout(() => $("#notification-dialog .dialog-close")?.focus(), 40);
}

function closeNotificationDialog() {
  $("#notification-dialog").hidden = true;
  document.body.classList.remove("account-dialog-open");
  state.dialogReturnFocus?.focus?.();
  state.dialogReturnFocus = null;
}

async function markNotificationRead(notificationId) {
  const updated = await fetchJson(`/account/notifications/${encodeURIComponent(notificationId)}/read`, {
    method: "PATCH",
  });
  state.notifications = state.notifications.map((item) => item.id === updated.id ? updated : item);
  state.notificationUnreadCount = state.notifications.filter((item) => !item.read_at).length;
  renderNotificationCenter();
}

async function markAllNotificationsRead() {
  const button = $("#notification-read-all");
  button.disabled = true;
  try {
    const center = await fetchJson("/account/notifications/read-all", { method: "PATCH" });
    state.notifications = center.items || [];
    state.notificationUnreadCount = center.unread_count || 0;
    renderNotificationCenter();
  } catch (error) {
    announce(error.message, "error");
    button.disabled = false;
  }
}

async function deleteNotification(notificationId) {
  await fetchJson(`/account/notifications/${encodeURIComponent(notificationId)}`, {
    method: "DELETE",
  });
  state.notifications = state.notifications.filter((item) => item.id !== notificationId);
  state.notificationUnreadCount = state.notifications.filter((item) => !item.read_at).length;
  renderNotificationCenter();
  announce("通知已刪除", "success");
}

async function deleteAllNotifications() {
  if (!state.notifications.length || !window.confirm("要刪除通知中心內的全部通知嗎？此動作無法復原。")) return;
  const button = $("#notification-delete-all");
  button.disabled = true;
  try {
    const center = await fetchJson("/account/notifications", { method: "DELETE" });
    state.notifications = center.items || [];
    state.notificationUnreadCount = center.unread_count || 0;
    renderNotificationCenter();
    announce("全部通知已刪除", "success");
  } catch (error) {
    announce(error.message, "error");
    button.disabled = false;
  }
}

function trapAccountDialogFocus(event) {
  if (event.key !== "Tab") return;
  const dialog = [$("#notification-dialog"), $("#auth-dialog")].find((item) => item && !item.hidden);
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

function renderEntitlementStatus() {
  const container = $("#profile-entitlement-status");
  if (!container) return;
  const entitlements = state.entitlements;
  if (!state.account || !entitlements) {
    container.hidden = true;
    container.innerHTML = "";
    return;
  }
  const closedBeta = entitlements.release_mode === "closed_beta";
  const subscription = entitlements.effective_tier === "subscription";
  container.hidden = false;
  container.innerHTML = closedBeta
    ? '<i data-lucide="badge-check" aria-hidden="true"></i><span><strong>免費使用中</strong><small>目前所有功能都免費開放，系統不會扣款。</small></span>'
    : subscription
      ? '<i data-lucide="sparkles" aria-hidden="true"></i><span><strong>訂閱功能已開啟</strong><small>可使用多份申請計畫、文件工具與智慧提醒。</small></span>'
      : '<i data-lucide="circle-check" aria-hidden="true"></i><span><strong>免費方案</strong><small>官方資訊、基本清單與提醒會持續免費提供。</small></span>';
}

async function loadProductEntitlements() {
  try {
    state.entitlements = await fetchJson("/product/entitlements");
  } catch (_) {
    state.entitlements = null;
  }
  renderEntitlementStatus();
  renderApplicationCenter();
  renderDocumentCheckAccess();
  renderPrivateVault();
  renderCalendarSync();
  if (state.account && entitlementFeatureEnabled("encrypted_document_vault")) {
    await loadPrivateVault();
  }
  if (
    state.account
    && entitlementFeatureEnabled("external_calendar_sync")
    && !state.calendarSyncLoading
    && !state.calendarSync
  ) {
    await loadCalendarSyncStatus();
  } else if (state.account && !entitlementFeatureEnabled("external_calendar_sync")) {
    state.calendarSync = null;
    renderCalendarSync();
  }
  scheduleCalendarConflictAnalysis();
  scheduleCalendarTaskAnalysis();
  initIcons();
}

function workspaceCalendarEventPayload(event) {
  return {
    id: String(event.id),
    title: event.title,
    date: event.date,
    category: event.category || "other",
    reminder_days: Number(event.reminderDays ?? event.reminder_days) || 0,
    note: event.note || "",
    source_url: event.sourceUrl || event.source_url || null,
    school_name: event.schoolName || event.school_name || null,
    preparation_days: Number(event.preparationDays ?? event.preparation_days) || 0,
    effort_hours: event.effortHours ?? event.effort_hours ?? null,
    remaining_hours: event.remainingHours ?? event.remaining_hours ?? null,
    depends_on: event.dependsOn || event.depends_on || [],
    available_from: event.availableFrom || event.available_from || null,
    waiting_reason: event.waitingReason || event.waiting_reason || null,
    document_id: event.documentId || event.document_id || null,
    status: ["todo", "preparing", "ready"].includes(event.status) ? event.status : "todo",
    generated_from_event_id: event.generatedFromEventId || event.generated_from_event_id || null,
    origin: event.origin === "official" ? "official" : "personal",
  };
}

function stateCalendarEvent(event) {
  return {
    id: event.id,
    title: event.title,
    date: event.date,
    category: event.category || "other",
    reminderDays: Number(event.reminder_days) || 0,
    note: event.note || "",
    sourceUrl: event.source_url || null,
    schoolName: event.school_name || "",
    preparationDays: Number(event.preparation_days) || 0,
    effortHours: event.effort_hours ?? null,
    remainingHours: event.remaining_hours ?? null,
    dependsOn: event.depends_on || [],
    availableFrom: event.available_from || "",
    waitingReason: event.waiting_reason || "",
    documentId: event.document_id || "",
    status: ["todo", "preparing", "ready"].includes(event.status) ? event.status : "todo",
    generatedFromEventId: event.generated_from_event_id || "",
    origin: event.origin === "official" ? "official" : "personal",
  };
}

function accountWorkspaceKey(homeSchool) {
  return String(homeSchool || "").trim().toLocaleLowerCase();
}

function normalizedBudgetAmount(value) {
  return Math.min(1_000_000_000, Math.max(0, Number(value) || 0));
}

function workspaceBudgetPlanPayload(plan) {
  if (!plan || typeof plan !== "object" || Array.isArray(plan)) return null;
  const savedAt = String(plan.saved_at || plan.savedAt || "");
  if (!Number.isFinite(Date.parse(savedAt))) return null;
  const currency = String(plan.currency || "TWD").trim().toUpperCase();
  return {
    currency: /^[A-Z]{3}$/.test(currency) ? currency : "TWD",
    months: Math.min(24, Math.max(1, Math.trunc(Number(plan.months) || 5))),
    housing: normalizedBudgetAmount(plan.housing),
    food: normalizedBudgetAmount(plan.food),
    transport: normalizedBudgetAmount(plan.transport),
    other: normalizedBudgetAmount(plan.other),
    one_time: normalizedBudgetAmount(plan.one_time ?? plan.oneTime),
    scholarship: normalizedBudgetAmount(plan.scholarship),
    saved_at: new Date(savedAt).toISOString(),
  };
}

function sanitizeBudgetPlans(plans) {
  if (!plans || typeof plans !== "object" || Array.isArray(plans)) return {};
  const sanitized = {};
  Object.entries(plans).forEach(([schoolName, plan]) => {
    const school = String(schoolName || plan?.schoolName || "").trim();
    const safePlan = workspaceBudgetPlanPayload(plan);
    if (school && safePlan) sanitized[school] = safePlan;
  });
  return sanitized;
}

function stateBudgetPlan(schoolName, plan) {
  const safePlan = workspaceBudgetPlanPayload(plan);
  if (!safePlan) return null;
  return {
    schoolName,
    currency: safePlan.currency,
    months: safePlan.months,
    housing: safePlan.housing,
    food: safePlan.food,
    transport: safePlan.transport,
    other: safePlan.other,
    oneTime: safePlan.one_time,
    scholarship: safePlan.scholarship,
    savedAt: safePlan.saved_at,
  };
}

function renderAccountWorkspaceSyncStatus() {
  const control = $("#account-workspace-sync-control");
  const status = $("#account-workspace-sync-status");
  if (!control || !status) return;
  const signedIn = Boolean(state.account);
  control.hidden = !signedIn;
  if (!signedIn) return;

  const hasInFlight = state.accountWorkspaceLoadingCount > 0
    || Object.keys(state.accountWorkspaceSyncLanes || {}).length > 0;
  const hasPending = Object.keys(state.accountWorkspacePending || {}).length > 0;
  let presentation;
  if (navigator.onLine === false) {
    presentation = {
      state: "offline",
      label: "離線，稍後同步",
      message: "目前離線；收藏與申請進度會在恢復連線後同步。",
      icon: "cloud-off",
    };
  } else if (hasInFlight) {
    presentation = {
      state: "syncing",
      label: "正在同步",
      message: "正在同步收藏與申請進度。",
      icon: "loader-circle",
    };
  } else if (Object.keys(state.accountWorkspaceSyncErrors || {}).length) {
    presentation = {
      state: "failed",
      label: "同步失敗",
      message: "同步失敗；變更仍保留在此裝置。",
      icon: "triangle-alert",
    };
  } else if (hasPending) {
    presentation = {
      state: "pending",
      label: "等待同步",
      message: "收藏與申請進度已有變更，正在等待同步。",
      icon: "cloud-upload",
    };
  } else if (state.accountWorkspaceHasSynced) {
    presentation = {
      state: "synced",
      label: "已同步",
      message: "條件、收藏與申請進度已同步。",
      icon: "circle-check",
    };
  } else {
    presentation = {
      state: "syncing",
      label: "正在同步",
      message: "正在載入已同步的收藏與申請進度。",
      icon: "loader-circle",
    };
  }

  const changed = status.dataset.syncState !== presentation.state;
  status.dataset.syncState = presentation.state;
  status.setAttribute("aria-busy", String(presentation.state === "syncing"));
  status.title = presentation.label;
  const label = $("#account-workspace-sync-label");
  const message = $("#account-workspace-sync-message");
  if (changed || label?.textContent !== presentation.label) {
    if (label) label.textContent = presentation.label;
    if (message) message.textContent = presentation.message;
    const icon = status.querySelector(".workspace-sync-status-icon");
    if (icon) icon.innerHTML = `<i data-lucide="${presentation.icon}" aria-hidden="true"></i>`;
    initIcons();
  }
  const retry = $("#account-workspace-sync-retry");
  if (retry) retry.hidden = presentation.state !== "failed";
}

function persistAccountWorkspaceSyncMetadata() {
  try {
    if (
      !state.accountWorkspaceSyncAccountId
      && !Object.keys(state.accountWorkspaceRevisions || {}).length
      && !Object.keys(state.accountWorkspaceBases || {}).length
      && !Object.keys(state.accountWorkspacePending || {}).length
    ) {
      window.localStorage.removeItem(STORAGE_KEYS.workspaceSync);
      return;
    }
    window.localStorage.setItem(STORAGE_KEYS.workspaceSync, JSON.stringify({
      account_id: state.accountWorkspaceSyncAccountId,
      revisions: state.accountWorkspaceRevisions,
      bases: state.accountWorkspaceBases,
      pending: state.accountWorkspacePending,
    }));
  } catch (_) {
    // The in-memory retry queue still works for the current page session.
  }
}

function clearAccountWorkspaceClientState() {
  window.clearTimeout(state.accountWorkspaceSyncTimer);
  window.clearTimeout(state.accountWorkspaceRetryTimer);
  state.accountWorkspaceSyncTimer = null;
  state.accountWorkspaceRetryTimer = null;
  state.accountWorkspaceLoadedSchool = "";
  state.accountWorkspaceSyncSuspended = false;
  state.accountWorkspaceRevisions = {};
  state.accountWorkspaceBases = {};
  state.accountWorkspacePending = {};
  state.accountWorkspaceSyncLanes = {};
  state.accountWorkspaceLoadingCount = 0;
  state.accountWorkspaceSyncAccountId = "";
  state.accountWorkspaceSyncErrors = {};
  state.accountWorkspaceHasSynced = false;
  persistAccountWorkspaceSyncMetadata();
  renderAccountWorkspaceSyncStatus();
}

function resetAccountWorkspaceOwnerScopedState(homeSchool = activeHomeSchool()) {
  const workspace = emptyAccountWorkspace(homeSchool);
  state.favorites = new Set();
  state.applications = new Set();
  state.applicationProgress = {};
  state.documentReadiness = {};
  state.applicationContext = { ...workspace.application_context };
  state.applicationSelections = {};
  state.submissionProgress = {};
  state.budgetPlans = {};
  state.calendarEvents = [];
  state.planningAvailability = null;
  state.preparationTasks = {};
  state.accountWorkspaceLoadedSchool = "";
  state.eligibilityProfile = null;
  state.personalApplicationPlan = null;
  state.advisorPlan = null;
  state.planningRecommendationKey = "";
  state.planningPreview = null;
  state.planningLoading = false;
  state.planningRequestId += 1;
  state.applicationProfileMemoryEnabled = false;
  clearApplicationFormDraftState();
  try {
    [
      STORAGE_KEYS.favorites,
      STORAGE_KEYS.applications,
      STORAGE_KEYS.progress,
      STORAGE_KEYS.documents,
      STORAGE_KEYS.eligibility,
      STORAGE_KEYS.calendarEvents,
      STORAGE_KEYS.planningAvailability,
      STORAGE_KEYS.preparationTasks,
      STORAGE_KEYS.budgetPlans,
      STORAGE_KEYS.applicationContext,
      STORAGE_KEYS.applicationSelections,
      STORAGE_KEYS.submissionProgress,
      STORAGE_KEYS.applicationProfileMemory,
      STORAGE_KEYS.applicationProfileMemoryEnabled,
    ].forEach((key) => window.localStorage.removeItem(key));
  } catch (_) {
    // In-memory isolation still prevents one account from importing another account's workspace.
  }
}

function prepareAccountWorkspaceSyncForAccount(account) {
  const accountId = String(account?.id || "");
  if (!accountId) return;
  const ownerMatches = Boolean(state.accountWorkspaceSyncAccountId)
    && state.accountWorkspaceSyncAccountId === accountId;
  if (!ownerMatches) {
    window.clearTimeout(state.accountWorkspaceSyncTimer);
    window.clearTimeout(state.accountWorkspaceRetryTimer);
    state.accountWorkspaceSyncTimer = null;
    state.accountWorkspaceRetryTimer = null;
    state.accountWorkspaceRevisions = {};
    state.accountWorkspaceBases = {};
    state.accountWorkspacePending = {};
    state.accountWorkspaceSyncLanes = {};
    state.accountWorkspaceLoadingCount = 0;
    state.accountWorkspaceSyncErrors = {};
    state.accountWorkspaceHasSynced = false;
    resetAccountWorkspaceOwnerScopedState();
  }
  state.accountWorkspaceSyncAccountId = accountId;
  persistAccountWorkspaceSyncMetadata();
}

function sanitizeSelectionConditions(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const profile = value.profile;
  if (!profile || typeof profile !== "object" || Array.isArray(profile)) return {profile:null};
  const number = (value, maximum) => {
    if (value === null || value === undefined || value === "") return null;
    const result = Number(value);
    return Number.isFinite(result) && result >= 0 && result <= maximum ? result : null;
  };
  const text = (value, length) => typeof value === "string" ? value.trim().slice(0,length) : "";
  return {profile:{
    college:text(profile.college,120), department:text(profile.department,120),
    current_year:text(profile.current_year,40), degree_level:text(profile.degree_level,80),
    academic_score:number(profile.academic_score,100),
    academic_gpa:number(profile.academic_gpa,4.3), class_rank_percent:number(profile.class_rank_percent,100),
    language_test:["toeic","ielts","toefl","toefl_new","duolingo","other"].includes(profile.language_test) ? profile.language_test : null,
    language_score:number(profile.language_score,1000),
    jlpt_level:['N1','N2','N3','N4','N5'].includes(profile.jlpt_level) ? profile.jlpt_level : null,
    target_term:text(profile.target_term,40), preferred_country:text(profile.preferred_country,80),
    monthly_budget:number(profile.monthly_budget,10000000), needs_scholarship:profile.needs_scholarship === true,
    academic_year:text(profile.academic_year,20), application_round:text(profile.application_round,80),
    preferred_teaching_language:["english","japanese","chinese","other"].includes(profile.preferred_teaching_language) ? profile.preferred_teaching_language : null,
    course_interests:text(profile.course_interests,120),
  }};
}

function selectionConditionsPayload(profile = state.eligibilityProfile) {
  return sanitizeSelectionConditions({profile:profile ? {
    college:profile.college, department:profile.department, current_year:profile.currentYear,
    degree_level:profile.degree, academic_score:profile.academicScore,
    academic_gpa:profile.academicGpa, class_rank_percent:profile.classRankPercent,
    language_test:profile.languageTest, language_score:profile.languageScore,
    jlpt_level:profile.jlptLevel || null,
    target_term:profile.targetTerm, preferred_country:profile.preferredCountry,
    monthly_budget:profile.monthlyBudget, needs_scholarship:profile.scholarshipNeeded,
    academic_year:profile.academicYear, application_round:profile.applicationRound,
    preferred_teaching_language:profile.teachingLanguage || null, course_interests:profile.courseInterests || "",
  } : null});
}

function selectionProfileFromWorkspace(conditions) {
  const profile = sanitizeSelectionConditions(conditions)?.profile;
  if (!profile) return null;
  return {
    college:profile.college, department:profile.department, currentYear:profile.current_year,
    degree:profile.degree_level, academicScore:profile.academic_score,
    academicGpa:profile.academic_gpa, classRankPercent:profile.class_rank_percent,
    languageTest:profile.language_test || "", languageScore:profile.language_score,
    jlptLevel:profile.jlpt_level || '',
    languageLabel:selectionLanguageLabel(profile.language_test, profile.language_score),
    targetTerm:profile.target_term, preferredCountry:profile.preferred_country,
    monthlyBudget:profile.monthly_budget, scholarshipNeeded:profile.needs_scholarship,
    academicYear:profile.academic_year, applicationRound:profile.application_round,
    teachingLanguage:profile.preferred_teaching_language || "", courseInterests:profile.course_interests || "",
  };
}

function sanitizeAccountWorkspacePayload(payload, homeSchool = activeHomeSchool()) {
  const source = payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
  const context = source.application_context && typeof source.application_context === "object"
    ? source.application_context
    : {};
  const applicationProgress = {};
  Object.entries(source.application_progress || {}).forEach(([school, steps]) => {
    if (!steps || typeof steps !== "object" || Array.isArray(steps)) return;
    applicationProgress[school] = Object.fromEntries(
      Object.entries(steps).map(([step, complete]) => [step, complete === true])
    );
  });
  const selections = {};
  Object.entries(source.application_selections || {}).forEach(([templateId, selection]) => {
    if (!selection || typeof selection !== "object" || Array.isArray(selection)) return;
    selections[templateId] = {
      selected: selection.selected === true,
      copies: Number(selection.copies) || 1,
      status: selection.status || "draft",
      reviewed_version: selection.reviewed_version || null,
      reviewed_content_sha256: selection.reviewed_content_sha256 || null,
      reviewed_at: selection.reviewed_at || null,
    };
  });
  const schoolName = String(source.home_school || homeSchool || activeHomeSchool()).trim();
  return {
    home_school: schoolName,
    revision: Math.max(0, Number(source.revision) || 0),
    favorite_schools: [...new Set((source.favorite_schools || []).map(String).map((item) => item.trim()).filter(Boolean))],
    discovery: UniWayDiscovery.sanitize(source.discovery),
    selection_conditions: sanitizeSelectionConditions(source.selection_conditions),
    application_schools: [...new Set((source.application_schools || []).map(String).map((item) => item.trim()).filter(Boolean))],
    application_progress: applicationProgress,
    document_readiness: Object.fromEntries(
      Object.entries(source.document_readiness || {}).filter(([, value]) => ["todo", "preparing", "ready"].includes(value))
    ),
    application_context: {
      school_name: schoolName,
      target_school: context.target_school || "",
      target_country: context.target_country || "",
      program_type: context.program_type || "exchange",
      college: context.college || "",
      department: context.department || "",
      degree_level: context.degree_level || "",
      academic_year: context.academic_year || "",
      application_round: context.application_round || "",
      semester: context.semester || "",
      flags: Array.isArray(context.flags) ? context.flags.map(String) : [],
      partner_document_states: Object.fromEntries(Object.entries(context.partner_document_states || {}).slice(0,214).filter(([,value])=>value && typeof value === "object" && !Array.isArray(value)).map(([key,value])=>[key,{host_admission_status:["unknown","not_accepted","accepted"].includes(value.host_admission_status) ? value.host_admission_status : "unknown",housing_choice:["unknown","on_campus","off_campus"].includes(value.housing_choice) ? value.housing_choice : "unknown"}])),
    },
    application_selections: selections,
    submission_progress: source.submission_progress && typeof source.submission_progress === "object"
      ? source.submission_progress
      : {},
    budget_plans: sanitizeBudgetPlans(source.budget_plans || source.budgetPlans),
    planning_availability: window.UniWayJourney.sanitizeAvailability(source.planning_availability),
    preparation_tasks: window.UniWayMultiPlan.sanitizeSettings(source.preparation_tasks),
    deadline_events: Array.isArray(source.deadline_events)
      ? source.deadline_events.map(workspaceCalendarEventPayload)
      : [],
  };
}

function workspaceValueComparable(value) {
  if (Array.isArray(value)) {
    return `[${value.map(workspaceValueComparable).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => (
      `${JSON.stringify(key)}:${workspaceValueComparable(value[key])}`
    )).join(",")}}`;
  }
  return JSON.stringify(value);
}

function workspaceValuesEqual(left, right) {
  return workspaceValueComparable(left) === workspaceValueComparable(right);
}

function mergeWorkspaceSet(baseItems, remoteItems, localItems) {
  const base = new Set(baseItems || []);
  const local = new Set(localItems || []);
  const merged = new Set(remoteItems || []);
  local.forEach((item) => {
    if (!base.has(item)) merged.add(item);
  });
  base.forEach((item) => {
    if (!local.has(item)) merged.delete(item);
  });
  return [...merged];
}

function mergeWorkspaceRecord(baseRecord, remoteRecord, localRecord, { recursive = false } = {}) {
  const base = baseRecord && typeof baseRecord === "object" && !Array.isArray(baseRecord) ? baseRecord : {};
  const remote = remoteRecord && typeof remoteRecord === "object" && !Array.isArray(remoteRecord) ? remoteRecord : {};
  const local = localRecord && typeof localRecord === "object" && !Array.isArray(localRecord) ? localRecord : {};
  const merged = {};
  const keys = new Set([...Object.keys(base), ...Object.keys(remote), ...Object.keys(local)]);
  keys.forEach((key) => {
    const baseHas = Object.prototype.hasOwnProperty.call(base, key);
    const remoteHas = Object.prototype.hasOwnProperty.call(remote, key);
    const localHas = Object.prototype.hasOwnProperty.call(local, key);
    const localMatchesBase = localHas === baseHas
      && (!localHas || workspaceValuesEqual(local[key], base[key]));
    if (localMatchesBase) {
      if (remoteHas) merged[key] = remote[key];
      return;
    }
    if (!localHas) return;
    const remoteMatchesBase = remoteHas === baseHas
      && (!remoteHas || workspaceValuesEqual(remote[key], base[key]));
    const canMergeRecursively = recursive
      && remoteHas
      && !remoteMatchesBase
      && local[key]
      && remote[key]
      && typeof local[key] === "object"
      && typeof remote[key] === "object"
      && !Array.isArray(local[key])
      && !Array.isArray(remote[key]);
    merged[key] = canMergeRecursively
      ? mergeWorkspaceRecord(baseHas ? base[key] : {}, remote[key], local[key], { recursive: true })
      : local[key];
  });
  return merged;
}

function workspaceEventsById(events) {
  return Object.fromEntries((events || []).map((event) => [event.id, event]));
}

function mergeAccountWorkspaceConflict(baseWorkspace, remoteWorkspace, localWorkspace) {
  const remote = sanitizeAccountWorkspacePayload(remoteWorkspace, remoteWorkspace?.home_school);
  const base = sanitizeAccountWorkspacePayload(
    baseWorkspace || emptyAccountWorkspace(remote.home_school),
    remote.home_school,
  );
  const local = sanitizeAccountWorkspacePayload(localWorkspace, remote.home_school);
  const deadlineEvents = mergeWorkspaceRecord(
    workspaceEventsById(base.deadline_events),
    workspaceEventsById(remote.deadline_events),
    workspaceEventsById(local.deadline_events),
  );
  return sanitizeAccountWorkspacePayload({
    home_school: remote.home_school,
    revision: remote.revision,
    discovery: mergeDiscoveryWorkspace(base.discovery, remote.discovery, local.discovery),
    // A profile is one condition snapshot; merging individual fields could invent an unsubmitted combination.
    selection_conditions: workspaceValuesEqual(base.selection_conditions, local.selection_conditions)
      ? remote.selection_conditions : local.selection_conditions,
    favorite_schools: mergeWorkspaceSet(
      base.favorite_schools,
      remote.favorite_schools,
      local.favorite_schools,
    ),
    application_schools: mergeWorkspaceSet(
      base.application_schools,
      remote.application_schools,
      local.application_schools,
    ),
    application_progress: mergeWorkspaceRecord(
      base.application_progress,
      remote.application_progress,
      local.application_progress,
      { recursive: true },
    ),
    document_readiness: mergeWorkspaceRecord(
      base.document_readiness,
      remote.document_readiness,
      local.document_readiness,
    ),
    application_context: {
      ...mergeWorkspaceRecord(
        base.application_context,
        remote.application_context,
        local.application_context,
      ),
      school_name: remote.home_school,
      partner_document_states: mergeWorkspaceRecord(
        base.application_context?.partner_document_states,
        remote.application_context?.partner_document_states,
        local.application_context?.partner_document_states,
      ),
    },
    application_selections: mergeWorkspaceRecord(
      base.application_selections,
      remote.application_selections,
      local.application_selections,
    ),
    submission_progress: mergeWorkspaceRecord(
      base.submission_progress,
      remote.submission_progress,
      local.submission_progress,
      { recursive: true },
    ),
    budget_plans: mergeWorkspaceRecord(
      base.budget_plans,
      remote.budget_plans,
      local.budget_plans,
    ),
    deadline_events: Object.values(deadlineEvents),
    planning_availability: workspaceValuesEqual(base.planning_availability, local.planning_availability) ? remote.planning_availability : local.planning_availability,
    preparation_tasks: mergeWorkspaceRecord(base.preparation_tasks, remote.preparation_tasks, local.preparation_tasks, {recursive:true}),
  }, remote.home_school);
}

function workspaceComparable(workspace) {
  const safe = sanitizeAccountWorkspacePayload(workspace, workspace?.home_school);
  safe.revision = 0;
  return JSON.stringify(safe);
}

function queueAccountWorkspaceSync(payload) {
  const safe = sanitizeAccountWorkspacePayload(payload, payload?.home_school);
  prepareAccountWorkspaceSyncForAccount(state.account);
  const key = accountWorkspaceKey(safe.home_school);
  safe.revision = Math.max(
    Number(state.accountWorkspaceRevisions[key]) || 0,
    Number(safe.revision) || 0
  );
  state.accountWorkspacePending[key] = safe;
  delete state.accountWorkspaceSyncErrors[key];
  persistAccountWorkspaceSyncMetadata();
  renderAccountWorkspaceSyncStatus();
  return safe;
}

function accountWorkspacePayload(homeSchool = activeHomeSchool()) {
  const key = accountWorkspaceKey(homeSchool);
  return sanitizeAccountWorkspacePayload({
    home_school: homeSchool,
    revision: state.accountWorkspaceRevisions[key] || 0,
    favorite_schools: [...state.favorites],
    discovery: discoveryData(homeSchool),
    selection_conditions: selectionConditionsPayload(),
    application_schools: [...state.applications],
    application_progress: state.applicationProgress,
    document_readiness: state.documentReadiness,
    application_context: {
      ...state.applicationContext,
      school_name: homeSchool,
    },
    application_selections: state.applicationSelections,
    submission_progress: state.submissionProgress,
    budget_plans: state.budgetPlans,
    deadline_events: state.calendarEvents.map(workspaceCalendarEventPayload),
    planning_availability: state.planningAvailability,
    preparation_tasks: state.preparationTasks,
  }, homeSchool);
}

function persistAccountWorkspaceLocally() {
  try {
    if (state.eligibilityProfile) window.localStorage.setItem(STORAGE_KEYS.eligibility, JSON.stringify(state.eligibilityProfile));
    else window.localStorage.removeItem(STORAGE_KEYS.eligibility);
    window.localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify([...state.favorites]));
    window.localStorage.setItem(STORAGE_KEYS.applications, JSON.stringify([...state.applications]));
    window.localStorage.setItem(STORAGE_KEYS.progress, JSON.stringify(state.applicationProgress));
    window.localStorage.setItem(STORAGE_KEYS.documents, JSON.stringify(state.documentReadiness));
    window.localStorage.setItem(STORAGE_KEYS.applicationContext, JSON.stringify(state.applicationContext));
    window.localStorage.setItem(STORAGE_KEYS.applicationSelections, JSON.stringify(state.applicationSelections));
    window.localStorage.setItem(STORAGE_KEYS.submissionProgress, JSON.stringify(state.submissionProgress));
    window.localStorage.setItem(STORAGE_KEYS.budgetPlans, JSON.stringify(state.budgetPlans));
    window.localStorage.setItem(STORAGE_KEYS.calendarEvents, JSON.stringify(state.calendarEvents));
    window.localStorage.setItem(STORAGE_KEYS.planningAvailability, JSON.stringify(state.planningAvailability));
    window.localStorage.setItem(STORAGE_KEYS.preparationTasks, JSON.stringify(state.preparationTasks));
    persistAccountWorkspaceSyncMetadata();
  } catch (_) {
    // Account sync remains authoritative when browser storage is unavailable.
  }
}

function renderAccountWorkspaceState() {
  window.UniWayMultiPlan?.render();
  if (!state.dashboard) {
    updateFavoriteCounts();
    renderApplicationJourney();
    restoreApplicationContextForm();
    renderApplicationCenter();
    return;
  }
  renderPartnerTable();
  renderFavorites();
  updateFavoriteCounts();
  renderDecisionBrief();
  renderDocumentReadiness();
  renderDocumentWorkspace();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  renderBudgetPlanner();
  renderAdvisorForm();
  renderEligibilityOptions({ preserveDraft: true });
  restoreEligibilityForm({ preserveDraft: true });
  renderApplicationCalendar();
  scheduleCalendarConflictAnalysis();
  scheduleCalendarTaskAnalysis();
  restoreApplicationContextForm();
  renderApplicationCenter();
  const workflow = state.activeSchool
    ? state.workflowCache.get(workflowContextKey(state.activeSchool))
    : null;
  if (workflow) {
    renderApplicationWorkflow(workflow);
  } else if (state.activeSchool) {
    const activeItem = partnerByName(state.activeSchool);
    if (activeItem) loadApplicationWorkflow(activeItem);
  }
}

function applyAccountWorkspace(workspace) {
  if (!workspace) return;
  if (state.account) applyDiscoveryWorkspace(workspace.discovery, workspace.home_school);
  state.accountWorkspaceSyncSuspended = true;
  try {
    state.favorites = new Set(workspace.favorite_schools || []);
    state.applications = new Set(workspace.application_schools || []);
    state.applicationProgress = workspace.application_progress || {};
    state.documentReadiness = workspace.document_readiness || {};
    state.applicationContext = {
      school_name: workspace.home_school || activeHomeSchool(),
      target_school: "",
      target_country: "",
      program_type: "exchange",
      college: "",
      department: "",
      degree_level: "",
      academic_year: "",
      application_round: "",
      semester: "",
      flags: [],
      ...(workspace.application_context || {}),
    };
    const syncedContext = workspace.application_context || {};
    const oldConditions = selectionConditionsPayload();
    if (workspace.selection_conditions !== null && workspace.selection_conditions !== undefined) {
      state.eligibilityProfile = selectionProfileFromWorkspace(workspace.selection_conditions);
    } else if (syncedContext.college || syncedContext.department || syncedContext.degree_level) {
      state.eligibilityProfile = {
        ...(state.eligibilityProfile || {}),
        college: syncedContext.college || "",
        department: syncedContext.department || "",
        degree: syncedContext.degree_level || "",
        academicYear: syncedContext.academic_year || "",
        applicationRound: syncedContext.application_round || "",
      };
    }
    if (!workspaceValuesEqual(oldConditions, selectionConditionsPayload())) {
      state.advisorPlan = null;
      state.personalApplicationPlan = null;
      state.planningPreview = null;
      state.planningRecommendationKey = "";
      state.conditionsRequestId += 1;
      state.advisorLoading = false;
      state.planningRequestId += 1;
      const submit = $("#advisor-submit");
      if (submit) { submit.disabled = false; submit.removeAttribute("aria-busy"); }
      $("#advisor-result-content").innerHTML = '<p>已載入帳號條件。更新推薦以查看符合這份條件的候選學校。</p>';
      $("#eligibility-result").innerHTML = '<p>已載入帳號條件。核對當期志願以更新申請清單。</p>';
    }
    state.applicationSelections = workspace.application_selections || {};
    state.submissionProgress = workspace.submission_progress || {};
    state.budgetPlans = Object.fromEntries(
      Object.entries(workspace.budget_plans || {})
        .map(([schoolName, plan]) => [schoolName, stateBudgetPlan(schoolName, plan)])
        .filter(([, plan]) => Boolean(plan))
    );
    state.calendarEvents = (workspace.deadline_events || []).map(stateCalendarEvent);
    state.planningAvailability = window.UniWayJourney.sanitizeAvailability(workspace.planning_availability);
    state.preparationTasks = window.UniWayMultiPlan.sanitizeSettings(workspace.preparation_tasks);
    state.accountWorkspaceLoadedSchool = workspace.home_school || activeHomeSchool();
    const workspaceKey = accountWorkspaceKey(state.accountWorkspaceLoadedSchool);
    state.accountWorkspaceRevisions[workspaceKey] = Math.max(
      Number(state.accountWorkspaceRevisions[workspaceKey]) || 0,
      Number(workspace.revision) || 0,
    );
    persistAccountWorkspaceLocally();
  } finally {
    state.accountWorkspaceSyncSuspended = false;
  }
  renderAccountWorkspaceState();
}

function emptyAccountWorkspace(homeSchool) {
  return {
    home_school: homeSchool,
    discovery: UniWayDiscovery.empty(),
    selection_conditions: {profile:null},
    revision: 0,
    favorite_schools: [],
    application_schools: [],
    application_progress: {},
    document_readiness: {},
    application_context: {
      school_name: homeSchool,
      target_school: "",
      target_country: "",
      program_type: "exchange",
      college: "",
      department: "",
      degree_level: "",
      academic_year: "",
      application_round: "",
      semester: "",
      flags: [],
    },
    application_selections: {},
    submission_progress: {},
    budget_plans: {},
    deadline_events: [],
  };
}

function schedulePendingWorkspaceRetry() {
  window.clearTimeout(state.accountWorkspaceRetryTimer);
  state.accountWorkspaceRetryTimer = null;
  if (
    !state.account
    || navigator.onLine === false
  ) {
    renderAccountWorkspaceSyncStatus();
    return;
  }
  state.accountWorkspaceRetryTimer = window.setTimeout(() => {
    void retryPendingWorkspaceSyncs();
  }, 5000);
}

function accountWorkspaceSyncErrorIsRetryable(error) {
  if (!error?.status) return true;
  return [408, 409, 425, 429].includes(error.status) || error.status >= 500;
}

async function drainAccountWorkspaceSync(key, { quiet = true, requestContext } = {}) {
  let lastEnvelope = null;
  let conflictRetries = 0;
  while (
    authenticatedRequestContextIsCurrent(requestContext)
    && navigator.onLine !== false
    && state.accountWorkspacePending[key]
  ) {
    const latest = state.accountWorkspacePending[key];
    const outgoing = sanitizeAccountWorkspacePayload({
      ...latest,
      revision: Math.max(
        Number(state.accountWorkspaceRevisions[key]) || 0,
        Number(latest.revision) || 0
      ),
    }, latest.home_school);
    state.accountWorkspacePending[key] = outgoing;
    persistAccountWorkspaceSyncMetadata();
    try {
      const envelope = await fetchJson("/account/workspace", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(outgoing),
      });
      if (!authenticatedRequestContextIsCurrent(requestContext)) return lastEnvelope;
      const saved = envelope?.workspace;
      if (!saved) return lastEnvelope;
      const savedWorkspace = sanitizeAccountWorkspacePayload(saved, saved.home_school);
      const savedRevision = Number(savedWorkspace.revision) || 0;
      state.accountWorkspaceRevisions[key] = Math.max(
        Number(state.accountWorkspaceRevisions[key]) || 0,
        savedRevision
      );
      const pending = state.accountWorkspacePending[key];
      if (pending && workspaceComparable(pending) === workspaceComparable(outgoing)) {
        delete state.accountWorkspacePending[key];
      } else if (pending) {
        state.accountWorkspacePending[key] = sanitizeAccountWorkspacePayload({
          ...pending,
          revision: state.accountWorkspaceRevisions[key],
        }, pending.home_school);
      }
      state.accountWorkspaceBases[key] = savedWorkspace;
      delete state.accountWorkspaceSyncErrors[key];
      state.accountWorkspaceHasSynced = true;
      persistAccountWorkspaceSyncMetadata();
      if (
        loadedAccountWorkspaceCanApply(savedWorkspace.home_school, savedWorkspace, requestContext)
        && workspaceComparable(accountWorkspacePayload(savedWorkspace.home_school))
          !== workspaceComparable(savedWorkspace)
      ) {
        applyAccountWorkspace(savedWorkspace);
      }
      renderAccountWorkspaceSyncStatus();
      lastEnvelope = { ...envelope, workspace: savedWorkspace };
      conflictRetries = 0;
    } catch (error) {
      if (error.staleSession || error.sessionExpired) return lastEnvelope;
      if (!authenticatedRequestContextIsCurrent(requestContext)) return lastEnvelope;
      const current = error.payload?.detail?.current_workspace;
      if (error.status === 409 && current) {
        state.accountWorkspaceRevisions[key] = Math.max(
          Number(state.accountWorkspaceRevisions[key]) || 0,
          Number(current.revision) || 0
        );
        const pending = state.accountWorkspacePending[key] || outgoing;
        const baseConditions = state.accountWorkspaceBases[key]?.selection_conditions ?? null;
        if (accountWorkspaceKey(activeHomeSchool()) === key
          && !workspaceValuesEqual(baseConditions,current.selection_conditions ?? null)
          && !workspaceValuesEqual(baseConditions,pending.selection_conditions ?? null)
          && !workspaceValuesEqual(current.selection_conditions ?? null,pending.selection_conditions ?? null)) {
          announce("另一裝置也更新了選校條件；這次保留你剛提交的整份條件，請再核對。", "info");
        }
        const mergedPending = mergeAccountWorkspaceConflict(
          state.accountWorkspaceBases[key],
          current,
          pending,
        );
        state.accountWorkspaceBases[key] = sanitizeAccountWorkspacePayload(
          current,
          current.home_school,
        );
        state.accountWorkspacePending[key] = mergedPending;
        persistAccountWorkspaceSyncMetadata();
        if (accountWorkspaceKey(activeHomeSchool()) === key) {
          applyAccountWorkspace(mergedPending);
        }
        if (conflictRetries < 1) {
          conflictRetries += 1;
          continue;
        }
      }
      const errorMessage = error.message || "帳號工作區同步失敗";
      state.accountWorkspaceSyncErrors[key] = errorMessage;
      renderAccountWorkspaceSyncStatus();
      if (accountWorkspaceSyncErrorIsRetryable(error)) schedulePendingWorkspaceRetry();
      if (!quiet) announce(errorMessage, "error", true);
      return lastEnvelope;
    }
  }
  return lastEnvelope;
}

function startAccountWorkspaceDrain(key, { quiet = true } = {}) {
  if (!state.account || navigator.onLine === false || !state.accountWorkspacePending[key]) {
    renderAccountWorkspaceSyncStatus();
    return Promise.resolve(null);
  }
  const existing = state.accountWorkspaceSyncLanes[key];
  if (existing) return existing;
  const requestContext = captureAuthenticatedRequestContext();
  delete state.accountWorkspaceSyncErrors[key];
  let lane;
  lane = drainAccountWorkspaceSync(key, { quiet, requestContext }).finally(() => {
    if (state.accountWorkspaceSyncLanes[key] === lane) {
      delete state.accountWorkspaceSyncLanes[key];
    }
    if (authenticatedRequestContextIsCurrent(requestContext)) {
      renderAccountWorkspaceSyncStatus();
    }
  });
  state.accountWorkspaceSyncLanes[key] = lane;
  renderAccountWorkspaceSyncStatus();
  return lane;
}

async function saveAccountWorkspace({
  homeSchool = activeHomeSchool(),
  payload = null,
  quiet = true,
} = {}) {
  if (!state.account || state.accountWorkspaceSyncSuspended) return null;
  const outgoing = queueAccountWorkspaceSync(payload || accountWorkspacePayload(homeSchool));
  if (navigator.onLine === false) return null;
  return startAccountWorkspaceDrain(accountWorkspaceKey(outgoing.home_school), { quiet });
}

async function retryPendingWorkspaceSyncs() {
  if (!state.account || navigator.onLine === false) {
    renderAccountWorkspaceSyncStatus();
    return;
  }
  const requestContext = captureAuthenticatedRequestContext();
  window.clearTimeout(state.accountWorkspaceRetryTimer);
  state.accountWorkspaceRetryTimer = null;
  renderAccountWorkspaceSyncStatus();
  const keys = Object.keys(state.accountWorkspacePending || {});
  if (!keys.length) {
    if (!state.accountWorkspaceHasSynced && state.accountWorkspaceLoadingCount === 0) {
      await loadAccountWorkspace();
    }
    renderAccountWorkspaceSyncStatus();
    return;
  }
  for (const key of keys) {
    if (!authenticatedRequestContextIsCurrent(requestContext)) return;
    if (!state.accountWorkspacePending[key]) continue;
    await startAccountWorkspaceDrain(key, { quiet: true });
    if (!authenticatedRequestContextIsCurrent(requestContext)) return;
  }
  renderAccountWorkspaceSyncStatus();
}

async function retryAccountWorkspaceSyncFromControl() {
  const retry = $("#account-workspace-sync-retry");
  const restoreFocus = retry && document.activeElement === retry;
  if (retry) retry.disabled = true;
  try {
    if (Object.keys(state.accountWorkspacePending || {}).length) {
      await retryPendingWorkspaceSyncs();
    } else {
      await loadAccountWorkspace();
    }
  } finally {
    if (retry) retry.disabled = false;
    if (restoreFocus && retry?.hidden) $("#account-button")?.focus();
  }
}

function scheduleAccountWorkspaceSync() {
  if (!state.account || state.accountWorkspaceSyncSuspended) return;
  const outgoing = queueAccountWorkspaceSync(accountWorkspacePayload());
  const key = accountWorkspaceKey(outgoing.home_school);
  window.clearTimeout(state.accountWorkspaceSyncTimer);
  state.accountWorkspaceSyncTimer = null;
  if (navigator.onLine === false) return;
  state.accountWorkspaceSyncTimer = window.setTimeout(() => {
    state.accountWorkspaceSyncTimer = null;
    void startAccountWorkspaceDrain(key, { quiet: true });
  }, 350);
}

function loadedAccountWorkspaceCanApply(homeSchool, workspace, requestContext) {
  if (!authenticatedRequestContextIsCurrent(requestContext) || !state.account || !workspace) return false;
  const key = accountWorkspaceKey(homeSchool);
  return accountWorkspaceKey(activeHomeSchool()) === key
    && !state.accountWorkspacePending[key]
    && (Number(workspace.revision) || 0) >= (Number(state.accountWorkspaceRevisions[key]) || 0);
}

async function loadAccountWorkspace({ homeSchool = activeHomeSchool() } = {}) {
  if (!state.account) return;
  const requestContext = captureAuthenticatedRequestContext();
  const key = accountWorkspaceKey(homeSchool);
  state.accountWorkspaceLoadingCount += 1;
  delete state.accountWorkspaceSyncErrors[key];
  state.accountWorkspaceHasSynced = false;
  renderAccountWorkspaceSyncStatus();
  const localPayload = accountWorkspacePayload(homeSchool);
  try {
    let envelope = await fetchJson(`/account/workspace?home_school=${encodeURIComponent(homeSchool)}`);
    if (!authenticatedRequestContextIsCurrent(requestContext)) return;
    const remoteWorkspace = envelope.exists
      ? sanitizeAccountWorkspacePayload(envelope.workspace, homeSchool)
      : emptyAccountWorkspace(homeSchool);
    const pendingRevision = Number(state.accountWorkspacePending[key]?.revision) || 0;
    const remoteRevision = Number(remoteWorkspace.revision) || 0;
    if (
      !state.accountWorkspacePending[key]
      || !envelope.exists
      || (!state.accountWorkspaceBases[key] && pendingRevision === remoteRevision)
    ) {
      state.accountWorkspaceBases[key] = remoteWorkspace;
      persistAccountWorkspaceSyncMetadata();
    }
    let candidate = null;
    if (!envelope.exists) {
      candidate = state.accountWorkspacePending[key] || localPayload;
      const saved = await saveAccountWorkspace({ homeSchool, payload: candidate });
      if (!authenticatedRequestContextIsCurrent(requestContext)) return;
      envelope = saved || { exists: false, workspace: candidate };
    } else if (state.accountWorkspacePending[key]) {
      candidate = mergeAccountWorkspaceConflict(
        state.accountWorkspaceBases[key],
        remoteWorkspace,
        state.accountWorkspacePending[key],
      );
      state.accountWorkspaceBases[key] = remoteWorkspace;
      state.accountWorkspacePending[key] = candidate;
      persistAccountWorkspaceSyncMetadata();
      const saved = await saveAccountWorkspace({ homeSchool, payload: candidate });
      if (!authenticatedRequestContextIsCurrent(requestContext)) return;
      envelope = saved || { exists: true, workspace: candidate };
    }
    if (loadedAccountWorkspaceCanApply(homeSchool, envelope?.workspace, requestContext)) {
      state.accountWorkspaceBases[key] = sanitizeAccountWorkspacePayload(envelope.workspace, homeSchool);
      persistAccountWorkspaceSyncMetadata();
      applyAccountWorkspace(envelope.workspace);
      // Migrate an authenticated, owner-scoped legacy browser profile once. Explicit clears never migrate.
      if (envelope.workspace.selection_conditions == null && state.eligibilityProfile) scheduleAccountWorkspaceSync();
    }
    if (authenticatedRequestContextIsCurrent(requestContext) && !state.accountWorkspacePending[key]) {
      delete state.accountWorkspaceSyncErrors[key];
      state.accountWorkspaceHasSynced = true;
    }
  } catch (error) {
    if (error.staleSession || !authenticatedRequestContextIsCurrent(requestContext)) return;
    const errorMessage = error.message || "帳號工作區暫時無法使用";
    state.accountWorkspaceSyncErrors[key] = errorMessage;
    if (accountWorkspaceSyncErrorIsRetryable(error)) schedulePendingWorkspaceRetry();
    announce(`帳號同步暫時無法使用：${errorMessage}`, "error");
  } finally {
    if (authenticatedRequestContextIsCurrent(requestContext)) {
      state.accountWorkspaceLoadingCount = Math.max(0, state.accountWorkspaceLoadingCount - 1);
      renderAccountWorkspaceSyncStatus();
    }
  }
}

async function hydrateAccountWorkspace({ homeSchool = activeHomeSchool() } = {}) {
  if (!canAccessPartnerCatalog()) return;
  const requestContext = captureAuthenticatedRequestContext();
  await loadAccountWorkspace({ homeSchool });
  if (
    !authenticatedRequestContextIsCurrent(requestContext)
    || navigator.onLine === false
    || !Object.keys(state.accountWorkspacePending || {}).length
  ) return;
  await retryPendingWorkspaceSyncs();
}

function renderAccountState() {
  const label = $("#account-button-label");
  const restorePending = !state.account && state.authRestoreState === "pending";
  const restoreUnavailable = !state.account && state.authRestoreState === "unavailable";
  const accountLabel = state.account?.display_name
    || (restorePending ? "驗證中" : restoreUnavailable ? "離線" : "登入");
  if (label) label.textContent = accountLabel;
  const accountButton = $("#account-button");
  if (accountButton) {
    accountButton.setAttribute(
      "aria-label",
      state.account
        ? `開啟${state.account.display_name || "我的"}帳號設定`
        : restorePending
          ? "正在驗證登入狀態"
          : restoreUnavailable
            ? "目前離線，私人資料已隱藏"
            : "登入或建立帳號"
    );
    accountButton.disabled = restorePending;
  }
  const avatar = $(".account-button-avatar");
  if (avatar) {
    avatar.innerHTML = state.account?.avatar_url
      ? `<img src="${escapeHtml(state.account.avatar_url)}" alt="" referrerpolicy="no-referrer" />`
      : '<i data-lucide="user-round" aria-hidden="true"></i>';
  }
  renderProfileAvatar();
  renderEntitlementStatus();
  syncProfileRoute();
  window.UniWayProfile?.refresh();
  renderBoardFollowControls();
  renderCalendarSync();
  renderDocumentCheckAccess();
  populateGlobalCommunitySchools();
  renderNotificationCenter();
  renderPrivateVault();
  renderBudgetAuthState();
  renderAdvisorAccessState();
  if (state.dashboard) {
    renderPartnerTable();
    renderFavorites();
    updateFavoriteCounts();
    renderDocumentReadiness();
    renderDocumentWorkspace();
    renderApplicationCalendar();
    const activeItem = partnerByName(state.activeSchool);
    const tracker = $("#application-tracker");
    if (activeItem && tracker) tracker.innerHTML = renderApplicationTracker(activeItem);
  }
  updateDetailFavoriteButton();
  updateDetailApplicationButton();
  renderAccountWorkspaceSyncStatus();
  window.UniWayHome?.render();
  initIcons();
}

async function acceptAccountSession(session) {
  const advisorForm = $("#advisor-form");
  const draftHome = activeHomeSchool();
  const guestDraft = !state.account && state.authRestoreState === "anonymous"
    && advisorForm?.dataset.draftOwner === JSON.stringify(["", draftHome])
    ? [...advisorForm.querySelectorAll("input[id], select[id], textarea[id]")].map(field => ({
      id: field.id, value: field.value, checked: field.type === "checkbox" ? field.checked : null,
    })) : null;
  state.authRestoreRequestId += 1;
  state.authSessionEpoch += 1;
  state.account = session.profile;
  clearProtectedCatalog();
  state.authRestoreState = "authenticated";
  state.guestComparisons.clear();
  state.entitlements = null;
  readStoredAuthenticatedState(state.account.id);
  alignAccountSchool();
  prepareAccountWorkspaceSyncForAccount(state.account);
  // Only an unsaved draft typed in this anonymous session can follow the
  // explicit sign-in. Old-account/quarantined state stays isolated, and a
  // different mother school never inherits the draft.
  if (guestDraft && activeHomeSchool() === draftHome) {
    advisorForm.dataset.draftOwner = JSON.stringify([state.account.id, draftHome]);
    guestDraft.forEach(({ id, value, checked }) => {
      const field = document.getElementById(id);
      if (!field || !advisorForm.contains(field)) return;
      if (checked !== null) field.checked = checked;
      else field.value = value;
    });
    $("#advisor-profile-status").textContent = "剛才填寫的條件仍未保存，送出後才會同步。";
  } else if (guestDraft) {
    // The question is also private draft text, outside the academic profile.
    $("#advisor-question").value = "";
  }
  if (state.account.content_updates_seen_at) {
    state.updateSeenAt = state.account.content_updates_seen_at;
  }
  state.anonymousIdentity = null;
  try {
    window.localStorage.removeItem(STORAGE_KEYS.communityIdentity);
  } catch (_) {
    // The next authenticated community request will replace the old identity.
  }
  renderAccountState();
  closeAuthDialog();
  promptForAccountSchool();
  const hydrationTasks = [
    loadCommunityIdentityOptions(),
    loadCommunityBoards(),
    loadProductEntitlements(),
    hydrateAccountWorkspace(),
    loadCalendarSyncStatus(),
    loadNotifications({ quiet: true }),
    loadGlobalCommunity(),
    refreshHomeUniversityData(),
  ];
  if (state.applicationTemplates.length) hydrationTasks.push(loadApplicationFormDrafts());
  const hydrationResults = await Promise.allSettled(hydrationTasks);
  return hydrationResults.filter((result) => result.status === "rejected").length;
}

function clearAuthenticatedClientState() {
  if (state.account?.id) clearDiscoveryAccountData(state.account.id);
  window.UniWayCommunity?.clearAuthenticatedState(state.account?.id || "");
  state.workflowIssueReportAbortController?.abort();
  state.workflowIssueReportAbortController = null;
  state.workflowIssueReportRequestId += 1;
  clearWorkflowIssueReportPending();
  closeWorkflowIssueReport({ force: true });
  state.authRestoreRequestId += 1;
  state.authSessionEpoch += 1;
  state.account = null;
  state.authRestoreState = "anonymous";
  clearProtectedCatalog();
  state.quarantinedAccountOwnerId = "";
  state.guestComparisons.clear();
  state.pendingBudgetDraft = null;
  state.anonymousIdentity = null;
  state.communityIdentityOptions = null;
  state.communityBoards = [];
  state.entitlements = null;
  resetPrivatePlanningExperience({ renderRelated: false });
  state.calendarSync = null;
  state.calendarConflictReport = null;
  state.calendarTaskScheduleReport = null;
  state.applicationDownloadSummary = null;
  state.applicationPreviews = {};
  state.applicationPreviewRequestIds = {};
  Object.values(state.applicationPreviewTimers || {}).forEach((timer) => window.clearTimeout(timer));
  state.applicationPreviewTimers = {};
  state.privateVault = { items: [], total_bytes: 0, max_file_bytes: 20 * 1024 * 1024 };
  state.privateVaultLoading = false;
  state.privateVaultError = "";
  state.communityRequestId += 1;
  state.communityCache.clear();
  clearApplicationFormDraftState();
  state.applicationProfileMemoryEnabled = false;
  resetPrivateVaultForm({ keepCandidate: false });
  resetNotificationState();
  applyAccountWorkspace(emptyAccountWorkspace(activeHomeSchool()));
  clearAccountWorkspaceClientState();
  try {
    [
      STORAGE_KEYS.favorites,
      STORAGE_KEYS.applications,
      STORAGE_KEYS.progress,
      STORAGE_KEYS.documents,
      STORAGE_KEYS.eligibility,
      STORAGE_KEYS.communityIdentity,
      STORAGE_KEYS.calendarEvents,
      STORAGE_KEYS.planningAvailability,
      STORAGE_KEYS.preparationTasks,
      STORAGE_KEYS.budgetPlans,
      STORAGE_KEYS.applicationContext,
      STORAGE_KEYS.applicationSelections,
      STORAGE_KEYS.submissionProgress,
      STORAGE_KEYS.applicationProfileMemory,
      STORAGE_KEYS.applicationProfileMemoryEnabled,
      STORAGE_KEYS.authToken,
      STORAGE_KEYS.updateSeenAt,
    ].forEach((key) => window.localStorage.removeItem(key));
  } catch (_) {
    // In-memory clearing still protects the signed-out page.
  }
  state.profileFilledFor = "";
  const notificationDialog = $("#notification-dialog");
  if (notificationDialog) notificationDialog.hidden = true;
  // The profile page only exists for a signed-in account, so signing out leaves it.
  if (window.location.hash === "#profile") window.location.replace("#home");
  document.body.classList.remove("account-dialog-open");
  state.dialogReturnFocus = null;
  renderAccountState();
  renderGlobalCommunityIdentitySelector();
  // Signing out hides private data only; the school catalogue stays open to everyone.
  reloadPublicCatalog();
}

async function reloadPublicCatalog() {
  const requestedSchool = activeHomeSchool();
  await Promise.all([
    loadDashboard({ homeSchool: requestedSchool }),
    loadApplicationTemplates({ homeSchool: requestedSchool }),
    loadCoverage({ homeSchool: requestedSchool }),
    loadDestinationProfiles({ homeSchool: requestedSchool }),
  ]);
  applyAppRoute({ loadFeed: false, resetScroll: false });
}

function handleExpiredAccountSession() {
  if (!state.account) return;
  clearAuthenticatedClientState();
  openAuthDialog("login");
  announce("登入已過期；已清除這台裝置上的私人資料，請重新登入。", "info", true);
  void Promise.allSettled([
    loadCommunityBoards(),
    loadProductEntitlements(),
    loadGlobalCommunity(),
  ]);
}

async function restoreAccount({ quiet = false } = {}) {
  const requestId = ++state.authRestoreRequestId;
  const hadActiveAccount = Boolean(state.account);
  state.authRestoreState = "pending";
  renderAccountState();
  let restoredAccount;
  try {
    restoredAccount = await fetchJson("/auth/session");
  } catch (error) {
    if (requestId !== state.authRestoreRequestId) return false;
    if (!error?.status) {
      state.authRestoreState = "unavailable";
      renderAccountState();
      if (!quiet) {
        announce(
          "目前無法驗證登入狀態；私人資料已隱藏，恢復連線後會自動重試。",
          "info",
          true,
        );
      }
      return false;
    }
    clearAuthenticatedClientState();
    return false;
  }
  if (requestId !== state.authRestoreRequestId) return false;
  if (restoredAccount) {
    state.authSessionEpoch += 1;
    state.account = restoredAccount;
    clearProtectedCatalog();
    state.authRestoreState = "authenticated";
    readStoredAuthenticatedState(state.account.id);
    alignAccountSchool();
  } else if (hadActiveAccount) {
    clearAuthenticatedClientState();
  } else {
    state.authSessionEpoch += 1;
    state.account = null;
    state.authRestoreState = "anonymous";
    state.quarantinedAccountOwnerId = "";
    clearStoredAuthenticatedState();
  }
  if (state.account?.content_updates_seen_at) {
    state.updateSeenAt = state.account.content_updates_seen_at;
  }
  if (state.account) prepareAccountWorkspaceSyncForAccount(state.account);
  renderAccountState();
  await Promise.all([
    loadCalendarSyncStatus(),
    loadProductEntitlements(),
    loadCommunityBoards(),
    state.account ? loadCommunityIdentityOptions() : Promise.resolve(),
    state.account ? loadNotifications({ quiet: true }) : Promise.resolve(),
  ]);
  if (state.account) await hydrateAccountWorkspace();
  if (window.location.hash === "#auth=terms") {
    // The server turned a sign-in away because the terms were not ticked: show the dialog again with the reminder.
    window.UniWayNavigation.replaceState({}, "", "#home");
    openAuthDialog("register", { remindTerms: true });
  }
  if (window.location.hash === "#auth=success") {
    window.UniWayNavigation.replaceState({}, "", "#home");
    if (state.account) {
      announce("登入完成", "success");
      window.UniWayAnalytics?.track("auth_success", {
        new_account: Date.now() - Date.parse(state.account.created_at || 0) < 5 * 60 * 1000,
        school_basis: state.account.school_basis || "",
        provider: state.account.providers?.[0] || "",
      });
      // Google returns here with a full page load; the school picker waits for the page to finish booting.
      state.pendingSchoolPrompt = true;
    }
  }
  return Boolean(state.account);
}

async function handleAccountConnectivityRestored() {
  if (state.authRestoreState === "unavailable") {
    const restored = await restoreAccount({ quiet: true });
    if (restored) announce("已重新連線並恢復私人工作區", "success");
    return;
  }
  await retryPendingWorkspaceSyncs();
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
        email_verification_token: values.get("email_verification_token"),
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
    // Accepting the session closes the dialog straight away; the form is freed at the same moment so a
    // quick sign-out and sign-in is not blocked while the account's data is still loading.
    const hydration = acceptAccountSession(session);
    if (form.id === "register-form") resetEmailVerificationFlow({ resetForm: true });
    else form.reset();
    button.disabled = form.id === "register-form" && !state.emailVerificationToken;
    const hydrationFailureCount = await hydration;
    announce(
      hydrationFailureCount
        ? "登入完成；部分資料暫時無法同步，系統會在後續操作重試。"
        : endpoint.endsWith("register") ? "帳號已建立" : "登入完成",
      hydrationFailureCount ? "error" : "success"
    );
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = form.id === "register-form" && !state.emailVerificationToken;
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
        // Left blank while no school is chosen yet; the server rejects an empty school.
        home_university: values.get("home_university") || undefined,
        target_countries: String(values.get("target_countries") || "").split(/[、,，]+/).map((item) => item.trim()).filter(Boolean),
        application_stage: values.get("application_stage"),
        notification_preferences: {
          deadline_reminder_days: values.getAll("reminder_days").map(Number),
          web_enabled: values.get("web_notifications") === "on",
          email_enabled: values.get("email_notifications") === "on",
          push_enabled: false,
          content_updates_enabled: values.get("content_updates") === "on",
        },
      }),
    });
    state.anonymousIdentity = null;
    state.communityIdentityOptions = null;
    try {
      window.localStorage.removeItem(STORAGE_KEYS.communityIdentity);
    } catch (_) {}
    renderAccountState();
    await loadCommunityIdentityOptions();
    renderApplicationJourney();
    renderApplicationCalendar();
    await loadNotifications({ quiet: true });
    status.textContent = "已儲存";
    window.UniWayProfile?.refresh();
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function logoutAccount() {
  window.UniWayAnalytics?.track("logout", {});
  const logoutRequest = fetchJson("/auth/logout", { method: "POST" });
  clearAuthenticatedClientState();
  try {
    await logoutRequest;
  } catch (_) {
    // Local logout still completes if the session already expired.
  }
  await loadCommunityBoards();
  await loadProductEntitlements();
  await loadGlobalCommunity();
  announce("已登出", "success");
}

async function deleteAccount() {
  if (!window.confirm("刪除後無法復原，確定要刪除帳號嗎？")) return;
  let mutationId = "";
  try {
    mutationId = window.sessionStorage.getItem(
      APPLICATION_SESSION_KEYS.accountDeletionMutation,
    ) || "";
    if (!mutationId) {
      mutationId = window.crypto?.randomUUID
        ? window.crypto.randomUUID().replaceAll("-", "")
        : `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`.padEnd(32, "0");
      window.sessionStorage.setItem(
        APPLICATION_SESSION_KEYS.accountDeletionMutation,
        mutationId,
      );
    }
  } catch (_) {
    mutationId = `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`.padEnd(32, "0");
  }
  try {
    await fetchJson("/auth/me", {
      method: "DELETE",
      headers: { "X-Account-Deletion-Mutation-ID": mutationId },
    });
    clearAuthenticatedClientState();
    await loadCommunityBoards();
    await loadProductEntitlements();
    await loadGlobalCommunity();
    announce("帳號已刪除", "success");
  } catch (error) {
    announce(error.message, "error", true);
  }
}

async function loadDashboard({ refreshed = false, homeSchool = activeHomeSchool() } = {}) {
  if (!canAccessPartnerCatalog()) { clearProtectedCatalog(); setRefreshState(false); return false; }
  const requestedSchool = homeSchool;
  const request = beginSchoolDataRequest("dashboard", requestedSchool);
  state.partnerDataLoading = true;
  state.partnerDataError = false;
  syncPartnerView();
  setLoadingState();
  const loadingAnnouncementRevision = state.statusRevision;
  try {
    const school = encodeURIComponent(requestedSchool);
    const dashboard = await fetchJson(`/student-dashboard?school=${school}`);
    if (!schoolDataRequestIsCurrent(request)) return false;
    state.dashboard = dashboard;
    state.partnerDataLoading = false;
    renderDashboard();
    state.periodOptionsReady = loadApplicationPeriodOptions(); // never rejects; the first load waits for it
    state.hasLoaded = true;
    if (state.statusRevision === loadingAnnouncementRevision) {
      if (refreshed) announce("資料已重新整理", "success");
      else clearAnnouncement();
    }
    return true;
  } catch (error) {
    if (!schoolDataRequestIsCurrent(request)) return false;
    state.partnerDataLoading = false;
    state.partnerDataError = true;
    syncPartnerView();
    showLoadError(error, { announceError: state.statusRevision === loadingAnnouncementRevision });
    return false;
  } finally {
    if (schoolDataRequestIsCurrent(request)) setRefreshState(false);
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
  $("#partner-table").innerHTML = '<div class="skeleton skeleton-table"></div>';
  $("#period-list").innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
  $("#scholarship-list").innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
  $("#documents-list").innerHTML = '<div class="skeleton skeleton-document"></div><div class="skeleton skeleton-document"></div>';
  ["#partner-table", "#period-list", "#scholarship-list", "#documents-list"].forEach((selector) => {
    $(selector).setAttribute("aria-busy", "true");
  });
}

function catalogueSourceUnavailable() {
  return state.dashboard?.catalogue_source?.status === "unavailable";
}

function renderDashboard() {
  discoveryData();
  renderDiscoveryRecents();
  const data = state.dashboard;
  const lastChecked = formatDate(data.last_checked);
  const documents = data.document_explanations || data.rule_explanations || [];

  $("#coverage-rate").textContent = catalogueSourceUnavailable() ? "—" : String(data.partner_universities.length);
  $("#source-count").textContent = String(data.sources.length);
  $("#last-checked").textContent = lastChecked.slice(0, 10);
  $("#top-updated").textContent = `資料更新：${lastChecked}`;
  $("#document-count").textContent = `${documents.length} 份`;

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
  renderPrivateVault();
  renderDocumentWorkspace();
  renderSources();
  renderEligibilityOptions();
  restoreEligibilityForm();
  renderAdvisorForm();
  renderSearchResults();
  updateFavoriteCounts();
  populateGlobalCommunitySchools();
  if (calendarSyncFeatureEnabled() && state.calendarSync?.enabled) syncCalendarEvents({ quiet: true });
  window.UniWayHome?.render();

  ["#partner-table", "#period-list", "#scholarship-list", "#documents-list"].forEach((selector) => {
    $(selector).setAttribute("aria-busy", "false");
  });
  initIcons();
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
  const applicationSchool = state.applicationContext.target_school || [...state.applications][0] || "";
  if (!profile) return { icon: "scan-search", title: "完成資格與目標設定", detail: "先填學院、學制與語言成績", href: "#advisor" };
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
  if (
    !state.account
    || state.account.notification_preferences?.content_updates_enabled === false
    || !state.dashboard?.last_checked
  ) return false;
  const checked = new Date(state.dashboard.last_checked).getTime();
  const seen = new Date(state.updateSeenAt || 0).getTime();
  return Number.isFinite(checked) && checked > seen;
}

async function markDataReviewSeen() {
  state.updateSeenAt = state.dashboard?.last_checked || new Date().toISOString();
  try {
    window.localStorage.setItem(STORAGE_KEYS.updateSeenAt, state.updateSeenAt);
  } catch (_) {
    // The badge can still update for this session.
  }
  renderPersonalPlanSnapshot();
  if (state.account) {
    try {
      state.account = await fetchJson("/auth/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content_updates_seen_at: state.updateSeenAt }),
      });
    } catch (_) {
      // Keep the local acknowledgement and retry on a later interaction.
    }
  }
}


function recommendationStatus(item) {
  const status = item.eligibility_status || "needs_confirmation";
  const labels = { matches_known:"已知基本條件相符", needs_confirmation:"資格待確認", does_not_match:"目前條件不符" };
  return { status, label:labels[status] || labels.needs_confirmation, blocked:status === "does_not_match", pending:status !== "matches_known" };
}

function recommendationActions(item) {
  const meta = recommendationStatus(item);
  const school = escapeHtml(item.school_name);
  return `${meta.blocked ? '<a class="secondary-button" href="#advisor">調整條件</a>' : `<button type="button" class="secondary-button" data-planning-target="${school}">${state.applicationContext.target_school === item.school_name ? "已設為目標" : meta.pending ? "設為待確認目標" : "選為目標"}</button>`}<button type="button" class="text-action school-detail-trigger" data-school-name="${school}">查看學校</button>`;
}

function recommendationGroups(items, renderCard, limit) {
  const groups = [
    ["matches_known", "已知基本條件相符", "已知門檻通過初步比對；仍須核對科系、年度與當期公告。"],
    ["needs_confirmation", "先確認，再決定", "有資格尚待確認，先查看缺口與官方來源。"],
    ["does_not_match", "目前條件不符", "公開範圍或成績門檻與目前條件不符；確認例外前先勿視為可申請。"],
  ];
  return groups.map(([status, title, hint]) => {
    const rows = items.filter(item=>recommendationStatus(item).status === status);
    if (!rows.length) return "";
    const cards = rows.slice(0, limit).map(renderCard).join("");
    const rest = rows.slice(limit);
    const more = rest.length
      ? `<details class="match-more"><summary><span class="when-closed">再看其他 ${rest.length} 所</span><span class="when-open">收合</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div class="match-group-cards">${rest.map((item, index) => renderCard(item, limit + index)).join("")}</div></details>`
      : "";
    const heading = `<div class="match-group-heading"><strong>${title}<span>${rows.length} 所</span></strong><p>${hint}</p></div>`;
    return status === "does_not_match" ? `<details class="match-group is-blocked"><summary>目前條件不符 · ${rows.length} 所<i data-lucide="chevron-down" aria-hidden="true"></i></summary>${heading}<div class="match-group-cards">${cards}</div>${more}</details>` : `<section class="match-group" data-match-group="${status}">${heading}<div class="match-group-cards">${cards}</div>${more}</section>`;
  }).join("");
}

function semesterFromTargetTerm(term) {
  if (/^\d{4}-spring$/.test(term || "")) return "第二學期";
  if (/^\d{4}-fall$/.test(term || "")) return "第一學期";
  return ["第一學期","第二學期","一學年","寒假／暑假"].includes(term) ? term : "";
}

function targetRecommendation() {
  if (state.planningPlanProfileKey !== planningProfileKey()) return null;
  const target = state.applicationContext.target_school;
  if (state.advisorPlan?.target_match?.school_name === target) return state.advisorPlan.target_match;
  return state.advisorPlan?.recommendations?.find(item=>item.school_name === target);
}

function renderPlanningNextAction() {
  const container = $("#planning-next-action");
  if (!container) return;
  const profile = state.eligibilityProfile;
  const target = state.applicationContext.target_school;
  const recommendation = targetRecommendation();
  const tasks = state.calendarEvents.filter(event=>event.schoolName === target && String(event.id).startsWith("preparation-") && event.date >= localDateKey());
  const ready = initialApplicationTemplates().filter(template=>applicationTemplateCompletion(template).ready && applicationTemplateReviewed(template));
  let action = { title:"從你的條件開始", detail:"填寫你已知的資訊；尚未考語言測驗也能先探索學校。", href:"#advisor", label:"填寫條件", icon:"sliders-horizontal" };
  if (profile && !target) action = { title:"選出想申請的學校", detail:"先看資格缺口與官方來源，再確認本次規劃目標。", href:"#advisor", label:"查看選校結果", icon:"school" };
  else if (target && recommendation && recommendationStatus(recommendation).pending) action = { title:recommendationStatus(recommendation).blocked ? "先處理目標學校的資格限制" : "先確認目標學校的資格", detail:[...(recommendation.blocking_reasons || []), ...(recommendation.confirmation_items || [])][0] || "詳細核對科系、語言、年度與梯次，暫勿把選定目標當成資格已通過。", href:"#eligibility", label:"核對詳細資格", icon:"list-checks" };
  else if (target && !recommendation) action = { title:"確認這所學校的當期資格", detail:"目標已保存，但目前尚無適用的資格比對。先核對詳細條件，再安排送件。", href:"#eligibility", label:"核對詳細資格", icon:"list-checks" };
  else if (target && !tasks.length) action = { title:"為目標學校安排準備時程", detail:"依當期官方期限預覽日期；若期限未確認，會引導你查看官方來源。", label:"預覽準備時程", icon:"calendar-range", planning:true };
  else if (target) action = { title:ready.length ? "核對官方要求與送件方式" : "開始準備這個階段的文件", detail:ready.length ? `已有 ${ready.length} 份草稿填完並核對；匯出 PDF 不代表已送件或已錄取。` : "先處理校內申請文件；錄取後與返國文件可以稍後再看。", href:"#application-center", label:"開啟申請文件", icon:"folder-check" };
  container.innerHTML = `<span class="next-action-icon"><i data-lucide="${action.icon}" aria-hidden="true"></i></span><div><small>現在，先做這一件事</small><strong>${escapeHtml(action.title)}</strong><p>${escapeHtml(action.detail)}</p></div>${action.planning ? '<button type="button" class="primary-button" data-open-planning>預覽準備時程<i data-lucide="arrow-right" aria-hidden="true"></i></button>' : `<a class="primary-button" href="${action.href}">${action.label}<i data-lucide="arrow-right" aria-hidden="true"></i></a>`}`;
}

function openPlanningWorkspace() {
  const focus = () => {
    window.UniWayApplicationWorkspace?.openDeadlineSettings();
    $("#planning-workspace").scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block:"start"});
    $("#planning-academic-year").focus({preventScroll:true});
  };
  if (window.location.hash === "#overview") focus();
  else { window.addEventListener("hashchange", ()=>requestAnimationFrame(focus), {once:true}); window.location.hash = "#overview"; }
}

function renderPlanningRecovery() {
  const container = $("#planning-schedule-recovery");
  if (!container) return;
  const partner = partnerByName(state.applicationContext.target_school);
  const source = safeSourceUrl(partner?.source_url);
  container.hidden = false;
  container.innerHTML = `<strong>先確認這三件事，再安排日期</strong><ul><li>本次申請學年度與梯次是否適用</li><li>校內送件與合作校提名各自的截止日</li><li>文件清單、份數與送件單位</li></ul><div>${source ? `<a class="secondary-button" href="${escapeHtml(source)}" target="_blank" rel="noreferrer">查看本校官方來源<i data-lucide="external-link" aria-hidden="true"></i></a>` : ""}<a class="secondary-button" href="#deadlines">核對期限來源</a><button class="text-action" type="button" data-open-manual-task>自行建立準備任務</button></div><p>可先建立沒有官方期限的個人準備任務；填入的日期會標示為個人安排。</p>${applicationInquiryMarkup()}`;
  initIcons();
}

function safeSourceUrl(value) {
  try { const url = new URL(value); return ["https:","http:"].includes(url.protocol) ? url.href : ""; } catch (_) { return ""; }
}

function applicationInquiryMarkup() {
  const context = state.applicationContext;
  const scope = [context.academic_year && `${context.academic_year} 學年度`,context.application_round,context.target_school].filter(Boolean).join(" · ") || "本次交換申請";
  const question = `您好，我想確認 ${scope} 的申請資訊。\n1. 本次是否開放我的學院、系所及學制申請？\n2. 校內甄選與合作校提名／送件各自的確切截止日為何？\n3. 當期正式表格、必備附件、份數與簽章要求為何？\n4. 請問應向哪個單位送件，以及適用哪份官方公告？\n謝謝。`;
  return `<details class="application-inquiry"><summary>不知道怎麼問？展開詢問草稿</summary><p>請自行補上學院、系所與學制，再透過校方官方管道詢問。</p><textarea readonly aria-label="詢問校方的草稿" rows="8">${escapeHtml(question)}</textarea><button type="button" class="secondary-button" data-copy-application-inquiry>複製詢問草稿</button><small role="status" class="inquiry-copy-status"></small></details>`;
}

async function confirmPlanningTargetChange(schoolName) {
  const dialog = $("#planning-target-change-dialog");
  const previous = state.applicationContext.target_school;
  if (!previous || previous === schoolName) return true;
  const context = planningContextKey();
  const tasks = state.calendarEvents.filter(item=>item.schoolName === previous).length;
  const drafted = state.applicationTemplates.filter(template=>Object.values(state.applicationAnswers[template.id] || {}).some(applicationValuePresent)).length;
  $("#planning-target-change-summary").textContent = `${previous} → ${schoolName}`;
  $("#planning-target-change-impact").innerHTML = `<li>申請文件與時程預覽會改用新目標。</li><li>保留 ${tasks} 項原學校任務與 ${drafted} 份已開始的草稿，原任務仍標示原學校。</li><li>文件的核對狀態會重設，須確認新學校適用規定後重新核對。</li>`;
  dialog.returnValue = "";
  dialog.showModal();
  $("#planning-target-change-cancel").focus();
  return new Promise(resolve=>dialog.addEventListener("close", ()=>resolve(dialog.returnValue === "confirm" && context === planningContextKey()), {once:true}));
}

function applicationDocumentStage() {
  const groups = applicationStageGroups();
  const context = JSON.stringify([state.account?.id, activeHomeSchool(), state.applicationContext.target_school, state.applicationContext.program_type]);
  if (state.documentStageView?.context === context && groups.some(group=>group.stage === state.documentStageView.stage)) return state.documentStageView.stage;
  const stage = state.account?.application_stage;
  const label = state.applicationContext.program_type === "short_term_credit" ? (stage === "returned" ? "短期課程返國後" : "短期課程申請") : ({submitted:"校內初審通過後",accepted:"錄取後／出國前",abroad:"海外研修期間",returned:"返國後"}[stage] || "校內申請");
  // Sending an application does not establish that it has passed screening.
  return groups.some(group=>group.stage === label && stage !== "submitted") ? label : groups[0]?.stage || "";
}

function selectApplicationStage(stage) {
  state.documentStageView = {context:JSON.stringify([state.account?.id, activeHomeSchool(), state.applicationContext.target_school, state.applicationContext.program_type]), stage};
  renderApplicationTemplates();
  initIcons();
}

function renderPersonalPlanSnapshot() {
  const container = $("#personal-plan-snapshot");
  if (!container || !state.dashboard) return;
  const profile = state.eligibilityProfile;
  const target = state.applicationContext.target_school;
  const conditions = profile ? [profile.college, profile.degree, profile.languageLabel, targetTermLabel(profile.targetTerm)].filter(Boolean).join(" · ") : "先填學院、學制、成績與語言能力，系統會整理合適的候選學校。";
  container.innerHTML = `
    <article class="planning-profile-summary"><span class="plan-snapshot-icon"><i data-lucide="sliders-horizontal" aria-hidden="true"></i></span><div><small>我的條件</small><strong>${escapeHtml(conditions)}</strong><a href="#advisor">${profile ? "更新條件與推薦" : "開始選校規劃"}<i data-lucide="arrow-right" aria-hidden="true"></i></a></div></article>
    <article class="planning-target-card"><span class="plan-snapshot-icon"><i data-lucide="goal" aria-hidden="true"></i></span><div><small>我的目標</small><strong>${escapeHtml(target || "尚未選定目標學校")}</strong><span>${target ? "文件工作區會帶入這所學校，接著依上方提示確認資格與安排時程。" : "查看推薦後，由你確認要申請的學校。"}</span></div></article>`;
  renderApplicationJourney();
  renderPlanningWorkspace();
  renderPlanningNextAction();
  window.UniWayJourney.render();
  window.UniWayApplicationWorkspace?.render();
  window.UniWayTracker?.render();
  initIcons();
}

function languageThresholdFromPartner(item, languageTest, degreeLevel = null) {
  if (item.source_url?.startsWith("https://oia.ccu.edu.tw/")) {
    return window.UniWayCcuLanguage?.assess(item, languageTest, degreeLevel).threshold ?? null;
  }
  if (homeSelectionRules().partner_requirements_need_confirmation) return null;
  const text = partnerSummaryPoints(item, "eligibility_points").join(" ");
  const patterns = {
    toeic: /(?:TOEIC|多益)\s*(?:達|至少|總分|成績)?\s*(\d{3})/i,
    ielts: /IELTS\s*(?:總分|overall|達|至少)?\s*(\d(?:\.\d)?)/i,
    toefl: /TOEFL(?:\s*iBT)?\s*(?:總分|達|至少)?\s*(\d{2,3})/i,
    duolingo: /Duolingo\s*(?:達|至少)?\s*(\d{2,3})/i,
  };
  const pattern = patterns[languageTest];
  if (!pattern) return null;
  const match = text.match(pattern);
  const threshold = match ? Number(match[1]) : null;
  return Number.isFinite(threshold) ? threshold : null;
}

function partnerAvailabilityMeta(item) {
  if (activeHomeSchool() === "淡江大學") {
    const tku = window.UniWayTkuDetails?.agreementMeta(item || {});
    if (tku) return tku;
  }
  const status = item?.availability_status || "open";
  if (["not_open", "needs_confirmation", "zero_quota", "fee_paying"].includes(status)) {
    const label = {not_open:"本季未開放（官方灰字）",needs_confirmation:"名額尚未核實",zero_quota:"零名額",fee_paying:"自費計畫"}[status];
    return {status,shortLabel:label,cardLabel:label,matchLabel:label,reason:item.availability_note || label,blocked:true};
  }
  const additional = {
    closed: { label: "表列交換校／校內申請已截止", reason: "本梯次校內甄選已截止" },
    reference_only: { label: "舊期參考／不能作當期申請", reason: "尚未核實新版名額及規定" },
    quota_unconfirmed: { label: "當期名額或期間待確認", reason: "名額或申請期間尚未確認可申請" },
  };
  if (additional[status]) {
    const meta = additional[status];
    return { status, shortLabel: meta.label, cardLabel: meta.label, matchLabel: meta.label,
      reason: meta.reason, blocked: true };
  }
  if (status === "departmental_reference") {
    return {
      status,
      shortLabel: "院級參考／當期需確認",
      cardLabel: "院級官方參考／中央當期名單未列",
      matchLabel: "當期開放待確認",
      reason: "院級官方資料仍列此校",
      blocked: true,
    };
  }
  if (status === "agreement_only") {
    if (homeSelectionRules().pending_quota_planning && /^0\s*名?$/.test(item.quota || "")) {
      return {status, shortLabel:"116-1零名額", cardLabel:"116-1零名額／本期未開放", matchLabel:"本期未開放", reason:"官方名單已更新為零名額", blocked:true};
    }
    if (homeSelectionRules().pending_quota_planning && item.quota == null) {
      return {status, shortLabel:"本期名額待核實", cardLabel:"合作備查／本期名額待核實", hint:"可先加入志願規劃；能否申請須先確認本期名額與條件", matchLabel:"本期名額待確認", reason:"本期甄選名額尚未核實", blocked:false, pending:true};
    }
    return {
      status,
      shortLabel: "合作備查／本期名額待確認",
      cardLabel: "合作備查・本期名額待確認",
      hint: "保留合作關係參考；本期是否開放及名額尚待確認",
      matchLabel: "本期名額待確認",
      reason: "交換合作關係備查",
      blocked: true,
    };
  }
  return {
    status: "open",
    shortLabel: item?.application_window_status === "closed" ? `${item.application_round}名額已列／校內截止` : "本期開放",
    cardLabel: item?.application_window_status === "closed" ? `${item.application_round}名額已列／校內截止` : "本期開放",
    matchLabel: "本期開放",
    reason: "中央當期名單已列",
    blocked: false,
  };
}

function renderPartnerAvailabilityNotice(item) {
  const availability = partnerAvailabilityMeta(item);
  if (!availability.blocked && !availability.pending) return "";
  const fallback = activeHomeSchool() === "淡江大學" && availability.status === "agreement_only"
    ? "姊妹校名錄列有合作關係；本期名額、院系計畫與開放狀態尚未核實，不表示官方明示尚未公告。"
    : availability.pending ? availability.hint
    : homeSelectionRules().pending_quota_planning && /^0\s*名?$/.test(item.quota || "") ? "官方本期名單已更新為零名額，本期未開放申請。"
    : availability.status === "departmental_reference"
    ? "中央當期名單未列，請先向所屬學院或國際處確認是否開放。"
    : ["not_open", "needs_confirmation", "zero_quota", "fee_paying"].includes(availability.status)
    ? availability.reason
    : availability.status === "closed"
    ? "此校列於官方名額表，但校內申請已截止；已獲推薦者請依外校通知續辦。"
    : availability.status === "reference_only"
    ? "這是已標示年度的舊期資料；新版尚未核實。"
    : availability.status === "quota_unconfirmed"
    ? "須確認當期正名額及申請期間後才能申請。"
    : "你的學校和這所學校簽有交換合約，只是這一期的交換名額表沒有列它，所以現在不能申請。之後若開放，會出現在學校國際處的名額表；開放前請先看國際處公告。";
  return `
    <div class="partner-availability-notice ${escapeHtml(availability.status)}" role="note">
      <i data-lucide="badge-alert" aria-hidden="true"></i>
      <div>
        <strong>${escapeHtml(availability.shortLabel)}</strong>
        <p>${escapeHtml(fallback)}</p>${item.availability_note ? `<details class="copy-disclosure"><summary>完整說明</summary><p>${escapeHtml(item.availability_note)}</p></details>` : ""}
      </div>
    </div>`;
}

function partnerMatch(item, profile = state.eligibilityProfile) {
  const reasons = [];
  const risks = [];
  let score = 0;
  const availability = partnerAvailabilityMeta(item);
  if (availability.pending) risks.push(availability.hint);
  if (availability.blocked) {
    return {
      score: -100,
      tone: "blocked",
      label: availability.matchLabel,
      reasons: [availability.reason],
      risks: [item.availability_note || "目前未列入當期交換名額表"],
    };
  }
  if (!profile) {
    const coverage = coverageForSchool(item.school_name);
    score = (coverage?.workflow_status === "completed" ? 20 : 0) + (coverage?.experience_status === "completed" ? 10 : 0) + (destinationProfileForSchool(item.school_name) ? 10 : 0);
    return { score, tone: availability.pending ? "review" : "setup", label: availability.pending ? availability.matchLabel : "設定條件後配對", reasons: ["申請與生活資料已整理"], risks };
  }

  const mismatches = [];
  if (state.dashboard?.academic_gpa_minimum != null) {
    if (profile.academicGpa == null) risks.push("尚未填GPA；須GPA至少3.0且歷年平均至少70分");
    else if (Number(profile.academicGpa) < Number(state.dashboard.academic_gpa_minimum)) mismatches.push("GPA未達3.0");
    if (Number(profile.academicScore) < academicMinimum()) mismatches.push("歷年平均未達70分");
    if (item.application_window_status === "closed") risks.push("校內收件已截止，須確認已有申請或提名資格");
  }
  const college = homeCollegeValue(profile.college);
  const cycleConfirmed = !homeSelectionRules().partner_requirements_need_confirmation;
  const collegeKnown = Boolean(cycleConfirmed && college && !academicScopeNeedsConfirmation(item, "colleges"));
  const degree = resolvedDegreeLevel(profile.degree, profile.currentYear);
  const degreeMatch = partnerDegreeScopeMatches(item, college, degree);
  const degreeKnown = Boolean(cycleConfirmed && degree && degreeMatch !== null && !academicScopeNeedsConfirmation(item, "degree_levels"));
  const collegePass = collegeKnown && collegeMatches(item.colleges, college);
  const coupledMatch = coupledAcademicScopeMatches(item, college, degree);
  const degreePass = degreeKnown && degreeMatch;
  if (!collegeKnown) risks.push(college ? "合作校學院範圍待確認" : "尚未填寫學院");
  else if (collegePass) { score += 30; reasons.push("符合學院範圍"); }
  else { mismatches.push("學院範圍待確認"); risks.push(`你的學院：${college}；學校範圍：${item.colleges}`); }
  if (!degreeKnown) risks.push(profile.degree ? degreeMatch === null && degree === "研究所" ? "研究所尚未區分碩博士；合作校學制範圍待確認" : "合作校學制範圍待確認" : "尚未填寫學制");
  else if (degreePass) { score += 20; reasons.push("符合目前學制"); }
  else { mismatches.push("學制範圍待確認"); risks.push(coupledMatch === false ? `學院／學制配對不符：${college}／${degree}；學校配對：${item.degree_levels}` : `你的學制：${degree}；學校範圍：${item.degree_levels}`); }
  if (profile.preferredCountry && item.country === profile.preferredCountry) { score += 15; reasons.push(`位於優先國家 ${item.country}`); }
  const threshold = languageThresholdFromPartner(item, profile.languageTest, profile.degree);
  const hasLanguageScore = Boolean(profile.languageTest) && Number.isFinite(Number(profile.languageScore)) && Number(profile.languageScore) > 0;
  if (!hasLanguageScore) {
    risks.push("尚未填寫語言測驗或分數");
  } else if (threshold === null) {
    score += 8;
    risks.push(item.language_review_note || "合作校語言門檻需另查");
  } else if (Number(profile.languageScore) >= threshold) {
    score += 20;
    reasons.push(`目前語言分數達公開門檻 ${threshold}`);
  } else {
    mismatches.push("語言分數未達門檻");
    risks.push(`${String(profile.languageTest).toUpperCase()}：目前 ${profile.languageScore}；公開門檻 ${threshold}`);
  }
  const coverage = coverageForSchool(item.school_name);
  if (coverage?.workflow_status === "completed") { score += 8; reasons.push("申請流程已查核"); }
  if (destinationProfileForSchool(item.school_name)) score += 5;
  if (coverage?.experience_status === "completed") score += 2;
  const blocked = mismatches.length > 0;
  return {
    score,
    tone: blocked ? "blocked" : risks.length ? "review" : "strong",
    label: blocked ? mismatches[0] : availability.pending ? availability.matchLabel : !collegeKnown || !degreeKnown || !hasLanguageScore ? "條件待補齊" : score >= 78 ? "高度符合" : "值得查看",
    reasons: reasons.slice(0, 3),
    risks,
  };
}

function renderPartnerMatchExplanation(match) {
  if (!state.eligibilityProfile) return "";
  return `<details class="partner-match-disclosure">
    <summary class="match-pill ${escapeHtml(match.tone)}">${escapeHtml(match.label)}</summary>
    <div><ul>${[...match.reasons, ...match.risks].map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
    <p>依你填寫的條件初步比對，正式資格以校方審查為準。</p><a href="#eligibility">修改我的條件</a></div>
  </details>`;
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
  const recommendations = state.planningPlanProfileKey === planningProfileKey() ? state.advisorPlan?.recommendations || [] : [];
  if (!recommendations.length) {
    container.innerHTML = `<div class="match-empty"><i data-lucide="scan-search" aria-hidden="true"></i><span><strong>${state.eligibilityProfile ? "條件已保存，接著查看推薦" : "從你的條件，找到合適的下一站"}</strong><small>依你的學院、語言能力與偏好整理候選，正式資格仍需核對。</small></span><a class="primary-button" href="#advisor">${state.eligibilityProfile ? "更新選校推薦" : "填寫條件並配對"}</a></div>`;
    initIcons();
    refreshPlanningRecommendations();
    return;
  }
  container.innerHTML = recommendationGroups(recommendations, (item, index) => {
    const meta = recommendationStatus(item);
    const gaps = [...new Set([...(item.blocking_reasons || []), ...(item.confirmation_items || []), ...(item.gaps || [])])];
    return `<article class="recommended-match-card planning-match-card" data-eligibility-status="${meta.status}"><span class="planning-match-icon" aria-hidden="true"><i data-lucide="school"></i></span><div class="recommended-match-copy"><div class="planning-match-meta"><span class="match-rank">${index+1}</span><span class="match-label ${meta.blocked ? "blocked" : meta.pending ? "review" : "strong"}">${meta.label}</span></div><strong>${escapeHtml(item.school_name)}</strong><small>${escapeHtml(item.country || "國家待確認")}</small><ul>${(item.reasons || []).slice(0,2).map(reason=>`<li>${escapeHtml(reason)}</li>`).join("")}</ul>${gaps.length ? `<details class="match-checks"><summary>${meta.blocked ? "查看限制" : "查看待確認事項"} · ${gaps.length} 項</summary><ul>${gaps.map(gap=>`<li>${escapeHtml(gap)}</li>`).join("")}</ul>${safeSourceUrl(item.source_urls?.[0]) ? `<a href="${escapeHtml(safeSourceUrl(item.source_urls[0]))}" target="_blank" rel="noreferrer">查看官方來源</a>` : ""}</details>` : ""}<div class="planning-match-actions">${recommendationActions(item)}</div></div></article>`;
  }, 3);
  initIcons();
}

function planningProfileKey() {
  return JSON.stringify([state.account?.id, activeHomeSchool(), state.eligibilityProfile]);
}

async function refreshPlanningRecommendations() {
  const profile = state.eligibilityProfile;
  if (!state.account || !profile?.college || !profile?.degree || state.advisorLoading || !state.dashboard) return;
  const profileKey = planningProfileKey();
  const targetSchool = state.applicationContext.target_school;
  const key = JSON.stringify([profileKey,targetSchool]);
  if (state.planningRecommendationKey === key) return;
  state.planningRecommendationKey = key;
  try {
    const plan = await fetchJson("/advisor/plan", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({school_name:activeHomeSchool(),target_school:targetSchool || null,college:profile.college,department:profile.department || null,current_year:profile.currentYear || null,degree_level:profile.degree,academic_score:profile.academicScore ?? null,academic_gpa:profile.academicGpa ?? null,class_rank_percent:profile.classRankPercent ?? null,language_test:profile.languageTest,language_score:profile.languageScore ?? null,jlpt_level:profile.jlptLevel || null,academic_year:profile.academicYear || null,application_round:profile.applicationRound || null,target_term:profile.targetTerm || null,preferred_country:profile.preferredCountry || null,monthly_budget:profile.monthlyBudget || null,needs_scholarship:Boolean(profile.scholarshipNeeded),preferred_teaching_language:profile.teachingLanguage || null,course_interests:profile.courseInterests || null}),
    });
    if (planningProfileKey() !== profileKey || state.applicationContext.target_school !== targetSchool || state.advisorLoading) return;
    state.advisorPlan = plan;
    state.planningPlanProfileKey = profileKey;
    renderRecommendedMatches();
    renderPlanningNextAction();
    initIcons();
  } catch (_) {
    // Keep the explicit retry link; a reload may retry this rules-only request.
  }
}

function renderApplicationJourney() {
  window.UniWayApplicationWorkspace?.render();
}

function planningContextKey() {
  return JSON.stringify([state.account?.id, workflowContextKey(state.applicationContext.target_school), state.applicationContext.program_type, state.applicationContext.semester, state.eligibilityProfile?.targetTerm]);
}

function planningPreviewAllowed() {
  const partner = partnerByName(state.applicationContext.target_school);
  return Boolean(state.account && partner && !partnerAvailabilityMeta(partner).blocked
    && (partnerAvailabilityMeta(partner).pending || calendarTaskFeatureEnabled()));
}

function renderPlanningWorkspace() {
  const summary = $("#planning-target-summary");
  if (!summary) return;
  const target = state.applicationContext.target_school;
  summary.innerHTML = target
    ? `<i data-lucide="school" aria-hidden="true"></i><div><small>本次規劃目標</small><strong>${escapeHtml(target)}</strong></div><a href="#application-center">修改申請設定</a>`
    : '<i data-lucide="route" aria-hidden="true"></i><div><strong>先確認你的目標學校</strong><small>從選校推薦按「選為目標」，或到申請文件設定已有的目標學校。</small></div><a href="#advisor">查看推薦</a>';
  const allowed = planningPreviewAllowed();
  $("#planning-preview-button").disabled = !allowed || state.planningLoading;
  if (state.planningLoading) $("#planning-preview-button").setAttribute("aria-busy", "true");
  else $("#planning-preview-button").removeAttribute("aria-busy");
  if (document.activeElement?.closest("#planning-schedule-form") === null) {
    $("#planning-academic-year").value = state.applicationContext.academic_year || "";
    $("#planning-application-round").value = state.applicationContext.application_round || "";
  }
  renderApplicationPeriodOptions();
  if (state.planningPreview?.key !== planningContextKey()) state.planningPreview = null;
  if (!state.planningPreview && !state.planningLoading) {
    $("#planning-schedule-preview").replaceChildren();
    $("#planning-confirm").hidden = true;
    $("#planning-update-durations").hidden = true;
    $("#planning-schedule-recovery").hidden = true;
    $("#planning-schedule-status").textContent = !target ? "選定目標後，就能預覽時程。"
      : partnerAvailabilityMeta(partnerByName(target)).pending ? "本期名額待核實，可預覽參考流程；確認前不會加入截止提醒。"
      : !calendarTaskFeatureEnabled() ? "目前帳號尚未開放自動準備安排；仍可在日曆手動建立任務並查看官方期限。"
      : "填寫申請學年度與準備天數，先預覽，再加入你的日曆。";
  }
  initIcons();
}

async function selectPlanningTarget(schoolName) {
  if ($("#planning-target-change-dialog").open) return;
  const match = state.planningPlanProfileKey === planningProfileKey() ? state.advisorPlan?.recommendations?.find(item=>item.school_name === schoolName) : null;
  if (match && recommendationStatus(match).blocked) { announce("目前條件不符，請先核對資格或調整條件。", "info"); return; }
  if (!requireAccountForPrivateAction("登入後才能保存目標學校。")) return;
  const owner = state.account.id;
  const homeSchool = activeHomeSchool();
  const partner = partnerByName(schoolName);
  if (!partner || partnerAvailabilityMeta(partner).blocked) {
    announce("這所學校當期開放仍待確認，請先核對官方資料。", "error");
    return;
  }
  if (!await confirmPlanningTargetChange(schoolName) || state.account?.id !== owner || activeHomeSchool() !== homeSchool) return;
  if (state.applicationContext.target_school !== schoolName) {
    state.planningRequestId += 1;
    state.planningLoading = false;
    state.planningPreview = null;
    invalidateAllApplicationReviews();
    state.applicationContext = { ...state.applicationContext, school_name: activeHomeSchool(), target_school: schoolName, target_country: partner.country || "", program_type: "exchange", college:state.eligibilityProfile?.college || state.applicationContext.college || "", department:state.eligibilityProfile?.department || state.applicationContext.department || "", degree_level:state.eligibilityProfile?.degree || state.applicationContext.degree_level || "" };
    if (!state.applications.has(schoolName)) toggleApplication(schoolName);
    persistApplicationContext();
    restoreApplicationContextForm();
    await loadApplicationTemplates();
  }
  if (state.account?.id !== owner || activeHomeSchool() !== homeSchool || state.applicationContext.target_school !== schoolName) return;
  renderPersonalPlanSnapshot();
  renderRecommendedMatches();
  window.location.hash = "#overview";
  announce("已設定目標學校，請依下一步提示確認資格與安排時程。", "success");
}

async function previewPlanningSchedule(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!form.reportValidity() || state.planningLoading || !planningPreviewAllowed()) return;
  const partner = partnerByName(state.applicationContext.target_school);
  if (!partner || partnerAvailabilityMeta(partner).blocked) return;
  const days = Number(form.elements.preparation_days.value);
  if (!Number.isInteger(days) || days < 1 || days > 90) return;
  const academicYear = form.elements.academic_year.value.trim();
  const round = form.elements.application_round.value.trim();
  if (academicYear !== state.applicationContext.academic_year || round !== (state.applicationContext.application_round || "")) {
    invalidateAllApplicationReviews();
    state.applicationContext.academic_year = academicYear;
    state.applicationContext.application_round = round;
    persistApplicationContext();
    restoreApplicationContextForm();
  }
  const key = planningContextKey();
  const requestId = ++state.planningRequestId;
  state.planningLoading = true;
  $("#planning-schedule-recovery").hidden = true;
  state.planningPreview = null;
  renderPlanningWorkspace();
  $("#planning-schedule-preview").replaceChildren();
  $("#planning-confirm").hidden = true;
  $("#planning-update-durations").hidden = true;
  $("#planning-schedule-status").textContent = "正在核對目標學校的官方期限…";
  $("#planning-preview-button").setAttribute("aria-busy", "true");
  try {
    const workflow = await fetchJson(`/application-workflow?${workflowRequestParams(partner).toString()}`, { cache: "no-store" });
    if (requestId !== state.planningRequestId || key !== planningContextKey()) return;
    if (partnerAvailabilityMeta(partner).pending && workflow.school_name === partner.school_name
      && workflow.home_university === activeHomeSchool() && String(workflow.academic_year || "").trim() === academicYear
      && (!round || workflow.application_round === round || (workflow.effective_application_rounds || []).includes(round))) {
      state.planningPreview = {key, days, events:[], report:{items:[]}, referenceOnly:true};
      $("#planning-schedule-preview").innerHTML = workflow.steps.map(step=>`<article class="planning-timeline-item"><span class="planning-timeline-icon"><i data-lucide="clipboard-list" aria-hidden="true"></i></span><div><strong>${escapeHtml(step.title)}</strong><p>${escapeHtml(step.details?.[0] || "此階段條件須依當期官方通知確認。")}</p>${safeSourceUrl(step.source_urls?.[0]) ? `<a href="${escapeHtml(safeSourceUrl(step.source_urls[0]))}" target="_blank" rel="noreferrer">核對官方來源</a>` : ""}</div></article>`).join("");
      $("#planning-schedule-status").textContent = "已顯示參考流程。本期名額與合作校條件尚待確認；這次預覽不會加入日曆或啟用截止提醒。";
      initIcons();
      return;
    }
    if (workflow.school_name !== partner.school_name || workflow.home_university !== activeHomeSchool()
      || workflow.review_status !== "published" || workflow.applicability_status !== "verified"
      || String(workflow.academic_year || "").trim() !== academicYear
      || (round && workflow.application_round !== round && !(workflow.effective_application_rounds || []).includes(round))) {
      throw new Error("這個學年度／梯次的流程尚未確認適用，請先核對官方公告；目前不會自動安排日期。");
    }
    const deadlines = workflowDeadlineEvents([workflow]).filter(item=>item.date >= localDateKey() && /^https?:\/\//i.test(item.sourceUrl));
    if (!deadlines.length) throw new Error("目前沒有已確認、有來源且尚未過期的截止日。請先確認官方期限，再手動加入日曆。");
    const durationKey = JSON.stringify([key,days]);
    const overrides = state.planningDurations?.key === durationKey ? state.planningDurations.values : {};
    const events = await Promise.all(deadlines.map(async item=>{
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${activeHomeSchool()}|${item.id}`));
      const id = `preparation-${Array.from(new Uint8Array(digest)).slice(0,16).map(byte=>byte.toString(16).padStart(2,"0")).join("")}`;
      const existing = state.calendarEvents.find(event=>event.id === id);
      return existing || { ...item, id, title:`準備：${item.title}`.slice(0,120), origin:"personal", preparationDays:overrides[id] || days, status:"todo", note:`依官方截止日安排；準備天數 ${overrides[id] || days} 天由你設定。${item.note}`.slice(0,1000) };
    }));
    const report = await fetchJson("/calendar/tasks/schedule", {
      method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({events:events.map(workspaceCalendarEventPayload)}),
    });
    if (requestId !== state.planningRequestId || key !== planningContextKey()) return;
    state.planningPreview = { key, days, events, report };
    state.planningDurations = { key:durationKey, values:Object.fromEntries(events.map(item=>[item.id,item.preparationDays])) };
    $("#planning-schedule-preview").innerHTML = (report.items || []).map(item=>{
      const source = events.find(event=>event.id === item.event_id);
      const saved = state.calendarEvents.some(event=>event.id === source?.id);
      return `<article class="planning-timeline-item"><span class="planning-timeline-icon"><i data-lucide="calendar-check" aria-hidden="true"></i></span><div><strong>${escapeHtml(item.title)}</strong><div class="planning-date-pair"><span>建議開始 <time>${escapeHtml(item.suggested_start_date)}</time></span><span>官方截止 <time>${escapeHtml(item.deadline_date)}</time></span></div><p>${escapeHtml(item.reason)}</p><label class="planning-task-duration"><span>這項任務預留</span><input type="number" min="1" max="90" required value="${source?.preparationDays || days}" data-planning-duration="${escapeHtml(item.event_id)}" aria-label="${escapeHtml(item.title)}準備天數" ${saved ? "disabled" : ""} /><span>天${saved ? " · 已保存，保留原設定" : ""}</span></label>${source?.sourceUrl ? `<a href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noreferrer">核對官方來源<i data-lucide="external-link" aria-hidden="true"></i></a>` : ""}</div></article>`;
    }).join("");
    const existingCount = events.filter(event=>state.calendarEvents.some(saved=>saved.id === event.id)).length;
    $("#planning-schedule-status").textContent = `已整理 ${report.items.length} 項準備安排，尚未加入日曆。${existingCount ? `其中 ${existingCount} 項已存在，保留原有天數與進度。` : ""}`;
    $("#planning-confirm").hidden = !report.items.length;
    $("#planning-update-durations").hidden = !report.items.length;
    initIcons();
  } catch (error) {
    if (requestId === state.planningRequestId && key === planningContextKey()) { $("#planning-schedule-status").textContent = error.message; renderPlanningRecovery(); }
  } finally {
    if (requestId === state.planningRequestId) {
      state.planningLoading = false;
      $("#planning-preview-button").disabled = !planningPreviewAllowed();
      $("#planning-preview-button").removeAttribute("aria-busy");
    }
  }
}

async function confirmPlanningSchedule() {
  const preview = state.planningPreview;
  if (preview?.needsRefresh) { announce("請先更新準備天數的預覽。", "info"); return; }
  if (!calendarTaskFeatureEnabled() || !preview || preview.key !== planningContextKey()
    || preview.days !== Number($("#planning-preparation-days").value)
    || $("#planning-academic-year").value.trim() !== state.applicationContext.academic_year
    || $("#planning-application-round").value.trim() !== (state.applicationContext.application_round || "")
    || preview.events.some(event=>event.date < localDateKey())) {
    announce("條件或準備天數已改變，請重新預覽時程。", "info");
    return;
  }
  const ids = new Set(state.calendarEvents.map(event=>event.id));
  const added = preview.events.filter(event=>!ids.has(event.id));
  state.calendarEvents.push(...added);
  persistCalendarEvents();
  await loadCalendarTaskSchedule();
  renderApplicationCalendar();
  renderApplicationJourney();
  renderPlanningNextAction();
  initIcons();
  $("#planning-confirm").hidden = true;
  $("#planning-schedule-status").textContent = added.length ? `已加入 ${added.length} 項準備任務，可到日曆追蹤進度。` : "這些準備任務已在日曆中，沒有重複加入。";
  announce(added.length ? "準備時程已加入日曆" : "已保留原有時程", "success");
}

function renderDecisionBrief() {
  if (!$("#decision-brief-grid")) return;
  const documents = state.dashboard.document_explanations || state.dashboard.rule_explanations || [];
  const recentRule = documents[0];
  const profile = state.eligibilityProfile;
  const eligibility = eligibilitySummary();
  const deadlines = upcomingDeadlines();
  const checklist = documentChecklistItems();
  const missingDocuments = checklist.filter((item) => readinessStatus(item.id) !== "ready");
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
      detail: checklist.length ? (missingDocuments[0]?.title || "目前列出的文件都已標記完成。") : "先查看官方文件摘要與適用條件。",
      href: "#documents",
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
  const academicPass = homeAcademicPass(profile);
  const languagePass = threshold ? profile.languageScore >= threshold.minimum : false;
  return {
    likely,
    review,
    qualificationLabel: activeUniversityProfile().id === "tku" ? "淡江須依語組、學制、梯次及官方矛盾項確認資格" : homeSelectionRules().language_certificate_required ? "校內正式語檢及外校條件仍須核對" : academicPass && languagePass ? (activeHomeSchool() === "國立臺灣大學" ? "所填成績與英語分數達基本門檻" : `符合${activeUniversityProfile().short_name}基本門檻`) : "仍有基本條件要確認",
  };
}

function upcomingDeadlines(limit = 3) {
  const today = localDateKey();
  return workflowDeadlineEvents()
    .filter((event) => event.date >= today)
    .sort((left, right) => left.date.localeCompare(right.date) || left.title.localeCompare(right.title, "zh-Hant"))
    .slice(0, limit)
    .map((event) => ({
      date: parseLocalDate(event.date),
      original: event.note,
      title: event.title,
      scope: calendarCategory(event.category).label,
      schoolName: event.schoolName,
      source: { source_url: event.sourceUrl },
    }));
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
  return workflowDeadlineEvents();
}

function structuredWorkflowDateKey(value) {
  if (!value) return "";
  const direct = String(value || "").match(/^(\d{4}-\d{2}-\d{2})/);
  if (direct) return parseLocalDate(direct[1]) ? direct[1] : "";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "" : localDateKey(parsed);
}

function workflowDeadlineEvents(workflows = state.workflowCache.values()) {
  const events = [];
  for (const workflow of workflows) {
    (workflow.steps || []).forEach((step) => {
      if (step.deadline_status !== "verified_exact" || !step.deadline_reminder_eligible) {
        return;
      }
      const submission = step.submission || {};
      const method = submission.method || "unknown";
      const paperFlow = method === "paper" || method === "mixed";
      const sourceUrl = step.deadline_source_url || "";
      const addEvent = ({ value, kind, label, note, category = "documents" }) => {
        const date = structuredWorkflowDateKey(value);
        if (!date) return;
        events.push({
          id: `workflow-${workflow.workflow_id || workflow.school_name}-${step.rule_id || step.order}-${kind}-${date}`,
          title: `${workflow.school_name}：${step.title}（${label}）`,
          date,
          category,
          reminderDays: 7,
          note: submission.deadline_note ? `${note} ${submission.deadline_note}` : note,
          sourceUrl,
          schoolName: workflow.school_name,
          origin: "official",
        });
      };

      if (paperFlow) {
        addEvent({
          value: submission.arrival_deadline_at,
          kind: "arrival",
          label: "紙本送達期限",
          note: "紙本文件必須在此日前送達指定收件單位；不要只以寄出日期判斷。",
        });
        addEvent({
          value: submission.send_by_at,
          kind: "send",
          label: "最晚寄出",
          note: "這是官方明確標示的最晚寄出時間；紙本送達期限仍應分開核對。",
        });
        return;
      }

      addEvent({
        value: submission.arrival_deadline_at || step.deadline_at,
        kind: "deadline",
        label: "步驟截止",
        note: "請在此期限前完成這個申請步驟，送件前再次核對官方公告。",
        category: method === "online" || method === "email" ? "partner" : "home",
      });
    });
  }
  return events;
}

function allApplicationCalendarEvents() {
  const combined = [...officialCalendarEvents(), ...state.calendarEvents]
    .filter((event) => parseLocalDate(event.date) && event.title)
    .sort((left, right) => left.date.localeCompare(right.date) || left.title.localeCompare(right.title, "zh-Hant"));
  const seen = new Set();
  return combined.filter((event) => {
    const key = `${event.origin}|${event.schoolName || ""}|${event.id || `${event.title}|${event.date}`}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function notificationPreferences() {
  return state.account?.notification_preferences || {
    deadline_reminder_days: [30, 14, 7, 3, 1],
    web_enabled: true,
    email_enabled: false,
    push_enabled: false,
    content_updates_enabled: true,
  };
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
  const configuredDays = state.account
    ? notificationPreferences().deadline_reminder_days
    : [Math.max(0, Number(event.reminderDays) || 0)];
  const alarms = configuredDays.flatMap((days) => [
    "BEGIN:VALARM",
    `TRIGGER:${days ? `-P${days}D` : "PT0M"}`,
    "ACTION:DISPLAY",
    `DESCRIPTION:${escapeIcs(event.title)}`,
    "END:VALARM",
  ]);
  return [
    "BEGIN:VEVENT",
    `UID:${escapeIcs(event.id)}@exchange-guide.local`,
    `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "")}`,
    `DTSTART;VALUE=DATE:${start}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${escapeIcs(`[交換申請] ${event.title}`)}`,
    `DESCRIPTION:${escapeIcs(calendarEventDescription(event))}`,
    event.sourceUrl ? `URL:${escapeIcs(event.sourceUrl)}` : "",
    ...alarms,
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
  const generated = Boolean(event.generatedFromEventId || event.generated_from_event_id);
  const completed = event.status === "ready";
  const conflicting = calendarConflictingEventIds().has(String(event.id));
  const statusLabels = { todo: "未開始", preparing: "準備中", ready: "已完成" };
  return `
    <article class="calendar-agenda-item tone-${category.tone}${completed ? " is-completed" : ""}${generated ? " is-generated" : ""}">
      <span class="calendar-agenda-icon"><i data-lucide="${category.icon}" aria-hidden="true"></i></span>
      <div class="calendar-agenda-copy">
        <span class="calendar-agenda-meta"><strong>${escapeHtml(category.label)}</strong><time datetime="${escapeHtml(event.date)}">${escapeHtml(formatCalendarDate(event.date))}</time><small>${escapeHtml(calendarCountdownLabel(event.date))}</small>${event.schoolName ? `<small>${escapeHtml(event.schoolName)}</small>` : ""}${Number(event.preparationDays || 0) > 0 ? `<small>準備 ${escapeHtml(event.preparationDays)} 天</small>` : ""}${completed ? `<small class="calendar-completed-badge"><i data-lucide="circle-check-big" aria-hidden="true"></i>${statusLabels.ready}</small>` : ""}${conflicting ? '<small class="calendar-conflict-badge"><i data-lucide="triangle-alert" aria-hidden="true"></i>多計畫衝突</small>' : ""}</span>
        <h3>${escapeHtml(event.title)}</h3>
        ${event.note ? `<p>${escapeHtml(truncate(event.note, 100))}</p>` : ""}
        <div class="calendar-agenda-actions">
          <a href="${escapeHtml(googleCalendarUrl(event))}" target="_blank" rel="noreferrer" class="calendar-action-link"><i data-lucide="calendar-plus" aria-hidden="true"></i><span>Google 日曆</span></a>
          <button type="button" class="calendar-action-link" data-download-calendar-event="${escapeHtml(event.id)}"><i data-lucide="download" aria-hidden="true"></i><span>Apple／其他</span></button>
          ${official && event.sourceUrl ? `<a href="${escapeHtml(event.sourceUrl)}" target="_blank" rel="noreferrer" class="calendar-action-link"><i data-lucide="external-link" aria-hidden="true"></i><span>來源</span></a>` : ""}
          ${!official && !generated ? `<label class="calendar-task-status"><span class="visually-hidden">${escapeHtml(event.title)}狀態</span><select data-calendar-task-status="${escapeHtml(event.id)}" aria-label="${escapeHtml(event.title)}狀態"><option value="todo" ${event.status !== "preparing" && event.status !== "ready" ? "selected" : ""}>未開始</option><option value="preparing" ${event.status === "preparing" ? "selected" : ""}>準備中</option><option value="ready" ${event.status === "ready" ? "selected" : ""}>已完成</option></select></label>` : ""}
          ${official ? '<span class="official-event-label"><i data-lucide="badge-check" aria-hidden="true"></i>官方日期</span>' : generated ? '<span class="official-event-label calendar-generated-label"><i data-lucide="sparkles" aria-hidden="true"></i>系統安排</span>' : `<button type="button" class="calendar-action-link danger" data-delete-calendar-event="${escapeHtml(event.id)}"><i data-lucide="trash-2" aria-hidden="true"></i><span>刪除</span></button>`}
        </div>
      </div>
    </article>`;
}

function renderDeadlineReminderCenter(events) {
  const container = $("#deadline-reminder-center");
  if (!container) return;
  if (!state.account) {
    container.innerHTML = '<article><i data-lucide="bell" aria-hidden="true"></i><div><strong>登入後開啟基本截止提醒</strong><small>公開資訊仍可完整瀏覽；登入後才會同步你的提醒設定。</small></div></article>';
    return;
  }
  const preferences = notificationPreferences();
  if (!preferences.web_enabled) {
    container.innerHTML = '<article><i data-lucide="bell-off" aria-hidden="true"></i><div><strong>Web 站內提醒已關閉</strong><small>可從個人設定重新開啟或調整提醒日。</small></div></article>';
    return;
  }
  const days = preferences.deadline_reminder_days || [];
  const alerts = events.filter((event) => days.includes(calendarDaysUntil(event.date)));
  if (alerts.length) {
    container.innerHTML = alerts.slice(0, 5).map((event) => `<article class="is-alert"><i data-lucide="bell-ring" aria-hidden="true"></i><div><strong>${escapeHtml(calendarCountdownLabel(event.date))}：${escapeHtml(event.title)}</strong><small>${escapeHtml(event.note || "請確認文件與送件方式。")}</small></div></article>`).join("");
    return;
  }
  const schedule = days.length ? days.map((day) => `${day} 天`).join("、") : "未設定";
  container.innerHTML = `<article><i data-lucide="bell" aria-hidden="true"></i><div><strong>目前沒有今天觸發的截止提醒</strong><small>已設定在截止前 ${escapeHtml(schedule)}顯示站內提醒。</small></div></article>`;
}

function calendarConflictFeatureEnabled() {
  return Boolean(state.account && entitlementFeatureEnabled("application_plan_conflicts"));
}

function calendarConflictEligibleEvents() {
  const today = localDateKey();
  return allApplicationCalendarEvents().filter(
    (event) => event.date >= today && String(event.schoolName || "").trim(),
  );
}

function calendarConflictingEventIds() {
  return new Set(
    (state.calendarConflictReport?.groups || []).flatMap((group) =>
      (group.events || []).map((event) => String(event.id)),
    ),
  );
}

function calendarConflictDates() {
  return new Set(
    (state.calendarConflictReport?.groups || []).flatMap((group) => [
      group.start_date,
      group.end_date,
    ]),
  );
}

function emptyCalendarConflictReport(events = []) {
  const schools = new Set(events.map((event) => event.schoolName).filter(Boolean));
  return {
    analyzed_event_count: events.length,
    plan_count: schools.size,
    conflict_count: 0,
    conflicting_event_count: 0,
    same_day_conflict_count: 0,
    tight_window_conflict_count: 0,
    groups: [],
  };
}

function renderCalendarPlanOptions() {
  const select = $("#calendar-event-school");
  if (!select) return;
  const current = select.value;
  const schools = [...state.applications].sort((left, right) => left.localeCompare(right, "zh-Hant"));
  select.innerHTML = [
    '<option value="">一般任務（不納入多計畫衝突）</option>',
    ...schools.map((school) => `<option value="${escapeHtml(school)}">${escapeHtml(school)}</option>`),
  ].join("");
  if (schools.includes(current)) select.value = current;
}

function renderCalendarConflictCenter() {
  renderCalendarInsightsSummary();
  const container = $("#calendar-conflict-center");
  const summary = $("#calendar-conflict-summary");
  const list = $("#calendar-conflict-list");
  if (!container || !summary || !list) return;
  if (!calendarConflictFeatureEnabled()) {
    container.hidden = true;
    return;
  }
  container.hidden = false;
  if (state.calendarConflictLoading) {
    summary.textContent = "正在核對多份申請計畫的已確認日期。";
    list.innerHTML = '<div class="skeleton skeleton-card"></div>';
    return;
  }
  if (state.calendarConflictError) {
    summary.textContent = "暫時無法完成衝突核對。";
    list.innerHTML = `<article class="calendar-conflict-empty"><i data-lucide="cloud-off" aria-hidden="true"></i><span><strong>請稍後再試</strong><small>${escapeHtml(state.calendarConflictError)}</small></span></article>`;
    initIcons();
    return;
  }
  const report = state.calendarConflictReport || emptyCalendarConflictReport();
  if (report.plan_count < 2) {
    summary.textContent = "至少需要兩份申請計畫各自有日期，系統才會進行跨校衝突核對。";
    list.innerHTML = '<article class="calendar-conflict-empty"><i data-lucide="calendar-range" aria-hidden="true"></i><span><strong>尚無跨計畫衝突可核對</strong><small>新增任務時選擇所屬申請學校；一般任務不會被誤判為跨校衝突。</small></span></article>';
    initIcons();
    return;
  }
  if (!report.conflict_count) {
    summary.textContent = `已核對 ${report.plan_count} 份計畫、${report.analyzed_event_count} 個已確認日期。`;
    list.innerHTML = '<article class="calendar-conflict-empty is-clear"><i data-lucide="calendar-check-2" aria-hidden="true"></i><span><strong>目前沒有 3 天內的跨計畫衝突</strong><small>只分析你已儲存或官方已確認的日期，不會推測尚未公告的期限。</small></span></article>';
    initIcons();
    return;
  }
  summary.textContent = `偵測到 ${report.conflict_count} 組衝突，影響 ${report.conflicting_event_count} 個任務；同日 ${report.same_day_conflict_count} 組、3 天內 ${report.tight_window_conflict_count} 組。`;
  list.innerHTML = report.groups.map((group) => {
    const sameDay = group.kind === "same_day";
    const dateLabel = sameDay
      ? formatCalendarDate(group.start_date, { year: "numeric", month: "long", day: "numeric" })
      : `${formatCalendarDate(group.start_date)}－${formatCalendarDate(group.end_date)}（相距 ${group.day_gap} 天）`;
    return `<article class="calendar-conflict-card ${sameDay ? "is-same-day" : ""}">
      <div class="calendar-conflict-card-heading"><span><i data-lucide="triangle-alert" aria-hidden="true"></i><strong>${sameDay ? "同一天有多校任務" : "多校任務間隔過近"}</strong></span><button type="button" class="text-action" data-calendar-conflict-date="${escapeHtml(group.start_date)}">查看日期</button></div>
      <time datetime="${escapeHtml(group.start_date)}">${escapeHtml(dateLabel)}</time>
      <p class="calendar-conflict-schools">${group.school_names.map(escapeHtml).join("、")}</p>
      <ul>${group.events.map((event) => `<li><time datetime="${escapeHtml(event.date)}">${escapeHtml(event.date)}</time><span>${escapeHtml(event.title)}</span></li>`).join("")}</ul>
      <small>${escapeHtml(group.resolution_hint)}</small>
    </article>`;
  }).join("");
  initIcons();
}

function ensureApplicationCalendarWorkflows() {
  if (!state.dashboard) return;
  [...state.applications].forEach((schoolName) => {
    const item = partnerByName(schoolName);
    if (!item) return;
    const cacheKey = workflowContextKey(schoolName);
    if (state.workflowCache.has(cacheKey) || state.calendarWorkflowAttempts.has(cacheKey)) return;
    state.calendarWorkflowAttempts.add(cacheKey);
    const params = workflowRequestParams(item);
    fetchJson(`/application-workflow?${params.toString()}`)
      .then((workflow) => {
        state.workflowCache.set(cacheKey, workflow);
        renderApplicationCalendar();
        scheduleCalendarConflictAnalysis();
        scheduleCalendarTaskAnalysis();
        if (calendarSyncFeatureEnabled() && state.calendarSync?.enabled) syncCalendarEvents({ quiet: true });
      })
      .catch(() => {
        // The calendar keeps personal tasks available; a normal workflow refresh can retry later.
      });
  });
}

async function loadCalendarConflicts() {
  window.clearTimeout(state.calendarConflictTimer);
  const requestSequence = ++state.calendarConflictRequestSequence;
  if (!calendarConflictFeatureEnabled()) {
    state.calendarConflictLoading = false;
    state.calendarConflictError = "";
    state.calendarConflictReport = null;
    renderCalendarConflictCenter();
    return;
  }
  const events = calendarConflictEligibleEvents();
  const schools = new Set(events.map((event) => event.schoolName).filter(Boolean));
  if (schools.size < 2) {
    state.calendarConflictLoading = false;
    state.calendarConflictError = "";
    state.calendarConflictReport = emptyCalendarConflictReport(events);
    renderCalendarConflictCenter();
    renderApplicationCalendar();
    return;
  }
  state.calendarConflictLoading = true;
  state.calendarConflictError = "";
  renderCalendarConflictCenter();
  try {
    const report = await fetchJson("/calendar/conflicts/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: events.map(workspaceCalendarEventPayload) }),
    });
    if (requestSequence !== state.calendarConflictRequestSequence) return;
    state.calendarConflictReport = report;
  } catch (error) {
    if (requestSequence !== state.calendarConflictRequestSequence) return;
    state.calendarConflictReport = null;
    state.calendarConflictError = error.message;
  } finally {
    if (requestSequence === state.calendarConflictRequestSequence) {
      state.calendarConflictLoading = false;
      renderCalendarConflictCenter();
      renderApplicationCalendar();
    }
  }
}

function scheduleCalendarConflictAnalysis() {
  window.clearTimeout(state.calendarConflictTimer);
  state.calendarConflictTimer = window.setTimeout(loadCalendarConflicts, 160);
}

function calendarTaskFeatureEnabled() {
  return Boolean(state.account && entitlementFeatureEnabled("smart_reminders"));
}

function calendarTaskEligibleEvents() {
  return (state.planningAvailability ? state.calendarEvents : allApplicationCalendarEvents()).filter(
    (event) => (Number(event.preparationDays || 0) > 0 || Number(event.effortHours || 0) > 0 || event.dependsOn?.length) && !event.generatedFromEventId,
  );
}

function emptyCalendarTaskScheduleReport() {
  return {
    as_of: localDateKey(),
    analyzed_event_count: 0,
    incomplete_count: 0,
    scheduled_count: 0,
    start_now_count: 0,
    due_soon_count: 0,
    overdue_count: 0,
    completed_count: 0,
    items: [],
  };
}

function scheduledPreparationEvents() {
  const report=state.calendarTaskScheduleReport;
  if (report?.mode === "workload") {
    return (report.work_sessions || []).map(session=>{
      const task=report.items.find(row=>row.event_id === session.event_id);
      return {id:`work-${session.event_id}-${session.date}-${session.sequence}`,
        title:`準備：${task?.title || "申請工作"} · ${Number(session.hours).toLocaleString("zh-TW")} 小時`,
        date:session.date, category:"documents", reminderDays:0, preparationDays:0,
        status:task?.status || "todo", note:"依個人可用時間安排的工作；不是官方送件期限。",
        schoolName:task?.school_name || "", origin:"personal", generatedFromEventId:session.event_id};
    });
  }
  return (state.calendarTaskScheduleReport?.items || [])
    .filter((item) => item.urgency !== "completed" && item.suggested_start_date)
    .map((item) => ({
      id: `schedule-start-${item.event_id}`,
      title: `開始準備：${item.title}`,
      date: item.suggested_start_date,
      category: "documents",
      reminderDays: 0,
      preparationDays: 0,
      status: item.status,
      note: item.reason,
      schoolName: item.school_name || "",
      origin: "personal",
      generatedFromEventId: item.event_id,
    }));
}

function calendarDisplayEvents() {
  return [...allApplicationCalendarEvents(), ...scheduledPreparationEvents()]
    .filter((event) => parseLocalDate(event.date) && event.title)
    .sort((left, right) => left.date.localeCompare(right.date) || left.title.localeCompare(right.title, "zh-Hant"));
}

function renderCalendarTaskScheduleCenter() {
  const container = $("#calendar-task-schedule-center");
  const summary = $("#calendar-task-schedule-summary");
  const list = $("#calendar-task-schedule-list");
  if (!container || !summary || !list) return;
  if (!calendarTaskFeatureEnabled()) {
    container.hidden = true;
    return;
  }
  container.hidden = false;
  if (state.calendarTaskScheduleLoading) {
    summary.textContent = "正在依你設定的準備天數安排開始日。";
    list.innerHTML = '<div class="skeleton skeleton-card"></div>';
    return;
  }
  if (state.calendarTaskScheduleError) {
    summary.textContent = "暫時無法更新任務安排。";
    list.innerHTML = `<article class="calendar-task-schedule-empty"><i data-lucide="cloud-off" aria-hidden="true"></i><span><strong>請稍後再試</strong><small>${escapeHtml(state.calendarTaskScheduleError)}</small></span></article>`;
    initIcons();
    return;
  }
  const report = state.calendarTaskScheduleReport || emptyCalendarTaskScheduleReport();
  if (!report.analyzed_event_count) {
    summary.textContent = "新增任務時填寫預估準備天數，系統才會倒推開始日。";
    list.innerHTML = '<article class="calendar-task-schedule-empty"><i data-lucide="list-start" aria-hidden="true"></i><span><strong>尚未設定可安排的任務</strong><small>準備天數由你輸入；系統不會猜測文件工期或官方期限。</small></span></article>';
    initIcons();
    return;
  }
  summary.textContent = `已安排 ${report.analyzed_event_count} 項；應開始 ${report.start_now_count}、3 天內到期 ${report.due_soon_count}、逾期未完成 ${report.overdue_count}、已完成 ${report.completed_count}。`;
  const urgencyMeta = {
    overdue: ["逾期未完成", "circle-alert"],
    due_soon: ["3 天內到期", "alarm-clock"],
    start_now: ["現在應開始", "play"],
    scheduled: ["已安排開始日", "calendar-check"],
    completed: ["已完成", "circle-check-big"],
    blocked: ["先處理阻礙", "circle-alert"],
  };
  list.innerHTML = report.items.map((item) => {
    const [label, icon] = urgencyMeta[item.urgency] || urgencyMeta.scheduled;
    return `<article class="calendar-task-schedule-card urgency-${escapeHtml(item.urgency)}">
      <div class="calendar-task-schedule-heading"><span><i data-lucide="${icon}" aria-hidden="true"></i><strong>${escapeHtml(label)}</strong></span><span class="calendar-task-schedule-links">${item.suggested_start_date ? `<button type="button" class="text-action" data-calendar-task-date="${escapeHtml(item.suggested_start_date)}">查看開始日</button>` : ""}${item.deadline_date ? `<button type="button" class="text-action" data-calendar-task-deadline="${escapeHtml(item.deadline_date)}">查看期限</button>` : ""}</span></div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${item.school_name ? `${escapeHtml(item.school_name)} · ` : ""}${report.mode === "workload" ? `已安排 ${Number(item.scheduled_hours || 0).toLocaleString("zh-TW")} 小時` : `準備 ${item.preparation_days} 天`}</p>
      <dl><div><dt>建議開始</dt><dd>${escapeHtml(item.suggested_start_date || "待安排")}</dd></div><div><dt>${item.deadline_kind === "official" ? "來源期限" : "個人完成目標"}</dt><dd>${escapeHtml(item.deadline_date || "尚未設定")}</dd></div></dl>
      <small>${escapeHtml(item.reason)}</small>
    </article>`;
  }).join("");
  initIcons();
}

async function loadCalendarTaskSchedule() {
  window.clearTimeout(state.calendarTaskScheduleTimer);
  const requestSequence = ++state.calendarTaskScheduleRequestSequence;
  const owner = JSON.stringify([state.account?.id, activeHomeSchool()]);
  if (!calendarTaskFeatureEnabled()) {
    state.calendarTaskScheduleLoading = false;
    state.calendarTaskScheduleError = "";
    state.calendarTaskScheduleReport = null;
    renderCalendarTaskScheduleCenter();
    return;
  }
  const events = calendarTaskEligibleEvents();
  const planRequest = window.UniWayMultiPlan.scheduleRequest();
  if (!events.length && !planRequest) {
    state.calendarTaskScheduleLoading = false;
    state.calendarTaskScheduleError = "";
    state.calendarTaskScheduleReport = emptyCalendarTaskScheduleReport();
    renderCalendarTaskScheduleCenter();
    renderApplicationCalendar();
    window.UniWayJourney.render();
    return;
  }
  state.calendarTaskScheduleLoading = true;
  state.calendarTaskScheduleError = "";
  renderCalendarTaskScheduleCenter();
  try {
    const result = await fetchJson(planRequest ? "/application-plan/schedule" : "/calendar/tasks/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(planRequest ? {...planRequest, personal_events:events.map(workspaceCalendarEventPayload)} : { events: events.map(workspaceCalendarEventPayload), availability: state.planningAvailability }),
    });
    if (requestSequence !== state.calendarTaskScheduleRequestSequence || owner !== JSON.stringify([state.account?.id, activeHomeSchool()])) return;
    state.calendarTaskScheduleReport = planRequest ? result.schedule : result;
  } catch (error) {
    if (requestSequence !== state.calendarTaskScheduleRequestSequence || owner !== JSON.stringify([state.account?.id, activeHomeSchool()])) return;
    state.calendarTaskScheduleReport = null;
    state.calendarTaskScheduleError = error.message;
  } finally {
    if (requestSequence === state.calendarTaskScheduleRequestSequence && owner === JSON.stringify([state.account?.id, activeHomeSchool()])) {
      state.calendarTaskScheduleLoading = false;
      renderCalendarTaskScheduleCenter();
      renderApplicationCalendar();
      window.UniWayJourney.render();
      if (calendarSyncFeatureEnabled() && state.calendarSync?.enabled) syncCalendarEvents({ quiet: true });
    }
  }
}

function scheduleCalendarTaskAnalysis() {
  window.clearTimeout(state.calendarTaskScheduleTimer);
  state.calendarTaskScheduleRequestSequence += 1;
  state.calendarTaskScheduleTimer = window.setTimeout(loadCalendarTaskSchedule, 180);
}

function renderCalendarInsightsSummary(events = calendarDisplayEvents()) {
  const reminderDays = state.account && notificationPreferences().web_enabled
    ? notificationPreferences().deadline_reminder_days || [] : [];
  const alerts = events.filter((event) => reminderDays.includes(calendarDaysUntil(event.date))).length;
  const conflicts = calendarConflictFeatureEnabled() ? Number(state.calendarConflictReport?.conflict_count) || 0 : 0;
  const summary = $("#calendar-insights-count");
  if (summary) summary.textContent = alerts || conflicts ? `${alerts} 項今日提醒 · ${conflicts} 組衝突` : "提醒設定 · 衝突檢查 · 準備安排";
  const brief = $("#calendar-alert-brief");
  if (brief) {
    brief.hidden = !alerts && !conflicts;
    brief.querySelector("span").textContent = [alerts ? `今天有 ${alerts} 項截止提醒` : "", conflicts ? `${conflicts} 組申請時程需要協調` : ""].filter(Boolean).join("；");
  }
}

function renderApplicationCalendar() {
  window.UniWayTracker?.render();
  const grid = $("#application-calendar-grid");
  if (!grid || !state.dashboard) return;
  ensureApplicationCalendarWorkflows();
  const events = calendarDisplayEvents();
  const currentMonth = state.calendarMonth;
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const firstDay = new Date(year, month, 1);
  const gridStart = new Date(year, month, 1 - firstDay.getDay());
  const today = localDateKey();
  const conflictDates = calendarConflictDates();
  renderCalendarPlanOptions();
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
    const hasConflict = conflictDates.has(key);
    const label = `${formatCalendarDate(key, { year: "numeric", month: "long", day: "numeric" })}${dayEvents.length ? `，${dayEvents.length} 個時程` : ""}${hasConflict ? "，有多計畫時程衝突" : ""}`;
    return `<button type="button" role="gridcell" class="calendar-day${outside ? " is-outside" : ""}${key === today ? " is-today" : ""}${key === state.calendarSelectedDate ? " is-selected" : ""}${hasConflict ? " has-plan-conflict" : ""}" data-calendar-date="${key}" aria-label="${escapeHtml(label)}" aria-pressed="${key === state.calendarSelectedDate}"><span>${date.getDate()}</span><span class="calendar-event-dots" aria-hidden="true">${tones}</span></button>`;
  }).join("");

  const futureEvents = events.filter((event) => event.date >= today);
  renderDeadlineReminderCenter(futureEvents);
  renderCalendarConflictCenter();
  renderCalendarTaskScheduleCenter();
  renderCalendarInsightsSummary(futureEvents);
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
    : `<div class="calendar-empty"><i data-lucide="calendar-check" aria-hidden="true"></i><strong>${state.calendarAgendaMode === "selected" ? "這天沒有安排" : "目前沒有近期時程"}</strong><span>${state.applicationContext.target_school ? "已選定目標，接著依官方期限預覽準備安排。" : "先選定目標，系統就能幫你安排準備時程。"}</span>${state.applicationContext.target_school ? '<button type="button" class="primary-button" data-open-planning>預覽準備時程</button>' : '<a href="#advisor" class="primary-button">填寫條件與選校</a>'}<button type="button" class="text-action" data-open-manual-task>自行建立任務</button></div>`;
  initIcons();
}

function persistCalendarEvents() {
  try {
    window.localStorage.setItem(STORAGE_KEYS.calendarEvents, JSON.stringify(state.calendarEvents));
  } catch (_) {
    announce("瀏覽器無法保存這個時程。", "error", true);
  }
  scheduleAccountWorkspaceSync();
  scheduleCalendarConflictAnalysis();
  scheduleCalendarTaskAnalysis();
  if (calendarSyncFeatureEnabled() && state.calendarSync?.enabled) syncCalendarEvents({ quiet: true });
}

function calendarSyncEventsPayload() {
  return calendarDisplayEvents().map((event) => ({
    id: String(event.id),
    title: event.title,
    date: event.date,
    category: event.category || "other",
    reminder_days: Number(event.reminderDays) || 0,
    note: event.note || "",
    source_url: event.sourceUrl || null,
    school_name: event.schoolName || null,
    preparation_days: Number(event.preparationDays) || 0,
    status: ["todo", "preparing", "ready"].includes(event.status) ? event.status : "todo",
    generated_from_event_id: event.generatedFromEventId || null,
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

function calendarSyncFeatureEnabled() {
  return Boolean(state.account && entitlementFeatureEnabled("external_calendar_sync"));
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
    button.disabled = Boolean(state.account && state.entitlements && !calendarSyncFeatureEnabled());
  });
  if (!state.account) {
    summary.textContent = "登入後可讓第三方日曆持續取得更新";
    status.innerHTML = '<span class="calendar-sync-state-icon"><i data-lucide="log-in" aria-hidden="true"></i></span><span><strong>登入後開啟訂閱同步</strong><small>你在系統新增或修改時程後，訂閱的日曆會持續取得更新。</small></span><button type="button" class="primary-button" data-open-auth>登入</button>';
    actions.replaceChildren();
    initIcons();
    return;
  }
  if (!state.entitlements) {
    summary.textContent = "正在確認方案權限";
    status.innerHTML = '<div class="skeleton skeleton-card"></div>';
    actions.replaceChildren();
    return;
  }
  if (!calendarSyncFeatureEnabled()) {
    summary.textContent = "目前方案未包含外部日曆同步";
    status.innerHTML = '<span class="calendar-sync-state-icon"><i data-lucide="lock-keyhole" aria-hidden="true"></i></span><span><strong>外部日曆同步是進階功能</strong><small>Web 站內基本截止提醒仍可使用；登入後目前免費使用，系統不會扣款。</small></span><button type="button" class="secondary-button" data-revoke-calendar-sync>撤銷舊同步網址</button>';
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
  if (!calendarSyncFeatureEnabled()) {
    announce("目前方案未包含外部日曆同步；Web 站內基本提醒仍可使用。", "error", true);
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
  if (!calendarSyncFeatureEnabled()) {
    if (!quiet) announce("目前方案未包含外部日曆同步。", "error", true);
    return;
  }
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
  if (!requireAccountForPrivateAction("新增個人申請任務需要先登入；官方日期仍可直接查看。")) {
    form.querySelector(".form-status").textContent = "登入後才會建立並同步個人任務。";
    return false;
  }
  const values = new FormData(form);
  const title = String(values.get("title") || "").trim();
  const date = String(values.get("date") || "");
  const status = form.querySelector(".form-status");
  if (!title || !parseLocalDate(date)) {
    status.textContent = "請填寫任務名稱與日期。";
    return false;
  }
  const id = window.crypto?.randomUUID?.() || `event-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  state.calendarEvents.push({
    id,
    title,
    date,
    category: String(values.get("category") || "other"),
    reminderDays: Number(values.get("reminder_days") || 0),
    preparationDays: Math.min(90, Math.max(0, Number(values.get("preparation_days")) || 0)),
    effortHours: values.get("effort_hours") ? Number(values.get("effort_hours")) : null,
    status: ["todo", "preparing", "ready"].includes(String(values.get("status"))) ? String(values.get("status")) : "todo",
    note: String(values.get("note") || "").trim(),
    schoolName: String(values.get("school_name") || "").trim(),
    origin: "personal",
  });
  state.calendarSelectedDate = date;
  state.calendarAgendaMode = "selected";
  state.calendarMonth = new Date(parseLocalDate(date).getFullYear(), parseLocalDate(date).getMonth(), 1);
  persistCalendarEvents();
  form.reset();
  form.elements.date.value = date;
  form.elements.preparation_days.value = "7";
  renderCalendarPlanOptions();
  status.textContent = "已加入你的申請日曆。";
  renderApplicationCalendar();
  announce("申請任務已加入", "success");
  return true;
}

function updateCalendarTaskStatus(eventId, status) {
  if (!requireAccountForPrivateAction("記錄任務進度需要先登入；官方日期仍可直接查看。")) {
    renderApplicationCalendar();
    return;
  }
  if (!["todo", "preparing", "ready"].includes(status)) return;
  const event = state.calendarEvents.find((item) => String(item.id) === String(eventId));
  if (!event || event.generatedFromEventId) return;
  event.status = status;
  persistCalendarEvents();
  renderApplicationCalendar();
  announce(`任務已更新為${status === "ready" ? "已完成" : status === "preparing" ? "準備中" : "未開始"}`, "success");
}

function deleteCalendarEvent(eventId) {
  if (!requireAccountForPrivateAction("修改個人申請日曆需要先登入。")) return;
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
  const loginNote = state.account
    ? ""
    : '<p class="application-plan-login-note"><i data-lucide="log-in" aria-hidden="true"></i><span>登入後才能記錄並同步文件準備狀態；文件說明仍可直接查看。</span><button type="button" class="text-action" data-open-auth>登入</button></p>';
  container.innerHTML = `
    ${loginNote}
    <div class="document-progress"><strong>${completed} / ${items.length} 已準備</strong><span>${items.filter((item) => readinessStatus(item.id) === "preparing").length} 項準備中</span></div>
    <div class="document-checklist">${items.map((item) => `
      <label>
        <input type="checkbox" class="document-readiness-checkbox" data-document-id="${escapeHtml(item.id)}" ${readinessStatus(item.id) === "ready" ? "checked" : ""} ${state.account ? "" : "disabled"} />
        <span><strong>${escapeHtml(item.title)}</strong>${item.conditional ? "<small>符合特定身分時才需要</small>" : ""}</span>
      </label>`).join("")}</div>`;
  window.UniWayGuide?.refresh();
}

function updateDocumentReadiness(documentId, checked) {
  if (!documentId) return;
  if (!requireAccountForPrivateAction("記錄文件準備狀態需要先登入；文件說明仍可直接查看。")) {
    renderDocumentReadiness();
    return;
  }
  state.documentReadiness[documentId] = checked ? "ready" : "todo";
  persistDocumentReadiness();
}

function updateDocumentStatus(documentId, status) {
  if (!documentId || !["todo", "preparing", "ready"].includes(status)) return;
  if (!requireAccountForPrivateAction("記錄文件準備狀態需要先登入；文件說明仍可直接查看。")) {
    renderDocumentWorkspace();
    return;
  }
  state.documentReadiness[documentId] = status;
  persistDocumentReadiness();
}

function persistDocumentReadiness() {
  try {
    window.localStorage.setItem(STORAGE_KEYS.documents, JSON.stringify(state.documentReadiness));
  } catch (_) {
    // Checklist remains available for this session.
  }
  scheduleAccountWorkspaceSync();
  renderDocumentReadiness();
  renderDocumentWorkspace();
  renderDecisionBrief();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
}

function renderDocumentWorkspace() {
  const container = $("#document-workspace-list");
  const progress = $("#document-workspace-progress");
  const planningStatus = $("#planning-document-status");
  if (!container || !state.dashboard) return;
  const items = documentChecklistItems();
  if (!items.length) {
    if (planningStatus) planningStatus.textContent = "尚無可追蹤的明確文件；先確認目標學校與當期官方規定。";
    container.innerHTML = '<p class="workspace-empty">目前沒有可追蹤的明確送件文件。</p>';
    if (progress) progress.textContent = "0 項";
    return;
  }
  const ready = items.filter((item) => readinessStatus(item.id) === "ready").length;
  const preparing = items.filter((item) => readinessStatus(item.id) === "preparing").length;
  if (planningStatus) planningStatus.textContent = `送件資料：${ready} / ${items.length} 項已標記完成${preparing ? `，${preparing} 項準備中` : ""}。填寫、列印與標記完成不代表已送件。`;
  if (progress) progress.textContent = `${ready} / ${items.length} 完成${preparing ? ` · ${preparing} 準備中` : ""}`;
  const loginNote = state.account
    ? ""
    : '<p class="application-plan-login-note"><i data-lucide="log-in" aria-hidden="true"></i><span>登入後才能更新並同步送件資料狀態。</span><button type="button" class="text-action" data-open-auth>登入</button></p>';
  container.innerHTML = loginNote + items.map((item) => `
    <article class="document-workspace-row status-${readinessStatus(item.id)}">
      <span class="document-workspace-icon"><i data-lucide="${readinessStatus(item.id) === "ready" ? "file-check-2" : readinessStatus(item.id) === "preparing" ? "file-clock" : "file"}" aria-hidden="true"></i></span>
      <details><summary><span><strong>${escapeHtml(item.title)}</strong>${item.conditional ? "<small>符合特定身分時才需要</small>" : ""}</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><p>${highlightHtml(item.detail)}</p></details>
      <label><span class="visually-hidden">${escapeHtml(item.title)}準備狀態</span><select data-document-status="${escapeHtml(item.id)}" ${state.account ? "" : "disabled"}><option value="todo" ${readinessStatus(item.id) === "todo" ? "selected" : ""}>未開始</option><option value="preparing" ${readinessStatus(item.id) === "preparing" ? "selected" : ""}>準備中</option><option value="ready" ${readinessStatus(item.id) === "ready" ? "selected" : ""}>已完成</option></select></label>
    </article>`).join("");
  initIcons();
}

function sharedApplicationCondition(key) {
  const values = {college:state.eligibilityProfile?.college,department:state.eligibilityProfile?.department,degree_level:state.eligibilityProfile?.degree,year_level:state.eligibilityProfile?.currentYear};
  return values[key] || "";
}

function applicationValue(template, field) {
  if (field.reusable_profile_key) {
    const remembered = state.applicationProfile?.[field.reusable_profile_key] ?? sharedApplicationCondition(field.reusable_profile_key);
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

function applicationDraftKey(templateId, homeSchool = activeHomeSchool()) {
  return `${homeSchool}::${templateId}`;
}

function activeApplicationDraft(templateId, homeSchool = activeHomeSchool()) {
  return state.applicationFormDrafts[applicationDraftKey(templateId, homeSchool)] || null;
}

function applicationDraftSafeProfile() {
  const safeKeys = new Set(
    state.applicationTemplates.flatMap((template) => template.fields)
      .filter((field) => field.reusable_profile_key && !field.sensitive && field.field_type !== "files")
      .map((field) => field.reusable_profile_key),
  );
  return Object.fromEntries(
    Object.entries(state.applicationProfile || {}).filter(([key]) => safeKeys.has(key)),
  );
}

function applicationDraftSafeAnswers(template) {
  const values = state.applicationAnswers?.[template.id] || {};
  const safeKeys = new Set(
    template.fields
      .filter((field) => !field.reusable_profile_key && !field.sensitive && field.field_type !== "files")
      .map((field) => field.id),
  );
  return Object.fromEntries(
    Object.entries(values).filter(([key]) => safeKeys.has(key)),
  );
}

function activeApplicationAttachmentLinks(templateId) {
  const fields = state.applicationFileVaultLinks?.[templateId] || {};
  const now = Date.now();
  return Object.fromEntries(
    Object.entries(fields).map(([fieldId, items]) => [
      fieldId,
      (Array.isArray(items) ? items : []).filter((item) => {
        const expiresAt = Date.parse(item.expires_at || "");
        return item.version_id && (!Number.isFinite(expiresAt) || expiresAt > now);
      }),
    ]).filter(([, items]) => items.length),
  );
}

function applicationFormDraftPayload(template, revision = null) {
  const current = activeApplicationDraft(template.id);
  return {
    home_school: activeHomeSchool(),
    template_version: template.version,
    revision: revision ?? Number(current?.revision || 0),
    profile: applicationDraftSafeProfile(),
    answers: applicationDraftSafeAnswers(template),
    attachments: activeApplicationAttachmentLinks(template.id),
  };
}

function mergeApplicationFormDraft(remote, local) {
  const attachments = { ...(remote?.attachments || {}) };
  Object.entries(local.attachments || {}).forEach(([fieldId, items]) => {
    const byVersion = new Map(
      [...(attachments[fieldId] || []), ...(items || [])]
        .filter((item) => item?.version_id)
        .map((item) => [item.version_id, item]),
    );
    attachments[fieldId] = [...byVersion.values()];
  });
  return {
    ...local,
    revision: Number(remote?.revision || 0),
    profile: { ...(remote?.profile || {}), ...(local.profile || {}) },
    answers: { ...(remote?.answers || {}), ...(local.answers || {}) },
    attachments,
  };
}

function renderApplicationDraftSyncStatus(template = applicationTemplateById(state.activeApplicationTemplateId)) {
  const container = $("#application-draft-sync-status");
  if (!container) return;
  container.className = "application-draft-sync-status";
  if (!template) {
    container.textContent = "";
    return;
  }
  const key = applicationDraftKey(template.id);
  if (!state.account) {
    container.classList.add("is-local");
    container.innerHTML = '<i data-lucide="monitor-dot" aria-hidden="true"></i><span><strong>本次分頁草稿</strong><small>登入後一般欄位才會加密同步；敏感欄位與檔案不會自動上傳。</small></span>';
  } else if (state.applicationFormDraftPending[key]) {
    container.classList.add("is-pending");
    container.innerHTML = '<i data-lucide="cloud-off" aria-hidden="true"></i><span><strong>等待同步</strong><small>一般欄位仍保留在本次分頁，恢復連線後會重試；敏感資料未上傳。</small></span>';
  } else {
    const draft = activeApplicationDraft(template.id);
    const updated = draft?.updated_at ? formatDate(draft.updated_at) : "輸入後自動保存";
    container.classList.add(draft ? "is-synced" : "is-ready");
    container.innerHTML = `<i data-lucide="${draft ? "cloud" : "cloud-upload"}" aria-hidden="true"></i><span><strong>${draft ? "一般欄位已加密同步" : "一般欄位將加密同步"}</strong><small>${escapeHtml(updated)} · 敏感欄位與檔案仍需逐次同意。</small></span>`;
  }
  initIcons();
}

function applyApplicationFormDrafts(drafts, { preserveLocal = true } = {}) {
  const localProfile = preserveLocal ? { ...(state.applicationProfile || {}) } : {};
  const remoteProfile = {};
  [...drafts].reverse().forEach((draft) => {
    state.applicationFormDrafts[applicationDraftKey(draft.template_id, draft.home_school)] = draft;
    Object.assign(remoteProfile, draft.profile || {});
    state.applicationAnswers[draft.template_id] = {
      ...(draft.answers || {}),
      ...(preserveLocal ? state.applicationAnswers?.[draft.template_id] || {} : {}),
    };
    state.applicationFileVaultLinks[draft.template_id] = Object.fromEntries(
      Object.entries(draft.attachments || {}).map(([fieldId, items]) => [
        fieldId,
        (items || []).filter((item) => !item.expires_at || Date.parse(item.expires_at) > Date.now()),
      ]),
    );
  });
  state.applicationProfile = { ...remoteProfile, ...localProfile };
  stripReusableApplicationAnswers();
}

async function loadApplicationFormDrafts({ homeSchool = activeHomeSchool() } = {}) {
  if (!state.account) return;
  const request = beginSchoolDataRequest("drafts", homeSchool);
  const accountContext = captureAuthenticatedRequestContext();
  try {
    const result = await fetchJson(`/account/application-drafts?home_school=${encodeURIComponent(homeSchool)}`);
    if (!schoolDataRequestIsCurrent(request) || !authenticatedRequestContextIsCurrent(accountContext)) return;
    state.applicationFormDraftSyncSuspended = true;
    applyApplicationFormDrafts(result.items || []);
    state.applicationFormDraftLoadedSchool = homeSchool;
    persistApplicationDraft({ syncRemote: false });
    if (state.activeApplicationTemplateId) {
      const template = applicationTemplateById(state.activeApplicationTemplateId);
      if (template && window.location.hash.startsWith("#application-form=")) renderApplicationFormPage(template);
    }
  } catch (error) {
    if (error.staleSession) return;
    if (schoolDataRequestIsCurrent(request) && authenticatedRequestContextIsCurrent(accountContext)) announce(`表單草稿同步暫時無法使用：${error.message}`, "error");
  } finally {
    if (schoolDataRequestIsCurrent(request) && authenticatedRequestContextIsCurrent(accountContext)) {
      state.applicationFormDraftSyncSuspended = false;
      renderApplicationDraftSyncStatus();
    }
  }
}

async function saveApplicationFormDraft(templateId, { payload = null, retryConflict = true } = {}) {
  const template = applicationTemplateById(templateId);
  if (!state.account || (!payload && (!template || state.applicationFormDraftSyncSuspended))) return null;
  const accountContext = captureAuthenticatedRequestContext();
  const outgoing = payload || applicationFormDraftPayload(template);
  const key = applicationDraftKey(templateId, outgoing.home_school);
  outgoing.revision = Math.max(Number(outgoing.revision || 0), Number(state.applicationFormDrafts[key]?.revision || 0));
  state.applicationFormDraftPending[key] = outgoing;
  const renderCurrent = () => {
    if (outgoing.home_school === activeHomeSchool() && authenticatedRequestContextIsCurrent(accountContext)) renderApplicationDraftSyncStatus();
  };
  renderCurrent();
  if (navigator.onLine === false) return null;
  try {
    const saved = await fetchJson(`/account/application-drafts/${encodeURIComponent(templateId)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(outgoing),
    });
    if (!authenticatedRequestContextIsCurrent(accountContext)) return null;
    if (Number(saved.revision || 0) >= Number(state.applicationFormDrafts[key]?.revision || 0)) {
      state.applicationFormDrafts[key] = saved;
      if (outgoing.home_school === activeHomeSchool()) state.applicationFileVaultLinks[templateId] = saved.attachments || {};
    }
    if (state.applicationFormDraftPending[key] === outgoing) delete state.applicationFormDraftPending[key];
    renderCurrent();
    return saved;
  } catch (error) {
    if (error.staleSession || !authenticatedRequestContextIsCurrent(accountContext)) return null;
    const current = error.payload?.detail?.current_draft;
    if (error.status === 409 && retryConflict && current && state.applicationFormDraftPending[key] === outgoing) {
      const merged = mergeApplicationFormDraft(current, outgoing);
      state.applicationFormDrafts[key] = current;
      return saveApplicationFormDraft(templateId, {
        payload: merged,
        retryConflict: false,
      });
    }
    renderCurrent();
    return null;
  }
}

function scheduleApplicationFormDraftSync(templateId = state.activeApplicationTemplateId) {
  if (!state.account || !templateId || state.applicationFormDraftSyncSuspended) return;
  const template = applicationTemplateById(templateId);
  if (!template) return;
  const outgoing = applicationFormDraftPayload(template);
  const accountContext = captureAuthenticatedRequestContext();
  state.applicationFormDraftPending[applicationDraftKey(templateId, outgoing.home_school)] = outgoing;
  window.clearTimeout(state.applicationFormDraftSyncTimer);
  state.applicationFormDraftSyncTimer = window.setTimeout(
    () => {
      if (authenticatedRequestContextIsCurrent(accountContext)) retryPendingApplicationFormDrafts();
    },
    650,
  );
}

async function retryPendingApplicationFormDrafts() {
  if (!state.account || navigator.onLine === false) return;
  const accountContext = captureAuthenticatedRequestContext();
  for (const [key, payload] of Object.entries(state.applicationFormDraftPending || {})) {
    if (!authenticatedRequestContextIsCurrent(accountContext)) return;
    const prefix = `${payload.home_school}::`;
    if (key.startsWith(prefix)) await saveApplicationFormDraft(key.slice(prefix.length), { payload });
  }
}

function clearApplicationFormDraftState() {
  window.clearTimeout(state.applicationFormDraftSyncTimer);
  state.applicationFormDrafts = {};
  state.applicationFormDraftLoadedSchool = "";
  state.applicationFormDraftPending = {};
  state.applicationFileVaultLinks = {};
  state.applicationFileConsentCandidate = null;
  state.applicationAnswers = {};
  state.applicationFiles = {};
  state.applicationProfile = {};
  const fields = $("#application-document-fields");
  if (fields) { fields.replaceChildren(); delete fields.dataset.renderKey; }
  $("#application-review-preview")?.replaceChildren();
  try {
    window.sessionStorage.removeItem(APPLICATION_SESSION_KEYS.profile);
    window.sessionStorage.removeItem(APPLICATION_SESSION_KEYS.answers);
  } catch (_) {
    // In-memory clearing still protects the signed-out session.
  }
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
  if (!field || field.field_type === "files") return;
  const value = field.field_type === "checkbox" ? Boolean(input.checked) : String(input.value || "").trim();
  if (field.reusable_profile_key) {
    if (applicationValuePresent(value)) state.applicationProfile[field.reusable_profile_key] = value;
    else delete state.applicationProfile[field.reusable_profile_key];
    if (state.applicationAnswers[template.id]) delete state.applicationAnswers[template.id][field.id];
  } else {
    state.applicationAnswers[template.id] ||= {};
    state.applicationAnswers[template.id][field.id] = value;
  }
  persistApplicationDraft();
  refreshApplicationFieldConditions(template);
  restoreApplicationProfileForm();
  renderApplicationAutofillStatus(template);
  scheduleApplicationReviewPreview(template.id);
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
  const required = template.fields.filter((field) => applicationFieldRequired(template, field));
  if (!required.length) return { completed: 0, total: 0, percent: 100, ready: true };
  const completed = required.filter((field) => applicationFieldHasValue(template, field)).length;
  return {
    completed,
    total: required.length,
    percent: Math.round((completed / required.length) * 100),
    ready: completed === required.length,
  };
}

function applicationFieldRequired(template, field) {
  return field.required || (field.required_when || []).some((clause) =>
    Object.entries(clause).every(([id, values]) => {
      const dependency = template.fields.find((item) => item.id === id);
      return dependency && values.includes(String(applicationValue(template, dependency) || ""));
    })
  );
}

function applicationFieldOptions(template, field) {
  for (const [id, groups] of Object.entries(field.options_by_field || {})) {
    const dependency = template.fields.find((item) => item.id === id);
    const options = dependency && groups[String(applicationValue(template, dependency) || "")];
    if (options) return options;
  }
  return field.options || [];
}

function refreshApplicationFieldConditions(template) {
  const form = $("#application-document-form");
  if (!form || state.activeApplicationTemplateId !== template.id) return;
  for (const field of template.fields) {
    if (!(field.required_when?.length || Object.keys(field.options_by_field || {}).length)) continue;
    const input = form.elements[field.id];
    if (!input) continue;
    input.required = applicationFieldRequired(template, field);
    const label = form.querySelector(`label[for="${input.id}"]`);
    if (label) label.textContent = `${field.label}${input.required ? " *" : ""}`;
    if (field.field_type === "select" && Object.keys(field.options_by_field || {}).length) {
      const options = applicationFieldOptions(template, field);
      const value = input.value;
      if (JSON.stringify(Array.from(input.options).slice(1).map((option) => option.value)) !== JSON.stringify(options)) {
        input.innerHTML = '<option value="">請選擇</option>' + options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("");
        input.value = options.includes(value) ? value : "";
        state.applicationAnswers[template.id] ||= {};
        state.applicationAnswers[template.id][field.id] = input.value;
        persistApplicationDraft();
      }
    }
  }
  const date = form.elements.language_result_date;
  if (date && activeHomeSchool() === "國立臺灣大學") {
    const test = form.elements.language_test?.value;
    const english = ["TOEFL iBT（舊制120分）", "TOEFL iBT（新制6分）", "IELTS Academic", "GEPT", "BESTEP"].includes(test);
    if (english) { date.min = "2025-05-01"; date.max = new Date().toISOString().slice(0, 10); }
    else { date.removeAttribute("min"); date.removeAttribute("max"); }
  }
  if (date && activeHomeSchool() === "國立中央大學") {
    date.removeAttribute("min");
    date.max = new Date().toISOString().slice(0, 10);
  }
}

function applicationProfileCompletion() {
  const required = ["student_name_zh", "student_name_en", "student_id", "college", "department", "degree_level", "year_level", "email", "phone"];
  const completed = required.filter((key) => applicationValuePresent(state.applicationProfile[key] || sharedApplicationCondition(key))).length;
  return { completed, total: required.length, ready: completed === required.length };
}

function persistApplicationContext({ sync = true } = {}) {
  if (!state.account) return;
  try {
    window.localStorage.setItem(STORAGE_KEYS.applicationContext, JSON.stringify(state.applicationContext));
    window.localStorage.setItem(STORAGE_KEYS.applicationSelections, JSON.stringify(state.applicationSelections));
  } catch (_) {
    // The current application setup remains available for this session.
  }
  if (sync) scheduleAccountWorkspaceSync();
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

function persistApplicationDraft({ syncRemote = true } = {}) {
  stripReusableApplicationAnswers();
  try {
    window.sessionStorage.setItem(APPLICATION_SESSION_KEYS.profile, JSON.stringify(state.applicationProfile));
    window.sessionStorage.setItem(APPLICATION_SESSION_KEYS.answers, JSON.stringify(applicationAnswersForSession()));
  } catch (_) {
    // Sensitive form data remains in memory and is cleared when the page closes.
  }
  persistApplicationProfileMemory();
  persistApplicationContext({ sync: syncRemote });
  if (syncRemote) {
    const fallback = initialApplicationTemplates()[0]?.id || state.applicationTemplates[0]?.id || "";
    scheduleApplicationFormDraftSync(state.activeApplicationTemplateId || fallback);
  }
}

function applicationFlagsFromForm(form) {
  return ["subsidy", "military_service", "full_year"].filter((name) => form.elements[name]?.checked);
}

function ncuDocumentStateKey(schoolName = state.applicationContext.target_school, year = state.applicationContext.academic_year, round = state.applicationContext.application_round, semester = state.applicationContext.semester) {
  return JSON.stringify([schoolName || "", year || "", round || "", semester || ""]);
}

function ncuDocumentState(schoolName, year, round, semester = state.applicationContext.semester) {
  return state.applicationContext.partner_document_states?.[ncuDocumentStateKey(schoolName, year, round, semester)] || {host_admission_status:"unknown",housing_choice:"unknown"};
}

function ncuCatalogContextKey(context) {
  const key = ncuDocumentStateKey(context.target_school,context.academic_year,context.application_round,context.semester);
  const selection = context.partner_document_states?.[key] || {};
  return JSON.stringify([context.target_school || "",context.college || "",context.department || "",context.degree_level || "",context.academic_year || "",context.application_round || "",context.semester || "",selection.host_admission_status || "unknown",selection.housing_choice || "unknown"]);
}

function restoreNcuDocumentState() {
  const panel = $("#ncu-document-state");
  if (!panel) return;
  panel.hidden = activeHomeSchool() !== "國立中央大學" || !state.applicationContext.target_school || state.applicationContext.program_type !== "exchange";
  const selection = ncuDocumentState(state.applicationContext.target_school, state.applicationContext.academic_year, state.applicationContext.application_round);
  $("#ncu-host-admission").value = selection.host_admission_status;
  $("#ncu-housing-choice").value = selection.housing_choice;
  $("#ncu-document-state-note").textContent = `此學校、年度／梯次與學期的條件文件會依選擇顯示準備時點；當期要求仍須查核。${state.account ? "選擇會保存於本次申請設定。" : "登入後可保存選擇。"}`;
}

function documentApplicabilityMarkup(results) {
  const labels = {applicable:"符合參考條件",not_applicable:"不適用",deferred:"錄取後再準備",needs_confirmation:"條件需確認"};
  return (results || []).map(result=>`<p class="document-applicability" data-document-applicability="${escapeHtml(result.status)}"><strong>${escapeHtml(labels[result.status] || "需確認")} · ${escapeHtml(result.requirement_name)}</strong><span>${escapeHtml(result.note)}</span></p>`).join("");
}

async function handleNcuDocumentStateChange() {
  if (activeHomeSchool() !== "國立中央大學" || !state.applicationContext.target_school) return;
  const key = ncuDocumentStateKey();
  state.applicationContext.partner_document_states = {...(state.applicationContext.partner_document_states || {}), [key]:{host_admission_status:$("#ncu-host-admission").value,housing_choice:$("#ncu-housing-choice").value}};
  persistApplicationContext();
  if (state.personalApplicationPlan?.choices?.some(choice=>choice.school_name === state.applicationContext.target_school)) {
    state.personalApplicationPlan = null;
    $("#eligibility-result").innerHTML = '<p>錄取或住宿條件已修改，請重新核對志願以更新個人準備任務。</p>';
    renderPersonalPlanSnapshot();
  }
  await loadApplicationTemplates();
  window.UniWayMultiPlan?.render();
}

function readApplicationContextForm({ targetSchool = $("#application-target-school")?.value || "" } = {}) {
  const form = $("#application-context-form");
  if (!form) return state.applicationContext;
  const partner = state.dashboard?.partner_universities?.find((item) => item.school_name === targetSchool);
  state.applicationContext = {
    ...state.applicationContext,
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
  form.elements.semester.value = semesterFromTargetTerm(state.applicationContext.semester) || semesterFromTargetTerm(state.eligibilityProfile?.targetTerm);
  ["subsidy", "military_service", "full_year"].forEach((name) => {
    form.elements[name].checked = (state.applicationContext.flags || []).includes(name);
  });
  renderApplicationTargetSchools();
  restoreNcuDocumentState();
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
    input.value = state.applicationProfile[input.name] || sharedApplicationCondition(input.name) || (input.name === "email" ? state.account?.email || "" : "");
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
  state.applicationPreviews = {};
  state.applicationTemplates.forEach((template) => {
    const existing = state.applicationSelections[template.id] || {};
    const reviewCurrent = existing.reviewed_version === template.version;
    state.applicationSelections[template.id] = {
      selected: Boolean(existing.selected),
      copies: Number(existing.copies) || template.default_copies,
      status: existing.status || "draft",
      reviewed_version: reviewCurrent ? existing.reviewed_version : null,
      reviewed_content_sha256: reviewCurrent ? existing.reviewed_content_sha256 || null : null,
      reviewed_at: reviewCurrent ? existing.reviewed_at || null : null,
    };
  });
  persistApplicationContext({ sync: false });
}

function applicationCatalogContextKey(homeSchool = activeHomeSchool(), context = state.applicationContext) {
  return JSON.stringify([homeSchool, ...["target_school", "program_type", "college", "department", "degree_level", "academic_year", "application_round", "semester"].map(key => context[key] || ""), [...(context.flags || [])].sort(), context.partner_document_states || {}]);
}

async function loadApplicationTemplates({ homeSchool = activeHomeSchool() } = {}) {
  if (!canAccessPartnerCatalog()) return false;
  const requestedSchool = homeSchool;
  const request = beginSchoolDataRequest("templates", requestedSchool);
  const context = { ...state.applicationContext, flags: [...(state.applicationContext.flags || [])] };
  const contextKey = applicationCatalogContextKey(requestedSchool, context);
  const requestId = ++state.applicationTemplateRequestId;
  const requestOwner = captureAuthenticatedRequestContext();
  const isCurrent = () => schoolDataRequestIsCurrent(request) && requestId === state.applicationTemplateRequestId
    && authenticatedRequestContextIsCurrent(requestOwner)
    && isCurrentHomeSchool(requestedSchool) && contextKey === applicationCatalogContextKey();
  const container = $("#application-template-list");
  state.applicationTemplates = [];
  state.applicationDocumentCatalog = null;
  state.applicationDocumentCatalogError = "";
  state.applicationDocumentCatalogContextKey = "";
  state.applicationLoading = true;
  renderApplicationDocumentCatalog();
  renderApplicationPacket();
  if (container) container.innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
  try {
    const params = new URLSearchParams({
      school: requestedSchool,
      program_type: context.program_type || "exchange",
    });
    if (context.flags?.length) params.set("flags", context.flags.join(","));
    ["academic_year", "application_round"].forEach(key => {
      if (context[key]) params.set(key, context[key]);
    });
    const templates = await fetchJson(`/application-center/templates?${params}`);
    if (!isCurrent()) return false;
    let catalog = null;
    let catalogError = "";
    if (context.program_type === "exchange" && context.target_school) {
      const catalogParams = new URLSearchParams({
        school: requestedSchool,
        target_school: context.target_school,
      });
      ["college", "department", "degree_level", "academic_year", "application_round", "semester"].forEach((key) => {
        if (context[key]) catalogParams.set(key, context[key]);
      });
      if (requestedSchool === "國立中央大學") {
        const selection = ncuDocumentState(context.target_school, context.academic_year, context.application_round);
        catalogParams.set("host_admission_status", selection.host_admission_status);
        catalogParams.set("housing_choice", selection.housing_choice);
      }
      try {
        catalog = await fetchJson(`/application-center/catalog?${catalogParams}`);
      } catch (error) {
        catalogError = error.message;
      }
    }
    if (!isCurrent()) return false;
    if (state.account && state.applicationFormDraftLoadedSchool !== requestedSchool) {
      await loadApplicationFormDrafts({ homeSchool: requestedSchool });
    }
    if (!isCurrent()) return false;
    state.applicationTemplates = templates;
    state.applicationDocumentCatalog = catalog;
    state.applicationDocumentCatalogError = catalogError;
    state.applicationDocumentCatalogContextKey = contextKey;
    initializeApplicationSelections();
    renderApplicationCenter();
    refreshSelectedApplicationPreviews();
    renderApplicationJourney();
    renderPersonalPlanSnapshot();
    const active = applicationTemplateById(state.activeApplicationTemplateId);
    if (active && window.location.hash.startsWith("#application-form=")) {
      if (applicationDocumentGenerationEnabled()) renderApplicationFormPage(active);
      else window.location.hash = "#application-center";
    }
    return true;
  } catch (error) {
    if (!isCurrent()) return false;
    state.applicationDocumentCatalogError = error.message;
    if (container) renderEmpty("#application-template-list", "暫時無法取得申請文件", error.message, "error");
    return false;
  } finally {
    if (isCurrent()) {
      state.applicationLoading = false;
      renderApplicationDocumentCatalog();
      renderApplicationPacket();
    }
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

function applicationDocumentGenerationEnabled() {
  return Boolean(
    state.account
    && entitlementFeatureEnabled("application_document_generation"),
  );
}

function renderApplicationGenerationGate() {
  const gate = $("#application-generation-gate");
  const profile = $("#application-profile-panel");
  if (!gate) return;
  const enabled = applicationDocumentGenerationEnabled();
  if (profile) profile.hidden = !enabled;
  if (enabled) {
    gate.hidden = true;
    gate.innerHTML = "";
    return;
  }
  gate.hidden = false;
  if (!state.account) {
    gate.innerHTML = `
      <span><i data-lucide="log-in" aria-hidden="true"></i></span>
      <div><strong>登入後使用自動填表與列印套件</strong><small>申請規定、官方來源與校方原始表格仍可免登入免費查看；登入不代表同意上傳個人文件。</small></div>
      <button type="button" class="primary-button" data-application-generation-login>登入後使用</button>`;
    initIcons();
    return;
  }
  if (!state.entitlements) {
    gate.innerHTML = '<div class="skeleton skeleton-card"></div>';
    return;
  }
  gate.innerHTML = `
    <span><i data-lucide="lock-keyhole" aria-hidden="true"></i></span>
    <div><strong>自動填表與申請文件套件是進階功能</strong><small>目前方案仍可免費查看申請規定、下載官方表格及使用基本申請清單；登入後目前免費使用，系統不會扣款。</small></div>`;
  initIcons();
}

function renderApplicationTemplateCard(template) {
  const completion = applicationTemplateCompletion(template);
  const selected = state.applicationSelections[template.id]?.selected;
  const enabled = applicationDocumentGenerationEnabled();
  const loginRequired = !state.account;
  return `
    <article class="application-template-card ${completion.ready ? "is-complete" : ""}">
      <span class="application-template-icon"><i data-lucide="${APPLICATION_STAGE_ICONS[template.stage] || "file-text"}" aria-hidden="true"></i></span>
      <div class="application-template-copy">
        <span class="application-template-meta"><span>${escapeHtml(template.category)}</span>${template.official_layout ? "<em>官方格式</em>" : ""}<span class="application-document-status status-${escapeHtml(applicationDocumentStatus(template.id))}">${escapeHtml(applicationDocumentStatusLabel(template.id))}</span>${selected ? `<span>${applicationTemplateReviewed(template) ? "已核對" : "待核對"}</span>` : ""}</span>
        <strong>${escapeHtml(template.short_title)}</strong>
        <span class="application-template-progress"><span><i style="width:${completion.percent}%"></i></span><b>${completion.percent}%</b><em>${template.default_copies} 份</em></span>
      </div>
      <div class="application-template-actions">
        <label class="template-packet-toggle"><input type="checkbox" data-application-packet-template="${escapeHtml(template.id)}" aria-label="加入${escapeHtml(template.short_title)}到列印包" ${selected ? "checked" : ""} ${enabled ? "" : "disabled"} /><span>列印包</span></label>
        ${template.official_download_url ? `<a class="application-template-official" href="${escapeHtml(template.official_download_url)}" target="_blank" rel="noreferrer" aria-label="下載${escapeHtml(template.short_title)}校方原始表格"><i data-lucide="file-down" aria-hidden="true"></i><span>官方表格</span></a>` : ""}
        <button type="button" class="application-template-open" data-open-application-template="${escapeHtml(template.id)}" aria-disabled="${String(!enabled && !loginRequired)}" aria-label="${enabled ? "填寫" : loginRequired ? "登入後填寫" : "自動填表進階功能："}${escapeHtml(template.short_title)}"><i data-lucide="${enabled ? "chevron-right" : loginRequired ? "log-in" : "lock-keyhole"}" aria-hidden="true"></i></button>
      </div>
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
  const active = applicationDocumentStage();
  const previous = new Map([...container.querySelectorAll("details[data-document-stage]")].map(item=>[item.dataset.documentStage,item.open]));
  const context = JSON.stringify([state.account?.id, activeHomeSchool(), state.applicationContext.target_school, active]);
  const preserve = container.dataset.stageContext === context;
  container.dataset.stageContext = context;
  const groups = applicationStageGroups();
  const selector = $("#application-document-stage");
  if (selector) { selector.innerHTML = groups.map(group=>`<option value="${escapeHtml(group.stage)}">${escapeHtml(group.stage)}</option>`).join(""); selector.value = active; }
  container.innerHTML = groups.map(group=>{
    const current = group.stage === active;
    const open = preserve && previous.has(group.stage) ? previous.get(group.stage) : current;
    return `<details class="application-template-stage ${current ? "is-current-stage" : ""}" data-document-stage="${escapeHtml(group.stage)}" ${open ? "open" : ""}><summary class="application-template-stage-heading"><strong>${escapeHtml(group.stage)}${current ? '<em>目前查看</em>' : ""}</strong><small>${group.templates.length} 份<i data-lucide="chevron-down" aria-hidden="true"></i></small></summary><div class="application-stage-tools">${group.templates.map(renderApplicationTemplateCard).join("")}</div></details>`;
  }).join("");
  initIcons();
}

function applicationRequirementMeta(item) {
  const parts = [
    item.copies ? `${item.copies} 份` : "份數待確認",
    APPLICATION_COPY_TYPE_LABELS[item.copy_type] || "形式待確認",
  ];
  if (item.signatures?.length) parts.push(`簽名：${item.signatures.join("、")}`);
  if (item.stamps?.length) parts.push(`核章：${item.stamps.join("、")}`);
  if (item.stage) parts.push(`階段：${({nomination:"提名",student_application:"學生申請",after_application:"外校申請後",second_submission:"第二次送件",post_offer:"錄取後",after_dorm_assignment:"住宿分配後",conditional_program:"特定計畫條件"})[item.stage]}`);
  if (item.conditional) parts.push(`適用條件：${item.condition || item.name}`);
  if (item.applicability_status) parts.push(`適用性：${({verified_current:"當期依據已核",needs_confirmation:"當期適用待確認",reference_only:"歷史參考"})[item.applicability_status]}`);
  if (item.applicability_year) parts.push(item.applicability_year);
  if (item.applicability_note) parts.push(item.applicability_note);
  if (item.official_form_verified && item.needs_confirmation) parts.push("官方文件已核實可開啟；適用性、完整清單及送件細節仍待確認");
  else if (item.applicability_status && item.official_form_url) parts.push("原檔下載未核實；版本適用性待確認");
  return parts.join(" · ");
}

function renderApplicationDocumentCatalog() {
  const container = $("#application-requirement-list");
  const count = $("#application-requirement-count");
  const summary = $("#application-requirement-summary");
  if (!container) return;
  if (state.applicationLoading && state.applicationContext.target_school) {
    if (count) count.textContent = "載入中";
    if (summary) summary.textContent = `${state.applicationContext.target_school} · 正在核對本次年度與官方文件來源…`;
    container.innerHTML = '<p class="workspace-empty" role="status">正在載入這所學校的文件清單。</p>';
    return;
  }
  if (state.applicationDocumentCatalogError) {
    if (count) count.textContent = "讀取失敗";
    if (summary) summary.textContent = "準備工具仍可使用，但當期文件需求暫時無法讀取。";
    container.innerHTML = `<div class="document-source-gap" role="alert"><p>${escapeHtml(state.applicationDocumentCatalogError)}</p><button type="button" class="secondary-button" data-retry-application-catalog>重新載入官方清單</button></div>`;
    return;
  }
  const catalog = state.applicationDocumentCatalogContextKey === applicationCatalogContextKey()
    ? state.applicationDocumentCatalog : null;
  if (!state.applicationContext.target_school) {
    if (count) count.textContent = "請選擇學校";
    if (summary) summary.textContent = "選擇目標學校後，會依學系、年度與梯次列出文件；沒有確認的份數或表格不會被當成正式版本。";
    container.innerHTML = '<p class="workspace-empty">尚未選擇目標學校。</p>';
    return;
  }
  if (!catalog?.workflow_found || !catalog.items?.length) {
    if (count) count.textContent = "待校方提供";
    if (summary) summary.textContent = `目前沒有可安全套用的結構化文件目錄，請聯絡 ${catalog?.contact_unit || `${activeHomeSchool()}國際事務處／所屬系所`}。`;
    container.innerHTML = `<div class="document-source-gap"><strong>先確認本次申請需要什麼</strong><p>準備工具可先存草稿；送件前向 ${escapeHtml(catalog?.contact_unit || `${activeHomeSchool()}國際事務處／所屬系所`)} 確認以下事項。</p><ul><li>適用的年度、梯次與申請資格</li><li>正式表格、必備附件、份數與簽章</li><li>校內送件單位與最後期限</li></ul><a class="secondary-button" href="#documents">查看本校官方文件來源</a>${applicationInquiryMarkup()}</div>`;
    return;
  }
  const confirmed = catalog.items.filter((item) => !item.needs_confirmation).length;
  const downloadable = catalog.items.filter((item) => item.download_available).length;
  if (count) count.textContent = `${catalog.items.length} 項`;
  if (summary) {
    const version = [catalog.academic_year && `${catalog.academic_year} 學年度`, catalog.application_round].filter(Boolean).join(" · ") || "未標示年度／梯次";
    summary.textContent = `${state.applicationContext.target_school} · ${version}；${confirmed} 項已確認，${downloadable} 份有官方表格直連，其餘須按來源或向指定單位確認。`;
  }
  const groups = [];
  catalog.items.forEach((item) => {
    let group = groups.find((row) => row.phase === item.phase);
    if (!group) {
      group = { phase: item.phase, items: [] };
      groups.push(group);
    }
    group.items.push(item);
  });
  container.innerHTML = groups.map((group, groupIndex) => `
    <details class="application-requirement-group" ${groupIndex === 0 ? "open" : ""}>
      <summary><span><strong>${escapeHtml(group.phase)}</strong><small>${group.items.length} 項</small></span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>
      <div>${group.items.map((item) => {
        const sourceUrl = item.source_urls?.[0] || "";
        const pendingForm = item.applicability_status && safeSourceUrl(item.official_form_url);
        const sourceLabel = activeHomeSchool() === "淡江大學" && item.download_available ? (item.applicability_status === "reference_only" ? "開啟官方一般參考表格" : "開啟校方原表／表單入口") : item.official_form_verified ? "開啟已核實官方表格／文件" : item.download_available ? "下載校方正式表格" : pendingForm ? "查看官方表格來源（待核實）" : "查看官方規定";
        const sourceHref = item.download_available || pendingForm ? item.official_form_url : sourceUrl;
        const referenceSources = activeHomeSchool() === "國立中央大學" && item.needs_confirmation
          ? [...new Set(item.source_urls || [])].filter((url) => url !== sourceHref && safeSourceUrl(url))
          : [];
        const checkedAt = item.source_checked_at ? formatDate(item.source_checked_at) : "查核日待補";
        return `
          <article class="application-requirement-item ${item.needs_confirmation ? "needs-confirmation" : "is-confirmed"}">
            <span class="application-requirement-order">${item.sequence}</span>
            <div><span class="application-requirement-badges"><em>${item.needs_confirmation ? "待確認" : "已確認"}</em>${item.conditional ? "<b>符合條件才需要</b>" : ""}${item.download_available ? "<b>官方表格</b>" : ""}</span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.step_title)}</small><p>${escapeHtml(applicationRequirementMeta(item))}</p>${documentApplicabilityMarkup(item.applicability ? [item.applicability] : [])}${item.needs_confirmation ? `<p class="application-requirement-contact">請聯絡 ${escapeHtml(item.contact_unit || catalog.contact_unit)}</p>` : ""}</div>
            <div class="application-requirement-source">${sourceHref ? `<a href="${escapeHtml(sourceHref)}" target="_blank" rel="noreferrer"><i data-lucide="external-link" aria-hidden="true"></i><span>${sourceLabel}</span></a>` : "<span>來源待校方提供</span>"}${referenceSources.length ? `<details><summary>其他參考來源（當期待確認）</summary>${referenceSources.map((url, index) => `<a href="${escapeHtml(safeSourceUrl(url))}" target="_blank" rel="noreferrer">參考來源 ${index + 1}</a>`).join("")}</details>` : ""}<small>${escapeHtml(checkedAt)}</small></div>
          </article>`;
      }).join("")}</div>
    </details>`).join("");
  initIcons();
}

function updateApplicationPacketCopies(input, { refreshRows = true } = {}) {
  const template = applicationTemplateById(input.dataset.applicationCopyTemplate);
  if (!template || !applicationDocumentGenerationEnabled()) return;
  const value = Math.max(1, Math.min(10, Number(input.value) || template.default_copies));
  const existing = state.applicationSelections[template.id] || {};
  state.applicationSelections[template.id] = { ...existing, selected:true, copies:value, status:applicationDocumentStatus(template.id), reviewed_version:null, reviewed_content_sha256:null, reviewed_at:null };
  persistApplicationContext();
  if (!refreshRows) {
    const readiness = input.closest(".application-packet-row")?.querySelector(".packet-readiness");
    if (readiness) {
      readiness.textContent = applicationTemplateCompletion(template).ready ? "待核對" : "待填寫";
      readiness.classList.remove("is-ready");
    }
  }
  renderApplicationPacket({ refreshRows });
  if (state.activeApplicationTemplateId === template.id) scheduleApplicationReviewPreview(template.id);
}

function renderApplicationPacket({ refreshRows = true } = {}) {
  const container = $("#application-packet-list");
  const total = $("#application-packet-total");
  const status = $("#application-packet-status");
  const button = $("#download-application-packet");
  if (!container) return;
  const generationEnabled = applicationDocumentGenerationEnabled();
  if (refreshRows) container.innerHTML = state.applicationTemplates.filter(template=>state.applicationSelections[template.id]?.selected).map((template) => {
    const selection = state.applicationSelections[template.id] || { selected:false, copies:template.default_copies };
    const preview = state.applicationPreviews[template.id];
    const attachments = (preview?.attachments || []).map(applicationAttachmentLabel);
    const ready = applicationTemplateCompletion(template).ready;
    const reviewed = applicationTemplateReviewed(template);
    const id = `packet-select-${template.id}`;
    return `<article class="application-packet-row${selection.selected ? " is-selected" : ""}">
      <div class="packet-row-heading"><input id="${escapeHtml(id)}" type="checkbox" aria-label="加入${escapeHtml(template.short_title)}到列印包" data-application-packet-template="${escapeHtml(template.id)}" ${selection.selected ? "checked" : ""} ${generationEnabled ? "" : "disabled"} /><label for="${escapeHtml(id)}"><strong>${escapeHtml(template.short_title)}</strong><small>${escapeHtml(template.stage)}</small></label><span class="packet-readiness ${reviewed ? "is-ready" : ""}">${reviewed ? "已核對" : ready ? "待核對" : "待填寫"}</span></div>
      <div class="packet-row-controls">${generationEnabled ? `<a href="#application-form=${encodeURIComponent(template.id)}">${ready ? "核對內容" : "繼續填寫"}<i data-lucide="arrow-up-right" aria-hidden="true"></i></a>` : "<small>目前不可匯出</small>"}<label class="packet-copies-label"><span>份數</span><input class="application-copy-input" type="number" min="1" max="10" value="${selection.copies || template.default_copies}" data-application-copy-template="${escapeHtml(template.id)}" aria-label="${escapeHtml(template.short_title)}列印份數" ${generationEnabled && selection.selected ? "" : "disabled"} /></label></div>
      <details class="packet-print-details"><summary>列印與附件資訊<i data-lucide="chevron-down" aria-hidden="true"></i></summary><p class="application-packet-print">${escapeHtml(applicationPrintSummary(template))}</p><p>實際附件：${escapeHtml(attachments.length ? attachments.join("；") : "尚無附件")}</p><p>狀態：${escapeHtml(applicationDocumentStatusLabel(template.id))} · ${reviewed ? "已核對目前版本" : "尚未核對目前版本"}</p></details>
    </article>`;
  }).join("");
  if (refreshRows && !container.children.length) container.innerHTML = '<div class="packet-empty"><i data-lucide="files" aria-hidden="true"></i><strong>只放這次要印的文件</strong><p>在準備工具勾選「列印包」，文件就會出現在這裡。填完並核對後才可匯出。</p></div>';
  const selectedTemplates = state.applicationTemplates.filter((template) => state.applicationSelections[template.id]?.selected);
  const copies = selectedTemplates.reduce((sum, template) => sum + Number(state.applicationSelections[template.id]?.copies || template.default_copies), 0);
  const incomplete = selectedTemplates.filter((template) => !applicationTemplateCompletion(template).ready);
  const unreviewed = selectedTemplates.filter((template) => !applicationTemplateReviewed(template));
  if (total) total.textContent = `${copies} 份`;
  const progress = $("#application-packet-progress");
  if (progress) {
    const readyCount = selectedTemplates.filter(template=>applicationTemplateCompletion(template).ready && applicationTemplateReviewed(template)).length;
    const percent = selectedTemplates.length ? Math.round(readyCount/selectedTemplates.length*100) : 0;
    progress.innerHTML = `<div><strong>${selectedTemplates.length ? `已選 ${selectedTemplates.length} 項文件` : "選擇這次要匯出的文件"}</strong><span>${readyCount} 項可匯出</span></div><progress value="${percent}" max="100" aria-label="已選文件的匯出準備進度">${percent}%</progress>`;
  }
  if (status) {
    status.className = `application-packet-status ${incomplete.length ? "is-warning" : selectedTemplates.length ? "is-success" : ""}`;
    status.textContent = !generationEnabled
      ? (!state.account ? "登入後可建立列印套件" : !state.entitlements ? "正在確認方案權限" : "目前方案未包含列印套件")
      : !selectedTemplates.length
      ? "尚未選取文件"
      : incomplete.length
        ? `${incomplete.length} 份尚未填完`
        : unreviewed.length
          ? `${unreviewed.length} 份尚未完成核對`
        : `可產生 ${copies} 份`;
  }
  if (button) button.disabled = !generationEnabled || !selectedTemplates.length || Boolean(incomplete.length) || Boolean(unreviewed.length) || state.applicationLoading;
  initIcons();
}

function updateApplicationCenterSteps() {
  const steps = [...document.querySelectorAll(".application-center-steps li")];
  if (!steps.length) return;
  const profileReady = applicationProfileCompletion().ready;
  const completedCount = state.applicationTemplates.filter((template) => applicationTemplateCompletion(template).ready).length;
  const selected = state.applicationTemplates.filter((template) => state.applicationSelections[template.id]?.selected);
  const packageReady = selected.length > 0 && selected.every((template) => (
    applicationTemplateCompletion(template).ready && applicationTemplateReviewed(template)
  ));
  [true, profileReady, completedCount > 0, packageReady].forEach((active, index) => steps[index]?.classList.toggle("is-active", active));
}

function renderApplicationCenter() {
  restoreApplicationContextForm();
  restoreApplicationProfileForm();
  renderApplicationTemplates();
  renderApplicationDocumentCatalog();
  renderApplicationGenerationGate();
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
  invalidateAllApplicationReviews();
  persistApplicationDraft();
  renderApplicationCenter();
  announce("共用資料已儲存", "success");
}

async function handleApplicationContextChange(event) {
  const targetInput = $("#application-target-school");
  // A background workspace render may restore the select while confirmation is open.
  const proposed = targetInput.value;
  if (event?.target === targetInput && targetInput.value !== state.applicationContext.target_school) {
    const owner = state.account?.id;
    const home = activeHomeSchool();
    targetInput.disabled = true;
    let confirmed;
    try {
      confirmed = await confirmPlanningTargetChange(proposed || "尚未決定");
    } finally {
      targetInput.disabled = false;
    }
    if (!confirmed || owner !== state.account?.id || home !== activeHomeSchool()) { restoreApplicationContextForm(); return; }
  }
  state.planningPreview = null;
  state.planningLoading = false;
  state.planningRequestId += 1;
  invalidateAllApplicationReviews();
  readApplicationContextForm({ targetSchool: proposed });
  await loadApplicationTemplates();
  renderPersonalPlanSnapshot();
}

function applicationFieldInput(template, field, inputId = "") {
  const value = applicationValue(template, field);
  const required = applicationFieldRequired(template, field) ? "required" : "";
  const maxLength = field.max_length ? `maxlength="${field.max_length}"` : "";
  const placeholder = field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : "";
  const common = `id="${escapeHtml(inputId)}" name="${escapeHtml(field.id)}" data-application-field="${escapeHtml(field.id)}" ${required} ${maxLength} ${placeholder}`;
  if (field.field_type === "textarea") {
    return `<textarea ${common}>${escapeHtml(value || "")}</textarea>`;
  }
  if (field.field_type === "select") {
    return `<select ${common}><option value="">請選擇</option>${applicationFieldOptions(template, field).map((option) => `<option value="${escapeHtml(option)}" ${String(value) === option ? "selected" : ""}>${escapeHtml(option)}</option>`).join("")}</select>`;
  }
  if (field.field_type === "checkbox") {
    return `<label class="application-checkbox-field"><input type="checkbox" ${common} ${value === true ? "checked" : ""} /><span>${escapeHtml(field.label)}</span></label>`;
  }
  if (field.field_type === "files") {
    const liveFiles = state.applicationFiles?.[template.id]?.[field.id] || [];
    const validFiles = liveFiles.filter((file) => typeof file?.data_url === "string" && file.data_url.startsWith("data:"));
    const minimum = Math.max(Number(field.min_files) || 0, field.required ? 1 : 0);
    const fileRequired = validFiles.length < minimum ? "required" : "";
    const accept = field.id.includes("photo") ? "image/jpeg,image/png" : "application/pdf,image/jpeg,image/png";
    const multiple = Number(field.max_files || 1) > 1 ? "multiple" : "";
    return `<label class="application-file-field"><i data-lucide="upload-cloud" aria-hidden="true"></i><strong>${escapeHtml(field.label)}</strong><input type="file" ${common.replace(required, fileRequired)} accept="${accept}" ${multiple} /><small>${escapeHtml(field.help_text || "可選擇 PDF 或圖片")}</small></label><p class="application-file-local-boundary"><i data-lucide="shield" aria-hidden="true"></i><span>敏感原檔預設只用於本次分頁，不會因登入自動上傳。</span></p><div class="application-file-preview" data-application-file-preview="${escapeHtml(field.id)}"></div>`;
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

function renderApplicationReviewPreview(template, { loading = false, error = "" } = {}) {
  const container = $("#application-review-preview");
  if (!container || state.activeApplicationTemplateId !== template.id) return;
  window.requestAnimationFrame(() => window.UniWayDocumentWorkbench?.renderFlow());
  if (loading) {
    container.innerHTML = `
      <div class="application-review-preview-heading"><div><h3 id="application-review-preview-title">逐欄預覽</h3></div><span class="application-review-state is-loading">正在更新</span></div>
      <div class="application-review-preview-loading"><span class="skeleton"></span><span class="skeleton"></span><span class="skeleton"></span></div>`;
    return;
  }
  if (error) {
    container.innerHTML = `
      <div class="application-review-preview-heading"><div><h3 id="application-review-preview-title">逐欄預覽</h3></div><span class="application-review-state is-error">更新失敗</span></div>
      <p class="application-review-preview-error">${escapeHtml(error)}</p>
      <button type="button" class="secondary-button" data-refresh-application-preview="${escapeHtml(template.id)}"><i data-lucide="refresh-cw" aria-hidden="true"></i><span>重新載入預覽</span></button>`;
    initIcons();
    return;
  }
  const item = state.applicationPreviews[template.id];
  if (!item) {
    renderApplicationReviewPreview(template, { loading: true });
    return;
  }
  const reviewed = applicationTemplateReviewed(template);
  const missing = item.missing_required_fields || [];
  const invalidAttachments = item.invalid_attachment_fields || [];
  const blocked = missing.length || invalidAttachments.length;
  const list = (values, empty) => values?.length ? values.join("、") : empty;
  const actualAttachments = (item.attachments || []).map(applicationAttachmentLabel);
  container.innerHTML = `
    <div class="application-review-preview-heading">
      <div><h3 id="application-review-preview-title">逐欄預覽</h3><p>空白欄位將保持空白。</p></div>
      <span class="application-review-state ${reviewed ? "is-reviewed" : blocked ? "is-missing" : "is-ready"}">${reviewed ? "已核對" : invalidAttachments.length ? `${invalidAttachments.length} 項附件錯誤` : missing.length ? `${missing.length} 欄待補` : "等待核對"}</span>
    </div>
    <dl class="application-review-field-list">
      ${(item.preview_fields || []).map((field) => `
        <div class="application-review-field ${field.is_blank ? "is-blank" : ""} ${field.validation_error ? "is-invalid" : ""}">
          <dt><span>${escapeHtml(field.label)}</span><small>${field.required ? "必填" : "選填"}${field.sensitive ? " · 敏感資料" : ""}</small></dt>
          <dd>${field.validation_error ? `<span class="application-review-file-error">${escapeHtml(field.validation_error)}</span>${field.display_value ? `<small>${escapeHtml(field.display_value)}</small>` : ""}` : field.is_blank ? '<span class="application-review-blank">留白（不會猜測）</span>' : escapeHtml(field.display_value)}</dd>
        </div>`).join("")}
    </dl>
    <section class="application-review-signoff" aria-label="列印與簽核位置">
      <h4>列印與簽核位置</h4>
      <dl>
        <div><dt>列印</dt><dd>${item.copies} 份 · ${escapeHtml(item.paper_size)} · ${escapeHtml(applicationPrintSidesLabel(template))}</dd></div>
        <div><dt>簽名</dt><dd>${escapeHtml(list(item.signatures, "不需要"))}</dd></div>
        <div><dt>核章</dt><dd>${escapeHtml(list(item.stamps, "不需要"))}</dd></div>
        <div><dt>送件</dt><dd>${escapeHtml(list(item.destinations, "學生自存"))}</dd></div>
        <div><dt>附件順序</dt><dd>${escapeHtml(actualAttachments.length ? actualAttachments.join("；") : "無")}</dd></div>
      </dl>
    </section>
    ${missing.length ? `<p class="application-review-missing"><i data-lucide="circle-alert" aria-hidden="true"></i><span>先完成必填欄位：${escapeHtml(missing.join("、"))}</span></p>` : ""}
    ${invalidAttachments.length ? `<p class="application-review-missing"><i data-lucide="file-warning" aria-hidden="true"></i><span>附件無法加入列印包：${escapeHtml(invalidAttachments.join("、"))}</span></p>` : ""}
    <label class="application-review-control ${blocked ? "is-disabled" : ""}">
      <input type="checkbox" data-application-review-template="${escapeHtml(template.id)}" ${reviewed ? "checked" : ""} ${blocked ? "disabled" : ""} />
      <span><strong>我已核對以上目前內容</strong><small>我已逐欄確認資料、份數、簽名、核章與送件單位；任何資料或份數變更後都必須重新核對。</small></span>
    </label>`;
  initIcons();
}

function applyApplicationPreviewManifest(manifest) {
  let invalidated = false;
  (manifest?.items || []).forEach((item) => {
    state.applicationPreviews[item.template_id] = item;
    const selection = state.applicationSelections[item.template_id];
    if (
      selection?.reviewed_content_sha256
      && selection.reviewed_content_sha256 !== item.review_content_sha256
    ) {
      invalidated = invalidateApplicationReview(item.template_id, {
        persist: false,
        render: false,
      }) || invalidated;
    }
  });
  if (invalidated) persistApplicationContext();
  return manifest;
}

async function refreshApplicationReviewPreview(templateId, { showLoading = true } = {}) {
  if (!applicationDocumentGenerationEnabled()) return null;
  const template = applicationTemplateById(templateId);
  if (!template) return null;
  const requestId = (state.applicationPreviewRequestIds[templateId] || 0) + 1;
  state.applicationPreviewRequestIds[templateId] = requestId;
  if (showLoading) renderApplicationReviewPreview(template, { loading: true });
  try {
    const manifest = await fetchJson("/application-center/manifest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(applicationPacketPayload(templateId)),
    });
    if (state.applicationPreviewRequestIds[templateId] !== requestId) return null;
    applyApplicationPreviewManifest(manifest);
    renderApplicationReviewPreview(template);
    renderApplicationTemplates();
    renderApplicationPacket();
    updateApplicationCenterSteps();
    if (state.activeApplicationTemplateId === template.id) {
      const download = $("#download-single-application-document");
      if (download) {
        download.disabled = !applicationTemplateCompletion(template).ready
          || !applicationTemplateReviewed(template);
      }
      const next = $("#application-document-next-step");
      if (next) next.textContent = applicationDocumentNextStep(template);
    }
    return manifest.items?.[0] || null;
  } catch (error) {
    if (state.applicationPreviewRequestIds[templateId] === requestId) {
      renderApplicationReviewPreview(template, { error: error.message });
    }
    return null;
  }
}

function scheduleApplicationReviewPreview(templateId) {
  window.clearTimeout(state.applicationPreviewTimers[templateId]);
  state.applicationPreviewTimers[templateId] = window.setTimeout(() => {
    refreshApplicationReviewPreview(templateId, { showLoading: false });
  }, 300);
}

async function refreshSelectedApplicationPreviews() {
  if (!applicationDocumentGenerationEnabled()) return null;
  const selected = state.applicationTemplates.filter(
    (template) => state.applicationSelections[template.id]?.selected,
  );
  if (!selected.length) return null;
  try {
    const manifest = await fetchJson("/application-center/manifest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(applicationPacketPayload()),
    });
    applyApplicationPreviewManifest(manifest);
    renderApplicationTemplates();
    renderApplicationPacket();
    updateApplicationCenterSteps();
    return manifest;
  } catch (_) {
    return null;
  }
}

function renderApplicationFormPage(template) {
  if (!applicationDocumentGenerationEnabled()) {
    window.location.hash = "#application-center";
    return;
  }
  state.activeApplicationTemplateId = template.id;
  $("#application-form-stage").textContent = template.stage;
  $("#application-form-title").textContent = template.title;
  $("#application-form-description").textContent = template.description;
  const badge = $("#application-form-official-badge");
  badge.className = `application-official-badge ${template.official_layout ? "" : "is-preparation"}`;
  badge.textContent = template.official_layout ? "官方格式" : "申請整理";
  const fieldTree = $("#application-document-fields");
  const fieldTreeKey = JSON.stringify([captureAuthenticatedRequestContext(), activeHomeSchool(), state.applicationContext, template.id, template.version, template.fields]);
  if (fieldTree.dataset.renderKey !== fieldTreeKey) {
    fieldTree.innerHTML = template.fields.map((field) => {
      const inputId = `application-field-${field.id.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
      const showHeading = !["checkbox", "files"].includes(field.field_type);
      const help = field.help_text && field.field_type !== "files"
        ? `<details class="application-field-help"><summary aria-label="${escapeHtml(field.label)}填寫提示"><i data-lucide="circle-help" aria-hidden="true"></i></summary><p>${escapeHtml(field.help_text)}</p></details>`
        : "";
      return `
        <div class="application-document-field ${["textarea", "files"].includes(field.field_type) ? "is-wide" : ""} ${field.sensitive ? "is-sensitive" : ""}">
          ${showHeading ? `<div class="application-field-heading"><label for="${escapeHtml(inputId)}">${escapeHtml(field.label)}${applicationFieldRequired(template, field) ? " *" : ""}</label>${help}</div>` : ""}
          ${applicationFieldInput(template, field, inputId)}
        </div>`;
    }).join("");
    fieldTree.dataset.renderKey = fieldTreeKey;
  } else {
    // Background draft hydration can refresh the same route. Preserve the live
    // field nodes, focus, file selections and cursor while bringing in saved values.
    template.fields.forEach(field => {
      const input = $("#application-document-form").elements[field.id];
      if (!input || input === document.activeElement || field.field_type === "files") return;
      const value = applicationValue(template, field);
      if (field.field_type === "checkbox") input.checked = value === true;
      else if (input.value !== String(value ?? "")) input.value = String(value ?? "");
    });
  }
  refreshApplicationFieldConditions(template);
  renderApplicationAutofillStatus(template);
  window.UniWayDocumentWorkbench?.open(template);
  window.UniWayJourney.focusDocumentGap(template);
  renderApplicationDraftSyncStatus(template);
  template.fields.filter((field) => field.field_type === "files").forEach((field) => {
    renderApplicationFilePreview(template, field);
  });
  renderApplicationReviewPreview(template);
  refreshApplicationReviewPreview(template.id, { showLoading: !state.applicationPreviews[template.id] });
  const selection = state.applicationSelections[template.id] || { copies: template.default_copies };
  const list = (values) => values?.length ? values.join("、") : "不需要";
  const attachments = applicationAttachmentOrder(template);
  $("#application-form-print-guide").innerHTML = `
    <h3>送件資訊</h3>
    <dl>
      <div><dt>份數</dt><dd>${selection.copies || template.default_copies} 份</dd></div>
      <div><dt>紙張</dt><dd>${escapeHtml(template.paper_size || "A4")}</dd></div>
      <div><dt>單雙面</dt><dd>${escapeHtml(applicationPrintSidesLabel(template))}</dd></div>
      <div><dt>附件順序</dt><dd>${escapeHtml(attachments.length ? attachments.join(" → ") : "無")}</dd></div>
      <div><dt>送件</dt><dd>${escapeHtml(list(template.destinations))}</dd></div>
      <div><dt>簽名</dt><dd>${escapeHtml(list(template.signatures))}</dd></div>
      <div><dt>核章</dt><dd>${escapeHtml(list(template.stamps))}</dd></div>
      <div><dt>下一步</dt><dd id="application-document-next-step">${escapeHtml(applicationDocumentNextStep(template))}</dd></div>
    </dl>
    ${template.print_note ? `<p class="application-print-note"><i data-lucide="printer" aria-hidden="true"></i><span>${escapeHtml(template.print_note)}</span></p>` : ""}
    ${template.official_download_url ? `<a class="application-official-download" href="${escapeHtml(template.official_download_url)}" target="_blank" rel="noreferrer"><i data-lucide="file-down" aria-hidden="true"></i><span>下載校方原始表格</span></a>` : ""}
    <label class="application-status-control"><span>進度</span><select data-application-status-template="${escapeHtml(template.id)}">${APPLICATION_DOCUMENT_STATUSES.map(([value, label]) => `<option value="${value}" ${applicationDocumentStatus(template.id) === value ? "selected" : ""}>${label}</option>`).join("")}</select></label>
    ${template.conditional_note ? `<details class="application-compact-help"><summary><span><i data-lucide="info" aria-hidden="true"></i>注意事項</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><p>${escapeHtml(template.conditional_note)}</p></details>` : ""}`;
  const source = $("#application-form-source");
  source.href = template.source_url;
  const status = $("#application-document-form-status");
  status.textContent = "";
  const download = $("#download-single-application-document");
  if (download) download.disabled = !applicationTemplateCompletion(template).ready || !applicationTemplateReviewed(template);
  initIcons();
}

function collectApplicationDocumentForm({ validate = true, invalidateReview = true } = {}) {
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
  const existing = state.applicationSelections[template.id] || {};
  state.applicationSelections[template.id] = {
    selected: true,
    copies: existing.copies || template.default_copies,
    status: existing.status || "draft",
    reviewed_version: invalidateReview ? null : existing.reviewed_version || null,
    reviewed_content_sha256: invalidateReview ? null : existing.reviewed_content_sha256 || null,
    reviewed_at: invalidateReview ? null : existing.reviewed_at || null,
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
    reader.onload = () => resolve({ name: file.name, type: file.type, data_url: reader.result, source_file: file });
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
  invalidateApplicationReview(template.id);
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
    renderApplicationFilePreview(template, field);
    persistApplicationDraft();
    scheduleApplicationReviewPreview(template.id);
    if (encoded.length < minimum) input.reportValidity();
  } catch (error) {
    announce(error.message, "error", true);
  }
}

function applicationFileCategory(field) {
  const key = `${field?.id || ""} ${field?.label || ""}`.toLowerCase();
  if (/passport|護照/.test(key)) return "passport";
  if (/transcript|成績單/.test(key)) return "transcript";
  if (/student.?id|學生證/.test(key)) return "student_id";
  if (/financial|財力|bank|銀行/.test(key)) return "financial_proof";
  if (/recommend|推薦/.test(key)) return "recommendation";
  if (/study.?plan|讀書計畫/.test(key)) return "study_plan";
  return "application_form";
}

function applicationFilePurposeLabel(value) {
  return value === "cross_device_access" ? "跨裝置存取" : "準備與核對申請";
}

function renderApplicationFilePreview(template, field) {
  const preview = document.querySelector(`[data-application-file-preview="${field.id}"]`);
  if (!preview) return;
  const localFiles = state.applicationFiles?.[template.id]?.[field.id] || [];
  const savedFiles = activeApplicationAttachmentLinks(template.id)[field.id] || [];
  const savedNames = new Set(savedFiles.map((item) => item.file_name));
  const localRows = localFiles.map((file, index) => `
    <div class="application-file-preview-row is-local">
      <span><i data-lucide="monitor-dot" aria-hidden="true"></i></span>
      <div><strong>${escapeHtml(file.name || "附件")}</strong><small>只在本次分頁${savedNames.has(file.name) ? " · 已另存加密版本" : " · 尚未上傳"}</small></div>
      ${savedNames.has(file.name) ? '<em class="application-file-state">已保存</em>' : `<button type="button" class="secondary-button" data-application-file-consent data-template-id="${escapeHtml(template.id)}" data-field-id="${escapeHtml(field.id)}" data-file-index="${index}">${state.account ? "設定保存" : "登入後選擇保存"}</button>`}
    </div>`).join("");
  const savedRows = savedFiles.map((item) => `
    <div class="application-file-preview-row is-encrypted">
      <span><i data-lucide="file-lock-2" aria-hidden="true"></i></span>
      <div><strong>${escapeHtml(item.file_name)}</strong><small>${escapeHtml(applicationFilePurposeLabel(item.purpose))} · 保存至 ${escapeHtml(formatDate(item.expires_at).slice(0, 10))}</small></div>
      <div class="application-file-saved-actions"><button type="button" class="text-button" data-load-application-vault-file data-template-id="${escapeHtml(template.id)}" data-field-id="${escapeHtml(field.id)}" data-version-id="${escapeHtml(item.version_id)}">載入本次表單</button><button type="button" class="icon-button danger" data-delete-application-vault-file data-template-id="${escapeHtml(template.id)}" data-field-id="${escapeHtml(field.id)}" data-document-id="${escapeHtml(item.document_id)}" data-version-id="${escapeHtml(item.version_id)}" aria-label="撤回並永久刪除 ${escapeHtml(item.file_name)}"><i data-lucide="trash-2" aria-hidden="true"></i></button></div>
    </div>`).join("");
  preview.innerHTML = localRows || savedRows
    ? `${localRows}${savedRows}`
    : '<span class="application-file-preview-empty">尚未選擇檔案；沒有任何內容被上傳。</span>';
  initIcons();
}

function blobFromApplicationFile(file) {
  if (file?.source_file instanceof Blob) return file.source_file;
  const dataUrl = String(file?.data_url || "");
  const match = dataUrl.match(/^data:([^;,]+)?(?:;base64)?,(.*)$/);
  if (!match) return null;
  const type = match[1] || file.type || "application/octet-stream";
  try {
    const binary = atob(match[2]);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return new Blob([bytes], { type });
  } catch (_) {
    return null;
  }
}

function openApplicationFileConsent(templateId, fieldId, fileIndex) {
  const template = applicationTemplateById(templateId);
  const field = template?.fields.find((item) => item.id === fieldId);
  const file = state.applicationFiles?.[templateId]?.[fieldId]?.[Number(fileIndex)];
  if (!template || !field || !file) return;
  if (!state.account) {
    announce("只有選擇跨裝置加密保存時才需要登入；目前檔案仍只在本次分頁。", "info", true);
    openAuthDialog("login");
    return;
  }
  if (!entitlementFeatureEnabled("encrypted_document_vault")) {
    announce("目前方案尚未開放加密私人文件庫；檔案仍只在本次分頁。", "info", true);
    return;
  }
  const blob = blobFromApplicationFile(file);
  if (!blob) {
    announce("這個檔案已不在記憶體中，請重新選擇後再設定保存。", "error", true);
    return;
  }
  state.applicationFileConsentCandidate = {
    templateId,
    fieldId,
    fileIndex: Number(fileIndex),
    fileName: file.name || "private-document",
    fileType: file.type || blob.type,
    blob,
    label: `${template.short_title}－${field.label}`.slice(0, 100),
    category: applicationFileCategory(field),
  };
  const dialog = $("#application-file-consent-dialog");
  const form = $("#application-file-consent-form");
  form.reset();
  $("#application-file-consent-name").textContent = state.applicationFileConsentCandidate.fileName;
  $("#application-file-consent-context").textContent = `${template.short_title} · ${field.label} · ${APPLICATION_FILE_CATEGORY_LABELS[state.applicationFileConsentCandidate.category] || "私人文件"}`;
  $("#application-file-consent-status").textContent = "";
  dialog.showModal();
  initIcons();
}

function closeApplicationFileConsent() {
  const dialog = $("#application-file-consent-dialog");
  if (dialog?.open) dialog.close();
  state.applicationFileConsentCandidate = null;
}

async function submitApplicationFileConsent(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const candidate = state.applicationFileConsentCandidate;
  const status = $("#application-file-consent-status");
  const button = form.querySelector('button[type="submit"]');
  if (!candidate) {
    status.textContent = "找不到本次要保存的檔案，請重新選擇。";
    return;
  }
  if (!form.elements.consent.checked) {
    status.textContent = "必須針對這一個檔案勾選本次保存同意。";
    form.elements.consent.focus();
    return;
  }
  const payload = new FormData();
  payload.append("file", candidate.blob, candidate.fileName);
  payload.append("label", candidate.label);
  payload.append("category", candidate.category);
  payload.append("purpose", form.elements.purpose.value);
  payload.append("retention_days", form.elements.retention_days.value);
  payload.append("consent", "true");
  button.disabled = true;
  status.textContent = "正在加密並保存這一個檔案…";
  try {
    const documentItem = await fetchJson("/account/vault/documents", { method: "POST", body: payload });
    const version = documentItem.versions?.[0];
    if (!version) throw new Error("保存完成，但無法取得加密版本資料。");
    state.applicationFileVaultLinks[candidate.templateId] ||= {};
    state.applicationFileVaultLinks[candidate.templateId][candidate.fieldId] ||= [];
    state.applicationFileVaultLinks[candidate.templateId][candidate.fieldId].push({
      document_id: documentItem.id,
      version_id: version.id,
      label: documentItem.label,
      file_name: version.file_name,
      category: documentItem.category,
      purpose: version.purpose,
      retention_days: version.retention_days,
      expires_at: version.expires_at,
    });
    await saveApplicationFormDraft(candidate.templateId);
    const template = applicationTemplateById(candidate.templateId);
    const field = template?.fields.find((item) => item.id === candidate.fieldId);
    if (template && field) renderApplicationFilePreview(template, field);
    closeApplicationFileConsent();
    await loadPrivateVault({ quiet: true });
    announce("這一個檔案已依所選目的與期限加密保存", "success");
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function deleteApplicationVaultFile(button) {
  const { templateId, fieldId, documentId, versionId } = button.dataset;
  const links = state.applicationFileVaultLinks?.[templateId]?.[fieldId] || [];
  const reference = links.find((item) => item.version_id === versionId);
  if (!reference) return;
  const confirmed = window.confirm(`確定撤回保存同意並永久刪除「${reference.file_name}」的這個版本嗎？`);
  if (!confirmed) return;
  button.disabled = true;
  try {
    await fetchJson(`/account/vault/documents/${encodeURIComponent(documentId)}/versions/${encodeURIComponent(versionId)}`, { method: "DELETE" });
    state.applicationFileVaultLinks[templateId][fieldId] = links.filter((item) => item.version_id !== versionId);
    await saveApplicationFormDraft(templateId);
    const template = applicationTemplateById(templateId);
    const field = template?.fields.find((item) => item.id === fieldId);
    if (template && field) renderApplicationFilePreview(template, field);
    await loadPrivateVault({ quiet: true });
    announce("保存同意已撤回，加密檔案版本已永久刪除", "success");
  } catch (error) {
    announce(error.message, "error", true);
  } finally {
    button.disabled = false;
  }
}

function readBlobAsApplicationFile(blob, fileName) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({
      name: fileName,
      type: blob.type,
      data_url: reader.result,
      source_file: blob,
    });
    reader.onerror = () => reject(new Error(`無法載入 ${fileName}`));
    reader.readAsDataURL(blob);
  });
}

async function loadApplicationVaultFile(button) {
  const { templateId, fieldId, versionId } = button.dataset;
  const reference = (state.applicationFileVaultLinks?.[templateId]?.[fieldId] || [])
    .find((item) => item.version_id === versionId);
  if (!reference) return;
  const requestContext = captureAuthenticatedRequestContext();
  button.disabled = true;
  try {
    const grant = await fetchJson(`/account/vault/versions/${encodeURIComponent(versionId)}/download-grant`, { method: "POST" });
    const vaultResponse = await fetch(grant.download_url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-Vault-Download-Token": grant.token,
      },
    });
    if (!vaultResponse.ok) throw new Error("無法載入加密文件，請稍後重試。");
    const blob = await vaultResponse.blob();
    assertAuthenticatedRequestCurrent(requestContext);
    const file = await readBlobAsApplicationFile(blob, reference.file_name);
    state.applicationFiles[templateId] ||= {};
    const current = state.applicationFiles[templateId][fieldId] || [];
    state.applicationFiles[templateId][fieldId] = [
      ...current.filter((item) => item.name !== file.name),
      file,
    ];
    state.applicationAnswers[templateId] ||= {};
    state.applicationAnswers[templateId][fieldId] = state.applicationFiles[templateId][fieldId];
    invalidateApplicationReview(templateId);
    persistApplicationDraft();
    const template = applicationTemplateById(templateId);
    const field = template?.fields.find((item) => item.id === fieldId);
    if (template && field) {
      renderApplicationFilePreview(template, field);
      scheduleApplicationReviewPreview(template.id);
    }
    announce("已將加密文件載入本次表單；未新增其他保存副本", "success");
  } catch (error) {
    if (error.staleSession) return;
    announce(error.message, "error", true);
  } finally {
    button.disabled = false;
  }
}

function applicationSelectionsPayload(singleTemplateId = "") {
  const templates = singleTemplateId
    ? state.applicationTemplates.filter((template) => template.id === singleTemplateId)
    : state.applicationTemplates.filter((template) => state.applicationSelections[template.id]?.selected);
  return templates.map((template) => ({
    template_id: template.id,
    copies: Number(state.applicationSelections[template.id]?.copies || template.default_copies),
    reviewed_version: state.applicationSelections[template.id]?.reviewed_version || null,
    reviewed_content_sha256: state.applicationSelections[template.id]?.reviewed_content_sha256 || null,
    reviewed_at: state.applicationSelections[template.id]?.reviewed_at || null,
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

function applicationFilenameFromDisposition(disposition, fallback) {
  const utf8 = String(disposition || "").match(/filename\*=UTF-8''([^;]+)/i);
  const plain = String(disposition || "").match(/filename="?([^";]+)"?/i);
  let candidate = fallback;
  try {
    candidate = utf8 ? decodeURIComponent(utf8[1]) : plain?.[1] || fallback;
  } catch (_) {
    candidate = fallback;
  }
  return String(candidate || "交換申請-列印包.pdf").split(/[\\/]/).pop();
}

function downloadApplicationBlob(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function renderApplicationDownloadDialog() {
  document.querySelectorAll("[data-generated-document-action]").forEach(button => {
    button.hidden = !window.UniWayDocumentWorkbench?.currentDocumentCandidate();
  });
  const summary = state.applicationDownloadSummary;
  const dialog = $("#application-download-dialog");
  if (!summary || !dialog) return;
  const stats = $("#application-download-stats");
  const list = $("#application-download-list");
  stats.innerHTML = [
    [summary.pageCount || "--", "PDF 總頁數"],
    [summary.documentCount || summary.items.length, "文件種類"],
    [summary.copyCount || "--", "列印總份數"],
    [summary.attachmentCount || 0, "套件內附件"],
  ].map(([value, label]) => `<span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(label)}</small></span>`).join("");
  list.innerHTML = summary.items.map((item) => {
    const attachments = (item.attachments || []).map(applicationAttachmentLabel);
    const signatures = item.signatures?.length ? item.signatures.join("、") : "不需要";
    const stamps = item.stamps?.length ? item.stamps.join("、") : "不需要";
    const destinations = item.destinations?.length ? item.destinations.join("、") : "學生自存";
    const printSides = {
      single_sided: "單面列印",
      double_sided: "雙面列印",
      confirm_official: "單雙面仍須向承辦單位確認",
    }[item.print_sides] || "單雙面仍須確認";
    return `<li>
      <div class="application-download-item-heading"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.copies)} 份</span></div>
      <dl>
        <div><dt>列印</dt><dd>${escapeHtml(item.paper_size)} · ${escapeHtml(printSides)}</dd></div>
        <div><dt>附件</dt><dd>${escapeHtml(attachments.length ? attachments.join("；") : "無")}</dd></div>
        <div><dt>簽名</dt><dd>${escapeHtml(signatures)}</dd></div>
        <div><dt>核章</dt><dd>${escapeHtml(stamps)}</dd></div>
        <div><dt>送件</dt><dd>${escapeHtml(destinations)}</dd></div>
      </dl>
      ${item.print_note ? `<p>${escapeHtml(item.print_note)}</p>` : ""}
    </li>`;
  }).join("");
  if (!dialog.open) dialog.showModal();
  initIcons();
}

function closeApplicationDownloadDialog() {
  const dialog = $("#application-download-dialog");
  if (dialog?.open) dialog.close();
}

function downloadGeneratedApplicationPacketAgain() {
  const summary = state.applicationDownloadSummary;
  if (!summary?.blob) return;
  downloadApplicationBlob(summary.blob, summary.fileName);
  announce("PDF 已再次下載到你的裝置", "success");
}

async function generateApplicationPdf(singleTemplateId = "") {
  if (!state.account) {
    openAuthDialog();
    return;
  }
  if (!applicationDocumentGenerationEnabled()) {
    announce("目前方案未包含自動填表與申請文件套件產生。", "error", true);
    return;
  }
  if (singleTemplateId && !collectApplicationDocumentForm({ invalidateReview: false })) return;
  const payload = applicationPacketPayload(singleTemplateId);
  if (!payload.selections.length) {
    announce("請先選擇要加入列印包的文件", "error", true);
    return;
  }
  const button = singleTemplateId ? $("#download-single-application-document") : $("#download-application-packet");
  const requestContext = captureAuthenticatedRequestContext();
  const original = button?.innerHTML;
  const generatedHomeSchool = state.homeSchool;
  const generatedFingerprint = window.UniWayDocumentWorkbench.fingerprint(singleTemplateId);
  if (button) {
    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner" aria-hidden="true"></span><span>正在產生 PDF</span>';
  }
  try {
    const response = await fetch("/application-center/pdf", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/pdf" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `PDF 產生失敗（${response.status}）`);
    }
    const blob = await response.blob();
    assertAuthenticatedRequestCurrent(requestContext);
    if (generatedHomeSchool !== state.homeSchool || generatedFingerprint !== window.UniWayDocumentWorkbench.fingerprint(singleTemplateId)
      || (singleTemplateId && state.activeApplicationTemplateId !== singleTemplateId)) {
      throw new Error("文件或申請背景已變更，請回到該文件重新核對後下載。");
    }
    const template = applicationTemplateById(singleTemplateId);
    const fallbackName = `${template?.short_title || state.applicationContext.target_school || "交換申請"}-列印包.pdf`;
    const fileName = applicationFilenameFromDisposition(response.headers.get("Content-Disposition"), fallbackName);
    downloadApplicationBlob(blob, fileName);
    const selectedItems = payload.selections
      .map((selection) => state.applicationPreviews[selection.template_id])
      .filter(Boolean);
    state.applicationDownloadSummary = {
      blob,
      fileName,
      pageCount: Number(response.headers.get("X-Application-Packet-Pages")) || 0,
      documentCount: Number(response.headers.get("X-Application-Packet-Documents")) || selectedItems.length,
      copyCount: Number(response.headers.get("X-Application-Packet-Copies")) || payload.selections.reduce((sum, item) => sum + Number(item.copies || 0), 0),
      attachmentCount: Number(response.headers.get("X-Application-Packet-Attachments")) || 0,
      storage: response.headers.get("X-Application-Storage") || "request-only",
      items: selectedItems,
    };
    state.generatedVaultCandidate = {
      blob,
      fileName,
      label: template?.short_title || `${state.applicationContext.target_school || "交換申請"}列印包`,
      category: "generated_packet",
      templateId: singleTemplateId,
      requestContext,
      homeSchool: generatedHomeSchool,
      fingerprint: generatedFingerprint,
    };
    state.useGeneratedVaultCandidate = false;
    renderGeneratedVaultCandidate();
    window.UniWayDocumentWorkbench?.renderGenerated();
    window.UniWayDocumentWorkbench?.renderFlow();
    renderApplicationDownloadDialog();
    announce("PDF 已下載；如要跨裝置保存，請到文件庫另外同意", "success");
  } catch (error) {
    if (error.staleSession) return;
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
  populateBudgetFormValues(schoolName, plan);
}

function populateBudgetFormValues(schoolName, plan = {}) {
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

function renderBudgetAuthState() {
  const button = $("#budget-save-button");
  const note = $("#budget-save-note");
  if (button) {
    const label = button.querySelector("span");
    if (label) label.textContent = state.account ? "儲存並同步估算" : "登入後儲存估算";
  }
  if (note) {
    note.innerHTML = state.account
      ? '<i data-lucide="cloud" aria-hidden="true"></i><span>這份估算會保存到你的私人工作區，並在 Web 與之後核准的 App 同步。</span>'
      : '<i data-lucide="calculator" aria-hidden="true"></i><span>試算不需登入；只有要保存到私人工作區時才登入，訪客輸入不會寫入瀏覽器。</span>';
  }
  initIcons();
}

function renderBudgetPlanner() {
  const select = $("#budget-school");
  if (!select || !state.dashboard) return;
  const schools = state.dashboard.partner_universities.map((item) => item.school_name);
  const pending = state.pendingBudgetDraft && schools.includes(state.pendingBudgetDraft.schoolName)
    ? state.pendingBudgetDraft
    : null;
  const selected = pending?.schoolName || preferredBudgetSchool();
  fillSelect("#budget-school", schools, "請選擇學校", selected);
  if (selected) {
    if (pending) populateBudgetFormValues(selected, pending);
    else populateBudgetForm(selected);
  }
  renderBudgetAuthState();
}

function saveBudgetPlan(event) {
  event.preventDefault();
  const values = budgetValuesFromForm();
  if (!values.schoolName) {
    announce("請先選擇要估算的學校", "error");
    return;
  }
  if (!state.account) {
    state.pendingBudgetDraft = values;
    renderBudgetAuthState();
    requireAccountForPrivateAction("登入後才會保存並同步這份交換預算；目前試算仍保留在這個分頁。");
    return;
  }
  state.pendingBudgetDraft = null;
  state.budgetPlans[values.schoolName] = { ...values, savedAt: new Date().toISOString() };
  persistAccountWorkspaceLocally();
  scheduleAccountWorkspaceSync();
  updateBudgetResult();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  announce("交換預算已保存，將與帳號同步", "success");
}

let partnerMapController = null;
let partnerMapLoadPromise = null;
let partnerMapLoadFailed = false;
let partnerMapGeneration = 0;
let partnerUrlSearch = "";
const PARTNER_QUERY_KEYS = { partnerQuery: "q", region: "region", country: "country", availability: "availability", college: "college", degree: "degree" };

function readPartnerUrl() {
  const previousFilters = JSON.stringify(Object.keys(PARTNER_QUERY_KEYS).map((key) => state[key]));
  const query = new URLSearchParams(window.location.search);
  state.partnerView = query.get("view") === "map" ? "map" : "list";
  Object.entries(PARTNER_QUERY_KEYS).forEach(([key, parameter]) => { state[key] = query.get(parameter) || ""; });
  $("#partner-search").value = state.partnerQuery;
  if (state.dashboard) renderPartnerFilters();
  partnerUrlSearch = window.location.search;
  return previousFilters !== JSON.stringify(Object.keys(PARTNER_QUERY_KEYS).map((key) => state[key]));
}

function writePartnerUrl({ push = false } = {}) {
  const url = new URL(window.location.href);
  url.searchParams.set("view", state.partnerView);
  Object.entries(PARTNER_QUERY_KEYS).forEach(([key, parameter]) => {
    if (state[key]) url.searchParams.set(parameter, state[key]);
    else url.searchParams.delete(parameter);
  });
  if (state.homeSchool) url.searchParams.set("home", activeHomeSchool());
  if (url.href !== window.location.href) window.UniWayNavigation[push ? "pushState" : "replaceState"](window.history.state, "", url);
  partnerUrlSearch = window.location.search;
}

function setPartnerView(view) {
  if (!["list", "map"].includes(view) || state.partnerView === view) return;
  state.partnerView = view;
  writePartnerUrl({ push: true });
  syncPartnerView();
}

function renderMapPreview(item) {
  const location = item.location || {}, availability = partnerAvailabilityMeta(item);
  const language = partnerSummaryPoints(item, "eligibility_points");
  return `<div class="map-preview-top">
    <button type="button" class="map-preview-close" data-close-map-preview aria-label="關閉學校預覽">×</button>
    ${renderSchoolPhoto(item, "map")}
    <div class="map-preview-place">${escapeHtml([location.city, item.country].filter(Boolean).join(" · "))}</div>
    <h4>${escapeHtml(item.school_name)}</h4>
    <span class="coverage-chip ${availability.blocked ? "empty" : ""}">${escapeHtml(availability.shortLabel)}</span>
  </div><div class="map-preview-body"><dl>
    <dt>交換名額</dt><dd>${escapeHtml(item.quota || "待公告")}</dd>
    <dt>研修期間</dt><dd>${escapeHtml(localizedPartnerValue(item, "study_period", "study_period"))}</dd>
    <dt>語言與資格</dt><dd>${escapeHtml(truncate(language.join("；") || item.eligibility || "待確認", 160))}</dd>
  </dl>${discoveryMatchBadge(item)}${discoveryPreviewExtras(item)}
    <div class="map-preview-actions"><button type="button" class="primary-button school-detail-trigger" data-school-name="${escapeHtml(item.school_name)}">查看詳細資料 <span aria-hidden="true">↗</span></button>${renderFavoriteButton(item)}</div>
    <details class="map-location-note"><summary>校區與資料來源</summary><p>${escapeHtml(location.note || "校級代表位置，實際校區以錄取資訊為準。")}</p>${renderPartnerLinks(item)}</details>
  </div>`;
}

function showPartnerMapStatus(title, message, { retry = false, loading = false } = {}) {
  const status = $("#partner-map-status");
  status.hidden = false;
  status.innerHTML = `${loading ? '<span class="map-loading-orbit" aria-hidden="true"></span>' : ""}<strong>${escapeHtml(title)}</strong><p>${escapeHtml(message)}</p>${loading ? "" : `<div class="map-status-actions">${retry ? '<button type="button" class="primary-button" data-map-retry>重新嘗試</button>' : ""}<button type="button" class="secondary-button" data-map-list>返回列表</button></div>`}`;
  status.querySelector("[data-map-list]")?.addEventListener("click", () => setPartnerView("list"));
  status.querySelector("[data-map-retry]")?.addEventListener("click", () => {
    if (state.partnerDataError || catalogueSourceUnavailable()) loadDashboard();
    else retryPartnerMap();
  });
}

function retryPartnerMap() {
  partnerMapGeneration += 1;
  partnerMapController?.destroy(); partnerMapController = null;
  partnerMapLoadPromise = null; partnerMapLoadFailed = false;
  syncPartnerView();
}

function partnerMapSnapshot() {
  return {
    partners: filteredPartners(), home: activeUniversityProfile(), homeSelected: Boolean(state.homeSchool), country: state.country,
    filterKey: Object.keys(PARTNER_QUERY_KEYS).map((key) => state[key]).filter(Boolean).join("\u001f") + (UniWayDiscovery.hasCriteria(discoveryCriteria) ? JSON.stringify(discoveryCriteria) : ""),
  };
}

function syncPartnerView() {
  renderCatalogAccessGate();
  const panel = $("#partner-map-panel");
  if (!panel) return;
  if (!canAccessPartnerCatalog()) {
    panel.hidden = true;
    $("#partner-table").hidden = true;
    $("#show-more-partners").hidden = true;
    partnerMapController?.setVisible(false);
    return;
  }
  const isMap = state.partnerView === "map";
  panel.hidden = !isMap;
  $("#partner-table").hidden = isMap;
  $("#show-more-partners").hidden = isMap || filteredPartners().length <= state.partnerLimit;
  document.querySelectorAll("[data-partner-view]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.partnerView === state.partnerView)));
  const active = isMap && !$("#partners").hidden && !$("#dashboard-view").hidden;
  partnerMapController?.setVisible(active);
  if (!active) return;
  if (state.partnerDataLoading || !state.dashboard && !state.partnerDataError) {
    showPartnerMapStatus("正在取得合作學校", "即將載入你的交換網絡。", { loading: true }); return;
  }
  if (state.partnerDataError) {
    $("#partner-map-preview").hidden = true;
    showPartnerMapStatus("暫時無法取得學校資料", "請確認連線後重試；你的搜尋與篩選條件已保留。", { retry: true }); return;
  }
  if (catalogueSourceUnavailable()) {
    $("#partner-map-preview").hidden = true;
    showPartnerMapStatus("合作校來源暫不可用", "尚無可用的歷次資料，請稍後重新讀取來源狀態。", { retry: true }); return;
  }
  if (partnerMapController) { partnerMapController.update(partnerMapSnapshot()); return; }
  if (partnerMapLoadPromise || partnerMapLoadFailed) return;
  showPartnerMapStatus("正在準備你的世界地圖", "首次載入需要一點時間。", { loading: true });
  const generation = partnerMapGeneration;
  partnerMapLoadPromise = import(`/static/partner-map.js?v=20261011-integration-1&attempt=${generation}`)
    .then((module) => module.createPartnerMap({ renderPreview: renderMapPreview, onSchoolSelect: loadDiscoveryPreview, onList: () => setPartnerView("list"), onRetry: retryPartnerMap, onIcons: initIcons, freshEngine: generation > 0 }))
    .then((controller) => {
      if (generation !== partnerMapGeneration) { controller.destroy(); return; }
      partnerMapController = controller;
      controller.update(partnerMapSnapshot());
      syncPartnerView();
    })
    .catch(() => {
      if (generation !== partnerMapGeneration) return;
      partnerMapLoadFailed = true;
      showPartnerMapStatus("地圖暫時無法載入", "請重新嘗試，或返回列表繼續找學校。", { retry: true });
    })
    .finally(() => { if (generation === partnerMapGeneration) partnerMapLoadPromise = null; });
}

function renderPartnerFilters() {
  const partners = state.dashboard.partner_universities;
  const regions = window.UniWayRegions;
  const allCountries = unique(partners.map((item) => item.country));
  // A region that does not exist (a made-up address) is dropped, so it cannot hide every school.
  if (state.region && !regions.isRegion(state.region)) state.region = "";
  const countries = state.region ? allCountries.filter((country) => regions.inRegion(country, state.region)) : allCountries;
  const colleges = homeCollegeOptions();
  state.college = homeCollegeValue(state.college);
  const degrees = window.UniWayAcademicUnits?.[activeHomeSchool()]?.degreeFilterOptions
    || unique(partners.flatMap((item) => splitOptions(item.degree_levels)));
  fillRegionSelect("#region-filter", allCountries, state.region);
  fillCountrySelect("#country-filter", countries, state.country);
  fillSelect("#college-filter", colleges, "全部學院", state.college);
  fillSelect("#degree-filter", degrees, "全部學制", state.degree);
  // Empty URL filters are explicit resets, not a request to keep the old select value.
  ["region", "country", "college", "degree", "availability"].forEach((key) => {
    $(`#${key}-filter`).value = state[key];
  });
}

function partnerQuotaNumber(item) {
  const match = String(item?.quota ?? "").match(/\d+/);
  return match ? Number(match[0]) : null;
}

// The earliest upcoming date written in the partner's deadline fields; null when the text names none.
const partnerDeadlineCache = new WeakMap();
function partnerNextDeadline(item) {
  if (partnerDeadlineCache.has(item)) return partnerDeadlineCache.get(item);
  const sources = [item?.partner_exchange_details?.application_deadline?.value, item?.nomination_deadline, item?.partner_application_deadline,
    partnerStudentSummary(item).application_deadline, item?.application_deadline];
  const today = parseLocalDate(localDateKey());
  let best = null;
  for (const text of sources.map((value) => String(value || ""))) {
    const dates = [];
    for (const [, year, month, day] of text.matchAll(/(20\d{2})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})/g)) dates.push(new Date(Number(year), Number(month) - 1, Number(day), 12));
    for (const [, month, day] of text.replace(/20\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}/g, " ").matchAll(/(\d{1,2})\s*月\s*(\d{1,2})\s*日?/g)) {
      const candidate = new Date(today.getFullYear(), Number(month) - 1, Number(day), 12);
      if (candidate < today) candidate.setFullYear(candidate.getFullYear() + 1);
      dates.push(candidate);
    }
    const upcoming = dates.filter((date) => !Number.isNaN(date.getTime()) && date >= today).sort((a, b) => a - b)[0];
    if (upcoming && (!best || upcoming < best)) best = upcoming;
    if (best) break;
  }
  partnerDeadlineCache.set(item, best);
  return best;
}

function partnerFitBucket(item) {
  if (!state.eligibilityProfile) return "";
  const tone = partnerMatch(item).tone;
  return tone === "strong" ? "fit" : tone === "review" ? "review" : "";
}

function filteredPartners({ ignore = "", sort = true } = {}) {
  if (!state.dashboard) return [];
  const query = normalize(state.partnerQuery);
  const partners = state.dashboard.partner_universities.filter((item) => {
    const destination = destinationProfileForSchool(item.school_name);
    const text = normalize(
      `${Object.values(item).join(" ")} ${item.location?.city || ""} ${JSON.stringify(item.student_summary_zh || {})} ${Object.values(destination || {}).join(" ")} ${window.UniWayRegions.searchText(item.country)}`
    );
    const quota = partnerQuotaNumber(item);
    return (
      (!query || text.includes(query)) &&
      (!state.availability || (item.availability_status || "open") === state.availability) &&
      window.UniWayRegions.inRegion(item.country, state.region) &&
      (ignore === "country" || !state.country || item.country === state.country) &&
      (!state.college || academicScopeNeedsConfirmation(item, "colleges") || collegeMatches(item.colleges, state.college)) &&
      (!state.degree || academicScopeNeedsConfirmation(item, "degree_levels") || degreeMatches(item.degree_levels, state.degree) !== false) &&
      (ignore === "quota" || !state.partnerQuota || (state.partnerQuota === "2plus" ? (quota ?? 0) >= 2 : quota === 1)) &&
      (ignore === "fit" || !state.partnerFit || partnerFitBucket(item) === state.partnerFit) &&
      coupledAcademicScopeMatches(item, state.college, state.degree) !== false && discoveryCriteriaMatch(item)
    );
  });
  if (!sort) return partners;
  if (state.partnerSort === "deadline") {
    partners.sort((left, right) => (partnerNextDeadline(left)?.getTime() ?? Infinity) - (partnerNextDeadline(right)?.getTime() ?? Infinity));
  } else if (state.partnerSort === "quota") {
    partners.sort((left, right) => (partnerQuotaNumber(right) ?? -1) - (partnerQuotaNumber(left) ?? -1));
  } else if (state.eligibilityProfile) {
    partners.sort((left, right) => partnerMatch(right).score - partnerMatch(left).score);
  }
  return partners;
}

function academicScopeNeedsConfirmation(item, key) {
  const status = item.field_evidence?.[key]?.status;
  if (status && status !== "verified_current") return true;
  const text = normalize(item[key]);
  if (!text || ["無", "none", "n/a", "na", "--", "—", "待補"].includes(text)
      || ["待確認", "依當期", "依協議", "依合作", "另洽", "未提供", "不含", "除外", "excluding", "except"].some(term => text.includes(term))) return true;
  const terms = key === "colleges"
    ? ["學院", "全校", "不限", "四院皆可", "工程", "工學", "管理", "商", "人文", "法律", "法學", "理學", "社科", "社會", "醫", "生命", "資訊", "藝術", "engineering", "business", "management", "law", "science", "humanities", "arts", "medicine", "faculty", "college"]
    : ["大學部", "學士", "本科", "研究所", "碩士", "博士", "不限", "全校", "undergraduate", "bachelor", "graduate", "master", "doctoral", "phd"];
  return !terms.some(term => text.includes(term)) && !(key === "colleges" && /\ball\b/i.test(text));
}

function coupledAcademicScopeOptions(item) {
  const options = item.program_options || [];
  if (!options.length) return null;
  if (["colleges", "degree_levels"].some(key => item.field_evidence?.[key]?.status !== "verified_current")) return null;
  const urls = new Set([item.field_evidence.colleges.source_url, item.field_evidence.degree_levels.source_url]);
  if (options.some(option => !urls.has(option.source_url) || academicScopeNeedsConfirmation(option, "colleges") || academicScopeNeedsConfirmation(option, "degree_levels"))) return null;
  return options;
}

function coupledAcademicScopeMatches(item, college, degree) {
  const options = coupledAcademicScopeOptions(item);
  if (!college || !degree || options === null) return null;
  const matches = options.filter(option => collegeMatches(option.colleges, college)).map(option => degreeMatches(option.degree_levels, degree));
  return matches.includes(true) ? true : matches.includes(null) ? null : false;
}

function resolvedDegreeLevel(degree, currentYear) {
  if (degree !== "研究所") return degree;
  const year = normalize(currentYear).normalize("NFKC");
  const master = year.includes("碩士") || /\bmaster(?:'s)?\b/i.test(year);
  const doctoral = year.includes("博士") || /\b(?:ph\.?d\.?|doctoral)\b/i.test(year);
  return master !== doctoral ? master ? "碩士班" : "博士班" : degree;
}

function partnerDegreeScopeMatches(item, college, degree) {
  if (college && coupledAcademicScopeOptions(item) !== null) return coupledAcademicScopeMatches(item, college, degree);
  return degreeMatches(item.degree_levels, degree);
}

function collegeMatches(value, selected) {
  const text = normalize(value).normalize("NFKC");
  if (["不限", "全校", "各學院", "四院皆可"].some(term => text.includes(term)) || /\ball\b/i.test(text)) return true;
  const aliases = {"醫學院":["醫學","medicine","medical"],"工學院":["工學","工程","engineering"],"法律學院":["法律","法學","law"],"智慧運算學院":["智慧運算","資訊","computer","informatics"],"管理學院":["管理","商學","business","management"],"資訊工程學系":["資訊","電腦","computer","informatics"]};
  return [selected, ...(aliases[selected] || [])].some(term => term && text.includes(normalize(term).normalize("NFKC")));
}

function degreeMatches(value, selected) {
  const text = normalize(value);
  if (selected === "研究所") {
    const master = degreeMatches(value, "碩士班"), doctoral = degreeMatches(value, "博士班");
    return master && doctoral ? true : master || doctoral ? null : false;
  }
  const aliases = {"大學部":["大學部","學士","undergraduate","bachelor"],"碩士班":["碩士","研究所","master","graduate"],"博士班":["博士","研究所","doctoral","phd","graduate"],"研究所":["研究所","碩士","博士","graduate","master","doctoral","phd"]};
  return (aliases[selected] || [selected]).some(term => /^[a-z]+$/i.test(term)
    ? new RegExp(`(?<![a-z])${term}(?![a-z])`, "i").test(text)
    : text.normalize("NFKC").includes(normalize(term).normalize("NFKC")));
}

// How many schools one page of the list shows, and how many each "show more" adds.
function partnerPageSize() {
  return window.matchMedia("(max-width: 820px)").matches ? 20 : 30;
}

function renderPartnerCount(total, shown) {
  if (catalogueSourceUnavailable()) { $("#partner-result-count").textContent = "來源暫不可用"; return; }
  const line = $("#partner-result-count");
  if (!line) return;
  line.textContent = !total ? "" : shown < total ? `共 ${total} 所，先顯示 ${shown} 所` : `共 ${total} 所`;
}

function renderPartnerTable() {
  const expandedSchools = new Set([...document.querySelectorAll("#partner-table .partner-card[open]")]
    .map((card) => card.closest("[data-school-card]")?.dataset.schoolCard));
  const partners = filteredPartners();
  const visible = partners.slice(0, state.partnerLimit);
  $("#partner-table").dataset.resultCount = String(partners.length);
  renderPartnerCount(partners.length, visible.length);

  if (!partners.length) {
    renderEmpty("#partner-table", catalogueSourceUnavailable() ? "合作校來源暫不可用" : "沒有符合的學校", catalogueSourceUnavailable() ? "尚無可用的歷次資料，請稍後重新讀取或前往官方來源確認。" : "調整國家、學院、學制或關鍵字後再試一次。");
    $("#show-more-partners").hidden = true;
    if (window.location.hash === "#partners") writePartnerUrl();
    syncPartnerView();
    window.UniWayExplore?.render();
    return;
  }

  $("#partner-table").innerHTML = `<div class="pr-school-grid">${visible.map(renderPartnerCard).join("")}</div>`;
  document.querySelectorAll("#partner-table .partner-card").forEach((card) => {
    if (expandedSchools.has(card.closest("[data-school-card]")?.dataset.schoolCard)) card.open = true;
  });

  const moreButton = $("#show-more-partners");
  const remaining = partners.length - visible.length;
  moreButton.hidden = remaining <= 0;
  moreButton.textContent = remaining > 0 ? `顯示更多學校（還有 ${remaining} 所）` : "";
  if (window.location.hash === "#partners") writePartnerUrl();
  syncPartnerView();
  window.UniWayExplore?.render();
  initIcons();
}

function partnerCardBadge(availability, match) {
  if (availability.blocked || availability.pending) return { tone: "warn", label: availability.cardLabel };
  if (state.eligibilityProfile) return match.tone === "strong" ? { tone: "ok", label: "符合資格" } : { tone: "warn", label: match.label };
  return { tone: "ok", label: availability.cardLabel };
}

// Short chips taken from the catalogue itself; nothing is invented when a field is missing.
function partnerCardTags(item) {
  const tags = [];
  const language = (item.language_conditions || []).map((condition) => condition.teaching_language).find(Boolean);
  if (language) tags.push(`${language}授課`);
  if (item.program_type) tags.push(item.program_type);
  const quota = partnerQuotaNumber(item);
  if (quota !== null) tags.push(`名額 ${quota}`);
  const period = localizedPartnerValue(item, "study_period", "study_period", "");
  if (period && period.length <= 12) tags.push(period);
  return [...new Set(tags)].slice(0, 3);
}

function partnerCardFoot(item) {
  const next = partnerNextDeadline(item);
  return next
    ? `<strong>截止 ${next.getMonth() + 1}/${String(next.getDate()).padStart(2, "0")}</strong> · ${escapeHtml(partnerDeadlineReference(item).label)}`
    : `<span>截止日請依官方公告</span>`;
}

function renderPartnerCard(item) {
  const availability = partnerAvailabilityMeta(item);
  const period = localizedPartnerValue(item, "study_period", "study_period");
  const deadline = partnerDeadlineReference(item);
  const match = partnerMatch(item);
  const badge = partnerCardBadge(availability, match);
  const name = escapeHtml(item.school_name);
  const comparing = discoveryCompare.has(item.school_name);
  const place = [item.country, item.location?.city].filter(Boolean).join("・");
  const rating = state.schoolRatings?.[item.school_name];
  return `
    <article class="pr-school-card" data-school-card="${name}">
      <div class="pr-card-media">
        <details class="partner-card">
          <summary aria-label="${name}：展開重點條件">
            ${renderSchoolPhoto(item, "card")}
            <span class="pr-badge pr-badge-${badge.tone}">${escapeHtml(badge.label)}</span>
          </summary>
          <div class="partner-card-content">
            <div class="coverage-chips">${renderCoverageBadges(item)}</div>
            ${renderPartnerAvailabilityNotice(item)}
            <div class="partner-facts">
              <div class="partner-fact"><span>計畫</span><strong>${escapeHtml(item.program_type || "依公告")}</strong></div>
              <div class="partner-fact"><span>名額</span><strong>${escapeHtml(item.quota || "依公告")}</strong></div>
              <div class="partner-fact"><span>研修期間</span><strong>${escapeHtml(period)}</strong></div>
              <div class="partner-fact"><span>${escapeHtml(deadline.label)}</span><strong>${highlightHtml(deadline.value)}</strong></div>
              <div class="partner-fact"><span>適用身分</span><strong>${escapeHtml([item.colleges, item.degree_levels].filter(Boolean).join("／") || "依公告")}</strong></div>
            </div>
            <div class="partner-card-summary"><strong>申請重點</strong>${renderStudentPointList(partnerSummaryPoints(item, "eligibility_points"), { limit: 3 })}</div>
            ${state.eligibilityProfile ? `<div class="partner-match-reasons"><strong>為什麼排在這裡</strong><ul>${match.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}${match.risks.map((risk) => `<li class="risk">${escapeHtml(risk)}</li>`).join("")}</ul></div>` : ""}
            <div class="partner-links">${renderPartnerLinks(item)}</div>
          </div>
        </details>
        ${renderFavoriteButton(item, true, { heart: true })}
        <label class="pr-compare${comparing ? " on" : ""}"><input type="checkbox" data-compare-pick="${name}"${comparing ? " checked" : ""} /><span class="pr-compare-box" aria-hidden="true"><i data-lucide="check"></i></span><span>加入比較</span></label>
      </div>
      <div class="pr-card-body">
        <div class="pr-card-title">
          <button type="button" class="partner-name school-detail-trigger" data-school-name="${name}">${name}</button>
          ${rating ? `<span class="pr-rating"><i data-lucide="star" aria-hidden="true"></i>${escapeHtml(String(rating.average))}<small>（${escapeHtml(String(rating.count))}）</small></span>` : ""}
        </div>
        <span class="pr-card-place">${escapeHtml(place || "未標示國家")}</span>
        ${availability.hint ? `<small class="availability-hint">${escapeHtml(availability.hint)}</small>` : ""}
        ${renderPartnerMatchExplanation(match)}
        ${discoveryMatchBadge(item)}
        <div class="pr-tags">${partnerCardTags(item).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>
        <span class="pr-card-foot">${partnerCardFoot(item)}</span>
      </div>
    </article>`;
}

function partnerStudentSummary(item) {
  return item?.student_summary_zh || {};
}

function localizedPartnerValue(item, summaryKey, rawKey, fallback = "依公告") {
  const value = partnerStudentSummary(item)[summaryKey] || item?.[rawKey];
  return value || fallback;
}

function partnerDeadlineReference(item) {
  const receiving = item?.partner_exchange_details?.application_deadline;
  if (receiving) {
    const statuses = {verified_current: "當期已核實", conflict: "來源矛盾，待確認", reference_only: "其他年度／梯次參考", needs_confirmation: "適用年度或條件待確認", missing: "本期未核實", explicit_not_announced: "官方明示尚未公告"};
    const value = `${statuses[receiving.status] || "待確認"}：${receiving.value || receiving.reason}`;
    return {label: "合作校申請截止", value, compact: `合作校申請：${value}`};
  }
  const rawValue = partnerStudentSummary(item).application_deadline || item?.application_deadline;
  const value = String(rawValue || "").trim();
  if (activeUniversityProfile().id === "tku") {
    const hostDeadline = value || "外校當期期限尚未核實";
    return { label: "外校申請期限（獲母校推薦後）", value: hostDeadline,
      compact: `外校期限：${hostDeadline}` };
  }
  const fallback = "當期公告待確認";
  if (!value) {
    return {
      label: "合作校參考時程",
      value: fallback,
      compact: `參考時程：${fallback}`,
    };
  }
  const alreadyQualified = /適用年度待確認|年份待確認|依.*公告|待確認|未定|提名信/.test(value);
  const qualifiedValue = alreadyQualified ? value : `${value}（適用年度待確認）`;
  return {
    label: "合作校參考時程",
    value: qualifiedValue,
    compact: `參考時程：${qualifiedValue}`,
  };
}

function partnerSummaryPoints(item, key) {
  const points = partnerStudentSummary(item)[key];
  if (Array.isArray(points) && points.length) return points.filter(Boolean);
  if (activeHomeSchool() === "國立臺灣大學") {
    const rawKey = { eligibility_points: "eligibility", application_steps: "application_info", tuition_points: "tuition_info" }[key];
    if (rawKey && item[rawKey]) return ["官方參考資料；116-1適用年度及身分仍待確認。", item[rawKey], `來源：${item.source_url}`];
  }
  return [];
}

function renderStudentPointList(points, { limit = 4, compact = false, fallback = "尚無資料", expandRemaining = false } = {}) {
  const all = (points || []).filter(Boolean);
  const visible = all.slice(0, limit);
  const values = visible.length ? visible : [fallback];
  const list = `<ul class="student-point-list${compact ? " compact" : ""}">${values
    .map((point) => `<li>${renderSummaryText(point)}</li>`)
    .join("")}</ul>`;
  return list + (expandRemaining && all.length > limit
    ? `<details class="partner-summary-more"><summary>查看其餘 ${all.length - limit} 項說明</summary>${renderStudentPointList(all.slice(limit), { limit: all.length, compact, fallback })}</details>`
    : "");
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
  const visual = schoolVisualRecordFor(item.school_name, item.country);
  const imagePage = visual?.official_page_url || item.image_page_url;
  const imageSource = imagePage
    ? `<a href="${escapeHtml(imagePage)}" target="_blank" rel="noreferrer">圖片來源</a>${renderSchoolImageCredit(item)}`
    : renderSchoolImageCredit(item);
  const rankingSource = item.ranking_source_url
    ? `<a href="${escapeHtml(item.ranking_source_url)}" target="_blank" rel="noreferrer">排名來源</a>`
    : "";
  return [website, source, imageSource, rankingSource].filter(Boolean).join("");
}

function renderSchoolImageCredit(item, includeNote = true) {
  const visual = schoolVisualRecordFor(item.school_name, item.country);
  const sourceNote = visual?.note || "";
  const note = visual?.artist && !sourceNote.includes(visual.artist)
    ? `攝影：${visual.artist} · ${visual.license_name || ""} · ${sourceNote}` : sourceNote;
  if (visual && visual.status !== "verified") return `<small class="school-image-credit">${visual.status === "needs_review" ? "照片待核對" : "照片待補"}：${escapeHtml(note || "尚未取得可核實的照片與授權來源。")}</small>`;
  if (visual?.license_name) {
    const license = String(visual.license_url || "").replace(/^http:\/\//, "https://");
    const safeLicense = /^https:\/\/(?:creativecommons\.org|commons\.wikimedia\.org)\//.test(license);
    const authorUrl = activeHomeSchool() === "國立中央大學" ? safeSourceUrl(visual.author_url) : "";
    return `<small class="school-image-credit">${includeNote ? escapeHtml(note) : ""}${safeLicense ? ` · <a href="${escapeHtml(license)}" target="_blank" rel="noreferrer">圖片授權</a>` : ""}${authorUrl ? ` · <a href="${escapeHtml(authorUrl)}" target="_blank" rel="noreferrer">攝影者網站</a>` : ""}</small>`;
  }
  if (!note.startsWith("攝影：")) return visual ? '<small class="school-image-credit">圖片來源已核對；再利用授權待確認。</small>' : "";
  return `<small class="school-image-credit">${escapeHtml(note)}${note.includes("CC BY-SA 3.0") ? ' · <a href="https://creativecommons.org/licenses/by-sa/3.0/" target="_blank" rel="noreferrer">圖片授權</a>' : ""}</small>`;
}

function partnerByName(schoolName) {
  return state.dashboard?.partner_universities.find(
    (item) => normalize(item.school_name) === normalize(schoolName)
  );
}

function activeSchoolSelections() {
  discoveryData();
  return state.account ? state.favorites : state.guestComparisons;
}

function renderFavoriteButton(item, iconOnly = false, { heart = false } = {}) {
  const saved = activeSchoolSelections().has(item.school_name);
  const label = state.account
    ? (saved ? "已收藏" : "收藏")
    : (saved ? "已加入比較" : "加入比較");
  const ariaLabel = state.account
    ? `${saved ? "取消收藏" : "收藏"}${item.school_name}`
    : `${saved ? "移出比較" : "加入比較"}${item.school_name}`;
  return `
    <button type="button" class="${iconOnly ? "icon-button" : "secondary-button"} favorite-toggle${saved ? " saved" : ""}" data-school-name="${escapeHtml(item.school_name)}" aria-pressed="${saved}" aria-label="${escapeHtml(ariaLabel)}"${iconOnly ? ` data-tooltip="${escapeHtml(state.account ? (saved ? "取消收藏" : "收藏") : (saved ? "移出比較" : "加入比較"))}"` : ""}>
      <i data-lucide="${heart ? "heart" : state.account ? (saved ? "bookmark-check" : "bookmark") : (saved ? "list-checks" : "list-plus")}" aria-hidden="true"></i>${iconOnly ? "" : `<span>${label}</span>`}
    </button>`;
}

function toggleFavorite(schoolName) {
  if (!schoolName) return;
  const selections = activeSchoolSelections();
  const removing = selections.has(schoolName);
  if (removing) selections.delete(schoolName);
  else selections.add(schoolName);
  if (removing) discoveryData().preference_order = discoveryData().preference_order.filter(name => name !== schoolName);
  persistDiscovery();
  if (state.account) {
    try {
      window.localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify([...state.favorites]));
    } catch (_) {
      // Favorites still work for this signed-in session.
    }
    scheduleAccountWorkspaceSync();
  } else {
    announce(
      removing
        ? "已從選校清單移除。"
        : "已加入選校清單，儲存在此裝置。",
      "info"
    );
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
  const count = activeSchoolSelections().size;
  const countBadge = $("#favorite-count");
  if (countBadge) countBadge.textContent = `${count} 所`;
  const navCount = $("#nav-favorite-count");
  if (navCount) {
    navCount.textContent = String(count);
    navCount.hidden = count === 0;
  }
  window.UniWayHome?.render();
}

function renderFavorites() {
  renderDiscoveryWorkspace();
}

function renderComparison(items) {
  const rows = [
    ["國家", (item) => item.country || "依公告"],
    ["語言與資格", (item) => summarizePartnerCondition(item, 180)],
    ["費用", (item) => discoveryCostSummary(item)],
    ["我的備註", (item) => discoveryData().school_preferences[item.school_name]?.note || "—"],
    ["名額", (item) => item.quota || "依公告"],
    ["研修期間", (item) => item.study_period || "依公告"],
    [activeUniversityProfile().id === "tku" ? "外校申請期限（獲母校推薦後）" : "合作校參考時程", (item) => partnerDeadlineReference(item).value],
    ["適用身分", (item) => [item.colleges, item.degree_levels].filter(Boolean).join("／") || "依公告"],
  ];
  return `
    <div class="compare-heading"><div><span class="section-kicker">最多先比較 3 所</span><h3>候選學校差異</h3></div><span>${items.length} 所比較中</span></div>
    <div class="compare-scroll"><table class="compare-table"><thead><tr><th>比較項目</th>${items.map((item) => `<th>${escapeHtml(item.school_name)}</th>`).join("")}</tr></thead><tbody>${rows
      .map(([label, getter]) => `<tr><th>${escapeHtml(label)}</th>${items.map((item) => `<td>${highlightHtml(getter(item))}</td>`).join("")}</tr>`)
      .join("")}</tbody></table></div>`;
}

function ncuSourceReadingScope(source) {
  const scopes = [source.source_read_scope_note_zh, source.reading_review?.scope]
    .filter(value => typeof value === "string" && value && value !== source.privacy_note);
  return [...new Set(scopes)].join("；");
}

function openUniversityDetail(item, { updateHistory = true } = {}) {
  if (!canAccessPartnerCatalog()) { window.location.hash = "#partners"; return; }
  if (!item) return;
  if (!$("#dashboard-view").hidden) {
    state.dashboardScrollY = window.scrollY;
    state.dashboardHash = window.location.hash.startsWith("#school=")
      ? "#partners"
      : window.location.hash || "#overview";
  }
  if (updateHistory) window.UniWayNavigation.pushState({ school: item.school_name }, "", `#school=${encodeURIComponent(item.school_name)}`);
  state.activeSchool = item.school_name;
  rememberDiscovery("school", item);
  discoveryTheme = "all";
  state.experienceRequestId += 1;
  state.workflowRequestId += 1;
  state.destinationRequestId += 1;
  state.communityRequestId += 1;
  $("#dashboard-view").hidden = true;
  partnerMapController?.setVisible(false);
  const detailView = $("#school-detail-view");
  detailView.hidden = false;
  setSchoolHeroProgress(detailView, 0);
  document.body.classList.add("school-detail-open");
  setActiveNavigation("partners");
  document.title = `${item.school_name} | UniWay`;
  $("#school-detail-country").textContent = [item.country, item.program_type].filter(Boolean).join(" · ");
  const stamp = $("#school-destination-stamp");
  const destination = [item.country, item.location?.city].filter(Boolean);
  stamp.hidden = !destination.length;
  stamp.innerHTML = destination.length ? `<span class="travel-stamp-caption">下一站</span><strong>${escapeHtml(item.country || item.location.city)}</strong>${item.country && item.location?.city ? `<span class="travel-stamp-city">${escapeHtml(item.location.city)}</span>` : ""}` : "";
  $("#school-detail-title").textContent = item.school_name;
  $("#school-detail-photo").innerHTML = `${renderSchoolPhoto(item, "detail")}<div class="school-detail-photo-source">${renderPartnerLinks(item)}</div>`;
  $("#school-detail-summary").innerHTML = highlightHtml(summarizePartnerCondition(item, 110, 1));
  $("#school-detail-primary-facts").innerHTML = renderPrimaryFacts(item);
  $("#school-detail-content").innerHTML = renderUniversityOverview(item);
  activateDetailTab("detail-overview");
  updateDetailFavoriteButton();
  updateDetailApplicationButton();
  window.UniWayDetail?.render(item);
  updateUniWayPublicNavigation(window.location.hash);
  if (!window.UniWayNavigation.isRestoring) window.scrollTo({ top: 0, behavior: "instant" });
  initIcons();
  window.requestAnimationFrame(updateSchoolHeroMotion);

  const cachedWorkflow = state.workflowCache.get(workflowContextKey(item.school_name));
  if (cachedWorkflow) renderApplicationWorkflow(cachedWorkflow);
  else loadApplicationWorkflow(item);

  const cachedExperience = state.experienceCache.get(item.school_name);
  if (cachedExperience) renderExperienceDigest(cachedExperience);
  else loadStudentExperiences(item);

  const cachedDestination = state.destinationCache.get(item.school_name);
  if (cachedDestination) renderDestinationProfile(item, cachedDestination);
  else loadDestinationProfile(item);

  window.UniWayDestinationTips?.load(item);

  const cachedCompleteness = state.completenessCache.get(item.school_name);
  if (cachedCompleteness) renderSchoolCompleteness(cachedCompleteness);
  else loadSchoolCompleteness(item);
  document.querySelector("#ncu-source-audit")?.addEventListener("toggle", async (event) => {
    if (!event.currentTarget.open || event.currentTarget.dataset.loaded) return;
    const element = event.currentTarget;
    const body = element.querySelector("#ncu-source-audit-body");
    try {
      const report = await fetchJson(`/partner-source-audit?school=${encodeURIComponent(item.school_name)}&home_school=${encodeURIComponent(activeHomeSchool())}`);
      if (state.activeSchool !== item.school_name) return;
      body.innerHTML = `<p>查核日：${escapeHtml(report.checked_at)}。已取得來源與缺口列於下方；下載成功不代表文字可讀或全文已查。各來源年度、校區與track適用性仍須核對。</p>
        <ul>${Object.values(report.fields).map(row=>`<li><strong>${escapeHtml(row.label)}</strong>：${escapeHtml(row.note)}${row.unresolved ? `<small>${escapeHtml(row.unresolved)}</small>`:""}${row.key.startsWith("home_") || row.key === "quota" ? (row.original_evidence || []).map(p=>`<details><summary>${escapeHtml(p.source_title)} · 原文第${escapeHtml(p.page)}頁</summary><p>${escapeHtml(p.applicability)} · 查核${escapeHtml(p.checked_at)} · <a href="${escapeHtml(safeSourceUrl(p.source_url))}" target="_blank" rel="noopener noreferrer">官方來源</a></p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${escapeHtml(p.text)}</pre></details>`).join("") : ""}</li>`).join("")}</ul>
        ${report.source_evidence.map(src=>`<details><summary>${escapeHtml(src.label)} · ${src.source_excerpt_only ? "必要欄位摘錄" : `${src.pages.length}個來源頁／段`}；${src.content_status?.text_page_count ?? 0}頁有文字；${src.content_status?.visual_reviewed_page_count ?? 0}頁已視覺查核${src.content_status?.visual_reviewed_image_count ? `；${src.content_status.visual_reviewed_image_count}張原文圖片已視覺查核` : ""}</summary><p>${escapeHtml(report.read_sources.find(row=>row.id === src.id)?.applicability || "適用性待核對")}</p><p><a href="${escapeHtml(safeSourceUrl(src.url))}" target="_blank" rel="noopener noreferrer">官方公開來源</a> · 查核${escapeHtml(src.checked_at)}${src.excerpt_note_zh ? `<small>${escapeHtml(src.excerpt_note_zh)}</small>` : ""}${src.conversion_review?.note_zh ? `<small>${escapeHtml(src.conversion_review.note_zh)}</small>` : ""}${src.visual_review?.instructions_zh ? `<small>${escapeHtml(src.visual_review.instructions_zh)}</small>` : ""}${(src.text_quality_issues || []).length ? `<small>${escapeHtml(src.text_quality_issues.map(x=>`${x.reason}（頁${x.pages.join("、")}）`).join("；"))}</small>` : ""}${(src.non_text_pages || []).length ? `<small>${src.non_text_pages.every(page => page == null) ? "無固定PDF頁碼的來源含空白段／工作表" : `第${escapeHtml(src.non_text_pages.join("、"))}頁無可抽取文字`}；${src.content_status?.all_pages_read ? "已有原件SHA相符的閱讀紀錄；文字／視覺查核範圍分列，原始空頁仍保留。" : "須看官方原頁，未視為全文核對完成。"}</small>` : ""}</p>${src.privacy_note ? `<p class="ncu-source-scope">${escapeHtml(src.privacy_note)}</p>` : ""}${ncuSourceReadingScope(src) && ncuSourceReadingScope(src) !== src.privacy_note ? `<p class="ncu-source-reading-scope">閱讀範圍：${escapeHtml(ncuSourceReadingScope(src))}</p>` : ""}${src.pages.map(p=>`<details><summary>${p.archive_member ? `原文表格 ${escapeHtml(p.archive_member)}（ZIP內檔案，無PDF頁碼）` : p.image ? `原文圖片 ${escapeHtml(p.image)}（無PDF頁碼）` : p.slide ? `原文投影片 ${escapeHtml(p.slide)}（無PDF頁碼）` : p.sheet ? `原文工作表 ${escapeHtml(p.sheet)}（無PDF頁碼）` : p.page == null ? (src.source_excerpt_only ? "必要欄位摘錄（無固定PDF頁碼）" : "原文（無固定PDF頁碼）") : `原文第${escapeHtml(p.page)}頁`}</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${escapeHtml(p.text || (p.sheet ? "此工作表沒有非空儲存格；原始空白工作表另保留，閱讀狀態依同SHA逐工作表紀錄。" : "此頁無可抽取文字；請看原件及另外標示的視覺核對摘錄。"))}</pre></details>`).join("")}${(src.page_transcriptions || []).map(p=>`<details class="ncu-visual-passage"><summary>視覺核對摘錄（原PDF第${escapeHtml(p.page)}頁）</summary><p>人工核對的選定原文段落；原始抽取另外保留，並非全文轉錄或本期適用性核准。</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${escapeHtml(p.text)}</pre></details>`).join("")}</details>`).join("")}
        ${(report.collection_attempts || []).filter(src => src.exclusion_reason).length ? `<section><p>已排除的候選來源：校名、國家或incoming方案不符，保留查核證據，不當外校申請規則。</p><ul>${report.collection_attempts.filter(src => src.exclusion_reason).map(src => `<li>${escapeHtml(src.exclusion_reason)} · <a href="${escapeHtml(safeSourceUrl(src.url))}" target="_blank" rel="noopener noreferrer">候選來源</a></li>`).join("")}</ul></section>` : ""}
        ${report.unretrieved_sources.length ? `<section><p>未取得來源：以下是本次讀取失敗的網址，不推定登入限定、官方未公告或停止交換。</p><ul>${report.unretrieved_sources.map(src=>`<li class="ncu-unretrieved-source" data-source-id="${escapeHtml(src.id)}"><strong>${escapeHtml(src.id)}</strong>：${escapeHtml(src.reason)}${src.url ? ` · <a href="${escapeHtml(safeSourceUrl(src.url))}" target="_blank" rel="noopener noreferrer">已查網址（本次未取得）</a>` : ""}</li>`).join("")}</ul></section>`:""}`;
      element.dataset.loaded = "true";
    } catch (error) { body.textContent = `查核記錄讀取失敗：${error.message}`; }
  });


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
    window.UniWayNavigation.pushState({}, "", state.dashboardHash || "#partners");
    applyAppRoute({ loadFeed: false, resetScroll: false });
  }
  window.setTimeout(() => {
    if (window.UniWayNavigation.isRestoring || window.location.hash !== state.dashboardHash) return;
    window.scrollTo({ top: state.dashboardScrollY || 0, behavior: "instant" });
    const returnPage = (state.dashboardHash || "#partners").slice(1);
    setActiveNavigation(UNIVERSITY_PAGE_ROUTES.has(returnPage) && returnPage !== "search" ? returnPage : "partners");
  }, 0);
}

let schoolHeroScrollFrame = 0;

function setSchoolHeroProgress(detailView, progress) {
  if (!detailView) return;
  const safeProgress = window.UniWayMotion?.reduced ? 0 : Math.min(1, Math.max(0, progress));
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
  const saved = activeSchoolSelections().has(state.activeSchool);
  button.dataset.schoolName = state.activeSchool;
  button.setAttribute("aria-pressed", String(saved));
  button.classList.toggle("saved", saved);
  const label = state.account
    ? (saved ? "已收藏" : "收藏")
    : (saved ? "已加入比較" : "加入比較");
  const icon = "heart";
  button.setAttribute(
    "aria-label",
    state.account
      ? `${saved ? "取消收藏" : "收藏"}${state.activeSchool}`
      : `${saved ? "移出比較" : "加入比較"}${state.activeSchool}`
  );
  button.innerHTML = `<i data-lucide="${icon}" aria-hidden="true"></i><span>${label}</span>`;
  initIcons();
}

function updateDetailApplicationButton() {
  const button = $("#detail-application-button");
  if (!button || !state.activeSchool) return;
  const added = Boolean(state.account && state.applications.has(state.activeSchool));
  const item = partnerByName(state.activeSchool);
  const availability = partnerAvailabilityMeta(item);
  const blocked = availability.blocked && !added;
  button.dataset.schoolName = state.activeSchool;
  button.setAttribute("aria-pressed", String(added));
  button.classList.toggle("added", added);
  button.disabled = blocked;
  button.title = blocked ? (item?.availability_note || "當期是否開放仍待確認") : "";
  const label = added
    ? "移出我的志願"
    : blocked
      ? availability.matchLabel
      : state.account ? "加入我的志願" : "登入建立計畫";
  const icon = added ? "bookmark-check" : blocked ? "badge-alert" : state.account ? "bookmark" : "log-in";
  button.innerHTML = `<i data-lucide="${icon}" aria-hidden="true"></i><span>${escapeHtml(label)}</span>`;
  initIcons();
  window.UniWayDetail?.render();
}

function toggleApplication(schoolName) {
  if (!schoolName) return;
  if (!state.account) {
    announce("建立個人申請計畫需要先登入；公開搜尋與比較仍可直接使用。", "info", true);
    openAuthDialog("register");
    return;
  }
  if (state.applications.has(schoolName)) state.applications.delete(schoolName);
  else {
    const item = partnerByName(schoolName);
    const availability = partnerAvailabilityMeta(item);
    if (availability.blocked) {
      announce(
        item?.availability_note || "當期是否開放仍待確認，不能加入正式申請計畫。",
        "error"
      );
      updateDetailApplicationButton();
      return;
    }
    state.applications.add(schoolName);
    state.favorites.add(schoolName);
  }
  try {
    window.localStorage.setItem(STORAGE_KEYS.applications, JSON.stringify([...state.applications]));
    window.localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify([...state.favorites]));
  } catch (_) {
    // The application list still works for this session.
  }
  scheduleAccountWorkspaceSync();
  updateDetailApplicationButton();
  renderFavorites();
  updateFavoriteCounts();
  renderDecisionBrief();
  renderDocumentReadiness();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  renderBudgetPlanner();
  renderApplicationCalendar();
  scheduleCalendarConflictAnalysis();
}

function renderPrimaryFacts(item, destinationProfile = state.destinationCache.get(item.school_name)) {
  const eligibility = partnerEligibilityStatus(item);
  const deadline = partnerDeadlineReference(item);
  return [
    ["我的資格", eligibility.label, eligibility.icon, eligibility.tone],
    [deadline.label, deadline.value, "calendar-clock", "deadline"],
    ["語言門檻", partnerLanguageRequirement(item), "languages", "language"],
    ["生活費參考", truncate(destinationProfile?.cost_summary || "官方費用待查核", 130), "wallet-cards", "cost"],
    ["交換名額", item.quota || (item.quota_status === "reference_only" ? (activeHomeSchool() === "淡江大學" ? "本期名額未核實" : "本季未開放") : item.quota_status === "not_published" ? "名額空白，待確認" : "依公告"), "users", "quota"],
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
  if (item.language_requirement) return truncate(item.language_requirement, 110);
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
      <div class="program-options-heading"><strong>這間學校列有 ${options.length} 種計畫資料</strong><span>請依學院、學制、適用學期與名額核對</span></div>
      <div class="program-option-list">
        ${options.map((option) => {
          const deadline = partnerDeadlineReference(option);
          return `
          <article class="program-option">
            <div><span class="program-option-type">${escapeHtml(option.program_type)}</span><h3>${escapeHtml([option.colleges, option.degree_levels].filter(Boolean).join(" · ") || "適用身分依公告")}</h3></div>
            <dl>
              <div><dt>名額</dt><dd>${escapeHtml(option.quota || (item.field_evidence ? "全校共用名額；本方案未另列" : "依公告"))}</dd></div>
              <div><dt>研修期間</dt><dd>${escapeHtml(localizedPartnerValue(option, "study_period", "study_period"))}</dd></div>
              <div><dt>${escapeHtml(deadline.label)}</dt><dd>${highlightHtml(deadline.value)}</dd></div>
            </dl>
            ${partnerSummaryPoints(option, "eligibility_points").length ? `<details><summary><span>查看此方案中文重點</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>${renderStudentPointList(partnerSummaryPoints(option, "eligibility_points"), { limit: 8 })}</details>` : ""}
            <a href="${escapeHtml(option.source_url)}" target="_blank" rel="noreferrer">查看${escapeHtml(activeUniversityProfile().short_name)}官方方案來源<i data-lucide="external-link" aria-hidden="true"></i></a>
          </article>`;
        }).join("")}
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
        <div><h3 id="partner-student-summary-title">合作校條件</h3></div>
        ${summary.translated_from_english ? '<span class="translation-status"><i data-lucide="languages" aria-hidden="true"></i>中文摘要</span>' : ""}
      </div>
      <div class="partner-summary-groups">
        ${groups.map((group) => `
          <section class="partner-summary-group">
            <h4><i data-lucide="${group.icon}" aria-hidden="true"></i>${escapeHtml(group.label)}</h4>
            ${renderStudentPointList(group.points, { limit: 10, expandRemaining: activeHomeSchool() === "國立中央大學" })}
          </section>`).join("")}
      </div>

    </section>`;
}

function renderPartnerFieldEvidence(item) {
  if (activeHomeSchool() === "淡江大學") return window.UniWayTkuDetails?.render(item, escapeHtml) || "";
  if (!item.field_evidence || !Object.keys(item.field_evidence).length) return "";
  const labels = {study_period:"交換期間", quota:"名額", eligibility:"合作校接收資格", language_requirement:"合作校語言", partner_application_prerequisite:"母校甄選／提名前提（非文件清單）", partner_documents:"合作校申請文件要求（未聲稱完整）", partner_application_deadline:"合作校申請截止", application_deadline:"中正校內截止", semester_dates:"學期日期", housing_info:"住宿資訊", tuition_info:"費用原文", course_restrictions:"課程限制", fact_sheet:"合作校簡章連結"};
  const statuses = {verified_current:"當期已核實",reference_only:"歷史參考",missing:"未載／未核實",needs_confirmation:"待確認",conflict:"來源矛盾，待確認",explicit_not_announced:"官方明示尚未公告"};
  return `<details class="overview-more"><summary>當期資料與官方依據（${escapeHtml(item.application_round || "")}）</summary>
    <p>合作校接收條件須與中正校內資格分別核對；灰字歷史資料不作當期申請依據。</p>
    ${Object.entries(labels).map(([key,label]) => {
      const evidence = item.field_evidence[key];
      if (!evidence) return "";
      const pages = evidence.source_pages?.length ? `，第${evidence.source_pages.join("、")}頁` : "";
      return `<article class="university-fact"><strong>${escapeHtml(label)} · ${escapeHtml(statuses[evidence.status] || evidence.status)}</strong>
        <p>${escapeHtml(evidence.excerpt || "當期值未核實")}</p>
        ${evidence.reference_excerpt ? `<details><summary>歷史參考（不能作當期申請依據）</summary><p>${escapeHtml(evidence.reference_excerpt)}</p></details>` : ""}
        ${evidence.note ? `<p>${escapeHtml(evidence.note)}</p>` : ""}
        <a href="${escapeHtml(evidence.source_url)}" target="_blank" rel="noreferrer">官方來源${escapeHtml(pages)}</a>
        <small> · 查核 ${escapeHtml((evidence.checked_at || "").slice(0,10))} · ${escapeHtml(evidence.application_round || "參考年度未明")}</small>
      </article>`;
    }).join("")}</details>`;
}

function renderUniversityOverview(item) {
  const tuitionPoints = partnerSummaryPoints(item, "tuition_points");
  const deadline = partnerDeadlineReference(item);
  const facts = [
    ["計畫類型", item.program_type || "依校方公告"],
    ["適用學院／學制", [item.colleges, item.degree_levels].filter(Boolean).join("／") || "依校方公告"],
    ["名額", item.quota || (item.quota_status === "reference_only" ? (activeHomeSchool() === "淡江大學" ? "本期名額未核實" : "本季未開放") : item.quota_status === "not_published" ? "名額空白，待確認" : "依校方公告")],
    ["研修期間", localizedPartnerValue(item, "study_period", "study_period", "依校方公告")],
    [deadline.label, deadline.value],
    ["學費", tuitionPoints.slice(0, 2).join("；") || "依校方公告"],
    ["排名資訊", item.ranking_info || "未提供"],
  ];
  return `
    <div class="detail-main-column">
      <section id="detail-overview" class="detail-section university-overview" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-overview">
        <div class="overview-intro-grid">
          <div class="detail-section-heading"><h2 id="detail-overview-title">申請重點</h2></div>
          <div class="rule-scope-grid">
            <article class="rule-scope home-rule"><div class="rule-step-heading"><span class="rule-step-number" aria-label="第一階段">01</span><span><i data-lucide="building-2" aria-hidden="true"></i>${escapeHtml(activeHomeSchool())}規定</span></div><h3>校內甄選</h3><p>通過${escapeHtml(activeUniversityProfile().short_name)}甄選後，由校方提名。</p></article>
            <article class="rule-scope partner-rule"><div class="rule-step-heading"><span class="rule-step-number" aria-label="第二階段">02</span><span><i data-lucide="globe-2" aria-hidden="true"></i>合作校規定</span></div><h3>提名後申請</h3><p>依合作校要求送件，等待審查結果。</p></article>
          </div>
        </div>
        ${renderPartnerAvailabilityNotice(item)}
        ${renderPartnerFieldEvidence(item)}
        ${activeHomeSchool() === "淡江大學" ? "" : window.UniWayCcuDetails?.render(item, escapeHtml) || ""}
        <details class="overview-more school-data-completeness"><summary>這所學校的資料完整度</summary><div id="school-data-completeness-body" aria-live="polite" aria-busy="true"><div class="skeleton skeleton-card"></div></div></details>
        ${activeHomeSchool() === "國立中央大學" ? '<details id="ncu-source-audit" class="overview-more"><summary>已查來源、適用年度與未解問題</summary><div id="ncu-source-audit-body">展開讀取逐欄查核與原文頁碼。</div></details>' : ""}
        <details class="overview-more"><summary>選校參考</summary><div id="quick-decision-fit">${renderQuickDecisionFit(item)}</div></details>
        ${renderProgramOptions(item)}
        <details class="overview-more"><summary>方案資料</summary><div class="university-facts">${facts.map(([label, value]) => `<div class="university-fact"><span>${escapeHtml(label)}</span><strong>${highlightHtml(value)}</strong></div>`).join("")}</div></details>
        ${renderPartnerStudentSummary(item)}
        <div class="partner-links detail-source-links">${renderPartnerLinks(item)}</div>
      </section>

      <section id="detail-application" class="detail-section workflow-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-application" hidden>
        <div class="detail-section-heading"><h2 id="application-workflow-title">詳細申請流程</h2></div>
        <div id="workflow-content" aria-live="polite" aria-busy="true">${renderWorkflowLoading()}</div>
      </section>

      <section id="detail-life" class="detail-section life-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-life" hidden>
        <div class="detail-section-heading"><h2 id="student-life-title">生活情報</h2></div>
        <div id="life-research-status" class="life-research-status" aria-live="polite"></div>
        <details class="life-official-guide"><summary>官方生活指南</summary><div id="destination-official-content" class="destination-official" aria-live="polite" aria-busy="true"><div class="skeleton skeleton-card"></div></div></details>
        <div id="life-content" class="life-grid" aria-live="polite" aria-busy="true">${renderLifeLoading()}</div>
      </section>

      <section id="detail-prep" class="detail-section prep-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-prep" hidden>
        <div class="detail-section-heading"><h2 id="destination-prep-title">出發前提醒</h2></div>
        <div id="prep-content" aria-live="polite" aria-busy="true"><div class="skeleton skeleton-card"></div></div>
      </section>

      <section id="detail-experiences" class="detail-section experience-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-experiences" hidden>
        <div class="detail-section-heading"><h2 id="student-experience-title">學生心得</h2></div>
        <div id="experience-content" aria-live="polite" aria-busy="true">${renderExperienceLoading()}</div>
      </section>

      <section id="detail-community" class="detail-section community-section" role="tabpanel" tabindex="0" aria-labelledby="detail-tab-community" hidden>
        <div class="detail-section-heading"><h2 id="community-title">${escapeHtml(item.school_name)} 學生社群</h2></div>
        <div id="community-content" class="community-content" aria-live="polite" aria-busy="true">${renderCommunityLoading()}</div>
        ${renderCommunityContributionForms(item)}
      </section>
    </div>

    <aside class="detail-side-column" aria-label="申請準備進度與官方來源">
      <section class="application-tracker"><div class="tracker-heading"><span class="tracker-heading-icon" aria-hidden="true"><i data-lucide="clipboard-check"></i></span><div><h2>我的申請進度</h2></div></div><div id="application-tracker">${renderApplicationTracker(item)}</div></section>
      <section class="decision-reminder"><i data-lucide="badge-check" aria-hidden="true"></i><div><strong>送件前確認</strong><p>截止日與資格以當期官方公告為準。</p></div></section>
    </aside>`;
}

function renderLifeLoading() {
  return LIFE_SECTIONS.map(() => '<div class="skeleton skeleton-life"></div>').join("");
}

function renderQuickDecisionFit(item, digest = state.experienceCache.get(item.school_name)) {
  const eligibility = partnerEligibilityStatus(item);
  const identity = [item.colleges, item.degree_levels].filter(Boolean).join("／") || "身分依合作校公告";
  const period = localizedPartnerValue(item, "study_period", "study_period");
  const deadline = partnerDeadlineReference(item);
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
    : [digest ? "學生來源不足，暫無共同評價。" : "正在比對學生來源中的共同優點"];

  const challenge = (digest?.common_challenges || [])[0];
  const warningPoints = [];
  if (eligibility.tone === "needs-review") warningPoints.push(`資格初判：${truncate(eligibility.label, 68)}`);
  if (challenge) warningPoints.push(`學生提醒（${challenge.source_count} 個來源）：${truncate(challenge.summary, 68)}`);
  warningPoints.push(`${deadline.label}：${truncate(deadline.value, 62)}`);
  warningPoints.push(`語言條件：${truncate(partnerLanguageRequirement(item), 68)}`);

  const groups = [
    { label: "適合條件", icon: "badge-check", tone: "fit", source: "合作校公開條件", points: fitPoints.slice(0, 4) },
    { label: "學生評價", icon: "thumbs-up", tone: "positive", source: digest ? `${digest.total_sources} 個公開學生來源` : "學生來源整理中", points: positivePoints },
    { label: "申請前先確認", icon: "triangle-alert", tone: "caution", source: "", points: warningPoints.slice(0, 4) },
  ];
  return `
    <section class="quick-decision-fit" aria-labelledby="quick-decision-fit-title">
      <div class="quick-decision-heading"><div><h3 id="quick-decision-fit-title">這間學校適合我嗎？</h3></div><span>摘要不取代正式資格審查</span></div>
      <div class="quick-decision-grid">
        ${groups.map((group) => `
          <article class="quick-decision-card ${group.tone}">
            <div><i data-lucide="${group.icon}" aria-hidden="true"></i><h4>${escapeHtml(group.label)}</h4></div>
            ${group.source ? `<small>${escapeHtml(group.source)}</small>` : ""}
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

const COMPLETENESS_STATUS = {
  available: ["已有", "check"], partial: ["部分", "circle-dashed"],
  needs_confirmation: ["待確認", "circle-alert"], missing: ["缺", "circle-minus"],
};

function renderSchoolCompleteness(report) {
  const body = $("#school-data-completeness-body");
  if (!body) return;
  body.setAttribute("aria-busy", "false");
  body.innerHTML = `
    <p class="school-completeness-summary"><strong>${report.available_count} / ${report.total_count} ${report.home_university === "淡江大學" ? "欄已有當期依據；請逐欄看適用範圍" : report.home_university === "國立中央大學" ? "項本期已核實" : "項已提供資料"}</strong>${report.priority_gaps.length ? `<span>，優先向學校確認：${report.priority_gaps.map(escapeHtml).join("、")}</span>` : ""}</p>
    <ul class="school-completeness-list">${report.items.map((row) => {
      const [statusLabel, icon] = COMPLETENESS_STATUS[row.status] || ["待確認", "circle-alert"];
      const label = report.home_university === "國立中央大學" && row.status === "available" ? "本期已核實" : statusLabel;
      const link = (row.source_urls || [])[0];
      return `<li data-completeness-status="${escapeHtml(row.status)}"><i data-lucide="${icon}" aria-hidden="true"></i><span><strong>${escapeHtml(row.label)}</strong><em>${label}</em><small>${escapeHtml(row.note)}${link ? ` <a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">來源</a>` : ""}</small></span></li>`;
    }).join("")}</ul>
    <small class="school-completeness-disclaimer">${escapeHtml(report.disclaimer)}</small>`;
  initIcons();
}

async function loadSchoolCompleteness(item) {
  const requestId = ++state.completenessRequestId;
  const context = captureSchoolContext();
  try {
    const report = await fetchJson(`/school-data-completeness?school=${encodeURIComponent(item.school_name)}&home_school=${encodeURIComponent(activeHomeSchool())}`);
    if (requestId !== state.completenessRequestId || !schoolContextIsCurrent(context) || state.activeSchool !== item.school_name) return;
    state.completenessCache.set(item.school_name, report);
    renderSchoolCompleteness(report);
  } catch (error) {
    if (requestId !== state.completenessRequestId || !schoolContextIsCurrent(context) || state.activeSchool !== item.school_name) return;
    const body = $("#school-data-completeness-body");
    if (body) { body.setAttribute("aria-busy", "false"); body.textContent = `資料完整度暫時無法載入：${error.message}`; }
  }
}

async function loadDestinationProfile(item) {
  const requestId = ++state.destinationRequestId;
  const context = captureSchoolContext();
  try {
    const profile = await fetchJson(`/destination-profile?school=${encodeURIComponent(item.school_name)}&home_school=${encodeURIComponent(activeHomeSchool())}`);
    if (requestId !== state.destinationRequestId || !schoolContextIsCurrent(context) || state.activeSchool !== item.school_name) return;
    state.destinationCache.set(item.school_name, profile);
    renderDestinationProfile(item, profile);
  } catch (error) {
    if (requestId !== state.destinationRequestId || !schoolContextIsCurrent(context) || state.activeSchool !== item.school_name) return;
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
  const cityStamp = $("#school-detail-view .travel-stamp-city");
  if (cityStamp && profile.city) cityStamp.textContent = profile.city;
  $("#school-detail-primary-facts").innerHTML = renderPrimaryFacts(item, profile);
  window.UniWayDetail?.gallery(item, profile);
  if (profile.home_university !== "淡江大學" && item.partner_exchange_details && Object.keys(item.partner_exchange_details).length && window.UniWayCcuDetails) {
    const status = profile.coverage_status === "official_partial" ? "合作校生活資料部分核實" : "合作校生活資料仍待確認";
    container.innerHTML = `<div class="destination-profile-status partial"><div><strong>${escapeHtml(status)}</strong><p>${escapeHtml(profile.coverage_note || "")}</p><small>最後查核：${escapeHtml(formatDate(profile.last_checked))}</small></div></div>`
      + window.UniWayCcuDetails.render(item, escapeHtml, ["housing", "housing_deadline", "costs", "insurance", "visa", "arrival", "course_restrictions", "academic_calendar"]);
    container.innerHTML += window.UniWayCcuDetails.renderProfileLife(profile, escapeHtml);
    initIcons();
    return;
  }
  if (!["official_verified", "official_partial"].includes(profile.coverage_status)) {
    container.innerHTML = `
      <div class="destination-profile-status pending">
        <i data-lucide="clock-3" aria-hidden="true"></i>
        <div><strong>官方指南待補</strong><p>可先查看下方生活資料。</p></div>
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
  const originalProfile = profile.original_display_facts || profile;
  const originalFacts = [
    ["所在地", originalProfile.city], ["費用參考", originalProfile.cost_summary],
    ["住宿", originalProfile.housing_summary], ["交通", originalProfile.transport_summary],
    ["校園生活", originalProfile.campus_life_summary],
  ].filter(([, value]) => value);
  const isPartial = profile.coverage_status === "official_partial";
  const statusClass = isPartial ? "partial" : "verified";
  const statusIcon = isPartial ? "badge-alert" : "badge-check";
  const statusLabel = isPartial ? "官方生活資訊部分查核" : "官方生活資訊已查核";
  container.innerHTML = `
    <div class="destination-profile-status ${statusClass}">
      <i data-lucide="${statusIcon}" aria-hidden="true"></i>
      <div><strong>${statusLabel}</strong><p>${escapeHtml(profile.coverage_note)}</p><small>最後查核：${escapeHtml(formatDate(profile.last_checked))}</small></div>
    </div>
    <div class="destination-facts">
      ${facts.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${highlightHtml(value)}</strong></div>`).join("")}
    </div>
    ${renderStudentSurvivalGuide(item, profile)}
    <details class="destination-source-library">
      <summary><span>查看本頁全部查核來源（${(profile.sources || []).length}）</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>
      <section class="destination-original-summary" aria-label="核對摘要原文">
        <h4>核對摘要原文</h4>
        <dl>${originalFacts.map(([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`).join("")}</dl>
      </section>
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
  const scopedPhotoAlreadyIncluded = activeHomeSchool() === "國立中央大學"
    && dormPhotos.some((photo) => photo.category === "campus" && item.image_url?.endsWith(photo.image_url));
  const campusPhoto = item.image_url && !scopedPhotoAlreadyIncluded ? [{
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
        <div><h3 id="student-survival-title">交換生生存指南</h3></div>

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
                <figcaption>${escapeHtml(photo.caption)}${photo.category === "campus" ? renderSchoolImageCredit(item, activeHomeSchool() !== "國立中央大學") : ""}</figcaption>
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
          <div class="student-guide-subheading"><div><i data-lucide="route" aria-hidden="true"></i><h4 id="student-guide-arrival-title">${profile.home_university === "淡江大學" ? "抵達後辦理事項" : "抵達後 72 小時"}</h4></div><small>${profile.home_university === "淡江大學" ? "各項依官方時限及外校通知辦理" : "照順序完成，先讓自己能通訊、付款、進校與選課"}</small></div>
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

function lifeContextKey() {
  return `${activeHomeSchool()}::${state.activeSchool || ""}`;
}

function renderLifeResearchStatus(context, { loading = false, error = "" } = {}) {
  const container = $("#life-research-status");
  if (!container) return;
  const status = { ready: "已更新", partial: "部分資料已更新", unavailable: "暫無新資料", not_collected: "待更新" };
  container.innerHTML = `<div class="life-research-heading"><span role="status">${escapeHtml(error || (loading ? "正在更新資料…" : status[context?.research_status] || ""))}${context?.checked_at && !loading ? ` · ${escapeHtml(formatDate(context.checked_at))}` : ""}</span><div class="life-research-actions"><button type="button" class="life-student-search" data-life-student-search>找學生分享</button><button type="button" class="secondary-button" data-refresh-life-context ${loading || context?.can_refresh === false ? "disabled" : ""}><i data-lucide="${loading ? "loader-circle" : "refresh-cw"}" aria-hidden="true"></i>${loading ? "更新中" : "更新資料"}</button></div></div>
    <details class="life-research-notes"><summary>資料說明</summary><p>官方資料保留來源與原文；尚未翻譯的內容會標示「原文」。AI 推論為規則產生的參考建議，非學生心得；機器翻譯未經人工審核。查閱日期不代表官網內容更新日。</p><p>${escapeHtml(context?.location_note || "正在讀取校區資料。")}</p>${(context?.research_notes || []).map(note => `<p>${escapeHtml(note)}</p>`).join("")}<small>補查結果暫存 6 小時；可按「更新資料」重新查詢。</small></details>`;
  initIcons();
}

async function loadSchoolLifeContext(item, { refresh = false } = {}) {
  if (!item) return;
  const requestContext = captureSchoolContext();
  const key = lifeContextKey();
  const loadingKey = `${requestContext.version}::${key}`;
  if (state.lifeContextLoading.has(loadingKey)) return;
  const cached = state.lifeContextCache.get(key);
  if (cached && !refresh) {
    renderLifeResearchStatus(cached);
    renderStudentLife(state.experienceCache.get(item.school_name) || { highlights: [] });
    return;
  }
  state.lifeContextLoading.add(loadingKey);
  renderLifeResearchStatus(cached, { loading: true });
  const query = `school=${encodeURIComponent(item.school_name)}&home_school=${encodeURIComponent(activeHomeSchool())}`;
  try {
    let context = cached || await fetchJson(`/school-life-context?${query}`);
    if (!schoolContextIsCurrent(requestContext) || lifeContextKey() !== key) return;
    state.lifeContextCache.set(key, context);
    if (lifeContextKey() === key) renderStudentLife(state.experienceCache.get(item.school_name) || { highlights: [] });
    if (refresh || context.research_status === "not_collected") {
      context = await fetchJson(`/school-life-context/refresh?${query}`, { method: "POST", signal: AbortSignal.timeout(60000) });
      if (!schoolContextIsCurrent(requestContext) || lifeContextKey() !== key) return;
      state.lifeContextCache.set(key, context);
    }
    if (!schoolContextIsCurrent(requestContext) || lifeContextKey() !== key) return;
    renderLifeResearchStatus(context);
    renderStudentLife(state.experienceCache.get(item.school_name) || { highlights: [] });
  } catch (error) {
    if (!schoolContextIsCurrent(requestContext) || lifeContextKey() !== key) return;
    renderLifeResearchStatus(state.lifeContextCache.get(key), { error: "補查暫時未完成，已保留可用資料；可稍後重試。" });
    renderStudentLife(state.experienceCache.get(item.school_name) || { highlights: [] });
  } finally {
    state.lifeContextLoading.delete(loadingKey);
  }
}

function renderLifeEvidenceSupplement(category, { limit = 2 } = {}) {
  if (!category) return "";
  const labels = { official: "官方", geographic: "周邊地點", mixed: "官方與學生" };
  const evidenceRows = (category.evidence || []).map(row => {
    const pending = row.translation_status === "pending";
    const original = row.original_text || row.text;
    return `<div class="life-evidence-item"><span class="life-kind ${escapeHtml(row.kind)}">${labels[row.kind] || "公開資料"}${row.translation_status === "machine" ? " · 機器翻譯" : pending ? " · 原文" : ""}</span><p class="life-evidence-text">${escapeHtml(pending ? "中文翻譯尚未完成，可查看原文。" : row.text)}</p>${row.original_excerpt ? `<small class="life-applicability-note">官網參考；適用校區與年度請核對來源。${row.checked_at ? ` 查閱 ${escapeHtml(formatDate(row.checked_at))}` : ""}</small>` : ""}<details class="life-evidence-source"><summary>原文與來源</summary>${pending || original !== row.text ? `<p>${escapeHtml(original)}</p>` : ""}<small>${escapeHtml(row.scope)}${row.checked_at ? ` · ${escapeHtml(formatDate(row.checked_at))}` : ""}</small><div class="life-source-links">${row.sources.map(source => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.title)} ↗</a>`).join("")}</div></details></div>`;
  });
  const evidence = evidenceRows.slice(0, limit).join("") + (evidenceRows.length > limit ? `<details class="life-more-evidence"><summary>再看 ${evidenceRows.length - limit} 則資料</summary>${evidenceRows.slice(limit).join("")}</details>` : "");
  const inference = category.inference;
  return `${evidence ? `<div class="life-evidence-list">${evidence}</div>` : ""}${inference ? `<div class="life-ai-inference"><span class="life-kind inference"><i data-lucide="sparkles" aria-hidden="true"></i>AI 推論</span><p>${escapeHtml(inference.text)}</p><details><summary>推論依據</summary><p>${escapeHtml(inference.limitation)}</p><div class="life-source-links">${inference.basis_urls.map((url, index) => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">推論依據 ${index + 1} ↗</a>`).join("")}</div></details></div>` : ""}
    <details class="life-next-step"><summary>繼續查詢</summary><p>${escapeHtml(category.next_step)}</p><a href="${escapeHtml(category.search_url)}" target="_blank" rel="noreferrer">搜尋相關資料 ↗</a></details>`;
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
  const missing = [];
  const cards = rankedSections.map(({ section, highlight }) => {
    const category = state.lifeContextCache.get(lifeContextKey())?.categories.find(item => item.theme === section.theme);
    const points = highlight ? buildLifeKeyPoints(highlight) : [];
    const hasConcretePoints = points.length > 0;
    if (!highlight && !category?.evidence.length) {
      missing.push({ section, category });
      return "";
    }
    return `
      <article class="life-card${highlight || category?.evidence.length ? " has-sources" : " needs-sources"}" data-life-theme="${section.theme}">
        <div class="life-card-heading"><i data-lucide="${section.icon}" aria-hidden="true"></i><h3>${escapeHtml(section.label)}</h3></div>
        ${
          highlight
            ? `<span class="life-kind student">學生心得 · ${highlight.source_count}</span>${hasConcretePoints
                ? `<ul class="life-key-points">${points.slice(0, 2).map((point) => `<li><strong>${highlightHtml(point)}</strong></li>`).join("")}</ul>`
                : `<p class="life-extraction-pending">原文內容不足，暫無摘要。</p>`}
               <details class="life-details"><summary><span>心得與來源</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary>${points.length > 2 ? `<ul>${points.slice(2).map(point => `<li>${highlightHtml(point)}</li>`).join("")}</ul>` : ""}${hasConcretePoints ? `<p>${highlightHtml(highlight.summary)}</p>` : ""}${renderLifeSourceLinks(highlight)}<small>學生經驗會因年份、科系與個人習慣不同。</small></details>`
            : ""
        }
        ${category ? renderLifeEvidenceSupplement(category, { limit: hasConcretePoints ? 1 : 2 }) : ""}
      </article>`;
  }).join("");
  container.innerHTML = cards + (missing.length ? `<details class="life-missing-topics"><summary>待補資料（${missing.length} 項）</summary><div>${missing.map(({ section, category }) => `<section><h4>${escapeHtml(section.label)}</h4>${category ? renderLifeEvidenceSupplement(category) : "<p>資料讀取中。</p>"}</section>`).join("")}</div></details>` : "");
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
  const sources = state.experienceCache.get(state.activeSchool)?.sources || [];
  const languages = { en: "英文", zh: "中文", ja: "日文", ko: "韓文", de: "德文", fr: "法文" };
  return `<div class="life-source-links" aria-label="此生活面向的學生來源">${links
    .map((url, index) => {
      const source = sources.find(item => item.source_url === url);
      const context = source ? [languages[source.language] || "原文", source.perspective === "official_student_story" ? "校方刊載的學生訪談" : source.platform, source.published_at ? `發表 ${source.published_at}` : "發表日期未標示"].filter(Boolean).join(" · ") : "";
      return `<div class="life-student-source"><a href="${escapeHtml(url)}" target="_blank" rel="noreferrer"><span>${escapeHtml(source?.title || `查看學生來源 ${index + 1}`)}</span><i data-lucide="external-link" aria-hidden="true"></i></a>${context ? `<small>${escapeHtml(context)}</small>` : ""}</div>`;
    })
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
  if (targetId === "detail-life") loadSchoolLifeContext(partnerByName(state.activeSchool));
  if (scroll) {
    $("#school-detail-content")?.scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "start" });
  }
}

function renderApplicationTracker(item) {
  const schoolProgress = state.applicationProgress[item.school_name] || {};
  const completed = APPLICATION_PROGRESS_STEPS.filter((step) => schoolProgress[step.id]).length;
  const percentage = Math.round((completed / APPLICATION_PROGRESS_STEPS.length) * 100);
  return `
    <div class="tracker-progress" role="progressbar" aria-label="申請準備進度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percentage}" aria-valuetext="${completed} / ${APPLICATION_PROGRESS_STEPS.length} 已完成"><div class="tracker-progress-ring" style="--tracker-progress:${percentage}%" aria-hidden="true"><strong>${percentage}<small>%</small></strong></div><div class="tracker-progress-copy"><strong>${completed} / ${APPLICATION_PROGRESS_STEPS.length} 已完成</strong><span>${completed === APPLICATION_PROGRESS_STEPS.length ? "已完成準備" : "準備中"}</span></div></div>
    ${state.account ? "" : '<p class="application-plan-login-note"><i data-lucide="log-in" aria-hidden="true"></i><span>登入以保存進度</span><button type="button" class="text-action" data-open-auth>登入</button></p>'}
    <div class="tracker-checklist">${APPLICATION_PROGRESS_STEPS.map((step) => `<label><input class="progress-checkbox" type="checkbox" data-progress-step="${step.id}" ${schoolProgress[step.id] ? "checked" : ""} ${state.account ? "" : "disabled"} /><span>${escapeHtml(step.label)}</span>${schoolProgress[step.id] ? '<span class="travel-task-stamp" aria-hidden="true">完成</span>' : ""}</label>`).join("")}</div>`;
}

function updateApplicationProgress(stepId, checked) {
  if (!state.activeSchool) return;
  if (!requireAccountForPrivateAction("記錄學校申請進度需要先登入；申請規定仍可直接查看。")) {
    const item = partnerByName(state.activeSchool);
    if (item) $("#application-tracker").innerHTML = renderApplicationTracker(item);
    return;
  }
  const current = { ...(state.applicationProgress[state.activeSchool] || {}) };
  current[stepId] = checked;
  state.applicationProgress[state.activeSchool] = current;
  try {
    window.localStorage.setItem(STORAGE_KEYS.progress, JSON.stringify(state.applicationProgress));
  } catch (_) {
    // Progress still works for this session.
  }
  scheduleAccountWorkspaceSync();
  const item = partnerByName(state.activeSchool);
  if (item) $("#application-tracker").innerHTML = renderApplicationTracker(item);
  const checkbox = document.querySelector(`[data-progress-step="${CSS.escape(stepId)}"]`);
  checkbox?.focus({ preventScroll: true });
  if (checked) checkbox?.closest("label").querySelector(".travel-task-stamp")?.classList.add("is-new");
}

function renderWorkflowLoading() {
  return `
    <div class="workflow-loading" role="status">
      <span>正在查核${escapeHtml(activeUniversityProfile().short_name)}與合作校官方申請流程…</span>
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
    </div>`;
}

function workflowContextKey(schoolName) {
  const profile = state.eligibilityProfile || {};
  return [
    activeHomeSchool(),
    schoolName,
    profile.college || state.applicationProfile?.college || "",
    profile.department || state.applicationProfile?.department || "",
    state.applicationContext.academic_year || "",
    state.applicationContext.application_round || "",
  ].join("|");
}

function workflowRequestParams(item) {
  const profile = state.eligibilityProfile || {};
  const params = new URLSearchParams({
    school: item.school_name,
    home_school: activeHomeSchool(),
  });
  const values = {
    college: profile.college || state.applicationProfile?.college || "",
    department: profile.department || state.applicationProfile?.department || "",
    academic_year: state.applicationContext.academic_year || "",
    application_round: state.applicationContext.application_round || "",
  };
  Object.entries(values).forEach(([key, value]) => {
    if (String(value).trim()) params.set(key, String(value).trim());
  });
  return params;
}

async function loadApplicationWorkflow(item, { forceRefresh = false } = {}) {
  const requestId = ++state.workflowRequestId;
  const context = captureSchoolContext();
  const cacheKey = workflowContextKey(item.school_name);
  const requestIsCurrent = () => requestId === state.workflowRequestId
    && schoolContextIsCurrent(context) && state.activeSchool === item.school_name
    && cacheKey === workflowContextKey(item.school_name);
  const content = $("#workflow-content");
  if (!content) return;
  content.setAttribute("aria-busy", "true");
  content.innerHTML = renderWorkflowLoading();

  try {
    const params = workflowRequestParams(item);
    const workflow = await fetchJson(
      `/application-workflow?${params.toString()}`,
      forceRefresh ? { cache: "no-store" } : {},
    );
    if (!requestIsCurrent()) return;
    state.workflowCache.set(cacheKey, workflow);
    renderApplicationWorkflow(workflow);
    renderApplicationCalendar();
    scheduleCalendarConflictAnalysis();
    if (calendarSyncFeatureEnabled() && state.calendarSync?.enabled) syncCalendarEvents({ quiet: true });
  } catch (error) {
    if (!requestIsCurrent()) return;
    content.setAttribute("aria-busy", "false");
    content.innerHTML = `
      <div class="experience-error">
        <strong>暫時無法載入已發布的申請流程</strong>
        <p>${escapeHtml(error.message)}</p>
        <button id="retry-workflow" type="button" class="secondary-button">重新載入</button>
      </div>`;
  }
  initIcons();
}

function renderApplicationWorkflow(workflow) {
  const content = $("#workflow-content");
  if (!content) return;
  state.activeWorkflow = workflow;
  content.setAttribute("aria-busy", "false");
  if (!workflow.steps?.length) {
    content.innerHTML = `
      <div class="empty-state">
        <i data-lucide="list-checks" aria-hidden="true"></i>
        <strong>尚未建立這所學校的官方流程</strong>
        <span>${escapeHtml(workflow.coverage_note)}</span>
        <small>官方資料完成查核並由管理者發布後，會自動顯示在這裡。</small>
      </div>`;
    initIcons();
    return;
  }

  const pendingStepCount = (workflow.steps || []).filter(workflowStepNeedsConfirmation).length;
  const fullyVerified = workflow.coverage_status === "official_verified" && pendingStepCount === 0;
  const applicabilityVerified = workflow.applicability_status === "verified";
  const publicationVerified = workflow.review_status === "published" && Boolean(workflow.published_at);
  const applicationRounds = workflow.effective_application_rounds || [];
  content.innerHTML = `
    <div class="workflow-status ${fullyVerified ? "verified" : "partial"}">
      <i data-lucide="${fullyVerified ? "badge-check" : "triangle-alert"}" aria-hidden="true"></i>
      <div>
        <strong>${fullyVerified ? "官方來源與送件細節已查核" : `官方來源已整理，${pendingStepCount} 個步驟仍需確認`}</strong>
        <p>${escapeHtml(workflow.coverage_note)}</p>
        <small>適用學年度：${workflow.academic_year ? escapeHtml(workflow.academic_year) : "待確認"} · 申請梯次：${applicationRounds.length ? applicationRounds.map(escapeHtml).join("、") : "待確認"} · 版本 ${escapeHtml(workflow.version || 1)} · 最後查核：${escapeHtml(formatDate(workflow.last_checked))}</small>
      </div>
    </div>
    <div class="workflow-warning${applicabilityVerified ? " is-verified" : ""}">
      <i data-lucide="${applicabilityVerified ? "badge-check" : "calendar-x-2"}" aria-hidden="true"></i>
      <div>
        <strong>${applicabilityVerified ? "適用年度與梯次已有官方來源" : "適用年度或梯次仍待確認"}</strong>
        <span>${escapeHtml(workflow.applicability_note || "不能把你選擇的年度或梯次自動套用到未標示版本的流程。")}</span>
      </div>
    </div>
    <div class="workflow-warning${publicationVerified ? " is-verified" : ""}">
      <i data-lucide="${publicationVerified ? "shield-check" : "shield-alert"}" aria-hidden="true"></i>
      <div>
        <strong>${publicationVerified ? "這份流程已完成正式發布" : "這是尚未完成正式發布的參考流程"}</strong>
        <span>${publicationVerified ? `發布時間：${escapeHtml(formatDate(workflow.published_at))}` : "可查看來源與準備方向，但正式發布前，即使資料中有精確日期也不會加入行事曆或截止提醒。"}</span>
      </div>
    </div>
    <div class="workflow-toolbar">
      <strong>共 ${workflow.steps.length} 個步驟</strong>
      <div class="workflow-toolbar-actions">
        ${workflow.workflow_id && workflow.issue_report_snapshot ? `<button type="button" class="secondary-button" data-workflow-issue-report>
          <i data-lucide="message-square-warning" aria-hidden="true"></i><span>回報規定錯誤</span>
        </button>` : ""}
        <button id="refresh-workflow" type="button" class="secondary-button">
          <i data-lucide="refresh-cw" aria-hidden="true"></i><span>重新載入流程資料</span>
        </button>
      </div>
    </div>
    <div class="workflow-timeline">
      ${workflow.steps.map((step, index) => renderWorkflowStep(step, index, workflow)).join("")}
    </div>
    <div class="workflow-sources">
      <strong>本流程使用的官方來源</strong>
      <div>
        ${(workflow.sources || [])
          .map(
            (source) => `<a href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer">
              <span><b>${escapeHtml(source.title)}</b><small>${escapeHtml(WORKFLOW_SOURCE_LABELS[source.authority] || "官方來源")}${source.priority ? ` · 優先級 ${escapeHtml(source.priority)}` : ""}</small></span><i data-lucide="external-link" aria-hidden="true"></i>
            </a>`
          )
          .join("")}
      </div>
      <p>${escapeHtml(workflow.disclaimer)}</p>
    </div>`;
  initIcons();
}

function createWorkflowIssueReportMutationId() {
  const suffix = window.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(16).slice(2)}-${Math.random().toString(16).slice(2)}`;
  return `workflow-report-${suffix}`;
}

function readWorkflowIssueReportPending() {
  const stored = state.workflowIssueReportPending
    || parseStoredJson(
      window.sessionStorage,
      APPLICATION_SESSION_KEYS.workflowIssueReportPending,
      null,
    );
  if (
    !stored
    || stored.account_id !== state.account?.id
    || typeof stored.mutation_id !== "string"
    || typeof stored.payload_key !== "string"
  ) {
    if (stored) clearWorkflowIssueReportPending();
    return null;
  }
  try {
    const payload = JSON.parse(stored.payload_key);
    if (!payload || typeof payload !== "object" || !payload.workflow_id) {
      clearWorkflowIssueReportPending();
      return null;
    }
  } catch (_) {
    clearWorkflowIssueReportPending();
    return null;
  }
  state.workflowIssueReportPending = stored;
  return stored;
}

function persistWorkflowIssueReportPending(payloadKey, mutationId) {
  const pending = {
    account_id: state.account?.id || "",
    mutation_id: mutationId,
    payload_key: payloadKey,
  };
  state.workflowIssueReportPending = pending;
  try {
    window.sessionStorage.setItem(
      APPLICATION_SESSION_KEYS.workflowIssueReportPending,
      JSON.stringify(pending),
    );
  } catch (_) {
    // In-memory retry remains available while this page stays open.
  }
}

function clearWorkflowIssueReportPending(mutationId = "") {
  const pending = state.workflowIssueReportPending;
  if (mutationId && pending?.mutation_id && pending.mutation_id !== mutationId) return;
  state.workflowIssueReportPending = null;
  try {
    const stored = parseStoredJson(
      window.sessionStorage,
      APPLICATION_SESSION_KEYS.workflowIssueReportPending,
      null,
    );
    if (!mutationId || !stored?.mutation_id || stored.mutation_id === mutationId) {
      window.sessionStorage.removeItem(APPLICATION_SESSION_KEYS.workflowIssueReportPending);
    }
  } catch (_) {
    // The in-memory copy has still been cleared.
  }
}

function closeWorkflowIssueReport({ force = false } = {}) {
  const dialog = $("#workflow-issue-report-dialog");
  const form = $("#workflow-issue-report-form");
  if (state.workflowIssueReportSubmitting && !force) {
    $("#workflow-issue-report-status").textContent = "回報仍在送出，請等待結果確認後再關閉。";
    return false;
  }
  if (dialog?.open) dialog.close();
  dialog?.querySelectorAll("button, input, select, textarea").forEach((control) => {
    control.disabled = false;
  });
  form?.reset();
  $("#workflow-issue-report-context").replaceChildren();
  $("#workflow-issue-report-status").textContent = "";
  state.workflowIssueReportContext = null;
  state.workflowIssueReportMutationId = "";
  state.workflowIssueReportPayloadKey = "";
  state.workflowIssueReportSubmitting = false;
  return true;
}

function openWorkflowIssueReport(button) {
  if (!state.account) {
    announce("登入後才能回報申請規定錯誤。", "info", true);
    openAuthDialog("register");
    return;
  }
  if (!state.account?.catalog_home_university) {
    announce("請先在個人設定選擇學校，再送出規定錯誤回報。", "info", true);
    openProfileDialog();
    return;
  }
  const form = $("#workflow-issue-report-form");
  const dialog = $("#workflow-issue-report-dialog");
  const pending = readWorkflowIssueReportPending();
  if (pending) {
    const pendingPayload = JSON.parse(pending.payload_key);
    const activeWorkflow = state.activeWorkflow;
    const isActiveSnapshot = activeWorkflow?.workflow_id === pendingPayload.workflow_id
      && activeWorkflow?.version === pendingPayload.workflow_version
      && activeWorkflow?.issue_report_snapshot === pendingPayload.workflow_snapshot;
    const pendingWorkflow = isActiveSnapshot
      ? activeWorkflow
      : {
        home_university: pendingPayload.home_school,
        school_name: pendingPayload.school_name,
        workflow_id: pendingPayload.workflow_id,
        version: pendingPayload.workflow_version,
        issue_report_snapshot: pendingPayload.workflow_snapshot,
        steps: [],
      };
    const pendingStep = pendingPayload.step_rule_id
      ? (pendingWorkflow.steps || []).find((item) => item.rule_id === pendingPayload.step_rule_id)
        || { rule_id: pendingPayload.step_rule_id, order: "", title: "先前選取的流程步驟" }
      : null;
    state.workflowIssueReportContext = {
      workflow: pendingWorkflow,
      step: pendingStep,
      basePayload: pendingPayload,
    };
    state.workflowIssueReportMutationId = pending.mutation_id;
    state.workflowIssueReportPayloadKey = pending.payload_key;
    form.reset();
    form.elements.category.value = pendingPayload.category;
    form.elements.description.value = pendingPayload.description;
    form.elements.official_source_url.value = pendingPayload.official_source_url;
    $("#workflow-issue-report-context").innerHTML = `
      <span><i data-lucide="rotate-ccw" aria-hidden="true"></i></span>
      <div><strong>${escapeHtml(pendingWorkflow.school_name)}</strong><small>先前回報結果尚未確認 · 原識別碼安全重試</small></div>`;
    $("#workflow-issue-report-status").textContent = "請不要修改原內容；再次確認後送出，系統會沿用同一識別碼查明先前結果。";
    dialog.showModal();
    initIcons();
    window.setTimeout(() => form.elements.confirm_boundary.focus(), 30);
    return;
  }
  const workflow = state.activeWorkflow;
  if (!workflow?.workflow_id || !workflow?.issue_report_snapshot) {
    announce("這份流程目前沒有可核對的正式版本識別，請重新載入後再試。", "error", true);
    return;
  }
  const stepRuleId = String(button?.dataset.stepRuleId || "").trim();
  const step = stepRuleId
    ? (workflow.steps || []).find((item) => String(item.rule_id || "") === stepRuleId)
    : null;
  if (stepRuleId && !step) {
    announce("找不到要回報的流程步驟，請重新載入後再試。", "error", true);
    return;
  }

  state.workflowIssueReportContext = { workflow, step };
  state.workflowIssueReportMutationId = "";
  state.workflowIssueReportPayloadKey = "";
  form.reset();
  form.elements.official_source_url.value = step?.action_url
    || workflow.sources?.[0]?.source_url
    || "";
  $("#workflow-issue-report-context").innerHTML = `
    <span><i data-lucide="${step ? "list-checks" : "school"}" aria-hidden="true"></i></span>
    <div><strong>${escapeHtml(workflow.school_name)}</strong><small>${step ? `步驟 ${escapeHtml(step.order)}：${escapeHtml(step.title)}` : `完整申請流程 · 版本 ${escapeHtml(workflow.version)}`}</small></div>`;
  $("#workflow-issue-report-status").textContent = "";
  dialog.showModal();
  initIcons();
  window.setTimeout(() => form.elements.category.focus(), 30);
}

function workflowIssueReportPayload(form) {
  const { workflow, step, basePayload } = state.workflowIssueReportContext || {};
  if (!workflow) return null;
  const profile = state.eligibilityProfile || {};
  const optional = (value) => String(value || "").trim() || null;
  return {
    home_school: basePayload?.home_school || workflow.home_university,
    school_name: basePayload?.school_name || workflow.school_name,
    workflow_id: basePayload?.workflow_id || workflow.workflow_id,
    workflow_version: basePayload?.workflow_version ?? workflow.version,
    workflow_snapshot: basePayload?.workflow_snapshot || workflow.issue_report_snapshot,
    step_rule_id: basePayload?.step_rule_id ?? step?.rule_id ?? null,
    college: basePayload?.college ?? optional(profile.college || state.applicationProfile?.college),
    department: basePayload?.department ?? optional(profile.department || state.applicationProfile?.department),
    academic_year: basePayload?.academic_year ?? optional(state.applicationContext.academic_year),
    application_round: basePayload?.application_round ?? optional(state.applicationContext.application_round),
    category: form.elements.category.value,
    description: form.elements.description.value.trim(),
    official_source_url: form.elements.official_source_url.value.trim(),
  };
}

function workflowIssueReportResponseMatches(response, payload) {
  const nullableFields = [
    "step_rule_id",
    "college",
    "department",
    "academic_year",
    "application_round",
  ];
  return Boolean(
    response
    && typeof response.id === "string"
    && response.id.trim()
    && response.status === "pending"
    && response.home_school === payload.home_school
    && response.school_name === payload.school_name
    && response.workflow_id === payload.workflow_id
    && Number.isInteger(response.workflow_version)
    && response.workflow_version === payload.workflow_version
    && response.workflow_snapshot === payload.workflow_snapshot
    && nullableFields.every(
      (field) => (response[field] ?? null) === (payload[field] ?? null),
    )
    && response.category === payload.category
    && response.description === payload.description
    && response.official_source_url === payload.official_source_url
  );
}

async function submitWorkflowIssueReport(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (state.workflowIssueReportSubmitting || !form.reportValidity()) return;
  if (!state.account?.catalog_home_university) {
    closeWorkflowIssueReport({ force: true });
    announce("尚未選擇學校，請先在個人設定選擇後再送出。", "error", true);
    openProfileDialog();
    return;
  }
  const payload = workflowIssueReportPayload(form);
  if (!payload) {
    announce("找不到要回報的流程，請關閉視窗並重新載入。", "error", true);
    return;
  }
  const payloadKey = JSON.stringify(payload);
  const pending = readWorkflowIssueReportPending();
  const status = $("#workflow-issue-report-status");
  if (pending && payloadKey !== pending.payload_key) {
    status.textContent = "先前回報結果尚未確認，不能修改內容後改用新識別碼；請恢復原內容再安全重試。";
    return;
  }
  if (pending) {
    state.workflowIssueReportPayloadKey = pending.payload_key;
    state.workflowIssueReportMutationId = pending.mutation_id;
  } else if (payloadKey !== state.workflowIssueReportPayloadKey) {
    state.workflowIssueReportPayloadKey = payloadKey;
    state.workflowIssueReportMutationId = createWorkflowIssueReportMutationId();
  }

  const requestId = ++state.workflowIssueReportRequestId;
  const mutationId = state.workflowIssueReportMutationId;
  const controls = form.querySelectorAll("button, input, select, textarea");
  const abortController = new AbortController();
  const timeoutId = window.setTimeout(() => abortController.abort(), 30_000);
  state.workflowIssueReportAbortController = abortController;
  persistWorkflowIssueReportPending(payloadKey, mutationId);
  state.workflowIssueReportSubmitting = true;
  controls.forEach((control) => { control.disabled = true; });
  status.textContent = "正在安全保存回報…";
  try {
    const response = await fetchJson("/application-workflow-issue-reports", {
      method: "POST",
      signal: abortController.signal,
      headers: {
        "Content-Type": "application/json",
        "X-Content-Report-Mutation-ID": mutationId,
      },
      body: payloadKey,
    });
    if (requestId !== state.workflowIssueReportRequestId) return;
    if (!workflowIssueReportResponseMatches(response, payload)) {
      const error = new Error("伺服器沒有回傳可驗證的回報收件結果。");
      error.outcomeUnknown = true;
      throw error;
    }
    clearWorkflowIssueReportPending(mutationId);
    closeWorkflowIssueReport({ force: true });
    announce("回報已送出。管理員會先核對；這不會直接改動正式規定。", "success", true);
  } catch (error) {
    if (requestId !== state.workflowIssueReportRequestId) return;
    if (error?.status && error.status < 500) {
      clearWorkflowIssueReportPending(mutationId);
      state.workflowIssueReportMutationId = "";
      state.workflowIssueReportPayloadKey = "";
    }
    status.textContent = !error?.status || error.status >= 500
      ? "連線或伺服器回應中斷，結果尚未確認；請不要修改內容，稍後可用同一識別碼安全重試。"
      : error.message;
  } finally {
    window.clearTimeout(timeoutId);
    if (state.workflowIssueReportAbortController === abortController) {
      state.workflowIssueReportAbortController = null;
    }
    if (requestId !== state.workflowIssueReportRequestId) return;
    state.workflowIssueReportSubmitting = false;
    controls.forEach((control) => { control.disabled = false; });
  }
}

function workflowSubmissionProgressKey(workflow, step) {
  return [
    activeHomeSchool(),
    workflow.workflow_id || workflow.school_name,
    `v${workflow.version || 1}`,
    step.rule_id || `step-${step.order}`,
  ].join("::");
}

function workflowSubmissionProgressRecord(workflow, step) {
  return state.submissionProgress[workflowSubmissionProgressKey(workflow, step)] || {
    title: step.title,
    method: step.submission?.method || "unknown",
    status: "not_started",
    proof_metadata: null,
  };
}

function submissionProgressActions(progress, method) {
  if (progress.status === "not_started") {
    return [{ action: "start", label: "開始準備", style: "primary-button", icon: "list-checks" }];
  }
  if (progress.status === "preparing") {
    const label = method === "paper"
      ? "我已寄出／送交紙本"
      : method === "in_person"
        ? "我已親自送交"
        : method === "mixed"
          ? "我已完成所有送件部分"
          : "我已送出";
    return [{ action: "submit", label, style: "primary-button", icon: "send" }];
  }
  if (progress.status === "submitted") {
    const actions = [{ action: "confirm_receipt", label: "記錄收件證明", style: "primary-button", icon: "badge-check" }];
    if (method !== "paper" && method !== "mixed") {
      actions.push({ action: "complete", label: "沒有回條，手動標記完成", style: "secondary-button", icon: "check" });
    }
    return actions;
  }
  if (progress.status === "receipt_confirmed") {
    return [{ action: "complete", label: "確認並標記完成", style: "primary-button", icon: "check-check" }];
  }
  return [];
}

function submissionProgressNextStep(progress, method) {
  if (progress.status === "not_started") {
    return method === "mixed"
      ? "先確認混合流程的每一個線上、電子郵件、紙本或親送部分。"
      : "先備齊文件並再次核對官方送件方式。";
  }
  if (progress.status === "preparing") {
    if (method === "mixed") return "完成規定的所有紙本與線上／電子郵件 部分後，再由你手動記錄。";
    if (method === "paper") return "實際寄出或送交紙本後，再由你手動記錄。";
    if (method === "in_person") return "親自交給承辦單位後，再由你手動記錄。";
    return "完成實際上傳或寄信後，再由你手動記錄。";
  }
  if (progress.status === "submitted") return method === "paper" || method === "mixed"
    ? "等待所有紙本部分送達，再記錄物流或收件證明；不能只以寄出日判斷完成。"
    : "確認承辦單位或系統已收件；有回條可記錄，沒有回條也能由你手動完成。";
  if (progress.status === "receipt_confirmed") return "確認附件、份數與收件狀態後，再標記完成。";
  return "這是你的手動完成紀錄；本平台沒有代替你送件。";
}

function submissionDefaultProofKind(method) {
  if (method === "paper" || method === "mixed") return "tracking";
  if (method === "online") return "submission_receipt";
  if (method === "email") return "confirmation_email";
  if (method === "in_person") return "in_person_receipt";
  return "other";
}

function renderWorkflowSubmissionProgress(workflow, step) {
  const submission = step.submission || { method: "unknown" };
  const method = submission.method || "unknown";
  const progressKey = workflowSubmissionProgressKey(workflow, step);
  const progress = workflowSubmissionProgressRecord(workflow, step);
  const progressActions = submissionProgressActions(progress, method);
  const proof = progress.proof_metadata;
  const proofSummary = proof
    ? `${SUBMISSION_PROOF_LABELS[proof.kind] || "收件證明"}${proof.reference ? ` · ${proof.reference}` : ""}${proof.file_name ? ` · ${proof.file_name}` : ""}${proof.recorded_at ? ` · ${formatDate(proof.recorded_at)} 由你記錄` : ""}`
    : "尚未記錄";
  const paperFlow = method === "paper" || method === "mixed";
  const deadlines = paperFlow
    ? [
      submission.send_by_at ? `最晚寄出：${formatDate(submission.send_by_at)}` : "",
      submission.arrival_deadline_at
        ? `必須送達：${formatDate(submission.arrival_deadline_at)}`
        : "必須送達：待確認（不要只以寄出日判斷）",
    ].filter(Boolean)
    : [submission.arrival_deadline_at
      ? `收件截止：${formatDate(submission.arrival_deadline_at)}`
      : step.deadline_at
        ? `截止：${formatDate(step.deadline_at)}`
        : step.deadline_status === "reference_only" && step.timing
          ? `參考時程：${step.timing}（精確日期待確認，不會自動提醒）`
          : "期限待官方確認，不會自動提醒"];
  if (method === "unknown") {
    return `<div class="workflow-progress is-disabled"><div><h4>我的送件紀錄</h4><strong>送件方式待確認</strong><small>官方方式確認前不能標記完成。</small></div></div>`;
  }
  const proofKind = submissionDefaultProofKind(method);
  return `
    <div class="workflow-progress status-${escapeHtml(progress.status)}" data-submission-progress-key="${escapeHtml(progressKey)}">
      <div class="workflow-progress-heading">
        <div><h4>我的送件紀錄</h4><strong>${escapeHtml(SUBMISSION_PROGRESS_STATUS_LABELS[progress.status] || progress.status)}</strong></div>
        <span>${escapeHtml(WORKFLOW_SUBMISSION_LABELS[method] || method)} · 學生手動</span>
      </div>
      <dl>
        <div><dt>下一步</dt><dd>${escapeHtml(submissionProgressNextStep(progress, method))}</dd></div>
        <div><dt>承辦</dt><dd>${escapeHtml(step.responsible_unit || step.responsible_party || "待確認")}</dd></div>
        <div><dt>期限</dt><dd>${deadlines.map((deadline) => `<span>${escapeHtml(deadline)}</span>`).join("")}</dd></div>
        <div><dt>收件證明</dt><dd>${escapeHtml(proofSummary)}</dd></div>
      </dl>
      ${state.account && progress.status === "submitted" ? `
        <div class="workflow-proof-fields">
          <label><span>證明種類</span><select data-submission-proof-kind><option value="tracking" ${proofKind === "tracking" ? "selected" : ""}>物流追蹤紀錄</option><option value="submission_receipt" ${proofKind === "submission_receipt" ? "selected" : ""}>系統送出回條</option><option value="confirmation_email" ${proofKind === "confirmation_email" ? "selected" : ""}>收件確認 電子郵件</option><option value="in_person_receipt" ${proofKind === "in_person_receipt" ? "selected" : ""}>親送收據</option><option value="other" ${proofKind === "other" ? "selected" : ""}>其他收件證明</option></select></label>
          <label><span>追蹤碼／收件編號（選填）</span><input data-submission-proof-reference maxlength="200" autocomplete="off" /></label>
          <small>只保存證明種類、編號與時間，不上傳或保存證明原檔。</small>
        </div>` : ""}
      <div class="workflow-progress-actions">
        ${!state.account ? `<button type="button" class="secondary-button" data-open-submission-auth><i data-lucide="log-in" aria-hidden="true"></i><span>登入後記錄進度</span></button>` : progressActions.map(({ action, label, style, icon }) => `<button type="button" class="${style}" data-submission-action="${action}" data-submission-progress-key="${escapeHtml(progressKey)}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${escapeHtml(label)}</span></button>`).join("")}
        ${state.account && progress.status !== "not_started" ? `<button type="button" class="text-button" data-submission-action="revert" data-submission-progress-key="${escapeHtml(progressKey)}">撤銷上一個標記</button>` : ""}
      </div>
      <p><i data-lucide="shield-check" aria-hidden="true"></i><span>所有狀態與收件證明都由你手動記錄；平台不會代送，也不會把這些標記當成校方正式收件結果。</span></p>
    </div>`;
}

function findSubmissionProgressContext(progressKey) {
  for (const workflow of state.workflowCache.values()) {
    const step = (workflow.steps || []).find((item) => workflowSubmissionProgressKey(workflow, item) === progressKey);
    if (step) return { workflow, step };
  }
  return null;
}

async function handleSubmissionProgressAction(button) {
  if (!state.account) {
    openAuthDialog();
    return;
  }
  const progressKey = button.dataset.submissionProgressKey;
  const context = findSubmissionProgressContext(progressKey);
  if (!context) {
    announce("找不到這個送件步驟，請重新載入官方流程。", "error", true);
    return;
  }
  const { workflow, step } = context;
  const card = button.closest(".workflow-progress");
  const action = button.dataset.submissionAction;
  const proofKind = card?.querySelector("[data-submission-proof-kind]")?.value;
  const proofReference = card?.querySelector("[data-submission-proof-reference]")?.value.trim();
  const submission = step.submission || {};
  const payload = {
    home_school: activeHomeSchool(),
    progress_key: progressKey,
    action,
    method: submission.method || "unknown",
    title: step.title,
    responsible_unit: step.responsible_unit || step.responsible_party || null,
    send_by_at: submission.send_by_at || null,
    arrival_deadline_at: submission.arrival_deadline_at || null,
    proof_metadata: action === "confirm_receipt" ? {
      kind: proofKind || submissionDefaultProofKind(submission.method),
      reference: proofReference || null,
    } : null,
    note: submission.deadline_note || null,
  };
  card?.querySelectorAll("[data-submission-action]").forEach((item) => { item.disabled = true; });
  try {
    const progress = await fetchJson("/account/submission-progress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.submissionProgress[progressKey] = progress;
    persistAccountWorkspaceLocally();
    await loadAccountWorkspace({ homeSchool: activeHomeSchool() });
    const refreshedCard = [...document.querySelectorAll("[data-submission-progress-key]")]
      .find((item) => item.dataset.submissionProgressKey === progressKey);
    if (refreshedCard) {
      const stepDetails = refreshedCard.closest("details");
      if (stepDetails) stepDetails.open = true;
      refreshedCard.scrollIntoView({ block: "center", behavior: window.UniWayMotion?.reduced ? "instant" : "smooth" });
    }
    announce("送件進度已同步；這仍是你自己的紀錄，不是校方收件結果。", "success");
  } catch (error) {
    const current = error.payload?.detail?.current_workspace;
    if (error.status === 409 && current) {
      await loadAccountWorkspace({ homeSchool: activeHomeSchool() }).catch(() => null);
      announce("另一個裝置剛更新申請進度；已載入最新版本，請確認後再操作。", "error", true);
      return;
    }
    if (!error.status || [408, 502, 503, 504].includes(error.status)) {
      await loadAccountWorkspace({ homeSchool: activeHomeSchool() }).catch(() => null);
      announce("連線或伺服器回應中斷，本次結果尚未確認；系統不會自動重送，請先確認目前進度。", "error", true);
      return;
    }
    announce(error.message, "error", true);
    card?.querySelectorAll("[data-submission-action]").forEach((item) => { item.disabled = false; });
  }
}

function renderWorkflowStep(step, index, workflow) {
  const needsConfirmation = workflowStepNeedsConfirmation(step);
  const requirements = step.document_requirements?.length
    ? step.document_requirements
    : (step.required_documents || []).map((name) => ({ name, copy_type: "unspecified", signatures: [], stamps: [], needs_confirmation: true }));
  return `
    <details class="workflow-step${needsConfirmation ? " needs-confirmation" : ""}">
      <summary>
        <span class="workflow-step-number" aria-hidden="true">${escapeHtml(step.order)}</span>
        <span class="workflow-step-title">
          <small>${escapeHtml(step.phase)} · ${escapeHtml(step.responsible_unit || step.responsible_party)}</small>
          <strong>${escapeHtml(step.title)}</strong>
          ${step.timing ? `<span><i data-lucide="calendar-clock" aria-hidden="true"></i>${highlightHtml(step.timing)}</span>` : ""}
        </span>
        <i data-lucide="chevron-down" aria-hidden="true"></i>
      </summary>
      <div class="workflow-step-body">
        <p>${highlightHtml(step.summary)}</p>
        ${renderWorkflowScope(step, workflow)}
        ${needsConfirmation ? `<div class="workflow-warning"><i data-lucide="triangle-alert" aria-hidden="true"></i><div><strong>此步驟仍有送件或文件細節待確認。</strong>${step.confirmation_contact ? `<span>請聯絡：${escapeHtml(step.confirmation_contact)}</span>` : ""}</div></div>` : ""}
        ${renderWorkflowDeadlineStatus(step, workflow)}
        ${renderWorkflowSubmission(step)}
        ${renderWorkflowSubmissionProgress(workflow, step)}
        ${step.details?.length ? `<div><h4>具體要做</h4><ul>${step.details.map((detail) => `<li>${highlightHtml(detail)}</li>`).join("")}</ul></div>` : ""}
        ${requirements.length ? `<div><h4>這一步要準備</h4><ul class="workflow-documents">${requirements.map((requirement) => renderWorkflowDocumentRequirement(requirement, { showReferenceForm: workflow.home_university === "國立中央大學" })).join("")}</ul></div>` : ""}
        ${step.action_url ? `<a class="official-link workflow-action" href="${escapeHtml(step.action_url)}" target="_blank" rel="noreferrer"><span>開啟這一步的官方頁面</span><i data-lucide="external-link" aria-hidden="true"></i></a>` : ""}
        ${workflow.workflow_id && workflow.issue_report_snapshot && step.rule_id ? `<div class="workflow-step-report"><span>發現資格、期限、文件或送件資訊不一致？</span><button type="button" class="text-button" data-workflow-issue-report data-step-rule-id="${escapeHtml(step.rule_id)}"><i data-lucide="message-square-warning" aria-hidden="true"></i>回報此步驟</button></div>` : ""}
      </div>
    </details>`;
}

function workflowStepNeedsConfirmation(step) {
  return step.support_status === "needs_confirmation"
    || Boolean(step.needs_confirmation)
    || step.deadline_status === "reference_only"
    || step.deadline_status === "needs_confirmation"
    || workflowArrivalDeadlinePending(step)
    || (step.document_requirements || []).some((item) => item.needs_confirmation);
}

function renderWorkflowDeadlineStatus(step, workflow) {
  if (step.deadline_status === "not_applicable") return "";
  if (step.deadline_status === "verified_exact" && step.deadline_reminder_eligible) {
    return `
      <div class="workflow-warning is-verified">
        <i data-lucide="calendar-check-2" aria-hidden="true"></i>
        <div>
          <strong>精確期限已連到官方來源，可加入提醒。</strong>
          <span>最後查核：${escapeHtml(formatDate(step.deadline_checked_at))}</span>
        </div>
      </div>`;
  }
  if (step.deadline_status === "verified_exact") {
    return `
      <div class="workflow-warning">
        <i data-lucide="shield-alert" aria-hidden="true"></i>
        <div>
          <strong>精確期限已有來源，但流程尚未正式發布。</strong>
          <span>最後查核：${escapeHtml(formatDate(step.deadline_checked_at))}；目前狀態為 ${escapeHtml(workflow.review_status || "legacy")}，不會加入行事曆或截止提醒。</span>
        </div>
      </div>`;
  }
  const referenceOnly = step.deadline_status === "reference_only";
  return `
    <div class="workflow-warning">
      <i data-lucide="calendar-x-2" aria-hidden="true"></i>
      <div>
        <strong>${referenceOnly ? "目前只有參考時程，沒有當期精確日期。" : "精確期限仍待官方確認。"}</strong>
        <span>${referenceOnly && step.timing ? `參考：${escapeHtml(step.timing)}；` : ""}這個日期不會加入行事曆或截止提醒，請聯絡 ${escapeHtml(step.confirmation_contact || "本校國際事務處")}。</span>
      </div>
    </div>`;
}

function workflowArrivalDeadlinePending(step) {
  const method = step.submission?.method;
  return (method === "paper" || method === "mixed")
    && !step.submission?.arrival_deadline_at;
}

function renderWorkflowScope(step, workflow) {
  const scope = step.scope || {};
  const labels = [
    ...(scope.colleges || []),
    ...(scope.departments || []),
    ...(scope.academic_years || []).map((value) => `${value} 學年度`),
    ...(scope.application_rounds || []),
  ];
  if (!labels.length) return "";
  const pendingHostScope = workflow?.home_university === "國立中央大學"
    && Boolean(scope.partner_universities?.length)
    && workflowStepNeedsConfirmation(step);
  const caption = pendingHostScope ? "規劃範圍（當期適用待確認）" : "適用範圍";
  return `<div class="workflow-rule-meta"><strong>${caption}</strong>${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>`;
}

function renderWorkflowSubmission(step) {
  const submission = step.submission || { method: "unknown" };
  const method = submission.method || "unknown";
  const paperFlow = method === "paper" || method === "mixed";
  const arrivalPending = paperFlow && !submission.arrival_deadline_at;
  const details = [
    submission.office ? `承辦地點：${submission.office}` : "",
    submission.address ? `地址：${submission.address}` : "",
    submission.receiving_hours ? `收件時間：${submission.receiving_hours}` : "",
    submission.email ? `電子郵件：${submission.email}` : "",
    submission.send_by_at ? `最晚寄出：${formatDate(submission.send_by_at)}` : "",
    submission.arrival_deadline_at ? `必須送達：${formatDate(submission.arrival_deadline_at)}` : "",
    arrivalPending ? "必須送達：待確認（不要只以寄出日判斷）" : "",
    submission.deadline_note ? `期限說明：${submission.deadline_note}` : "",
  ].filter(Boolean);
  return `
    <div class="workflow-submission${method === "unknown" || arrivalPending ? " is-pending" : ""}">
      <h4>送件方式</h4>
      <strong>${escapeHtml(WORKFLOW_SUBMISSION_LABELS[method] || method)}</strong>
      ${details.length ? `<ul>${details.map((detail) => `<li>${escapeHtml(detail)}</li>`).join("")}</ul>` : method === "unknown" ? "<p>官方資料尚未明確標示紙本、線上或親送方式。</p>" : ""}
    </div>`;
}

function renderWorkflowDocumentRequirement(requirement, { showReferenceForm = false } = {}) {
  const metadata = [];
  const stages = {nomination:"提名",student_application:"申請",after_application:"申請後補件（不等錄取）",second_submission:"第二次文件送件（時點待確認）",post_offer:"錄取後",after_dorm_assignment:"宿舍分配後",conditional_program:"特定計畫文件"};
  if (requirement.stage) metadata.push(`階段：${stages[requirement.stage] || requirement.stage}`);
  if (requirement.applicability_status) metadata.push(`適用性：${({verified_current:"當期依據已核",needs_confirmation:"當期適用待確認",reference_only:"歷史參考"})[requirement.applicability_status]}`);
  if (requirement.applicability_year) metadata.push(requirement.applicability_year);
  if (requirement.applicability_note) metadata.push(requirement.applicability_note);
  if (requirement.conditional) metadata.push(`適用條件：${requirement.condition || requirement.name}`);
  if (requirement.copies) metadata.push(`${requirement.copies} 份`);
  metadata.push(WORKFLOW_COPY_LABELS[requirement.copy_type] || "文件形式待確認");
  if (requirement.signatures?.length) metadata.push(`簽署：${requirement.signatures.join("、")}`);
  if (requirement.stamps?.length) metadata.push(`核章：${requirement.stamps.join("、")}`);
  const referenceUrl = showReferenceForm && requirement.official_form_url
    ? safeSourceUrl(requirement.official_form_url)
    : null;
  return `
    <li class="${requirement.needs_confirmation ? "needs-confirmation" : ""}">
      <i data-lucide="${requirement.needs_confirmation ? "circle-help" : "file-check-2"}" aria-hidden="true"></i>
      <span><b>${highlightHtml(requirement.name)}</b><small>${metadata.map(escapeHtml).join(" · ")}${requirement.needs_confirmation ? " · 適用性及送件細節待確認" : ""}</small>${!showReferenceForm && safeSourceUrl(requirement.official_form_url) ? (requirement.official_form_verified ? `<a href="${escapeHtml(requirement.official_form_url)}" target="_blank" rel="noreferrer">開啟已核實官方表格／文件</a><small>官方文件可查閱；流程尚未發布，仍須核對適用計畫、年度及簽章。</small>` : `<a href="${escapeHtml(requirement.official_form_url)}" target="_blank" rel="noreferrer">查看官方表格來源（待核實）</a><small>原檔下載未核實，適用年度仍待確認。</small>`) : ""}${referenceUrl && referenceUrl !== "#" ? `<small><a href="${escapeHtml(referenceUrl)}" target="_blank" rel="noopener noreferrer">官方參考表格（當期適用待確認）</a></small>` : ""}</span>
    </li>`;
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
  updateQuickDecisionFit(digest);
  renderStudentLife(digest);
  renderDiscoveryExperiences(digest);
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
  if (!state.account) {
    openAuthDialog();
    throw new Error("登入後才能發文、留言或使用私訊。");
  }
  if (!state.communityIdentityOptions) await loadCommunityIdentityOptions();
  if (state.communityIdentityAccountId === state.account.id && state.anonymousIdentity?.id && state.anonymousIdentity?.access_token) return state.anonymousIdentity;
  const session = await fetchJson("/auth/community-identity", { method: "POST" });
  state.anonymousIdentity = session;
  state.communityIdentityAccountId = state.account.id;
  try {
    window.localStorage.setItem(STORAGE_KEYS.communityIdentity, JSON.stringify(session));
  } catch (_) {
    // The anonymous session remains available until this tab is closed.
  }
  return session;
}

function fallbackCommunityIdentityOptions() {
  const schoolEnabled = Boolean(state.account?.catalog_home_university);
  const departmentEnabled = Boolean(
    schoolEnabled && state.account?.verified_department
  );
  return {
    default_mode: "anonymous",
    options: [
      { mode: "anonymous", label: "匿名學生", enabled: true },
      { mode: "real_name", label: state.account?.display_name || "本名", enabled: Boolean(state.account) },
      {
        mode: "verified_school",
        label: schoolEnabled ? `${state.account.catalog_home_university}學生` : "學校身分",
        enabled: schoolEnabled,
        unavailable_reason: schoolEnabled ? null : "選擇學校後可使用",
      },
      {
        mode: "verified_department",
        label: departmentEnabled
          ? `${state.account.catalog_home_university} ${state.account.verified_department}`
          : "學校與系所",
        enabled: departmentEnabled,
        unavailable_reason: departmentEnabled ? null : "驗證資料尚未包含系所",
      },
    ],
  };
}

async function loadCommunityIdentityOptions() {
  if (!state.account) {
    state.communityIdentityOptions = null;
    renderGlobalCommunityIdentitySelector();
    return null;
  }
  try {
    state.communityIdentityOptions = await fetchJson("/auth/community-identity-options");
  } catch (_) {
    state.communityIdentityOptions = fallbackCommunityIdentityOptions();
  }
  renderGlobalCommunityIdentitySelector();
  return state.communityIdentityOptions;
}

function renderCommunityIdentitySelector() {
  const identityOptions = state.communityIdentityOptions || fallbackCommunityIdentityOptions();
  const options = identityOptions.options || [];
  const defaultMode = identityOptions.default_mode || "anonymous";
  return `<label class="community-identity-selector"><span>這次顯示身分</span><select name="identity_mode" data-community-identity-select>${options.map((option) => `<option value="${escapeHtml(option.mode)}" ${option.mode === defaultMode ? "selected" : ""} ${option.enabled ? "" : "disabled"} data-identity-label="${escapeHtml(option.label)}">${escapeHtml(option.label)}${option.enabled ? "" : `（${escapeHtml(option.unavailable_reason || "目前無法使用")}）`}</option>`).join("")}</select><small data-community-identity-preview aria-live="polite">這次公開顯示：${escapeHtml(options.find((option) => option.mode === defaultMode)?.label || "匿名學生")}（每次送出可重新選擇）</small></label>`;
}

function renderGlobalCommunityIdentitySelector() {
  const container = $("#global-community-identity");
  if (!container) return;
  container.innerHTML = state.account
    ? renderCommunityIdentitySelector()
    : '<p class="community-access-note">登入後才可發文；瀏覽與比較不需要登入。</p>';
}

function updateCommunityIdentityPreview(select) {
  const preview = select.closest("label")?.querySelector("[data-community-identity-preview]");
  const label = select.selectedOptions[0]?.dataset.identityLabel
    || select.selectedOptions[0]?.textContent
    || "匿名學生";
  if (preview) preview.textContent = `這次公開顯示：${label}（每次送出可重新選擇）`;
}

function resetCommunityIdentityPreviews(container) {
  container.querySelectorAll("[data-community-identity-select]").forEach(
    updateCommunityIdentityPreview
  );
}

async function fetchCommunityAuth(url, options = {}) {
  const requestContext = captureAuthenticatedRequestContext();
  const { communityIdentityRetry, ...fetchOptions } = options;
  const response = await fetch(url, {
    ...fetchOptions,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...communityAuthHeaders(),
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  assertAuthenticatedRequestCurrent(requestContext);
  if (response.status === 401 && state.account && !communityIdentityRetry
      && typeof data.detail === "string" && data.detail.includes("匿名身分")) {
    state.anonymousIdentity = null;
    await ensureAnonymousIdentity();
    return fetchCommunityAuth(url, { ...options, communityIdentityRetry: true });
  }
  if (!response.ok) {
    const error = new Error(data.detail || `伺服器回應 ${response.status}`);
    error.status = response.status;
    error.payload = data;
    throw error;
  }
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
    const [questions, chat, conversations] = await Promise.all([
      fetchJson(`/community/questions?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`),
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
    const hub = { questions, posts: [], chat, conversations, messages: Object.fromEntries(conversationMessages) };
    state.communityCache.set(item.school_name, hub);
    renderCommunityThreads(hub);
  } catch (error) {
    if (error.staleSession) {
      content.setAttribute("aria-busy", "false");
      return;
    }
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
      <small>${state.account ? "每次發文或留言都能選擇顯示身分，預設匿名；請勿張貼聯絡方式或個資。" : "內容可公開閱讀；登入後才能發文、留言與使用邀請制私訊。"}</small>
    </div>
    <div class="community-mode-switch" role="tablist" aria-label="社群功能">
      ${[
        ["posts", "動態貼文", "layout-list"],
        ["chat", "公開聊天室", "messages-square"],
        ["messages", "私訊", "mail"],
      ].map(([view, label, icon]) => `<button type="button" role="tab" data-community-view="${view}" aria-selected="${state.communityView === view}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${label}</span></button>`).join("")}
    </div>
    <section class="community-pane" data-community-pane="posts" ${state.communityView === "posts" ? "" : "hidden"}>
      ${renderCommunityPostComposer()}
      <div class="community-post-list">${data.posts.length ? data.posts.map(renderCommunityPostThread).join("") : renderCommunityEmpty("還沒有公開貼文", "分享申請問題、住宿情報或實際交換經驗，其他學生就能一起補充。")}</div>
      ${data.questions.length ? `<details class="legacy-community-questions"><summary><span>查看既有公開問答</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div class="community-thread-list">${data.questions.map(renderCommunityThread).join("")}</div></details>` : ""}
    </section>
    <section class="community-pane" data-community-pane="chat" ${state.communityView === "chat" ? "" : "hidden"}>
      <div class="public-chat-stream">${data.chat.length ? data.chat.map(renderPublicChatMessage).join("") : renderCommunityEmpty("聊天室還沒有訊息", "可以先詢問是否有人正在申請同一間學校。")}</div>
      ${state.account ? `<form id="public-chat-form" class="community-inline-composer"><label class="sr-only" for="public-chat-body">公開訊息</label><input id="public-chat-body" name="body" minlength="2" maxlength="500" required placeholder="公開詢問這間學校的申請或生活…" />${renderCommunityIdentitySelector()}<button type="submit" class="primary-button" aria-label="送出公開訊息"><i data-lucide="send" aria-hidden="true"></i><span>送出</span></button><div class="form-status" role="status"></div></form>` : '<button type="button" class="secondary-button" data-open-auth>登入後加入聊天</button>'}
    </section>
    <section class="community-pane" data-community-pane="messages" ${state.communityView === "messages" ? "" : "hidden"}>
      ${state.account ? '<form id="private-invite-form" class="private-invite-form" hidden><div><span class="section-kicker">私訊邀請</span><strong id="private-invite-name">匿名學生</strong></div><input type="hidden" name="recipient_id" /><label><span>先說明想請教的事情</span><textarea name="initial_message" minlength="5" maxlength="500" required placeholder="對方接受邀請後，才能繼續私訊。"></textarea></label><div class="community-form-footer"><button type="button" class="secondary-button" data-cancel-invite>取消</button><button type="submit" class="primary-button"><i data-lucide="mail-plus" aria-hidden="true"></i><span>送出邀請</span></button><div class="form-status" role="status"></div></div></form>' : ""}
      <div class="private-conversation-list">${state.account ? (data.conversations.length ? data.conversations.map((conversation) => renderPrivateConversation(conversation, data.messages[conversation.id] || [])).join("") : renderCommunityEmpty("目前沒有私訊", "從公開貼文或聊天室點選「邀請私訊」，對方接受後才能對話。")) : renderCommunityEmpty("登入後使用私訊", "雙方同意後才能開始對話，也可以隨時封鎖與檢舉。")}</div>
    </section>`;
  initIcons();
}

function renderCommunityEmpty(title, detail, kind = "empty", action = "") {
  const isError = kind === "error";
  return `<div class="community-empty product-state is-${escapeHtml(kind)}" data-state="${escapeHtml(kind)}" role="${isError ? "alert" : "status"}"><i data-lucide="${isError ? "circle-alert" : "message-circle"}" aria-hidden="true"></i><div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(detail)}</p>${action}</div></div>`;
}

function renderCommunityPostComposer() {
  return `<div class="community-post-composer community-fixed-board-note"><span><i data-lucide="signpost" aria-hidden="true"></i></span><div><strong>公開貼文集中在固定看板</strong><small>合作校頁面保留校友問答；新貼文請發布到公共留學板、語言學校板，或你已驗證學校的交換板。</small></div><button type="button" class="secondary-button" data-open-global-community-composer>選擇看板發文</button></div>`;
}

function communityBoardAccessForPost(post) {
  const boardId = post.board_id
    || communityBoardIdForSchool(post.school_name)
    || (post.school_name === LANGUAGE_SCHOOL_COMMUNITY_BOARD ? LANGUAGE_SCHOOL_COMMUNITY_BOARD_ID : PUBLIC_COMMUNITY_BOARD_ID);
  return state.communityBoards.find((board) => board.id === boardId) || null;
}

function renderCommunityPostThread(thread, { global = false } = {}) {
  const post = thread.post;
  const comments = thread.comments || [];
  const canInvite = !global && state.account && post.author_id && post.author_id !== state.anonymousIdentity?.id;
  const canDeletePost = state.account && post.viewer_can_delete;
  const meta = [
    communityTopicLabel(post.topic),
    post.country,
    post.academic_year,
    applicationStageLabel(post.application_stage),
  ].filter(Boolean);
  const publicBoard = PUBLIC_COMMUNITY_BOARDS.includes(post.school_name);
  const universityBoard = state.supportedUniversities.some(
    (item) => normalize(item.school_name) === normalize(post.school_name)
  );
  let schoolAction = `<span><i data-lucide="globe-2" aria-hidden="true"></i>${PUBLIC_COMMUNITY_BOARD}</span>`;
  if (post.school_name === LANGUAGE_SCHOOL_COMMUNITY_BOARD) {
    schoolAction = `<a class="text-action post-board-link" href="#language-school-board"><i data-lucide="languages" aria-hidden="true"></i><span>${LANGUAGE_SCHOOL_COMMUNITY_BOARD}</span></a>`;
  } else if (universityBoard) {
    schoolAction = `<a class="text-action post-board-link" href="#board=${encodeURIComponent(post.school_name)}"><i data-lucide="graduation-cap" aria-hidden="true"></i><span>${escapeHtml(post.school_name)}板</span></a>`;
  } else if (global && !publicBoard) {
    schoolAction = `<button type="button" class="text-action school-detail-trigger" data-school-name="${escapeHtml(post.school_name)}"><i data-lucide="school" aria-hidden="true"></i><span>${escapeHtml(post.school_name)}</span></button>`;
  }
  const boardAccess = communityBoardAccessForPost(post);
  const commentComposer = boardAccess?.can_comment
    ? `<form class="community-inline-composer post-comment-form" data-post-id="${escapeHtml(post.id)}"><label class="sr-only">回覆內容</label><input name="body" minlength="2" maxlength="800" required placeholder="補充具體資訊…" />${renderCommunityIdentitySelector()}<button type="submit" class="secondary-button"><i data-lucide="reply" aria-hidden="true"></i><span>回覆</span></button><div class="form-status" role="status"></div></form>`
    : !state.account
      ? '<button type="button" class="secondary-button" data-open-auth><i data-lucide="log-in" aria-hidden="true"></i><span>登入後回覆</span></button>'
      : `<div class="community-access-note community-access-action"><span>${escapeHtml(boardAccess?.unavailable_reason || "目前不能在這個看板留言。")}</span><button type="button" class="text-action" data-open-verification>查看驗證狀態</button></div>`;
  return `<article class="community-post-card" data-community-school="${escapeHtml(post.school_name)}">
    <div class="community-post-meta"><span>${escapeHtml({ discussion: "討論", question: "請益", experience: "經驗" }[post.post_type] || "貼文")}</span><span>${escapeHtml(meta.join(" · "))}</span><time>${escapeHtml(formatDate(post.created_at))}</time></div>
    <h3>${escapeHtml(post.title)}</h3><p>${escapeHtml(post.body)}</p>
    <div class="community-post-context">${schoolAction}</div>
    <div class="community-author-row"><strong>${escapeHtml(post.display_name)}</strong><div>${canInvite ? `<button type="button" class="text-action" data-invite-recipient="${escapeHtml(post.author_id)}" data-recipient-name="${escapeHtml(post.display_name)}"><i data-lucide="mail-plus" aria-hidden="true"></i><span>邀請私訊</span></button>` : ""}${canDeletePost ? `<button type="button" class="icon-action" data-delete-post="${escapeHtml(post.id)}" aria-label="刪除這篇貼文"><i data-lucide="trash-2" aria-hidden="true"></i></button>` : ""}<button type="button" class="icon-action" data-report-resource="post" data-resource-id="${escapeHtml(post.id)}" aria-label="檢舉這篇貼文"><i data-lucide="flag" aria-hidden="true"></i></button></div></div>
    <details class="community-comments"><summary><span>${comments.length} 則回覆</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><div>${comments.map((comment) => `<article><div><strong>${escapeHtml(comment.display_name)}</strong>${state.account && comment.viewer_can_delete ? `<button type="button" class="icon-action" data-delete-comment="${escapeHtml(comment.id)}" data-post-id="${escapeHtml(post.id)}" aria-label="刪除這則留言"><i data-lucide="trash-2" aria-hidden="true"></i></button>` : ""}</div><p>${escapeHtml(comment.body)}</p></article>`).join("") || '<p class="no-answer">還沒有回覆。</p>'}${commentComposer}</div></details>
  </article>`;
}

function renderPublicChatMessage(message) {
  const canInvite = Boolean(message.author_id) && message.author_id !== state.anonymousIdentity?.id;
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
  const answerAction = state.account
    ? `<details class="answer-contribution"><summary><span>分享你的經驗回答</span><i data-lucide="message-square-reply" aria-hidden="true"></i></summary>
          <form class="community-form answer-form" data-question-id="${escapeHtml(question.id)}">
            <label><span>回答內容</span><textarea name="body" minlength="10" maxlength="1500" required placeholder="請提供具體年份、情境與實際經驗，避免只寫好或不好。"></textarea></label>
            <label><span>交換年份</span><input name="exchange_year" inputmode="numeric" maxlength="20" placeholder="例如 2025" /></label>
            ${renderCommunityIdentitySelector()}
            <label class="consent-check"><input name="accept_rules" type="checkbox" required /><span>我不會填寫 電子郵件、電話、社群帳號或他人個資，並同意內容先經審核。</span></label>
            <div class="community-form-footer"><div class="form-status" role="status"></div><button type="submit" class="primary-button"><span>送出回答</span><i data-lucide="send" aria-hidden="true"></i></button></div>
          </form>
        </details>`
    : '<button type="button" class="secondary-button" data-open-auth>登入後回答</button>';
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
        ${answerAction}
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
          ${renderCommunityIdentitySelector()}
          <label class="consent-check"><input name="accept_rules" type="checkbox" required /><span>我不會填寫 電子郵件、電話、社群帳號或他人個資，並同意問題先經審核。</span></label>
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
          ${renderCommunityIdentitySelector()}
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
    language: "語言學校板",
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
  document.body.dataset.globalFeed = state.globalCommunityFeed || "all";
}

function renderCommunityPageContext(isUniversityBoard = false) {
  const kicker = $("#community-home-kicker");
  const title = $("#community-hub-title");
  const description = $("#community-home-description");
  const school = activeHomeSchool();
  const languageBoard = !isUniversityBoard && state.globalCommunityFeed === "language";
  const publicBoard = !isUniversityBoard && state.globalCommunityFeed === "public";
  const following = !isUniversityBoard && state.globalCommunityFeed === "following";
  if (kicker) {
    kicker.textContent = isUniversityBoard
      ? `${school}板`
      : languageBoard
        ? "公共主題板"
        : publicBoard
          ? "跨校公共看板"
          : following
            ? "你的個人化動態"
            : "全台學生共同交流";
  }
  if (title) {
    title.textContent = isUniversityBoard
      ? `${school}討論板`
      : languageBoard
        ? LANGUAGE_SCHOOL_COMMUNITY_BOARD
        : publicBoard
          ? PUBLIC_COMMUNITY_BOARD
          : following
            ? "我的追蹤"
            : "學長姐心得";
  }
  if (description) {
    description.textContent = isUniversityBoard
      ? `校級看板限已驗證 Email 的會員查看、發文與留言，不限同校。這裡顯示${school}板的交換申請與校內討論。`
      : languageBoard
        ? "交流課程選擇、簽證、住宿與城市生活；目前不提供完整語言學校申請流程。"
        : publicBoard
          ? "跨校討論交換申請、簽證、住宿與海外生活。"
          : following
            ? "集中查看你已追蹤學校看板的最新文章。"
            : "每一段旅程，都有人同行。";
  }
  window.UniWayForum?.render();
}

function renderGlobalCommunityTopics() {
  const container = $("#global-community-topics");
  if (!container) return;
  container.innerHTML = COMMUNITY_TOPICS.map(([value, label]) => `
    <button type="button" data-global-community-topic="${escapeHtml(value)}" aria-pressed="${state.globalCommunityTopic === value}">${escapeHtml(label)}</button>`).join("");
}

async function loadCommunityBoards() {
  try {
    state.communityBoards = await fetchJson("/community/boards");
  } catch (_) {
    state.communityBoards = [];
  }
  populateGlobalCommunitySchools();
  window.UniWayCommunity?.syncDetail();
  return state.communityBoards;
}

function communityBoardIdForSchool(schoolName) {
  const normalized = normalize(schoolName);
  const board = state.communityBoards.find(
    (item) => item.school_name && normalize(item.school_name) === normalized
  );
  return board?.id || "";
}

function activeCommunityBoardAccess() {
  if (state.globalCommunityFeed === "public") {
    return state.communityBoards.find((board) => board.id === PUBLIC_COMMUNITY_BOARD_ID) || null;
  }
  if (state.globalCommunityFeed === "language") {
    return state.communityBoards.find((board) => board.id === LANGUAGE_SCHOOL_COMMUNITY_BOARD_ID) || null;
  }
  if (state.globalCommunityFeed === "cgu") {
    return state.communityBoards.find(
      (board) => board.id === communityBoardIdForSchool(CGU_COMMUNITY_BOARD)
    ) || null;
  }
  if (state.globalCommunityFeed === "university") {
    return state.communityBoards.find(
      (board) => board.id === communityBoardIdForSchool(activeHomeSchool())
    ) || null;
  }
  return null;
}

function populateGlobalCommunitySchools() {
  const select = $("#global-community-school");
  if (!select) return;
  const current = select.value || PUBLIC_COMMUNITY_BOARD_ID;
  const boards = state.communityBoards.length
    ? state.communityBoards
    : [
        { id: PUBLIC_COMMUNITY_BOARD_ID, label: PUBLIC_COMMUNITY_BOARD, can_post: Boolean(state.account?.email_verified) },
        { id: LANGUAGE_SCHOOL_COMMUNITY_BOARD_ID, label: LANGUAGE_SCHOOL_COMMUNITY_BOARD, can_post: Boolean(state.account?.email_verified) },
      ];
  select.innerHTML = boards.map((board) => {
    const reason = board.can_post ? "" : `（${escapeHtml(board.unavailable_reason || "目前不可發言")}）`;
    return `<option value="${escapeHtml(board.id)}" ${board.can_post ? "" : "disabled"}>${escapeHtml(board.label)}${reason}</option>`;
  }).join("");
  if ([...select.options].some((option) => option.value === current)) select.value = current;
  else select.value = [...select.options].find((option) => !option.disabled)?.value || "";
}

async function loadGlobalCommunity({ force = false } = {}) {
  return window.UniWayCommunity.load({ force });
}

function renderGlobalCommunityFeed() {
  return window.UniWayCommunity.load();
}

function initDiscussionReader() {
  window.UniWayCommunity.init({
    fetch: fetchJson, escape: escapeHtml, icons: initIcons, date: formatDate,
    topicLabel: communityTopicLabel, stageLabel: applicationStageLabel,
    announce, report: reportCommunityResource, deleteResource: deleteCommunityResource,
    beforeOpen: () => window.clearTimeout(state.globalCommunityTimer),
    context() {
      const route = state.globalCommunityFeed;
      const boards = route === "public" ? [PUBLIC_COMMUNITY_BOARD_ID]
        : route === "language" ? [LANGUAGE_SCHOOL_COMMUNITY_BOARD_ID]
        : route === "cgu" ? [CGU_COMMUNITY_BOARD]
        : route === "university" ? [activeHomeSchool()]
        : route === "following" ? [...followedBoardSet()] : [];
      return { key: `${state.account?.id || "guest"}:${Boolean(state.account?.email_verified)}:${route}:${boards.join(",")}`,
        permissionKey: `${state.account?.id || "guest"}:${state.communityBoards.map((board) => `${board.id}:${board.can_read}:${board.can_comment}`).join(",")}`,
        accountId: state.account?.id || "", boards,
        active: Boolean(globalFeedForHash() || ["#cgu-posts", "#university-posts"].includes(location.hash)),
        emptyFollowing: route === "following" && (!state.account || !boards.length),
        followingGuest: route === "following" && !state.account };
    },
    syncFilters(filters) {
      state.globalCommunityTopic = filters.topic;
      state.globalCommunityQuery = filters.q;
      $("#global-community-search").value = filters.q;
      renderGlobalCommunityTopics();
    },
    empty(filters, context) {
      if (context.followingGuest) return renderCommunityEmpty("登入後查看追蹤動態", "追蹤學校看板後，新文章會集中顯示在這裡。", "empty", '<button type="button" class="secondary-button" data-open-auth>登入</button>');
      if (context.emptyFollowing) return renderCommunityEmpty("還沒有追蹤任何看板", "先追蹤感興趣的學校看板，再回來查看新文章。");
      if (filters.saved) return renderCommunityEmpty("沒有符合條件的收藏文章", state.account ? "收藏會同步到登入帳號。可先清除搜尋條件，或到文章列表收藏想再讀的經驗。" : "收藏會保存在此瀏覽器。可先清除搜尋條件，或到文章列表收藏想再讀的經驗。");
      if (filters.q || filters.topic) return renderCommunityEmpty("找不到符合條件的文章", "試試國家、學校或申請年度，或切換其他主題。");
      if (filters.sort === "unanswered") return renderCommunityEmpty("目前沒有待回覆的問題", "有新的申請問題時，就能在這裡一起幫忙。");
      return `<div class="discussion-welcome" role="status">
        <div class="discussion-welcome-art" aria-hidden="true"><span class="discussion-art-orbit"></span><span class="discussion-art-globe"><i data-lucide="globe-2"></i></span><span class="discussion-art-bubble"><i data-lucide="messages-square"></i></span><span class="discussion-art-spark"><i data-lucide="sparkles"></i></span></div>
        <span class="discussion-welcome-kicker">下一站，從一場對話開始</span><h3>來分享第一篇交換經驗</h3>
        <p>正在準備申請，還是已經走過一趟旅程？<br />你的問題與經驗，都值得被聽見。</p>
        <button type="button" class="primary-button" data-open-global-community-composer><i data-lucide="square-pen" aria-hidden="true"></i>發表文章</button>
        <small>寫下國家、年份與目前階段，讓交流更有方向。</small>
      </div>`;
    },
    composer(post) {
      const board = communityBoardAccessForPost(post);
      if (!state.account) return '<button type="button" class="secondary-button" data-open-auth>登入後回覆</button>';
      if (!board?.can_comment) return `<div class="community-access-note"><p>${escapeHtml(board?.unavailable_reason || "請先完成驗證，才能回覆。")}</p><button type="button" class="secondary-button" data-open-verification>查看驗證狀態</button></div>`;
      return `<form class="community-inline-composer post-comment-form" data-post-id="${escapeHtml(post.id)}"><input type="hidden" name="parent_id" value="" /><div data-discussion-reply-target hidden><span></span><button type="button" class="text-action" data-discussion-reply-cancel>改為回覆文章</button></div><label for="discussion-reply-body">分享實際經驗或補充問題</label><textarea id="discussion-reply-body" name="body" minlength="2" maxlength="800" required placeholder="例如：我在 2026 秋季申請日本交換時…"></textarea>${renderCommunityIdentitySelector()}<small data-discussion-draft-status role="status">草稿會保存在此分頁</small><button type="submit" class="primary-button">發布回覆</button><div class="form-status" role="status"></div></form>`;
    },
    commentGate() {
      if (!state.account) openAuthDialog();
      else openProfileDialog();
    },
    submitReply: (form) => handleCommunityFormSubmit(form, submitPostCommentForm, "回覆已發布。"),
  });
  window.UniWayModeration.init({ fetch: fetchJson, escape: escapeHtml, announce,
    accountId: () => state.account?.id || "", refreshed: () => window.UniWayCommunity.refresh() });
}

function openGlobalCommunityComposer() {
  if (!state.account) {
    openAuthDialog("register");
    return;
  }
  if (!state.account.email_verified) {
    openProfileDialog();
    announce("請先完成 電子郵件 驗證，再參與公共社群。", "error");
    return;
  }
  const activeBoard = activeCommunityBoardAccess();
  if (activeBoard && !activeBoard.can_post) {
    openProfileDialog();
    announce(activeBoard.unavailable_reason || "目前不能在這個看板發文。", "error");
    return;
  }
  const form = $("#global-community-form");
  form.hidden = false;
  const boardSelect = form.elements.board_id;
  if (["cgu", "university"].includes(state.globalCommunityFeed) || document.body.classList.contains("cgu-community-mode")) {
    boardSelect.value = communityBoardIdForSchool(
      state.globalCommunityFeed === "cgu" ? CGU_COMMUNITY_BOARD : activeHomeSchool()
    );
  } else if (state.globalCommunityFeed === "public") {
    boardSelect.value = PUBLIC_COMMUNITY_BOARD_ID;
  } else if (state.globalCommunityFeed === "language") {
    boardSelect.value = LANGUAGE_SCHOOL_COMMUNITY_BOARD_ID;
  }
  window.UniWayCommunity.restorePostDraft();
  resetCommunityIdentityPreviews(form);
  form.scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "center" });
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
    const created = await submitCommunityJson("/community/posts", {
      board_id: values.get("board_id"),
      post_type: values.get("post_type"),
      topic: values.get("topic"),
      country: values.get("country") || null,
      academic_year: values.get("academic_year") || null,
      application_stage: values.get("application_stage") || null,
      title: values.get("title"),
      body: values.get("body"),
      identity_mode: values.get("identity_mode") || "anonymous",
    });
    form.reset();
    resetCommunityIdentityPreviews(form);
    form.hidden = true;
    status.textContent = "";
    state.globalCommunityTopic = "";
    state.globalCommunityQuery = "";
    $("#global-community-search").value = "";
    window.UniWayCommunity.clearDraft("post");
    window.UniWayCommunity.updateFilters({ q: "", topic: "" });
    await loadGlobalCommunity({ force: true });
    announce(
      created.status === "pending" ? "文章已送出，通過審核後公開。" : "文章已發布",
      "success"
    );
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

async function deleteCommunityResource(url, confirmation) {
  if (!window.confirm(confirmation)) return false;
  try {
    await ensureAnonymousIdentity();
    await submitCommunityJson(url, {}, "DELETE");
    announce("內容已刪除", "success");
    return true;
  } catch (error) {
    announce(error.message, "error", true);
    return false;
  }
}

async function submitJson(url, payload) {
  return fetchJson(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

const pendingCommunityMutationIds = new Map();

function canonicalCommunityMutationValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => {
      const canonical = canonicalCommunityMutationValue(item);
      return canonical === undefined ? null : canonical;
    });
  }
  if (value && typeof value === "object") {
    return Object.keys(value)
      .sort()
      .reduce((result, key) => {
        const canonical = canonicalCommunityMutationValue(value[key]);
        if (canonical !== undefined) result[key] = canonical;
        return result;
      }, {});
  }
  if (typeof value === "number" && !Number.isFinite(value)) return null;
  if (["undefined", "function", "symbol"].includes(typeof value)) return undefined;
  return value;
}

function canonicalCommunityMutationPayload(payload) {
  return JSON.stringify(canonicalCommunityMutationValue(payload));
}

function communityMutationSupportsIdempotency(url, method) {
  if (method === "DELETE") return /^\/community\/posts\/[^/]+(?:\/comments\/[^/]+)?$/.test(url);
  if (method !== "POST") return false;
  return url === "/community/posts"
    || /^\/community\/posts\/[^/]+\/comments$/.test(url)
    || url === "/community/questions"
    || /^\/community\/questions\/[^/]+\/answers$/.test(url)
    || url === "/community/chat"
    || url === "/experience-submissions"
    || url === "/community/conversations"
    || /^\/community\/conversations\/[^/]+\/accept$/.test(url)
    || /^\/community\/conversations\/[^/]+\/messages$/.test(url)
    || url === "/community/blocks"
    || url === "/community/reports";
}

function createCommunityMutationId() {
  return window.crypto?.randomUUID?.()
    || `community-${Date.now().toString(36)}-${Math.random().toString(16).slice(2)}-${Math.random().toString(16).slice(2)}`;
}

async function submitCommunityJson(url, payload, method = "POST") {
  const normalizedMethod = String(method || "POST").toUpperCase();
  if (!communityMutationSupportsIdempotency(url, normalizedMethod)) {
    return fetchCommunityAuth(url, { method, body: JSON.stringify(payload) });
  }
  const body = canonicalCommunityMutationPayload(payload);

  // Keep ambiguous retries account-bound so another signed-in user never reuses the key.
  const mutationKey = `${String(state.account?.id || "")}\n${normalizedMethod}\n${url}\n${body}`;
  const mutationId = pendingCommunityMutationIds.get(mutationKey)
    || createCommunityMutationId();
  pendingCommunityMutationIds.set(mutationKey, mutationId);
  try {
    const result = await fetchCommunityAuth(url, {
      method: normalizedMethod,
      headers: { "X-Community-Mutation-ID": mutationId },
      body,
    });
    pendingCommunityMutationIds.delete(mutationKey);
    return result;
  } catch (error) {
    // Network failures and 5xx responses are ambiguous; retain the key for a safe retry.
    if (error?.status && error.status < 500) {
      pendingCommunityMutationIds.delete(mutationKey);
    }
    throw error;
  }
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
  await ensureAnonymousIdentity();
  return submitCommunityJson("/community/posts", {
    board_id: PUBLIC_COMMUNITY_BOARD_ID,
    post_type: values.get("post_type"),
    title: values.get("title"),
    body: values.get("body"),
    identity_mode: values.get("identity_mode") || "anonymous",
  });
}

async function submitPostCommentForm(form) {
  const values = new FormData(form);
  await ensureAnonymousIdentity();
  return submitCommunityJson(`/community/posts/${encodeURIComponent(form.dataset.postId)}/comments`, {
    body: values.get("body"),
    identity_mode: values.get("identity_mode") || "anonymous",
    parent_id: values.get("parent_id") || null,
  });
}

async function submitPublicChatForm(form) {
  const values = new FormData(form);
  await ensureAnonymousIdentity();
  return submitCommunityJson("/community/chat", {
    school_name: state.activeSchool,
    body: values.get("body"),
    identity_mode: values.get("identity_mode") || "anonymous",
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
  await ensureAnonymousIdentity();
  return submitCommunityJson("/community/questions", {
    school_name: state.activeSchool,
    home_university: activeHomeSchool(),
    topic: values.get("topic"),
    title: values.get("title"),
    body: values.get("body"),
    identity_mode: values.get("identity_mode") || "anonymous",
    accept_rules: values.get("accept_rules") === "on",
  });
}

async function submitAnswerForm(form) {
  const values = new FormData(form);
  await ensureAnonymousIdentity();
  return submitCommunityJson(`/community/questions/${encodeURIComponent(form.dataset.questionId)}/answers`, {
    body: values.get("body"),
    identity_mode: values.get("identity_mode") || "anonymous",
    exchange_year: values.get("exchange_year") || null,
    accept_rules: values.get("accept_rules") === "on",
  });
}

async function submitExperienceForm(form) {
  const values = new FormData(form);
  await ensureAnonymousIdentity();
  return submitCommunityJson("/experience-submissions", {
    school_name: state.activeSchool,
    home_university: activeHomeSchool(),
    title: values.get("title"),
    summary: values.get("summary"),
    exchange_year: values.get("exchange_year"),
    themes: values.getAll("themes"),
    source_url: values.get("source_url") || null,
    identity_mode: values.get("identity_mode") || "anonymous",
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
    const result = await submitter(form);
    form.reset();
    resetCommunityIdentityPreviews(form);
    status.className = "form-status is-success";
    status.textContent = result?.status === "pending" && result?.identity_mode
      ? "內容已送出，通過審核後公開。"
      : successMessage;
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

function applicationPeriodMeta(item) {
  const status = item?.status || "needs_confirmation";
  const statusMap = {
    upcoming: { label: "尚未開放", tone: "upcoming" },
    open: { label: "申請中", tone: "open" },
    closed: { label: "本梯次已截止", tone: "closed" },
    action_required: { label: "限符合身分者處理", tone: "action" },
    reference_only: { label: "原則時程參考", tone: "reference" },
    needs_confirmation: { label: "適用期間待確認", tone: "pending" },
  };
  const scopeMap = {
    home_application: "校內申請",
    post_selection: "初審後續",
    recurring_reference: "歷年原則",
    short_course: "短期課程",
  };
  const audienceMap = {
    all_students: "所有申請學生",
    applicants: "已送出申請者",
    selected_applicants: "校內初審通過者",
    conditional_applicants: "初審名單標記＊者",
  };
  const dateStatusMap = {
    verified_exact: "官方精確日期",
    reference_only: "只有參考時程",
    needs_confirmation: "日期待確認",
    not_applicable: "不適用日期",
  };
  const deadlineLabel = item?.scope === "post_selection"
    ? "條件式補件期限"
    : item?.scope === "home_application"
    ? "校內申請截止"
    : "時程";
  return {
    ...(statusMap[status] || statusMap.needs_confirmation),
    scopeLabel: scopeMap[item?.scope] || "申請資訊",
    audienceLabel: audienceMap[item?.audience] || "請查看適用對象",
    dateStatusLabel: dateStatusMap[item?.date_status] || "日期待確認",
    deadlineLabel,
  };
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
      const meta = applicationPeriodMeta(item);
      const deadlineText = item.deadline_at
        ? `${meta.deadlineLabel}：${formatDate(item.deadline_at)}`
        : item.date_status === "reference_only"
        ? "沒有可安全套用到下一梯次的精確日期"
        : details[0] || "尚無可驗證的精確日期";
      return `
        <details class="deadline-card" data-period-status="${escapeHtml(meta.tone)}">
          <summary>
            <span>
              <span class="deadline-card-labels"><span class="deadline-scope-pill">${escapeHtml(meta.scopeLabel)}</span><span class="deadline-status-pill ${escapeHtml(meta.tone)}">${escapeHtml(meta.label)}</span></span>
              <strong>${escapeHtml(item.title)}</strong>
              <span class="deadline-date">${escapeHtml(truncate(deadlineText, 88))}</span>
            </span>
            <i data-lucide="chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="deadline-card-content">
            <div class="deadline-status-note" role="note"><i data-lucide="badge-alert" aria-hidden="true"></i><p>${escapeHtml(item.status_note || "請開啟官方來源確認最新狀態。")}</p></div>
            <dl class="deadline-period-meta">
              <div><dt>適用學年度／梯次</dt><dd>${escapeHtml([item.academic_year ? `${item.academic_year} 學年度` : "年度待確認", item.application_round || "梯次待確認"].join("／"))}</dd></div>
              <div><dt>適用對象</dt><dd>${escapeHtml(meta.audienceLabel)}</dd></div>
              <div><dt>日期性質</dt><dd>${escapeHtml(meta.dateStatusLabel)}</dd></div>
              <div><dt>最後查核</dt><dd>${escapeHtml(item.checked_at ? formatDateOnly(item.checked_at) : "待查核")}</dd></div>
            </dl>
            ${details.length ? `<ul class="deadline-details">${details.map((detail) => `<li>${highlightHtml(detail)}</li>`).join("")}</ul>` : ""}
            ${item.deadline_note ? `<p class="deadline-reminder-note"><i data-lucide="${item.reminder_eligible ? "bell-ring" : "bell-off"}" aria-hidden="true"></i><span>${escapeHtml(item.deadline_note)}</span></p>` : ""}
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
  if (minimum != null && profile.academicScore != null && profile.academicScore < minimum && /70\s*分|75\s*分|歷年學業成績|領航者|學海/.test(text)) {
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

function entitlementFeatureEnabled(feature) {
  return Boolean(state.entitlements?.features?.find((item) => item.feature === feature)?.enabled);
}

function formatVaultBytes(value) {
  const bytes = Number(value) || 0;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function vaultCategoryLabel(value) {
  return {
    application_form: "申請表",
    generated_packet: "系統列印包",
    passport: "護照",
    transcript: "成績單",
    student_id: "學生證",
    financial_proof: "財力證明",
    recommendation: "推薦信",
    study_plan: "讀書計畫",
    other: "其他",
  }[value] || "其他";
}

function vaultPurposeLabel(value) {
  return {
    application_preparation: "準備與核對申請",
    cross_device_access: "跨裝置存取",
    generated_packet_backup: "備份列印包",
  }[value] || "指定用途";
}

function findVaultVersion(versionId) {
  for (const documentItem of state.privateVault.items || []) {
    const version = (documentItem.versions || []).find((item) => item.id === versionId);
    if (version) return version;
  }
  return null;
}

function renderGeneratedVaultCandidate() {
  const container = $("#generated-vault-candidate");
  if (!container) return;
  const candidate = window.UniWayDocumentWorkbench?.vaultCandidate();
  container.hidden = !candidate;
  if (!candidate) {
    container.innerHTML = "";
    return;
  }
  container.innerHTML = `
    <span><i data-lucide="file-check-2" aria-hidden="true"></i></span>
    <div><strong>剛產生的 PDF 仍只在這個瀏覽器中</strong><small>${escapeHtml(candidate.fileName)} · 尚未上傳或保存</small></div>
    <button type="button" class="secondary-button" data-use-generated-vault>${state.useGeneratedVaultCandidate ? "已帶入保存表單" : "帶入保存表單"}</button>`;
}

function renderPrivateVault() {
  const gate = $("#private-vault-gate");
  const content = $("#private-vault-content");
  const list = $("#private-vault-list");
  const usage = $("#private-vault-usage");
  if (!gate || !content || !list || !usage) return;
  renderGeneratedVaultCandidate();
  if (!state.account) {
    usage.textContent = "登入後使用";
    content.hidden = true;
    gate.hidden = false;
    gate.innerHTML = '<span><i data-lucide="log-in" aria-hidden="true"></i></span><div><strong>瀏覽官方文件不需要登入</strong><small>只有要加密保存自己的文件時才登入；登入本身不代表同意上傳。</small></div><button type="button" class="primary-button" data-private-vault-login>登入後使用</button>';
    initIcons();
    return;
  }
  if (!state.entitlements) {
    usage.textContent = "確認權限中";
    content.hidden = true;
    gate.hidden = false;
    gate.innerHTML = '<div class="skeleton skeleton-card"></div>';
    return;
  }
  if (!entitlementFeatureEnabled("encrypted_document_vault")) {
    usage.textContent = "進階功能";
    content.hidden = true;
    gate.hidden = false;
    gate.innerHTML = '<span><i data-lucide="lock-keyhole" aria-hidden="true"></i></span><div><strong>目前方案尚未開放私人文件庫</strong><small>官方資料、搜尋與比較仍可免費使用。</small></div>';
    initIcons();
    return;
  }
  gate.hidden = true;
  gate.innerHTML = "";
  content.hidden = false;
  usage.textContent = `${state.privateVault.items?.length || 0} 份 · ${formatVaultBytes(state.privateVault.total_bytes)}`;
  if (state.privateVaultLoading) {
    list.innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
    return;
  }
  if (state.privateVaultError) {
    list.innerHTML = `<div class="advisor-error"><strong>無法取得私人文件庫</strong><span>${escapeHtml(state.privateVaultError)}</span><button type="button" class="secondary-button" data-private-vault-retry>重新載入</button></div>`;
    return;
  }
  const items = state.privateVault.items || [];
  if (!items.length) {
    list.innerHTML = '<div class="private-vault-empty"><i data-lucide="folder-lock" aria-hidden="true"></i><span><strong>私人文件庫目前是空的</strong><small>只有你逐檔同意的文件才會出現在這裡。</small></span></div>';
    initIcons();
    return;
  }
  list.innerHTML = items.map((item) => `
    <article class="private-vault-document">
      <header><span><i data-lucide="file-lock-2" aria-hidden="true"></i></span><div><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(vaultCategoryLabel(item.category))} · ${item.versions.length} 個加密版本</small></div><div class="private-vault-document-actions"><button type="button" class="text-button" data-private-vault-new-version="${escapeHtml(item.id)}">新增版本</button><button type="button" class="icon-button danger" data-private-vault-delete-document="${escapeHtml(item.id)}" aria-label="永久刪除 ${escapeHtml(item.label)}"><i data-lucide="trash-2" aria-hidden="true"></i></button></div></header>
      <div class="private-vault-versions">${(item.versions || []).map((version) => `
        <div class="private-vault-version"><span class="private-vault-version-number">v${version.version_number}</span><div><strong>${escapeHtml(version.file_name)}</strong><small>${formatVaultBytes(version.size_bytes)} · ${escapeHtml(vaultPurposeLabel(version.purpose))} · 保存至 ${escapeHtml(formatDate(version.expires_at).slice(0, 10))}</small></div><div><button type="button" class="icon-button" data-private-vault-download="${escapeHtml(version.id)}" aria-label="下載 ${escapeHtml(version.file_name)}"><i data-lucide="download" aria-hidden="true"></i></button><button type="button" class="icon-button danger" data-private-vault-delete-version="${escapeHtml(version.id)}" data-private-vault-document="${escapeHtml(item.id)}" aria-label="永久刪除 ${escapeHtml(version.file_name)}"><i data-lucide="file-x-2" aria-hidden="true"></i></button></div></div>`).join("")}</div>
    </article>`).join("");
  initIcons();
}

async function loadPrivateVault({ quiet = true } = {}) {
  const requestId = ++state.privateVaultRequestId;
  const requestContext = captureAuthenticatedRequestContext();
  const current = () => requestId === state.privateVaultRequestId && authenticatedRequestContextIsCurrent(requestContext);
  if (!state.account || !entitlementFeatureEnabled("encrypted_document_vault")) {
    state.privateVault = { items: [], total_bytes: 0, max_file_bytes: 20 * 1024 * 1024 };
    renderPrivateVault();
    return;
  }
  state.privateVaultLoading = true;
  state.privateVaultError = "";
  renderPrivateVault();
  try {
    const result = await fetchJson("/account/vault/documents");
    if (!current()) return;
    state.privateVault = result;
  } catch (error) {
    if (error.staleSession || !current()) return;
    state.privateVaultError = error.message;
    if (!quiet) announce(error.message, "error", true);
  } finally {
    if (current()) { state.privateVaultLoading = false; renderPrivateVault(); }
  }
}

function resetPrivateVaultForm({ keepCandidate = true } = {}) {
  const form = $("#private-vault-form");
  if (!form) return;
  form.reset();
  state.privateVaultFormRevision += 1;
  form.querySelector('button[type="submit"]').disabled = false;
  state.privateVaultEditingDocumentId = "";
  state.useGeneratedVaultCandidate = false;
  if (!keepCandidate) state.generatedVaultCandidate = null;
  $("#private-vault-label").disabled = false;
  $("#private-vault-category").disabled = false;
  $("#private-vault-form-title").textContent = "保存新文件";
  $("#private-vault-form-note").textContent = "選擇檔案後仍須勾選本次保存同意。";
  $("#private-vault-cancel-version").hidden = true;
  $("#private-vault-file-name").textContent = "選擇私人文件";
  $("#private-vault-file-meta").textContent = "PDF、DOCX、TXT、JPG、PNG 或 WebP，20 MB 以內";
  $("#private-vault-form-status").textContent = "";
  renderGeneratedVaultCandidate();
}

function beginPrivateVaultVersion(documentId) {
  const item = (state.privateVault.items || []).find((row) => row.id === documentId);
  if (!item) return;
  resetPrivateVaultForm();
  state.privateVaultEditingDocumentId = documentId;
  const label = $("#private-vault-label");
  const category = $("#private-vault-category");
  label.value = item.label;
  label.disabled = true;
  category.value = item.category;
  category.disabled = true;
  $("#private-vault-form-title").textContent = `新增「${item.label}」版本`;
  $("#private-vault-form-note").textContent = "新版本有獨立保存期限，也必須再次明確同意。";
  $("#private-vault-cancel-version").hidden = false;
  $("#private-vault-form").scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "center" });
  $("#private-vault-file").focus();
}

function useGeneratedVaultCandidate() {
  const candidate = state.generatedVaultCandidate;
  if (!window.UniWayDocumentWorkbench?.candidateCurrent(candidate)) return;
  if (!state.account) {
    openAuthDialog();
    return;
  }
  resetPrivateVaultForm();
  state.useGeneratedVaultCandidate = true;
  $("#private-vault-label").value = candidate.label;
  $("#private-vault-category").value = candidate.category;
  $("#private-vault-form").elements.purpose.value = "generated_packet_backup";
  $("#private-vault-file-name").textContent = candidate.fileName;
  $("#private-vault-file-meta").textContent = `${formatVaultBytes(candidate.blob.size)} · 尚未保存`;
  renderGeneratedVaultCandidate();
  $("#private-vault-form").scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "center" });
}

async function submitPrivateVault(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = $("#private-vault-form-status");
  const button = form.querySelector('button[type="submit"]');
  const selected = $("#private-vault-file").files?.[0];
  const candidate = state.useGeneratedVaultCandidate ? state.generatedVaultCandidate : null;
  if (candidate && !window.UniWayDocumentWorkbench?.candidateCurrent(candidate)) {
    resetPrivateVaultForm();
    status.textContent = "文件內容或申請背景已變更，請重新核對並下載 PDF，再選擇保存。";
    return;
  }
  const source = candidate?.blob || selected;
  const fileName = candidate?.fileName || selected?.name;
  if (!source || !fileName) {
    status.textContent = "請先選擇要保存的檔案。";
    return;
  }
  if (!form.elements.consent.checked) {
    status.textContent = "必須勾選這一次的逐檔保存同意。";
    form.elements.consent.focus();
    return;
  }
  const payload = new FormData();
  payload.append("file", source, fileName);
  payload.append("purpose", form.elements.purpose.value);
  payload.append("retention_days", form.elements.retention_days.value);
  payload.append("consent", "true");
  let endpoint = "/account/vault/documents";
  if (state.privateVaultEditingDocumentId) {
    endpoint += `/${encodeURIComponent(state.privateVaultEditingDocumentId)}/versions`;
  } else {
    payload.append("label", form.elements.label.value.trim());
    payload.append("category", form.elements.category.value);
  }
  button.disabled = true;
  status.textContent = "正在加密並保存…";
  const requestContext = captureAuthenticatedRequestContext();
  const formRevision = state.privateVaultFormRevision;
  const requestedHome = state.homeSchool;
  const current = () => authenticatedRequestContextIsCurrent(requestContext)
    && requestedHome === state.homeSchool && formRevision === state.privateVaultFormRevision;
  try {
    await fetchJson(endpoint, { method: "POST", body: payload });
    if (!current()) return;
    const usedGenerated = Boolean(candidate);
    resetPrivateVaultForm({ keepCandidate: !usedGenerated });
    await loadPrivateVault({ quiet: false });
    if (!authenticatedRequestContextIsCurrent(requestContext) || requestedHome !== state.homeSchool) return;
    announce("文件已逐檔同意並加密保存", "success");
  } catch (error) {
    if (!current()) return;
    status.textContent = error.message;
  } finally {
    if (current()) { button.disabled = false; initIcons(); }
  }
}

async function downloadPrivateVaultVersion(versionId, button) {
  const version = findVaultVersion(versionId);
  if (!version) return;
  const requestContext = captureAuthenticatedRequestContext();
  button.disabled = true;
  try {
    const grant = await fetchJson(`/account/vault/versions/${encodeURIComponent(versionId)}/download-grant`, { method: "POST" });
    const response = await fetch(grant.download_url, {
      method: "POST",
      cache: "no-store",
      credentials: "same-origin",
      headers: { Accept: "application/octet-stream", "X-Vault-Download-Token": grant.token },
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `下載失敗（${response.status}）`);
    }
    const blob = await response.blob();
    assertAuthenticatedRequestCurrent(requestContext);
    const disposition = response.headers.get("Content-Disposition") || "";
    const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
    const fileName = encodedName ? decodeURIComponent(encodedName) : version.file_name;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1500);
    announce("私人文件已下載", "success");
  } catch (error) {
    if (error.staleSession) return;
    announce(error.message, "error", true);
  } finally {
    button.disabled = false;
  }
}

async function deletePrivateVaultDocument(documentId) {
  const item = (state.privateVault.items || []).find((row) => row.id === documentId);
  if (!item || !window.confirm(`永久刪除「${item.label}」及所有版本？此操作無法復原。`)) return;
  try {
    await fetchJson(`/account/vault/documents/${encodeURIComponent(documentId)}`, { method: "DELETE" });
    if (state.privateVaultEditingDocumentId === documentId) resetPrivateVaultForm();
    await loadPrivateVault({ quiet: false });
    announce("文件與所有加密版本已永久刪除", "success");
  } catch (error) {
    announce(error.message, "error", true);
  }
}

async function deletePrivateVaultVersion(documentId, versionId) {
  const version = findVaultVersion(versionId);
  if (!version || !window.confirm(`永久刪除 ${version.file_name}（v${version.version_number}）？此操作無法復原。`)) return;
  try {
    await fetchJson(`/account/vault/documents/${encodeURIComponent(documentId)}/versions/${encodeURIComponent(versionId)}`, { method: "DELETE" });
    await loadPrivateVault({ quiet: false });
    announce("加密版本已永久刪除", "success");
  } catch (error) {
    announce(error.message, "error", true);
  }
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

async function loadApplicationPeriodOptions() {
  if (!canAccessPartnerCatalog()) return;
  const context = captureAuthenticatedRequestContext();
  const requestId = ++state.applicationPeriodRequestId;
  const homeSchool = activeHomeSchool();
  const hint = $("#application-period-hint");
  hint.textContent = "正在讀取本校流程的年度與梯次…";
  try {
    const result = await fetchJson(`/application-period-options?home_school=${encodeURIComponent(homeSchool)}`);
    if (!authenticatedRequestContextIsCurrent(context) || homeSchool !== activeHomeSchool() || requestId !== state.applicationPeriodRequestId) return;
    state.applicationPeriodOptions = result;
    renderApplicationPeriodOptions();
    $("#application-period-retry").hidden = true;
  } catch (error) {
    if (!authenticatedRequestContextIsCurrent(context) || homeSchool !== activeHomeSchool() || requestId !== state.applicationPeriodRequestId) return;
    hint.textContent = "未能讀取年度與梯次來源。已填內容保留；請重試後核對當期資料。";
    $("#application-period-retry").hidden = false;
  }
}

function renderApplicationPeriodOptions() {
  const yearField = $("#eligibility-academic-year");
  const roundField = $("#eligibility-application-round");
  if (!yearField || !roundField) return;
  const selectedYear = yearField.value;
  const selectedRound = roundField.value;
  const data = canAccessPartnerCatalog() && state.applicationPeriodOptions?.home_university === activeHomeSchool() ? state.applicationPeriodOptions : null;
  const periods = data?.periods || [];
  // Retain future years and legacy drafts, but never present them as published periods.
  const currentYear = new Date().getFullYear() - 1911;
  const defaultYears = activeHomeSchool() === "淡江大學"
    ? window.UniWayTKU.applicationYears(periods)
    : [String(currentYear), String(currentYear+1), String(currentYear+2)];
  const years = [...new Set([...defaultYears,...periods.map(row=>row.academic_year),selectedYear].filter(Boolean))];
  yearField.innerHTML = '<option value="">請選擇</option>' + years.sort().reverse().map(year=>
    `<option value="${escapeHtml(year)}">${escapeHtml(year)} 學年度${periods.some(row=>row.academic_year === year) ? "" : "（流程資料待確認）"}</option>`).join("");
  yearField.value = selectedYear;
  const relevant = periods.filter(row=>row.academic_year === selectedYear);
  const defaultRounds = activeHomeSchool() === "淡江大學"
    ? ["其他／尚未核實"]
    : ["第一梯次","第二梯次","其他／尚未公告"];
  const rounds = [...new Set([...relevant.map(row=>row.application_round),...periods.map(row=>row.application_round),
    ...defaultRounds,selectedRound].filter(Boolean))];
  roundField.innerHTML = '<option value="">請選擇</option>' + rounds.map(round=>{
    const row = relevant.find(item=>item.application_round === round);
    const note = row ? row.needs_confirmation ? "（適用性待確認）" : "" : "（此年度流程待確認）";
    return `<option value="${escapeHtml(round)}">${escapeHtml(round)}${note}</option>`;
  }).join("");
  roundField.value = selectedRound;
  const row = relevant.find(item=>item.application_round === selectedRound);
  $("#application-period-hint").textContent = !data
    ? "年度與梯次須與母校公告一致；資料載入後可核對各年度的流程資料。"
    : !selectedYear ? "先選學年度；系統會列出該年度已有資料的梯次。其他選項均標示待確認。"
    : row ? `${selectedYear} 學年度 · ${selectedRound}：${row.school_count} 所學校有流程資料${row.needs_confirmation ? "，適用性仍須向校方確認" : ""}。不同梯次不互相套用，當期開放與期限以來源為準。`
    : `${selectedYear} 學年度${selectedRound ? ` · ${selectedRound}` : ""} 尚無對應流程資料；不會沿用其他年度或梯次的期限。請核對母校當期公告。`;
  const source = $("#application-period-source");
  const url = row?.source_urls?.find(url=>/^https?:\/\//i.test(url));
  source.hidden = !url;
  if (url) source.href = url;
  else source.removeAttribute("href");
  const planningYear = $("#planning-academic-year");
  const planningRound = $("#planning-application-round");
  $("#planning-year-options").innerHTML = [...new Set(periods.map(row=>row.academic_year))].map(year=>`<option value="${escapeHtml(year)}"></option>`).join("");
  const planningPeriods = periods.filter(row=>row.academic_year === planningYear.value.trim());
  $("#planning-round-options").innerHTML = planningPeriods.map(row=>`<option value="${escapeHtml(row.application_round)}"></option>`).join("");
  const matches = planningPeriods.some(row=>row.application_round === planningRound.value.trim());
  $("#planning-period-hint").textContent = planningYear.value && !matches
    ? "這組年度／梯次尚無對應流程；系統不會借用其他年度期限。可先建立自己的準備任務。"
    : "年度與梯次建議取自本校已發布流程；準備任務與官方截止日分開保存。";
}

function renderEligibilityOptions({ preserveDraft = false } = {}) {
  if (!state.dashboard) return;
  const form = $("#advisor-form");
  const owner = JSON.stringify([state.account?.id || "", activeHomeSchool()]);
  const maximum = state.dashboard.maximum_preferences || 5;
  const gpaField = $("#advisor-academic-gpa");
  renderAcademicFields();
  const selects = [1,2,3,4,5].map(rank=>$(`#eligibility-preference-${rank}`));
  selects.forEach((field,index)=>{field.closest?.("label") && (field.closest("label").hidden=index>=maximum);if(index>=maximum)field.value="";});
  const draft = form.dataset.draftOwner === owner ? selects.map(field=>field.value) : null;
  const openSchools = state.dashboard.partner_universities
    .filter(item=>!partnerAvailabilityMeta(item).blocked).map(item=>item.school_name);
  const preferences = draft || [...state.applications];
  selects.slice(0,maximum).forEach((field,index)=>fillSelect(`#${field.id}`,openSchools,index ? `不設定第 ${index+1} 志願` : "請選擇第一志願",preferences[index] || ""));
}

function restoreEligibilityForm({ preserveDraft = false } = {}) {
  const form = $("#advisor-form");
  if (form.dataset.draftOwner === JSON.stringify([state.account?.id || "", activeHomeSchool()])) return;
  const profile = state.eligibilityProfile;
  if (profile) {
    // A saved custom period remains selectable even before metadata arrives.
    [[$("#eligibility-academic-year"),profile.academicYear],[$("#eligibility-application-round"),profile.applicationRound]].forEach(([field,value])=>{
      if (value && ![...field.options].some(option=>option.value === value)) field.add(new Option(value,value));
    });
    $("#eligibility-academic-year").value = profile.academicYear || "";
    $("#eligibility-application-round").value = profile.applicationRound || "";
    $("#clear-saved-eligibility").hidden = false;
  } else {
    $("#eligibility-academic-year").value = "";
    $("#eligibility-application-round").value = "";
    $("#clear-saved-eligibility").hidden = true;
  }
  renderApplicationPeriodOptions();
}

function conditionsDraftKey() {
  return JSON.stringify([...$("#advisor-form").querySelectorAll("input, select, textarea")]
    .map(field=>[field.id,field.value,field.type === "checkbox" && field.checked]));
}

function applicationPlanStatusMeta(status) {
  return {
    eligible: { label: "目前條件通過", tone: "pass" },
    needs_confirmation: { label: "需要校方確認", tone: "review" },
    ineligible: { label: "目前有條件不符", tone: "fail" },
    unavailable: { label: "本期未開放", tone: "fail" },
  }[status] || { label: "待確認", tone: "review" };
}

function renderPersonalApplicationPlan(plan) {
  const result = $("#eligibility-result");
  if (!result || !plan) return;
  const hasBlockingChoice = plan.choices.some((choice) => ["ineligible", "unavailable"].includes(choice.status));
  const hasConfirmation = plan.choices.some((choice) => choice.status === "needs_confirmation");
  result.className = `eligibility-result ${hasBlockingChoice || hasConfirmation ? "is-warning" : "is-pass"}`;
  result.innerHTML = `
    <div class="application-plan-result-heading">
      <span><i data-lucide="route" aria-hidden="true"></i></span>
      <div><h3>你的 ${escapeHtml(plan.home_school)} 申請清單</h3><p>${escapeHtml(plan.disclaimer)}</p></div>
    </div>
    <div class="application-plan-choices">${plan.choices.map((choice) => {
      const meta = applicationPlanStatusMeta(choice.status);
      return `
        <article class="application-plan-choice ${meta.tone}">
          <header><span class="application-plan-rank">第 ${choice.rank} 志願</span><div><strong>${escapeHtml(choice.school_name)}</strong><small>${escapeHtml(choice.country || "未標示國家")}</small></div><em class="application-plan-status ${meta.tone}">${escapeHtml(meta.label)}</em></header>
          <p>${escapeHtml(choice.summary)}</p>
          <div class="eligibility-checks">${choice.checks.map((check) => renderCheckRow(check.status === "needs_confirmation" ? "review" : check.status, `${check.title}：${check.detail}${check.contact_unit ? `（聯絡 ${check.contact_unit}）` : ""}`)).join("")}</div>
          ${choice.checklist.length ? `<details class="application-plan-checklist" open><summary><span>個人下一步</span><strong>${choice.checklist.length} 項</strong></summary><ol>${choice.checklist.map((item) => `<li class="${item.needs_confirmation ? "needs-confirmation" : "verified"}"><span><i data-lucide="${item.needs_confirmation ? "circle-help" : "circle-check"}" aria-hidden="true"></i></span><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.detail)}</p>${documentApplicabilityMarkup(item.document_applicability)}<small>${escapeHtml(item.phase)} · ${escapeHtml(item.responsible_unit)}${item.confirmation_contact ? ` · 請聯絡 ${escapeHtml(item.confirmation_contact)}` : ""}</small>${item.source_urls?.[0] ? `<a href="${escapeHtml(item.source_urls[0])}" target="_blank" rel="noopener noreferrer">查看官方來源</a>` : ""}</div></li>`).join("")}</ol></details>` : `<div class="application-plan-empty"><strong>暫不建立執行清單</strong><span>這個志願尚未開放或缺少結構化流程，請先聯絡 ${escapeHtml(plan.contact_unit)}。</span></div>`}
        </article>`;
    }).join("")}</div>
    <div class="eligibility-actions"><button id="view-matched-schools" type="button" class="secondary-button">回到合作校比較</button></div>`;
  $("#view-matched-schools")?.addEventListener("click", () => {
    state.partnerLimit = partnerPageSize();
    renderPartnerFilters();
    renderPartnerTable();
    window.location.hash = "#partners";
  });
  initIcons();
}

async function checkEligibility(event) {
  event.preventDefault();
  if (state.advisorLoading) return;
  const college = $("#advisor-college").value;
  const department = departmentField("advisor").value.trim();
  const degree = $("#advisor-degree").value;
  const academicYear = $("#eligibility-academic-year").value;
  const applicationRound = $("#eligibility-application-round").value;
  const academicScore = optionalNumber($("#advisor-academic-score").value);
  const ntu = activeHomeSchool() === "國立臺灣大學";
  const academicGpa = (ntu || state.dashboard?.academic_gpa_minimum != null) ? optionalNumber($("#advisor-academic-gpa").value) : null;
  const classRankPercent = ntu ? optionalNumber($("#advisor-class-rank").value) : null;
  const languageTest = $("#advisor-language-test").value;
  const languageScore = Number($("#advisor-language-score").value);
  const jlptLevel = activeHomeSchool() === '淡江大學' ? $('#advisor-jlpt-level').value : '';
  const targetTerm = $("#advisor-target-term").value;
  const preferredCountry = $("#advisor-country").value;
  const monthlyBudget = Number($("#advisor-monthly-budget").value) || 0;
  const scholarshipNeeded = $("#advisor-scholarship").checked;
  const teachingLanguage = $("#advisor-teaching-language").value;
  const courseInterests = $("#advisor-course-interests").value.trim();
  const result = $("#eligibility-result");
  const preferences = [1, 2, 3, 4, 5].slice(0,state.dashboard?.maximum_preferences || 5)
    .map((rank) => ({ rank, school_name: $(`#eligibility-preference-${rank}`).value }))
    .filter((item) => item.school_name)
    .map((item, index) => ({ ...item, rank: index + 1, ...(activeHomeSchool() === "國立中央大學" ? {document_preparation_state:ncuDocumentState(item.school_name, academicYear, applicationRound)} : {}) }));

  if (!college || !department || !degree || !academicYear || !applicationRound || (!ntu && (academicScore === null || !Number.isFinite(academicScore))) || (!languageTest && !jlptLevel) || !preferences.length) {
    announce("請完成所有必填欄位", "error");
    return;
  }
  if (new Set(preferences.map((item) => item.school_name)).size !== preferences.length) {
    announce("同一所學校不能重複列為志願", "error");
    return;
  }
  if (!state.account) {
    announce("建立個人申請清單需要先登入；公開搜尋與比較仍可直接使用。", "info", true);
    openAuthDialog("register");
    return;
  }

  const button = event.currentTarget.querySelector('button[type="submit"]');
  const requestedOwner = state.account.id;
  const requestedHome = activeHomeSchool();
  const requestId = ++state.conditionsRequestId;
  const draftKey = conditionsDraftKey();
  state.advisorLoading = true;
  button.disabled = true;
  result.className = "eligibility-result";
  result.innerHTML = '<div class="result-placeholder"><i data-lucide="loader-circle" aria-hidden="true"></i><strong>正在套用已查核規則</strong><span>不使用 AI 猜測；缺少的資料會列為待確認。</span></div>';
  initIcons();
  const profile = {
    college,
    department,
    degree,
    academicScore,
    academicGpa,
    classRankPercent,
    languageTest,
    languageScore,
    jlptLevel,
    languageLabel: languageScore > 0 ? `${languageTest.toUpperCase()} ${languageScore}` : "語言能力待確認",
    academicYear,
    applicationRound,
    currentYear: $("#advisor-current-year").value,
    targetTerm,
    preferredCountry,
    monthlyBudget,
    scholarshipNeeded,
    teachingLanguage,
    courseInterests,
  };
  const payload = {
    home_school: activeHomeSchool(),
    college,
    department,
    degree_level: degree,
    current_year: profile.currentYear,
    academic_score: ntu ? null : academicScore,
    academic_gpa: academicGpa,
    class_rank_percent: classRankPercent,
    language_test: languageTest || null,
    language_score: Number.isFinite(languageScore) && languageScore > 0 ? languageScore : null,
    jlpt_level: jlptLevel || null,
    academic_year: academicYear,
    application_round: applicationRound,
    preferences,
  };
  try {
    const plan = await fetchJson("/application-plan/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (state.account?.id !== requestedOwner || activeHomeSchool() !== requestedHome || requestId !== state.conditionsRequestId) return;
    if (draftKey !== conditionsDraftKey()) {
      result.innerHTML = '<p>查詢期間條件已修改，請重新核對志願。剛才的結果未套用或保存。</p>';
      announce("條件已修改，請重新核對志願。", "info");
      return;
    }
    state.eligibilityProfile = profile;
    state.personalApplicationPlan = plan;
    delete $("#advisor-form").dataset.draftOwner;
    state.applications = new Set(preferences.map((item) => item.school_name));
    const firstPartner = partnerByName(preferences[0].school_name);
    const previousContext = state.applicationContext;
    state.applicationContext = {
      ...state.applicationContext,
      school_name: activeHomeSchool(),
      target_school: preferences[0].school_name,
      target_country: firstPartner?.country || "",
      college,
      department,
      degree_level: degree,
      academic_year: academicYear,
      application_round: applicationRound,
      semester: semesterFromTargetTerm(targetTerm),
    };
    if (["target_school","college","department","degree_level","academic_year","application_round","semester"].some(field=>previousContext[field] !== state.applicationContext[field])) invalidateAllApplicationReviews();
    restoreApplicationContextForm();
    try {
      window.localStorage.setItem(STORAGE_KEYS.eligibility, JSON.stringify(state.eligibilityProfile));
    } catch (_) {
      // The authenticated workspace remains authoritative when local storage is unavailable.
    }
    persistAccountWorkspaceLocally();
    scheduleAccountWorkspaceSync();
    $("#clear-saved-eligibility").hidden = false;
    renderPersonalApplicationPlan(plan);
    renderAdvisorForm();
    state.college = college;
    state.degree = degree;
    renderDecisionBrief();
    renderDeadlinePreview();
    renderApplicationJourney();
    renderPersonalPlanSnapshot();
    renderRecommendedMatches();
    renderPartnerTable();
    renderFavorites();
    renderScholarships();
    renderBudgetPlanner();
    await loadApplicationTemplates();
    announce("個人申請清單已建立並同步", "success");
  } catch (error) {
    if (error.staleSession || requestId !== state.conditionsRequestId || state.account?.id !== requestedOwner || activeHomeSchool() !== requestedHome) return;
    result.className = "eligibility-result is-warning";
    result.innerHTML = `<div class="result-placeholder"><i data-lucide="triangle-alert" aria-hidden="true"></i><strong>暫時無法建立清單</strong><span>${escapeHtml(error.message)}</span></div>`;
    initIcons();
  } finally {
    if (requestId === state.conditionsRequestId) { state.advisorLoading = false; button.disabled = false; }
  }
}

function resetPrivatePlanningExperience({ renderRelated = true } = {}) {
  state.eligibilityProfile = null;
  state.personalApplicationPlan = null;
  state.advisorPlan = null;
  state.planningRecommendationKey = "";
  state.planningPreview = null;
  state.planningLoading = false;
  state.planningRequestId += 1;
  state.advisorLoading = false;
  state.conditionsRequestId += 1;
  try {
    window.localStorage.removeItem(STORAGE_KEYS.eligibility);
  } catch (_) {
    // The current session can still be reset.
  }

  const clearEligibility = $("#clear-saved-eligibility");
  if (clearEligibility) clearEligibility.hidden = true;
  const result = $("#eligibility-result");
  if (result) {
    result.className = "eligibility-result";
    result.innerHTML = '<div class="result-placeholder"><i data-lucide="clipboard-check" aria-hidden="true"></i><strong>還沒開始檢查</strong><span>填入資料後，系統會比對校內基本門檻與合作校公開條件。</span></div>';
  }

  const advisorForm = $("#advisor-form");
  if (advisorForm) {
    delete advisorForm.dataset.draftOwner;
    advisorForm.reset();
    advisorForm.querySelectorAll("input, select, textarea").forEach((field) => {
      if (field.type === "checkbox") field.checked = false;
      else field.value = "";
    });
  }
  const advisorButton = $("#advisor-submit");
  renderDepartmentOptions("advisor");
  if (advisorButton) {
    advisorButton.disabled = false;
    advisorButton.removeAttribute("aria-busy");
  }
  $("#advisor-result-content")?.replaceChildren();
  setAdvisorAssistantState("idle");
  if (state.dashboard) renderAdvisorForm();
  else renderAdvisorAccessState();

  if (!renderRelated) {
    initIcons();
    return;
  }
  renderDecisionBrief();
  renderApplicationJourney();
  renderPersonalPlanSnapshot();
  renderRecommendedMatches();
  renderPartnerFilters();
  renderPartnerTable();
  renderScholarships();
  initIcons();
}

function clearEligibilityProfile() {
  state.college = "";
  state.degree = "";
  resetPrivatePlanningExperience();
  persistAccountWorkspaceLocally();
  if (state.account) scheduleAccountWorkspaceSync();
  announce("選校與資格條件已清除", "success");
}

function renderCheckRow(type, text) {
  const icon = type === "pass" ? "circle-check" : type === "fail" ? "circle-alert" : "info";
  return `<div class="check-row ${type}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${escapeHtml(text)}</span></div>`;
}

function renderAdvisorForm() {
  if (!state.dashboard) return;
  const form = $("#advisor-form");
  const owner = JSON.stringify([state.account?.id || "",activeHomeSchool()]);
  if (form.dataset.draftOwner === owner) { renderAdvisorAccessState(); window.UniWayTKU?.renderEligibility?.(activeHomeSchool(), null); return; }
  delete form.dataset.draftOwner;
  const profile = state.eligibilityProfile || {};
  const partners = state.dashboard.partner_universities || [];
  const colleges = homeCollegeOptions();
  const countries = unique(partners.map((item) => item.country).filter(Boolean));
  fillSelect("#advisor-college", colleges, "尚未設定", homeCollegeValue(profile.college));
  renderDepartmentOptions("advisor", profile.department || "");
  fillSelect("#advisor-country", countries, "不限國家", profile.preferredCountry || "");
  $("#advisor-degree").value = profile.degree || "";
  $("#advisor-current-year").value = profile.currentYear || "";
  $("#advisor-academic-score").value = profile.academicScore ?? "";
  $("#advisor-academic-gpa").value = profile.academicGpa ?? "";
  $("#advisor-class-rank").value = profile.classRankPercent ?? "";
  renderAcademicFields();
  $("#advisor-language-test").value = profile.languageTest || "";
  $("#advisor-language-score").value = profile.languageScore ?? "";
  $("#advisor-target-term").value = profile.targetTerm || "";
  $("#advisor-monthly-budget").value = profile.monthlyBudget || "";
  $("#advisor-teaching-language").value = profile.teachingLanguage || "";
  $("#advisor-course-interests").value = profile.courseInterests || "";
  $("#advisor-scholarship").checked = Boolean(profile.scholarshipNeeded);
  renderAdvisorAccessState();
  window.UniWayTKU?.renderEligibility?.(activeHomeSchool(), profile);
}

function renderAdvisorAccessState() {
  const label = $("#advisor-submit")?.querySelector("span");
  const eligibility = $("#advisor-form")?.dataset.mode === "eligibility";
  if (label) label.textContent = state.account ? (eligibility ? "核對志願並建立計畫" : "產生我的申請方案") : (eligibility ? "登入後核對志願" : "登入後產生方案");
  const status = $("#advisor-profile-status");
  if (status && !$("#advisor-form").dataset.draftOwner) {
    status.textContent = state.eligibilityProfile
      ? "已保存條件"
      : state.account ? "尚未設定" : "未登入，不會保存條件";
  }
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

// ────────────────────────────────────────────────────────
// LAI-08: AI Status Manager, Consent, and Degradation
// ────────────────────────────────────────────────────────

const AI_STATUS_LABELS = {
  paused: { text: "AI 暫停", icon: "pause-circle", color: "var(--muted-color)" },
  offline: { text: "AI 離線", icon: "wifi-off", color: "var(--muted-color)" },
  loading: { text: "AI 載入中…", icon: "loader-2", color: "var(--warning-color, #e6a700)" },
  ready: { text: "本機 Gemma 4 就緒", icon: "sparkles", color: "var(--success-color, #2ea44f)" },
  busy: { text: "AI 處理中…", icon: "loader-2", color: "var(--warning-color, #e6a700)" },
  degraded: { text: "AI 降級（規則模式）", icon: "alert-triangle", color: "var(--warning-color, #e6a700)" },
};

class AiStatusManager {
  constructor() {
    this.state = "paused";
    this.pollInterval = null;
    this.consentGiven = false;
    this.currentFileHash = null;
  }

  async poll() {
    try {
      const status = await fetchJson("/ai/status");
      state.aiStatus = status;
      const newState = status?.runtime_state || (status?.ai_enabled ? "ready" : "paused");
      if (newState !== this.state) {
        this.state = newState;
        this.render();
        this.updateDegradation();
        this.announceStateChange();
      }
    } catch (_) {
      if (this.state !== "offline") {
        this.state = "offline";
        this.render();
        this.updateDegradation();
        this.announceStateChange();
      }
    }
  }

  start(intervalMs = 30000) {
    this.poll();
    this.pollInterval = setInterval(() => this.poll(), intervalMs);
  }

  stop() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  render() {
    const chip = $("#ai-status-chip");
    if (!chip) return;
    const info = AI_STATUS_LABELS[this.state] || AI_STATUS_LABELS.paused;
    chip.innerHTML = `<i data-lucide="${info.icon}" aria-hidden="true"></i><span>${info.text}</span>`;
    chip.style.setProperty("--ai-chip-color", info.color);
    chip.dataset.state = this.state;
    chip.hidden = false;
    initIcons();
  }

  announceStateChange() {
    const live = $("#ai-status-live");
    if (!live) return;
    const info = AI_STATUS_LABELS[this.state] || AI_STATUS_LABELS.paused;
    live.textContent = info.text;
  }

  updateDegradation() {
    const aiFeatures = document.querySelectorAll("[data-requires-ai]");
    const isAvailable = this.state === "ready";
    for (const el of aiFeatures) {
      el.classList.toggle("ai-unavailable", !isAvailable);
    }
    const banner = $("#ai-fallback-banner");
    if (banner) {
      banner.hidden = isAvailable;
    }
  }

  /** Invalidate consent when file changes. */
  onFileChange(fileHash) {
    if (fileHash !== this.currentFileHash) {
      this.consentGiven = false;
      this.currentFileHash = fileHash;
      const checkbox = $("#document-check-consent");
      if (checkbox) checkbox.checked = false;
    }
  }

  grantConsent() {
    this.consentGiven = true;
  }

  revokeConsent() {
    this.consentGiven = false;
    this.currentFileHash = null;
    const checkbox = $("#document-check-consent");
    if (checkbox) checkbox.checked = false;
  }

  get canSendToAi() {
    return this.state === "ready" && this.consentGiven;
  }
}

const aiStatusManager = new AiStatusManager();

function optionalNumber(value) {
  if (value === "" || value === null || value === undefined) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

const ADVISOR_ASSISTANT_STATE_META = {
  idle: {
    eyebrow: "留學小助手",
    title: "建立第一份申請方案",
    detail: "填寫條件後，我會整理候選學校、條件缺口與下一步。",
  },
  loading: {
    eyebrow: "官方資料整理中",
    title: "正在整理官方資料",
    detail: "只會依已查核來源與你填寫的條件整理，不使用虛構進度。",
  },
  success: {
    eyebrow: "整理完成",
    title: "申請方案已整理完成",
    detail: "請先查看條件缺口，再回到官方來源確認最新規定。",
  },
  insufficient: {
    eyebrow: "資料不足",
    title: "目前能確認的資料有限",
    detail: "缺少的部分會清楚標示，不會用推測補齊。",
  },
  error: {
    eyebrow: "整理中斷",
    title: "暫時無法完成整理",
    detail: "請稍後再試；你已填寫的表單內容仍會保留。",
  },
};

function setAdvisorAssistantState(nextState, detailOverride = "") {
  const assistant = $("#advisor-assistant");
  if (!assistant) return;
  const safeState = Object.prototype.hasOwnProperty.call(ADVISOR_ASSISTANT_STATE_META, nextState)
    ? nextState
    : "idle";
  const meta = ADVISOR_ASSISTANT_STATE_META[safeState];
  assistant.dataset.state = safeState;
  assistant.setAttribute("aria-busy", safeState === "loading" ? "true" : "false");
  $("#advisor-assistant-title").textContent = meta.title;
  $("#advisor-assistant-detail").textContent = detailOverride || meta.detail;
  const eyebrow = assistant.querySelector(".advisor-assistant-eyebrow");
  if (eyebrow) eyebrow.textContent = meta.eyebrow;
  assistant.classList.remove("is-entering");
  void assistant.offsetWidth;
  assistant.classList.add("is-entering");
}

function advisorAssistantStateForPlan(plan) {
  const evidenceStatus = plan?.answer?.evidence_status;
  return ["limited", "not_found", "none"].includes(evidenceStatus) ? "insufficient" : "success";
}

async function submitAdvisorPlan(event) {
  event.preventDefault();
  if (state.advisorLoading) return;
  if (!state.account) {
    announce("產生個人申請方案需要先登入；目前填寫內容尚未送出或保存。", "info", true);
    openAuthDialog("register");
    return;
  }
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = {
    school_name: activeHomeSchool(),
    target_school: state.applicationContext.target_school || null,
    college: formData.get("college") || null,
    department: formData.get("department") || null,
    current_year: formData.get("current_year") || null,
    degree_level: formData.get("degree_level") || null,
    academic_score: optionalNumber(formData.get("academic_score")),
    academic_gpa: optionalNumber(formData.get("academic_gpa")),
    class_rank_percent: optionalNumber(formData.get("class_rank_percent")),
    language_test: formData.get("language_test") || null,
    language_score: optionalNumber(formData.get("language_score")),
    jlpt_level: formData.get('jlpt_level') || null,
    academic_year: $('#eligibility-academic-year').value || null,
    application_round: $('#eligibility-application-round').value || null,
    target_term: formData.get("target_term") || null,
    preferred_country: formData.get("preferred_country") || null,
    monthly_budget: optionalNumber(formData.get("monthly_budget")),
    needs_scholarship: formData.get("needs_scholarship") === "on",
    preferred_teaching_language: formData.get("preferred_teaching_language") || null,
    course_interests: String(formData.get("course_interests") || "").trim() || null,
    question: String(formData.get("question") || "").trim() || null,
  };
  const button = $("#advisor-submit");
  const owner = state.account.id;
  const requestedHome = activeHomeSchool();
  const requestId = ++state.conditionsRequestId;
  const draftKey = conditionsDraftKey();
  const academicYear = $("#eligibility-academic-year").value;
  const applicationRound = $("#eligibility-application-round").value;
  state.advisorLoading = true;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  setAdvisorAssistantState("loading");
  $("#advisor-result-content").innerHTML = '<div class="advisor-loading" aria-hidden="true"><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div></div>';
  try {
    const plan = await fetchJson("/advisor/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (state.account?.id !== owner || activeHomeSchool() !== requestedHome || requestId !== state.conditionsRequestId) return;
    if (draftKey !== conditionsDraftKey()) {
      $("#advisor-profile-status").textContent = "條件已修改，請重新更新推薦";
      $("#advisor-result-content").innerHTML = '<p>查詢期間條件已修改，剛才的推薦未套用或保存。</p>';
      setAdvisorAssistantState("idle");
      return;
    }
    state.advisorPlan = plan;
    delete form.dataset.draftOwner;
    if (payload.college || payload.degree_level || payload.academic_score !== null || payload.language_test || payload.jlpt_level) {
      const threshold = languageThreshold(payload.language_test);
      state.eligibilityProfile = {
        academicYear,
        applicationRound,
        college: payload.college,
        department: payload.department || "",
        currentYear: payload.current_year || "",
        degree: payload.degree_level,
        academicScore: payload.academic_score,
        academicGpa: payload.academic_gpa,
        classRankPercent: payload.class_rank_percent,
        languageTest: payload.language_test,
        languageScore: payload.language_score,
        jlptLevel: payload.jlpt_level || '',
        languageLabel: selectionLanguageLabel(payload.language_test, payload.language_score),
        targetTerm: payload.target_term || "",
        preferredCountry: payload.preferred_country || "",
        monthlyBudget: payload.monthly_budget || 0,
        scholarshipNeeded: payload.needs_scholarship,
        teachingLanguage: payload.preferred_teaching_language || "",
        courseInterests: payload.course_interests || "",
      };
      try {
        window.localStorage.setItem(STORAGE_KEYS.eligibility, JSON.stringify(state.eligibilityProfile));
      } catch (_) {
        // The advisor result still applies for this session.
      }
      if (state.applicationContext.college !== payload.college || state.applicationContext.department !== (payload.department || "") || state.applicationContext.degree_level !== payload.degree_level) {
        invalidateAllApplicationReviews();
        state.applicationContext = { ...state.applicationContext, college:payload.college || "", department:payload.department || "", degree_level:payload.degree_level || "", semester:semesterFromTargetTerm(payload.target_term) || state.applicationContext.semester };
        persistApplicationContext();
      }
      const semester = semesterFromTargetTerm(payload.target_term);
      if (semester && semester !== state.applicationContext.semester) { invalidateAllApplicationReviews(); state.applicationContext.semester = semester; persistApplicationContext(); }
      restoreApplicationContextForm();
      state.personalApplicationPlan = null;
      $("#eligibility-result").innerHTML = '<p>條件已更新。選擇本次年度、梯次與志願後，重新核對資格。</p>';
      state.planningPlanProfileKey = planningProfileKey();
      state.planningRecommendationKey = JSON.stringify([planningProfileKey(),state.applicationContext.target_school]);
      restoreEligibilityForm();
      $("#advisor-profile-status").textContent = "已保存條件";
      state.planningPreview = null;
      state.planningRequestId += 1;
      state.planningLoading = false;
      scheduleAccountWorkspaceSync();
      renderPersonalPlanSnapshot();
      renderRecommendedMatches();
    }
    renderAdvisorResult(state.advisorPlan);
    renderRecommendedMatches();
    renderPersonalPlanSnapshot();
  } catch (error) {
    if (error.staleSession || requestId !== state.conditionsRequestId || state.account?.id !== owner || activeHomeSchool() !== requestedHome) return;
    setAdvisorAssistantState("error");
    $("#advisor-result-content").innerHTML = `<div class="advisor-error"><i data-lucide="circle-alert" aria-hidden="true"></i><strong>暫時無法產生方案</strong><span>${escapeHtml(error.message)}</span><button type="button" class="secondary-button" data-retry-advisor>重新嘗試</button></div>`;
    initIcons();
  } finally {
    if (requestId === state.conditionsRequestId) {
      state.advisorLoading = false;
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  }
}

function advisorTaskAction(task) {
  if (task.due_date) return `<button type="button" class="secondary-button" data-advisor-calendar="${escapeHtml(task.id)}"><i data-lucide="calendar-plus" aria-hidden="true"></i><span>加入日曆</span></button>`;
  const routes = { profile: "#advisor", eligibility: "#eligibility", language: "#eligibility", documents: "#application-center", scholarship: "#scholarships" };
  return `<a class="secondary-button" href="${routes[task.category] || "#overview"}"><span>前往處理</span><i data-lucide="arrow-right" aria-hidden="true"></i></a>`;
}

function advisorFitDetails(item) {
  const budget = item.budget_fit, language = item.teaching_language, course = item.course_interest;
  if (!budget && !language && !course) return "";
  const money = (value) => Number(value).toLocaleString("zh-TW", { maximumFractionDigits: 0 });
  const rows = [];
  if (budget) {
    const label = { within: "每月生活費在你的預算內", partly_within: "每月生活費可能超出預算", over: "每月生活費高於你的預算", unknown: "無法比對預算" }[budget.status] || "預算待確認";
    const estimate = budget.estimate;
    const body = estimate && budget.status !== "unknown"
      ? `來源記載每月約 ${escapeHtml(estimate.currency)} ${money(estimate.low)}${estimate.high !== estimate.low ? `–${money(estimate.high)}` : ""}（約 NT$${money(budget.low_twd)}${budget.high_twd !== budget.low_twd ? `–${money(budget.high_twd)}` : ""}，概估）。${escapeHtml(budget.exclusions)}${budget.fx_note ? ` ${escapeHtml(budget.fx_note)}` : ""}`
      : escapeHtml(budget.reason || "來源沒有可比對的每月生活費。");
    const evidence = estimate ? `<blockquote>${escapeHtml(estimate.evidence)}</blockquote>${(estimate.source_urls || []).slice(0, 2).map((url, index) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">費用來源 ${index + 1}</a>`).join(" · ")}` : "";
    rows.push(`<li data-fit="budget" data-fit-status="${escapeHtml(budget.status)}"><strong>${label}</strong><p>${body}</p>${evidence}</li>`);
  }
  if (language) {
    const label = { listed: "授課語言可能相符", not_listed: "語言要求與偏好不同", unknown: "語組與語言要求" }[language.status];
    rows.push(`<li data-fit="language" data-fit-status="${escapeHtml(language.status)}"><strong>${label}</strong><p>${escapeHtml(language.detail)}</p></li>`);
  }
  if (course) {
    rows.push(`<li data-fit="course" data-fit-status="${escapeHtml(course.status)}"><strong>${course.status === "mentioned" ? "公開資料提到你想修的領域" : "課程需自行核對"}</strong><p>${escapeHtml(course.detail)}</p>${(course.evidence || []).map((text) => `<blockquote>${escapeHtml(text)}</blockquote>`).join("")}</li>`);
  }
  return `<details class="advisor-fit-details"><summary><span>費用、語言與課程</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><ul>${rows.join("")}</ul></details>`;
}

function renderAdvisorResult(plan) {
  const container = $("#advisor-result-content");
  if (!plan) return;
  const recommendations = plan.recommendations || [];
  const tasks = plan.tasks || [];
  const answer = plan.answer;
  const modeLabel = "規則整理";
  setAdvisorAssistantState(advisorAssistantStateForPlan(plan));
  container.innerHTML = `
    <section class="advisor-summary-card glass-panel">
      <div><span class="advisor-mode"><i data-lucide="badge-check" aria-hidden="true"></i>系統資格比對</span><h3>${escapeHtml(plan.summary)}</h3></div>
      <div class="advisor-qualification">${(plan.qualification || []).map((item) => `<span><i data-lucide="${/未達|尚未|認定|待確認/.test(item) ? "circle-alert" : /已設定|已記錄/.test(item) ? "info" : "check"}" aria-hidden="true"></i>${escapeHtml(item)}</span>`).join("")}</div>
    </section>
    <section class="advisor-result-section">
      <div class="concise-heading"><div><span class="section-kicker">系統依公開條件排序</span><h3>你的選校結果</h3></div><a href="#partners">探索全部合作校</a></div>
      <div class="advisor-school-list">${recommendationGroups(recommendations, (item) => `
        <article class="advisor-school-card">
          <div class="advisor-school-photo">${item.image_url ? `<img src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.school_name)}校園" loading="lazy" />` : '<span><i data-lucide="school" aria-hidden="true"></i></span>'}</div>
          <div class="advisor-school-copy"><span>${escapeHtml(item.country || "未標示國家")}</span><strong>${escapeHtml(item.school_name)}</strong><small class="match-status ${recommendationStatus(item).status}">${recommendationStatus(item).label}</small><div>${(item.reasons || []).slice(0, 2).map((reason) => `<em>${escapeHtml(reason)}</em>`).join("")}</div></div>
          <div class="advisor-match-score"><strong>${item.match_score}</strong><small>排序分數</small></div>
          <div class="advisor-school-actions">${recommendationActions(item)}</div>
          ${advisorFitDetails(item)}
          ${[...(item.blocking_reasons || []), ...(item.confirmation_items || []), ...(item.gaps || [])].length ? `<details><summary><span>資格限制與待確認事項</span><i data-lucide="chevron-down" aria-hidden="true"></i></summary><ul>${[...new Set([...(item.blocking_reasons || []), ...(item.confirmation_items || []), ...(item.gaps || [])])].map((gap) => `<li>${escapeHtml(gap)}</li>`).join("")}</ul>${item.source_urls?.[0] ? `<a href="${escapeHtml(item.source_urls[0])}" target="_blank" rel="noreferrer">官方來源<i data-lucide="external-link" aria-hidden="true"></i></a>` : ""}</details>` : ""}
        </article>`, 5) || '<div class="advisor-empty"><strong>尚無可排序學校</strong><small>補齊條件後再試一次。</small></div>'}</div>
    </section>
    <section class="advisor-result-section">
      <div class="concise-heading"><div><h3>我的下一步</h3></div><a href="#calendar">查看日曆</a></div>
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
  if (!requireAccountForPrivateAction("把個人待辦加入申請日曆需要先登入。")) return;
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

function documentCompletenessReviewEnabled() {
  return Boolean(
    state.account
    && entitlementFeatureEnabled("document_completeness_review"),
  );
}

function renderDocumentCheckAccess() {
  const gate = $("#document-check-gate");
  const content = $("#document-check-content");
  if (!gate || !content) return;
  if (documentCompletenessReviewEnabled()) {
    gate.hidden = true;
    gate.innerHTML = "";
    content.hidden = false;
    return;
  }
  gate.hidden = false;
  content.hidden = true;
  if (!state.account) {
    gate.innerHTML = `
      <span><i data-lucide="log-in" aria-hidden="true"></i></span>
      <div><strong>登入後使用文件完整性檢查</strong><small>官方申請規定與表格仍可免登入查看；只有開始檢查自己的文件時才需要登入。</small></div>
      <button type="button" class="primary-button" data-document-check-login>登入後使用</button>`;
    initIcons();
    return;
  }
  if (!state.entitlements) {
    gate.innerHTML = '<div class="skeleton skeleton-card"></div>';
    return;
  }
  gate.innerHTML = `
    <span><i data-lucide="lock-keyhole" aria-hidden="true"></i></span>
    <div><strong>文件完整性檢查是進階功能</strong><small>免費方案仍可查看文件需求、下載官方表格並自行核對；登入後目前免費使用，系統不會扣款。</small></div>`;
  initIcons();
}

function resetDocumentCheck({ keepFile = false } = {}) {
  state.documentCheckRequestId += 1;
  state.documentCheckAbortController?.abort();
  state.documentCheckAbortController = null;
  state.documentCheckResult = null;
  state.documentCheckLoading = false;
  state.documentCheckGeneratedCandidate = null;
  state.documentCheckProvenance = null;
  const form = $("#document-check-form");
  if (!form) return;
  if (!keepFile) form.reset();
  $("#document-check-file").required = true;
  $("#document-check-consent").checked = false;
  $("#document-check-submit").disabled = !documentCompletenessReviewEnabled();
  $("#document-check-submit").removeAttribute("aria-busy");
  $("#document-upload-title").textContent = "選擇申請文件";
  $("#document-upload-meta").textContent = "PDF、DOCX 或 TXT，10 MB 以內";
  $("#document-check-status").textContent = "";
  $("#document-check-result").innerHTML = '<div class="advisor-empty"><strong>尚未檢查文件</strong><small>選擇成品並同意後，才會傳送本次檢查。</small></div>';
}

async function submitDocumentCheck(event) {
  event.preventDefault();
  if (state.documentCheckLoading) return;
  if (!state.account) {
    openAuthDialog();
    return;
  }
  if (!documentCompletenessReviewEnabled()) {
    announce("目前方案未包含文件完整性檢查。", "error", true);
    return;
  }
  const form = event.currentTarget;
  const candidate = state.documentCheckGeneratedCandidate;
  if (candidate && !window.UniWayDocumentWorkbench?.candidateCurrent(candidate)) {
    resetDocumentCheck();
    $("#document-check-status").textContent = "這份 PDF 的內容或申請背景已變更，請重新下載後選擇。";
    return;
  }
  const file = candidate?.blob || $("#document-check-file").files?.[0];
  if (!file) {
    announce("請先選擇文件", "error");
    return;
  }
  const consent = $("#document-check-consent");
  if (!consent.checked) {
    $("#document-check-status").textContent = "請先勾選同意傳送這一份文件；登入不代表同意傳送。";
    consent.focus();
    announce("請先同意傳送這一份文件", "error");
    return;
  }
  const data = new FormData(form);
  if (candidate) data.set("file", file, candidate.fileName);
  data.set("consent", "true");
  if (!String(data.get("expected_word_limit") || "").trim()) data.delete("expected_word_limit");
  const button = $("#document-check-submit");
  const requestId = ++state.documentCheckRequestId;
  const requestContext = captureAuthenticatedRequestContext();
  const requestedHome = state.homeSchool;
  const requestedRoute = location.hash;
  const current = () => requestId === state.documentCheckRequestId
    && authenticatedRequestContextIsCurrent(requestContext)
    && requestedHome === state.homeSchool && requestedRoute === location.hash
    && (!candidate || window.UniWayDocumentWorkbench.candidateCurrent(candidate));
  const controller = new AbortController();
  state.documentCheckAbortController = controller;
  state.documentCheckLoading = true;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  $("#document-check-status").textContent = "正在讀取文件…";
  $("#document-check-result").innerHTML = '<div class="advisor-loading"><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div></div>';
  try {
    const result = await fetchJson("/document-check", { method: "POST", body: data, signal:controller.signal });
    if (!current()) return;
    state.documentCheckResult = result;
    window.UniWayDocumentWorkbench?.renderFlow();
    state.documentCheckProvenance = {fileName:candidate?.fileName || file.name, generated:Boolean(candidate)};
    renderDocumentCheckResult(state.documentCheckResult);
    $("#document-check-status").textContent = "檢查完成";
  } catch (error) {
    if (!current()) return;
    $("#document-check-result").innerHTML = `<div class="advisor-error"><i data-lucide="circle-alert" aria-hidden="true"></i><strong>無法檢查這份文件</strong><span>${escapeHtml(error.message)}</span></div>`;
    $("#document-check-status").textContent = error.message;
    initIcons();
  } finally {
    if (current()) {
      state.documentCheckLoading = false;
      state.documentCheckAbortController = null;
      button.disabled = !documentCompletenessReviewEnabled();
      button.removeAttribute("aria-busy");
    }
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
    <p class="document-check-provenance">本次檢查：${escapeHtml(state.documentCheckProvenance?.fileName || "已選擇的文件")} · ${state.documentCheckProvenance?.generated ? "剛下載的 PDF" : "自行選擇的成品"}。規則檢查不代表校方已受理。</p>
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

function submitWritingAssistant(event) {
  event.preventDefault();
  $("#writing-assistant-status").textContent = "AI 功能暫緩，現在無法送出文字。";
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
        detail: [item.country, destination?.city, item.program_type, item.colleges, item.degree_levels, partnerDeadlineReference(item).compact].filter(Boolean).join("／"),
        type: "合作學校",
        source: { source_url: item.source_url },
      });
    }
  });
  information.forEach((item) => {
    if (normalize(`${item.title} ${(item.details || []).join(" ")}`).includes(query)) {
      const periodMeta = item.status ? applicationPeriodMeta(item) : null;
      const detail = periodMeta
        ? [periodMeta.label, item.deadline_at ? `${periodMeta.deadlineLabel}：${formatDate(item.deadline_at)}` : "", ...(item.details || []).slice(0, 1)].filter(Boolean).join("；")
        : (item.details || []).slice(0, 2).join("；");
      rows.push({ title: item.title, detail, type: periodMeta?.scopeLabel || "申請資訊", source: item.source });
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

// The region drop-down: "歐洲（全部）" and its parts, "亞洲（全部）" and its parts, and so on, only for regions that have a school.
function fillRegionSelect(selector, countries, selected = "") {
  const element = $(selector);
  const groups = window.UniWayRegions.regionGroups(countries);
  const option = (entry) => `<option value="${escapeHtml(entry.id)}">${escapeHtml(entry.label)}</option>`;
  element.innerHTML = [
    '<option value="">全部地區</option>',
    ...groups.map((group) => group.options.length === 1 && group.options[0].label === group.label
      ? option(group.options[0])
      : `<optgroup label="${escapeHtml(group.label)}">${group.options.map(option).join("")}</optgroup>`),
  ].join("");
  if ([...element.options].some((entry) => entry.value === selected)) element.value = selected;
}

// The country drop-down, split by region so "波蘭" is found under 東歐／中歐 instead of among 40 names in no obvious order.
function fillCountrySelect(selector, countries, selected = "") {
  const element = $(selector);
  const groups = window.UniWayRegions.countryGroups(countries);
  const option = (country) => `<option value="${escapeHtml(country)}">${escapeHtml(country)}</option>`;
  element.innerHTML = [
    '<option value="">全部國家</option>',
    ...(groups.length === 1
      ? groups[0].countries.map(option)
      : groups.map((group) => `<optgroup label="${escapeHtml(group.label)}">${group.countries.map(option).join("")}</optgroup>`)),
  ].join("");
  if ([...element.options].some((entry) => entry.value === selected)) element.value = selected;
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

function renderEmpty(selector, title, message, kind = "empty") {
  const template = $("#empty-template");
  const node = template.content.firstElementChild.cloneNode(true);
  const isError = kind === "error";
  node.classList.add("product-state", `is-${kind}`);
  node.dataset.state = kind;
  node.setAttribute("role", isError ? "alert" : "status");
  node.querySelector("i")?.setAttribute("data-lucide", isError ? "circle-alert" : "inbox");
  node.querySelector("strong").textContent = title;
  node.querySelector("span").textContent = message;
  $(selector).replaceChildren(node);
  initIcons();
}

const pageLoadingOperations = new Map();
let pageLoadingHideTimer = 0;

function ensureRuntimeLoadingOverlay() {
  let overlay = document.querySelector("#runtime-loading-splash");
  if (overlay) return overlay;
  const bootSplash = document.querySelector("#boot-splash");
  if (!bootSplash) return null;
  overlay = bootSplash.cloneNode(true);
  overlay.id = "runtime-loading-splash";
  overlay.className = "boot-splash runtime-loading-splash";
  overlay.hidden = true;
  overlay.querySelector(".boot-splash-hint")?.remove();
  overlay.querySelector(".boot-splash-hint-more")?.remove();
  bootSplash.after(overlay);
  return overlay;
}

function syncPageLoadingOverlay() {
  const overlay = ensureRuntimeLoadingOverlay();
  if (!overlay) return;
  const message = pageLoadingOperations.get("school-switch")
    || [...pageLoadingOperations.values()].at(-1)
    || "";
  window.clearTimeout(pageLoadingHideTimer);
  if (message) {
    overlay.setAttribute("aria-label", message);
    document.body.setAttribute("aria-busy", "true");
    // The boot splash already shows the same animation during initial start-up.
    if (document.querySelector("#boot-splash")) return;
    overlay.hidden = false;
    overlay.classList.remove("is-leaving");
    window.requestAnimationFrame(() => overlay.classList.add("is-active"));
    return;
  }
  document.body.setAttribute("aria-busy", "false");
  if (overlay.hidden) return;
  overlay.classList.add("is-leaving");
  pageLoadingHideTimer = window.setTimeout(() => {
    overlay.hidden = true;
    overlay.classList.remove("is-active", "is-leaving");
  }, 340);
}

function startPageLoading(key, message) {
  pageLoadingOperations.delete(key);
  pageLoadingOperations.set(key, message);
  syncPageLoadingOverlay();
}

function stopPageLoading(key) {
  pageLoadingOperations.delete(key);
  syncPageLoadingOverlay();
}

function announce(message, type = "info", persist = false) {
  state.statusRevision += 1;
  window.clearTimeout(state.statusTimer);
  if (type === "loading") {
    $("#page-status").replaceChildren();
    startPageLoading("page-status", message);
    return;
  }
  stopPageLoading("page-status");
  const icon = type === "error" ? "circle-alert" : type === "success" ? "circle-check" : "info";
  $("#page-status").innerHTML = `<div class="status-message ${escapeHtml(type)}"><i data-lucide="${icon}" aria-hidden="true"></i><span>${escapeHtml(message)}</span>${type === "error" ? '<button id="retry-load" type="button" class="secondary-button">重試</button>' : ""}</div>`;
  initIcons();
  if (!persist && type !== "error") {
    state.statusTimer = window.setTimeout(clearAnnouncement, 2600);
  }
}

function clearAnnouncement() {
  state.statusRevision += 1;
  window.clearTimeout(state.statusTimer);
  stopPageLoading("page-status");
  $("#page-status").replaceChildren();
}

function showLoadError(error, { announceError = true } = {}) {
  if (announceError) announce(`資料載入失敗：${error.message}`, "error", true);
  renderEmpty("#partner-table", "暫時無法取得學校資料", "請確認網路或服務狀態後重新嘗試。", "error");
  renderEmpty("#period-list", "暫時無法取得截止日期", "重新整理後再試一次。", "error");
  renderEmpty("#scholarship-list", "暫時無法取得補助資料", "重新整理後再試一次。", "error");
  renderEmpty("#documents-list", "暫時無法取得文件摘要", "重新整理後再試一次。", "error");
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
  if (window.UniWayNavigation.isRestoring) return;
  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "instant" });
  scrollToTop();
  window.requestAnimationFrame(scrollToTop);
}

function focusRouteHeading(selector) {
  const route = window.location.hash;
  const origin = document.activeElement;
  window.requestAnimationFrame(() => {
    if (window.location.hash !== route) return;
    // A queued route callback must not steal focus from a control the user
    // has already reached with the keyboard during the next frame.
    if (document.activeElement !== origin && document.activeElement?.closest("button, a, input, textarea, select, summary, [role='tab']")) return;
    if (document.querySelector('[aria-modal="true"]:not([hidden])')) return;
    const heading = typeof selector === "string" ? document.querySelector(selector) : selector;
    if (!(heading instanceof HTMLElement) || heading.getClientRects().length === 0) return;
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
  });
}

function showUniversityPage(pageId, { resetScroll = true, focusHeading = true } = {}) {
  const activePage = UNIVERSITY_PAGE_ROUTES.has(pageId) ? pageId : null;
  const pageNodes = [...document.querySelectorAll("[data-university-page]")];
  pageNodes.forEach((node) => {
    node.hidden = !activePage || node.dataset.universityPage !== activePage;
  });
  window.UniWayApplicationWorkspace?.show(activePage);
  window.UniWayDocumentWorkbench?.route(activePage);
  syncPartnerView();

  if (!activePage) {
    delete document.body.dataset.activeUniversityPage;
    return null;
  }

  document.body.dataset.activeUniversityPage = activePage;
  setActiveNavigation(activePage === "search" ? "" : activePage === "application-form" ? "application-center" : activePage);
  document.title = `${UNIVERSITY_PAGE_TITLES[activePage]} | UniWay`;

  if (resetScroll) resetRouteScroll();
  if (focusHeading) {
    const page = pageNodes.find((node) => node.dataset.universityPage === activePage && !node.hidden);
    focusRouteHeading(page?.querySelector("h1, h2"));
  }
  return activePage;
}

function globalFeedForHash(hash = window.location.hash) {
  return {
    "#forum": "all",
    "#following": "following",
    "#public-board": "public",
    "#language-school-board": "language",
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

function isPublicExplorationRoute(hash = window.location.hash) {
  return hash === "#home" || hash === "#feedback" || hash === "#profile" || hash === "#partners" || hash === "#search" || /^#school=/.test(hash) || /^#guide(=|$)/.test(hash);
}

function isPersonalizedRoute(hash = window.location.hash) {
  return /^#application-form=/.test(hash)
    || ["#overview", "#advisor", "#favorites", "#calendar", "#deadlines", "#scholarships", "#budget", "#eligibility", "#application-center", "#document-check", "#writing-assistant", "#documents", "#university-posts", "#cgu-posts"].includes(hash);
}

function updateUniWayPublicNavigation(hash = window.location.hash) {
  window.UniWayMotion?.route(hash);
  const activeRoute = isPersonalizedRoute(hash) || /^#guide(=|$)/.test(hash) ? "overview" : globalFeedForHash(hash)
    ? "forum"
    : (/^#school=/.test(hash) || hash === "#search" ? "partners" : hash.slice(1));
  document.querySelectorAll(".application-tools-panel a").forEach((link) => {
    if (link.getAttribute("href") === hash) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  document.querySelectorAll("[data-public-route]").forEach((link) => {
    const active = link.dataset.publicRoute === activeRoute;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  document.querySelectorAll("#account-button, #mobile-account-button, #global-mobile-account-button").forEach((button) => {
    if (hash === "#profile") button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
}

function applyAppRoute({ loadFeed = true, resetScroll = true } = {}) {
  let hash = window.location.hash || "#home";
  const globalFeed = globalFeedForHash(hash);
  const isUniversityPosts = hash === "#cgu-posts" || hash === "#university-posts";
  const isPublicExploration = isPublicExplorationRoute(hash);
  document.body.classList.toggle("global-home-mode", Boolean(globalFeed));
  document.body.classList.toggle("public-exploration-mode", !globalFeed && isPublicExploration);
  document.body.classList.toggle("university-board-mode", !globalFeed && !isPublicExploration);
  document.body.classList.toggle("cgu-community-mode", isUniversityPosts);
  updateUniWayPublicNavigation(hash);
  window.UniWayCommunity?.syncDetail();

  if (globalFeed) {
    showUniversityPage(null, { resetScroll: false, focusHeading: false });
    state.globalCommunityFeed = globalFeed;
    renderCommunityPageContext(["cgu", "university"].includes(globalFeed));
    renderGlobalCommunityNavigation();
    setActiveNavigation("");
    document.title = `${globalFeed === "following" ? "我的追蹤" : globalFeed === "public" ? "公共留學板" : globalFeed === "language" ? LANGUAGE_SCHOOL_COMMUNITY_BOARD : globalFeed === "cgu" ? "長庚大學貼文" : globalFeed === "university" ? `${activeHomeSchool()}貼文` : "論壇"} | UniWay`;
    if (!state.activeSchool) {
      $("#dashboard-view").hidden = false;
      $("#school-detail-view").hidden = true;
    }
    if (resetScroll) resetRouteScroll();
    if (resetScroll) focusRouteHeading("#community-hub-title");
    if (loadFeed) loadGlobalCommunity();
    return;
  }

  if (isUniversityPosts) {
    showUniversityPage(null, { resetScroll: false, focusHeading: false });
    state.globalCommunityFeed = hash === "#cgu-posts" ? "cgu" : "university";
    renderCommunityPageContext(true);
    setActiveNavigation("university-posts");
    document.title = `${activeHomeSchool()}討論板 | UniWay`;
    if (resetScroll) resetRouteScroll();
    if (resetScroll) focusRouteHeading("#community-hub-title");
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
    if (!applicationDocumentGenerationEnabled()) {
      showUniversityPage("application-center", { resetScroll, focusHeading: resetScroll });
      renderApplicationCenter();
      return;
    }
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

  if (hash === "#profile") {
    // The profile page is private: without an account the sign-in dialog opens over the home page instead.
    // While the saved session is still being checked the page waits, and syncProfileRoute() settles it afterwards.
    if (!state.account && state.authRestoreState !== "pending") {
      openAuthDialog();
      window.location.replace("#home");
      return;
    }
    if (state.account) fillProfileForm();
    showUniversityPage("profile", { resetScroll, focusHeading: resetScroll && Boolean(state.account) });
    return;
  }

  const guideRoute = hash.match(/^#guide(?:=(.+))?$/);
  if (guideRoute) {
    // The article is drawn before the page is shown so the route heading exists when it is focused.
    window.UniWayGuide?.show(guideRoute[1] ? decodeURIComponent(guideRoute[1]) : "");
    showUniversityPage("guide", { resetScroll, focusHeading: resetScroll });
    return;
  }

  const sectionId = hash === "#home" ? "home" : hash.slice(1) || "overview";
  showUniversityPage(UNIVERSITY_PAGE_ROUTES.has(sectionId) ? sectionId : "overview", {
    resetScroll,
    focusHeading: resetScroll,
  });
}

function handleLocationRoute() {
  const filtersChanged = window.location.search !== partnerUrlSearch ? readPartnerUrl() : false;
  const routeHome = new URLSearchParams(window.location.search).get("home");
  if (routeHome && routeHome !== activeHomeSchool() && state.supportedUniversities.some((item) => item.school_name === routeHome)) setHomeSchool(routeHome);
  const route = window.location.hash.match(/^#school=(.+)$/);
  if (route && state.dashboard) {
    document.body.classList.remove("global-home-mode", "university-board-mode", "cgu-community-mode");
    document.body.classList.add("public-exploration-mode");
    updateUniWayPublicNavigation(window.location.hash);
    const item = partnerByName(decodeURIComponent(route[1]));
    if (item && state.activeSchool !== item.school_name) {
      openUniversityDetail(item, { updateHistory: false });
    }
    return;
  }
  if (state.activeSchool) closeUniversityDetail({ updateHistory: false });
  applyAppRoute();
  if (window.location.hash === "#partners" && state.dashboard) {
    writePartnerUrl();
    if (filtersChanged) renderPartnerTable();
    else syncPartnerView();
  }
  if (isPersonalizedRoute() && !state.homeSchool) initializeSchoolOnboarding();
}

function bindEvents() {
  ["input", "change"].forEach((type) => {
    $("#advisor-form").addEventListener(type, () => {
      $("#advisor-form").dataset.draftOwner = JSON.stringify([state.account?.id || "", activeHomeSchool()]);
    });
  });
  ["advisor"].forEach((prefix) => {
    $(`#${prefix}-college`).addEventListener("change", () => renderDepartmentOptions(prefix, departmentField(prefix).value));
  });
  document.querySelectorAll("[data-calendar-panel]").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = $(button.dataset.calendarPanel);
      if (!panel) return;
      panel.open = true;
      panel.scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "start" });
      panel.querySelector("summary")?.focus();
    });
  });
  document.querySelectorAll("[data-partner-view]").forEach((button) => {
    button.addEventListener("click", () => setPartnerView(button.dataset.partnerView));
  });
  document.addEventListener("error", (event) => {
    const image = event.target;
    if (image instanceof HTMLImageElement && image.dataset.removeOnError === "true") {
      const fallback = image.parentElement?.querySelector(".school-photo-fallback");
      fallback?.removeAttribute("aria-hidden");
      fallback?.setAttribute("role", "img");
      image.remove();
    }
  }, true);
  document.addEventListener("click", (event) => {
    const personalizedLink = event.target.closest("[data-requires-home-school]");
    if (!personalizedLink || state.homeSchool) return;
    event.preventDefault();
    state.pendingPersonalizedHash = personalizedLink.getAttribute("href") || "";
    openSchoolOnboarding();
  });
  $("#account-button").addEventListener("click", () => state.account ? openProfileDialog() : openAuthDialog());
  $("#notification-button").addEventListener("click", openNotificationDialog);
  $("#account-workspace-sync-retry").addEventListener("click", () => {
    void retryAccountWorkspaceSyncFromControl();
  });
  $("#mobile-account-button")?.addEventListener("click", () => state.account ? openProfileDialog() : openAuthDialog());
  $("#global-mobile-account-button").addEventListener("click", () => state.account ? openProfileDialog() : openAuthDialog());
  document.querySelectorAll("[data-close-auth]").forEach((button) => button.addEventListener("click", closeAuthDialog));
  document.querySelectorAll("[data-close-notifications]").forEach((button) => button.addEventListener("click", closeNotificationDialog));
  $("#notification-read-all").addEventListener("click", markAllNotificationsRead);
  $("#notification-delete-all").addEventListener("click", deleteAllNotifications);
  $("#notification-center-list").addEventListener("click", async (event) => {
    const changesButton = event.target.closest("[data-notification-changes]");
    if (changesButton) { await showNotificationChanges(changesButton); return; }
    const readButton = event.target.closest("[data-read-notification]");
    if (readButton) {
      readButton.disabled = true;
      try {
        await markNotificationRead(readButton.dataset.readNotification);
      } catch (error) {
        announce(error.message, "error");
        readButton.disabled = false;
      }
      return;
    }
    const deleteButton = event.target.closest("[data-delete-notification]");
    if (deleteButton) {
      deleteButton.disabled = true;
      try {
        await deleteNotification(deleteButton.dataset.deleteNotification);
      } catch (error) {
        announce(error.message, "error");
        deleteButton.disabled = false;
      }
      return;
    }
    const openLink = event.target.closest("[data-open-notification]");
    if (!openLink) return;
    event.preventDefault();
    const href = openLink.getAttribute("href") || "/#deadlines";
    try {
      await markNotificationRead(openLink.dataset.openNotification);
    } catch (_) {
      // The deadline remains available even if the read marker cannot sync yet.
    }
    closeNotificationDialog();
    window.location.href = href;
  });
  document.querySelectorAll("[data-auth-mode]").forEach((button) => button.addEventListener("click", () => setAuthMode(button.dataset.authMode)));
  document.querySelectorAll("[data-oauth-provider]").forEach((button) => button.addEventListener("click", () => {
    if (button.disabled) return;
    // Nobody leaves for the provider (and so nobody creates an account) without ticking the current terms; the server
    // checks the same version again, so skipping this script does not skip the tick.
    const consent = $("#terms-consent");
    if (consent && !consent.checked) {
      $("#terms-consent-hint").hidden = false;
      consent.focus();
      return;
    }
    const version = consent?.dataset.termsVersion || "";
    rememberAcceptedTerms(version);
    window.location.href = `/auth/oauth/${encodeURIComponent(button.dataset.oauthProvider)}/start?terms=${encodeURIComponent(version)}`;
  }));
  $("#terms-consent")?.addEventListener("change", (event) => {
    if (event.currentTarget.checked) $("#terms-consent-hint").hidden = true;
  });
  $("#request-email-verification").addEventListener("click", requestEmailVerification);
  $("#confirm-email-verification").addEventListener("click", confirmEmailVerification);
  $("#registration-email").addEventListener("input", (event) => {
    const current = event.currentTarget.value.trim().toLowerCase();
    if (state.emailVerificationAddress && current !== state.emailVerificationAddress) resetEmailVerificationFlow();
  });
  $("#request-profile-email-verification").addEventListener("click", requestProfileEmailVerification);
  $("#confirm-profile-email-verification").addEventListener("click", confirmProfileEmailVerification);
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
  $("#workflow-issue-report-form").addEventListener("submit", submitWorkflowIssueReport);
  $("#workflow-issue-report-dialog").addEventListener("click", (event) => {
    if (event.target === event.currentTarget || event.target.closest("[data-close-workflow-issue-report]")) {
      closeWorkflowIssueReport();
    }
  });
  $("#workflow-issue-report-dialog").addEventListener("cancel", (event) => {
    event.preventDefault();
    closeWorkflowIssueReport();
  });
  document.addEventListener("keydown", (event) => {
    trapAccountDialogFocus(event);
    if (event.key === "Escape") {
      if (!$("#auth-dialog").hidden) closeAuthDialog();
      if (!$("#notification-dialog").hidden) closeNotificationDialog();
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
    window.UniWayCommunity.updateFilters({ topic: state.globalCommunityTopic });
  });
  $("#global-community-search").addEventListener("input", (event) => {
    window.clearTimeout(state.globalCommunityTimer);
    const query = event.target.value.trim();
    state.globalCommunityTimer = window.setTimeout(() => {
      state.globalCommunityQuery = query;
      window.UniWayCommunity.updateFilters({ q: state.globalCommunityQuery });
    }, 280);
  });
  $("#global-community-feed").addEventListener("submit", async (event) => {
    const form = event.target.closest(".post-comment-form");
    if (!form) return;
    event.preventDefault();
    if (await handleCommunityFormSubmit(form, submitPostCommentForm, "回覆已發布。")) await loadGlobalCommunity();
  });
  $("#global-community-feed").addEventListener("click", async (event) => {
    const deletePost = event.target.closest("[data-delete-post]");
    if (deletePost) {
      if (await deleteCommunityResource(`/community/posts/${encodeURIComponent(deletePost.dataset.deletePost)}`, "確定要刪除這篇貼文與全部留言嗎？")) await loadGlobalCommunity();
      return;
    }
    const deleteComment = event.target.closest("[data-delete-comment]");
    if (deleteComment) {
      if (await deleteCommunityResource(`/community/posts/${encodeURIComponent(deleteComment.dataset.postId)}/comments/${encodeURIComponent(deleteComment.dataset.deleteComment)}`, "確定要刪除這則留言嗎？")) await loadGlobalCommunity();
      return;
    }
    const report = event.target.closest("[data-report-resource]");
    if (report) await reportCommunityResource(report);
  });

  $("#refresh-button").addEventListener("click", async () => {
    if (document.body.classList.contains("global-home-mode") || document.body.classList.contains("cgu-community-mode")) {
      await loadGlobalCommunity({ force: true });
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

  $("#onboarding-close")?.addEventListener("click", dismissSchoolOnboarding);
  $("#school-search")?.addEventListener("input", (event) => renderSchoolOptions(event.target.value));
  // Choosing a school is a single click: it saves the choice (for a new account) and opens that school's page.
  $("#school-options")?.addEventListener("click", async (event) => {
    const option = event.target.closest("[data-home-school]");
    if (option) await chooseHomeSchool(option.dataset.homeSchool);
  });
  document.addEventListener("keydown", handleOnboardingKeydown);

  $("#partner-search").addEventListener("input", (event) => {
    state.partnerQuery = event.target.value;
    state.partnerLimit = partnerPageSize();
    renderPartnerTable();
  });

  ["availability", "region", "country", "college", "degree"].forEach((name) => {
    $(`#${name}-filter`).addEventListener("change", (event) => {
      state[name] = event.target.value;
      state.partnerLimit = partnerPageSize();
      // A new region changes which countries can be picked; a country outside it is let go.
      if (name === "region") {
        if (state.country && !window.UniWayRegions.inRegion(state.country, state.region)) state.country = "";
        renderPartnerFilters();
      }
      renderPartnerTable();
    });
  });

  $("#clear-partner-filters").addEventListener("click", () => {
    state.partnerQuery = "";
    discoveryCriteria = {};
    $("#discovery-criteria-form").reset();
    renderDiscoveryCriteria();
    state.availability = "";
    state.region = "";
    state.country = "";
    state.college = "";
    state.degree = "";
    state.partnerQuota = "";
    state.partnerFit = "";
    state.partnerLimit = partnerPageSize();
    $("#partner-search").value = "";
    renderPartnerFilters();
    renderPartnerTable();
  });

  $("#show-more-partners").addEventListener("click", () => {
    state.partnerLimit += partnerPageSize();
    renderPartnerTable();
  });

  $("#calendar-event-form").elements.date.value = localDateKey();
  $("#calendar-event-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (addCalendarEvent(event.currentTarget)) {
      event.currentTarget.closest("details")?.removeAttribute("open");
    }
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
    $("#calendar-sync-panel").scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "center" });
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
    const conflictDateButton = event.target.closest("[data-calendar-conflict-date]");
    if (conflictDateButton) {
      const date = parseLocalDate(conflictDateButton.dataset.calendarConflictDate);
      if (!date) return;
      state.calendarSelectedDate = localDateKey(date);
      state.calendarMonth = new Date(date.getFullYear(), date.getMonth(), 1);
      state.calendarAgendaMode = "selected";
      renderApplicationCalendar();
      $("#calendar-agenda-list")?.scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "center" });
      return;
    }
    const taskDateButton = event.target.closest("[data-calendar-task-date], [data-calendar-task-deadline]");
    if (taskDateButton) {
      const date = parseLocalDate(taskDateButton.dataset.calendarTaskDate || taskDateButton.dataset.calendarTaskDeadline);
      if (!date) return;
      state.calendarSelectedDate = localDateKey(date);
      state.calendarMonth = new Date(date.getFullYear(), date.getMonth(), 1);
      state.calendarAgendaMode = "selected";
      renderApplicationCalendar();
      $("#calendar-agenda-list")?.scrollIntoView({ behavior: window.UniWayMotion?.reduced ? "instant" : "smooth", block: "center" });
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
      const item = calendarDisplayEvents().find((row) => row.id === download.dataset.downloadCalendarEvent);
      if (item) downloadCalendarEvents([item], `${item.date}-${item.title.replace(/[^\p{L}\p{N}-]+/gu, "-")}.ics`);
      return;
    }
    const remove = event.target.closest("[data-delete-calendar-event]");
    if (remove) deleteCalendarEvent(remove.dataset.deleteCalendarEvent);
  });

  $("#calendar").addEventListener("change", (event) => {
    const status = event.target.closest("[data-calendar-task-status]");
    if (status) updateCalendarTaskStatus(status.dataset.calendarTaskStatus, status.value);
  });

  $("#clear-saved-eligibility").addEventListener("click", clearEligibilityProfile);
  $("#eligibility-academic-year").addEventListener("change", renderApplicationPeriodOptions);
  $("#eligibility-application-round").addEventListener("change", renderApplicationPeriodOptions);
  $("#application-period-retry").addEventListener("click", loadApplicationPeriodOptions);
  ["#planning-academic-year","#planning-application-round"].forEach(selector=>$(selector).addEventListener("input",renderApplicationPeriodOptions));
  $("#advisor-form").addEventListener("submit", event=>window.location.hash === "#eligibility" ? checkEligibility(event) : submitAdvisorPlan(event));
  ["input","change"].forEach(type=>$("#advisor-form").addEventListener(type, ()=>{
    $("#advisor-form").dataset.draftOwner = JSON.stringify([state.account?.id || "",activeHomeSchool()]);
    $("#advisor-profile-status").textContent = "條件已修改，尚未更新方案";
  }));
  $("#planning-schedule-form").addEventListener("submit", previewPlanningSchedule);
  $("#planning-schedule-form").addEventListener("input", () => {
    if (!state.planningPreview && !state.planningLoading) return;
    state.planningRequestId += 1;
    state.planningLoading = false;
    state.planningPreview = null;
    $("#planning-schedule-preview").replaceChildren();
    $("#planning-confirm").hidden = true;
    $("#planning-update-durations").hidden = true;
    $("#planning-preview-button").disabled = !planningPreviewAllowed();
    $("#planning-preview-button").removeAttribute("aria-busy");
    $("#planning-schedule-status").textContent = "條件或準備天數已改變，請重新預覽時程。";
  });
  $("#planning-confirm").addEventListener("click", confirmPlanningSchedule);
  $("#planning-schedule-preview").addEventListener("input", event=>{
    const input = event.target.closest("[data-planning-duration]");
    if (!input || !state.planningDurations) return;
    const days = Number(input.value);
    if (Number.isInteger(days) && days >= 1 && days <= 90) state.planningDurations.values[input.dataset.planningDuration] = days;
    if (state.planningPreview) state.planningPreview.needsRefresh = true;
    $("#planning-confirm").hidden = true;
    $("#planning-schedule-status").textContent = "準備天數已調整，請更新預覽後再加入日曆。";
  });
  $("#planning-update-durations").addEventListener("click", ()=>{
    const inputs = [...document.querySelectorAll("[data-planning-duration]")];
    if (!inputs.every(input=>input.reportValidity())) return;
    $("#planning-schedule-form").requestSubmit();
  });
  $("#advisor-form").addEventListener("click", (event) => {
    const prompt = event.target.closest("[data-advisor-question]");
    if (!prompt) return;
    $("#advisor-question").value = prompt.dataset.advisorQuestion;
    $("#advisor-question").focus();
  });
  $("#document-check-form").addEventListener("submit", submitDocumentCheck);
  $("#document-check-gate").addEventListener("click", (event) => {
    if (event.target.closest("[data-document-check-login]")) openAuthDialog();
  });
  $("#document-check-file").addEventListener("change", (event) => {
    const file = event.currentTarget.files?.[0];
    resetDocumentCheck({ keepFile: true });
    const consent = $("#document-check-consent");
    consent.checked = false;
    $("#document-upload-title").textContent = file?.name || "選擇申請文件";
    $("#document-upload-meta").textContent = file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : "PDF、DOCX 或 TXT，10 MB 以內";
    $("#document-check-status").textContent = file
      ? "已選擇新文件；請閱讀並重新勾選傳送同意。"
      : "";
  });
  $("#writing-assistant-form").addEventListener("submit", submitWritingAssistant);

  $("#budget-form").addEventListener("submit", saveBudgetPlan);
  $("#budget-form").addEventListener("input", () => {
    state.pendingBudgetDraft = null;
    updateBudgetResult();
  });
  $("#budget-currency").addEventListener("change", () => {
    state.pendingBudgetDraft = null;
    updateBudgetResult();
  });
  $("#budget-school").addEventListener("change", (event) => {
    state.pendingBudgetDraft = null;
    populateBudgetForm(event.target.value);
  });

  $("#application-context-form").addEventListener("submit", (event) => event.preventDefault());
  $("#application-context-form").addEventListener("change", (event) => {
    if (["ncu-host-admission", "ncu-housing-choice"].includes(event.target.id)) return;
    handleApplicationContextChange(event);
  });
  $("#ncu-host-admission").addEventListener("change", handleNcuDocumentStateChange);
  $("#ncu-housing-choice").addEventListener("change", handleNcuDocumentStateChange);
  $("#application-profile-form").addEventListener("submit", saveApplicationProfile);
  $("#application-remember-profile").addEventListener("change", (event) => setApplicationProfileMemory(event.target.checked));
  $("#clear-application-profile-memory").addEventListener("click", clearApplicationProfileMemory);
  $("#application-template-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-open-application-template]");
    if (!button) return;
    if (!state.account) {
      openAuthDialog();
      return;
    }
    if (!applicationDocumentGenerationEnabled()) {
      announce("目前方案未包含自動填表與申請文件套件產生。", "error", true);
      return;
    }
    window.location.hash = `#application-form=${encodeURIComponent(button.dataset.openApplicationTemplate)}`;
  });
  $("#application-generation-gate").addEventListener("click", (event) => {
    if (event.target.closest("[data-application-generation-login]")) openAuthDialog();
  });
  $("#application-document-stage").addEventListener("change", event=>selectApplicationStage(event.target.value));
  $("#application-template-list").addEventListener("change", handlePacketSelection);
  $("#application-packet-list").addEventListener("change", handlePacketSelection);
  function handlePacketSelection(event) {
    const checkbox = event.target.closest("[data-application-packet-template]");
    if (checkbox) {
      const template = applicationTemplateById(checkbox.dataset.applicationPacketTemplate);
      if (!template) return;
      const existing = state.applicationSelections[template.id] || {};
      state.applicationSelections[template.id] = {
        ...existing,
        selected: checkbox.checked,
        copies: existing.copies || template.default_copies,
        status: applicationDocumentStatus(template.id),
      };
      persistApplicationContext();
      renderApplicationTemplates();
      renderApplicationPacket();
      updateApplicationCenterSteps();
      if (!checkbox.isConnected) {
        const replacement = [...document.querySelectorAll("[data-application-packet-template]")].find(input=>input.dataset.applicationPacketTemplate === template.id && input.getClientRects().length);
        if (replacement) replacement.focus({preventScroll:true});
        else { $("#application-packet-title").setAttribute("tabindex","-1"); $("#application-packet-title").focus({preventScroll:true}); }
      }
      initIcons();
      return;
    }
    const copies = event.target.closest("[data-application-copy-template]");
    if (copies) {
      updateApplicationPacketCopies(copies);
    }
  }
  $("#download-application-packet").addEventListener("click", () => generateApplicationPdf());
  $("#application-packet-list").addEventListener("input", (event) => {
    const input = event.target.closest("[data-application-copy-template]");
    if (input) updateApplicationPacketCopies(input, { refreshRows:false });
  });
  $("#application-document-form").addEventListener("submit", saveApplicationDocument);
  $("#application-document-form").addEventListener("input", (event) => {
    const input = event.target.closest("[data-application-field]");
    if (!input) return;
    if (state.activeApplicationTemplateId) invalidateApplicationReview(state.activeApplicationTemplateId);
    const template = applicationTemplateById(state.activeApplicationTemplateId);
    if (template) rememberApplicationField(template, input);
    window.UniWayDocumentWorkbench?.draftChanged(template?.id);
  });
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
      window.UniWayDocumentWorkbench?.draftChanged(state.activeApplicationTemplateId);
      return;
    }
    const sharedInput = event.target.closest("[data-application-field]");
    if (sharedInput) {
      const template = applicationTemplateById(state.activeApplicationTemplateId);
      if (template) rememberApplicationField(template, sharedInput);
    }
  });
  $("#application-document-form").addEventListener("click", (event) => {
    const consent = event.target.closest("[data-application-file-consent]");
    if (consent) {
      openApplicationFileConsent(
        consent.dataset.templateId,
        consent.dataset.fieldId,
        consent.dataset.fileIndex,
      );
      return;
    }
    const loadSaved = event.target.closest("[data-load-application-vault-file]");
    if (loadSaved) {
      loadApplicationVaultFile(loadSaved);
      return;
    }
    const deleteSaved = event.target.closest("[data-delete-application-vault-file]");
    if (deleteSaved) deleteApplicationVaultFile(deleteSaved);
  });
  $("#application-file-consent-form").addEventListener("submit", submitApplicationFileConsent);
  $("#application-file-consent-dialog").addEventListener("click", (event) => {
    if (event.target.closest("[data-close-application-file-consent]")) closeApplicationFileConsent();
  });
  $("#application-file-consent-dialog").addEventListener("cancel", (event) => {
    event.preventDefault();
    closeApplicationFileConsent();
  });
  $("#application-download-dialog").addEventListener("click", (event) => {
    const action = event.target.closest("[data-generated-document-action]");
    if (action) {
      window.UniWayDocumentWorkbench.generatedAction(action.dataset.generatedDocumentAction);
      return;
    }
    if (event.target.closest("[data-close-application-download]")) {
      closeApplicationDownloadDialog();
      return;
    }
    if (event.target.closest("[data-download-application-again]")) {
      downloadGeneratedApplicationPacketAgain();
    }
  });
  $("#application-download-dialog").addEventListener("cancel", (event) => {
    event.preventDefault();
    closeApplicationDownloadDialog();
  });
  $("#application-review-preview").addEventListener("click", (event) => {
    const refresh = event.target.closest("[data-refresh-application-preview]");
    if (refresh) refreshApplicationReviewPreview(refresh.dataset.refreshApplicationPreview);
  });
  $("#application-review-preview").addEventListener("change", async (event) => {
    const review = event.target.closest("[data-application-review-template]");
    if (!review) return;
    const template = applicationTemplateById(review.dataset.applicationReviewTemplate);
    if (!template) return;
    if (review.checked) {
      if (!collectApplicationDocumentForm({ invalidateReview: false })) {
        review.checked = false;
        return;
      }
      review.disabled = true;
      const preview = await refreshApplicationReviewPreview(template.id);
      if (
        !preview
        || preview.missing_required_fields?.length
        || preview.invalid_attachment_fields?.length
      ) {
        review.checked = false;
        return;
      }
      const existing = state.applicationSelections[template.id] || {
        selected: true,
        copies: template.default_copies,
        status: "draft",
      };
      state.applicationSelections[template.id] = {
        ...existing,
        selected: true,
        status: existing.status === "draft" ? "ready_to_print" : existing.status,
        reviewed_version: template.version,
        reviewed_content_sha256: preview.review_content_sha256,
        reviewed_at: new Date().toISOString(),
      };
      announce(`${template.short_title}已完成目前內容核對`, "success");
    } else {
      invalidateApplicationReview(template.id, { persist: false, render: false });
    }
    persistApplicationContext();
    renderApplicationReviewPreview(template);
    renderApplicationTemplates();
    renderApplicationPacket();
    updateApplicationCenterSteps();
    const progress = $("#application-form-print-guide")?.querySelector(
      `[data-application-status-template="${template.id}"]`,
    );
    if (progress) progress.value = applicationDocumentStatus(template.id);
    const next = $("#application-document-next-step");
    if (next) next.textContent = applicationDocumentNextStep(template);
    const download = $("#download-single-application-document");
    if (download) download.disabled = !applicationTemplateCompletion(template).ready || !applicationTemplateReviewed(template);
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

  $("#private-vault-form").addEventListener("submit", submitPrivateVault);
  $("#private-vault-file").addEventListener("change", (event) => {
    const file = event.currentTarget.files?.[0];
    state.useGeneratedVaultCandidate = false;
    $("#private-vault-file-name").textContent = file?.name || "選擇私人文件";
    $("#private-vault-file-meta").textContent = file
      ? `${formatVaultBytes(file.size)} · 尚未保存`
      : "PDF、DOCX、TXT、JPG、PNG 或 WebP，20 MB 以內";
    renderGeneratedVaultCandidate();
  });
  $("#private-vault-cancel-version").addEventListener("click", () => resetPrivateVaultForm());
  $("#private-vault").addEventListener("click", (event) => {
    if (event.target.closest("[data-private-vault-login]")) {
      openAuthDialog();
      return;
    }
    if (event.target.closest("[data-use-generated-vault]")) {
      useGeneratedVaultCandidate();
      return;
    }
    if (event.target.closest("[data-private-vault-retry]")) {
      loadPrivateVault({ quiet: false });
      return;
    }
    const newVersion = event.target.closest("[data-private-vault-new-version]");
    if (newVersion) {
      beginPrivateVaultVersion(newVersion.dataset.privateVaultNewVersion);
      return;
    }
    const download = event.target.closest("[data-private-vault-download]");
    if (download) {
      downloadPrivateVaultVersion(download.dataset.privateVaultDownload, download);
      return;
    }
    const deleteVersion = event.target.closest("[data-private-vault-delete-version]");
    if (deleteVersion) {
      deletePrivateVaultVersion(
        deleteVersion.dataset.privateVaultDocument,
        deleteVersion.dataset.privateVaultDeleteVersion,
      );
      return;
    }
    const deleteDocument = event.target.closest("[data-private-vault-delete-document]");
    if (deleteDocument) deletePrivateVaultDocument(deleteDocument.dataset.privateVaultDeleteDocument);
  });

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
    if (event.target.closest("[data-life-student-search]")) {
      const item = partnerByName(state.activeSchool);
      activateDetailTab("detail-experiences", { focus: true, scroll: true });
      if (item) loadStudentExperiences(item, { forceRefresh: true });
      return;
    }
    if (event.target.closest("[data-refresh-life-context]")) {
      await loadSchoolLifeContext(partnerByName(state.activeSchool), { refresh: true });
      return;
    }
    if (event.target.closest("[data-open-submission-auth]")) {
      openAuthDialog();
      return;
    }
    const submissionAction = event.target.closest("[data-submission-action]");
    if (submissionAction) {
      await handleSubmissionProgressAction(submissionAction);
      return;
    }
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
    const deletePost = event.target.closest("[data-delete-post]");
    if (deletePost) {
      if (await deleteCommunityResource(`/community/posts/${encodeURIComponent(deletePost.dataset.deletePost)}`, "確定要刪除這篇貼文與全部留言嗎？")) await refreshCommunityHub("posts");
      return;
    }
    const deleteComment = event.target.closest("[data-delete-comment]");
    if (deleteComment) {
      if (await deleteCommunityResource(`/community/posts/${encodeURIComponent(deleteComment.dataset.postId)}/comments/${encodeURIComponent(deleteComment.dataset.deleteComment)}`, "確定要刪除這則留言嗎？")) await refreshCommunityHub("posts");
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
    const workflowIssueReport = event.target.closest("[data-workflow-issue-report]");
    if (workflowIssueReport) {
      openWorkflowIssueReport(workflowIssueReport);
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
    if (event.target.closest("[data-open-planning]")) { event.preventDefault(); openPlanningWorkspace(); return; }
    if (event.target.closest("[data-open-manual-task]")) {
      const open = () => { $(".calendar-quick-add").open = true; $("#calendar-event-form input[name=title]").focus(); };
      if (window.location.hash === "#calendar") open();
      else { window.addEventListener("hashchange", ()=>requestAnimationFrame(open), {once:true}); window.location.hash = "#calendar"; }
      return;
    }
    const copyInquiry = event.target.closest("[data-copy-application-inquiry]");
    if (copyInquiry) {
      const inquiry = copyInquiry.closest(".application-inquiry");
      navigator.clipboard.writeText(inquiry.querySelector("textarea").value).then(()=>{
        inquiry.querySelector(".inquiry-copy-status").textContent = "已複製；請自行確認後向校方詢問。";
      }).catch(()=>{
        inquiry.querySelector("textarea").select();
        inquiry.querySelector(".inquiry-copy-status").textContent = "請按 Ctrl+C 或使用裝置的複製功能。";
      });
      return;
    }
    if (event.target.closest("[data-retry-application-catalog]")) { loadApplicationTemplates(); return; }
    const planningTarget = event.target.closest("[data-planning-target]");
    if (planningTarget) { selectPlanningTarget(planningTarget.dataset.planningTarget); return; }
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
    if (event.target.closest("[data-open-verification]")) {
      openProfileDialog();
      return;
    }
    if (event.target.closest("[data-open-global-community-composer]")) {
      if (
        document.body.classList.contains("global-home-mode")
        || document.body.classList.contains("cgu-community-mode")
      ) {
        openGlobalCommunityComposer();
        return;
      }
      if (state.activeSchool) closeUniversityDetail({ updateHistory: false });
      window.location.hash = "#public-board";
      window.setTimeout(openGlobalCommunityComposer, 80);
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
    const identitySelect = event.target.closest("[data-community-identity-select]");
    if (identitySelect) {
      updateCommunityIdentityPreview(identitySelect);
      return;
    }
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
  window.addEventListener("online", handleAccountConnectivityRestored);
  window.addEventListener("offline", renderAccountWorkspaceSyncStatus);
  window.addEventListener("online", retryPendingApplicationFormDrafts);
}

async function boot() {
  if (!window.location.hash || window.location.hash === "#community-hub") {
    window.UniWayNavigation.replaceState({}, "", new URLSearchParams(window.location.search).has("view") ? "#partners" : window.location.hash ? "#forum" : "#home");
  }
  initializeTheme();
  readStoredState();
  readPartnerUrl();
  window.__uniwayCurrentSchool = () => state.activeSchool || "";
  window.UniWayAnalytics?.setContextProvider(() => ({
    school: activeHomeSchool(),
    signedIn: Boolean(state.account),
    schoolBasis: state.account?.school_basis || "",
  }));
  window.UniWayApplicationWorkspace.init();
  window.UniWayDocumentWorkbench.init();
  renderAccountState();
  initDiscussionReader();
  applyAppRoute({ loadFeed: false, resetScroll: false });
  bindEvents();
  window.UniWayJourney.bind();
  initDiscovery();
  renderGlobalCommunityTopics();
  renderGlobalCommunityIdentitySelector();
  initIcons();
  await Promise.all([loadSupportedUniversities(), loadAuthProviders(), restoreAccount(), loadSchoolImages(), loadAdvisorStatus()]);
  if (state.pendingSchoolPrompt) {
    state.pendingSchoolPrompt = false;
    promptForAccountSchool();
  }
  const sharedHome = new URLSearchParams(window.location.search).get("home");
  if (sharedHome && state.supportedUniversities.some((item) => item.school_name === sharedHome)) setHomeSchool(sharedHome, { reload: false });
  aiStatusManager.start(30000);
  await loadDashboard();
  await loadApplicationTemplates();
  applyAppRoute({ loadFeed: false, resetScroll: false });
  if (isPersonalizedRoute() && !state.homeSchool) initializeSchoolOnboarding();
  // The loading screen stays until the page is completely ready, so nothing inside it is still "loading" when it goes.
  // These four do not depend on each other, so they run together (one failing does not hold the others back).
  await Promise.allSettled([loadGlobalCommunity(), loadCoverage(), loadDestinationProfiles(), state.periodOptionsReady]);
  const route = window.location.hash.match(/^#school=(.+)$/);
  if (route) {
    const item = partnerByName(decodeURIComponent(route[1]));
    if (item) openUniversityDetail(item, { updateHistory: false });
  }
}

// The loading screen goes when starting is over, however it ended; it can never stay in front of the page for good.
boot().finally(() => window.UniWaySplash?.done());
