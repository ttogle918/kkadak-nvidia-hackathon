// D22 여행 기간 입력: URL 우선 · 입력 · localStorage 실패 · 잘못된 범위 미전송 · 예시 일정 trip 미사용 · mock 모드 그대로.
import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire } from './_fakedom_ctsl.js';

installFakeDom();
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT, DICTS } = await import('../src/lib/i18n.js');
const { evalTrip, tripFromSearch, initialTripInput, isDateStr } = await import('../src/lib/trip.js');
const topbar = await import('../src/components/layout/topbar.js');

const realFetch = globalThis.fetch;
const realLS = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
afterEach(() => {
  globalThis.fetch = realFetch;
  if (realLS) Object.defineProperty(globalThis, 'localStorage', realLS); else delete globalThis.localStorage;
});

const BASE = 'http://x/api';
const jsonRes = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const memLS = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), m }; };
const setLS = (v) => Object.defineProperty(globalThis, 'localStorage', { value: v, configurable: true, writable: true });
const t = createT(() => 'ko');

function captureFetch() {
  const bodies = [];
  globalThis.fetch = async (url, init = {}) => {
    const path = String(url).replace(BASE, '');
    if (init.method === 'POST' && path === '/messages') {
      bodies.push(JSON.parse(init.body));
      return jsonRes(200, { reply: { id: 'r', role: 'agent', text: 'ok', blocked: false }, logs: [] });
    }
    return jsonRes(200, []);
  };
  return bodies;
}

async function setup(api, over = {}) {
  const store = createStore(createInitialState(over));
  const actions = createActions({ store, api });
  await actions.loadAll();
  const ctx = { store, api, t: createT(() => store.getState().lang), actions };
  const root = new El('section', 'html');
  topbar.mount(root, ctx);
  return { store, actions, root };
}
const inputs = (root) => root.find((e) => e.tag === 'input' && e.dataset?.trip);
const change = (root, which, value) => { const el = inputs(root).find((e) => e.dataset.trip === which); el.value = value; fire(el, 'change'); };

test('evalTrip: 둘 다 비면 정상(오류 아님), 형식·순서·한쪽만이면 오류, 유효하면 trip', () => {
  assert.deepEqual(evalTrip({ from: '', to: '' }), { trip: null, error: false });
  assert.deepEqual(evalTrip({ from: '2026-10-15', to: '2026-10-18' }), { trip: { from: '2026-10-15', to: '2026-10-18' }, error: false });
  assert.deepEqual(evalTrip({ from: '2026-10-15', to: '2026-10-15' }).error, false);
  for (const bad of [{ from: '2026-10-18', to: '2026-10-15' }, { from: '2026-10-15', to: '' }, { from: 'x', to: '2026-10-15' }, { from: '2026-02-30', to: '2026-03-01' }]) {
    assert.deepEqual(evalTrip(bad), { trip: null, error: true });
  }
  assert.equal(isDateStr('2026-13-01'), false);
});

test('URL ?trip= 은 입력값(localStorage)보다 우선한다. 모양이 틀린 URL 값은 무시하고 저장값을 쓴다', () => {
  const ls = memLS();
  setLS(ls);
  ls.setItem('kc.trip', JSON.stringify({ from: '2026-01-01', to: '2026-01-03' }));
  assert.deepEqual(initialTripInput('?trip=2026-10-15..2026-10-18'), { from: '2026-10-15', to: '2026-10-18' });
  assert.deepEqual(initialTripInput(''), { from: '2026-01-01', to: '2026-01-03' });
  assert.deepEqual(initialTripInput('?trip=garbage'), { from: '2026-01-01', to: '2026-01-03' });
  assert.equal(tripFromSearch('?trip=2026-10-15'), null);
});

test('localStorage 읽기·쓰기가 던져도 화면과 전송은 돈다', async () => {
  Object.defineProperty(globalThis, 'localStorage', { get() { throw new Error('denied'); }, configurable: true });
  assert.deepEqual(initialTripInput(''), { from: '', to: '' });
  setLS({ getItem() { throw new Error('x'); }, setItem() { throw new Error('quota'); } });
  assert.deepEqual(initialTripInput(''), { from: '', to: '' });
  const bodies = captureFetch();
  const api = createApi({ mode: 'chat', baseUrl: BASE });
  const { store, actions, root } = await setup(api);
  change(root, 'from', '2026-10-15');
  change(root, 'to', '2026-10-18');
  assert.deepEqual(store.getState().tripInput, { from: '2026-10-15', to: '2026-10-18' });
  await actions.send('1일차 창덕궁');
  assert.deepEqual(bodies[0].context.trip, { from: '2026-10-15', to: '2026-10-18' });
});

test('입력은 저장되고, 저장값 모양이 이상하면 버린다', async () => {
  const ls = memLS();
  setLS(ls);
  const api = createApi({ mode: 'chat', baseUrl: BASE });
  captureFetch();
  const { root } = await setup(api);
  change(root, 'from', '2026-10-15');
  assert.deepEqual(JSON.parse(ls.m.get('kc.trip')), { from: '2026-10-15', to: '' });
  ls.setItem('kc.trip', JSON.stringify({ from: '<img>', to: 5 }));
  assert.deepEqual(initialTripInput(''), { from: '', to: '' });
  ls.setItem('kc.trip', '{not json');
  assert.deepEqual(initialTripInput(''), { from: '', to: '' });
});

test('잘못된 범위(시작 > 끝)·한쪽만 입력이면 trip 을 보내지 않고 입력칸 옆에 고정 문구를 보인다. 비어 있으면 문구 없음', async () => {
  setLS(memLS());
  const bodies = captureFetch();
  const api = createApi({ mode: 'chat', baseUrl: BASE });
  const { actions, root } = await setup(api);
  assert.equal(root.find((e) => e.dataset?.trip === 'invalid').length, 0, '비어 있는 것이 정상 — 경고 없음');
  assert.match(root.text, /여행 기간 \(선택\)/);
  assert.match(root.text, /일정 글의 날짜가 먼저 쓰여요\. 연도가 없거나 날짜를 안 쓸 때 기준이 돼요\./);
  change(root, 'from', '2026-10-18');
  change(root, 'to', '2026-10-15');
  const err = root.find((e) => e.dataset?.trip === 'invalid');
  assert.equal(err.length, 1);
  assert.equal(err[0].text, t('trip.invalid'));
  assert.equal(err[0].attrs.role, 'alert');
  await actions.send('1일차 창덕궁');
  assert.equal('trip' in bodies[0].context, false);
  change(root, 'to', '');
  await actions.send('2일차 경복궁');
  assert.equal('trip' in bodies[1].context, false, '한쪽만이면 보내지 않는다');
});

test('실제 모드: 예시 일정(data.itinerary.trip)의 기간은 요청에 싣지 않는다', async () => {
  setLS(memLS());
  const bodies = captureFetch();
  const api = { ...createApi({ mode: 'chat', baseUrl: BASE }), getItinerary: async () => ({ anchors: [], free_slots: [], timeline: [], landmarks: [], trip: { from: '2026-10-15', to: '2026-10-18' } }) };
  const { store, actions } = await setup(api);
  assert.deepEqual(store.getState().data.itinerary.trip, { from: '2026-10-15', to: '2026-10-18' });
  await actions.send('1일차 창덕궁');
  assert.equal('trip' in bodies[0].context, false);
});

test('mock 모드: 입력칸이 없고, 예시 일정의 기간을 보내는 기존 동작 그대로', async () => {
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const seen = [];
  const spy = { ...api, sendMessage: async (x, c) => { seen.push(c); return api.sendMessage(x, c); } };
  const { actions, root } = await setup(spy);
  assert.equal(inputs(root).length, 0);
  await actions.send('1일차 창덕궁');
  assert.deepEqual(seen[0].trip, { from: '2026-10-15', to: '2026-10-18' });
});

test('입력칸: type=date 두 칸, 라벨 i18n(ko·en)', async () => {
  setLS(memLS());
  captureFetch();
  const { root } = await setup(createApi({ mode: 'chat', baseUrl: BASE }), { tripInput: { from: '2026-10-15', to: '2026-10-18' } });
  const ins = inputs(root);
  assert.deepEqual(ins.map((e) => [e.dataset.trip, e.attrs.type, e.value]), [['from', 'date', '2026-10-15'], ['to', 'date', '2026-10-18']]);
  for (const k of ['trip.title', 'trip.from', 'trip.to', 'trip.help', 'trip.invalid', 'mock.status.error', 'rationale.pending', 'bundle.problem.partial', 'bundle.problem.year_assumed']) {
    assert.ok(DICTS.ko[k] && DICTS.en[k], k);
    assert.doesNotMatch(DICTS.en[k], /[가-힣]/, `${k} en`);
  }
  assert.doesNotMatch(DICTS.ko['rationale.pending'], /MOCK/);
});
