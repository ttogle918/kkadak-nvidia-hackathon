import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ITINERARY } from '../src/data/itinerary.js';
import { timelineView, dayTabs, dayDate, dayAnchorNames, STATUS_META } from '../src/components/timeline/logic.js';

const st = (o = {}) => ({ day: 1, added: false, skipped: false, selectedNow: 'card_now_1', data: { itinerary: ITINERARY }, ...o });
const statuses = (v) => v.rows.map((r) => r.status);

test('제안 상태: 빈 시간 1개(원래 일정 뒤) + 점선 제안, 추가 후 보조 빈 시간', () => {
  assert.deepEqual(statuses(timelineView(st())), ['original', 'original', 'original', 'free', 'proposed', 'original']);
});

test('추가함: 제안이 added, 큰 빈 시간이 사라지고 숙소 도보 빈 시간이 생긴다', () => {
  const v = timelineView(st({ added: true }));
  assert.deepEqual(statuses(v), ['original', 'original', 'original', 'added', 'free', 'original']);
  assert.equal(v.rows[3].meta.tagKey, 'timeline.added');
});

test('건너뜀: skipped, 원래 일정은 어느 경우에도 바뀌지 않는다', () => {
  const v = timelineView(st({ skipped: true }));
  assert.equal(v.rows.find((r) => r.id === 'tl_5').status, 'skipped');
  assert.deepEqual(v.rows.filter((r) => r.status === 'original').map((r) => r.id), ['tl_1', 'tl_2', 'tl_3', 'tl_7']);
});

test('다른 카드를 고른 상태에서는 제안이 그대로 proposed', () => {
  assert.equal(timelineView(st({ added: true, selectedNow: 'card_now_2' })).rows.find((r) => r.id === 'tl_5').status, 'proposed');
});

test('DAY 2·3 은 비어 있다(empty) / itinerary 가 없으면 빈 행', () => {
  assert.equal(timelineView(st({ day: 2 })).empty, true);
  assert.equal(timelineView(st({ data: { itinerary: null } })).empty, true);
});

test('dayTabs·dayDate·dayAnchorNames', () => {
  assert.deepEqual(dayTabs(ITINERARY), [1, 2, 3]);
  assert.equal(dayDate(ITINERARY.trip, 1), '10/15');
  assert.equal(dayDate(ITINERARY.trip, 3), '10/17');
  assert.equal(dayDate({ from: '2026-10-31' }, 2), '11/1');
  assert.equal(dayDate(null, 1), '');
  assert.equal(dayAnchorNames(ITINERARY, 2).length, 2);
});

test('상태 구분은 라벨·기호를 함께 가진다(색만 의존하지 않음)', () => {
  for (const [status, m] of Object.entries(STATUS_META)) assert.ok(m.glyph, status);
  assert.equal(STATUS_META.free.tagKey, null);
  assert.equal(new Set(Object.values(STATUS_META).map((m) => m.glyph)).size, 5);
});
