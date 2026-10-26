import * as THREE from './vendor/three.module.min.js';
import { OrbitControls } from './vendor/OrbitControls.js';
import { DEPARTMENTS, departmentFor, seatLayout, daylightAt, canRest, chooseActivity, breakRoute } from './office-world-state.js';
import { buildHeadquarters, createCoastalWater } from './office-building.js';

// A local, procedural dollhouse: no remote assets, tracking, or model API calls.
export function initOfficeWorld(bridge) {
  const host = document.querySelector('#world-canvas');
  const stage = document.querySelector('#world-stage');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  host.append(renderer.domElement);
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('aria-label', '海邊 3D 公司。拖曳旋轉，滾輪縮放；也可使用上方視角按鈕及下方員工名冊。');
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2('#b3d8dd', 0.006);
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 500);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = !reduced.matches;
  controls.dampingFactor = 0.075;
  controls.enablePan = false;
  controls.minDistance = 14;
  controls.maxDistance = 125;
  controls.minPolarAngle = 0.25;
  controls.maxPolarAngle = Math.PI * 0.47;
  const people = new Map();
  const picking = [];
  const lamps = [];
  const clouds = [];
  const deliveries = [];
  let timeZone = 'Asia/Taipei';
  let activeDepartment = 'all';
  let viewMode = 'exterior';
  let dayState;
  let targetView = null;
  let disposed = false;
  let hidden = document.hidden;
  let lastFrame = 0;
  let animationTime = 0;
  let lastClock = 0;
  let pending = 0;
  const staffGroup = new THREE.Group();
  scene.add(staffGroup);
  const labels = document.querySelector('#world-labels');
  const materials = new Map();
  const boxGeometry = new THREE.BoxGeometry(1, 1, 1);
  const sphereGeometry = new THREE.SphereGeometry(1, 12, 8);
  const cylinderGeometry = new THREE.CylinderGeometry(1, 1, 1, 10);
  const m = (color, extras = {}) => {
    const key = `${color}:${JSON.stringify(extras)}`;
    if (!materials.has(key)) materials.set(key, new THREE.MeshStandardMaterial({ color, roughness: 0.78, ...extras }));
    return materials.get(key);
  };
  function mesh(geometry, material, position, scale, parent = scene) {
    const obj = new THREE.Mesh(geometry, material);
    obj.position.set(...position);
    obj.scale.set(...scale);
    obj.castShadow = true;
    obj.receiveShadow = true;
    parent.add(obj);
    return obj;
  }
  const box = (color, p, s, parent, extras) => mesh(boxGeometry, m(color, extras), p, s, parent);
  const sphere = (color, p, s, parent, extras) => mesh(sphereGeometry, m(color, extras), p, s, parent);
  const cylinder = (color, p, s, parent, extras) => mesh(cylinderGeometry, m(color, extras), p, s, parent);

  function textTexture(text, subtitle, color = '#1b4645', bg = '#f5f1e7') {
    const canvas = document.createElement('canvas');
    canvas.width = 768; canvas.height = 192;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, 768, 192);
    ctx.fillStyle = color; ctx.textAlign = 'center';
    ctx.font = 'bold 55px "GenJyuuGothic", sans-serif';
    ctx.fillText(text, 384, subtitle ? 87 : 112);
    if (subtitle) { ctx.font = '22px sans-serif'; ctx.fillText(subtitle, 384, 143); }
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }
  function sign(text, subtitle, p, width = 5.8, color) {
    const texture = textTexture(text, subtitle, color);
    const material = new THREE.MeshBasicMaterial({ map: texture, side: THREE.DoubleSide });
    const board = new THREE.Mesh(new THREE.PlaneGeometry(width, width / 4), material);
    board.position.set(...p);
    scene.add(board);
    return board;
  }
  function plant(x, z, size = 1, elevation = 0) {
    cylinder('#b98763', [x, elevation + 0.65, z], [0.36 * size, 0.7, 0.36 * size]);
    for (let i = 0; i < 5; i++) {
      const angle = i * 2.4;
      const leaf = sphere(i % 2 ? '#426f5c' : '#629373', [x + Math.sin(angle) * 0.22, elevation + 1.25 + i * 0.12, z + Math.cos(angle) * 0.22], [0.25 * size, 0.65 * size, 0.16 * size]);
      leaf.rotation.z = Math.sin(angle) * 0.55;
    }
  }
  function palm(x, z, size = 1) {
    const trunk = cylinder('#9d7a51', [x, 2.9 * size, z], [0.22, 5.8 * size, 0.25]);
    trunk.rotation.z = 0.08;
    for (let i = 0; i < 7; i++) {
      const a = i * Math.PI * 2 / 7;
      const leaf = sphere(i % 2 ? '#2e7262' : '#559475', [x + Math.sin(a) * 1.2 * size, 5.8 * size, z + Math.cos(a) * 1.2 * size], [0.55 * size, 0.16, 2.1 * size]);
      leaf.rotation.y = a; leaf.rotation.x = 0.17;
    }
  }

  // A complete two-storey coastal headquarters, with a removable facade/roof.
  const sea = createCoastalWater(scene);
  const sand = mesh(new THREE.CylinderGeometry(1, 1.05, 1, 64), m('#dccba5'), [0, -0.85, 2], [26, 0.65, 23]);
  box('#a69579', [0, -0.3, 0], [29, 0.8, 21.8]);
  box('#eee5d5', [0, 0.15, 0], [28.7, 0.2, 21.5]);
  // Ocean-facing terrace and pier.
  box('#b09271', [1, 0, 12.7], [27, 0.45, 4.3]);
  for (let i = 0; i < 33; i++) box('#d1b899', [-12.2 + i * 0.82, 0.25, 12.7], [0.76, 0.09, 4.15]);
  box('#ac8d66', [-18, -0.15, 18], [3.2, 0.3, 14]);
  for (let z = 12; z < 25; z += 1.5) {
    box('#c8af87', [-18, 0.05, z], [3.3, 0.1, 1.3]);
    cylinder('#72583c', [-19.5, -0.3, z], [0.12, 2, 0.12]);
    cylinder('#72583c', [-16.5, -0.3, z], [0.12, 2, 0.12]);
  }
  for (const x of [-12.5, -2.5, 2.5, 13.5]) { box('#cbbd9f', [x, 0.9, 14.7], [0.12, 1.3, 0.12]); }
  box('#e7dfc8', [-7.5, 1.5, 14.7], [10, 0.12, 0.12]);
  box('#e7dfc8', [8, 1.5, 14.7], [11, 0.12, 0.12]);
  box('#ddd4c2', [0, 0.07, 15.2], [5.2, 0.18, 0.8]);
  box('#ddd4c2', [0, -0.11, 16], [5.5, 0.18, 0.8]);
  for (const z of [17, 18.6, 20.2]) box('#e3d9c5', [0, -0.37, z], [5.5, 0.18, 1.3]);
  const building = buildHeadquarters({ scene, box, sphere, cylinder, sign });

  DEPARTMENTS.forEach((d, i) => {
    const y = d.elevation;
    box(d.color, [d.x, y + 0.28, d.z], [8.5, 0.05, 8.3], scene, { roughness: 1 });
    box('#eee8dc', [d.x, y + 0.32, d.z - 0.15], [8.15, 0.04, 7.6]);
    // A clear nameplate at the front of every department, readable from the default view.
    const title = sign(`${d.level}F / ${d.name}`, d.en, [d.x, y + 0.4, d.z + 3.5], 6.4, d.color);
    title.rotation.x = -Math.PI / 2;
    if (i < 3) sign(d.name, d.en, [d.x, y + 3.3, -10.29], 6.6);
    // Warm suspended fixtures that switch on at night.
    const fixture = box('#384e49', [d.x, y + 4.15, d.z], [3.3, 0.13, 0.33]);
    const glow = box('#fff1cd', [d.x, y + 4.24, d.z], [3.1, 0.045, 0.26], scene, { emissive: '#ffcf87', emissiveIntensity: 0 });
    const light = new THREE.PointLight('#ffd99e', 0, 11, 2);
    light.position.set(d.x, y + 3.7, d.z); scene.add(light);
    const pool = new THREE.Mesh(new THREE.CircleGeometry(3.4, 32), new THREE.MeshBasicMaterial({ color: '#ffca78', transparent: true, opacity: 0, depthWrite: false }));
    pool.rotation.x = -Math.PI / 2; pool.position.set(d.x, y + 0.35, d.z); scene.add(pool);
    lamps.push({ glow, light, fixture, pool });
  });
  // Glass partitions separate the six studios without blocking the people.
  for (const x of [-4.5, 4.5]) {
    for (const z of [-6, 5.5]) {
      const y = z < 0 ? 5.4 : 0;
      box('#d4d8cf', [x, y + 0.8, z], [0.16, 1, 6]);
      const glass = box('#aaccc4', [x, y + 1.8, z], [0.045, 1, 6], scene, { transparent: true, opacity: 0.18, depthWrite: false });
      glass.castShadow = false;
      box('#688b80', [x, y + 2.32, z], [0.09, 0.07, 6]);
    }
  }
  for (const x of [-11.6, -6.6, -2.6, 2.6, 6.6, 11.6]) box('#d4d8cf', [x, 6.2, -0.5], [2.8, 1, 0.15]);

  // Department-specific props: samples, a photography rig, charts, and a meeting table.
  for (let i = 0; i < 4; i++) box(['#d98972', '#dcbf67', '#80ad9b', '#8b9dcd'][i], [-2.5 + i * 1.6, 7.4, -9.45], [1.1, 1.5, 0.09]);
  box('#3a464f', [11.5, 7.2, -8.4], [2.8, 2.8, 0.18]);
  cylinder('#394750', [7, 6.75, -8.4], [0.07, 2.1, 0.07]);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.08, 8, 24), m('#fff0cb', { emissive: '#ffd8a0', emissiveIntensity: 0.6 }));
  ring.position.set(7, 7.9, -8.4); scene.add(ring);
  box('#434e57', [11.2, 7.1, -8], [0.6, 0.45, 0.6]);
  cylinder('#434e57', [11.2, 6.3, -8], [0.06, 1.4, 0.06]);
  for (let i = 0; i < 5; i++) box('#719e88', [-2.8 + i * 1.3, 0.8 + i * 0.16, 1], [0.5, 0.7 + i * 0.3, 0.35]);
  // Shared water station, terrace fitness mat, bench and coffee table.
  box('#ddd2bf', [16.8, 0.15, 12], [5.8, 0.25, 3.5]);
  box('#e7ede8', [17.8, 1.15, 11.2], [0.85, 1.6, 0.8]);
  cylinder('#8bc9da', [17.8, 2.25, 11.2], [0.34, 0.7, 0.34], scene, { transparent: true, opacity: 0.75 });
  box('#365b6e', [17.8, 1.5, 11.65], [0.4, 0.2, 0.12]);
  sign('補水站', 'WATER BREAK', [17.8, 3, 10.7], 2.2);
  box('#699e92', [9, 0.34, 12.5], [3.5, 0.08, 1.7]);
  sign('海風伸展區', 'BREATHE & STRETCH', [9, 0.36, 14], 3.8).rotation.x = -Math.PI / 2;
  box('#bf8a65', [-5, 0.8, 12.8], [4, 0.25, 1]);
  for (const x of [-6.5, -3.5]) box('#4c6254', [x, 0.5, 12.8], [0.15, 0.7, 0.8]);
  cylinder('#e8d8bb', [-8.7, 0.85, 12.5], [0.75, 0.1, 0.75]);
  cylinder('#5a6856', [-8.7, 0.5, 12.5], [0.1, 0.7, 0.1]);
  [[-13, -8], [-13, 9], [13, -8], [13, 9], [3.5, 9]].forEach(([x,z]) => plant(x,z,1,z < 0 ? 5.4 : 0));
  palm(-20, -8, 1.15); palm(20, -5, 1.05); palm(21, 10, 0.9); palm(-22, 6, 0.85);
  for (let i = 0; i < 5; i++) sphere('#a2aa95', [-21 + i * 0.85, -0.25, -14 + Math.sin(i) * 0.7], [1, 0.7, 1.3]);

  const hemi = new THREE.HemisphereLight('#f5ffff', '#8d8168', 2.5); scene.add(hemi);
  const sunLight = new THREE.DirectionalLight('#fff0cf', 3); scene.add(sunLight);
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.set(2048, 2048);
  Object.assign(sunLight.shadow.camera, { left: -32, right: 32, top: 30, bottom: -30, far: 160 });
  sunLight.shadow.bias = -0.0007;
  sunLight.shadow.normalBias = 0.08;
  const moonLight = new THREE.DirectionalLight('#9fb9ee', 0); moonLight.position.set(-25, 35, 10); scene.add(moonLight);
  const sun = sphere('#ffe6a0', [0, 20, -75], [3.3, 3.3, 3.3], scene, { emissive: '#ffca68', emissiveIntensity: 2 });
  sun.castShadow = false;
  const moon = sphere('#e5edff', [-25, 20, -60], [2.2, 2.2, 2.2], scene, { emissive: '#ccd9ff', emissiveIntensity: 1.2 });
  moon.castShadow = false;
  for (let i = 0; i < 7; i++) {
    const cloud = new THREE.Group();
    cloud.position.set(-65 + i * 21, 18 + i % 3 * 3, -65 - i % 2 * 25);
    for (let j = 0; j < 3; j++) sphere('#eef6ef', [j * 2.2, Math.sin(j) * 0.9, 0], [3.4, 1, 1.8], cloud);
    scene.add(cloud); clouds.push(cloud);
  }
  const starPositions = [];
  for (let i = 0; i < 120; i++) starPositions.push(Math.sin(i * 132.7) * 125, 18 + ((i * 17) % 65), -30 - (i * 13) % 120);
  const starGeometry = new THREE.BufferGeometry();
  starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
  const stars = new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: '#edf5ff', size: 0.18, transparent: true, opacity: 0 }));
  scene.add(stars);

  function createPerson(agent, seat, index) {
    const group = new THREE.Group(); staffGroup.add(group);
    const desk = new THREE.Group(); group.add(desk);
    desk.position.set(seat.x, seat.elevation, seat.z);
    const shirt = agent.shirt || '#678e8c';
    const skin = ['#ecc4a2', '#c78d69', '#edba94', '#d5a282'][index % 4];
    box('#c49f77', [0, 1.35, 0], [2.12, 0.15, 1.15], desk);
    for (const x of [-0.83, 0.83]) for (const z of [-0.4, 0.4]) box('#66766e', [x, 0.8, z], [0.09, 1, 0.09], desk);
    box('#243d43', [0, 1.93, -0.3], [1.04, 0.7, 0.1], desk);
    const screen = box('#6ea9b2', [0, 1.93, -0.24], [0.92, 0.57, 0.025], desk, { emissive: '#5b9ead', emissiveIntensity: 0.4 });
    screen.material = screen.material.clone();
    for (let j = 0; j < 3; j++) box('#d3efe0', [-0.12, 2.08 - j * 0.14, -0.222], [0.52 - j * 0.09, 0.035, 0.012], desk);
    box('#344950', [0, 1.52, -0.3], [0.1, 0.35, 0.12], desk);
    box('#6d7f7b', [0, 1.47, 0.2], [0.7, 0.04, 0.24], desk);
    cylinder('#f4e8ca', [0.77, 1.6, 0.04], [0.1, 0.26, 0.1], desk);
    cylinder('#66766e', [-0.82, 1.7, -0.25], [0.035, 0.6, 0.035], desk);
    const deskLamp = sphere('#fff0c5', [-0.82, 2.02, -0.25], [0.17, 0.1, 0.17], desk, { emissive: '#ffce84', emissiveIntensity: 0 });
    box('#496168', [0, 0.88, 0.9], [0.65, 0.13, 0.65], desk);
    box('#496168', [0, 1.3, 1.17], [0.68, 0.8, 0.1], desk);
    cylinder('#334950', [0, 0.55, 0.9], [0.06, 0.6, 0.06], desk);
    const person = new THREE.Group(); group.add(person);
    person.position.set(seat.x, seat.elevation + 0.35, seat.z + 0.75);
    const torso = box(shirt, [0, 0.92, 0], [0.52, 0.7, 0.34], person);
    const head = new THREE.Group(); head.position.y = 1.5; person.add(head);
    sphere(skin, [0, 0, 0], [0.29, 0.31, 0.27], head);
    sphere(agent.hair_color || '#352a28', [0, 0.15, -0.045], [0.3, 0.22, 0.26], head);
    for (const x of [-0.1, 0.1]) sphere('#333c40', [x, 0.025, 0.25], [0.025, 0.032, 0.018], head);
    if (agent.hair === 'bun' || agent.hair === 'ponytail') sphere(agent.hair_color, [0, 0.28, -0.18], [0.14, 0.14, 0.14], head);
    if (agent.accessory === 'headphones') {
      for (const x of [-0.31, 0.31]) box('#334652', [x, 0.04, 0], [0.1, 0.25, 0.2], head);
      box('#334652', [0, 0.36, 0], [0.65, 0.06, 0.1], head);
    }
    if (agent.accessory === 'glasses') for (const x of [-0.11, 0.11]) box('#31464b', [x, 0.03, 0.27], [0.19, 0.12, 0.025], head);
    const arms = [-1, 1].map(s => {
      const arm = new THREE.Group(); arm.position.set(s * 0.33, 1.12, 0); person.add(arm);
      box(shirt, [0, -0.2, 0], [0.16, 0.4, 0.2], arm);
      sphere(skin, [0, -0.44, 0], [0.095, 0.12, 0.095], arm);
      return arm;
    });
    const legs = [-1, 1].map(s => {
      const leg = new THREE.Group(); leg.position.set(s * 0.16, 0.62, 0); person.add(leg);
      box('#394e60', [0, -0.23, 0], [0.19, 0.46, 0.22], leg);
      box('#f1e8d8', [0, -0.46, 0.05], [0.21, 0.13, 0.34], leg);
      return leg;
    });
    const marker = new THREE.Mesh(new THREE.RingGeometry(0.48, 0.57, 24), new THREE.MeshBasicMaterial({ color: '#72c3b0', side: THREE.DoubleSide }));
    marker.rotation.x = -Math.PI / 2; marker.position.y = 0.08; person.add(marker);
    person.traverse(obj => { if (obj.isMesh) { obj.castShadow = false; obj.userData.agentId = agent.id; picking.push(obj); } });
    const label = document.createElement('button');
    label.type = 'button'; label.className = 'world-person'; label.dataset.agent = agent.id;
    const name = document.createElement('b'); name.textContent = agent.name;
    const status = document.createElement('span'); status.textContent = '待命';
    label.append(name, status); labels.append(label);
    label.addEventListener('click', () => bridge.openAgent(agent.id));
    const entry = { agent, seat, group, desk, person, torso, head, arms, legs, screen, deskLamp, marker, label, status, mode: 'desk', path: [], until: 0, nextRest: animationTime + 8 + Math.random() * 22, activity: null, phase: Math.random() * 6 };
    people.set(agent.id, entry);
    return entry;
  }

  const ACTIVITY = { nap: '休息 · 小睡一下', water: '休息 · 裝水', exercise: '休息 · 海風伸展' };
  function resetPose(p) {
    p.head.rotation.set(0, 0, 0); p.torso.rotation.set(0, 0, 0);
    p.arms.forEach(a => a.rotation.set(0, 0, 0)); p.legs.forEach(l => l.rotation.set(0, 0, 0));
  }
  function returnToDesk(p) {
    resetPose(p);
    if (p.activity === 'nap') { p.mode = 'desk'; p.activity = null; p.nextRest = animationTime + 20 + Math.random() * 30; return; }
    // Retrace the actual path, including when a task interrupts a walk halfway through.
    p.path = (p.trail || [new THREE.Vector3(p.seat.x, p.seat.elevation + 0.35, p.seat.z + 0.75)]).slice().reverse();
    p.mode = 'return';
  }
  function startRest(p) {
    // Shared facilities are occupied by at most one colleague at a time.
    const occupied = new Set([...people.values()].filter(a => a.mode !== 'desk').map(a => a.activity));
    const chosen = chooseActivity();
    p.activity = occupied.has(chosen) ? 'nap' : chosen;
    p.until = animationTime + 10 + Math.random() * 12;
    if (p.activity === 'nap') p.mode = 'rest';
    else {
      p.mode = 'walk';
      p.trail = [p.person.position.clone()];
      p.path = breakRoute(p.seat, p.activity).map(point => new THREE.Vector3(...point));
    }
  }
  function updatePerson(p, dt, time) {
    const state = p.agent.state || 'idle';
    const resting = canRest(state) && p.agent.id !== 'boss';
    if (!resting && (p.mode === 'rest' || p.mode === 'walk')) returnToDesk(p);
    if (reduced.matches && p.mode !== 'desk') {
      p.person.position.set(p.seat.x, p.seat.elevation + 0.35, p.seat.z + 0.75); p.mode = 'desk'; p.activity = null; resetPose(p);
    }
    if (!reduced.matches && resting && p.mode === 'desk' && time >= p.nextRest) {
      if ([...people.values()].filter(a => a.mode !== 'desk').length < 4) startRest(p);
      else p.nextRest = time + 5;
    }
    if (p.mode === 'walk' || p.mode === 'return') {
      const next = p.path[0];
      if (next) {
        const delta = next.clone().sub(p.person.position);
        const distance = delta.length();
        const speed = p.mode === 'return' && !resting ? 5 : 3.1;
        if (distance <= dt * speed) { p.person.position.copy(next); p.path.shift(); if (p.mode === 'walk') p.trail.push(next.clone()); }
        else { p.person.position.addScaledVector(delta.normalize(), speed * dt); p.person.rotation.y = Math.atan2(delta.x, delta.z); }
        p.legs.forEach((leg, i) => leg.rotation.x = Math.sin(time * 10 + i * Math.PI) * 0.4);
        p.arms.forEach((arm, i) => arm.rotation.x = -Math.sin(time * 10 + i * Math.PI) * 0.25);
      } else {
        if (p.mode === 'return') { p.mode = 'desk'; p.activity = null; p.nextRest = time + 18 + Math.random() * 30; }
        else { p.mode = 'rest'; p.until = time + 10 + Math.random() * 10; }
        resetPose(p);
      }
    } else if (p.mode === 'rest') {
      if (time >= p.until) returnToDesk(p);
      else if (p.activity === 'nap') { p.head.rotation.x = 0.48; p.head.rotation.z = Math.sin(time * 1.3) * 0.06; }
      else if (p.activity === 'water') { p.person.rotation.y = Math.PI; p.arms[1].rotation.x = -1.8 + Math.sin(time * 1.5) * 0.15; }
      else { p.person.rotation.y = 0; p.arms.forEach((a,i) => a.rotation.z = (i ? 1 : -1) * (1.6 + Math.sin(time * 1.7) * 0.5)); p.head.rotation.z = Math.sin(time * 1.7) * 0.15; }
    } else {
      p.person.rotation.y = Math.PI;
      p.head.rotation.x = 0;
      p.arms.forEach((a,i) => a.rotation.x = !resting && !reduced.matches ? -0.85 + Math.sin(time * 8 + i * 2) * 0.12 : -0.6);
      p.legs.forEach(l => l.rotation.x = -0.65);
    }
    const work = !canRest(state) && !['waiting', 'error'].includes(state);
    const color = state === 'error' ? '#e27c69' : state === 'waiting' ? '#e0b653' : work ? '#73cebd' : '#91a7a4';
    p.marker.material.color.set(color);
    p.screen.material.emissiveIntensity = work ? 0.8 : 0.2 + (dayState?.night || 0) * 0.3;
    p.status.textContent = p.mode === 'return' ? (resting ? '回座位' : '收到工作 · 回座位') : p.mode !== 'desk' ? ACTIVITY[p.activity] : state === 'error' ? '需要協助' : state === 'waiting' ? '等待處理' : work ? '工作中' : p.agent.id === 'boss' ? `${pending} 則待審` : '待命中';
    const onStairs = p.person.position.x > 15 && p.person.position.x < 17 && p.person.position.y > 0.4 && p.person.position.z >= 0.4 && p.person.position.z <= 10.5;
    p.label.dataset.location = onStairs ? 'stairs' : p.person.position.z > 10.8 ? 'terrace' : 'office';
    if (p.mode === 'walk') p.status.textContent = onStairs ? '下樓 · 休息一下' : p.activity === 'water' ? '前往補水站' : '前往海風伸展區';
    if (p.mode === 'return' && onStairs) p.status.textContent = resting ? '上樓 · 回座位' : '收到工作 · 上樓';
    p.label.dataset.activity = p.mode === 'desk' ? 'desk' : p.activity || 'return';
    p.label.dataset.state = state;
    p.label.dataset.floor = String(p.seat.department.level);
    p.label.title = `${p.agent.name}｜${p.seat.department.name}｜${p.status.textContent}\n${p.agent.message || ''}`;
    // Project real 3D anchors into the label layer; buttons remain usable with keyboard.
    const point = p.person.position.clone().add(new THREE.Vector3(0, 2.2, 0)).project(camera);
    const outdoors = p.person.position.z > 10.8 || p.person.position.x > 14.5;
    p.label.hidden = (viewMode !== 'interior' && !outdoors) || point.z > 1 || point.z < -1 || Math.abs(point.x) > 1.02 || Math.abs(point.y) > 1.02;
    p.labelX = (point.x * 0.5 + 0.5) * host.clientWidth;
    p.labelY = (-point.y * 0.5 + 0.5) * host.clientHeight;
    p.labelDepth = point.z;
    p.label.style.transform = `translate(${p.labelX}px,${p.labelY}px) translate(-50%,-100%)`;
    p.label.classList.toggle('muted', activeDepartment !== 'all' && p.seat.department.id !== activeDepartment);
  }

  function arrangeLabels() {
    // At a distant/mobile view, show only names that fit. All people remain clickable
    // in 3D and in the full roster; keyboard focus also reveals a crowded name.
    const occupied = [];
    const entries = [...people.values()].filter(p => !p.label.hidden).sort((a, b) =>
      Number(b.seat.department.id === activeDepartment) - Number(a.seat.department.id === activeDepartment) || a.labelDepth - b.labelDepth);
    for (const p of entries) {
      const width = p.label.offsetWidth, height = p.label.offsetHeight;
      const rect = { left: p.labelX - width / 2, right: p.labelX + width / 2, top: p.labelY - height, bottom: p.labelY };
      const crowded = occupied.some(r => rect.left < r.right + 4 && rect.right > r.left - 4 && rect.top < r.bottom + 4 && rect.bottom > r.top - 4);
      p.label.classList.toggle('crowded', crowded);
      if (!crowded) occupied.push(rect);
    }
  }

  function renderRoster(agents) {
    const roster = document.querySelector('#department-roster');
    roster.replaceChildren();
    DEPARTMENTS.forEach(dept => {
      const group = document.createElement('section'); group.className = 'department-roster';
      group.dataset.department = dept.id; group.style.setProperty('--dept', dept.color);
      const title = document.createElement('h3'); title.textContent = `0${dept.level}F / ${dept.name}`; group.append(title);
      const staff = agents.filter(a => departmentFor(a.id).id === dept.id);
      staff.forEach(a => {
        const button = document.createElement('button'); button.type = 'button'; button.dataset.person = a.id;
        const dot = document.createElement('i'); dot.style.background = a.shirt || dept.color;
        const name = document.createElement('b'); name.textContent = a.name;
        const role = document.createElement('span'); role.textContent = a.title;
        button.append(dot, name, role); button.addEventListener('click', () => bridge.openAgent(a.id)); group.append(button);
      });
      roster.append(group);
    });
    document.querySelector('#staff-total').textContent = `${agents.length - 1} 位同事 · 2 層樓 · 6 個部門`;
  }
  function sync() {
    const state = bridge.getState(); timeZone = state.tz || 'Asia/Taipei';
    const agents = [...state.agents.values(), { id: 'boss', name: '你', title: '老闆 · 審核', shirt: '#d8b56c', hair_color: '#3a332e', state: 'idle' }];
    pending = [...state.drafts.values()].filter(d => ['pending_approval','needs_changes'].includes(d.status)).length;
    const ids = agents.map(a => a.id).join('|');
    if (stage.dataset.staff !== ids) {
      // Shared geometry/materials survive roster changes; only per-person ring geometry/materials are disposed.
      for (const p of people.values()) { p.marker.geometry.dispose(); p.marker.material.dispose(); p.screen.material.dispose(); p.label.remove(); }
      people.clear(); staffGroup.clear(); picking.length = 0;
      const seats = seatLayout(agents);
      agents.forEach((a,i) => createPerson(a, seats.find(s => s.id === a.id), i));
      stage.dataset.staff = ids;
    } else agents.forEach(a => { if (people.has(a.id)) people.get(a.id).agent = a; });
    renderRoster(agents); updateDay();
  }
  function updateDay() {
    dayState = daylightAt(new Date(), timeZone);
    const { daylight, night, phase, hour } = dayState;
    document.body.dataset.worldPhase = phase;
    stage.dataset.phase = phase;
    stage.dataset.lights = night > 0.2 ? 'on' : 'off';
    document.querySelector('#world-time').textContent = dayState.clock;
    document.querySelector('#world-timezone').textContent = timeZone === 'Asia/Taipei' ? '台北時間' : timeZone;
    document.querySelector('#world-weather').textContent = dayState.label;
    document.querySelector('#world-status').textContent = '即時同步';
    const sky = new THREE.Color('#13263f').lerp(new THREE.Color('#b6dadc'), daylight);
    if (phase === 'dawn' || phase === 'dusk') sky.lerp(new THREE.Color('#e5b399'), Math.sin(daylight * Math.PI) * 0.6);
    scene.fog.color.copy(sky);
    stage.style.background = `linear-gradient(${sky.getStyle()}, ${new THREE.Color('#213d50').lerp(new THREE.Color('#e2e4cf'), daylight).getStyle()})`;
    hemi.intensity = 0.4 + daylight * 2.3;
    sunLight.intensity = daylight * 3.2; moonLight.intensity = night * 0.5;
    sunLight.position.set(Math.cos(dayState.sunAngle) * -45, Math.max(8, Math.sin(dayState.sunAngle) * 55), -20);
    sun.visible = hour >= 5.5 && hour < 18.5;
    sun.position.set(-15 - Math.cos(dayState.sunAngle) * 20, 14 + Math.max(0, Math.sin(dayState.sunAngle)) * 6, -35);
    sun.scale.setScalar(1.8);
    moon.visible = !sun.visible;
    moon.position.set(-23 - Math.cos(dayState.moonAngle) * 8, 16 + Math.max(0, Math.sin(dayState.moonAngle)) * 4, -32);
    moon.scale.setScalar(1.4);
    renderer.shadowMap.needsUpdate = true;
    stars.material.opacity = night * 0.85;
    sea.daylight.value = daylight; sea.sky.value.copy(sky); building.setNight(night);
    sand.material.color.copy(new THREE.Color('#82938b').lerp(new THREE.Color('#dccba5'), daylight));
    clouds.forEach(c => { c.visible = daylight > 0.12; });
    lamps.forEach(({ glow, light, pool }) => { glow.material.emissiveIntensity = night * 3; light.intensity = night * 65; pool.material.opacity = night * 0.12; });
    people.forEach(p => { p.deskLamp.material.emissiveIntensity = night * 3; });
  }
  function focusDepartment(id = 'all', immediate = false) {
    activeDepartment = id;
    document.querySelectorAll('[data-world-department]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.worldDepartment === id)));
    const d = DEPARTMENTS.find(d => d.id === id);
    if (d) setMode('interior', false);
    const mobile = host.clientWidth < 600;
    const target = d ? new THREE.Vector3(d.x, d.elevation + 1, d.z) : new THREE.Vector3(0, 3.8, 2);
    let position;
    if (d) position = target.clone().add(new THREE.Vector3(10, 14, 17));
    else if (viewMode === 'interior') position = new THREE.Vector3(...(mobile ? [48, 48, 64] : [34, 36, 43]));
    else if (viewMode === 'terrace') { target.set(-2, 5, 7); position = new THREE.Vector3(...(mobile ? [-35, 30, 48] : [-28, 23, 36])); }
    else position = new THREE.Vector3(...(mobile ? [61, 44, 78] : [36, 27, 44]));
    targetView = { target, position };
    if (immediate || reduced.matches) { camera.position.copy(position); controls.target.copy(target); controls.update(); targetView = null; }
  }
  function setMode(mode, resetCamera = true) {
    viewMode = mode; building.setMode(mode); stage.dataset.view = mode;
    document.querySelectorAll('[data-world-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.worldView === mode)));
    const interior = mode === 'interior';
    document.querySelector('#world-enter').textContent = interior ? '看整棟外觀 ↗' : '走進辦公室 ↗';
    document.querySelector('#world-view-title').textContent = { exterior: 'THE HEADQUARTERS', interior: 'INSIDE THE OFFICE', terrace: 'THE ROOFTOP GARDEN' }[mode];
    document.querySelector('#world-view-description').textContent = { exterior: '海岸總部 · 兩層的日常', interior: '2F 創意製作 / 1F 營運管理', terrace: '屋頂花園 · 留一點空間給靈感' }[mode];
    renderer.shadowMap.needsUpdate = true;
    if (resetCamera) focusDepartment();
  }
  document.querySelector('#world-views').addEventListener('click', event => {
    const button = event.target.closest('[data-world-view]'); if (button) setMode(button.dataset.worldView);
  });
  document.querySelector('#world-enter').addEventListener('click', () => setMode(viewMode === 'interior' ? 'exterior' : 'interior'));
  document.querySelector('#department-nav').addEventListener('click', e => {
    const b = e.target.closest('[data-world-department]'); if (b) focusDepartment(b.dataset.worldDepartment);
  });
  document.querySelector('#world-reset').addEventListener('click', () => focusDepartment());
  document.querySelector('#world-rotate').addEventListener('click', () => {
    targetView = null; const offset = camera.position.clone().sub(controls.target); offset.applyAxisAngle(new THREE.Vector3(0,1,0), Math.PI / 6); camera.position.copy(controls.target).add(offset); controls.update();
  });
  for (const [id, factor] of [['world-in',0.82],['world-out',1.22]]) document.querySelector(`#${id}`).addEventListener('click', () => {
    targetView = null; const offset = camera.position.clone().sub(controls.target); offset.setLength(THREE.MathUtils.clamp(offset.length() * factor, controls.minDistance, controls.maxDistance)); camera.position.copy(controls.target).add(offset); controls.update();
  });
  controls.addEventListener('start', () => { targetView = null; });
  let down;
  renderer.domElement.addEventListener('pointerdown', e => { down = [e.clientX,e.clientY]; });
  renderer.domElement.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX-down[0],e.clientY-down[1]) > 6) return;
    const rect = renderer.domElement.getBoundingClientRect();
    const ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1, -(e.clientY-rect.top)/rect.height*2+1), camera);
    const visiblePeople = picking.filter(obj => {
      const p = people.get(obj.userData.agentId);
      return viewMode === 'interior' || p.person.position.z > 10.8 || p.person.position.x > 14.5;
    });
    const hit = ray.intersectObjects(visiblePeople, false)[0];
    if (hit) bridge.openAgent(hit.object.userData.agentId);
    down = null;
  });
  function handoff(event) {
    if (reduced.matches || deliveries.length >= 6) return;
    const from = people.get(event.detail.from), to = people.get(event.detail.to);
    if (!from || !to) return;
    const paper = box('#fff4c8', [from.seat.x, from.seat.elevation + 2.5, from.seat.z], [0.5, 0.04, 0.7]);
    deliveries.push({ paper, from: paper.position.clone(), to: new THREE.Vector3(to.seat.x,to.seat.elevation + 2.5,to.seat.z), start: animationTime });
  }
  window.addEventListener('office:sync', sync);
  window.addEventListener('office:agent', e => {
    const p = people.get(e.detail.id); if (p) p.agent = e.detail;
  });
  window.addEventListener('office:handoff', handoff);
  document.addEventListener('visibilitychange', () => { hidden = document.hidden; lastFrame = performance.now(); if (!hidden) updateDay(); });
  const resize = new ResizeObserver(() => {
    camera.aspect = host.clientWidth / Math.max(1, host.clientHeight); camera.updateProjectionMatrix();
    renderer.setSize(host.clientWidth, host.clientHeight);
  });
  resize.observe(host);
  renderer.domElement.addEventListener('webglcontextlost', e => {
    e.preventDefault(); disposed = true; renderer.setAnimationLoop(null); controls.dispose(); resize.disconnect();
    bridge.fallback('3D 畫面暫時中斷，已切換平面工作台。重新整理可再試。');
  });
  setMode('exterior', false); focusDepartment('all', true); sync();
  document.body.classList.add('world-ready');
  document.querySelector('#flat-office').open = false;
  const vector = new THREE.Vector3();
  function frame(now) {
    if (disposed || hidden || now - lastFrame < (reduced.matches ? 100 : 32)) return;
    const elapsed = Math.max(0, (now - lastFrame) / 1000);
    const dt = Math.min(0.15, elapsed); lastFrame = now; animationTime += Math.min(60, elapsed);
    if (now - lastClock > 15000) { updateDay(); lastClock = now; }
    if (targetView) {
      camera.position.lerp(targetView.position, 0.1); controls.target.lerp(targetView.target, 0.1);
      if (camera.position.distanceTo(targetView.position) < 0.03) targetView = null;
    }
    controls.update();
    people.forEach(p => updatePerson(p, dt, animationTime));
    arrangeLabels();
    if (!reduced.matches) {
      sea.time.value = animationTime;
      for (let i = deliveries.length - 1; i >= 0; i--) {
        const d = deliveries[i], t = Math.min(1,(animationTime-d.start)/1.6);
        d.paper.position.copy(vector.lerpVectors(d.from,d.to,t)); d.paper.position.y += Math.sin(t*Math.PI)*3;
        d.paper.rotation.y = t*Math.PI;
        if (t === 1) { scene.remove(d.paper); deliveries.splice(i,1); }
      }
    }
    renderer.render(scene, camera);
  }
  renderer.setAnimationLoop(frame);
  // Pause the GPU when the page is gone; the scheduler continues on the server independently.
  window.addEventListener('pagehide', () => { renderer.setAnimationLoop(null); }, { once: true });
  window.addEventListener('pageshow', e => { if (e.persisted && !disposed) { lastFrame = performance.now(); renderer.setAnimationLoop(frame); } });
}
