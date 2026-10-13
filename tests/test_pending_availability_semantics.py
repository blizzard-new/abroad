"""Unknown quota cannot assert a source's non-announcement or absence of places."""
import subprocess
from pathlib import Path


def test_unknown_quota_and_dates_do_not_imply_an_official_announcement_state():
    source = Path('src/exchange_info/static/app.js').resolve()
    script = r'''
    const assert = require('node:assert/strict');
    const source = require('node:fs').readFileSync(process.argv[1], 'utf8');
    const state = {homeSchool: '國立中央大學'};
    let planning = true;
    const homeSelectionRules = () => ({pending_quota_planning: planning});
    for (const name of ['activeHomeSchool','partnerAvailabilityMeta','applicationPeriodMeta']) {
      const match = source.match(new RegExp('^function '+name+'\\([^]*?^}', 'm'));
      assert.ok(match, name); eval(match[0]);
    }
    const pending = {availability_status:'agreement_only',quota:null,
      quota_status:'not_published',availability_note:'本期尚未核實'};
    const before = JSON.stringify(pending);
    for (const enabled of [true,false]) {
      planning = enabled;
      const result = partnerAvailabilityMeta(pending);
      assert.match(result.cardLabel, /待核實|待確認/);
      assert.doesNotMatch(JSON.stringify(result), /待公告|未公告|沒開放名額|沒有開放名額/);
      assert.equal(Boolean(result.pending), enabled);
      assert.equal(result.blocked, !enabled);
    }
    planning = true;
    for (const zero of ['0','0 名']) {
      const result = partnerAvailabilityMeta({...pending,quota:zero,quota_status:'zero'});
      assert.equal(result.blocked,true); assert.match(result.cardLabel,/零名額/);
      assert.equal(Boolean(result.pending),false);
    }
    const reference = partnerAvailabilityMeta({availability_status:'reference_only',quota:null});
    assert.equal(reference.blocked,true); assert.match(reference.cardLabel,/舊期參考/);
    assert.equal(partnerAvailabilityMeta({availability_status:'zero_quota'}).shortLabel,'零名額');
    assert.equal(partnerAvailabilityMeta({availability_status:'needs_confirmation'}).shortLabel,'名額尚未核實');
    assert.equal(applicationPeriodMeta({status:'needs_confirmation'}).label,'適用期間待確認');
    assert.equal(JSON.stringify(pending),before);
    // The independent field-evidence state remains explicitly represented.
    assert.match(source, /explicit_not_announced:\s*"官方明示尚未公告"/);
    '''
    result = subprocess.run(['node','-e',script,str(source)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
