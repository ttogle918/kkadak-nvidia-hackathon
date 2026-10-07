import { test } from 'node:test';
import assert from 'node:assert/strict';
import { labelWidth, segLabelSpec, nowLabelSpec, stripGlyph } from '../src/components/map/labels.js';
import { modeOpacity, dayOpacity, segStyle, layeredSegments, makeProjector, pathD, centroid, approxRadius } from '../src/components/map/route-layer.js';
import { stepLine, badgeMixText } from '../src/components/map/route-list.js';
import { ROUTES } from '../src/data/routes.js';
import { CARDS } from '../src/data/cards.js';

test('라벨 너비: 목업 공식(글자 수 × 폭 + 여백), ko 가 en 보다 넓다', () => {
  assert.equal(labelWidth('◆ 왕이 지나던 길', 'ko', 'seg'), Math.round('◆ 왕이 지나던 길'.length * 9.6 + 16));
  assert.equal(labelWidth('abcd', 'en', 'seg'), Math.round(4 * 5.8 + 16));
  assert.equal(labelWidth('가나다', 'ko', 'zone'), Math.round(3 * 10.5 + 16));
  assert.equal(labelWidth('가나다', 'ko', 'walk'), Math.round(3 * 9.5 + 14));
  assert.ok(labelWidth('가나다', 'ko') > labelWidth('가나다', 'en'));
  assert.equal(labelWidth(null, 'ko'), 16);
});

test('이름표 사양: 선택 시 반전, weak 는 점선, align 으로 x 이동', () => {
  const a = segLabelSpec({ text: 'x', xy: [100, 50], selected: false, weak: true, lang: 'ko' });
  assert.deepEqual([a.tone, a.dashed, a.tx, a.ty], ['old', true, 108, 64]);
  assert.equal(segLabelSpec({ text: 'x', xy: [1, 2], selected: true, weak: false, lang: 'ko' }).tone, 'old-on');
  const r = nowLabelSpec({ text: 'abc', x: 470, y: 10, lang: 'en', align: 'right' });
  assert.equal(r.x + r.w, 470);
  assert.equal(nowLabelSpec({ text: 'a', x: 1, y: 1, lang: 'en', minW: 70 }).w, 70);
  assert.equal(stripGlyph('✓ 확인됨'), '확인됨');
});

test('모드 -> 투명도, 날짜 -> 투명도', () => {
  assert.deepEqual(modeOpacity('old'), { old: 1, now: 0 });
  assert.deepEqual(modeOpacity('now'), { old: 0, now: 1 });
  assert.deepEqual(modeOpacity('both'), { old: 1, now: 1 });
  const now1 = CARDS.find((c) => c.id === 'card_now_1');
  assert.equal(dayOpacity(1, now1), 1);
  assert.equal(dayOpacity(2, now1), 0.12);
  assert.equal(dayOpacity(1, null), 1);
});

test('구간 스타일: 딱지별 선 모양, 선택 강조, 이야기 없음·dim 은 클릭 불가', () => {
  assert.deepEqual(segStyle({ badge: '기록' }), { w: 6, op: 0.78, halo: 0.55, dash: 'none', clickable: true, tone: 'old' });
  assert.equal(segStyle({ badge: '전승' }).dash, '13 6');
  assert.equal(segStyle({ badge: '추정' }).dash, '1 9');
  assert.equal(segStyle({ badge: '기록', weak: true }).dash, '1 9'); // weak 는 점선
  const on = segStyle({ badge: '기록', selected: true });
  assert.deepEqual([on.w, on.op, on.halo], [9, 1, 0.9]);
  const plain = segStyle({ hasStory: false });
  assert.deepEqual([plain.clickable, plain.w, plain.op], [false, 4, 0.55]);
  const dim = segStyle({ badge: '기록', dim: true, selected: true });
  assert.deepEqual([dim.clickable, dim.op], [false, 0.25]);
});

test('경로 겹치기: 선택 경로 구간이 위, 다른 경로 전용 구간은 dim 으로 아래', () => {
  const b = layeredSegments(ROUTES, 'B');
  assert.equal(b.filter((x) => x.active).length, 3);
  assert.deepEqual(b.filter((x) => !x.active).map((x) => x.seg.card_id), ['card_old_2']); // C 와 A 는 같은 구간이라 한 번만
  assert.equal(b[0].active, false);
  const a = layeredSegments(ROUTES, 'A');
  assert.equal(a.length, 4);
  assert.ok(a.every((x) => x.active));
  assert.equal(layeredSegments(ROUTES, 'ZZ')[0].routeId, 'A'); // 모르는 id 는 첫 경로
  assert.deepEqual(layeredSegments([], 'A'), []);
});

test('좌표: schematic 은 그대로, 지리 좌표는 viewBox 안으로', () => {
  assert.deepEqual(makeProjector('schematic', [])([1, 2]), [1, 2]);
  const p = makeProjector('geo', [[37.0, 127.0], [37.1, 127.1]]);
  for (const pt of [[37.0, 127.0], [37.1, 127.1]]) {
    const [x, y] = p(pt);
    assert.ok(x >= 0 && x <= 600 && y >= 0 && y <= 700, `${x},${y}`);
  }
  assert.ok(p([37.1, 127.0])[1] < p([37.0, 127.0])[1]); // 북쪽이 위
  assert.equal(pathD([[1, 2], [3, 4]]), 'M1 2 L3 4');
  assert.deepEqual(centroid([[0, 0], [10, 20]]), [5, 10]);
  assert.equal(approxRadius(150), 45);
  assert.equal(approxRadius(1), 20);
});

test('구간 목록 문구', () => {
  const t = (x) => (typeof x === 'string' ? x : x.ko);
  const c1 = CARDS.find((c) => c.id === 'card_old_1');
  assert.equal(stepLine(c1, t), c1.facts[0].text.ko);
  assert.equal(stepLine(null, t), '');
  assert.equal(badgeMixText({ 기록: 1, 전승: 2 }, (k) => k), 'badge.기록 1 · badge.전승 2');
});
