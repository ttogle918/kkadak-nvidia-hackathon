import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire, byClass, tick } from './_fakedom_ctsl.js';

installFakeDom();
const { createStore } = await import('../src/lib/store.js');
const { createController, initialState } = await import('../src/events/controller.js');
const { createMockEventsApi } = await import('../src/events/api.js');
const { mountEvents } = await import('../src/events/view.js');

const mem = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) }; };
async function run(extra, lang) {
  const base = createMockEventsApi();
  const api = { ...base, async search(b) { return { ...(await base.search(b)), ...extra }; } };
  const storage = mem();
  const store = createStore(initialState(storage, { today: '2026-10-16', demo: api.demo }));
  if (lang) store.setState({ lang });
  const controller = createController({ store, api, storage, now: () => new Date('2026-10-07T03:00:00Z') });
  const root = new El('div', 'html');
  mountEvents(root, { store, api, controller });
  fire(byClass(root, 'ev-form')[0], 'submit');
  await tick(); await tick();
  return root;
}
const sample = (n) => Array.from({ length: n }, (_, i) => ({ title: `T${i}`, reason: 'R' }));

test('요약 응답: n 은 excluded_total(원본 개수), 사유별 목록과 예시 20건', async () => {
  const root = await run({ excluded: sample(20), excluded_total: 8620, excluded_by_reason: { '기간 밖': 8000, '구 밖': 620 } });
  const t = root.text;
  assert.match(t, /제외된 항목 8620건 보기/);
  assert.match(t, /기간 밖 — 8000/);
  assert.match(t, /구 밖 — 620/);
  assert.match(t, /예시 20건/);
  assert.match(t, /T19 — R/);
});

test('excluded_total 이 없으면 excluded 길이, 사유 목록 없음', async () => {
  const root = await run({ excluded: sample(3), excluded_total: undefined });
  assert.match(root.text, /제외된 항목 3건 보기/);
  assert.doesNotMatch(root.text, /사유별 개수/);
});

test('excluded_total 0 이고 목록도 비면 절 없음, 영어 문구', async () => {
  assert.equal(byClass(await run({ excluded: [], excluded_total: 0 }), 'ev-excluded').length, 0);
  const en = await run({ excluded: sample(2), excluded_total: 50, excluded_by_reason: { x: 50 } }, 'en');
  assert.match(en.text, /Show 50 excluded items/);
  assert.match(en.text, /Count by reason/);
  assert.match(en.text, /Examples \(2\)/);
});
