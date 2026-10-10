// T318 실제 모드: 예시 데이터 끄기(MOCK 딱지 0·빈 상태·연결 실패 오류 상태) · 보안 로그 서버 연결 · 근거 선택 연결 ·
// 문제 코드 i18n · 시각 표시 · 명시 모드 base · 카카오 점선. ?api=mock 과 auto+backend 꺼짐은 그대로여야 한다(회귀).
import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { installFakeDom, El, fire, byAct } from './_fakedom_ctsl.js';

installFakeDom();
let innerHtmlWrites = 0;
Object.defineProperty(El.prototype, 'innerHTML', { set() { innerHtmlWrites += 1; }, get() { return ''; } });
const baseReplace = El.prototype.replaceChildren;
El.prototype.replaceChildren = function replaceChildren(...nodes) { return baseReplace.call(this, ...nodes.map((n) => (typeof n === 'string' ? { nodeType: 3, text: n } : n))); };

const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi, resolveApi, DEFAULT_CHAT_BASE } = await import('../src/api/index.js');
const { createHttpApi } = await import('../src/api/http.js');
const { createT, DICTS } = await import('../src/lib/i18n.js');
const { validateChatBundle } = await import('../src/api/bundle.js');
const { CHAT_BUNDLE_SAMPLE } = await import('../src/data/chat-bundle.js');
const { problemLines, formatServerTime, mentionCardIds, HIDDEN_PROBLEM_CODES } = await import('../src/lib/chat-bundle.js');
const { scheduleNoteNode } = await import('../src/lib/chat-bundle-view.js');
const { realScreen, screenStatus, mockRegions } = await import('../src/state/selectors.js');
const { createKakaoView } = await import('../src/components/map/kakao-view.js');
const timeline = await import('../src/components/timeline/index.js');
const cards = await import('../src/components/cards/index.js');
const rationale = await import('../src/components/rationale/index.js');
const topbar = await import('../src/components/layout/topbar.js');
const securitylog = await import('../src/components/securitylog/index.js');
const map = await import('../src/components/map/index.js');

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

const BASE = 'http://x/api';
const EVIL = '<img src=x onerror=alert(1)>';
const jsonRes = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const tick = (ms = 5) => new Promise((r) => setTimeout(r, ms));
const ko = createT(() => 'ko');
const en = createT(() => 'en');
const flat = (n) => n.text;
const badges = (root) => root.find((e) => e.dataset?.mock != null);
const rows = (root) => root.find((e) => (e.attrs?.class ?? '') === 'securitylog-row');

/** 라우팅하는 가짜 fetch. routes: {'GET /audit': body | (init)=>res}. 호출 기록을 돌려준다. */
function fakeFetch(routes) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    const method = init.method ?? 'GET';
    calls.push({ method, url: String(url), body: init.body, headers: init.headers });
    const path = String(url).replace(BASE, '');
    const r = routes[`${method} ${path}`];
    if (r === undefined) return jsonRes(404, { error: { code: 'not_found', message: '/home/secret/x.py' } });
    if (r instanceof Error) throw r;
    return typeof r === 'function' ? r(init) : jsonRes(200, r);
  };
  return calls;
}

const L = (k, e = k) => ({ ko: k, en: e });
const rat = (key) => ({ card_id: key, chips: [{ key: 'why', tone: 'old', label: L('◆ 근거 있음', '◆ Grounded') }], items: { why: { title: L('왜'), text: L('본문', 'body'), rows: [{ k: L('k'), v: L('v') }] } } });
const AUDIT = [
  { id: 'audit:run1:3', time: '09:41:02', at: '2026-10-10T00:41:02Z', kind: 'ok', text: L('kc_search 실행', 'kc_search ran'), decided_by: null, decided_at: null, origin: 'audit' },
  { id: 'draft:abc', time: '09:42:00', at: '2026-10-10T00:42:00Z', kind: 'pend', text: L('blog.example.com · 허용 목록에 없음', 'blog.example.com · not on the allow list'), decided_by: null, decided_at: null, origin: 'hitl' },
];

/** 실제 서버가 준 v2 묶음(sample 아님). */
function realBundle(edit) {
  const raw = structuredClone(CHAT_BUNDLE_SAMPLE);
  raw.schema = 'kc-chat-bundle/v2';
  raw.sample = false;
  raw.schedule = { source: 'llm', attempts: 1, model: 'm', prompt_sha: 'x', cache_created_at: null };
  raw.routes = [{
    id: 'day1', day: 1, date: '2026-10-15', skipped: [],
    legs: [{ from: '창덕궁', to: '익선동', from_ll: [37.57964694739535, 126.99099980677127], to_ll: [37.5734371942191, 126.989775723896], straight_m: 850, walk_min: 14, provider: 'kakao', estimated: false }],
  }];
  raw.rationale = { 'mention:story_sample_a1': rat('mention:story_sample_a1'), 'mention:story_sample_b1': rat('mention:story_sample_b1') };
  raw.events_rationale = { 'event:sample:1': rat('event:sample:1') };
  for (const r of raw.mentions.anchors) for (const m of r.mentions) m.card_id = `story_${m.article_id}`; // 서버가 언급마다 싣는 카드 id
  edit?.(raw);
  const v = validateChatBundle(raw);
  assert.equal(v.ok, true, v.reason);
  return v.bundle;
}

function spyApi(api) {
  const calls = [];
  const out = { ...api };
  for (const k of Object.keys(api)) if (typeof api[k] === 'function') out[k] = (...a) => { calls.push(k); return api[k](...a); };
  out.calls = calls;
  return out;
}

async function boot(api, over = {}) {
  const store = createStore(createInitialState(over));
  const actions = createActions({ store, api });
  await actions.loadAll();
  const ctx = { store, api, t: createT(() => store.getState().lang), actions };
  const mk = (mod) => { const root = new El('section', 'html'); mod.mount(root, ctx); return root; };
  return { store, ctx, actions, mk };
}
const realApi = (mode = 'chat') => createApi({ mode, baseUrl: BASE });

// ---------------------------------------------------------------------------------------------- api
test('실제 모드 api: 예시 없음 — itinerary·routes·cards·sources 는 빈 값, card·rationale 은 not_found, 서버를 부르지 않는다', async () => {
  const calls = fakeFetch({});
  for (const mode of ['chat', 'http']) {
    const api = realApi(mode);
    assert.deepEqual(api.dataKinds, { itinerary: 'empty', routes: 'empty', cards: 'empty', sources: 'empty', rationale: 'bundle', messages: 'server', audit: 'server' });
    assert.deepEqual(await api.getItinerary(), { anchors: [], free_slots: [], timeline: [], landmarks: [] });
    assert.deepEqual([await api.getRoutes(), await api.getCards(), await api.getSources()], [[], [], []]);
    await assert.rejects(() => api.getCard('card_old_4'), (e) => e.code === 'not_found');
    await assert.rejects(() => api.getRationale('card_now_1'), (e) => e.code === 'not_found');
  }
  assert.equal(calls.length, 0);
});

test('GET /audit: 서버 항목만 받고, 모양이 틀린 항목은 버리며, 서버 전용 필드(origin·at)는 화면 값에 남기지 않는다', async () => {
  const calls = fakeFetch({ 'GET /audit': [...AUDIT, { id: 5 }, { id: 'x', time: 't', kind: 'weird', text: 'a' }, null, { id: 'y', time: 't', kind: 'ok', text: { ko: 1, en: 2 } }] });
  const logs = await createHttpApi({ baseUrl: BASE }).getAuditLog();
  assert.deepEqual(calls.map((c) => `${c.method} ${c.url}`), [`GET ${BASE}/audit`]);
  assert.deepEqual(logs.map((l) => l.id), ['audit:run1:3', 'draft:abc']);
  assert.equal('origin' in logs[0], false);
  fakeFetch({ 'GET /audit': { not: 'array' } });
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getAuditLog(), (e) => e.code === 'bad_response');
});

test('POST /audit/{id}/decision: 본문은 {"decision"} 뿐(신원·사유 없음), id 는 인코딩, 잘못된 값은 보내지 않는다', async () => {
  const calls = fakeFetch({ 'POST /audit/draft%3Aabc/decision': () => jsonRes(200, { ...AUDIT[1], kind: 'approved', decided_by: 'human:ops', decided_at: '2026-10-10T01:00:00Z' }) });
  const api = createHttpApi({ baseUrl: BASE });
  const entry = await api.decideAudit('draft:abc', 'approve');
  assert.equal(calls.length, 1);
  assert.equal(calls[0].method, 'POST');
  assert.equal(calls[0].url, `${BASE}/audit/draft%3Aabc/decision`);
  assert.equal(calls[0].body, '{"decision":"approve"}');
  assert.deepEqual(Object.keys(JSON.parse(calls[0].body)), ['decision']);
  assert.equal(entry.kind, 'approved');
  assert.equal(entry.decided_by, 'human:ops');
  await assert.rejects(() => api.decideAudit('draft:abc', 'approve; DROP'), (e) => e.code === 'validation_error');
  assert.equal(calls.length, 1, '잘못된 결정은 요청하지 않는다');
});

test('결정 오류: 서버 message 는 쓰지 않고 code 별 고정 문구', async () => {
  fakeFetch({ 'POST /audit/draft%3Aabc/decision': () => jsonRes(409, { error: { code: 'already_decided', message: '/home/secret/db.sqlite 오류' } }) });
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).decideAudit('draft:abc', 'reject'),
    (e) => e.code === 'already_decided' && e.status === 409 && !e.message.includes('secret') && /이미 결정/.test(e.message));
});

// ---------------------------------------------------------------------------------------------- 화면
test('실제 모드 첫 화면(묶음 없음): MOCK 딱지 0, 빈 상태 문구, 상단 "실제 서버 · 일정 대기", 근거 안내, 서버 보안 로그만', async () => {
  fakeFetch({ 'GET /messages': [], 'GET /audit': AUDIT });
  const api = spyApi(realApi());
  const { store, mk } = await boot(api);
  const tl = mk(timeline); const cd = mk(cards); const mp = mk(map); const tb = mk(topbar); const ra = mk(rationale); const sl = mk(securitylog);
  await tick();
  for (const [name, r] of Object.entries({ tl, cd, mp, tb, ra, sl })) assert.equal(badges(r).length, 0, `${name} MOCK 딱지`);
  assert.match(tl.text, /아직 정리된 일정이 없어요/);
  assert.match(cd.text, /일정을 정리하면 실록 기록과 주변 행사/);
  assert.match(mp.text, /좌표가 확인된 장소가 지도에 보여요/);
  assert.equal(tb.find((e) => e.dataset?.status)[0].dataset.status, 'empty');
  assert.match(tb.text, /실제 서버 · 일정 대기/);
  assert.match(ra.text, /카드를 고르면 판단 근거가 보여요/);
  assert.equal(ra.find((e) => e.dataset?.act === 'chip').length, 0);
  assert.doesNotMatch([tl, cd, mp, ra].map((r) => r.text).join(' '), /야장|덕수궁|정동|MOCK/, '예시 카드·지도 이름이 없다');
  // (c) 기본 선택 없음, getCard·getRationale 호출 없음
  assert.equal(store.getState().selectedSeg, null);
  assert.equal(store.getState().selectedNow, null);
  assert.equal(api.calls.includes('getCard') || api.calls.includes('getRationale'), false);
  // 보안 로그: 서버 기록(audit:, draft:)만, 예시 log_ 없음
  assert.deepEqual(store.getState().logs.map((l) => l.id), ['audit:run1:3', 'draft:abc']);
  assert.deepEqual(rows(sl).map((e) => e.dataset.id), ['audit:run1:3', 'draft:abc']);
  assert.equal(innerHtmlWrites, 0);
});

test('명시 chat·http 모드에서 backend 에 닿지 못하면: 오류 상태 문구(예시로 채우지 않는다), 서버 오류 문구는 숨김', async () => {
  fakeFetch({ 'GET /messages': new TypeError('fetch failed') });
  for (const mode of ['chat', 'http']) {
    const { store, mk } = await boot(realApi(mode));
    assert.equal(store.getState().loaded, false);
    assert.equal(realScreen(store.getState(), realApi(mode)), 'error');
    const tl = mk(timeline); const cd = mk(cards); const mp = mk(map); const tb = mk(topbar);
    for (const r of [tl, cd, mp]) {
      assert.match(r.text, /서버에 연결하지 못했어요/);
      assert.equal(badges(r).length, 0);
      assert.equal(r.find((e) => e.dataset?.real === 'error' && e.dataset.area != null).length, 1);
    }
    assert.equal(badges(tb).length, 0);
    assert.doesNotMatch(tl.text + cd.text + mp.text, /야장|덕수궁|fetch failed/);
  }
});

test('실제 모드 + 실제 묶음: 모든 영역 MOCK 딱지 0, 상단 "챗봇이 정리한 일정", "예시 일정 보기" 버튼 없음, 내 위치(예시) 없음', async () => {
  fakeFetch({ 'GET /messages': [], 'GET /audit': [] });
  const api = realApi();
  const { store, mk } = await boot(api, { chatBundle: realBundle() });
  const tl = mk(timeline); const cd = mk(cards); const mp = mk(map); const tb = mk(topbar); const ra = mk(rationale);
  await tick();
  for (const [name, r] of Object.entries({ tl, cd, mp, tb, ra })) assert.equal(badges(r).length, 0, `${name} MOCK 딱지`);
  assert.equal(byAct(tl, 'clear-bundle').length, 0, '실제 모드에는 돌아갈 예시 일정이 없다');
  assert.match(tb.text, /챗봇이 정리한 일정 \(실제 서버\)/);
  assert.equal(mockRegions(store.getState(), api).myLocation, null);
  // (g) 근거가 실제로 뜰 때도 MOCK 딱지가 함께 뜨지 않는다
  cd.find((e) => e.dataset?.act === 'select-item')[0] && fire(cd.find((e) => e.dataset?.act === 'select-item')[0], 'click');
  await tick();
  assert.ok(ra.find((e) => e.dataset?.act === 'chip').length > 0, '근거 칩');
  assert.equal(badges(ra).length, 0);
});

// ---------------------------------------------------------------------------------------------- 회귀
test('회귀: ?api=mock 과 auto+backend 꺼짐은 예전과 같다(전체 MOCK, 예시 선택·근거·카드·내 위치)', async () => {
  fakeFetch({ 'GET /messages': new TypeError('fetch failed') });
  const auto = await resolveApi({ mode: 'auto', latencyMs: 0 });
  assert.equal(auto.mode, 'mock');
  for (const api of [auto, createApi({ mode: 'mock', latencyMs: 0 })]) {
    const { store, mk } = await boot(api);
    const s = store.getState();
    assert.equal(realScreen(s, api), null);
    assert.equal(screenStatus(s, api), 'all-mock');
    assert.deepEqual([s.selectedSeg, s.selectedNow], ['card_old_4', 'card_now_1'], '예시 기본 선택 유지');
    assert.equal(mockRegions(s, api).myLocation, 'mock');
    assert.deepEqual(s.logs.map((l) => l.id), ['log_001', 'log_002', 'log_003', 'log_004']);
    const tl = mk(timeline); const cd = mk(cards); const ra = mk(rationale); const tb = mk(topbar); const sl = mk(securitylog);
    await tick();
    assert.equal(badges(tl).length, 1);
    assert.equal(badges(cd).length, 1);
    assert.equal(badges(ra).length, 1);
    assert.match(tb.text, /백엔드 미연결 — 전체 MOCK/);
    assert.match(cd.text, /야장|덕수궁|정동/);
    assert.ok(ra.find((e) => e.dataset?.act === 'chip').length > 0);
    assert.equal(byAct(cd, 'select-item').length, 0, 'mock 모드에는 선택 버튼이 없다');
    assert.deepEqual(rows(sl).map((e) => e.dataset.id), ['log_001', 'log_002', 'log_003', 'log_004']);
  }
});

// ---------------------------------------------------------------------------------------------- 보안 로그
test('보안 로그 결정 버튼: 서버로 {decision} 만 보내고 항목이 서버 응답으로 바뀐다. 전송 뒤에는 서버 로그로 다시 받는다', async () => {
  let audit = structuredClone(AUDIT);
  const calls = fakeFetch({
    'GET /messages': [],
    'GET /audit': () => jsonRes(200, audit),
    'POST /audit/draft%3Aabc/decision': () => {
      audit = audit.map((e) => (e.id === 'draft:abc' ? { ...e, kind: 'approved', decided_by: 'human:ops' } : e));
      return jsonRes(200, audit[1]);
    },
    'POST /messages': () => {
      audit = [...audit, { id: 'audit:run2:1', time: '09:50:00', kind: 'deny', text: L('차단', 'blocked'), decided_by: null }];
      return jsonRes(200, { reply: { id: 'm1', role: 'agent', text: L('답', 'a'), blocked: false }, logs: [{ id: 'log_zzz', time: '1', kind: 'ok', text: 'x', decided_by: null }], bundle: null });
    },
  });
  const { store, mk, actions } = await boot(realApi());
  const sl = mk(securitylog);
  fire(byAct(sl, 'decide', 'approve')[0], 'click');
  await tick(); await tick();
  const post = calls.find((c) => c.method === 'POST');
  assert.equal(post.url, `${BASE}/audit/draft%3Aabc/decision`);
  assert.equal(post.body, '{"decision":"approve"}');
  assert.equal(store.getState().logs.find((l) => l.id === 'draft:abc').kind, 'approved');
  assert.equal(byAct(sl, 'decide').length, 0, '결정된 항목에는 버튼이 없다');
  await actions.send('안녕');
  const ids = store.getState().logs.map((l) => l.id);
  assert.deepEqual(ids, ['audit:run1:3', 'draft:abc', 'audit:run2:1'], '서버 기록만 — 응답에 딸린 예시 로그를 섞지 않는다');
});

// ---------------------------------------------------------------------------------------------- 근거 선택
test('(a) 묶음의 실록 언급·행사 카드를 누르면 선택이 채워지고 근거가 mention:/event: 로 뜬다. 버튼이라 키보드로도 선택된다', async () => {
  fakeFetch({ 'GET /messages': [], 'GET /audit': [] });
  const bundle = realBundle();
  const { store, mk } = await boot(realApi(), { chatBundle: bundle });
  const cd = mk(cards); const ra = mk(rationale);
  await tick();
  const btns = cd.find((e) => e.dataset?.act === 'select-item');
  assert.ok(btns.every((b) => b.tag === 'button' && b.attrs.type === 'button'), '버튼(탭 순서·Enter·Space 기본 동작)');
  assert.deepEqual(btns.map((b) => `${b.dataset.kind}:${b.dataset.id}`), ['mention:story_sample_a1', 'mention:story_sample_a2', 'mention:story_sample_b1', 'event:sample:1']);
  assert.match(ra.text, /카드를 고르면 판단 근거가 보여요/);
  // 근거가 있는 언급
  fire(btns[0], 'click');
  await tick();
  assert.deepEqual([store.getState().selectedSeg, store.getState().selectedNow], ['story_sample_a1', null]);
  assert.ok(ra.find((e) => e.dataset?.act === 'chip').length > 0);
  assert.match(ra.text, /◆ 근거 있음/);
  const pressed = cd.find((e) => e.dataset?.act === 'select-item' && e.attrs['aria-pressed'] === 'true');
  assert.deepEqual(pressed.map((b) => b.dataset.id), ['story_sample_a1']);
  // 근거가 없는 언급은 사실대로
  fire(cd.find((e) => e.dataset?.act === 'select-item' && e.dataset.id === 'story_sample_a2')[0], 'click');
  await tick();
  assert.match(ra.text, /이 카드의 판단 근거 없음/);
  // 행사
  fire(cd.find((e) => e.dataset?.act === 'select-item' && e.dataset.kind === 'event')[0], 'click');
  await tick();
  assert.deepEqual([store.getState().selectedSeg, store.getState().selectedNow], [null, 'sample:1']);
  assert.match(ra.text, /◆ 근거 있음/);
  // 보기 모드가 해당 종류를 숨기고 있으면 둘 다 보기로
  store.setState({ mode: 'old' });
  fire(cd.find((e) => e.dataset?.act === 'select-item' && e.dataset.kind === 'event')[0], 'click');
  assert.equal(store.getState().mode, 'both');
});

test('카드 id: 서버가 준 card_id 를 그대로 쓴다(추정 없음). card_id 가 없거나 문자열이 아니거나 너무 길면 선택 버튼이 없다', () => {
  const b = realBundle((r) => {
    r.mentions.anchors[1].mentions[0].article_id = 'sample_a1'; // 다른 앵커에서 같은 기사
    r.mentions.anchors[1].mentions[0].card_id = 'story_sample_a1_2';
    r.rationale['mention:story_sample_a1_2'] = rat('mention:story_sample_a1_2');
  });
  assert.deepEqual([...mentionCardIds(b).values()], ['story_sample_a1', 'story_sample_a2', 'story_sample_a1_2']);
  const bad = realBundle((r) => {
    r.mentions.anchors[0].mentions[0].card_id = 42;
    r.mentions.anchors[0].mentions[1].card_id = 'x'.repeat(500);
    delete r.mentions.anchors[1].mentions[0].card_id;
  });
  assert.equal(mentionCardIds(bad).size, 0);
  assert.ok(bad.mentions.anchors.every((a) => a.mentions.every((m) => m.card_id === null)));
});

test('B2: 같은 기사가 두 앵커에 걸리고 한쪽 근거가 빠져도, 다른 쪽 근거가 대신 뜨지 않는다', async () => {
  fakeFetch({ 'GET /messages': [], 'GET /audit': [] });
  const b = realBundle((r) => {
    r.mentions.anchors[1].mentions[0].article_id = 'sample_a1';
    r.mentions.anchors[1].mentions[0].card_id = 'story_sample_a1_2'; // 근거(rationale)는 없다
  });
  const { store, mk } = await boot(realApi(), { chatBundle: b, mode: 'both' });
  const cd = mk(cards); const ra = mk(rationale);
  await tick();
  const btns = byAct(cd, 'select-item');
  assert.deepEqual(btns.filter((x) => x.dataset.kind === 'mention').map((x) => x.dataset.id), ['story_sample_a1', 'story_sample_a2', 'story_sample_a1_2']);
  fire(btns.find((x) => x.dataset.id === 'story_sample_a1_2'), 'click');
  await tick();
  assert.equal(store.getState().selectedSeg, 'story_sample_a1_2');
  assert.equal(ra.find((e) => e.dataset?.act === 'chip').length, 0, '다른 쪽(story_sample_a1) 근거가 뜨지 않는다');
  assert.match(ra.text, /이 카드의 판단 근거 없음/);
  fire(byAct(cd, 'select-item').find((x) => x.dataset.id === 'story_sample_a1'), 'click');
  await tick();
  assert.ok(ra.find((e) => e.dataset?.act === 'chip').length > 0);
});

test('card_id 가 없는 언급에는 선택 버튼이 없다', async () => {
  fakeFetch({ 'GET /messages': [], 'GET /audit': [] });
  const b = realBundle((r) => { for (const a of r.mentions.anchors) for (const m of a.mentions) delete m.card_id; });
  const { mk } = await boot(realApi(), { chatBundle: b });
  const cd = mk(cards);
  await tick();
  assert.deepEqual(byAct(cd, 'select-item').map((x) => x.dataset.kind), ['event']);
});

test('실제 모드에서 새 묶음이 오면 이전 선택을 비운다', async () => {
  fakeFetch({ 'GET /messages': [], 'GET /audit': [], 'POST /messages': () => jsonRes(200, { reply: { id: 'm', role: 'agent', text: 'ok', blocked: false }, logs: [], bundle: JSON.parse(JSON.stringify(realBundle())) }) });
  const { store, actions } = await boot(realApi());
  store.setState({ selectedSeg: 'story_old', selectedNow: 'old_event' });
  await actions.send('1일차 창덕궁');
  assert.deepEqual([store.getState().selectedSeg, store.getState().selectedNow], [null, null]);
  assert.ok(store.getState().chatBundle);
});

// ---------------------------------------------------------------------------------------------- 문제 코드
const TABLE = {
  AMPM_ASSUMED: '오전·오후 표기가 없어 시간을 가정했어요 — 확인해 주세요',
  TIME_FORMAT: '시각을 확인하지 못한 일정이 있어요', TIME_NOT_IN_QUOTE: '시각을 확인하지 못한 일정이 있어요', TIME_WITHOUT_DATE: '시각을 확인하지 못한 일정이 있어요',
  DATE_FORMAT: '날짜를 확인하지 못한 일정이 있어요', DATE_NOT_IN_QUOTE: '날짜를 확인하지 못한 일정이 있어요', DATE_INVALID: '날짜를 확인하지 못한 일정이 있어요',
  COORD_UNKNOWN: '좌표를 모르는 장소는 지도에 핀이 없어요 — 목록·카드에는 나와요', OVERLAP: '시간이 겹치는 일정이 있어요', LONG_SPAN: '12시간이 넘는 일정이 있어요 — 확인이 필요해요',
  DAY_UNTIMED: '시각을 모르는 일정이 있어 그날의 빈 시간은 계산하지 않았어요', FREE_SLOTS_INCOMPLETE: '날짜·시각을 모르는 일정은 빈 시간 계산에서 빠졌어요',
  EVENTS_UNAVAILABLE: '주변 행사를 검색하지 못했어요', TRUNCATED: '양이 많아 일부만 보여요',
  NAME_PARTICLE_STRIPPED: '이름 끝의 조사를 떼고 장소를 찾은 곳이 있어요',
  BAD_FIELD_TYPE: '이름이나 일부 값을 확인하지 못한 일정이 있어요', NAME_NOT_IN_QUOTE: '이름이나 일부 값을 확인하지 못한 일정이 있어요', NAME_MISSING: '이름이나 일부 값을 확인하지 못한 일정이 있어요', ANCHOR_NO_NAME: '이름이나 일부 값을 확인하지 못한 일정이 있어요',
  YEAR_ASSUMED: '연도가 없어 다가오는 날짜로 정했어요 — 여행 기간을 넣으면 정확해져요', QUOTE_NOT_FOUND: '원문에서 확인되지 않은 일정 후보는 뺐어요', NO_ANCHOR_VERIFIED: '원문에서 확인된 일정이 없어요',
  TYPE_DOWNGRADED: '숙소인지 확실하지 않은 곳은 방문지로 처리했어요', LLM_FAILED: '일정을 읽는 중 문제가 있었어요 — 다시 시도해 주세요',
  MENTION_NO_MATCH: '일부 실록 기록을 불러오지 못했어요', FIELD_DROPPED: '서버 응답의 일부를 읽지 못해 뺐어요',
  ROUTE_PROVIDER_REMOTE_REFUSED: '이동 시간을 계산하지 못해 이동 시간이 없어요', SOMETHING_NEW: '확인이 필요한 항목이 있어요',
};

test('문제 코드: 코드별 고정 문구(ko), 내부 동작 코드는 목록에서 뺀다, 모르는 코드는 일반 문구, 서버 message 는 화면에 없다', () => {
  for (const [code, text] of Object.entries(TABLE)) {
    const [line] = problemLines({ problems: [{ code, message: EVIL }] });
    assert.equal(ko(line.key, line.params), text, code);
    assert.ok(Object.hasOwn(DICTS.en, line.key), `${code} en 키`);
    assert.doesNotMatch(en(line.key, line.params), /[가-힣]/, `${code} en 문구에 한글 없음`);
  }
  const hidden = HIDDEN_PROBLEM_CODES.map((code) => ({ code, message: '1회차 QUOTE_NOT_FOUND 후 재시도' }));
  assert.deepEqual(HIDDEN_PROBLEM_CODES.sort(), ['CACHE_UNAVAILABLE', 'EXCLUDED_SUMMARIZED', 'LLM_RETRY', 'RETRY_SKIPPED_BUDGET']);
  assert.deepEqual(problemLines({ problems: hidden }), []);
  // 서버 message 원문(내부 문구)은 어떤 줄에도 들어가지 않는다
  const lines = problemLines({ problems: [
    { code: 'LLM_RETRY', message: '1회차 QUOTE_NOT_FOUND 후 재시도' },
    { code: 'AMPM_ASSUMED', message: 'anchor#1: 오전·오후 표기가 없어 모델의 해석을 썼음(anchor#1.from 14:00) — 확인 필요' },
    { code: 'SOMETHING_NEW', message: EVIL },
  ] });
  assert.deepEqual(lines.map((l) => l.key), ['bundle.problem.ampm', 'bundle.problem.generic']);
  assert.doesNotMatch(JSON.stringify(lines), /anchor#|QUOTE_NOT_FOUND|onerror/);
});

test('문제 코드: 장소 이름은 묶음의 앵커 이름과 정확히 같을 때만 붙인다 (좌표 모름·조사 제거·겹침)', () => {
  const b = { itinerary: { anchors: [{ name: '신촌' }, { name: '창덕궁' }, { name: '익선동' }] }, problems: [
    { code: 'COORD_UNKNOWN', message: '신촌: 장소 사전에 없어 좌표를 비워 둠' },
    { code: 'COORD_UNKNOWN', message: `${EVIL}: 장소 사전에 없어 좌표를 비워 둠` },
    { code: 'NAME_PARTICLE_STRIPPED', message: '창덕궁에서 → 창덕궁: 이름 끝 조사를 떼고 장소 사전에서 찾음' },
    { code: 'OVERLAP', message: '일정이 겹침: 창덕궁 / 익선동' },
  ] };
  const lines = problemLines(b);
  assert.deepEqual(lines.map((l) => ko(l.key, l.params)), [
    '신촌: 좌표를 몰라 지도에 핀이 없어요 (목록·카드에는 나와요)',
    '좌표를 모르는 장소는 지도에 핀이 없어요 — 목록·카드에는 나와요', // 앵커에 없는 이름은 붙이지 않는다
    '창덕궁: 이름 끝의 조사를 떼고 장소를 찾았어요',
    '창덕궁 · 익선동: 시간이 겹쳐요',
  ]);
  assert.match(en(lines[0].key, lines[0].params), /^신촌: no coordinates/);
});

test('문제 코드: 서버가 쓰는 모든 코드(_problem 호출)가 고정 문구를 갖거나 내부 코드로 숨겨진다', () => {
  const files = ['domains/kcontext/schedule/understand.py', 'domains/kcontext/pipeline/run.py', 'backend/chat_story.py'].map((f) => new URL(`../../../${f}`, import.meta.url));
  if (!files.every((f) => fs.existsSync(f))) return; // 프론트만 따로 복사된 환경
  const codes = new Set();
  for (const f of files) for (const m of fs.readFileSync(f, 'utf8').matchAll(/_problem\(\s*"([A-Z][A-Z_]+)"/g)) codes.add(m[1]);
  assert.ok(codes.size >= 40, `코드 ${codes.size}개`);
  const generic = [];
  for (const code of codes) {
    if (HIDDEN_PROBLEM_CODES.includes(code)) continue;
    if (problemLines({ problems: [{ code, message: '' }] })[0].key === 'bundle.problem.generic') generic.push(code);
  }
  assert.deepEqual(generic, [], '일반 문구로 떨어지는 코드는 i18n 을 추가한다');
  assert.ok(codes.has('AMPM_ASSUMED'));
});

test('타임라인: 문제 목록은 고정 문구만(서버 message 와 내부 코드 없음), en 전환', async () => {
  fakeFetch({ 'GET /messages': [], 'GET /audit': [] });
  const bundle = realBundle((r) => {
    r.problems = [
      { code: 'LLM_RETRY', message: '1회차 QUOTE_NOT_FOUND 후 재시도' },
      { code: 'AMPM_ASSUMED', message: 'anchor#1: …(anchor#1.from 14:00)' },
      { code: 'CACHE_UNAVAILABLE', message: '캐시를 쓸 수 없음 (OSError)' },
      { code: 'ZZZ', message: EVIL },
    ];
    r.itinerary.anchors[1].name = '창덕궁';
  });
  const { store, mk } = await boot(realApi(), { chatBundle: bundle });
  const tl = mk(timeline);
  const items = tl.find((e) => (e.attrs?.class ?? '').split(' ').includes('timeline-problems__item')).map((e) => e.text);
  assert.deepEqual(items, ['오전·오후 표기가 없어 시간을 가정했어요 — 확인해 주세요', '확인이 필요한 항목이 있어요']);
  assert.doesNotMatch(tl.text, /QUOTE_NOT_FOUND|anchor#|OSError|onerror/);
  store.setState({ lang: 'en' });
  assert.match(tl.text, /No AM\/PM was given/);
  assert.match(tl.text, /Some items need checking/);
});

// ---------------------------------------------------------------------------------------------- 시각
test('(e) 서버 시각(UTC ISO)은 한국 시간으로: ko "10월 10일 0:51", en 영어 형식, 읽을 수 없으면 원문 대신 시각 없는 문구', () => {
  assert.equal(formatServerTime('2026-10-09T15:51:48Z', 'ko'), '10월 10일 0:51');
  assert.equal(formatServerTime('2026-10-09T15:51:48Z', 'en'), 'Oct 10, 12:51 AM (KST)');
  assert.equal(formatServerTime('2026-12-31T20:00:00Z', 'ko'), '1월 1일 5:00', '해를 넘겨도 날짜가 맞다');
  assert.equal(formatServerTime('2026-10-10T03:04:00+09:00', 'ko'), '10월 10일 3:04');
  for (const bad of ['어제', '2026-13-45T99:99:99Z', '', null, undefined, 5, EVIL]) assert.equal(formatServerTime(bad, 'ko'), null, String(bad));
  const sched = (at) => ({ source: 'cache', attempts: 0, model: null, prompt_sha: 'x', cache_created_at: at });
  assert.equal(flat(scheduleNoteNode(sched('2026-10-09T15:51:48Z'), ko)), '이전 결과 재사용 (10월 10일 0:51)');
  assert.equal(flat(scheduleNoteNode(sched('2026-10-09T15:51:48Z'), en)), 'Previous result reused (Oct 10, 12:51 AM (KST))');
  assert.equal(flat(scheduleNoteNode(sched(EVIL), ko)), '이전 결과 재사용');
  assert.doesNotMatch(flat(scheduleNoteNode(sched('2026-10-09T15:51:48Z'), ko)), /2026|T15|Z/);
});

// ---------------------------------------------------------------------------------------------- 명시 모드 base
test('(f) ?api=chat·http 를 명시하고 base 가 없으면 auto 와 같은 기본 주소, base 가 있으면 그것, mock 은 무관', async () => {
  fakeFetch({});
  assert.equal((await resolveApi({ mode: 'chat' })).baseUrl, DEFAULT_CHAT_BASE);
  assert.equal((await resolveApi({ mode: 'http' })).baseUrl, DEFAULT_CHAT_BASE);
  assert.equal((await resolveApi({ mode: 'chat', baseUrl: 'http://h:9/api' })).baseUrl, 'http://h:9/api');
  const calls = fakeFetch({ 'GET /messages': [] });
  const auto = await resolveApi({ mode: 'auto', baseUrl: BASE });
  assert.equal(auto.mode, 'chat');
  assert.equal(calls.length, 1);
  assert.equal((await resolveApi({ mode: 'mock', latencyMs: 0 })).mode, 'mock');
});

// ---------------------------------------------------------------------------------------------- 카카오
function makeKakao() {
  const log = { lines: [], markers: [], overlays: [] };
  class LatLng { constructor(a, b) { this.lat = a; this.lng = b; } }
  class Map { constructor() { log.map = this; } relayout() {} setBounds() {} setCenter() {} setLevel() {} }
  class Marker { constructor(o) { this.o = o; log.markers.push(this); } setMap() {} }
  class Polyline { constructor(o) { this.o = o; log.lines.push(this); } setMap() {} }
  class CustomOverlay { constructor(o) { this.o = o; log.overlays.push(this); } setMap() {} }
  class LatLngBounds { extend() {} }
  return { log, maps: { LatLng, Map, Marker, Polyline, CustomOverlay, LatLngBounds, event: { addListener() {} } } };
}

test('(b) 카카오 렌더러: 같은 날 이웃 핀 사이 점선 + "직선 연결(실제 길 아님)" 라벨, 실제 모드는 내 위치(예시)를 그리지 않는다', () => {
  const k = makeKakao();
  const view = createKakaoView(k, new El('div', 'html'), ko, { myLocation: false });
  view.update({ chatBundle: realBundle(), day: 1, data: {} });
  assert.equal(k.log.markers.length, 3, '좌표 있는 앵커 핀');
  assert.equal(k.log.lines.length, 1);
  assert.equal(k.log.lines[0].o.strokeStyle, 'shortdot', '실선이 아니라 점선');
  assert.deepEqual(k.log.lines[0].o.path.map((p) => [p.lat, p.lng]), [[37.57964694739535, 126.99099980677127], [37.5734371942191, 126.989775723896]]);
  assert.match(k.log.overlays[0].o.content.text, /직선 연결\(실제 길 아님\)/);
  assert.match(view.status.text, /직선 연결\(실제 길 아님\)/, '오버레이 없이도 글자 라벨이 남는다');
  // routes 가 없으면(v1) 점선 없음
  const k1 = makeKakao();
  const v1 = createKakaoView(k1, new El('div', 'html'), ko);
  v1.update({ chatBundle: validateChatBundle(structuredClone(CHAT_BUNDLE_SAMPLE)).bundle, day: 1, data: {} });
  assert.equal(k1.log.lines.length, 0);
  assert.equal(k1.log.overlays.length, 0);
  // 내 위치: 기본(mock)은 그린다, 실제 모드(myLocation:false)는 그리지 않는다
  const km = makeKakao();
  createKakaoView(km, new El('div', 'html'), ko).update({ chatBundle: null, day: 1, data: { cards: [], routes: [] } });
  assert.equal(km.log.overlays.length, 1, '예시 내 위치');
  const kr = makeKakao();
  createKakaoView(kr, new El('div', 'html'), ko, { myLocation: false }).update({ chatBundle: null, day: 1, data: { cards: [], routes: [] } });
  assert.equal(kr.log.overlays.length, 0);
  assert.equal(kr.log.markers.length, 0);
});

test('i18n: T318 이 추가한 키는 ko·en 모두에 있다', () => {
  const keys = ['mock.status.empty', 'real.empty.timeline', 'real.empty.cards', 'real.empty.map', 'real.error', 'bundle.select_item', 'bundle.problem.generic', 'bundle.problem.ampm'];
  for (const k of keys) { assert.ok(DICTS.ko[k], k); assert.ok(DICTS.en[k], k); }
});
