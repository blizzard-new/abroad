/* One document, one set of forms. Legacy routes borrow the same tool nodes. */
window.UniWayDocumentWorkbench = (() => {
  let root, context = "", mounted = false;
  const borrowed = [];
  const panes = ["edit", "check", "vault", "source"];
  const key = () => JSON.stringify([state.account?.id, state.authSessionEpoch, state.homeSchool, state.applicationContext, state.activeApplicationTemplateId]);

  function move(node, host) {
    if (!node || !host) return;
    const anchor = document.createComment(`document-workbench:${node.id || "guide"}`);
    node.before(anchor);
    borrowed.push({node, anchor, host});
  }

  function init() {
    root = document.querySelector("#document-workbench");
    if (!root) return;
    move(document.querySelector("#document-check-gate"), root.querySelector('[data-document-pane="check"]'));
    move(document.querySelector("#document-check-content"), root.querySelector('[data-document-pane="check"]'));
    move(document.querySelector("#private-vault"), root.querySelector('[data-document-pane="vault"]'));
    root.addEventListener("click", event => {
      const tab = event.target.closest("[data-document-tab]");
      if (tab) select(tab.dataset.documentTab);
      if (event.target.closest("[data-check-generated-document]")) useGeneratedCheck();
      const stage = event.target.closest("[data-flow-stage]");
      if (stage && !event.target.closest("#document-flow-skip")) runFlowStage(stage.dataset.flowStage);
      const skip = event.target.closest("#document-flow-skip");
      if (skip && skip.dataset.flowStage) { skipped.add(skip.dataset.flowStage); renderFlow(); }
    });
    root.querySelector('[role="tablist"]').addEventListener("keydown", event => {
      const tab = event.target.closest("[data-document-tab]");
      if (!tab || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const index = panes.indexOf(tab.dataset.documentTab);
      const next = event.key === "Home" ? 0 : event.key === "End" ? panes.length - 1
        : (index + (event.key === "ArrowRight" ? 1 : -1) + panes.length) % panes.length;
      select(panes[next]);
      root.querySelector(`[data-document-tab="${panes[next]}"]`).focus();
    });
    document.querySelector(".application-form-guide").addEventListener("change", event => {
      const input = event.target.closest("[data-application-status-template]");
      if (!input) return;
      const template = applicationTemplateById(input.dataset.applicationStatusTemplate);
      if (!template) return;
      state.applicationSelections[template.id] = {...state.applicationSelections[template.id], status:input.value};
      persistApplicationContext();
      document.querySelector("#application-document-next-step").textContent = applicationDocumentNextStep(template);
      renderFlow();
    });
  }

  function route(page) {
    if (!root) return;
    mounted = page === "application-form";
    borrowed.forEach(({node, anchor, host}) => {
      if (mounted) host.append(node);
      else anchor.after(node);
    });
    // A check selected for a particular template never follows a legacy tool link.
    if (!mounted && context) {
      context = "";
      resetDocumentCheck();
      resetPrivateVaultForm();
    }
    if (!mounted && page !== "document-check" && state.documentCheckLoading) resetDocumentCheck();
  }

  function open(template) {
    if (!root || !template) return;
    const next = key();
    if (next !== context) {
      context = next;
      skipped.clear();
      resetDocumentCheck();
      resetPrivateVaultForm();
      select("edit");
    }
    if (state.documentCheckGeneratedCandidate && !candidateCurrent(state.documentCheckGeneratedCandidate)) resetDocumentCheck();
    if (state.useGeneratedVaultCandidate && !candidateCurrent()) resetPrivateVaultForm();
    root.querySelector("#document-workbench-context").textContent =
      [state.homeSchool, state.applicationContext.academic_year && `${state.applicationContext.academic_year} 學年度`,
        state.applicationContext.application_round, template.short_title || template.title].filter(Boolean).join(" · ");
    renderGenerated();
    renderFlow();
  }

  // One progress model for the whole document: fill -> review -> PDF -> check ->
  // keep -> submit. It reads existing state only and never marks anything sent.
  const skipped = new Set();
  const SENT_STATUSES = ["pending_signature", "pending_department_stamp", "pending_submission", "completed"];
  function flowStages(template) {
    const completion = applicationTemplateCompletion(template);
    const reviewed = applicationTemplateReviewed(template);
    const candidate = currentDocumentCandidate();
    const status = applicationDocumentStatus(template.id);
    const downloaded = Boolean(candidate) || SENT_STATUSES.includes(status);
    const kept = Object.values(state.applicationFileVaultLinks?.[template.id] || {}).some(list => (list || []).length);
    return [
      {id:"fill", label:"填寫必填欄位", done:completion.ready,
        detail:completion.ready ? "必填欄位都有內容" : `已填 ${completion.completed} / ${completion.total} 項必填`},
      {id:"review", label:"逐欄核對", done:reviewed,
        detail:reviewed ? "已核對目前內容" : completion.ready ? "請核對預覽並勾選我已核對" : "先完成必填欄位"},
      {id:"download", label:"下載列印 PDF", done:downloaded,
        detail:downloaded ? "已產生過 PDF" : reviewed ? "可下載並依份數列印" : "核對後才能下載"},
      {id:"check", label:"檢查成品", done:Boolean(state.documentCheckResult), optional:true,
        detail:state.documentCheckResult ? "已有本次檢查結果" : "選擇性：用規則檢查簽名與完整度"},
      {id:"vault", label:"私人保存", done:kept, optional:true,
        detail:kept ? "已連結私人文件庫的檔案" : "選擇性：逐檔同意後加密保存"},
      {id:"submit", label:"簽名、核章與送件", done:status === "completed",
        detail:status === "completed" ? "你已標示完成（非校方受理）" : applicationDocumentNextStep(template)},
    ];
  }
  function flowCurrent(stages, downloaded) {
    return stages.find(stage => !stage.done && (!stage.optional || (downloaded && !skipped.has(stage.id))));
  }
  function renderFlow() {
    const list = root?.querySelector("#document-flow-steps");
    const template = applicationTemplateById(state.activeApplicationTemplateId);
    if (!list || !template) return;
    const stages = flowStages(template);
    const downloaded = stages[2].done;
    const current = flowCurrent(stages, downloaded);
    list.innerHTML = stages.map((stage, index) => {
      const flowState = stage.done ? "done" : stage === current ? "current" : stage.optional ? "optional" : "todo";
      const label = {done:"已完成", current:"下一步", optional:"可選", todo:"稍後"}[flowState];
      return `<li><button type="button" data-flow-stage="${stage.id}" data-flow-state="${flowState}" ${stage === current ? 'aria-current="step"' : ""}><span class="document-flow-state-label">${index + 1} · ${label}</span><strong>${escapeHtml(stage.label)}</strong><small>${escapeHtml(stage.detail)}</small></button></li>`;
    }).join("");
    const next = root.querySelector("#document-flow-next"), skip = root.querySelector("#document-flow-skip");
    const allDone = stages.every(stage => stage.done || stage.optional);
    next.dataset.flowStage = current ? current.id : "submit";
    next.textContent = current ? `下一步：${current.label}` : allDone ? "回到來源與送件確認" : "繼續";
    skip.hidden = !(current && current.optional);
    skip.dataset.flowStage = current?.id || "";
    root.querySelector("#document-flow-note").textContent = `${stages.filter(stage => stage.done).length} / ${stages.length} 步`;
  }
  function runFlowStage(id) {
    const template = applicationTemplateById(state.activeApplicationTemplateId);
    if (!template) return;
    if (id === "fill") {
      select("edit");
      const field = template.fields.find(item => applicationFieldRequired(template, item) && !applicationFieldHasValue(template, item));
      const input = field ? document.querySelector(`#application-document-fields [data-application-field="${CSS.escape(field.id)}"]`) : document.querySelector("#application-document-fields input, #application-document-fields textarea, #application-document-fields select");
      input?.focus(); input?.scrollIntoView({block:"center", behavior:window.UniWayMotion?.reduced ? "instant" : "smooth"});
    } else if (id === "review") {
      select("edit");
      const box = document.querySelector("#application-review-preview");
      box?.scrollIntoView({block:"center", behavior:window.UniWayMotion?.reduced ? "instant" : "smooth"});
      box?.querySelector("input, button")?.focus();
    } else if (id === "download") {
      select("edit");
      const button = document.querySelector("#download-single-application-document");
      if (button && !button.disabled) button.click();
      else runFlowStage(applicationTemplateCompletion(template).ready ? "review" : "fill");
    } else if (id === "check") {
      if (currentDocumentCandidate()) generatedAction("check"); else select("check");
    } else if (id === "vault") {
      if (currentDocumentCandidate()) generatedAction("vault"); else select("vault");
    } else if (id === "submit") {
      select("source");
      document.querySelector("[data-application-status-template]")?.focus();
    }
    renderFlow();
  }

  function select(pane) {
    if (!root || !panes.includes(pane)) return;
    root.querySelectorAll("[data-document-tab]").forEach(tab => {
      const selected = tab.dataset.documentTab === pane;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    root.querySelectorAll("[data-document-pane]").forEach(panel => { panel.hidden = panel.dataset.documentPane !== pane; });
    renderGenerated();
    renderFlow();
  }

  function fingerprint(templateId) {
    const template = applicationTemplateById(templateId);
    return JSON.stringify([state.applicationContext, template?.version, state.applicationProfile,
      templateId ? state.applicationAnswers[templateId] : state.applicationAnswers,
      applicationSelectionsPayload(templateId).map(item => [item.template_id, item.copies])]);
  }

  function candidateCurrent(candidate = state.generatedVaultCandidate) {
    return Boolean(candidate && authenticatedRequestContextIsCurrent(candidate.requestContext)
      && candidate.homeSchool === state.homeSchool && candidate.fingerprint === fingerprint(candidate.templateId || ""));
  }

  function currentDocumentCandidate() {
    const candidate = state.generatedVaultCandidate;
    return mounted && candidate?.templateId === state.activeApplicationTemplateId && candidateCurrent(candidate) ? candidate : null;
  }

  function vaultCandidate() {
    if (mounted) return currentDocumentCandidate();
    return candidateCurrent() ? state.generatedVaultCandidate : null;
  }

  function renderGenerated() {
    if (!root) return;
    const candidate = currentDocumentCandidate();
    const button = root.querySelector("[data-check-generated-document]");
    button.hidden = !candidate;
    root.querySelector("#document-generated-check-note").textContent = candidate
      ? `可直接使用剛下載的 ${candidate.fileName}；選擇後仍須另行同意傳送。`
      : "可選擇自己的成品；填寫並核對後下載 PDF，也能直接帶入這裡檢查。";
    renderGeneratedVaultCandidate();
  }

  function useGeneratedCheck() {
    const candidate = currentDocumentCandidate();
    if (!candidate) return;
    resetDocumentCheck();
    state.documentCheckGeneratedCandidate = candidate;
    document.querySelector("#document-check-file").required = false;
    document.querySelector("#document-upload-title").textContent = candidate.fileName;
    document.querySelector("#document-upload-meta").textContent = "使用剛下載的同一份 PDF；尚未傳送";
    document.querySelector("#document-check-status").textContent = "請閱讀並勾選本次檢查同意，再開始檢查。";
    document.querySelector("#document-check-consent").focus();
  }

  function generatedAction(pane) {
    if (!currentDocumentCandidate()) return;
    closeApplicationDownloadDialog();
    select(pane);
    if (pane === "check") useGeneratedCheck();
    if (pane === "vault") useGeneratedVaultCandidate();
  }

  function draftChanged(templateId) {
    if (templateId !== state.activeApplicationTemplateId) return;
    if (state.documentCheckGeneratedCandidate) resetDocumentCheck();
    if (state.useGeneratedVaultCandidate && !candidateCurrent()) resetPrivateVaultForm();
    renderGenerated();
  }

  function reset() {
    context = "";
    resetDocumentCheck();
    select("edit");
  }

  return {init, route, open, select, renderFlow, fingerprint, candidateCurrent, currentDocumentCandidate, vaultCandidate, generatedAction, draftChanged, renderGenerated, reset};
})();
