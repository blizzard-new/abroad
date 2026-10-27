# Three.js 0.180.0

Source: https://www.npmjs.com/package/three/v/0.180.0 (npm release tarball).
Upstream: https://github.com/mrdoob/three.js/tree/r180
License: MIT; see THREE-LICENSE.txt.

Vendored files: build/three.module.min.js, build/three.core.min.js,
examples/jsm/controls/OrbitControls.js. The only change to OrbitControls is
its import specifier, from `three` to `./three.module.min.js`, so the office
works entirely from its own static server with no CDN or package manager at runtime.
