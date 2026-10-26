// Architecture remains separate from employee/work state. All assets are procedural.
import * as THREE from './vendor/three.module.min.js';

export function buildHeadquarters({ scene, box, sphere, cylinder, sign, foliage }) {
  const structure = new THREE.Group(), envelope = new THREE.Group(), roof = new THREE.Group();
  scene.add(structure, envelope, roof);
  const nightSurfaces = [];
  const stone = '#e9e2d4', frame = '#334e4b', timber = '#b58c60';
  const glass = { transparent: true, opacity: 0.32, depthWrite: false, roughness: 0.08, metalness: 0.42, envMapIntensity: 1.25 };
  function glazing(p, s, parent = envelope) {
    const pane = box('#87b3ad', p, s, parent, glass); pane.castShadow = false;
    return pane;
  }
  function plaque(text, sub, p, width, parent = structure, color = '#274c3e', background) {
    const board = sign(text, sub, p, width, color, background); parent.attach(board); return board;
  }
  function strip(p, s, parent = structure) {
    const light = box('#fff1cf', p, s, parent, { emissive: '#ffd6a0', emissiveIntensity: 0.1 });
    nightSurfaces.push(light.material); return light;
  }
  function planter(x, y, z, width = 3, parent = roof) {
    box('#cec6b2', [x, y + 0.22, z], [width, 0.45, 0.9], parent);
    box('#586951', [x, y + 0.46, z], [width - 0.12, 0.04, 0.75], parent);
    for (let i = 0; i < Math.ceil(width); i++) {
      foliage.plant(x - width / 2 + .5 + i, y + .46, z, .55, parent);
    }
  }

  // A true second floor at 5.4 m, with a continuous front gallery and east stair.
  box(stone, [0, 5.42, -4.5], [29.3, 0.36, 12.3], structure);
  box(frame, [0, 5.64, 1.6], [29.5, 0.1, 0.2], structure);
  for (const x of [-14.1, -4.5, 4.5, 14.1]) {
    box(stone, [x, 2.9, -9.9], [0.38, 5.3, 0.45], structure);
    box(stone, [x, 2.9, 0.8], [0.38, 5.3, 0.45], structure);
    box(stone, [x, 8.05, -9.9], [0.26, 4.9, 0.3], structure);
  }
  // Layered rear and west elevations: stone plinths, bronze window frames, sun fins.
  for (const y of [0, 5.4]) {
    box(stone, [0, y + 0.8, -10.45], [29, 1.15, 0.25], structure);
    box(frame, [0, y + 4.85, -10.45], [29.3, 0.18, 0.25], structure);
    for (let i = 0; i < 7; i++) {
      const x = -14 + i * 4.66;
      box(frame, [x, y + 2.9, -10.45], [0.08, 3.8, 0.16], structure);
      if (i < 6) glazing([x + 2.3, y + 2.9, -10.45], [4.5, 3.7, 0.04], structure);
    }
    for (let z = -10; z <= 0; z += 2.7) {
      box(timber, [-14.5, y + 2.6, z], [0.35, 4.7, 0.12], structure);
      glazing([-14.3, y + 2.8, z + 1.1], [0.04, 4.3, 2.1], structure);
    }
  }
  // Front lower facade, inset double doors, continuous signage and entrance canopy.
  box(stone, [0, 4.9, 10.55], [29.6, 0.85, 0.6], envelope);
  strip([0, 4.42, 10.9], [28.5, 0.06, 0.08], envelope);
  for (const x of [-14.2, -10.7, -7.2, -3.7, 3.7, 7.2, 10.7, 14.2]) {
    box(frame, [x, 2.45, 10.55], [0.1, 4.2, 0.18], envelope);
    if (x < -3.7 || (x >= 3.7 && x < 14)) glazing([x + 1.7, 2.45, 10.55], [3.3, 4.1, 0.05]);
  }
  for (const x of [-1.25, 1.25]) {
    glazing([x, 2.2, 10.3], [2.4, 3.8, 0.06]);
    box(frame, [x + (x < 0 ? 1.13 : -1.13), 2.2, 10.35], [0.08, 3.9, 0.08], envelope);
    box('#c9b27c', [x + (x < 0 ? 0.95 : -0.95), 2, 10.45], [0.045, 0.65, 0.06], envelope);
  }
  box(frame, [0, 4.2, 12], [7.5, 0.18, 3.4], envelope);
  for (let x = -3.5; x <= 3.5; x += 0.45) box(timber, [x, 4.08, 12], [0.12, 0.12, 3.3], envelope);
  plaque('U N I W A Y', 'COASTAL HEADQUARTERS', [0, 4.96, 10.88], 6.1, envelope, '#f4e8c8', '#153f35');
  box('#e3dccd', [0, 0.29, 11.6], [6.7, 0.14, 2.2], structure);
  // Side glazing leaves an exit beside the staircase and shared terrace.
  glazing([14.3, 2.5, 4], [0.05, 4.2, 8.3]);
  for (const z of [-0.2, 3.8, 8.2]) box(frame, [14.3, 2.5, z], [0.13, 4.5, 0.13], envelope);
  box(stone, [14.3, 4.9, 4.5], [0.5, 0.85, 10.5], envelope);
  // Upper studios open onto a shared gallery; walls and roof retract in cutaway mode.
  box(stone, [0, 10.4, -4.5], [30.1, 0.45, 12.9], roof);
  box('#c4bfac', [0, 10.68, -4.5], [29.6, 0.12, 12.4], roof);
  for (const x of [-14.4, -4.7, 4.7, 14.4]) box(frame, [x, 8.05, 1.5], [0.13, 4.7, 0.14], envelope);
  for (const x of [-9.55, 0, 9.55]) {
    glazing([x, 8.05, 1.5], [9.2, 4.6, 0.045]);
    box(frame, [x, 8.05, 1.5], [0.07, 4.6, 0.1], envelope);
    strip([x, 10.03, 1.55], [9.1, 0.06, 0.08], envelope);
  }
  glazing([14.3, 8, -4.6], [0.05, 4.6, 11.9]);
  // Permanent slender roof beams keep the building's outline legible in section.
  for (const x of [-14.4, 14.4]) box(frame, [x, 10.2, -4.5], [0.14, 0.18, 12.4], structure);
  box('#b39256', [0, 10.5, 1.96], [8.2, 2.2, .12], roof, { metalness: .65, roughness: .35 });
  plaque('U N I W A Y', 'COASTAL HEADQUARTERS', [0, 10.5, 2.03], 8, roof, '#f4e8c8', '#153f35');

  // Joinery, facade reveals and gutters give the building a finished exterior.
  for (const x of [-12.4, 12.4]) {
    for (let i = 0; i < 11; i++) box(timber, [x - 1.2 + i * .24, 2.5, 10.65], [.18, 3.95, .16], envelope);
    box(frame, [x, .48, 10.7], [2.7, .14, .18], envelope);
    box(frame, [x, 4.43, 10.7], [2.7, .14, .18], envelope);
  }
  for (const y of [5.12, 10.17]) {
    const z = y > 6 ? 1.85 : 10.83;
    box(frame, [0, y, z], [29.5, .08, .09], y > 6 ? roof : envelope);
  }
  for (const x of [-14.55, 14.55]) {
    cylinder(frame, [x, 5.2, -10.6], [.07, 10.1, .07], structure);
    for (const y of [1.2, 4.1, 7.4, 9.7]) box('#b39256', [x, y, -10.6], [.19, .05, .2], structure, { metalness: .6, roughness: .4 });
  }
  box(frame, [0, 10.65, -10.9], [30.1, .13, .22], roof);
  for (const x of [-14, 14]) for (const z of [2, 6.2, 10.4]) {
    box(frame, [x, 5.8, z], [.22, .07, .25], roof);
    box(frame, [x, 6.43, z], [.04, 1.25, .04], roof);
  }

  // Roof garden above the lower offices: decking, pergola, lounge and planting.
  box(stone, [0, 5.42, 6.2], [29.3, 0.36, 9.3], roof);
  box('#c4a683', [0, 5.66, 6.2], [28.8, 0.12, 8.9], roof);
  for (let z = 1.9; z < 10.5; z += 0.45) box('#ad8e6d', [0, 5.73, z], [28.7, 0.015, 0.022], roof);
  for (const x of [-14, 14]) {
    glazing([x, 6.4, 6.2], [0.04, 1.3, 8.6], roof);
    box(frame, [x, 7.1, 6.2], [0.07, 0.06, 8.6], roof);
  }
  glazing([0, 6.4, 10.55], [28.1, 1.3, 0.04], roof);
  box(frame, [0, 7.1, 10.55], [28.1, 0.06, 0.07], roof);
  for (const x of [-12.5, -5.5]) for (const z of [3.2, 9.4]) box(frame, [x, 7.2, z], [0.14, 3, 0.14], roof);
  for (let x = -12.7; x <= -5.3; x += 0.44) box(timber, [x, 8.8, 6.3], [0.16, 0.2, 6.7], roof);
  strip([-9, 8.64, 3.2], [7.2, 0.06, 0.08], roof);
  strip([-9, 8.64, 9.4], [7.2, 0.06, 0.08], roof);
  for (const x of [-11.7, -6.4]) {
    box('#ece5d8', [x, 6.17, 6.5], [1.2, 0.6, 3.1], roof);
    box('#6a8070', [x, 6.6, 6.5], [0.22, 0.65, 3.2], roof);
    for (const z of [5.6, 6.5, 7.4]) box('#d6b07d', [x, 6.54, z], [0.9, 0.16, 0.75], roof);
  }
  cylinder('#c2ac8a', [-9, 6.2, 6.5], [1, 0.16, 1], roof);
  cylinder(frame, [-9, 5.95, 6.5], [0.12, 0.5, 0.12], roof);
  planter(9, 5.75, 9.4, 7); planter(2, 5.75, 9.4, 4); planter(12.8, 5.75, 4, 2);
  // Smaller coconut palms continue the coastal planting onto the roof garden.
  for (const x of [2, 10]) {
    cylinder('#c6bca5', [x, 6.05, 5], [0.8, 0.65, 0.8], roof);
    foliage.palm(x, 6.3, 5, .42, roof);
  }
  // Rooftop solar panels and a low service screen, visible on an orbit around the HQ.
  for (const x of [-9, -4.7, 4.7, 9]) for (const z of [-7, -3]) {
    box('#b7b7a8', [x, 10.84, z], [3.7, 0.16, 2.8], roof);
    const panel = box('#284858', [x, 11, z], [3.5, 0.08, 2.6], roof, { roughness: 0.24, metalness: 0.4 }); panel.rotation.x = -0.08;
    for (let i = -1; i <= 1; i++) box('#759497', [x + i * 0.86, 11.12, z], [0.025, 0.025, 2.5], roof);
    for (let i = -1; i <= 1; i++) box('#759497', [x, 11.12 - i * .065, z + i * .8], [3.4, .02, .025], roof);
  }
  box(stone, [0, 11.1, -8.2], [3.5, 0.8, 2.7], roof);
  for (let z = -9.3; z <= -7.1; z += 0.3) box(frame, [0, 11.53, z], [3.2, 0.05, 0.07], roof);

  // East staircase: 20 real treads and continuous handrails, matching breakRoute.
  box('#d3c9b7', [16, 0.15, 5.5], [3.2, 0.25, 12.8], structure);
  box(stone, [15.5, 5.44, 0], [3.4, 0.3, 1.5], structure);
  for (let i = 1; i <= 20; i++) {
    const z = 10.75 - i * 0.5, y = 0.3 + i * 0.27;
    box('#d8ccba', [16, y - 0.1, z], [2.25, 0.2, 0.5], structure);
    strip([16, y + 0.012, z + 0.23], [2.12, 0.025, 0.03], structure);
    if (i % 4 === 0) for (const x of [14.85, 17.15]) box(frame, [x, y + 0.5, z], [0.045, 1, 0.045], structure);
  }
  for (const x of [14.85, 17.15]) {
    const rail = box(frame, [x, 4.05, 5.5], [0.065, 0.065, 11.36], structure); rail.rotation.x = Math.atan(0.54);
  }
  plaque('02', 'CREATIVE', [16, 6.5, -0.6], 1.5);
  plaque('01', 'OPERATIONS', [14.6, 1.8, 10.9], 1.5);
  // Ground-floor lobby behind the operational studios.
  box('#d0b493', [0, 1.1, -6.3], [5.5, 1.5, 1.2], structure);
  box('#eee7d9', [0, 1.9, -6.3], [5.7, 0.1, 1.4], structure);
  strip([0, 0.6, -5.67], [4.8, 0.06, 0.04]);
  plaque('U N I W A Y', 'WELCOME TO THE COAST', [0, 3.2, -10.27], 8);
  for (const x of [-10, -6.7]) {
    box('#748f83', [x, 0.8, -6.5], [2.7, 0.65, 1.15], structure);
    box('#748f83', [x, 1.25, -6.95], [2.7, 0.75, 0.24], structure);
  }
  cylinder('#ccba9a', [-8.4, 0.85, -4.5], [1.1, 0.13, 0.7], structure);
  planter(10, 0.3, -7.5, 5, structure);
  // Arrival marker and promenade lights anchor the building to its site.
  box(stone, [-12.3, 1.25, 17], [3, 2.4, 0.45], structure);
  plaque('UniWay', '海岸總部 / 01', [-12.3, 1.45, 17.24], 2.6);
  for (const x of [-10, -4, 4, 11]) {
    cylinder(frame, [x, 0.65, 16.2], [0.1, 1.15, 0.1], structure);
    strip([x, 1.18, 16.2], [0.19, 0.2, 0.19]);
  }
  const entryLight = new THREE.PointLight('#ffd8a0', 0, 12, 2);
  entryLight.position.set(0, 3.5, 12); scene.add(entryLight);
  const gardenLight = new THREE.PointLight('#ffe2b4', 0, 16, 2);
  gardenLight.position.set(-7, 8.5, 6.5); roof.add(gardenLight);

  // Consolidate repeated static details into instanced draws, separately per view layer.
  for (const layer of [structure, envelope, roof]) {
    layer.updateMatrixWorld(true);
    const batches = new Map();
    layer.traverse(obj => {
      if (!obj.isMesh || obj.material.transparent || obj.material.isMeshBasicMaterial) return;
      if (!batches.has(obj.geometry)) batches.set(obj.geometry, new Map());
      const materials = batches.get(obj.geometry);
      if (!materials.has(obj.material)) materials.set(obj.material, []);
      materials.get(obj.material).push(obj);
    });
    for (const members of [...batches.values()].flatMap(materials => [...materials.values()])) {
      if (members.length < 3) continue;
      const batch = new THREE.InstancedMesh(members[0].geometry, members[0].material, members.length);
      batch.customDepthMaterial = members[0].customDepthMaterial;
      members.forEach((obj, i) => { batch.setMatrixAt(i, obj.matrixWorld); obj.removeFromParent(); });
      batch.castShadow = true; batch.receiveShadow = true; layer.add(batch);
    }
  }
  return {
    setMode(mode) { envelope.visible = roof.visible = mode !== 'interior'; },
    setNight(amount) {
      nightSurfaces.forEach(material => { material.emissiveIntensity = 0.1 + amount * 2.1; });
      entryLight.intensity = amount * 75;
      gardenLight.intensity = amount * 70;
      entryLight.visible = gardenLight.visible = amount > .001;
    },
  };
}
