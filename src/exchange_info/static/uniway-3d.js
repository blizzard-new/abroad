/* UniWay 3D & Interactive Visual Engine
 * Real-time WebGL + Custom GLSL Shaders (Procedural 3D Globe, Great-Circle Flight Ribbons, Orbital Particle Field)
 * + Platform-wide 3D Perspective Card Tilt & Specular Spotlight.
 * External script (CSP script-src 'self' compliant), zero external dependencies.
 */
(() => {
  "use strict";
  if (window.UniWay3D) return;

  const TAIWAN = { name: "臺灣（出發地）", lat: 25.033, lon: 121.565 };

  const GLOBAL_HUBS = [
    {
      id: "jp",
      label: "日本・東京／東北",
      title: "日本交換航線｜東京・東北・京都",
      meta: "航程約 2,100 km · 亞洲最熱門交換目的地 · 涵蓋東北大學、早稻田、立命館等合作校",
      countryFilter: "日本",
      lat: 35.68,
      lon: 139.76,
      color: [0.09, 0.72, 0.89],
    },
    {
      id: "de",
      label: "德國・慕尼黑／海德堡",
      title: "德國交換航線｜慕尼黑・海德堡・柏林",
      meta: "航程約 9,300 km · 歐洲理工與商管重鎮 · 豐富英語授課學程與免學費交換名額",
      countryFilter: "德國",
      lat: 48.14,
      lon: 11.58,
      color: [0.54, 0.44, 0.92],
    },
    {
      id: "us",
      label: "美國・加州／西雅圖",
      title: "北美交換航線｜加州・西雅圖・波士頓",
      meta: "航程約 10,400 km · 頂尖研究型學府與矽谷創新圈 · 學期交換與雙聯學位多元選擇",
      countryFilter: "美國",
      lat: 37.77,
      lon: -122.42,
      color: [0.94, 0.42, 0.35],
    },
    {
      id: "uk",
      label: "英國・倫敦／曼徹斯特",
      title: "歐洲交換航線｜英國・法國・荷蘭",
      meta: "航程約 9,700 km · 經典人文社科與金融學府 · 深度體驗歐洲跨文化學術生活",
      countryFilter: "英國",
      lat: 51.51,
      lon: -0.13,
      color: [0.22, 0.68, 0.96],
    },
    {
      id: "au",
      label: "澳洲・雪梨／墨爾本",
      title: "大洋洲交換航線｜雪梨・墨爾本・布里斯本",
      meta: "航程約 7,200 km · 南半球英語留學首選 · 氣候宜人、時差小且生活機能完善",
      countryFilter: "澳洲",
      lat: -33.87,
      lon: 151.21,
      color: [0.16, 0.78, 0.62],
    },
    {
      id: "kr",
      label: "韓國・首爾",
      title: "韓國交換航線｜首爾・釜山",
      meta: "航程約 1,480 km · 亞洲創新與文化樞紐 · 英語與韓語授課雙軌課程齊全",
      countryFilter: "韓國",
      lat: 37.57,
      lon: 126.98,
      color: [0.95, 0.62, 0.24],
    },
  ];

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const DEG2RAD = Math.PI / 180;

  function latLonToVec3(lat, lon, radius = 1) {
    const phi = (90 - lat) * DEG2RAD;
    const theta = (lon + 180) * DEG2RAD;
    const sinPhi = Math.sin(phi);
    return [
      -radius * sinPhi * Math.cos(theta),
      radius * Math.cos(phi),
      radius * sinPhi * Math.sin(theta),
    ];
  }

  function normalize3(v) {
    const len = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / len, v[1] / len, v[2] / len];
  }

  function cross3(a, b) {
    return [
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0],
    ];
  }

  function slerp3(a, b, t) {
    const na = normalize3(a);
    const nb = normalize3(b);
    let dot = Math.max(-1, Math.min(1, na[0] * nb[0] + na[1] * nb[1] + na[2] * nb[2]));
    const omega = Math.acos(dot);
    if (omega < 1e-4) {
      return normalize3([
        na[0] + (nb[0] - na[0]) * t,
        na[1] + (nb[1] - na[1]) * t,
        na[2] + (nb[2] - na[2]) * t,
      ]);
    }
    const sinOmega = Math.sin(omega);
    const s0 = Math.sin((1 - t) * omega) / sinOmega;
    const s1 = Math.sin(t * omega) / sinOmega;
    return [na[0] * s0 + nb[0] * s1, na[1] * s0 + nb[1] * s1, na[2] * s0 + nb[2] * s1];
  }

  function mat4Perspective(fovRad, aspect, near, far) {
    const f = 1 / Math.tan(fovRad / 2);
    const nf = 1 / (near - far);
    return new Float32Array([
      f / aspect, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (far + near) * nf, -1,
      0, 0, 2 * far * near * nf, 0,
    ]);
  }

  function mat4ModelView(yaw, pitch, dist, tx = 0.14, ty = -0.02) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    // Rotate Y (yaw) then Rotate X (pitch), then translate in view space
    return new Float32Array([
      cy, sp * sy, -cp * sy, 0,
      0, cp, sp, 0,
      sy, -sp * cy, cp * cy, 0,
      tx, ty, -dist, 1,
    ]);
  }

  // ---- Custom GLSL Shaders -----------------------------------------------------------------------------------------
  const GLOBE_VERT = `
    attribute vec3 a_pos;
    attribute vec2 a_uv;
    uniform mat4 u_proj;
    uniform mat4 u_view;
    varying vec3 v_normal;
    varying vec3 v_worldPos;
    varying vec3 v_viewPos;
    varying vec2 v_uv;
    void main() {
      vec4 viewPos = u_view * vec4(a_pos, 1.0);
      v_worldPos = normalize(a_pos);
      v_normal = normalize((u_view * vec4(a_pos, 0.0)).xyz);
      v_viewPos = viewPos.xyz;
      v_uv = a_uv;
      gl_Position = u_proj * viewPos;
    }
  `;

  const GLOBE_FRAG = `
    precision highp float;
    varying vec3 v_normal;
    varying vec3 v_worldPos;
    varying vec3 v_viewPos;
    varying vec2 v_uv;
    uniform float u_time;
    uniform float u_dark;
    uniform float u_stageMode;

    // Stylized continental landmass field + procedural detail
    float lobe(vec3 p, float latDeg, float lonDeg, float spread) {
      float phi = radians(90.0 - latDeg);
      float theta = radians(lonDeg + 180.0);
      vec3 c = vec3(-sin(phi) * cos(theta), cos(phi), sin(phi) * sin(theta));
      float d = max(0.0, dot(p, c));
      return pow(d, spread);
    }

    float landField(vec3 p) {
      float m = 0.0;
      // East Asia, Taiwan & Japan
      m += 1.05 * lobe(p, 32.0, 114.0, 14.0);
      m += 0.92 * lobe(p, 25.0, 121.5, 90.0);
      m += 0.88 * lobe(p, 36.0, 139.0, 48.0);
      // SE Asia & India & Eurasia
      m += 0.85 * lobe(p, 15.0, 104.0, 22.0);
      m += 0.85 * lobe(p, 22.0, 79.0, 20.0);
      m += 0.95 * lobe(p, 52.0, 84.0, 8.0);
      // Europe & UK
      m += 1.02 * lobe(p, 49.0, 14.0, 18.0);
      m += 0.82 * lobe(p, 54.0, -2.0, 52.0);
      m += 0.82 * lobe(p, 62.0, 18.0, 24.0);
      // Africa
      m += 1.05 * lobe(p, 8.0, 21.0, 11.0);
      m += 0.88 * lobe(p, -18.0, 24.0, 18.0);
      // North America
      m += 1.08 * lobe(p, 42.0, -102.0, 10.0);
      m += 0.82 * lobe(p, 60.0, -115.0, 14.0);
      // South America
      m += 0.98 * lobe(p, -14.0, -60.0, 14.0);
      m += 0.82 * lobe(p, -34.0, -64.0, 24.0);
      // Australia
      m += 0.96 * lobe(p, -25.0, 134.0, 20.0);

      // Procedural shoreline modulation
      float detail = 0.14 * sin(p.x * 19.0 + p.y * 13.0) * cos(p.z * 17.0 - p.x * 11.0)
                   + 0.07 * sin(p.y * 37.0 - p.z * 29.0);
      return m + detail;
    }

    void main() {
      vec3 N = normalize(v_normal);
      vec3 V = normalize(-v_viewPos);
      vec3 L = normalize(vec3(0.55, 0.48, 0.68));
      vec3 H = normalize(L + V);

      float ndl = max(dot(N, L), 0.0);
      float fresnel = pow(1.0 - max(dot(N, V), 0.0), 2.5);

      float lf = landField(v_worldPos);
      float land = smoothstep(0.46, 0.56, lf);
      float coast = smoothstep(0.40, 0.48, lf) * (1.0 - smoothstep(0.54, 0.62, lf));

      // Geodesic lat/lon grid
      float latGrid = abs(fract(v_uv.y * 12.0) - 0.5);
      float lonGrid = abs(fract(v_uv.x * 24.0) - 0.5);
      float grid = 1.0 - smoothstep(0.0, 0.032, min(latGrid, lonGrid));

      // Animated scanner wave reactive to stage hover
      float pulseFreq = 3.0 + u_stageMode * 0.8;
      float radarWave = 0.5 + 0.5 * sin(v_worldPos.y * 10.0 - u_time * pulseFreq);
      float radarBand = smoothstep(0.92, 1.0, radarWave) * (0.25 + 0.12 * u_stageMode);

      // Theme palettes
      vec3 seaLight = mix(vec3(0.42, 0.72, 0.88), vec3(0.16, 0.52, 0.74), 1.0 - ndl * 0.65);
      vec3 landLight = mix(vec3(0.58, 0.85, 0.73), vec3(0.28, 0.72, 0.66), sin(v_worldPos.y * 4.0) * 0.5 + 0.5);
      vec3 seaDark = mix(vec3(0.05, 0.13, 0.25), vec3(0.09, 0.24, 0.42), ndl);
      vec3 landDark = mix(vec3(0.11, 0.36, 0.48), vec3(0.18, 0.55, 0.64), ndl);

      vec3 seaColor = mix(seaLight, seaDark, u_dark);
      vec3 landColor = mix(landLight, landDark, u_dark);

      vec3 col = mix(seaColor, landColor, land);

      // Coastal shelf highlight
      vec3 coastColor = mix(vec3(0.86, 0.97, 0.94), vec3(0.32, 0.85, 0.96), u_dark);
      col = mix(col, coastColor, coast * 0.55);

      // Geodesic grid overlay
      vec3 gridColor = mix(vec3(0.92, 0.98, 1.0), vec3(0.38, 0.78, 0.98), u_dark);
      col = mix(col, gridColor, grid * 0.18);

      // Ocean specular highlight
      float spec = pow(max(dot(N, H), 0.0), 28.0) * (1.0 - land * 0.7);
      col += spec * mix(vec3(0.45, 0.58, 0.65), vec3(0.25, 0.55, 0.78), u_dark);

      // Stage energy band
      col += radarBand * vec3(0.18, 0.76, 0.95);

      // Fresnel atmospheric rim glow
      vec3 rimColor = mix(vec3(0.15, 0.68, 0.92), vec3(0.32, 0.84, 1.0), u_dark);
      if (u_stageMode > 2.5) {
        rimColor = mix(rimColor, vec3(0.96, 0.48, 0.38), 0.45);
      }
      col = mix(col, rimColor, fresnel * 0.68);

      gl_FragColor = vec4(col, 0.98);
    }
  `;

  const ARC_VERT = `
    attribute vec3 a_pos;
    attribute float a_t;
    attribute float a_hubIndex;
    attribute vec3 a_color;
    uniform mat4 u_proj;
    uniform mat4 u_view;
    varying float v_t;
    varying float v_hubIndex;
    varying vec3 v_color;
    void main() {
      v_t = a_t;
      v_hubIndex = a_hubIndex;
      v_color = a_color;
      gl_Position = u_proj * u_view * vec4(a_pos, 1.0);
    }
  `;

  const ARC_FRAG = `
    precision highp float;
    varying float v_t;
    varying float v_hubIndex;
    varying vec3 v_color;
    uniform float u_time;
    uniform float u_activeHub;
    uniform float u_stageMode;

    void main() {
      bool isSelected = abs(v_hubIndex - u_activeHub) < 0.25;
      float speed = (isSelected ? 0.62 : 0.36) + u_stageMode * 0.08;
      float p1 = fract(v_t - u_time * speed);
      float p2 = fract(v_t - u_time * speed + 0.5);
      float comet1 = smoothstep(0.65, 0.99, p1);
      float comet2 = smoothstep(0.72, 0.99, p2);
      float pulse = max(comet1, comet2 * 0.8);

      float endFade = smoothstep(0.0, 0.06, v_t) * smoothstep(1.0, 0.94, v_t);
      float baseAlpha = isSelected ? 0.55 : 0.24;
      float alpha = (baseAlpha + pulse * (isSelected ? 0.75 : 0.48)) * endFade;

      vec3 headGlow = mix(v_color, vec3(1.0, 0.97, 0.92), pulse * 0.72);
      gl_FragColor = vec4(headGlow, min(1.0, alpha));
    }
  `;

  const PARTICLE_VERT = `
    attribute vec3 a_pos;
    attribute float a_size;
    attribute vec3 a_color;
    attribute float a_phase;
    uniform mat4 u_proj;
    uniform mat4 u_view;
    uniform float u_time;
    uniform float u_dpr;
    varying vec3 v_color;
    varying float v_alpha;
    void main() {
      vec3 p = a_pos;
      float wobble = sin(u_time * 1.6 + a_phase) * 0.025;
      p += normalize(a_pos) * wobble;
      vec4 viewPos = u_view * vec4(p, 1.0);
      gl_Position = u_proj * viewPos;
      float dist = max(1.2, -viewPos.z);
      float pulse = 0.78 + 0.32 * sin(u_time * 2.8 + a_phase);
      gl_PointSize = clamp((a_size * pulse * u_dpr * 3.1) / dist, 2.0, 26.0);
      v_color = a_color;
      // Fade points behind the globe slightly
      v_alpha = smoothstep(-3.8, -2.1, viewPos.z);
    }
  `;

  const PARTICLE_FRAG = `
    precision highp float;
    varying vec3 v_color;
    varying float v_alpha;
    void main() {
      vec2 c = gl_PointCoord - vec2(0.5);
      float r = length(c) * 2.0;
      if (r > 1.0) discard;
      float core = pow(1.0 - r, 1.8);
      gl_FragColor = vec4(v_color + core * 0.35, core * v_alpha);
    }
  `;

  function compileShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      gl.deleteShader(shader);
      return null;
    }
    return shader;
  }

  function createProgram(gl, vsSource, fsSource) {
    const vs = compileShader(gl, gl.VERTEX_SHADER, vsSource);
    const fs = compileShader(gl, gl.FRAGMENT_SHADER, fsSource);
    if (!vs || !fs) return null;
    const prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      gl.deleteProgram(prog);
      return null;
    }
    return prog;
  }

  function buildSphereGeometry(latBands = 44, lonBands = 60, radius = 1.0) {
    const positions = [];
    const uvs = [];
    const indices = [];
    for (let lat = 0; lat <= latBands; lat++) {
      const v = lat / latBands;
      const theta = v * Math.PI;
      const sinTheta = Math.sin(theta);
      const cosTheta = Math.cos(theta);
      for (let lon = 0; lon <= lonBands; lon++) {
        const u = lon / lonBands;
        const phi = u * 2 * Math.PI;
        const x = -radius * sinTheta * Math.cos(phi);
        const y = radius * cosTheta;
        const z = radius * sinTheta * Math.sin(phi);
        positions.push(x, y, z);
        uvs.push(u, v);
      }
    }
    for (let lat = 0; lat < latBands; lat++) {
      for (let lon = 0; lon < lonBands; lon++) {
        const first = lat * (lonBands + 1) + lon;
        const second = first + lonBands + 1;
        indices.push(first, second, first + 1);
        indices.push(second, second + 1, first + 1);
      }
    }
    return {
      positions: new Float32Array(positions),
      uvs: new Float32Array(uvs),
      indices: new Uint16Array(indices),
    };
  }

  function buildFlightRibbonGeometry() {
    const start = latLonToVec3(TAIWAN.lat, TAIWAN.lon, 1.005);
    const positions = [];
    const ts = [];
    const hubIndices = [];
    const colors = [];
    const indices = [];
    let vertexCount = 0;
    const steps = 44;

    GLOBAL_HUBS.forEach((hub, hubIdx) => {
      const end = latLonToVec3(hub.lat, hub.lon, 1.005);
      const chordDist = Math.hypot(end[0] - start[0], end[1] - start[1], end[2] - start[2]);
      const archHeight = 0.17 + chordDist * 0.21;
      const width = 0.023;

      const pts = [];
      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const dir = slerp3(start, end, t);
        const altitude = 1.006 + archHeight * 4 * t * (1 - t);
        pts.push([dir[0] * altitude, dir[1] * altitude, dir[2] * altitude]);
      }

      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const p = pts[i];
        const next = pts[Math.min(steps, i + 1)];
        const prev = pts[Math.max(0, i - 1)];
        const tangent = normalize3([next[0] - prev[0], next[1] - prev[1], next[2] - prev[2]]);
        const side = normalize3(cross3(tangent, p));

        for (const sign of [-1, 1]) {
          positions.push(
            p[0] + side[0] * width * sign,
            p[1] + side[1] * width * sign,
            p[2] + side[2] * width * sign
          );
          ts.push(t);
          hubIndices.push(hubIdx);
          colors.push(hub.color[0], hub.color[1], hub.color[2]);
        }

        if (i < steps) {
          const base = vertexCount + i * 2;
          indices.push(base, base + 1, base + 2);
          indices.push(base + 1, base + 3, base + 2);
        }
      }
      vertexCount += (steps + 1) * 2;
    });

    return {
      positions: new Float32Array(positions),
      ts: new Float32Array(ts),
      hubIndices: new Float32Array(hubIndices),
      colors: new Float32Array(colors),
      indices: new Uint16Array(indices),
    };
  }

  function buildOrbitalAndBeaconParticles() {
    const positions = [];
    const sizes = [];
    const colors = [];
    const phases = [];

    // Taiwan origin beacon (coral-gold)
    const tw = latLonToVec3(TAIWAN.lat, TAIWAN.lon, 1.022);
    positions.push(tw[0], tw[1], tw[2]);
    sizes.push(9.5);
    colors.push(1.0, 0.38, 0.32);
    phases.push(0.0);

    // Destination hub beacons
    GLOBAL_HUBS.forEach((hub, i) => {
      const p = latLonToVec3(hub.lat, hub.lon, 1.022);
      positions.push(p[0], p[1], p[2]);
      sizes.push(8.2);
      colors.push(hub.color[0], hub.color[1], hub.color[2]);
      phases.push(i * 1.1);
    });

    // 180 deterministic 3D orbital stars & atmospheric nodes
    for (let i = 0; i < 180; i++) {
      const seed1 = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
      const seed2 = Math.sin(i * 93.9898 + 19.133) * 24634.6345;
      const u = seed1 - Math.floor(seed1);
      const v = seed2 - Math.floor(seed2);
      const lat = (u - 0.5) * 165;
      const lon = v * 360 - 180;
      const ringRadius = i < 60 ? 1.16 + (i % 7) * 0.035 : 1.28 + (i % 11) * 0.045;
      const p = latLonToVec3(lat, lon, ringRadius);
      positions.push(p[0], p[1], p[2]);
      sizes.push(2.2 + (i % 5) * 0.9);
      const palette = GLOBAL_HUBS[i % GLOBAL_HUBS.length].color;
      colors.push(palette[0], palette[1], palette[2]);
      phases.push(i * 0.43);
    }

    return {
      positions: new Float32Array(positions),
      sizes: new Float32Array(sizes),
      colors: new Float32Array(colors),
      phases: new Float32Array(phases),
      count: positions.length / 3,
    };
  }

  function targetAnglesForHub(hub) {
    // Center camera between Taiwan and the selected hub so both the origin and destination arc are visible
    let midLat = (TAIWAN.lat * 0.35 + hub.lat * 0.65);
    let dLon = hub.lon - TAIWAN.lon;
    if (dLon > 180) dLon -= 360;
    if (dLon < -180) dLon += 360;
    const midLon = TAIWAN.lon + dLon * 0.62;
    const yaw = -(midLon + 90) * DEG2RAD;
    const pitch = Math.max(-0.52, Math.min(0.58, midLat * DEG2RAD * 0.68));
    return { yaw, pitch };
  }

  // ---- Main 3D Scene Controller ------------------------------------------------------------------------------------
  function initHeroScene() {
    const canvas = document.getElementById("uw-hero-webgl-canvas");
    if (!canvas) return null;

    const initialAngles = targetAnglesForHub(GLOBAL_HUBS[0]);
    const state = {
      activeHubIndex: 0,
      autoTour: true,
      stageMode: 0,
      yaw: initialAngles.yaw,
      pitch: initialAngles.pitch,
      targetYaw: initialAngles.yaw,
      targetPitch: initialAngles.pitch,
      velYaw: 0,
      velPitch: 0,
      dragging: false,
      lastPointerX: 0,
      lastPointerY: 0,
      pointerParallaxX: 0,
      pointerParallaxY: 0,
      lastTourSwitch: performance.now(),
      rafId: 0,
    };

    const gl = canvas.getContext("webgl", { alpha: true, antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" })
      || canvas.getContext("experimental-webgl", { alpha: true, antialias: true, preserveDrawingBuffer: true });

    let globeProg = null;
    let arcProg = null;
    let particleProg = null;
    let buffers = null;

    if (gl) {
      globeProg = createProgram(gl, GLOBE_VERT, GLOBE_FRAG);
      arcProg = createProgram(gl, ARC_VERT, ARC_FRAG);
      particleProg = createProgram(gl, PARTICLE_VERT, PARTICLE_FRAG);

      if (globeProg && arcProg && particleProg) {
        const sphere = buildSphereGeometry(44, 60, 1.0);
        const arcs = buildFlightRibbonGeometry();
        const particles = buildOrbitalAndBeaconParticles();

        const makeBuf = (target, data) => {
          const b = gl.createBuffer();
          gl.bindBuffer(target, b);
          gl.bufferData(target, data, gl.STATIC_DRAW);
          return b;
        };

        buffers = {
          spherePos: makeBuf(gl.ARRAY_BUFFER, sphere.positions),
          sphereUv: makeBuf(gl.ARRAY_BUFFER, sphere.uvs),
          sphereIdx: makeBuf(gl.ELEMENT_ARRAY_BUFFER, sphere.indices),
          sphereCount: sphere.indices.length,

          arcPos: makeBuf(gl.ARRAY_BUFFER, arcs.positions),
          arcT: makeBuf(gl.ARRAY_BUFFER, arcs.ts),
          arcHub: makeBuf(gl.ARRAY_BUFFER, arcs.hubIndices),
          arcCol: makeBuf(gl.ARRAY_BUFFER, arcs.colors),
          arcIdx: makeBuf(gl.ELEMENT_ARRAY_BUFFER, arcs.indices),
          arcCount: arcs.indices.length,

          partPos: makeBuf(gl.ARRAY_BUFFER, particles.positions),
          partSize: makeBuf(gl.ARRAY_BUFFER, particles.sizes),
          partCol: makeBuf(gl.ARRAY_BUFFER, particles.colors),
          partPhase: makeBuf(gl.ARRAY_BUFFER, particles.phases),
          partCount: particles.count,
        };
      }
    }

    // 2D Canvas fallback if headless browser disables WebGL
    const ctx2d = !buffers ? canvas.getContext("2d") : null;

    function updateHudForHub(index) {
      const hub = GLOBAL_HUBS[index] || GLOBAL_HUBS[0];
      const titleEl = document.getElementById("uw-3d-hub-card-title");
      const metaEl = document.getElementById("uw-3d-hub-card-meta");
      const linkEl = document.getElementById("uw-3d-hub-card-link");
      if (titleEl) titleEl.textContent = hub.title;
      if (metaEl) metaEl.textContent = hub.meta;
      if (linkEl) {
        linkEl.dataset.hubCountry = hub.countryFilter;
      }
      document.querySelectorAll(".uw-3d-hub-pill").forEach((pill, idx) => {
        pill.setAttribute("aria-pressed", String(idx === index));
      });
    }

    function selectHub(index, { manual = false } = {}) {
      const normalized = ((index % GLOBAL_HUBS.length) + GLOBAL_HUBS.length) % GLOBAL_HUBS.length;
      state.activeHubIndex = normalized;
      const angles = targetAnglesForHub(GLOBAL_HUBS[normalized]);
      // Keep yaw transition shortest-path
      let diff = angles.yaw - state.yaw;
      while (diff > Math.PI) diff -= Math.PI * 2;
      while (diff < -Math.PI) diff += Math.PI * 2;
      state.targetYaw = state.yaw + diff;
      state.targetPitch = angles.pitch;
      if (manual) {
        state.lastTourSwitch = performance.now() + 3500;
      }
      updateHudForHub(normalized);
    }

    // Bind destination pills
    document.querySelectorAll(".uw-3d-hub-pill").forEach((pill, idx) => {
      pill.addEventListener("click", () => selectHub(idx, { manual: true }));
    });

    // Bind HUD quick-filter link to jump to #partners with country filter pre-selected if available
    const hubLink = document.getElementById("uw-3d-hub-card-link");
    hubLink?.addEventListener("click", () => {
      const country = hubLink.dataset.hubCountry || "";
      const countrySelect = document.getElementById("country-filter");
      if (country && countrySelect) {
        const matchingOption = [...countrySelect.options].find((opt) => opt.value.includes(country));
        if (matchingOption) {
          countrySelect.value = matchingOption.value;
          countrySelect.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }
    });

    // Bind Auto-Tour toggle
    const tourToggle = document.getElementById("uw-3d-tour-toggle");
    tourToggle?.addEventListener("click", () => {
      state.autoTour = !state.autoTour;
      tourToggle.setAttribute("aria-pressed", String(state.autoTour));
      tourToggle.textContent = state.autoTour ? "自動巡航：開" : "自動巡航：關";
      state.lastTourSwitch = performance.now();
    });

    // Drag to rotate globe
    canvas.addEventListener("pointerdown", (e) => {
      state.dragging = true;
      state.lastPointerX = e.clientX;
      state.lastPointerY = e.clientY;
      canvas.setPointerCapture?.(e.pointerId);
    });

    canvas.addEventListener("pointermove", (e) => {
      const rect = canvas.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        state.pointerParallaxX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
        state.pointerParallaxY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      }
      if (!state.dragging) return;
      const dx = e.clientX - state.lastPointerX;
      const dy = e.clientY - state.lastPointerY;
      state.lastPointerX = e.clientX;
      state.lastPointerY = e.clientY;
      state.velYaw = dx * 0.0065;
      state.velPitch = dy * 0.0055;
      state.yaw += state.velYaw;
      state.pitch = Math.max(-0.85, Math.min(0.85, state.pitch + state.velPitch));
      state.targetYaw = state.yaw;
      state.targetPitch = state.pitch;
      state.lastTourSwitch = performance.now() + 4000;
    });

    const stopDrag = () => { state.dragging = false; };
    canvas.addEventListener("pointerup", stopDrag);
    canvas.addEventListener("pointercancel", stopDrag);

    // Stage hover links (.guide-stage 01-04) modulate the 3D shader mode
    document.querySelectorAll(".guide-stage").forEach((stageEl, idx) => {
      stageEl.addEventListener("pointerenter", () => { state.stageMode = idx + 1; });
      stageEl.addEventListener("pointerleave", () => { state.stageMode = 0; });
    });

    function resizeCanvas() {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.max(1, Math.round(rect.width * dpr));
      const h = Math.max(1, Math.round(rect.height * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      return { w, h, dpr };
    }

    function renderWebGL(now) {
      const { w, h, dpr } = resizeCanvas();
      gl.viewport(0, 0, w, h);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);

      const isDark = document.documentElement.dataset.theme === "dark" ? 1.0 : 0.0;
      const timeSec = now * 0.001;
      const proj = mat4Perspective(40 * DEG2RAD, w / h, 0.1, 20.0);
      const view = mat4ModelView(
        state.yaw + state.pointerParallaxX * 0.08,
        state.pitch + state.pointerParallaxY * 0.06,
        3.62
      );

      // 1. Draw Procedural 3D Globe
      gl.useProgram(globeProg);
      gl.disable(gl.BLEND);
      gl.depthMask(true);

      const bindAttr = (prog, name, buf, size) => {
        const loc = gl.getAttribLocation(prog, name);
        if (loc < 0) return;
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
      };

      bindAttr(globeProg, "a_pos", buffers.spherePos, 3);
      bindAttr(globeProg, "a_uv", buffers.sphereUv, 2);
      gl.uniformMatrix4fv(gl.getUniformLocation(globeProg, "u_proj"), false, proj);
      gl.uniformMatrix4fv(gl.getUniformLocation(globeProg, "u_view"), false, view);
      gl.uniform1f(gl.getUniformLocation(globeProg, "u_time"), timeSec);
      gl.uniform1f(gl.getUniformLocation(globeProg, "u_dark"), isDark);
      gl.uniform1f(gl.getUniformLocation(globeProg, "u_stageMode"), state.stageMode);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffers.sphereIdx);
      gl.drawElements(gl.TRIANGLES, buffers.sphereCount, gl.UNSIGNED_SHORT, 0);

      // 2. Draw 3D Great-Circle Flight Arcs with additive shader pulses
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);

      gl.useProgram(arcProg);
      bindAttr(arcProg, "a_pos", buffers.arcPos, 3);
      bindAttr(arcProg, "a_t", buffers.arcT, 1);
      bindAttr(arcProg, "a_hubIndex", buffers.arcHub, 1);
      bindAttr(arcProg, "a_color", buffers.arcCol, 3);
      gl.uniformMatrix4fv(gl.getUniformLocation(arcProg, "u_proj"), false, proj);
      gl.uniformMatrix4fv(gl.getUniformLocation(arcProg, "u_view"), false, view);
      gl.uniform1f(gl.getUniformLocation(arcProg, "u_time"), timeSec);
      gl.uniform1f(gl.getUniformLocation(arcProg, "u_activeHub"), state.activeHubIndex);
      gl.uniform1f(gl.getUniformLocation(arcProg, "u_stageMode"), state.stageMode);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffers.arcIdx);
      gl.drawElements(gl.TRIANGLES, buffers.arcCount, gl.UNSIGNED_SHORT, 0);

      // 3. Draw 3D Orbital Particle Field & Hub Beacons
      gl.useProgram(particleProg);
      bindAttr(particleProg, "a_pos", buffers.partPos, 3);
      bindAttr(particleProg, "a_size", buffers.partSize, 1);
      bindAttr(particleProg, "a_color", buffers.partCol, 3);
      bindAttr(particleProg, "a_phase", buffers.partPhase, 1);
      gl.uniformMatrix4fv(gl.getUniformLocation(particleProg, "u_proj"), false, proj);
      gl.uniformMatrix4fv(gl.getUniformLocation(particleProg, "u_view"), false, view);
      gl.uniform1f(gl.getUniformLocation(particleProg, "u_time"), timeSec);
      gl.uniform1f(gl.getUniformLocation(particleProg, "u_dpr"), dpr);

      gl.drawArrays(gl.POINTS, 0, buffers.partCount);
      gl.depthMask(true);
    }

    function renderFallback2D(now) {
      if (!ctx2d) return;
      const { w, h } = resizeCanvas();
      ctx2d.clearRect(0, 0, w, h);
      const cx = w * 0.5;
      const cy = h * 0.5;
      const r = Math.min(w, h) * 0.34;
      const grad = ctx2d.createRadialGradient(cx - r * 0.25, cy - r * 0.25, r * 0.1, cx, cy, r);
      grad.addColorStop(0, "#4cc9f0");
      grad.addColorStop(0.65, "#167ba1");
      grad.addColorStop(1, "#0d3b66");
      ctx2d.fillStyle = grad;
      ctx2d.beginPath();
      ctx2d.arc(cx, cy, r, 0, Math.PI * 2);
      ctx2d.fill();
      ctx2d.strokeStyle = "rgba(255, 255, 255, 0.35)";
      ctx2d.lineWidth = 2;
      ctx2d.beginPath();
      ctx2d.ellipse(cx, cy, r * 1.18, r * 0.42, Math.sin(now * 0.001) * 0.2, 0, Math.PI * 2);
      ctx2d.stroke();
    }

    function tick(now) {
      state.rafId = 0;
      const guideSection = document.getElementById("guide");
      if (document.hidden || !guideSection || guideSection.hidden) {
        return;
      }

      if (!reducedMotion.matches) {
        if (!state.dragging) {
          if (state.autoTour && now - state.lastTourSwitch > 4400) {
            state.lastTourSwitch = now;
            selectHub((state.activeHubIndex + 1) % GLOBAL_HUBS.length);
          }
          // Smooth spring interpolation toward target angles + gentle orbital drift
          state.targetYaw += 0.0012;
          state.yaw += (state.targetYaw - state.yaw) * 0.075;
          state.pitch += (state.targetPitch - state.pitch) * 0.075;
        }
      }

      if (buffers) renderWebGL(now);
      else renderFallback2D(now);

      if (!reducedMotion.matches) {
        state.rafId = window.requestAnimationFrame(tick);
      }
    }

    function startLoop() {
      if (!state.rafId) {
        state.rafId = window.requestAnimationFrame(tick);
      }
    }

    function renderFrame(now = performance.now()) {
      if (buffers) renderWebGL(now);
      else renderFallback2D(now);
    }

    updateHudForHub(0);
    startLoop();

    window.addEventListener("hashchange", startLoop);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) startLoop();
    });
    reducedMotion.addEventListener("change", startLoop);

    return { selectHub, startLoop, renderFrame, get state() { return state; } };
  }

  // ---- Platform-wide 3D Interactive Card Tilt & Specular Spotlight -------------------------------------------------
  function init3DCards() {
    const CARD_SELECTOR = ".guide-stage, .featured-board-card, .partner-card";
    const MAX_TILT = 6.5;

    function bindCard(card) {
      if (!(card instanceof HTMLElement) || card.dataset.uw3dReady === "true") return;
      card.dataset.uw3dReady = "true";

      card.addEventListener("pointermove", (e) => {
        if (reducedMotion.matches) return;
        const rect = card.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        const px = (e.clientX - rect.left) / rect.width;
        const py = (e.clientY - rect.top) / rect.height;
        const rx = (0.5 - py) * MAX_TILT * 2;
        const ry = (px - 0.5) * MAX_TILT * 2;
        card.style.setProperty("--uw-card-rx", `${rx.toFixed(2)}deg`);
        card.style.setProperty("--uw-card-ry", `${ry.toFixed(2)}deg`);
        card.style.setProperty("--uw-card-mx", `${(px * 100).toFixed(1)}%`);
        card.style.setProperty("--uw-card-my", `${(py * 100).toFixed(1)}%`);
      }, { passive: true });

      const reset = () => {
        card.style.setProperty("--uw-card-rx", "0deg");
        card.style.setProperty("--uw-card-ry", "0deg");
      };
      card.addEventListener("pointerleave", reset, { passive: true });
      card.addEventListener("pointercancel", reset, { passive: true });
    }

    function scanCards() {
      document.querySelectorAll(CARD_SELECTOR).forEach(bindCard);
    }

    // Track pointer over hero intro for ambient radial glow
    const heroIntro = document.querySelector("#guide .guide-intro");
    heroIntro?.addEventListener("pointermove", (e) => {
      if (reducedMotion.matches) return;
      const rect = heroIntro.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      heroIntro.style.setProperty("--uw-hero-mx", `${(((e.clientX - rect.left) / rect.width) * 100).toFixed(1)}%`);
      heroIntro.style.setProperty("--uw-hero-my", `${(((e.clientY - rect.top) / rect.height) * 100).toFixed(1)}%`);
    }, { passive: true });

    scanCards();
    const observer = new MutationObserver(() => scanCards());
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function boot3D() {
    const hero = initHeroScene();
    init3DCards();
    window.UniWay3D = Object.freeze({
      hero,
      hubs: GLOBAL_HUBS,
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot3D, { once: true });
  } else {
    boot3D();
  }
})();
