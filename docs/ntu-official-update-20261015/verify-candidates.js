/* Source and scope checks for the research-only PR28 deliverables.
 * Run with Node: node docs/ntu-official-update-20261015/verify-candidates.js
 * This does not test or modify the application or fetch remote sources.
 */
"use strict";
function verifyCandidateFiles(contents, xlsxBytes, previousContents) {
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const c = JSON.parse(contents["結構化候選資料.json"]);
  const s = JSON.parse(contents["補送來源與查核紀錄.json"]);
  check(c.artifact_role === "research_candidate_only", "candidate role");
  check(c.application_open_confirmed === false && c.all_current_cycle_fields_verified === false
    && c.local_integration_complete === false, "unverified platform state promoted");
  const rows = c.prior_identity_rows_with_reviewed_delta;
  check(rows.length === 288 && new Set(rows.map(r => r.portal_id)).size === 288, "288 school identity inventory");
  const positive = rows.filter(r => r.quota && r.quota !== "0 名");
  check(positive.length === 20 && rows.filter(r => r.quota === "").length === 261
    && rows.filter(r => r.quota === "0 名").length === 7, "quota categories");
  check(positive.reduce((n,r) => n + Number(r.quota.replace(" 名","")),0) === 43
    && positive.reduce((n,r) => n + Number(r.headcount.replace(" 名","")),0) === 81, "quota units/totals");
  check(rows.find(r => r.portal_id === "95").quota === ""
    && rows.find(r => r.portal_id === "599").quota === "0 名", "old Deakin closure or Queen's zero misclassified");
  check(c.field_coverage.length === 2820 && new Set(c.field_coverage.map(r => r.portal_id)).size === 282
    && new Set(c.field_coverage.map(r => r.portal_id + "|" + r.field)).size === 2820, "282 by ten grain");
  for (const field of ["quota","eligibility","language","documents","deadlines","calendar","housing","cost","courses","insurance_visa"]) {
    check(c.field_coverage.filter(r => r.field === field).length === 282, "field denominator " + field);
  }
  check(c.field_coverage.every(r => r.target_cycle_fully_verified === false), "whole-cycle claims");
  check(s.records.length === 13 && new Set(s.records.map(r => r.record_id)).size === 13
    && new Set(s.records.map(r => r.portal_id)).size === 7
    && new Set(s.records.map(r => r.portal_id + "|" + r.field)).size === 10, "supplement grain");
  check(s.records.every(r => r.full_current_cycle_requirement_verified === false
    && r.home_selection_rule_changed === false && r.source_academic_year === null), "undated references promoted");
  const scholarships = s.records.filter(r => r.change_type === "scholarship_reference_link_added");
  check(scholarships.length === 3 && scholarships.every(r => r.current_2027_2028_deadline_confirmed === false), "old scholarships promoted");
  check(scholarships.find(r => r.record_id.includes("exchange-scholarship")).student_direct_application_allowed === false, "nomination boundary");
  const ts = s.records.filter(r => r.portal_id === "107");
  check(ts.length === 2 && ts.every(r => r.chat_timing_ambiguity_preserved === true
    && r.independent_pdf_body_read === false && r.raw_original_archived_in_this_PR === false
    && r.new_financial_proof_requirement === false
    && JSON.stringify(r.pdf_pages) === "[2,6,24,25]"), "CoE pages/version scope");
  check(s.tsukuba_pdf_receipt.new_sha256 === "14d780564775aad32463ba0fe78c386812f650fb38d94f21309c1f54eed89e78"
    && s.tsukuba_pdf_receipt.independent_raw_sha_verified === false
    && s.tsukuba_pdf_receipt.archived_binary_in_PR === false, "PDF receipt versus original");
  const library = s.tsukuba_pdf_receipt.library_reference;
  check(s.tsukuba_pdf_receipt.original_available_in_library === true
    && library.library_file_id === "libfile_96954a090f8481918724c70e11501a13"
    && library.file_id === "file_00000000316481f5861bd82c8bfb5fa7"
    && library.file_name === "7c463d5e808c02b2-a1.pdf"
    && library.size_bytes === 1863560 && library.num_pages === 25
    && JSON.stringify(library.read_pages) === "[2,6,24,25]"
    && library.raw_SHA256_recomputed === false && library.raw_bytes_materialized === false
    && library.page_pixels_visually_inspected === false, "Library identity/content versus byte verification");
  check(ts.every(r => r.independent_page_text_read === true
    && JSON.stringify(r.independent_page_text_read_pages) === "[2,6,24,25]"), "four Library page texts");
  check(s.parent_full_comparison.detailed_pages.identical_bytes + s.parent_full_comparison.detailed_pages.changed === 288, "parent detail count");
  const a = s.parent_full_comparison.tracked_attachments;
  check(a.identical + a.changed + a.unknown === 92 && a.unknown === 6
    && a.unknown_means_unchanged === false, "attachment unknowns");
  const linkStates = s.reference_link_checks.map(r => r.independent_status);
  check(linkStates.filter(v => v === "readable_html").length === 4
    && linkStates.filter(v => v === "tool_reported_404").length === 2
    && linkStates.filter(v => v === "tool_fetch_timeout").length === 2, "two retrieval records collapsed");

  function parseCSV(text) {
    text = text.replace(/^\uFEFF/, "");
    const result=[]; let row=[], value="", quoted=false;
    for(let i=0;i<text.length;i++) {
      const ch=text[i];
      if(quoted) { if(ch === '"' && text[i+1] === '"') { value+='"'; i++; }
        else if(ch === '"') quoted=false; else value+=ch;
      } else if(ch === '"') quoted=true;
      else if(ch === ',') {row.push(value);value="";}
      else if(ch === '\n') {row.push(value);if(row.some(Boolean))result.push(row);row=[];value="";}
      else if(ch !== '\r') value+=ch;
    }
    check(!quoted, "unterminated CSV quote");
    if(value || row.length) {row.push(value);result.push(row);}
    return result;
  }
  const csv = parseCSV(contents["原282校十類查核_20261015.csv"]);
  check(csv.length === 2821 && csv.every(r => r.length === 21), "CSV row/column round trip");
  let unchangedBaseCells = false;
  if(previousContents) {
    const old = JSON.parse(previousContents["結構化候選資料.json"]);
    const oldCSV = parseCSV(previousContents["原282校十類查核_20261015.csv"]);
    check(oldCSV.length === csv.length, "previous CSV grain");
    for(let i=1;i<csv.length;i++) for(let j=0;j<21;j++) {
      if(j < 12 || j > 15) check(oldCSV[i][j] === csv[i][j], "baseline/reply cell changed at "+i+":"+j);
    }
    const oldMap = new Map(old.field_coverage.map(r => [r.portal_id+"|"+r.field,r]));
    for(const r of c.field_coverage) {
      const p=oldMap.get(r.portal_id+"|"+r.field);
      check(p && p.baseline_status === r.baseline_status && p.baseline_review_outcome === r.baseline_review_outcome
        && p.baseline_checked_at === r.baseline_checked_at && p.current_publication_status === r.current_publication_status, "original conclusion changed");
    }
    unchangedBaseCells=true;
  }
  const u16 = o => xlsxBytes[o] | (xlsxBytes[o+1] << 8);
  const u32 = o => (xlsxBytes[o] | (xlsxBytes[o+1]<<8) | (xlsxBytes[o+2]<<16) | (xlsxBytes[o+3]<<24)) >>> 0;
  function crc(bytes) {let c=0xffffffff;for(const b of bytes){c^=b;for(let i=0;i<8;i++)c=(c&1)?(0xedb88320^(c>>>1)):(c>>>1);}return(c^0xffffffff)>>>0;}
  function ascii(bytes) {let out=[];for(let i=0;i<bytes.length;i+=8192)out.push(String.fromCharCode(...bytes.subarray(i,i+8192)));return out.join("");}
  let offset=0; const parts={};
  while(u32(offset) === 0x04034b50) {
    check((u16(offset+6)&1) === 0 && u16(offset+8) === 0, "unexpected encrypted/compressed ZIP");
    const size=u32(offset+18),nameLength=u16(offset+26),extra=u16(offset+28);
    const name=ascii(xlsxBytes.subarray(offset+30,offset+30+nameLength)),start=offset+30+nameLength+extra;
    const body=xlsxBytes.subarray(start,start+size);
    check(crc(body) === u32(offset+14), "ZIP CRC "+name);
    parts[name]=ascii(body);offset=start+size;
  }
  check(Object.keys(parts).length === 10 && u32(offset) === 0x02014b50
    && u32(xlsxBytes.length-22) === 0x06054b50 && u16(xlsxBytes.length-12) === 10, "ZIP central/end directory");
  check((parts["xl/workbook.xml"].match(/<sheet name=/g)||[]).length === 6, "Excel sheet count");
  check((parts["xl/worksheets/sheet3.xml"].match(/<row r=/g)||[]).length === 2821, "Excel 2820 field rows");
  check((parts["xl/worksheets/sheet6.xml"].match(/<row r=/g)||[]).length === 14, "Excel 13 supplement rows");
  check(Object.values(parts).every(text => !/<f[ >]/.test(text)), "unexpected spreadsheet formulas");
  for(const [name,text] of Object.entries(parts)) {
    const stack=[];
    for(const m of text.matchAll(/<[^>]+>/g)) {
      const tag=m[0];if(tag.startsWith("<?") || tag.endsWith("/>"))continue;
      if(tag.startsWith("</"))check(stack.pop() === tag.slice(2,-1),"XML nesting "+name);
      else stack.push(tag.slice(1).match(/^[^\s>]+/)[0]);
    }
    check(stack.length === 0,"XML unclosed "+name);
  }
  return {school_count:288,original_pending_schools:282,field_rows:2820,csv_columns:21,
    positive:20,blank:261,zero:7,academic_year_slots:43,maximum_persons:81,supplement_records:13,
    supplement_schools:7,changed_field_pairs:10,baseline_and_reply_cells_unchanged:unchangedBaseCells,
    excel_sheets:6,zip_parts:10,all_zip_crc_passed:true,excel_formula_cells:0,
    Library_original_metadata_and_four_page_texts_read:true,pdf_binary_independently_verified:false,runtime_tests_run:false};
}
if(typeof module !== "undefined") module.exports={verifyCandidateFiles};
if(typeof require !== "undefined" && require.main === module) {
  const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto");
  const names=["結構化候選資料.json","補送來源與查核紀錄.json","原282校十類查核_20261015.csv"];
  const current=Object.fromEntries(names.map(n=>[n,fs.readFileSync(path.join(__dirname,n),"utf8")]));
  const previous={};for(const n of ["結構化候選資料.json","原282校十類查核_20261015.csv"])
    previous[n]=cp.execFileSync("git",["show","36b2ea7288519d240e022fff7d749d9e4d65c6d6:docs/ntu-official-update-20261015/"+n],{encoding:"utf8",maxBuffer:20*1024*1024});
  const result=verifyCandidateFiles(current,fs.readFileSync(path.join(__dirname,"臺大116-1_282校逐欄回填_20261015.xlsx")),previous);
  const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,"deliverables-manifest.json"),"utf8"));
  for(const f of manifest.files) {
    const b=fs.readFileSync(path.join(__dirname,f.filename));
    if(b.length !== f.bytes || crypto.createHash("sha256").update(b).digest("hex") !== f.sha256)
      throw new Error("Manifest mismatch "+f.filename);
  }
  console.log(JSON.stringify({...result,manifest_sha256_verified:true},null,2));
}
