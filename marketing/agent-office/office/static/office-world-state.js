// Shared, deterministic world rules. The simulation never changes an agent's backend state.
export const DEPARTMENTS = [
  { id: 'research', name: '企劃研究部', en: 'RESEARCH & STRATEGY', color: '#71b8a2', x: -9, z: -5, level: 2, elevation: 5.4, roles: ['strategist'] },
  { id: 'design', name: '視覺設計部', en: 'DESIGN STUDIO', color: '#e8a16c', x: 0, z: -5, level: 2, elevation: 5.4, roles: ['designer'] },
  { id: 'video', name: '影音製作部', en: 'MOTION STUDIO', color: '#a898cf', x: 9, z: -5, level: 2, elevation: 5.4, roles: ['video'] },
  { id: 'social', name: '社群發佈部', en: 'SOCIAL & PUBLISHING', color: '#739fca', x: -9, z: 4, level: 1, elevation: 0, roles: ['threads', 'publisher', 'community'] },
  { id: 'quality', name: '品管數據部', en: 'QUALITY & INSIGHTS', color: '#cfb96d', x: 0, z: 4, level: 1, elevation: 0, roles: ['reviewer', 'analyst'] },
  { id: 'management', name: '總管辦公室', en: 'DIRECTOR’S OFFICE', color: '#8faeb2', x: 9, z: 4, level: 1, elevation: 0, roles: ['chief', 'boss'] },
];

export function departmentFor(id) {
  return DEPARTMENTS.find(d => d.roles.includes(id)) || DEPARTMENTS[0];
}

export function seatLayout(agents) {
  return DEPARTMENTS.flatMap(department => {
    const staff = agents.filter(a => departmentFor(a.id).id === department.id);
    const columns = staff.length > 4 ? 3 : 2;
    return staff.map((agent, index) => ({
      id: agent.id, department, elevation: department.elevation,
      x: department.x + (index % columns - (columns - 1) / 2) * 2.55,
      z: department.z - 1.8 + Math.floor(index / columns) * 2.3,
    }));
  });
}

export const BREAK_SPOTS = { water: [17.8, 0.35, 12.5], exercise: [9, 0.35, 12.5] };

// Physical route: leave through the studio doorway, use the east staircase from
// level 2, then join the ground-level terrace. The renderer retraces this on return.
export function breakRoute(seat, activity) {
  const d = seat.department, y = seat.elevation + 0.35;
  const aisle = d.level === 2 ? -0.1 : 9.9;
  const route = [[seat.x, y, seat.z + 1.45], [d.x + 3.7, y, seat.z + 1.45],
    [d.x + 3.7, y, d.z + 3], [d.x, y, d.z + 3], [d.x, y, aisle], [14.9, y, aisle]];
  if (d.level === 2) {
    route.push([16, y, -0.1], [16, y, 0.5]);
    for (let i = 19; i >= 0; i--) route.push([16, 0.35 + i * 0.27, 10.5 - i * 0.5]);
  }
  route.push([18.3, 0.35, 10.8], [18.3, 0.35, 12.5], [...BREAK_SPOTS[activity]]);
  return route;
}

const clamp = n => Math.max(0, Math.min(1, n));
const smooth = n => { const t = clamp(n); return t * t * (3 - 2 * t); };

export function daylightAt(date = new Date(), timeZone = 'Asia/Taipei') {
  let formatter;
  try { formatter = new Intl.DateTimeFormat('en-GB', { timeZone, hourCycle: 'h23', hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
  catch { timeZone = 'Asia/Taipei'; formatter = new Intl.DateTimeFormat('en-GB', { timeZone, hourCycle: 'h23', hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
  const parts = Object.fromEntries(formatter.formatToParts(date).map(p => [p.type, p.value]));
  const hour = Number(parts.hour) % 24 + Number(parts.minute) / 60 + Number(parts.second) / 3600;
  const daylight = smooth((hour - 5.5) / 1.5) * (1 - smooth((hour - 17) / 1.5));
  const phase = hour < 5.5 || hour >= 18.5 ? 'night' : hour < 7 ? 'dawn' : hour < 17 ? 'day' : 'dusk';
  return {
    hour, daylight, night: 1 - daylight, phase, timeZone,
    label: { night: '月夜 · 室內亮燈', dawn: '晨光 · 海岸甦醒', day: '晴日 · 海風徐徐', dusk: '日落 · 燈光漸亮' }[phase],
    clock: `${String(Number(parts.hour) % 24).padStart(2, '0')}:${parts.minute}`,
    // An illustrative daily arc, not a location-specific astronomical ephemeris.
    sunAngle: ((hour - 6) / 12) * Math.PI,
    moonAngle: (((hour + 6) % 24) / 12) * Math.PI,
  };
}

export const canRest = state => state === 'idle' || state === 'done' || !state;
export const REST_ACTIVITIES = ['nap', 'water', 'exercise'];
export function chooseActivity(random = Math.random) {
  return REST_ACTIVITIES[Math.min(REST_ACTIVITIES.length - 1, Math.floor(random() * REST_ACTIVITIES.length))];
}
