import * as THREE from './vendor/three.module.min.js';

// Seeded surface detail stays identical across reloads and never consumes the
// employee simulation's random stream. No remote textures or models are needed.
function randomSource(seed) {
  return () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
}

function surfaceTexture(kind, renderer) {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 256;
  const ctx = canvas.getContext('2d'), pixels = ctx.createImageData(256, 256), random = randomSource(917);
  for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
    const noise = random() - 0.5;
    const grain = Math.sin(x * 0.55 + Math.sin(y * 0.055) * 2 + Math.sin(x * 0.12) * 3);
    let value = 238 + noise * 23;
    if (kind === 'wood') value = 216 + grain * 23 + noise * 15 + Math.sin(x * 2.4 + y * 0.015) * 8;
    if (kind === 'stone') value = 237 + noise * 20 + Math.sin(y * 0.16 + Math.sin(x * 0.04)) * 7;
    if (kind === 'fabric') value = 226 + (x % 3 === 0 || y % 3 === 0 ? -20 : 7) + noise * 10;
    if (kind === 'bark') value = 193 + Math.sin(y * 0.65 + Math.sin(x * 0.07) * 0.7) * 28 + noise * 24;
    const i = (y * 256 + x) * 4;
    pixels.data[i] = pixels.data[i + 1] = pixels.data[i + 2] = value; pixels.data[i + 3] = 255;
  }
  ctx.putImageData(pixels, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
  if (kind === 'wood') texture.repeat.set(1, 3);
  if (kind === 'bark') texture.repeat.set(2, 5);
  return texture;
}

export function createResortSurfaces(renderer, scene) {
  const textures = Object.fromEntries(['wood', 'stone', 'fabric', 'bark', 'sand'].map(kind => [kind, surfaceTexture(kind, renderer)]));
  const wood = new Set(['#b58c60', '#c4a683', '#d1b899', '#b09271', '#bf8a65', '#c49f77', '#c8af87', '#ac8d66', '#d0b493']);
  const stone = new Set(['#e9e2d4', '#d8ccba', '#e3dccd', '#ddd4c2', '#e3d9c5', '#eee8dc', '#eee5d5', '#cec6b2', '#c6bca5']);
  const darkMetal = new Set(['#334e4b', '#304b49', '#516c68', '#688b80']);
  const fabric = new Set(['#ece5d8', '#d6b07d', '#6a8070', '#748f83']);
  const cache = new Map();
  function material(color, extras = {}) {
    const key = `${color}:${JSON.stringify(extras)}`;
    if (!cache.has(key)) {
      let params = { color, roughness: 0.72 };
      if (wood.has(color)) params = { color: color === '#c4a683' ? '#b67a43' : '#9b6134', map: textures.wood, bumpMap: textures.wood, bumpScale: 0.035, roughness: 0.54 };
      if (stone.has(color)) params = { color: '#f1e3c9', map: textures.stone, bumpMap: textures.stone, bumpScale: 0.04, roughness: 0.86 };
      if (darkMetal.has(color)) params = { color: '#183d36', metalness: 0.48, roughness: 0.32 };
      if (fabric.has(color)) params = { color: color === '#d6b07d' ? '#bc633e' : color === '#ece5d8' ? '#f7ead4' : '#285b49', map: textures.fabric, roughness: 0.95, bumpMap: textures.fabric, bumpScale: 0.015 };
      cache.set(key, new THREE.MeshStandardMaterial({ ...params, ...extras }));
    }
    return cache.get(key);
  }
  // A local sky panorama supplies soft reflected highlights on glass and metal.
  const panorama = document.createElement('canvas'); panorama.width = 512; panorama.height = 256;
  const ctx = panorama.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 256);
  [[0, '#2d79a4'], [.45, '#b9dfec'], [.5, '#e8f0df'], [.65, '#628c86'], [1, '#1b433d']].forEach(([at, color]) => gradient.addColorStop(at, color));
  ctx.fillStyle = gradient; ctx.fillRect(0, 0, 512, 256);
  const sun = ctx.createRadialGradient(160, 60, 2, 160, 60, 46);
  sun.addColorStop(0, '#fffbea'); sun.addColorStop(.15, '#fffbea'); sun.addColorStop(1, '#fffbea00');
  ctx.fillStyle = sun; ctx.fillRect(110, 10, 100, 100);
  const skyTexture = new THREE.CanvasTexture(panorama); skyTexture.colorSpace = THREE.SRGBColorSpace;
  skyTexture.mapping = THREE.EquirectangularReflectionMapping;
  const pmrem = new THREE.PMREMGenerator(renderer), environment = pmrem.fromEquirectangular(skyTexture);
  scene.environment = environment.texture; scene.environmentIntensity = 0.55;
  skyTexture.dispose(); pmrem.dispose();
  return { material, textures, environment };
}

const coastWaves = [[3, 0.032, 0.6], [5, 0.018, 1.2]];
export const coastRadius = angle => 1 + coastWaves.reduce((sum, [frequency, amplitude, phase]) => sum + Math.sin(angle * frequency + phase) * amplitude, 0);
export const COAST_GLSL = `float coastRadius(float a) { return 1.0 ${coastWaves.map(([f, a, p]) => `+ ${a.toFixed(6)} * sin(a * ${f.toFixed(1)} + ${p.toFixed(6)})`).join(' ')}; }`;

export function createBeachGeometry() {
  const rings = [[0, -.52], [.65, -.52], [.85, -.55], [.95, -.7], [1, -.87], [1.08, -1.2], [1.18, -1.65]];
  const positions = [], colors = [], uv = [], indices = [], segments = 128;
  rings.forEach(([radius, height], row) => {
    for (let i = 0; i <= segments; i++) {
      const a = i / segments * Math.PI * 2, r = radius * coastRadius(a);
      const x = Math.sin(a) * r * 26, z = Math.cos(a) * r * 23 + 2;
      positions.push(x, height, z); uv.push(x / 6, z / 6);
      const wet = THREE.MathUtils.smoothstep(radius, .93, 1.1);
      const color = new THREE.Color('#f5dda4').lerp(new THREE.Color('#a88d59'), wet);
      colors.push(color.r, color.g, color.b);
      if (row && i) {
        const c = row * (segments + 1) + i, b = c - segments - 1;
        indices.push(c - 1, b, b - 1, c - 1, c, b);
      }
    }
  });
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geometry.setIndex(indices); geometry.computeVertexNormals();
  return geometry;
}

export function createResortBeach(scene, surfaces) {
  const material = new THREE.MeshStandardMaterial({ vertexColors: true, map: surfaces.textures.sand, bumpMap: surfaces.textures.sand, bumpScale: .03, roughness: 1 });
  const beach = new THREE.Mesh(createBeachGeometry(), material);
  beach.receiveShadow = true; scene.add(beach); return beach;
}

// Curved leaf strips include a raised centre vein, shaded edges and tapered tips.
function leafBuilder() {
  const positions = [], colors = [], weights = [], indices = [];
  function blade(start, control, end, width, color, wind = 1, segments = 5) {
    const curve = new THREE.QuadraticBezierCurve3(start, control, end);
    const base = positions.length / 3;
    for (let i = 0; i <= segments; i++) {
      const t = i / segments, center = curve.getPoint(t), tangent = curve.getTangent(t);
      const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
      const breadth = Math.pow(Math.sin(Math.PI * t), .75) * width;
      for (const j of [-1, 0, 1]) {
        const point = center.clone().addScaledVector(side, j * breadth);
        point.y += j === 0 ? breadth * .3 : -breadth * .08;
        positions.push(point.x, point.y, point.z);
        const shade = color.clone().multiplyScalar(j === 0 ? 1.16 : .88 + t * .06);
        colors.push(shade.r, shade.g, shade.b); weights.push(wind * t);
      }
      if (i) for (let j = 0; j < 2; j++) {
        const n = base + i * 3 + j;
        indices.push(n - 3, n, n + 1, n - 3, n + 1, n - 2);
      }
    }
  }
  function finish() {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geometry.setAttribute('windWeight', new THREE.Float32BufferAttribute(weights, 1));
    geometry.setIndex(indices); geometry.computeVertexNormals(); geometry.computeBoundingSphere();
    geometry.boundingSphere.radius += .25; // keep wind-deformed tips inside the culling bound
    return geometry;
  }
  return { blade, finish };
}

export function createPalmCrownGeometry() {
  const builder = leafBuilder();
  for (let frond = 0; frond < 11; frond++) {
    const angle = frond * 2.39996, length = 3.7 + Math.sin(frond * 7.1) * .65;
    const direction = new THREE.Vector3(Math.sin(angle), 0, Math.cos(angle));
    const side = new THREE.Vector3(direction.z, 0, -direction.x);
    const color = new THREE.Color(['#28612d', '#3a7b33', '#537f35', '#1d592d'][frond % 4]);
    const point = t => direction.clone().multiplyScalar(t * length).setY(Math.sin(t * Math.PI) * (frond % 3 === 0 ? 1.4 : .8) - t * t * 1.25);
    builder.blade(point(0), point(.5).add(new THREE.Vector3(0, .3, 0)), point(1), .038, new THREE.Color('#8a9847'), .35, 14);
    for (let i = 1; i <= 19; i++) {
      const t = .08 + i / 21 * .86, root = point(t);
      const extent = Math.pow(Math.sin(t * Math.PI), .7) * (1.1 + length * .08);
      for (const s of [-1, 1]) {
        const end = root.clone().addScaledVector(side, s * extent).addScaledVector(direction, .42 + t * .25); end.y -= .28 + extent * .18;
        const control = root.clone().lerp(end, .48); control.y += .16;
        builder.blade(root, control, end, .075 + (1 - t) * .035, color, .6 + t * .5, 4);
      }
    }
  }
  return builder.finish();
}

export function createTropicalLeafGeometry() {
  const builder = leafBuilder();
  for (let i = 0; i < 11; i++) {
    const a = i * 2.39996, length = 1.05 + (i % 3) * .23;
    const root = new THREE.Vector3(0, .12, 0);
    const end = new THREE.Vector3(Math.sin(a) * length, .45 + (i % 4) * .18, Math.cos(a) * length);
    const control = end.clone().multiplyScalar(.42); control.y = 1.5 + i % 3 * .15;
    builder.blade(root, control, end, .19 + i % 2 * .06, new THREE.Color(['#1f683d', '#3c7d40', '#648b3b'][i % 3]), .6, 7);
  }
  return builder.finish();
}

export function createFoliage(surfaces) {
  const time = { value: 0 };
  const vertexWind = `attribute float windWeight; uniform float foliageTime;\n`;
  const bend = `#include <begin_vertex>
    transformed.x += sin(foliageTime * 0.7 + position.z * 0.8 + position.y * 0.3) * windWeight * 0.10;
    transformed.z += cos(foliageTime * 0.53 + position.x * 0.6) * windWeight * 0.065;`;
  const leaves = new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: .72, emissive: '#133d14', emissiveIntensity: .12 });
  leaves.onBeforeCompile = shader => {
    shader.uniforms.foliageTime = time;
    shader.vertexShader = vertexWind + shader.vertexShader.replace('#include <begin_vertex>', bend);
  };
  leaves.customProgramCacheKey = () => 'coastal-foliage-v1';
  const depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side: THREE.DoubleSide });
  depth.onBeforeCompile = leaves.onBeforeCompile; depth.customProgramCacheKey = () => 'coastal-foliage-depth-v1';
  const crown = createPalmCrownGeometry(), shrub = createTropicalLeafGeometry();
  const trunkCurve = new THREE.CatmullRomCurve3([new THREE.Vector3(), new THREE.Vector3(.12, 2, .05), new THREE.Vector3(.42, 4.6, .12), new THREE.Vector3(.78, 6.8, .2)]);
  const trunk = new THREE.TubeGeometry(trunkCurve, 32, .22, 10, false);
  const trunkMaterial = new THREE.MeshStandardMaterial({ color: '#a38252', map: surfaces.textures.bark, bumpMap: surfaces.textures.bark, bumpScale: .08, roughness: .92 });
  const fruitGeometry = new THREE.SphereGeometry(.17, 8, 6), fruitMaterial = new THREE.MeshStandardMaterial({ color: '#6b6635', roughness: .85 });
  function leafMesh(geometry) {
    const mesh = new THREE.Mesh(geometry, leaves); mesh.castShadow = mesh.receiveShadow = true; mesh.customDepthMaterial = depth; return mesh;
  }
  return {
    time,
    palm(x, y, z, size, parent) {
      const group = new THREE.Group(); group.position.set(x, y, z); group.scale.setScalar(size); group.rotation.y = x * .17; parent.add(group);
      const stem = new THREE.Mesh(trunk, trunkMaterial); stem.castShadow = stem.receiveShadow = true; group.add(stem);
      const canopy = leafMesh(crown); canopy.position.copy(trunkCurve.getPoint(1)); group.add(canopy);
      for (let i = 0; i < 4; i++) {
        const fruit = new THREE.Mesh(fruitGeometry, fruitMaterial); fruit.position.set(.78 + Math.sin(i * 2.4) * .24, 6.55, .2 + Math.cos(i * 2.4) * .24); group.add(fruit);
      }
      return group;
    },
    plant(x, y, z, size, parent) {
      const mesh = leafMesh(shrub); mesh.position.set(x, y, z); mesh.scale.setScalar(size); mesh.rotation.y = x + z; parent.add(mesh); return mesh;
    },
  };
}

export function addBeachLounge({ scene, box, cylinder, foliage }) {
  const group = new THREE.Group(); group.position.set(9, -.5, 19); group.rotation.y = -.4; scene.add(group);
  for (const x of [-1.2, 1.2]) {
    box('#b58c60', [x, .4, 0], [1.5, .16, 3.3], group);
    for (const z of [-1.3, 1.3]) box('#334e4b', [x, .15, z], [1.3, .45, .08], group);
    box('#ece5d8', [x, .55, .35], [1.32, .2, 2.3], group);
    const back = box('#ece5d8', [x, .83, -1], [1.32, .2, 1.15], group); back.rotation.x = .4;
    box('#d6b07d', [x, .72, 1], [1.36, .06, .55], group);
  }
  cylinder('#b58c60', [0, 1.85, -2.1], [.045, 3.7, .045], group);
  const positions = [], indices = [], colors = [];
  for (let ring = 0; ring <= 5; ring++) for (let i = 0; i <= 64; i++) {
    const a = i / 64 * Math.PI * 2, radius = ring / 5 * 2.65;
    const scallop = ring === 5 ? Math.pow(Math.sin(a * 4), 2) * .12 : 0;
    positions.push(Math.sin(a) * radius, 3.7 - Math.pow(ring / 5, 1.4) * .65 - scallop, Math.cos(a) * radius - 2.1);
    const c = new THREE.Color(Math.floor((i % 64) / 8) % 2 ? '#e4c9a1' : '#fff2d9'); colors.push(c.r, c.g, c.b);
    if (ring && i) { const n = ring * 65 + i; indices.push(n - 1, n - 66, n - 65, n - 1, n - 65, n); }
  }
  const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3)); geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3)); geometry.setIndex(indices); geometry.computeVertexNormals();
  const canopy = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: .95 })); canopy.castShadow = true; group.add(canopy);
  cylinder('#e9e2d4', [0, .65, 1.9], [.65, .12, .65], group);
  cylinder('#b58c60', [0, .3, 1.9], [.12, .6, .12], group);
  cylinder('#d6b07d', [.15, .83, 1.9], [.08, .25, .08], group);
  foliage.plant(5.8, -.5, 19, .8, scene);
}
