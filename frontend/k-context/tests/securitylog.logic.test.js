import { test } from 'node:test';
import assert from 'node:assert/strict';
import { LOG_META, metaOf, canDecide, decidedNoteKey, countByKind, DECISIONS } from '../src/components/securitylog/logic.js';
import { AUDIT_LOG } from '../src/data/auditlog.js';
import { DICTS } from '../src/lib/i18n.js';

test('5개 kind 모두 기호+라벨 키가 있고 사전에 있다', () => {
  assert.deepEqual(Object.keys(LOG_META).sort(), ['approved', 'deny', 'ok', 'pend', 'rejected']);
  for (const m of Object.values(LOG_META)) {
    assert.ok(m.icon);
    assert.ok(DICTS.ko[m.labelKey] && DICTS.en[m.labelKey]);
  }
  assert.equal(metaOf('???').labelKey, null);
});

test('승인 대기(pend)만 결정 가능', () => {
  assert.deepEqual(AUDIT_LOG.filter(canDecide).map((l) => l.id), ['log_003']);
  for (const k of ['ok', 'deny', 'approved', 'rejected', 'x']) assert.equal(canDecide({ kind: k }), false);
  assert.equal(canDecide(null), false);
  assert.deepEqual(DECISIONS, ['approve', 'reject']);
});

test('결정 안내·건수', () => {
  assert.equal(decidedNoteKey({ kind: 'approved' }), 'log.decided_approved');
  assert.equal(decidedNoteKey({ kind: 'rejected' }), 'log.decided_rejected');
  assert.equal(decidedNoteKey({ kind: 'ok' }), null);
  assert.deepEqual(countByKind(AUDIT_LOG), { ok: 2, deny: 1, pend: 1, approved: 0, rejected: 0 });
});
