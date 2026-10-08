// CCU's reviewed language conditions. Source text never supplies a numeric fallback.
window.UniWayCcuLanguage = {
  assess(item, test, degreeLevel = null) {
    const note = item.language_review_note || "中正當期語言條件尚未完成結構化核對。";
    const unknown = {threshold:null,note};
    if (item.field_evidence?.language_requirement?.status !== "verified_current") return unknown;
    let rules = (item.language_conditions || []).filter(rule => rule.test === test);
    if (rules.some(rule => rule.degree_levels?.length)) {
      if (!degreeLevel) return unknown;
      const degreeAliases = {"大學部":["大學部","學士班","本科"],"碩士班":["碩士班","研究所"],"博士班":["博士班","研究所"]};
      rules = rules.filter(rule => !rule.degree_levels?.length || rule.degree_levels.some(level => (degreeAliases[level] || [level]).includes(degreeLevel)));
    }
    if (rules.length !== 1) return unknown;
    const rule = rules[0];
    if (rule.requirement_level !== "required" || rule.minimum_score == null || rule.scope_choice_required || rule.additional_conditions?.length || rule.track || rule.host_faculties?.length || rule.teaching_language) return unknown;
    return {threshold:rule.minimum_score,note};
  }
};
