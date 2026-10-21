// Exercise the actual frontend lookup with all four separately returned routes.
// This is a function-level check, not browser visual acceptance.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const code = fs.readFileSync(path.join(root, 'src/exchange_info/static/app.js'), 'utf8');
const normalize = code.slice(code.indexOf('function normalize(value)'), code.indexOf('function activeHomeSchool()'));
const lookup = code.slice(code.indexOf('let destinationProfileIndexRef'), code.indexOf('let coveragePartnersIndexRef'));
assert.ok(normalize && lookup);
const all = fs.readFileSync(path.join(root, 'src/exchange_info/official_data/fju/destination_profiles.jsonl'), 'utf8')
  .trim().split(/\r?\n/).map(JSON.parse);
const profiles = all.filter(p => /Sacred Heart, Tokyo|Baiko Gakuin/.test(p.school_name));
assert.equal(profiles.length, 4);
const context = { state: { destinationProfiles: profiles } };
vm.createContext(context);
vm.runInContext(normalize + lookup, context);
for (const p of profiles) assert.equal(context.destinationProfileForSchool(p.school_name), p);
assert.equal(context.destinationProfileForSchool('(其他課程)梅光學院大學 Baiko Gakuin University'), undefined);
const independent = { ...profiles[3], cost_summary: 'Synthetic independent refresh' };
context.state.destinationProfiles = profiles.map(p => p === profiles[3] ? independent : p);
assert.equal(context.destinationProfileForSchool(independent.school_name), independent);
assert.equal(context.destinationProfileForSchool(profiles[2].school_name), profiles[2]);
console.log('4 routes remain distinct; unknown route does not fall back; refreshed list invalidates the lookup cache.');
