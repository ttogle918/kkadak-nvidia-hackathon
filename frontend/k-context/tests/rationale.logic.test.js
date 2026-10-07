import { test } from 'node:test';
import assert from 'node:assert/strict';
import { activeCardIds, conflictMarks, createLatestGuard, funnelRows, mergeRationale, openItem, rejectedFor } from '../src/components/rationale/logic.js';
import { CARDS } from '../src/data/cards.js';
import { NOW_RATIONALE, storyRationale } from '../src/data/rationale.js';

test('activeCardIds: mode 별로 옛날/지금 카드를 고른다', () => {
  const s = { mode: 'both', selectedSeg: 'card_old_4', selectedNow: 'card_now_1' };
  assert.deepEqual(activeCardIds(s), ['card_old_4', 'card_now_1']);
  assert.deepEqual(activeCardIds({ ...s, mode: 'old' }), ['card_old_4']);
  assert.deepEqual(activeCardIds({ ...s, mode: 'now' }), ['card_now_1']);
  assert.deepEqual(activeCardIds({ ...s, selectedSeg: null, selectedNow: null }), []);
});

test('mergeRationale: 칩을 이어 붙이고 같은 key 는 먼저 온 것이 이긴다', () => {
  const old = storyRationale('card_old_4', '전승', 2, true);
  const now = NOW_RATIONALE.card_now_1;
  const m = mergeRationale([old, now]);
  assert.equal(m.chips.length, old.chips.length + now.chips.length);
  assert.ok(m.items.funnel && m.items.alt);
  const dup = mergeRationale([{ chips: [{ key: 'a' }], items: { a: { title: 1 } } }, { chips: [{ key: 'a' }], items: { a: { title: 2 } } }]);
  assert.equal(dup.chips.length, 1);
  assert.equal(dup.items.a.title, 1);
  assert.deepEqual(mergeRationale([]), { chips: [], items: {} });
});

test('funnelRows: 숫자 행만 막대로, 첫 행이 채택', () => {
  const rows = NOW_RATIONALE.card_now_1.items.funnel.rows;
  const f = funnelRows(rows);
  assert.equal(f[0].kind, 'adopted');
  assert.ok(f.slice(1).every((r) => r.kind === 'dropped'));
  assert.equal(f.find((r) => r.v === '5').ratio, 1);
  assert.equal(funnelRows([{ k: 'a', v: '도보 18분' }]), null);
  assert.equal(funnelRows([]), null);
});

test('conflictMarks: ✓ 가 있으면 채택/버림, 없으면(미해결) 표시하지 않는다', () => {
  const t = (x) => (typeof x === 'string' ? x : x.ko);
  const resolved = NOW_RATIONALE.card_now_1.items.conflict.rows;
  assert.deepEqual(conflictMarks(resolved, t), ['dropped', 'adopted']);
  const unresolved = NOW_RATIONALE.card_now_3.items.conflict.rows;
  assert.deepEqual(conflictMarks(unresolved, t), [null, null]);
});

test('openItem·rejectedFor', () => {
  const m = mergeRationale([NOW_RATIONALE.card_now_1]);
  assert.equal(openItem(m, 'fit').key, 'fit');
  assert.equal(openItem(m, 'nope'), null);
  assert.equal(openItem(m, null), null);
  assert.equal(rejectedFor(CARDS, ['card_now_1']).length, 1);
  assert.deepEqual(rejectedFor(CARDS, ['card_old_1']), []);
});

test('createLatestGuard', () => {
  const g = createLatestGuard();
  const a = g.next();
  g.next();
  assert.equal(g.isCurrent(a), false);
});
