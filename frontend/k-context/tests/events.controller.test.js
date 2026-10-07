import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/lib/store.js';
import { createController, initialState } from '../src/events/controller.js';
import { createMockEventsApi, EventsApiError } from '../src/events/api.js';

const memStorage = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v), m }; };
function setup(api = createMockEventsApi(), storage = memStorage(), today = '2026-10-15') {
  const store = createStore(initialState(storage, { today, demo: api.demo }));
  const c = createController({ store, api, storage, now: () => new Date('2026-10-07T03:00:00Z') });
  return { store, c, api, storage };
}
const get = (x) => x.store.getState();

test('초기 상태: 서울 오늘 기준 기본 날짜, 저장된 값이 있으면 복원', () => {
  const x = setup();
  assert.equal(get(x).form.from, '2026-10-15');
  assert.equal(get(x).form.to, '2026-10-18');
  x.c.setForm({ interests: '공연' });
  x.c.setLang('en');
  const again = createStore(initialState(x.storage, { today: '2030-01-01', demo: true }));
  assert.equal(again.getState().form.interests, '공연');
  assert.equal(again.getState().lang, 'en');
  assert.equal(again.getState().form.from, '2026-10-15'); // 저장된 폼이 우선
});

test('검색: 잘못된 입력은 요청 없이 오류 표시, 정상이면 결과', async () => {
  let called = 0;
  const api = { ...createMockEventsApi(), async search(b) { called++; return createMockEventsApi().search(b); } };
  const x = setup(api);
  x.c.setForm({ from: '2026-10-19', to: '2026-10-15' });
  assert.equal(await x.c.search(), null);
  assert.equal(get(x).formErrors.dates, 'form.error.dates');
  assert.equal(called, 0);
  x.c.setForm({ from: '2026-10-16', to: '2026-10-19' });
  const r = await x.c.search();
  assert.ok(r.events.length >= 2 && called === 1);
  assert.deepEqual(get(x).formErrors, {});
  assert.equal(get(x).loading, false);
});

test('검색 실패: 네트워크와 서버 오류를 구분하고 이전 결과는 유지', async () => {
  const x = setup();
  x.c.setForm({ from: '2026-10-16', to: '2026-10-17' });
  await x.c.search();
  const before = get(x).result;
  x.api.search = async () => { throw new EventsApiError('network', 0, 'n'); };
  assert.equal(await x.c.search(), null);
  assert.equal(get(x).error, 'error.network');
  assert.equal(get(x).result, before);
  x.api.search = async () => { throw new EventsApiError('internal_error', 500, 's'); };
  await x.c.search();
  assert.equal(get(x).error, 'error.server');
});

test('상세: 열기·닫기, 늦게 도착한 응답은 버린다', async () => {
  const x = setup();
  await x.c.openDetail('demo:1');
  assert.equal(get(x).detail.id, 'demo:1');
  x.c.closeDetail();
  assert.equal(get(x).detail, null);
  const waiting = {};
  x.api.detail = (id) => new Promise((res) => { waiting[id] = () => res({ id, title: id }); });
  const slow = x.c.openDetail('demo:1');
  const fast = x.c.openDetail('demo:2');
  waiting['demo:2'](); // 나중에 연 것이 먼저 도착
  await fast;
  waiting['demo:1'](); // 먼저 연 것이 늦게 도착 — 버려져야 한다
  await slow;
  assert.equal(get(x).selectedId, 'demo:2');
  assert.equal(get(x).detail.id, 'demo:2');
  x.api.detail = createMockEventsApi().detail;
  await x.c.openDetail('demo:999'); // 없는 행사
  assert.equal(get(x).detail, null);
  assert.equal(get(x).error, 'error.server');
});

test('내 일정: 입력 검증·정렬·삭제(행사 항목은 이 경로로 지우지 않는다)', () => {
  const x = setup();
  assert.equal(x.c.addUserPlan({ title: '점심', date: '2026-10-16', start: '13:00', end: '12:00' }), false);
  assert.equal(get(x).planFormError, true);
  assert.equal(x.c.addUserPlan({ title: '점심', date: '2026-10-16', start: '12:00', end: '13:00' }), true);
  assert.equal(x.c.addUserPlan({ title: '아침', date: '2026-10-16', start: '08:00', end: '09:00' }), true);
  assert.deepEqual(get(x).itinerary.map((p) => p.title), ['아침', '점심']);
  assert.equal(get(x).planFormError, false);
  x.store.setState({ itinerary: [...get(x).itinerary, { id: 'evt:1', title: '행사', date: '2026-10-16', start: '19:00', end: '20:00', source: 'catalog' }] });
  x.c.deleteUserPlan('evt:1');
  assert.equal(get(x).itinerary.length, 3);
  x.c.deleteUserPlan(get(x).itinerary[0].id);
  assert.equal(get(x).itinerary.length, 2);
  assert.equal(JSON.parse(x.storage.m.get('kc.events.v1.demo')).itinerary.length, 2); // 저장됨
});

test('샘플 일정은 데모 모드에서만', () => {
  const real = setup({ ...createMockEventsApi(), demo: false });
  real.c.loadSamplePlans();
  assert.equal(get(real).itinerary.length, 0);
  const demo = setup();
  demo.c.loadSamplePlans();
  demo.c.loadSamplePlans();
  assert.equal(get(demo).itinerary.length, 2);
});

test('행사 일정 추가·취소: 서버가 돌려준 일정을 그대로 쓴다', async () => {
  const x = setup();
  x.c.setForm({ from: '2026-10-16', to: '2026-10-17' });
  x.c.addUserPlan({ title: '점심', date: '2026-10-16', start: '12:00', end: '13:00' });
  const r = await x.c.search();
  const sug = r.suggestions.find((s) => s.entry_id === 'demo:1');
  assert.equal(await x.c.addSession(sug), true);
  const added = get(x).itinerary.find((p) => p.source === 'catalog');
  assert.equal(added.entry_id, 'demo:1');
  assert.equal(await x.c.removeCatalogItem(get(x).itinerary.find((p) => p.source === 'user').id), false); // 내 일정은 안 됨
  assert.equal(await x.c.removeCatalogItem(added.id), true);
  assert.equal(get(x).itinerary.filter((p) => p.source === 'catalog').length, 0);
});

test('일정 추가 거절(409): 이유를 보이고 force 로 다시 시도할 수 있다', async () => {
  const x = setup();
  let force;
  x.api.addToPlan = async (b) => {
    force = b.force;
    if (!b.force) throw new EventsApiError('conflict', 409, '기존 일정과 겹침');
    return { itinerary: [{ id: 'evt:x', title: 't', date: 'd', start: 's', end: 'e', source: 'catalog' }] };
  };
  const sug = { entry_id: 'e1', date: '2026-10-16', session: { start_time: '19:00' } };
  assert.equal(await x.c.addSession(sug), false);
  assert.equal(get(x).planError.code, 'conflict');
  assert.equal(get(x).planError.message, '기존 일정과 겹침');
  assert.equal(force, false);
  assert.equal(await x.c.addSession(sug, { force: true }), true);
  assert.equal(force, true);
  assert.equal(get(x).planError, null);
});

test('저장한 행사: 저장·취소·변경 배지·확인', async () => {
  const x = setup();
  await x.c.openDetail('demo:1');
  const ev = get(x).detail;
  x.c.toggleSave(ev);
  assert.ok(get(x).saved['demo:1']);
  assert.equal(get(x).saved['demo:1'].savedAt, '2026-10-07T12:00'); // 서울 시각
  x.api.savedChanges = async (ids, since) => {
    assert.deepEqual(ids, ['demo:1']);
    assert.equal(since, '2026-10-07T12:00');
    return { saved: [{ entry_id: 'demo:1', has_major: true, changes: [{ field: 'start_date', old: 'a', new: 'b', detected_at: '2026-10-07T13:00', importance: 'major' }] }] };
  };
  await x.c.checkSaved();
  assert.equal(get(x).saved['demo:1'].hasMajor, true);
  assert.equal(get(x).saved['demo:1'].changes.length, 1);
  x.c.ackSaved('demo:1');
  assert.equal(get(x).saved['demo:1'].changes.length, 0);
  x.c.toggleSave(ev);
  assert.deepEqual(get(x).saved, {});
});

test('변경 확인이 실패해도 저장 목록은 그대로다', async () => {
  const x = setup();
  await x.c.openDetail('demo:1');
  x.c.toggleSave(get(x).detail);
  x.api.savedChanges = async () => { throw new EventsApiError('network', 0, 'n'); };
  await x.c.checkSaved();
  assert.ok(get(x).saved['demo:1']);
  assert.equal(get(x).checking, false);
});

test('제보: 클라이언트 검증·서버 검증 메시지·성공', async () => {
  const x = setup();
  assert.equal(await x.c.submitReport({ official_link: 'nope', reason: '사유가 충분히 깁니다' }), false);
  assert.equal(get(x).reportError, 'client');
  assert.equal(await x.c.submitReport({ official_link: 'https://a.invalid/x', reason: '짧' }), false);
  x.api.submitReport = async () => { throw new EventsApiError('bad_request', 400, '공식 링크가 필요하다'); };
  assert.equal(await x.c.submitReport({ official_link: 'https://a.invalid/x', reason: '사유가 충분히 깁니다' }), false);
  assert.equal(get(x).reportError, '공식 링크가 필요하다');
  let sent;
  x.api.submitReport = async (b) => { sent = b; return { report: { status: 'pending' } }; };
  assert.equal(await x.c.submitReport({ kind: 'new_event', official_link: ' https://a.invalid/x ', reason: ' 사유가 충분히 깁니다 ', entry_id: '', fields: { title: ' ○○ ', start_date: '', note: undefined } }), true);
  assert.deepEqual(sent, { kind: 'new_event', official_link: 'https://a.invalid/x', reason: '사유가 충분히 깁니다', fields: { title: '○○' } });
  assert.equal(get(x).reportStatus, 'sent');
});


test('저장 키: 데모와 실제 모드의 일정·저장 목록이 섞이지 않는다', () => {
  const storage = memStorage();
  const demo = setup(createMockEventsApi(), storage);
  demo.c.addUserPlan({ title: '데모 점심', date: '2026-10-16', start: '12:00', end: '13:00' });
  const real = setup({ ...createMockEventsApi(), demo: false }, storage);
  assert.equal(get(real).itinerary.length, 0);
  real.c.addUserPlan({ title: '실제 점심', date: '2026-10-16', start: '12:00', end: '13:00' });
  const again = createStore(initialState(storage, { today: '2026-10-15', demo: true }));
  assert.deepEqual(again.getState().itinerary.map((p) => p.title), ['데모 점심']);
  assert.ok(storage.m.has('kc.events.v1') && storage.m.has('kc.events.v1.demo'));
});

test('저장소에서 읽은 일정·저장 목록은 검증한다(손상된 항목 하나가 검색을 막지 않는다)', async () => {
  const storage = memStorage();
  storage.setItem('kc.events.v1.demo', JSON.stringify({
    itinerary: [
      { id: 'ok', title: '점심', date: '2026-10-16', start: '12:00', end: '13:00' },
      { id: 'bad1', date: '내일', start: '12:00', end: '13:00' }, { id: '', date: '2026-10-16', start: '1', end: '2' }, null, 'x',
      { id: 'bad2', date: '2026-10-16', start: '14:00', end: '13:00' },
      { id: 'bad3', date: '2026-10-16', start: '10:00', end: '11:00', lat: 'abc', lng: 1 },
    ],
    saved: { 'ev:1': { id: 'ev:1', title: '저장', seenAt: '2026-10-07T12:00' }, 'ev:2': 'x', 'ev:3': { title: 1 } },
  }));
  const x = setup(createMockEventsApi(), storage);
  assert.deepEqual(get(x).itinerary.map((p) => p.id), ['ok']);
  assert.deepEqual(Object.keys(get(x).saved), ['ev:1']);
  x.c.setForm({ from: '2026-10-16', to: '2026-10-17' });
  assert.ok(await x.c.search());
  storage.setItem('kc.events.v1.demo', JSON.stringify({ itinerary: 'oops', saved: [1, 2] }));
  const y = setup(createMockEventsApi(), storage);
  assert.deepEqual(get(y).itinerary, []);
  assert.deepEqual(get(y).saved, {});
});

test('검색 경쟁: 먼저 시작한 느린 검색의 응답이 최신 결과를 덮지 않는다', async () => {
  const x = setup();
  const waiting = [];
  x.api.search = (b) => new Promise((res) => waiting.push(() => res({ events: [{ id: b.trip.from }], suggestions: [], excluded: [], problems: [], coverage: null, map: { points: [], unlocated: [] } })));
  x.c.setForm({ from: '2026-10-16', to: '2026-10-17' });
  const slow = x.c.search();
  x.c.setForm({ from: '2026-10-17', to: '2026-10-18' });
  const fast = x.c.search();
  waiting[1](); // 나중 검색이 먼저 도착
  await fast;
  waiting[0](); // 먼저 시작한 검색이 늦게 도착 — 버려져야 한다
  assert.equal(await slow, null);
  assert.deepEqual(get(x).result.events.map((e) => e.id), ['2026-10-17']);
  assert.equal(get(x).loading, false);
});
