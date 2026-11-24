#!/usr/bin/env node
// PreToolUse guard. Exit 2 blocks the call and shows stderr to Claude.
// Fails open on unreadable input so a bad payload never bricks the session.
import { readFileSync } from 'node:fs';

let input;
try {
  input = JSON.parse(readFileSync(0, 'utf8'));
} catch {
  process.exit(0);
}

const tool = input.tool_name;
const args = input.tool_input ?? {};

function block(reason) {
  console.error(`Blocked by guard: ${reason}`);
  process.exit(2);
}

// .env, .env.local, .env.production.local, *.pem, id_rsa*, credentials(.json). Names ending in .example are allowed.
const SECRET_FILE = /(^|\/)(\.env(\.(?!(?:[^/]*\.)?example$)[^/]*)?|[^/]*\.pem|id_rsa[^/]*|credentials(\.json)?)$/;

if (tool === 'Edit' || tool === 'Write' || tool === 'MultiEdit') {
  const path = args.file_path ?? '';
  if (SECRET_FILE.test(path)) {
    block(`${path} looks like a secrets file. Edit .env.example or ask the user.`);
  }
}

if (tool === 'Bash') {
  const cmd = args.command ?? '';
  const rules = [
    [/\bgit\s+push\b/, 'git push is done by the user'],
    [/\bgit\s+reset\s+--hard\b/, 'git reset --hard destroys work'],
    [/\bgit\s+clean\s+-[a-zA-Z]*f/, 'git clean -f deletes untracked files'],
    [/\bgit\s+rebase\b/, 'rebase rewrites history'],
    [/\bgit\s+commit\b[^\n]*--amend/, 'amend rewrites history'],
    [/\bgit\s+checkout\s+(--\s+)?\.(\s|$)/, 'this discards all working tree changes'],
    [/\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+(\/|~|\$HOME)(\s|$)/, 'recursive delete of a root or home path'],
    [/\b(cat|less|more|head|tail|type|bat)\b[^|;&\n]*\.env(?!(?:\.[\w-]+)*\.example(?:\s|$|"|'))(\.[\w-]+)*(\s|$|"|')/, 'reading .env files is not allowed'],
  ];
  for (const [pattern, reason] of rules) {
    if (pattern.test(cmd)) block(reason);
  }
}

process.exit(0);
