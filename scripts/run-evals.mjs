#!/usr/bin/env node
// Deterministic check runner. One command answers "does it pass or not".
//   node scripts/run-evals.mjs --profile fast
//   node scripts/run-evals.mjs --list
//   node scripts/run-evals.mjs --profile full --dry-run
// Stops at the first failing check, prints the tail of its output,
// and writes evals/results/latest.json.
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = join(root, 'evals', 'manifest.json');
const resultsPath = join(root, 'evals', 'results', 'latest.json');
const TAIL_LINES = 40;

const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const option = (name) => {
  const i = argv.indexOf(name);
  return i === -1 ? undefined : argv[i + 1];
};

function fail(message, code = 2) {
  console.error(`[FAIL] ${message}`);
  process.exit(code);
}

function loadManifest() {
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch (error) {
    fail(`cannot read ${manifestPath}: ${error.message}`);
  }
  const { checks = {}, profiles = {} } = manifest;
  for (const [name, check] of Object.entries(checks)) {
    if (typeof check.cmd !== 'string' || !Array.isArray(check.args ?? [])) {
      fail(`check "${name}" needs a string "cmd" and an array "args"`);
    }
  }
  for (const [profile, names] of Object.entries(profiles)) {
    for (const name of names) {
      if (!checks[name]) fail(`profile "${profile}" references unknown check "${name}"`);
    }
  }
  return { checks, profiles };
}

const { checks, profiles } = loadManifest();

if (flag('--list')) {
  for (const [profile, names] of Object.entries(profiles)) {
    console.log(`${profile}: ${names.join(', ')}`);
  }
  process.exit(0);
}

const profile = option('--profile') ?? 'fast';
if (!profiles[profile]) {
  fail(`unknown profile "${profile}". Available: ${Object.keys(profiles).join(', ')}`);
}

const dryRun = flag('--dry-run');
const results = [];
let failed = null;

for (const name of profiles[profile]) {
  const check = checks[name];
  const line = [check.cmd, ...(check.args ?? [])].join(' ');
  const cwd = join(root, check.cwd ?? '.');

  if (dryRun) {
    console.log(`[DRY ] ${name}: (${check.cwd ?? '.'}) ${line}`);
    continue;
  }

  const started = Date.now();
  const run = spawnSync(check.cmd, check.args ?? [], {
    cwd,
    env: { ...process.env, ...(check.env ?? {}) },
    encoding: 'utf8',
    shell: process.platform === 'win32',
    maxBuffer: 64 * 1024 * 1024,
  });
  const ms = Date.now() - started;
  const ok = run.status === 0 && !run.error;
  results.push({ name, status: ok ? 'pass' : 'fail', ms });
  console.log(`[${ok ? ' OK ' : 'FAIL'}] ${name} (${(ms / 1000).toFixed(1)}s)`);

  if (!ok) {
    failed = name;
    const output = `${run.stdout ?? ''}${run.stderr ?? ''}${run.error ? `\n${run.error.message}` : ''}`;
    console.log(output.trimEnd().split('\n').slice(-TAIL_LINES).join('\n'));
    break;
  }
}

if (dryRun) process.exit(0);

mkdirSync(dirname(resultsPath), { recursive: true });
writeFileSync(
  resultsPath,
  JSON.stringify({ profile, finishedAt: new Date().toISOString(), passed: failed === null, results }, null, 2),
);

if (failed) fail(`profile "${profile}" stopped at "${failed}"`, 1);
console.log(`[ OK ] profile "${profile}" passed (${results.length} checks)`);
