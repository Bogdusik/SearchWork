#!/usr/bin/env node
// Validates a verify report against its spec.
//   node scripts/check-report.mjs <report.md> <spec.md>
// The report is judged by structure and rules, never by the tester's own summary.
import { readFileSync } from 'node:fs';

const [reportPath, specPath] = process.argv.slice(2);
if (!reportPath || !specPath) {
  console.error('usage: check-report.mjs <report.md> <spec.md>');
  process.exit(2);
}

const VERDICTS = ['Pass', 'Fail', 'Partial', 'Not tested'];
// Methods that may support a Pass. Anything else caps at Partial.
const LIVE_METHODS = ['live ui', 'api capture', 'live api'];

const spec = readFileSync(specPath, 'utf8');
const report = readFileSync(reportPath, 'utf8');
const problems = [];

const expected = [...spec.matchAll(/^\s*[-*]\s*\**(AC\d+)\**\s*:/gm)].map((m) => m[1]);
if (expected.length === 0) problems.push(`no acceptance criteria ("- AC1: ...") found in ${specPath}`);

function section(text, title) {
  const match = text.match(new RegExp(`^##\\s+${title}\\s*$([\\s\\S]*?)(?=^##\\s|(?![\\s\\S]))`, 'm'));
  return match ? match[1] : '';
}

function tableRows(body) {
  return body
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.startsWith('|') && !/^\|\s*-/.test(l))
    .map((l) => l.split('|').slice(1, -1).map((c) => c.trim()))
    .slice(1); // header row
}

const verdictRows = tableRows(section(report, 'Verdicts'));
const seen = new Map();
for (const [id, verdict, method] of verdictRows) {
  if (seen.has(id)) problems.push(`${id} has more than one verdict`);
  seen.set(id, { verdict, method });
  if (!VERDICTS.includes(verdict)) problems.push(`${id}: verdict "${verdict}" must be one of ${VERDICTS.join(', ')}`);
  if (!method) problems.push(`${id}: method or reason is empty`);
  if (verdict === 'Pass' && method) {
    const parts = method.toLowerCase().split('+').map((p) => p.trim());
    if (!parts.every((p) => LIVE_METHODS.includes(p))) {
      problems.push(`${id}: Pass needs live evidence only, but method is "${method}" (use Partial)`);
    }
  }
}
for (const id of expected) if (!seen.has(id)) problems.push(`${id} has no verdict`);
for (const id of seen.keys()) if (!expected.includes(id)) problems.push(`${id} is not a criterion of the spec`);

const count = (v) => [...seen.values()].filter((r) => r.verdict === v).length;
const summary = section(report, 'Summary');
const claimed = summary.match(/(\d+)\s+criteria:\s*(\d+)\s+pass,\s*(\d+)\s+fail,\s*(\d+)\s+partial,\s*(\d+)\s+not tested/i);
if (!claimed) {
  problems.push('Summary must read "<n> criteria: <p> pass, <f> fail, <x> partial, <t> not tested."');
} else {
  const actual = [seen.size, count('Pass'), count('Fail'), count('Partial'), count('Not tested')];
  if (actual.some((n, i) => n !== Number(claimed[i + 1]))) {
    problems.push(`Summary counts [${claimed.slice(1, 6).join(', ')}] do not match the table [${actual.join(', ')}]`);
  }
}

const failing = tableRows(section(report, 'Failing'));
for (const [id, verdict] of [...seen].map(([k, v]) => [k, v.verdict])) {
  if (verdict !== 'Fail') continue;
  const row = failing.find((r) => r[0] === id);
  if (!row) problems.push(`${id}: Fail needs a row in "Failing" with expected, actual, evidence`);
  else if (row.slice(1, 4).some((c) => !c)) problems.push(`${id}: expected, actual and evidence must all be filled`);
}

const unresolved = tableRows(section(report, 'Partial and not tested'));
for (const [id, { verdict }] of seen) {
  if ((verdict === 'Partial' || verdict === 'Not tested') && !unresolved.find((r) => r[0] === id && r[1])) {
    problems.push(`${id}: ${verdict} needs a reason row in "Partial and not tested"`);
  }
}

if (problems.length) {
  console.log('[FAIL] report is invalid:');
  for (const p of problems) console.log(`  - ${p}`);
  process.exit(1);
}
console.log(`[ OK ] report valid: ${seen.size} criteria`);
