// Ordinal JLPT levels stay separate from numeric English examination scores.
(() => {
  let controller, generation = 0, timer;
  const field = id => document.getElementById(id);
  const levels = ['N1','N2','N3','N4','N5'];
  const number = id => {
    const raw = field(id)?.value;
    return raw === '' || raw === undefined ? null : Number(raw);
  };
  async function update() {
    const panel = field('tku-eligibility-check'), output = field('tku-eligibility-result');
    controller?.abort();
    const requestId = ++generation;
    if (!panel || panel.hidden) return;
    controller = new AbortController();
    output.textContent = '正在核對已知規則…';
    const year = field('eligibility-academic-year')?.value;
    const round = field('eligibility-application-round')?.value;
    const current = (!year || year === '2027-2028') && (!round || round === '日語組第二次甄選');
    const payload = {
      round_id:current ? 'jp-2027-2028-round-2' : `${year}/${round}`,
      partner_id:field('tku-eligibility-partner').value,
      academic_average:number('advisor-academic-score'),
      degree_level:field('advisor-degree')?.value || null,
      year_of_study:({'大一':1,'大二':2,'大三':3,'大四':4})[field('advisor-current-year')?.value] || null,
      jlpt_level:levels.includes(field('advisor-jlpt-level').value) ? field('advisor-jlpt-level').value : null,
    };
    try {
      const response = await fetch('/tku/eligibility-check', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload), signal:controller.signal,
      });
      if (!response.ok) throw new Error('規則查核暫時無法完成，請重新核對官方來源。');
      const result = await response.json();
      if (requestId !== generation || panel.hidden) return;
      const status = {pass:'符合已知門檻',fail:'未達已知門檻',needs_confirmation:'待確認'};
      output.dataset.languageStatus = result.language_status || 'needs_confirmation';
      output.dataset.applicationStatus = result.application_status;
      output.textContent = result.application_status === 'not_verified_new'
        ? '此年度／梯次尚未核實新版；不能沿用2027–2028日語二甄條件。'
        : `JLPT ${payload.jlpt_level || '待補'}，母校要求${result.jlpt_minimum || '另核對英語／豁免'}：${status[result.language_status] || '待確認'}。學業：${status[result.academic_status]}；學制／年級等母校已知條件：${status[result.home_status]}。校內已截止，不能新申請。${result.notes.join(' ')}`;
    } catch (error) {
      if (requestId === generation && !panel.hidden && error.name !== 'AbortError') output.textContent = error.message;
    }
  }
  window.UniWayTKU ||= {};
  window.UniWayTKU.renderEligibility = (home, profile) => {
    const show = home === '淡江大學';
    document.querySelectorAll('[data-tku-eligibility]').forEach(el => { el.hidden = !show; });
    const select = field('advisor-jlpt-level');
    if (!select) return;
    select.disabled = !show;
    if (profile) select.value = levels.includes(profile.jlptLevel) ? profile.jlptLevel : '';
    if (!show) { controller?.abort(); ++generation; field('tku-eligibility-result').textContent = ''; }
    else { clearTimeout(timer); timer = setTimeout(update, 0); }
  };
  const relevant = new Set(['advisor-degree','advisor-current-year','advisor-academic-score','advisor-jlpt-level',
    'tku-eligibility-partner','eligibility-academic-year','eligibility-application-round']);
  document.addEventListener('change', event => {
    if (relevant.has(event.target.id)) { clearTimeout(timer); timer = setTimeout(update, 150); }
  });
})();
