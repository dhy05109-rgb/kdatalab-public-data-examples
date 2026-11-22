// Shared helpers for the JavaScript examples - Node 18+, no npm packages.
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SAMPLES = path.join(HERE, '..', 'samples');

/** Call a K-Data Lab API through the RapidAPI gateway. */
export async function rapidapi(host, pathname, params = {}) {
  const key = process.env.RAPIDAPI_KEY;
  if (!key) {
    console.error(
      `This example needs a RapidAPI key.\n\n` +
      `  1. Subscribe to the free BASIC plan on https://rapidapi.com/\n` +
      `  2. export RAPIDAPI_KEY="your-key"\n\n` +
      `Or run with --demo to render a bundled sample response.\n`
    );
    process.exit(2);
  }
  const url = new URL(`https://${host}${pathname}`);
  for (const [name, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(name, String(value));
  }
  const response = await fetch(url, {
    headers: {
      'X-RapidAPI-Key': key,
      'X-RapidAPI-Host': host,
      Accept: 'application/json',
    },
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${body.slice(0, 400)}`);
  return JSON.parse(body);
}

/** Load one of the sample responses used by --demo. */
export async function sample(name) {
  return JSON.parse(await readFile(path.join(SAMPLES, name), 'utf8'));
}

export function demoBanner(name, payload) {
  console.log(`[demo] no API key needed - rendering samples/${name}`);
  if (payload._sample?.note) console.log(`[demo] ${payload._sample.note}`);
  console.log('');
}

const pad = (text, width) => String(text ?? '').padEnd(width).slice(0, width);

export function table(headers, rows, widths = []) {
  if (rows.length === 0) {
    console.log('(no rows)');
    return;
  }
  const sizes = headers.map((header, index) => {
    const column = Math.max(header.length, ...rows.map((row) => String(row[index] ?? '').length));
    return widths[index] ?? Math.min(column, 52);
  });
  const line = (cells) => cells.map((cell, index) => pad(cell, sizes[index])).join('  ').trimEnd();
  console.log(line(headers));
  console.log(line(sizes.map((size) => '-'.repeat(size))));
  for (const row of rows) console.log(line(row));
}

export const money = (value, currency = '$') => {
  if (value === null || value === undefined) return '-';
  if (Math.abs(value) >= 1e9) return `${currency}${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `${currency}${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e4) return `${currency}${(value / 1e3).toFixed(1)}K`;
  return `${currency}${Math.round(value).toLocaleString('en-US')}`;
};

export const pct = (value, signed = false) => {
  if (value === null || value === undefined) return '-';
  const fixed = Number(value).toFixed(2);
  return `${signed && value > 0 ? '+' : ''}${fixed}%`;
};

export const num = (value) => (value === null || value === undefined ? '-' : Number(value).toLocaleString('en-US'));

export const clip = (text, width = 60) => {
  if (!text) return '-';
  const clean = String(text).replace(/\s+/g, ' ').trim();
  return clean.length <= width ? clean : `${clean.slice(0, width - 1)}…`;
};

/** Very small flag parser: --demo, --key=value, --key value. */
export function parseArgs(argv = process.argv.slice(2)) {
  const args = { demo: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith('--')) continue;
    const [flag, inline] = token.slice(2).split('=');
    if (flag === 'demo') args.demo = true;
    else if (inline !== undefined) args[flag] = inline;
    else if (argv[index + 1] && !argv[index + 1].startsWith('--')) args[flag] = argv[++index];
    else args[flag] = true;
  }
  return args;
}
