/* Shared, DOM-free rules for the selection workspace. Never infer admission. */
(function (root) {
  "use strict";
  const THEMES = { housing: "住宿", food: "吃飯", transport: "交通", academics: "課業", cost: "費用", visa: "簽證", social: "交流", climate: "氣候", safety: "醫療與安全", travel: "旅行", campus_culture: "校園", support: "支援", career: "職涯", challenges: "挑戰" };
  const empty = () => ({ school_preferences: {}, preference_order: [], saved_experiences: {}, recent_views: [] });
  const text = (value, max = 1000) => typeof value === "string" ? value.trim().slice(0, max) : "";
  const record = value => value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const safeUrl = value => { try { const u = new URL(value); return ["https:", "http:"].includes(u.protocol) && !u.username && !u.password ? u.href : ""; } catch { return ""; } };
  function sourceKey(source) { return `${text(source.school_name, 240)}::${safeUrl(source.source_url)}`; }
  function sourceSnapshot(source) {
    return { school_name: text(source.school_name, 240), country: text(source.country, 100), title: text(source.title, 500), source_url: safeUrl(source.source_url),
      summary: text(source.summary, 1500), summary_zh: text(source.summary_zh, 1500), original_summary: text(source.original_summary, 1500),
      exchange_term: text(source.exchange_term, 120), published_at: text(source.published_at, 100), language: text(source.language, 40), source_type: text(source.source_type, 40),
      translation_status: text(source.translation_status, 40), themes: Array.isArray(source.themes) ? source.themes.filter(t => THEMES[t]).slice(0, 14) : [],
      theme_summaries: Object.fromEntries(Object.entries(record(source.theme_summaries)).filter(([t]) => THEMES[t]).map(([k,v]) => [k,text(v,1500)])),
      theme_summaries_zh: Object.fromEntries(Object.entries(record(source.theme_summaries_zh)).filter(([t]) => THEMES[t]).map(([k,v]) => [k,text(v,1500)])) };
  }
  function sanitize(value) {
    const v = record(value), result = empty();
    for (const [name, pref] of Object.entries(record(v.school_preferences)).slice(0, 500)) {
      if (!text(name, 240) || ["__proto__", "constructor", "prototype"].includes(name)) continue;
      result.school_preferences[text(name, 240)] = { interest: Math.max(0, Math.min(5, Math.floor(Number(pref?.interest) || 0))), note: text(pref?.note, 1000) };
    }
    result.preference_order = [...new Set((Array.isArray(v.preference_order) ? v.preference_order : []).map(x => text(x, 240)).filter(Boolean))].slice(0, 30);
    for (const source of Object.values(record(v.saved_experiences)).slice(0, 300)) {
      const s = sourceSnapshot(record(source));
      if (s.school_name && s.source_url) result.saved_experiences[sourceKey(s)] = s;
    }
    const seen = new Set();
    for (const row of (Array.isArray(v.recent_views) ? v.recent_views : [])) {
      const s = sourceSnapshot(record(row)), kind = row?.kind === "experience" ? "experience" : "school";
      const key = `${kind}:${kind === "school" ? s.school_name : sourceKey(s)}`;
      if (!s.school_name || seen.has(key) || kind === "experience" && !s.source_url) continue;
      seen.add(key); result.recent_views.push({ ...s, kind, viewed_at: text(row.viewed_at, 40) });
      if (result.recent_views.length >= 20) break;
    }
    return result;
  }
  function hasCriteria(c = {}) { return Boolean(c.test || c.score || c.grade || c.degree || c.term); }
  const number = value => value !== "" && value != null && Number.isFinite(Number(value)) ? Number(value) : null;
  const tests = {
    ielts: /IELTS\s*(?:overall|總分|至少|達|[≥:：])?\s*(\d(?:\.\d)?)/ig,
    toefl: /(?:TOEFL(?:\s*[- ]?iBT)?|托福)\s*(?:總分|至少|達|[≥:：])?\s*(\d{2,3})/ig,
    toeic: /(?:TOEIC|多益)\s*(?:總分|至少|達|[≥:：])?\s*(\d{3})/ig,
    duolingo: /Duolingo\s*(?:總分|至少|達|[≥:：])?\s*(\d{2,3})/ig,
    jlpt: /(?:JLPT|日檢|日語能力|日本語能力)[^。;；\n]{0,20}?N\s*([1-5])/ig,
    topik: /TOPIK\s*(?:第|level)?\s*([1-6])/ig,
  };
  function assessOption(item, c) {
    const outcomes = [], reasons = [];
    const put = (status, reason) => { outcomes.push(status); reasons.push(reason); };
    const raw = [item.eligibility, ...(item.student_summary_zh?.eligibility_points || [])].filter(Boolean).join("；");
    const ambiguous = /(?:小分|單科|各科|each\s+(?:band|section)|subscore|系所|限.*系|另須|另外需|depending|視.*科系|CEFR|大[二三四]|學分|credits)/i.test(raw);
    if (c.test || c.score) {
      const score = number(c.score), pattern = tests[c.test];
      const values = pattern ? [...raw.matchAll(new RegExp(pattern.source, "ig"))].map(m => Number(m[1])) : [];
      const unique = [...new Set(values)];
      const exams = [...new Set((raw.match(/IELTS|TOEFL|TOEIC|Duolingo|JLPT|TOPIK|日檢/ig) || []).map(s => s.toUpperCase()))];
      const combinedExams = exams.length > 1 && !/或|\bor\b/i.test(raw);
      if (score == null || !pattern) put("unknown", "語言成績未填完整");
      else if (!unique.length) put("unknown", "此檢定門檻待確認");
      else if (unique.length > 1 || ambiguous || combinedExams || /TOEFL\s*(?:ITP|PBT)/i.test(raw) && c.test === "toefl") put("unknown", "語言條件依方案或單科而異");
      else {
        const threshold = unique[0], met = c.test === "jlpt" ? score <= threshold : score >= threshold;
        const otherLanguage = /\b(?:IELTS|TOEFL|TOEIC|Duolingo|JLPT|TOPIK)\b|日檢/i;
        const hasAlternative = /或|\bor\b/i.test(raw) && otherLanguage.test(raw);
        put(met ? "match" : hasAlternative ? "unknown" : "mismatch", `${c.test.toUpperCase()} ${c.test === "jlpt" ? "N" : ""}${threshold}${met ? "，已達門檻" : hasAlternative ? "，可再核對其他檢定" : "，尚未達門檻"}`);
      }
    }
    if (c.grade) {
      const score = number(c.grade), scale = Number(c.scale || 100);
      const gpa = [...new Map([...raw.matchAll(/GPA\s*(?:至少|達|[≥:：])?\s*(\d(?:\.\d+)?)\s*(?:\/|out of\s*)\s*(4(?:\.0|\.3)?|5(?:\.0)?)/ig)].map(m => [`${Number(m[1])}:${Number(m[2])}`, m])).values()];
      const average = raw.match(/(?:平均(?:成績)?|學業成績|百分制)[^。；;\d]{0,8}(\d{2}(?:\.\d+)?)\s*(?:分|以上|[（(]百分)/);
      if (score == null || score > scale || score < 0) put("unknown", "請核對成績與滿分制");
      else if (gpa.length === 1 && Number(gpa[0][2]) === scale) put(score >= Number(gpa[0][1]) ? "match" : "mismatch", `GPA ${gpa[0][1]} / ${scale}`);
      else if (average && scale === 100) put(score >= Number(average[1]) ? "match" : "mismatch", `平均 ${average[1]} 分`);
      else put("unknown", "成績門檻或計分制待確認");
    }
    if (c.degree) {
      const degree = item.degree_levels || "";
      if (!degree || /依|確認|不限|全校/.test(degree)) put("unknown", "適用學制待確認");
      else {
        const eligible = c.degree === "undergraduate" ? /大學部|學士|undergraduate|bachelor/i.test(degree) : /研究所|碩士|博士|graduate|master/i.test(degree.replace(/undergraduate/ig, ""));
        put(eligible ? "match" : "mismatch", eligible ? "學制符合" : "未列此學制");
      }
    }
    if (c.term) {
      const term = item.study_period || "";
      const spring = /春季|下學期|spring/i.test(term), fall = /秋季|上學期|fall|autumn/i.test(term);
      if (!spring && !fall) put("unknown", "開放交換學期待確認");
      else put((c.term === "spring" ? spring : fall) ? "match" : "mismatch", term);
    }
    const status = outcomes.includes("mismatch") ? "mismatch" : outcomes.includes("unknown") || !outcomes.length ? "unknown" : "match";
    return { status, reasons, label: { match: "已知門檻符合", unknown: "條件待確認", mismatch: "有條件未符" }[status] };
  }
  function assess(item, c = {}) {
    if (!hasCriteria(c)) return { status: "none", reasons: [], label: "" };
    const options = item.program_options?.length ? item.program_options.map(o => assessOption({ ...item, ...o, student_summary_zh: o.student_summary_zh || {} }, c)) : [assessOption(item, c)];
    let result = options.find(o => o.status === "match") || options.find(o => o.status === "unknown") || options[0];
    if (item.availability_status && item.availability_status !== "open" && result.status === "match") result = { ...result, status: "unknown", label: "條件待確認", reasons: [...result.reasons, "本期開放狀態待確認"] };
    return result;
  }
  const api = { THEMES, empty, sanitize, sourceKey, sourceSnapshot, safeUrl, hasCriteria, assess };
  root.UniWayDiscovery = api;
  if (typeof module !== "undefined") module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
