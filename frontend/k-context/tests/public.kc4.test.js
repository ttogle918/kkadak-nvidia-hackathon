// T413 프론트 마무리: 공개 모드 승인 닫힘(getMeta) 연결 + 행사 화면의 제한·상한 오류 고정 문구.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/lib/store.js';
import { createInitialState } from '../src/state/initial.js';
import { createActions } from '../src/state/actions.js';
import { createController, initialState, errKey } from '../src/events/controller.js';
import { createMockEventsApi, EventsApiError } from '../src/events/api.js';
import { KO, EN, makeT } from '../src/events/i18n.js';

const realApi = (meta, extra = {}) => ({
  mode: 'http',
  async getItinerary() { return null; }, async getRoutes() { return []; }, async getCards() { return []; },
  async getSources() { return []; }, async getMessages() { return []; }, async getAuditLog() { return []; },
  ...(meta === undefined ? {} : { getMeta: meta }),
  ...extra,
});
const boot = async (api) => {
  const store = createStore(createInitialState());
  await createActions({ store, api }).loadAll();
  return store.getState();
};

test('loadAll: getMeta().decisions === closed 이면 decisionsClosed', async () => {
  assert.equal((await boot(realApi(async () => ({ public: true, decisions: 'closed', reports: 'closed' })))).decisionsClosed, true);
  assert.equal((await boot(realApi(async () => ({ public: false, decisions: 'open', reports: 'open' })))).decisionsClosed, false);
});

test('loadAll: getMeta 실패·없음이면 열림(false)으로 두고 화면은 계속 로드된다', async () => {
  const s1 = await boot(realApi(async () => { throw new Error('x'); }));
  assert.ok(!s1.decisionsClosed);
  assert.equal(s1.loaded, true);
  assert.equal(!(await boot(realApi(undefined))).decisionsClosed, true);
});

test('mock 모드는 getMeta 를 부르지 않는다', async () => {
  let called = 0;
  const api = realApi(async () => { called++; return { decisions: 'closed' }; }, { mode: 'mock' });
  const s = await boot(api);
  assert.equal(called, 0);
  assert.ok(!s.decisionsClosed);
});

test('보안 로그 행: closed 이면 승인 버튼 대신 안내, 아니면 버튼', async () => {
  const { installFakeDom, byClass, byAct } = await import('./_fakedom_ctsl.js');
  installFakeDom();
  const { logRowNode } = await import('../src/components/securitylog/log-row.js');
  const t = (k) => (typeof k === 'string' ? k : k.ko);
  const entry = { id: 'draft:1', time: '09:00:00', kind: 'pend', text: 'x' };
  const closed = logRowNode({ entry, t, closed: true });
  assert.equal(byAct(closed, 'decide').length, 0);
  assert.equal(byClass(closed, 'securitylog-closed')[0].text, 'log.decision_closed');
  const open = logRowNode({ entry, t });
  assert.equal(byAct(open, 'decide').length, 2);
  assert.equal(byClass(open, 'securitylog-closed').length, 0);
});

test('행사 화면: 제한·상한 오류는 코드별 고정 문구 키, 서버 message 는 쓰지 않는다', () => {
  const E = (code, msg = '서버 원문') => new EventsApiError(code, 429, msg);
  assert.equal(errKey(E('rate_limited')), 'error.rate_limited');
  assert.equal(errKey(E('busy')), 'error.busy');
  assert.equal(errKey(E('daily_limit')), 'error.daily_limit');
  assert.equal(errKey(E('disabled_in_public')), 'error.disabled_in_public');
  assert.equal(errKey(E('no_session')), 'error.no_session');
  assert.equal(errKey(E('network')), 'error.network');
  assert.equal(errKey(E('internal_error')), 'error.server');
  assert.equal(errKey(new Error('x')), 'error.server');
  assert.equal(errKey(E('constructor')), 'error.server'); // 프로토타입 키 방어
  for (const k of ['error.rate_limited', 'error.busy', 'error.daily_limit', 'error.disabled_in_public', 'error.no_session']) {
    assert.ok(KO[k] && EN[k], k);
    assert.equal(makeT('ko')(k), KO[k]);
  }
});

test('행사 컨트롤러: 검색이 429 rate_limited 면 state.error 가 고정 문구 키', async () => {
  const api = { ...createMockEventsApi(), async search() { throw new EventsApiError('rate_limited', 429, 'rate_limited'); } };
  const store = createStore(initialState({ getItem: () => null, setItem() {} }, { today: '2026-10-15', demo: true }));
  const c = createController({ store, api, storage: null, now: () => new Date('2026-10-07T03:00:00Z') });
  assert.equal(await c.search(), null);
  assert.equal(store.getState().error, 'error.rate_limited');
});

test('createApi 실제 모드는 getMeta 를 붙인다(리뷰 경고 1 — 가짜 api 만으로는 못 잡음)', async () => {
  const { createApi } = await import('../src/api/index.js');
  for (const mode of ['http', 'chat']) {
    assert.equal(typeof createApi({ mode, baseUrl: '/api' }).getMeta, 'function', mode);
  }
  assert.equal(createApi({ mode: 'mock' }).getMeta, undefined);
});
