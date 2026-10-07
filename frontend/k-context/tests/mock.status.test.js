// MOCK 표시: 딱지 컴포넌트 · 판정 선택자 · 화면별 딱지 · chatBundle 이 있을 때 mock 판단 근거 숨김 · topbar 상태.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, byClass } from './_fakedom_ctsl.js';

installFakeDom();
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi, DATA_KINDS } = await import('../src/api/index.js');
const { createT, DICTS } = await import('../src/lib/i18n.js');
const { validateChatBundle } = await import('../src/api/bundle.js');
const { CHAT_BUNDLE_SAMPLE } = await import('../src/data/chat-bundle.js');
const { mockBadge } = await import('../src/lib/mock-badge.js');
const { dataKindOf, bundleKind, mockRegions, screenStatus } = await import('../src/state/selectors.js');
const timeline = await import('../src/components/timeline/index.js');
const cards = await import('../src/components/cards/index.js');
const rationale = await import('../src/components/rationale/index.js');
const topbar = await import('../src/components/layout/topbar.js');
const map = await import('../src/components/map/index.js');

const tick = (ms = 10) => new Promise((r) => setTimeout(r, ms));
const bundle = (sample) => { const raw = structuredClone(CHAT_BUNDLE_SAMPLE); raw.sample = sample; return validateChatBundle(raw).bundle; };
const chatApi = () => createApi({ mode: 'chat', baseUrl: 'http://localhost:1/api', latencyMs: 0 });
const t = createT(() => 'ko');
const badges = (root) => root.find((e) => e.dataset?.mock != null);

test('딱지: MOCK 글자 + 설명 문구(note) + 종류별 title, 텍스트 노드로만', () => {
  const a = mockBadge(t);
  assert.equal(a.text, 'MOCK');
  assert.equal(a.attrs.title, '예시 데이터 — 실제 아님');
  assert.equal(a.dataset.mock, 'mock');
  assert.equal(a.attrs['aria-label'], undefined, 'aria-label 중복 없음');
  const b = mockBadge(t, { kind: 'fixture', note: true });
  assert.equal(b.dataset.mock, 'fixture');
  assert.match(b.text, /^MOCK/);
  assert.match(b.text, /fixture/);
  assert.equal(mockBadge(t, { kind: 'zzz' }).dataset.mock, 'mock', '모르는 종류는 mock');
});

test('i18n: mock.* 키가 ko·en 에 모두 있다', () => {
  const ks = Object.keys(DICTS.ko).filter((k) => k.startsWith('mock.'));
  assert.ok(ks.length >= 7);
  for (const k of ks) assert.ok(DICTS.en[k], k);
});

test('api.dataKinds: mock=전부 mock, chat=cards·sources·rationale 은 fixture·messages 는 server, 응답은 감싸지 않는다', async () => {
  const m = createApi({ mode: 'mock', latencyMs: 0 });
  assert.deepEqual(m.dataKinds, DATA_KINDS.mock);
  assert.ok(Object.values(m.dataKinds).every((k) => k === 'mock'));
  const c = chatApi();
  assert.equal(c.dataKinds.cards, 'fixture');
  assert.equal(c.dataKinds.rationale, 'fixture');
  assert.equal(c.dataKinds.messages, 'server');
  assert.equal(c.dataKinds.itinerary, 'mock');
  assert.ok(Array.isArray(await m.getCards()), '응답은 그대로 배열');
  assert.equal(dataKindOf({}, 'cards'), 'mock', 'dataKinds 가 없으면 실제로 단정하지 않는다');
});

test('판정: backend 없음(mock)=전체 MOCK, 서버+번들 없음=mock·fixture, 서버+실제 번들=실제', () => {
  const s0 = createInitialState();
  const mock = createApi({ mode: 'mock', latencyMs: 0 });
  assert.equal(screenStatus(s0, mock), 'all-mock');
  assert.deepEqual(mockRegions(s0, mock), { timeline: 'mock', routes: 'mock', map: 'mock', cards: 'mock', rationale: 'mock', hideRationale: false, myLocation: 'mock' });

  const chat = chatApi();
  assert.equal(screenStatus(s0, chat), 'mock');
  const r = mockRegions(s0, chat);
  assert.equal(r.timeline, 'mock');
  assert.equal(r.cards, 'fixture');
  assert.equal(r.rationale, 'fixture');

  const real = createInitialState({ chatBundle: bundle(false) });
  assert.equal(bundleKind(real, chat), 'server');
  assert.equal(screenStatus(real, chat), 'bundle');
  const rr = mockRegions(real, chat);
  assert.deepEqual([rr.timeline, rr.routes, rr.map, rr.cards, rr.rationale], [null, null, null, null, null]);
  assert.equal(rr.hideRationale, true);
  assert.equal(rr.myLocation, 'mock', '내 위치는 항상 예시');

  // 같은 번들이어도 sample 이거나 backend 가 없으면 MOCK
  const sample = createInitialState({ chatBundle: bundle(true) });
  assert.equal(bundleKind(sample, chat), 'mock');
  assert.equal(mockRegions(sample, chat).timeline, 'mock');
  assert.equal(bundleKind(createInitialState({ chatBundle: bundle(false) }), mock), 'mock');
  assert.equal(screenStatus(sample, mock), 'all-mock');
});

async function mountAll(over, api) {
  const store = createStore(createInitialState(over));
  const actions = createActions({ store, api });
  await actions.loadAll().catch(() => {});
  const ctx = { store, api, t: createT(() => store.getState().lang), actions };
  const mk = (mod) => { const root = new El('section', 'html'); mod.mount(root, ctx); return root; };
  return { store, ctx, mk };
}

test('기본 화면(mock): 타임라인·카드·판단 근거·지도 경로 줄·상단에 MOCK 딱지', async () => {
  const { mk } = await mountAll({}, createApi({ mode: 'mock', latencyMs: 0 }));
  const tl = mk(timeline); const cd = mk(cards); const ra = mk(rationale); const mp = mk(map); const tb = mk(topbar);
  await tick();
  assert.equal(badges(tl).length, 1);
  assert.match(tl.text, /MOCK.*예시 데이터 — 실제 아님/);
  assert.equal(badges(cd).length, 1);
  assert.equal(badges(ra).length, 1);
  assert.equal(badges(mp).length, 1);
  assert.equal(byClass(mp, 'mock-row').length, 1);
  assert.equal(tb.find((e) => e.dataset?.status).length, 1);
  assert.equal(tb.find((e) => e.dataset?.status)[0].dataset.status, 'all-mock');
  assert.match(tb.text, /백엔드 미연결 — 전체 MOCK/);
  assert.equal(badges(tb).length, 1);
});

test('서버 연결(chat), 번들 없음: 상단은 "서버는 챗봇 답만 실제"(MOCK 딱지 포함)', async () => {
  const { mk } = await mountAll({}, chatApi());
  const tb = mk(topbar);
  assert.match(tb.text, /MOCK 데이터 — 서버는 챗봇 답만 실제/);
  assert.equal(tb.find((e) => e.dataset?.status)[0].dataset.status, 'mock');
  assert.equal(badges(tb).length, 1);
});

test('서버 연결(chat) + fixture 카드: 카드 영역 딱지는 fixture 종류', async () => {
  const mockApi = createApi({ mode: 'mock', latencyMs: 0 });
  const chat = chatApi();
  const cardsData = await mockApi.getCards(); // 서버 fixture 는 mock 과 같은 내용 — 로드만 mock 으로 대신한다
  const { store, mk } = await mountAll({}, chat);
  store.setState({ data: { ...store.getState().data, cards: cardsData }, loaded: true });
  const cd = mk(cards);
  const b = badges(cd);
  assert.equal(b.length, 1);
  assert.equal(b[0].dataset.mock, 'fixture');
});

test('실제 서버 번들: 타임라인·카드·지도·상단에 MOCK 딱지 없음, mock 판단 근거는 숨김 + 안내 한 줄', async () => {
  const api = chatApi();
  const { store, mk } = await mountAll({ chatBundle: bundle(false) }, api);
  store.setState({ data: { ...store.getState().data, cards: await createApi({ mode: 'mock', latencyMs: 0 }).getCards(), loaded: true } });
  const tl = mk(timeline); const cd = mk(cards); const mp = mk(map); const tb = mk(topbar);
  const ra = mk(rationale);
  await tick();
  assert.equal(badges(tl).length, 0);
  assert.equal(badges(cd).length, 0);
  assert.equal(badges(mp).length, 0);
  assert.equal(badges(tb).length, 0);
  assert.match(tb.text, /챗봇이 정리한 일정 \(실제 서버\)/);
  assert.equal(ra.find((e) => e.dataset?.act === 'chip').length, 0, '칩 없음');
  assert.equal(ra.find((e) => e.dataset?.status === 'hidden').length, 1);
  assert.match(ra.text, /판단 근거는 아직 준비 중이에요 \(MOCK 예시는 숨김\)/);
  assert.equal(badges(ra).length, 0);
});

test('sample 번들(mock api): 타임라인·카드·지도에 MOCK 딱지, 판단 근거 숨김, 번들을 지우면 mock 근거가 돌아온다', async () => {
  const { store, mk } = await mountAll({ chatBundle: bundle(true) }, createApi({ mode: 'mock', latencyMs: 0 }));
  const tl = mk(timeline); const cd = mk(cards); const mp = mk(map); const ra = mk(rationale);
  await tick();
  assert.equal(badges(tl).length, 1);
  assert.equal(badges(cd).length, 1);
  assert.equal(badges(mp).length, 1);
  assert.equal(ra.find((e) => e.dataset?.act === 'chip').length, 0);
  assert.match(ra.text, /MOCK 예시는 숨김/);
  store.setState({ chatBundle: null });
  await tick();
  assert.ok(ra.find((e) => e.dataset?.act === 'chip').length > 0, '번들이 없으면 근거 칩');
  assert.equal(badges(ra).length, 1);
});
