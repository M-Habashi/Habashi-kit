import { pathToFileURL } from 'node:url';
import * as core from './lib/core.js';
import * as icims from './lib/icims.js';
import * as paylocity from './lib/paylocity.js';
import * as aaim from './lib/aaim.js';
import * as yello from './lib/yello.js';

export const helpers = { ...core, ...icims, ...paylocity, ...aaim, ...yello };
export const dependencies = Object.fromEntries(Object.entries(helpers).map(([name, fn]) =>
  [name, Object.keys(helpers).filter(other => other !== name && new RegExp(`\\b${other}\\b`).test(fn.toString()))]));

export function emit(name, page, args = []) {
  if (!Object.hasOwn(helpers, name)) throw new Error(`Unknown helper: ${name}`);
  if (!Number.isSafeInteger(page) || page < 0) throw new Error('--page must be a nonnegative integer');
  if (!Array.isArray(args)) throw new Error('--args must be a JSON array');
  const names = new Set();
  const add = name => {
    if (names.has(name)) return;
    names.add(name);
    for (const dep of dependencies[name] ?? []) add(dep);
  };
  add(name);
  const params = name === 'un' || name === 'refOf' ? JSON.stringify(args).slice(1, -1) :
    `browser.page(${page})${args.length ? `, ...${JSON.stringify(args)}` : ''}`;
  return `return (async () => {\n${[...names].map(name => helpers[name].toString()).join('\n\n')}\nreturn await ${name}(${params});\n})();`;
}

export function main(argv) {
  if (argv.length === 1 && argv[0] === '--list') {
    console.log(Object.entries(helpers).map(([name, fn]) => `${name}(${fn.toString().match(/^[^(]*\(([^)]*)\)/)[1]})`).join('\n'));
    return;
  }
  const [name, ...flags] = argv;
  const options = {};
  for (let i = 0; i < flags.length; i += 2) {
    if (!['--page', '--args'].includes(flags[i]) || flags[i + 1] === undefined) throw new Error('Usage: emit.mjs <helper> --page <id> --args <json-array> | --list');
    options[flags[i]] = flags[i + 1];
  }
  console.log(emit(name, options['--page'] === undefined ? NaN : Number(options['--page']), JSON.parse(options['--args'] ?? '[]')));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
