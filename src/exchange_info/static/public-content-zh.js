/* Translate public reading content only. Never touch IDs, forms, user data or URLs. */
(function (root) {
  "use strict";
  const routes = new Set(["/student-dashboard", "/exchange-info", "/destination-profile", "/destination-profiles",
    "/destination-profile/refresh", "/school-life-context", "/school-life-context/refresh",
    "/student-experiences", "/student-experiences/refresh", "/application-workflow"]);
  const fields = new Set(["title", "summary", "description", "detail", "details", "text",
    "points", "key_points", "eligibility_points", "application_steps", "tuition_points", "ranking_info",
    "cost_summary", "housing_summary", "transport_summary", "campus_life_summary",
    "location_note", "research_notes", "coverage_note", "disclaimer", "caution", "note",
    "next_step", "limitation", "academic_score_rule", "requirements"]);
  const summaryFields = new Set(["study_period", "application_deadline", "eligibility_points", "application_steps", "tuition_points"]);
  const terms = /(?<![A-Za-z])(?:TOEIC|TOEFL(?:\s+(?:iBT|ITP|PBT))?|IELTS|Duolingo(?: English Test)?|DET|JLPT|TOPIK|CEFR|MCER|GPA|ECTS|SAT|GRE|GMAT|PTE|TEF|TCF|DELF|DALF|TestDaF|DSH|Cambridge English Qualification|Cambridge FCE|Linguaskill|FCE|CAE|COE|JYPE|COLABS|iBT|ITP|PBT|IBT|TOFEL|IELT|JPT|CSOM|CSE|SE-B|SE-G|SPACE|PDF|DOCX?|TXT|JPG|PNG|WebP|QS|THE|MBA|BBA|BA|MA|MSc|PhD|ESL|EAP|ASAP|UCI|NTNU|UWM|CGU|ETS|TA|AI|USD|EUR|TWD|JPY|KRW|AUD|CAD|NZD|CHF|GBP|[ABC][12]|N[1-5])(?:\b|(?=[\u4e00-\u9fff\d]))/gi;
  function normalizeTerms(value) {
    return String(value).split(/(https?:\/\/[^\s）)<>；，。！？「」『』【】]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})/g)
      .map((part, index) => index % 2 ? part : part.replace(/多益\s*(?:TOEIC)?/gi, "TOEIC")
        .replace(/\b(toeic|ielts|toefl|jlpt|topik|cefr)\b/gi, term => term.toUpperCase())).join("");
  }
  function needsTranslation(value) {
    let text = String(value).replace(/https?:\/\/[^\s）)<>]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "").replace(terms, "");
    text = text.replace(/\b(?:[A-Za-z0-9-]+\.)+(?:edu|ac|com|org|net|cz|jp|se|pl|uk|kr|vn|ro|tr|lt|cn|fr|it|es|de|ca)(?:\.[A-Za-z]{2,})*\b/g, "")
      .replace(/\b[\w.-]+\.(?:pdf|docx?|xlsx?)\b/gi, "")
      .replace(/\b(?:iCLA|CROUS|Crous|CVEC|UNIST|MSU|KNU|ERICA|EDHEC|HSUHK|KEDGE|UNYP|VSB-TUO|BTH|KMUTT|KMITL|EIGSI|SKEMA|ESCA|UFE|VUT|BUT|PUT|WUT|UNIPO|ISIC|FAQ|LAC|Erasmus|T-money|EZL|LAN|VPN)\b/g, "");
    if ([...text].some(char => /\p{L}/u.test(char) && !/[\p{Script=Han}\p{Script=Latin}]/u.test(char))) return true;
    const han = (text.match(/[\u3400-\u9fff]/gu) || []).length;
    if (han >= 4) {
      text = text.replace(/\b(?:[A-ZÀ-Þ][a-zà-öø-ÿ]+(?:\s+|$)){2,}/g, "").replace(/\b[A-ZÀ-Þ][A-Za-zÀ-ÿ]*\b/g, "");
    } else if (han) {
      text = text.replace(/(?<![A-Za-z])[A-Z]{2,10}(?![A-Za-z])/g, "");
    }
    text = text.replace(/\b(?:eSIM|SIM|Wi-Fi|fact\s*sheet|factsheet)\b/gi, "");
    if (/^[\w.-]+\.(?:pdf|docx?|xlsx?)$/i.test(String(value))) return false;
    return /[A-Za-z\u00c0-\u024f]{2,}/u.test(text);
  }
  function collect(data) {
    const targets = [];
    function add(parent, key, source, statusOwner) {
      if (typeof parent[key] !== "string") return;
      parent[key] = normalizeTerms(parent[key]);
      if (!needsTranslation(parent[key])) return;
      if (parent[key].length <= 1800) {
        targets.push({ parent, key, text: parent[key], source_url: source, statusOwner });
        return;
      }
      // Keep long source paragraphs complete without exceeding the local model's input bound.
      const group = { parent, key, parts: [] };
      let remaining = parent[key];
      while (remaining.length) {
        let end = Math.min(1800, remaining.length);
        if (end < remaining.length) {
          const prefix = remaining.slice(0, end);
          const boundary = Math.max(prefix.lastIndexOf("。"), prefix.lastIndexOf("；"), prefix.lastIndexOf("\n"), prefix.lastIndexOf(" "));
          if (boundary > 900) end = boundary + 1;
        }
        const text = remaining.slice(0, end), index = group.parts.push(text) - 1;
        if (needsTranslation(text)) targets.push({ parent: group.parts, key: index, text, source_url: source, statusOwner, group });
        remaining = remaining.slice(end);
      }
    }
    function visit(node, source = "", section = "") {
      if (!node || typeof node !== "object") return;
      if (Array.isArray(node)) { node.forEach((item, i) => typeof item === "string" ? add(node, i, source) : visit(item, source, section)); return; }
      source = node.source_url || node.sources?.[0]?.url || node.sources?.[0]?.source_url || node.source?.url || source;
      if (node.kind && Array.isArray(node.sources)) add(node, "scope", source);
      if (Object.hasOwn(node, "summary_zh")) {
        node.summary_zh ||= node.summary || "";
        add(node, "summary_zh", source, node);
      }
      if (node.theme_summaries && node.theme_summaries_zh) {
        for (const [theme, text] of Object.entries(node.theme_summaries)) node.theme_summaries_zh[theme] ||= text;
      }
      for (const [key, value] of Object.entries(node)) {
        if (key.startsWith("original_") || ["summary_zh", "theme_summaries", "school_name", "country", "city", "english_name", "colleges", "degree_levels"].includes(key)) continue;
        if (key === "summary" && Object.hasOwn(node, "summary_zh")) continue;
        if (typeof value === "string") {
          if (fields.has(key) || section === "theme_summaries_zh" || section === "student_summary_zh" && summaryFields.has(key)) add(node, key, source, key === "text" ? node : null);
        } else if (Array.isArray(value)) {
          if (fields.has(key) || summaryFields.has(key)) visit(value, source, key);
          else value.filter(item => item && typeof item === "object").forEach(item => visit(item, source, key));
        } else if (value && typeof value === "object") visit(value, source, key);
      }
    }
    visit(data);
    return targets;
  }
  const cache = new Map();
  let generationEnabled = true;
  const keyOf = row => JSON.stringify([row.text, row.source_url]);
  async function request(entries, generate) {
    const response = await fetch("/public-translations", { method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ entries, generate }), signal: AbortSignal.timeout(35000) });
    if (!response.ok) throw new Error("中文翻譯暫時無法使用");
    const result = await response.json();
    if (result.generation_enabled === false) generationEnabled = false;
    result.entries.forEach((row, index) => { if (row.zh && row.status !== "pending") cache.set(keyOf(entries[index]), row); });
  }
  async function localize(url, data) {
    if (!routes.has(String(url).split("?")[0]) || !data) return data;
    const localized = structuredClone(data), targets = collect(localized);
    const entries = [...new Map(targets.map(row => [keyOf(row), { text: row.text, source_url: row.source_url }])).values()];
    try {
      for (let i = 0; i < entries.length; i += 160) {
        const batches = [];
        for (let j = i; j < Math.min(entries.length, i + 160); j += 40) batches.push(request(entries.slice(j, j + 40), false));
        await Promise.all(batches);
      }
      const missing = entries.filter(row => !cache.has(keyOf(row)));
      // Small batches bound local model input; subsequent loads reuse the source-bound cache.
      for (let i = 0; generationEnabled && i < missing.length;) {
        const batch = [missing[i++]];
        while (i < missing.length && batch.length < 4 && batch.reduce((sum, row) => sum + row.text.length, missing[i].text.length) <= 2400) batch.push(missing[i++]);
        await request(batch, true);
      }
    } catch (_) { /* A failed translation must not be presented as translated evidence. */ }
    for (const row of targets) {
      const result = cache.get(keyOf(row));
      // New or temporarily unavailable translations must not erase source facts.
      row.parent[row.key] = result?.zh || row.text;
      if (row.statusOwner && result) row.statusOwner.translation_status = result.status;
      else if (row.statusOwner) row.statusOwner.translation_status = "pending";
    }
    for (const group of new Set(targets.map(row => row.group).filter(Boolean))) group.parent[group.key] = group.parts.join("");
    return localized;
  }
  const api = { localize, collect, needsTranslation, normalizeTerms };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.UniWayChinese = api;
})(typeof window === "undefined" ? {} : window);
