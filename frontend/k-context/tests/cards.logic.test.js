import { test } from 'node:test';
import assert from 'node:assert/strict';
import { MAX_TAGS, badgeShape, betweenText, checkGlyph, createLatestGuard, findSource, isSafeHttpUrl, nowButtons, splitTags, supportingFacts, visibleCards } from '../src/components/cards/logic.js';
import { CARDS } from '../src/data/cards.js';
import { SOURCES } from '../src/data/sources.js';
import { BADGE_KEY } from '../src/lib/format.js';

const src = (n) => Array.from({ length: n }, (_, i) => ({ id: `d${i}` }));

test('splitTags: 3개까지는 그대로, 초과하면 3개 + 숨긴 수, 펼치면 전부', () => {
  assert.equal(MAX_TAGS, 3);
  assert.deepEqual(splitTags(src(3), false).hidden, 0);
  const r = splitTags(src(4), false);
  assert.equal(r.shown.length, 3);
  assert.equal(r.hidden, 1);
  assert.deepEqual(r.shown.map((x) => x.n), [1, 2, 3]);
  const open = splitTags(src(5), true);
  assert.equal(open.shown.length, 5);
  assert.equal(open.hidden, 0);
  assert.equal(open.shown[4].n, 5); // 번호는 접어도 바뀌지 않는다
  assert.deepEqual(splitTags(undefined, false), { shown: [], hidden: 0 });
});

test('badgeShape: 6개 딱지가 모두 data-badge 키를 갖고, 글리프·테두리로도 구분된다', () => {
  for (const b of Object.keys(BADGE_KEY)) assert.equal(badgeShape(b).key, BADGE_KEY[b]);
  assert.deepEqual(badgeShape('기록'), { key: 'record', glyph: '◆', border: 'solid' });
  assert.equal(badgeShape('추정').border, 'dashed');
  assert.equal(badgeShape('전승').border, 'solid');
  assert.notEqual(badgeShape('전승').border, badgeShape('추정').border);
  assert.equal(badgeShape('보류').border, 'dashed');
  assert.equal(badgeShape('???').key, 'unknown');
});

test('nowButtons: 보류는 둘 다 비활성, 확인 필요는 "확인 후 추가", 추가·건너뜀 후 상태', () => {
  const hold = nowButtons('보류');
  assert.equal(hold.primary.kind, 'hold');
  assert.equal(hold.primary.disabled, true);
  assert.equal(hold.skip.disabled, true);
  assert.deepEqual([nowButtons('확인됨').primary.kind, nowButtons('확인됨').primary.disabled], ['add', false]);
  assert.equal(nowButtons('확인 필요').primary.labelKey, 'card.add_after_check');
  const added = nowButtons('확인됨', { added: true });
  assert.deepEqual([added.primary.kind, added.primary.disabled], ['added', true]);
  const skipped = nowButtons('확인됨', { skipped: true });
  assert.equal(skipped.skip.disabled, true);
  assert.equal(skipped.primary.disabled, false);
});

test('betweenText·checkGlyph·isSafeHttpUrl', () => {
  const t = (x) => (typeof x === 'string' ? x : x.ko);
  assert.equal(betweenText([{ ko: 'A' }, { ko: 'B' }], t), 'A → B');
  assert.equal(betweenText(['신촌 일정 이후'], t), '신촌 일정 이후');
  assert.equal(betweenText(null, t), '');
  assert.deepEqual(['ok', 'warn', 'bad'].map(checkGlyph), ['✓', '!', '✕']);
  assert.equal(isSafeHttpUrl('https://example.org/a'), true);
  assert.equal(isSafeHttpUrl('javascript:alert(1)'), false);
  assert.equal(isSafeHttpUrl(''), false);
});

const state = (o = {}) => ({ mode: 'both', selectedSeg: 'card_old_4', selectedNow: 'card_now_1', data: { cards: CARDS, sources: Object.values(SOURCES) }, ...o });

test('visibleCards: mode 에 따라 옛날/지금을 고른다', () => {
  const both = visibleCards(state());
  assert.deepEqual([both.old?.id, both.now?.id], ['card_old_4', 'card_now_1']);
  assert.equal(visibleCards(state({ mode: 'old' })).now, null);
  assert.equal(visibleCards(state({ mode: 'now' })).old, null);
  assert.equal(visibleCards(state({ selectedSeg: 'card_now_1' })).old, null); // 종류가 안 맞으면 무시
  assert.deepEqual(visibleCards({ mode: 'both', data: { cards: null } }), { old: null, now: null });
});

test('findSource·supportingFacts: 출처 id 로 찾고, 받치는 사실 문장을 모은다', () => {
  assert.equal(findSource(state(), 'doc_03').tier, 'B');
  assert.equal(findSource(state({ data: { cards: CARDS, sources: null } }), 'doc_03').id, 'doc_03'); // 카드에 박힌 출처로 폴백
  assert.equal(findSource(state(), 'nope'), null);
  const old = CARDS.find((c) => c.id === 'card_old_4'); // sources: doc_02, doc_01 / facts ref 1,2
  const f = supportingFacts(old, 'doc_02');
  assert.deepEqual(f.map((x) => x.n), [1]);
  assert.equal(f[0].mark, '①');
  assert.deepEqual(supportingFacts(old, 'doc_09'), []);
  assert.deepEqual(supportingFacts(null, 'doc_02'), []);
});

test('createLatestGuard: 마지막 요청만 유효', async () => {
  const g = createLatestGuard();
  const a = g.next();
  const b = g.next();
  assert.equal(g.isCurrent(a), false);
  assert.equal(g.isCurrent(b), true);
  g.invalidate();
  assert.equal(g.isCurrent(b), false);
});
