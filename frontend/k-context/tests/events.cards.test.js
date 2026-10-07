import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateCard } from '../src/api/schema.js';

// Python(catalog/cards.py)이 만든 `now` 카드 fixture 가 프론트의 validateCard 와 판단 근거 모양을 통과하는지 본다.
// fixture 는 tests/domains/kcontext/catalog/gen_cards_fixture.py 로 만들고 Python 테스트가 최신인지 확인한다. 값은 전부 합성이다.
const fx = JSON.parse(readFileSync(new URL('./fixtures/now_cards.json', import.meta.url), 'utf8'));
const isText = (v) => typeof v === 'string' || (v && typeof v.ko === 'string' && typeof v.en === 'string');

test('행사 카드 fixture: 모든 카드가 validateCard 를 통과한다', () => {
  assert.ok(fx.cards.length >= 3);
  for (const c of fx.cards) assert.deepEqual(validateCard(c), [], c.id);
});

test('딱지는 확인됨·확인 필요·보류 셋뿐이고, 이동시간을 모르면 숫자로 속이지 않고 표시한다', () => {
  assert.deepEqual([...new Set(fx.cards.map((c) => c.badge))].sort(), ['보류', '확인 필요', '확인됨']);
  const known = fx.cards.find((c) => c.time_cost_unknown === false);
  assert.equal(known.time_cost_min, 7);
  for (const c of fx.cards.filter((x) => x.time_cost_unknown)) assert.ok(c.checks.some((k) => /이동시간 확인 필요/.test(k.text.ko)), c.id);
});

test('검색 수집(tier C) 행사는 같은 출처 태그에 등급을 보여 주고 미확인으로 표시한다', () => {
  const web = fx.cards.find((c) => c.title.ko.includes('검색 수집'));
  assert.equal(web.sources[0].tier, 'C');
  assert.equal(web.sources[0].unverified, true);
  assert.match(web.caveats[0].ko, /검색 수집 · 미확인/);
  assert.notEqual(web.badge, '확인됨');
  assert.ok(web.sources.every((s) => s.locator && s.collected_at && s.quote));
});

test('충돌 행사는 보류이고 확정하지 않은 값을 rejected 에 남긴다', () => {
  const c = fx.cards.find((x) => x.badge === '보류');
  assert.ok(c.rejected.length >= 1 && c.rejected.some((r) => /확정하지 않음/.test(r.reason.ko)));
});

test('판단 근거: 카드마다 chips 와 items 가 맞물리고 깔때기가 있다', () => {
  for (const c of fx.cards) {
    const r = fx.rationale[c.id];
    assert.equal(r.card_id, c.id);
    assert.ok(r.chips.length >= 4);
    for (const ch of r.chips) {
      assert.ok(isText(ch.label) && ch.tone === 'now', ch.key);
      const it = r.items[ch.key];
      assert.ok(it && isText(it.title) && isText(it.text) && Array.isArray(it.rows), `${c.id}.${ch.key}`);
    }
    assert.ok(r.chips.some((ch) => ch.key === 'funnel'));
  }
  assert.equal(fx.funnel.candidates, fx.funnel.adopted + Object.values(fx.funnel.reasons).reduce((a, b) => a + b, 0) + fx.cards.length * 0);
});

test('좌표는 [lat, lng] 이고 geo 공간이다(화면용 API 계약 §2-6)', () => {
  for (const c of fx.cards) {
    assert.equal(c.geometry.space, 'geo');
    const [lat, lng] = c.geometry.coords[0];
    assert.ok(lat > 30 && lat < 40 && lng > 120 && lng < 135, c.id);
  }
});
