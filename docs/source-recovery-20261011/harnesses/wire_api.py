from pathlib import Path
p=Path('src/exchange_info/api.py');s=p.read_text();s=s.replace('from .student_view import build_student_dashboard, fetch_partner_universities','from .student_view import build_student_dashboard\nfrom .cgu_catalogue import CatalogueView, create_cgu_catalogue')
s=s.replace('    partner_cache_lock = threading.Lock()','''    partner_cache_lock = threading.Lock()
    cgu_catalogue = None
    cgu_catalogue_lock = threading.Lock()

    def cgu_catalogue_view() -> CatalogueView:
        nonlocal cgu_catalogue
        if cgu_catalogue is None:
            with cgu_catalogue_lock:
                if cgu_catalogue is None:
                    cgu_catalogue = create_cgu_catalogue(resolved_data_dir)
                    app.state.cgu_catalogue = cgu_catalogue
        return cgu_catalogue.view()
''',1)
marker='''        if university.id == "tku":
            # Window state'''
s=s.replace(marker,'''        if university.id == CGU.id:
            view = cgu_catalogue_view()
            if view.source.status == "unavailable":
                raise HTTPException(status_code=503, detail="長庚合作校來源暫不可用，尚無可用的歷次資料；請稍後重試。", headers={"Retry-After": "60"})
            return apply_partner_research(view.partners, load_partner_research(resolved_data_dir), home_university=university.school_name, copy_nested=False)
        if university.id == "tku":
            # Window state''',1)
s=s.replace('else fetch_partner_universities()','else []',1)
s=s.replace('''                raw_files_dir=resolved_data_dir / "raw_files",
            )
            with dashboard_cache_lock:''','''                raw_files_dir=resolved_data_dir / "raw_files",
                fetch_partner_sheets=False,
            )
            with dashboard_cache_lock:''',1)
s=s.replace('''        # Building this one downloads the partner sheet and parses a dozen official PDFs:''','''        # The base dashboard parses official PDFs; partner rows are overlaid from the
        # shared source provider on every response, never retained in this cache.
        # Building this one parses a dozen official PDFs:''',1)
s=s.replace('''            return cached[2].model_copy(deep=True)
        return build_cached_dashboard(university, signature).model_copy(deep=True)''','''            base_dashboard = cached[2]
        else:
            base_dashboard = build_cached_dashboard(university, signature)
        view = cgu_catalogue_view()
        return base_dashboard.model_copy(deep=True, update={
            "partner_universities": apply_partner_research(view.partners, load_partner_research(resolved_data_dir), home_university=university.school_name, copy_nested=False),
            "catalogue_source": view.source,
        })''',1)
s=s.replace('''        for university in universities:
            for partner in partners_for_university(university):''','''        unavailable = None
        for university in universities:
            try:
                partners = partners_for_university(university)
            except HTTPException as error:
                if error.status_code != 503 or home_school:
                    raise
                unavailable = error
                continue
            for partner in partners:''',1)
s=s.replace('''        raise HTTPException(status_code=404, detail="這所學校不在目前支援大學的當期合作校名單中。")''','''        if unavailable:
            raise unavailable
        raise HTTPException(status_code=404, detail="這所學校不在目前支援大學的當期合作校名單中。")''',1)
p.write_text(s)
p=Path('src/exchange_info/static/index.html');s=p.read_text();s=s.replace('<div id="page-status" class="page-status" role="status" aria-live="polite"></div>','<div id="page-status" class="page-status" role="status" aria-live="polite"></div>\n        <aside id="catalogue-source-status" class="catalogue-source-status" role="status" aria-live="polite" hidden></aside>');p.write_text(s)
p=Path('src/exchange_info/static/app.js');s=p.read_text();s=s.replace('  state.partnerDataLoading = true;\n  state.partnerDataError = false;','  state.partnerDataLoading = true;\n  state.partnerDataError = false;\n  $("#catalogue-source-status").hidden = true;',1)
s=s.replace('function renderDashboard() {','''function catalogueSourceUnavailable() {
  return state.dashboard?.catalogue_source?.status === "unavailable";
}

function renderCatalogueSourceStatus() {
  const banner = $("#catalogue-source-status");
  const source = state.dashboard?.catalogue_source;
  banner.hidden = !source || activeHomeSchool() !== "長庚大學";
  if (banner.hidden) { banner.textContent = ""; return; }
  const time = source.last_success_at ? formatDate(source.last_success_at) : "尚無成功取得時間";
  const title = source.status === "unavailable" ? "長庚合作校來源暫不可用" : source.last_attempt_result === "failed" ? "長庚合作校來源暫不可用，保留歷次資料" : source.status === "retrieved" ? "長庚合作校來源已取得" : "長庚合作校使用歷次資料";
  banner.innerHTML = `<strong>${escapeHtml(title)}</strong><p>來源取得時間：${escapeHtml(time)}。取得時間不代表當期已核實；年度、名額與開放狀態請依原資料及官方公告確認。</p><a href="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554" target="_blank" rel="noopener">交換來源</a> · <a href="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533" target="_blank" rel="noopener">雙學位來源</a><button type="button" class="text-button" data-reload-catalogue>重新讀取來源狀態</button>`;
  banner.querySelector("[data-reload-catalogue]").addEventListener("click", () => loadDashboard({ refreshed: true }));
}

function renderDashboard() {''',1)
s=s.replace('  $("#coverage-rate").textContent = String(data.partner_universities.length);','  renderCatalogueSourceStatus();\n  $("#coverage-rate").textContent = catalogueSourceUnavailable() ? "—" : String(data.partner_universities.length);',1)
s=s.replace('''  if (!partners.length) {
    renderEmpty("#partner-table", "沒有符合的學校", "調整國家、學院、學制或關鍵字後再試一次。");''','''  if (!partners.length) {
    renderEmpty("#partner-table", catalogueSourceUnavailable() ? "合作校來源暫不可用" : "沒有符合的學校", catalogueSourceUnavailable() ? "尚無可用的歷次資料，請稍後重新讀取或前往官方來源確認。" : "調整國家、學院、學制或關鍵字後再試一次。");''',1)
# Counter is shared by list and map.
s=s.replace('function renderPartnerCount(total, shown) {','function renderPartnerCount(total, shown) {\n  if (catalogueSourceUnavailable()) { $("#partner-count").textContent = "來源暫不可用"; return; }',1)
p.write_text(s)
p=Path('src/exchange_info/static/styles.css');s=p.read_text();s+='''\n.catalogue-source-status { margin: 12px 0 20px; padding: 14px 18px; border: 1px solid #bfccd2; border-radius: 12px; background: #f3f7f8; color: #223e48; font-size: .875rem; overflow-wrap: anywhere; }
.catalogue-source-status[hidden] { display: none; }
.catalogue-source-status p { margin: 6px 0; line-height: 1.6; }
.catalogue-source-status button { margin-left: 12px; }
''';p.write_text(s)
for p in Path('src/exchange_info/static').glob('*'):
 if p.suffix in ('.js','.html','.css'):
  s=p.read_text(); t=s.replace('20261011-coverage-1','20261011-source-recovery-1')
  if s!=t:p.write_text(t)
