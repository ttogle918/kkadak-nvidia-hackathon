import { test } from 'node:test';
import assert from 'node:assert/strict';
import { El, installDom, fire, byAct } from './_cr_fakedom.js';

installDom();
const { mount } = await import('../src/components/rationale/index.js');
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');

const tick = (ms = 10) => new Promise((r) => setTimeout(r, ms));

async function setup(overrides = {}, apiPatch = (a) => a) {
  const store = createStore(createInitialState(overrides));
  const api = apiPatch(createApi({ mode: 'mock', latencyMs: 0 }));
  const actions = createActions({ store, api });
  const t = createT(() => store.getState().lang);
  await actions.loadAll();
  const root = new El('section');
  const m = mount(root, { store, api, t, actions });
  await tick();
  return { store, api, actions, root, m };
}
const chipKeys = (root) => root.find((e) => e.dataset?.act === 'chip').map((e) => e.dataset.key);

test('mode now: 지금 카드의 태그 6개(팝오버는 닫힘), destroy 가 비운다', async () => {
  const { root, m } = await setup({ mode: 'now' });
  assert.deepEqual(chipKeys(root), ['funnel', 'fit', 'date', 'detour', 'src', 'conflict']);
  assert.match(root.text, /후보 12건 중 채택 2/);
  assert.equal(root.find((e) => e.attrs?.class?.includes('rationale-pop')).length, 0);
  m.destroy();
  assert.equal(root.children.length, 0);
});

test('mode both: 옛날 칩과 지금 칩이 함께 나온다', async () => {
  const { root } = await setup({ mode: 'both' });
  const keys = chipKeys(root);
  assert.ok(keys.includes('grade') && keys.includes('funnel'));
  const tones = new Set(root.find((e) => e.dataset?.act === 'chip').map((e) => e.dataset.tone));
  assert.deepEqual([...tones].sort(), ['now', 'old']);
});

test('칩 클릭 → openEvidence, 패널 표시(깔때기), 같은 칩 다시 클릭/닫기 버튼으로 닫힘', async () => {
  const { root, store } = await setup({ mode: 'now' });
  fire(root, 'click', byAct(root, 'chip', (e) => e.dataset.key === 'funnel'));
  assert.equal(store.getState().openEvidence, 'funnel');
  assert.equal(root.find((e) => e.attrs?.class === 'rationale-funnel').length, 1);
  assert.match(root.text, /기간 종료/);
  assert.equal(byAct(root, 'chip', (e) => e.dataset.key === 'funnel').attrs['aria-expanded'], 'true');
  fire(root, 'click', byAct(root, 'close'));
  assert.equal(store.getState().openEvidence, null);
  fire(root, 'click', byAct(root, 'chip', (e) => e.dataset.key === 'funnel'));
  fire(root, 'click', byAct(root, 'chip', (e) => e.dataset.key === 'funnel'));
  assert.equal(store.getState().openEvidence, null);
});

test('충돌 해결: 채택/버림 표시, 미해결 충돌(보류 카드)에는 표시가 없다', async () => {
  const a = await setup({ mode: 'now', openEvidence: 'conflict' });
  assert.deepEqual(a.root.find((e) => e.dataset?.mark).map((e) => e.dataset.mark), ['dropped', 'adopted']);
  assert.match(a.root.text, /채택/);
  const b = await setup({ mode: 'now', selectedNow: 'card_now_3', openEvidence: 'conflict' });
  assert.equal(b.root.find((e) => e.dataset?.mark).length, 0);
  assert.match(b.root.text, /해결된 척하지 않습니다/);
});

test('걸러낸 것(rejected) 목록과 이유는 깔때기 팝오버 안에 보인다', async () => {
  const { root, store } = await setup({ mode: 'now' });
  assert.doesNotMatch(root.text, /걸러낸 것/);
  store.setState({ openEvidence: 'funnel' });
  assert.match(root.text, /걸러낸 것/);
  assert.match(root.text, /포스터: 19:00 시작/);
  assert.match(root.text, /이유/);
});

test('카드 선택이 바뀌면 다시 불러온다', async () => {
  const { root, actions } = await setup({ mode: 'now' });
  actions.selectNow('card_now_3');
  await tick();
  assert.deepEqual(chipKeys(root), ['conflict']);
});

test('경쟁 상태: 느린 이전 응답이 나중에 와도 최신 카드의 근거를 덮지 않는다', async () => {
  let calls = 0;
  const slow = (api) => {
    const orig = api.getRationale.bind(api);
    return { ...api, getRationale: async (id) => { calls += 1; if (id === 'card_now_1') await tick(40); return orig(id); } };
  };
  const { root, actions } = await setup({ mode: 'now', selectedNow: 'card_now_3' }, slow);
  actions.selectNow('card_now_1'); // 느린 요청 시작
  actions.selectNow('card_now_2'); // 곧바로 다른 카드로
  await tick(80);
  assert.deepEqual(chipKeys(root), ['src', 'date']); // card_now_2 의 칩. card_now_1 응답은 버려졌다
  assert.ok(calls >= 3);
});

test('getRationale 가 실패하면 오류 문구', async () => {
  const bad = (api) => ({ ...api, getRationale: async () => { throw new Error('x'); } });
  const { root } = await setup({ mode: 'now' }, bad);
  assert.match(root.text, /불러오지 못했어요/);
});

test('destroy 후에는 늦게 온 응답이 DOM 을 다시 채우지 않는다', async () => {
  const slow = (api) => {
    const orig = api.getRationale.bind(api);
    return { ...api, getRationale: async (id) => { await tick(30); return orig(id); } };
  };
  const store = createStore(createInitialState({ mode: 'now' }));
  const api = slow(createApi({ mode: 'mock', latencyMs: 0 }));
  const actions = createActions({ store, api });
  const root = new El('section');
  const m = mount(root, { store, api, t: createT(() => 'ko'), actions });
  m.destroy();
  await tick(60);
  assert.equal(root.children.length, 0);
});

test('태그는 작은 pill: 글리프+라벨 텍스트를 가지고 aria-expanded 로 열림을 알린다', async () => {
  const { root } = await setup({ mode: 'both' });
  const tags = root.find((e) => e.dataset?.act === 'chip');
  assert.ok(tags.length >= 7);
  for (const tg of tags) {
    assert.match(tg.attrs.class, /rationale-tag/);
    assert.match(tg.text, /^[◆◇●]/);
    assert.equal(tg.attrs['aria-expanded'], 'false');
  }
});

test('Esc 와 바깥 클릭으로 팝오버가 닫히고, 닫히면 태그로 포커스가 돌아온다', async () => {
  const before = (document.listeners.keydown ?? []).length;
  const { root, store, m } = await setup({ mode: 'now' });
  fire(root, 'click', byAct(root, 'chip', (e) => e.dataset.key === 'fit'));
  assert.equal(store.getState().openEvidence, 'fit');
  await tick(); // 같은 클릭으로 연 직후의 바깥 클릭 무시 구간이 지나야 한다
  const L = document.listeners;
  L.keydown.forEach((fn) => fn({ key: 'Escape', target: root }));
  assert.equal(store.getState().openEvidence, null);
  assert.equal(document.activeElement?.dataset?.fk, 'chip:fit');
  fire(root, 'click', byAct(root, 'chip', (e) => e.dataset.key === 'date'));
  await tick();
  L.click.forEach((fn) => fn({ target: new El('div') })); // 모듈 바깥
  assert.equal(store.getState().openEvidence, null);
  m.destroy();
  assert.equal((L.keydown ?? []).length, before, 'destroy 가 리스너를 해제');
});
