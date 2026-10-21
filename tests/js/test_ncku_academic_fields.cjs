const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const source = fs.readFileSync(path.join(root, 'src/exchange_info/static/app.js'), 'utf8');
const code = source.slice(source.indexOf('function academicMinimum()'), source.indexOf('function homeCollegeOptions()'));
const dashboard = JSON.parse(fs.readFileSync(path.join(root, 'src/exchange_info/official_data/ncku/student_dashboard.json'), 'utf8'));
const markup = fs.readFileSync(path.join(root, 'src/exchange_info/static/index.html'), 'utf8');
const nodes = new Map();
function $(id) {
  assert.ok(markup.includes(`id="${id.slice(1)}"`), `selector must exist in actual markup: ${id}`);
  if (!nodes.has(id)) nodes.set(id, {hidden:false,disabled:false,options:[],querySelectorAll:()=>[]});
  return nodes.get(id);
}
const gpaLabel=$('#advisor-gpa-field');
gpaLabel.querySelector=()=>$('#advisor-academic-gpa');
const rankLabel={hidden:true,querySelector:()=>$('#advisor-class-rank')};
const context=vm.createContext({state:{dashboard},$,document:{querySelectorAll:()=>[gpaLabel,rankLabel]},activeHomeSchool:()=> '國立成功大學'});
vm.runInContext(code,context);
const scenarios=[
  [{degree:'學士班',academicScore:77},true],
  [{degree:'學士班',academicScore:76,classRankPercent:50},true],
  [{degree:'學士班',classRankPercent:50},true],
  [{degree:'學士班',academicScore:76,classRankPercent:51,academicGpa:4.3},false],
  [{degree:'學士班',academicGpa:4.3},false],
  [{degree:'學士班',classRankPercent:0},false],
  [{degree:'碩士班'},true],
  [{degree:'在職碩士班'},true],
  [{degree:'',academicScore:100},false],
];
for(const [profile,expected] of scenarios) assert.equal(context.homeAcademicPass(profile),expected);
context.renderAcademicFields();
assert.equal($('#advisor-percent-field').hidden,false);
assert.equal($('#advisor-academic-score').disabled,false);
assert.equal(rankLabel.hidden,false);
assert.equal($('#advisor-class-rank').disabled,false);
assert.equal(gpaLabel.hidden,true);
assert.equal($('#advisor-academic-gpa').disabled,true);
assert.equal($('#advisor-rank-label').textContent,'前一學期班／系排名（前幾%）');
context.state.dashboard={selection_rules:{academic_policy:'gpa_or_rank',undergraduate_gpa_minimum:2.44,undergraduate_rank_maximum:50}};
context.renderAcademicFields();
assert.equal($('#advisor-percent-field').hidden,true);
assert.equal(gpaLabel.hidden,false);
assert.equal($('#advisor-rank-label').textContent,'適用學年班排名（前幾%）');
context.state.dashboard={selection_rules:{academic_policy:'percentage'},academic_score_minimum:70};
context.renderAcademicFields();
assert.equal(rankLabel.hidden,true);
assert.equal($('#advisor-class-rank').disabled,true);
assert.equal($('#advisor-academic-score').disabled,false);
console.log('NCKU academic function/field behavior: 9 qualification cases and 13 field assertions passed; no browser rendering asserted.');
