import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const main = resolve(import.meta.dirname, '../src/main.ts');

function settingsFile(body: unknown): string {
  const path = join(mkdtempSync(join(tmpdir(), 'relay-')), 'relay.json');
  writeFileSync(path, JSON.stringify(body));
  return path;
}

void test('relay starts on valid settings', () => {
  const out = execFileSync(process.execPath, [main, '--config', settingsFile({ endpoint: 'https://example.test/in', retries: 3 })], { encoding: 'utf8' });
  assert.equal(out, 'relay: forwarding to https://example.test/in (3 retries)\n');
});

void test('relay refuses settings holding an unknown field', () => {
  const run = spawnSync(process.execPath, [main, '--config', settingsFile({ endpoint: 'https://example.test/in', retries: 3, verbose: true })], { encoding: 'utf8' });
  assert.notEqual(run.status, 0);
  assert.match(run.stderr, /verbose/u);
});
