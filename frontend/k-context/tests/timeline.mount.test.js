import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire, byAct, byClass, tick } from './_fakedom_ctsl.js';

installFakeDom();
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');
const timeline = await import('../src/components/timeline/index.js');

async function setup() {
  const store = createStore(createInitialState());
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api });
  const ctx = { store, api, t: createT(() => store.getState().lang), actions };
  const root = new El('section', 'html');
  const m = timeline.mount(root, ctx); // 로드 전에도 던지지 않는다
  await actions.loadAll();
  return { store, root, m };
}
const rows = (root) => byClass(root, 'timeline-row');

test('mount: 로드 전엔 빈 상태, 로드 후 DAY 1 행 6개 + 날짜 탭 3개 + 범례', async () => {
  const { root } = await setup();
  assert.equal(rows(root).length, 6);
  assert.equal(byAct(root, 'day').length, 3);
  assert.equal(byClass(root, 'timeline-legend__item').length, 5);
  assert.equal(rows(root)[4].dataset.status, 'proposed');
  assert.match(rows(root)[4].text, /제안/); // 라벨 텍스트
  assert.match(rows(root)[4].text, /○○ 야장/);
});

test('추가/건너뜀은 store 를 따라간다', async () => {
  const { store, root } = await setup();
  store.setState({ added: true });
  assert.ok(rows(root).some((r) => r.dataset.status === 'added' && /추가함/.test(r.text)));
  store.setState({ added: false, skipped: true });
  assert.ok(rows(root).some((r) => r.dataset.status === 'skipped' && /건너뜀/.test(r.text)));
});

test('DAY 탭 클릭 -> setDay, 빈 날은 안내 문구', async () => {
  const { store, root } = await setup();
  fire(byAct(root, 'day', '2')[0], 'click');
  assert.equal(store.getState().day, 2);
  assert.equal(rows(root).length, 0);
  assert.equal(byClass(root, 'timeline__empty').length, 1);
  assert.match(byClass(root, 'timeline__day')[0].text, /DAY 2 · 10\/16/);
});

test('최소 변경 토글 -> toggleMinimize, aria-checked 반영', async () => {
  const { store, root } = await setup();
  assert.equal(byAct(root, 'toggle-min')[0].attrs['aria-checked'], 'true');
  fire(byAct(root, 'toggle-min')[0], 'click');
  assert.equal(store.getState().minimizeChanges, false);
  assert.equal(byAct(root, 'toggle-min')[0].attrs['aria-checked'], 'false');
});

test('en 전환 + destroy', async () => {
  const { store, root, m } = await setup();
  store.setState({ lang: 'en' });
  assert.match(rows(root)[0].text, /Leave hotel/);
  m.destroy();
  assert.equal(root.children.length, 0);
  store.setState({ day: 3 });
  assert.equal(root.children.length, 0);
});
