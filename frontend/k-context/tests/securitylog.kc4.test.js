import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sanitizeAuditEntry } from '../src/api/http.js';
import { sortNewestFirst, formatWhen } from '../src/components/securitylog/logic.js';
import { AUDIT_LOG } from '../src/data/auditlog.js';

const base = { id: 'audit:1', time: '09:00:00', kind: 'ok', text: 'x' };

test('sanitize: 유효한 at 보존, 잘못된 at 제거', () => {
  assert.equal(sanitizeAuditEntry({ ...base, at: '2026-10-09T00:00:00+00:00' }).at, '2026-10-09T00:00:00+00:00');
  for (const at of ['nope', 123, null, 'x'.repeat(41), '2026-10-09T00:00:00+00:00' + ' '.repeat(20)]) {
    assert.equal('at' in sanitizeAuditEntry({ ...base, at }), false);
  }
  assert.equal('at' in sanitizeAuditEntry(base), false);
});

test('sortNewestFirst: 내림차순, 동률은 id 오름차순, at 없는 항목은 원래 순서로 뒤', () => {
  const l = [
    { id: 'n1' }, { id: 'b', at: '2026-10-09T00:00:00Z' }, { id: 'n2', at: 'bad' },
    { id: 'c', at: '2026-10-10T00:00:00Z' }, { id: 'a', at: '2026-10-09T00:00:00Z' },
  ];
  const copy = [...l];
  assert.deepEqual(sortNewestFirst(l).map((e) => e.id), ['c', 'a', 'b', 'n1', 'n2']);
  assert.deepEqual(l, copy);
});

test('sortNewestFirst: mock 데이터는 순서 무변화', () => {
  assert.deepEqual(sortNewestFirst(AUDIT_LOG).map((e) => e.id), AUDIT_LOG.map((e) => e.id));
  assert.deepEqual(sortNewestFirst(null), []);
});

test('formatWhen: Asia/Seoul MM-DD HH:MM:SS', () => {
  assert.equal(formatWhen('2026-10-09T15:30:05+00:00'), '10-10 00:30:05');
  assert.equal(formatWhen('2026-10-09T00:00:00+09:00'), '10-09 00:00:00');
  assert.equal(formatWhen('bad'), null);
  assert.equal(formatWhen(undefined), null);
});

test('행: at 있으면 날짜 포함, 없으면 time', async () => {
  const { installFakeDom, byClass } = await import('./_fakedom_ctsl.js');
  installFakeDom();
  const { logRowNode } = await import('../src/components/securitylog/log-row.js');
  const t = (k) => (typeof k === 'string' ? k : k.ko);
  const timeOf = (node) => byClass(node, 'securitylog-row__time')[0].text;
  assert.equal(timeOf(logRowNode({ entry: { ...base, at: '2026-10-09T15:30:05Z' }, t })), '10-10 00:30:05');
  assert.equal(timeOf(logRowNode({ entry: base, t })), '09:00:00');
});
