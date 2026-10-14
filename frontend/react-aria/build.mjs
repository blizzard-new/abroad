import { appendFile, readFile } from 'node:fs/promises';
import { build } from 'esbuild';

const output = '../../src/exchange_info/static/react-aria-school-picker.js';
const result = await build({
  entryPoints: ['school-picker.jsx'],
  bundle: true,
  minify: true,
  jsx: 'automatic',
  define: { 'process.env.NODE_ENV': '"production"' },
  target: 'es2020',
  legalComments: 'linked',
  metafile: true,
  outfile: output,
});
const inputs = new Set(Object.values(result.metafile.outputs)
  .flatMap(asset => Object.keys(asset.inputs || {})).filter(path => !path.startsWith('<')));
const notices = new Set();
for (const source of await Promise.all([...inputs].map(path => readFile(path, 'utf8')))) {
  for (const match of source.matchAll(/^\s*\*?\s*(Copyright[^\n]*)$/gm)) notices.add(match[1].trim());
}
await appendFile(`${output}.LEGAL.txt`,
  '\nBundled copyright notices:\n' + [...notices].sort().join('\n') + '\n' +
  '\nReact / React DOM / Scheduler — MIT\n' + await readFile('node_modules/react/LICENSE', 'utf8') +
  '\nAdobe React Aria / React Stately / @internationalized / @react-types — Apache-2.0\n' +
  await readFile('node_modules/react-aria-components/LICENSE', 'utf8'));
