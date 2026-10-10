// T438: 주변 행사 거리 표시·서울 전체 안내 — 검증기 수용, 직선 약 N km, scope 안내
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom } from './_fakedom_ctsl.js';

installFakeDom();
const { validateChatBundle } = await import('../src/api/bundle.js');
const { CHAT_BUNDLE_SAMPLE } = await import('../src/data/chat-bundle.js');
const { bundleCardNodes } = await import('../src/components/cards/bundle-view.js');
const { distanceKm } = await import('../src/lib/chat-bundle-view.js');
const { createT } = await import('../src/lib/i18n.js');
const ko = (await import('../src/i18n/ko.js')).default;
const en = (await import('../src/i18n/en.js')).default;

const ev = (id, d) => ({ id, title: `행사${id}`, schedule: { start_date: '2026-10-16', end_date: '2026-10-16' }, venue: { name: 'v' }, links: [], ...(d === undefined ? {} : { distance_m: d }) });
const mk = (events) => { const raw = structuredClone(CHAT_BUNDLE_SAMPLE); raw.events = { problems: [], ...events }; const r = validateChatBundle(raw); assert.ok(r.ok); return r.bundle; };
const t = createT(() => 'ko');
const walk = (n, acc = []) => { acc.push(n); (n.children ?? []).forEach((c) => walk(c, acc)); return acc; };
const text = (nodes) => nodes.flatMap((n) => walk(n)).map((n) => n.text ?? n.textContent ?? '').join('|');

test('검증기: distance_m·events_far_total·events_scope 수용, 이상한 값은 버림', () => {
  const b = mk({ events: [ev('a', 1234), ev('b', null), ev('c', -5), ev('d', 1.5)], events_far_total: 7, events_scope: 'nearby' });
  assert.deepEqual(b.events.events.map((e) => e.distance_m), [1234, null, null, null]);
  assert.equal(b.events.events_far_total, 7);
  assert.equal(b.events.events_scope, 'nearby');
  const c = mk({ events: [ev('a')], events_far_total: 'x', events_scope: 'mars' });
  assert.equal(c.events.events_far_total, 0);
  assert.equal(c.events.events_scope, null);
});

test('화면: 직선 약 N km, 3km 밖 제외 안내, 거리 모르면 표시 없음', () => {
  const b = mk({ events: [ev('a', 1234), ev('b', null)], events_far_total: 4, events_scope: 'nearby' });
  const s = text(bundleCardNodes(b, t));
  assert.ok(s.includes('직선 약 1.2 km'));
  assert.ok(s.includes('4건'));
  assert.ok(!s.includes('서울 전체'));
  assert.equal(bundleCardNodes(b, t).flatMap((n) => walk(n)).filter((n) => n.dataset?.distance !== undefined).length, 1);
  assert.equal(distanceKm(20), '0.1');
});

test('화면: seoul 이면 안내, 필드 없는 옛 묶음은 안내 없음, 영어 키 존재', () => {
  const s = text(bundleCardNodes(mk({ events: [ev('a')], events_scope: 'seoul' }), t));
  assert.ok(s.includes('장소 위치를 몰라 서울 전체 행사를 보여요'));
  assert.ok(!text(bundleCardNodes(mk({ events: [ev('a')] }), t)).includes('서울 전체'));
  for (const k of ['bundle.events.distance', 'bundle.events.scope_seoul', 'bundle.events.far']) assert.ok(ko[k] && en[k], k);
});
