import test from 'node:test';
import assert from 'node:assert/strict';
import { daylightAt, seatLayout, DEPARTMENTS, canRest, chooseActivity, breakRoute, BREAK_SPOTS, advanceAlongPath } from '../office/static/office-world-state.js';

test('Taipei noon, 19:00 and midnight follow the real instant, regardless of host timezone', () => {
  const noon = daylightAt(new Date('2026-10-26T04:00:00Z'));
  assert.equal(noon.clock, '12:00'); assert.equal(noon.phase, 'day'); assert.equal(noon.daylight, 1);
  const evening = daylightAt(new Date('2026-10-26T11:00:00Z'));
  assert.equal(evening.clock, '19:00'); assert.equal(evening.phase, 'night'); assert.equal(evening.night, 1);
  const midnight = daylightAt(new Date('2026-10-26T16:00:00Z'));
  assert.equal(midnight.hour, 0); assert.equal(midnight.clock, '00:00'); assert.equal(midnight.phase, 'night');
});

test('sunrise and sunset blend lighting; an office timezone can differ from Taipei', () => {
  const dawn = daylightAt(new Date('2026-10-25T22:00:00Z'));
  assert.equal(dawn.phase, 'dawn'); assert.ok(dawn.daylight > 0 && dawn.daylight < 1);
  const dusk = daylightAt(new Date('2026-10-26T10:00:00Z'));
  assert.equal(dusk.phase, 'dusk'); assert.ok(dusk.night > 0 && dusk.night < 1);
  assert.equal(daylightAt(new Date('2026-10-26T11:00:00Z'), 'UTC').phase, 'day');
  assert.equal(daylightAt(new Date('2026-10-26T11:00:00Z'), 'bad-zone').clock, '19:00');
});

test('every existing employee, boss and all six hires get a distinct seat within their department', () => {
  const staff = DEPARTMENTS.flatMap(d => d.roles).concat(Array.from({length: 6}, (_, i) => `hire-${i}`)).map(id => ({id}));
  const seats = seatLayout(staff);
  assert.equal(seats.length, 16);
  assert.equal(new Set(seats.map(s => `${s.x},${s.z}`)).size, 16);
  for (const seat of seats) {
    assert.ok(Math.abs(seat.x - seat.department.x) < 3.2);
    assert.ok(Math.abs(seat.z - seat.department.z) < 3.2);
    if (seat.id.startsWith('hire-')) assert.equal(seat.department.id, 'research');
  }
  assert.equal(seats.find(s => s.id === 'designer').department.id, 'design');
  assert.equal(seats.find(s => s.id === 'video').department.id, 'video');
  assert.equal(seats.find(s => s.id === 'publisher').department.id, 'social');
  for (const id of ['strategist', 'designer', 'video', 'hire-5']) assert.equal(seats.find(s => s.id === id).elevation, 5.4);
  for (const id of ['threads', 'analyst', 'chief', 'boss']) assert.equal(seats.find(s => s.id === id).elevation, 0);
});

test('upstairs breaks use the actual staircase; downstairs stays on the ground and both reach shared facilities', () => {
  const seats = seatLayout(DEPARTMENTS.flatMap(d => d.roles).map(id => ({id})));
  for (const seat of seats) for (const activity of ['water', 'exercise']) {
    const route = breakRoute(seat, activity);
    assert.deepEqual(route.at(-1), BREAK_SPOTS[activity]);
    assert.equal(route[0][1], seat.elevation + 0.35);
    assert.ok(route.every(p => p.every(Number.isFinite)));
    if (seat.department.level === 2) {
      const descending = route.filter((p, i) => i > 0 && p[1] < route[i - 1][1]);
      assert.equal(descending.length, 20);
      for (const p of descending) { assert.equal(p[0], 16); assert.ok(p[2] >= 1 && p[2] <= 10.5); }
      for (let i = 1; i < route.length; i++) assert.ok(Math.abs(route[i][1] - route[i - 1][1]) <= .271, 'never teleport between floors');
    } else assert.ok(route.every(p => p[1] === .35));
  }
});

test('only idle or completed employees can rest; waiting and errors stay visible as work states', () => {
  for (const state of ['idle', 'done', undefined]) assert.equal(canRest(state), true);
  for (const state of ['working', 'thinking', 'rendering', 'reviewing', 'waiting', 'error']) assert.equal(canRest(state), false);
  assert.deepEqual([0, 0.4, 0.9].map(n => chooseActivity(() => n)), ['nap', 'water', 'exercise']);
});

test('walking covers equal distance at low or high frame rates, without pausing at stair waypoints', () => {
  const route = Array.from({length: 20}, (_, i) => ({x: 16, y: 5.75 - (i + 1) * .27, z: .5 + (i + 1) * .5}));
  const slow = {x: 16, y: 5.75, z: .5}, fast = {...slow};
  const slowPath = route.map(p => ({...p})), fastPath = route.map(p => ({...p}));
  const step = advanceAlongPath(slow, slowPath, 3.1 * 2);
  for (let i = 0; i < 60; i++) advanceAlongPath(fast, fastPath, 3.1 / 30);
  assert.ok(step.reached.length >= 10);
  assert.equal(slowPath.length, fastPath.length);
  for (const axis of ['x','y','z']) assert.ok(Math.abs(slow[axis] - fast[axis]) < 1e-10);
  advanceAlongPath(slow, slowPath, 100);
  assert.deepEqual(slow, route.at(-1)); assert.equal(slowPath.length, 0);
});
