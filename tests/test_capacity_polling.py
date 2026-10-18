"""Exercise the shipped polling class with a clock and visibility/network events."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_ai_polling_pauses_resumes_and_does_not_overlap():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the browser scheduling unit check")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([node, "-", str(root / "src/exchange_info/static/app.js")], input=r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(process.argv[2], 'utf8');
const start = source.indexOf('class AiStatusManager {');
const end = source.indexOf('const aiStatusManager =', start);
assert.ok(start >= 0 && end > start);
const timers = new Map(), events = new Map();
let nextId = 1, requests = 0, release;
const target = {
  addEventListener(name, callback) { events.set(name, callback); },
  removeEventListener(name) { events.delete(name); },
};
const context = {
  state: {aiStatus: {runtime_state: 'paused'}},
  document: {...target, hidden: false}, window: target, navigator: {onLine: true},
  setTimeout(callback, delay) { const id = nextId++; timers.set(id, {callback, delay}); return id; },
  clearTimeout(id) { timers.delete(id); },
  fetchJson: () => { requests++; return new Promise(resolve => { release = resolve; }); },
};
vm.createContext(context);
vm.runInContext(source.slice(start, end) + ';globalThis.Manager = AiStatusManager;', context);
const manager = new context.Manager();
manager.render = manager.updateDegradation = manager.announceStateChange = () => {};
const delay = () => [...timers.values()][0]?.delay;
(async () => {
  manager.start();
  assert.equal(requests, 0, 'boot status must be reused');
  assert.equal(delay(), 300000);
  manager.start();
  assert.equal(timers.size, 1, 'starting again must not duplicate timers');
  context.document.hidden = true;
  events.get('visibilitychange')();
  assert.equal(timers.size, 0);
  await manager.poll();
  assert.equal(requests, 0);
  context.document.hidden = false;
  events.get('visibilitychange')();
  assert.ok(delay() >= 500 && delay() <= 2000);
  const flight = manager.poll();
  await manager.poll();
  assert.equal(requests, 1, 'only one request may be in flight');
  release({runtime_state: 'ready'});
  await flight;
  assert.equal(delay(), 30000);
  context.navigator.onLine = false;
  events.get('offline')();
  assert.equal(timers.size, 0);
  context.navigator.onLine = true;
  events.get('online')();
  assert.equal(timers.size, 1);
  const last = manager.poll();
  manager.stop();
  release({runtime_state: 'paused'});
  await last;
  assert.equal(manager.state, 'ready', 'stopped response must not update the UI');
  assert.equal(timers.size, 0);
  assert.equal(events.size, 0);
})().catch(error => { console.error(error); process.exitCode = 1; });
""", text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
