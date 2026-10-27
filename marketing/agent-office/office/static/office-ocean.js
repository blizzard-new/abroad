import * as THREE from './vendor/three.module.min.js';
import { COAST_GLSL } from './office-nature.js';

// Sun/sky reflections use the animated surface normal and a Fresnel response.
// This single pass intentionally avoids a second full scene render on mobile.
export function createCoastalWater(scene) {
  const uniforms = {
    time: { value: 0 }, daylight: { value: 1 }, sky: { value: new THREE.Color('#91cfe6') },
    lightDirection: { value: new THREE.Vector3(-.2, .9, -.3).normalize() },
  };
  const material = new THREE.ShaderMaterial({
    uniforms, toneMapped: false,
    vertexShader: `uniform float time; varying vec3 world;
      void main() {
        vec4 p = modelMatrix * vec4(position, 1.0);
        float swell = sin(dot(p.xz, vec2(0.31,0.19)) + time * 0.65) * 0.06
          + sin(dot(p.xz, vec2(-0.22,0.36)) - time * 0.48) * 0.035;
        p.y += swell; world = p.xyz;
        gl_Position = projectionMatrix * viewMatrix * p;
      }`,
    fragmentShader: `uniform float time; uniform float daylight; uniform vec3 sky; uniform vec3 lightDirection;
      varying vec3 world;
      ${COAST_GLSL}
      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
      float noise(vec2 p) {
        vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
      }
      vec3 noiseGradient(vec2 p) {
        vec2 i = floor(p), f = fract(p), u = f*f*(3.0-2.0*f), du = 6.0*f*(1.0-f);
        float a=hash(i), b=hash(i+vec2(1,0)), c=hash(i+vec2(0,1)), d=hash(i+vec2(1,1));
        return vec3(mix(mix(a,b,u.x),mix(c,d,u.x),u.y), du.x*mix(b-a,d-c,u.y), du.y*mix(c-a,d-b,u.x));
      }
      void main() {
        vec2 p = world.xz, elliptical = vec2(p.x / 26.0, (p.y - 2.0) / 23.0);
        float coast = length(elliptical) / coastRadius(atan(elliptical.x, elliptical.y));
        float shoreDistance = (coast - 1.05) * 23.0;
        float depth = max(0.0, shoreDistance * 0.52);
        float distanceToCamera = distance(cameraPosition, world);
        float detail = 1.0 - smoothstep(.08, .65, max(length(dFdx(p)), length(dFdy(p))));
        mat2 turn1 = mat2(.8,.6,-.6,.8), turn2 = mat2(.38,-.925,.925,.38);
        vec3 n1 = noiseGradient(turn1*p*.55 + vec2(time*.17,-time*.09));
        vec3 n2 = noiseGradient(turn2*p*1.35 + vec2(-time*.11,time*.18));
        vec3 n3 = noiseGradient(p*3.4 + vec2(time*.22,time*.13));
        vec2 slope = .19*(n1.yz*turn1) + detail*(.095*(n2.yz*turn2) + .048*n3.yz);
        slope += vec2(.018,.011)*cos(dot(p,vec2(.31,.19))+time*.65);
        slope *= mix(1.0, .2, smoothstep(50.0, 220.0, distanceToCamera));
        vec3 normal = normalize(vec3(-slope.x, 1.0, -slope.y));
        vec3 view = normalize(cameraPosition - world);
        float facing = clamp(dot(normal, view), 0.0, 1.0);
        float fresnel = .025 + .55 * pow(1.0 - facing, 5.0);
        vec3 reflected = reflect(-view, normal);
        vec3 horizon = mix(vec3(.025,.045,.075), vec3(.42,.69,.78), daylight);
        vec3 zenith = mix(vec3(.004,.012,.03), vec3(.055,.25,.48), daylight);
        vec3 reflection = mix(horizon, zenith, pow(max(0.0, reflected.y), .45));
        vec3 deep = mix(vec3(.0015,.009,.018), vec3(.005,.105,.17), daylight);
        vec3 lagoon = mix(vec3(.003,.032,.033), vec3(.005,.39,.34), daylight);
        vec3 bottom = mix(vec3(.014,.033,.031), vec3(.32,.52,.32), daylight);
        vec3 water = mix(lagoon, deep, 1.0 - exp(-depth * .16));
        water = mix(water, bottom, exp(-depth * 1.7) * .6);
        float caustic = pow(1.0 - abs(sin(p.x * 2.1 + sin(p.y * 1.6 + time * .4)) * sin(p.y * 2.2 + sin(p.x * 1.3 - time * .3))), 12.0);
        water += vec3(.06,.09,.055) * caustic * exp(-depth * .9) * daylight;
        vec3 halfVector = normalize(view + lightDirection);
        float glitter = pow(max(0.0, dot(normal, halfVector)), 170.0) * (daylight * 1.4 + .08);
        float grain = noise(p * 2.4 + time * .2);
        float surf = sin(shoreDistance * 2.2 + time * 1.1 + noise(p * .6) * 2.0);
        float breaking = smoothstep(.55, .95, surf) * (1.0 - smoothstep(.3, 3.8, shoreDistance));
        float edge = exp(-abs(shoreDistance - .2 - sin(time * .6) * .2) * 4.0);
        float foam = clamp((breaking * .58 + edge * .6) * smoothstep(.22,.7,grain), 0.0, .8);
        vec3 color = mix(water, reflection, fresnel) + vec3(glitter) * vec3(1.0,.94,.8);
        color = mix(color, mix(vec3(.12,.18,.22),vec3(.85,.94,.89),daylight), foam);
        float fog = smoothstep(105.0, 300.0, distanceToCamera);
        gl_FragColor = vec4(mix(color, sky, fog), 1.0);
        #include <colorspace_fragment>
      }`,
  });
  // Concentrate vertices near the island while keeping the distant horizon continuous.
  const geometry = new THREE.PlaneGeometry(2000, 2000, 128, 128);
  const position = geometry.attributes.position;
  for (let i = 0; i < position.count; i++) {
    for (const axis of ['X', 'Y']) {
      const value = position[`get${axis}`](i) / 1000;
      position[`set${axis}`](i, Math.sign(value) * value * value * 1000);
    }
  }
  const water = new THREE.Mesh(geometry, material);
  water.rotation.x = -Math.PI / 2; water.position.y = -1.08; water.frustumCulled = false;
  scene.add(water);
  return uniforms;
}
