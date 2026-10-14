import { appendFile, readFile } from 'node:fs/promises';
import { build } from 'esbuild';

const output = '../../src/exchange_info/static/gradient-waves.js';

await build({
  entryPoints: ['platform-background.jsx'],
  bundle: true,
  minify: true,
  jsx: 'automatic',
  define: { 'process.env.NODE_ENV': '"production"' },
  target: 'es2020',
  legalComments: 'linked',
  outfile: output,
});
await appendFile(`${output}.LEGAL.txt`,
  '\nReact / React DOM / Scheduler — MIT\n' + await readFile('node_modules/react/LICENSE', 'utf8') +
  '\nOGL 1.0.11 — Unlicense (public domain)\n' +
  '\nReact Bits — GradientWaves\n' + await readFile('LICENSE.react-bits.md', 'utf8'));
