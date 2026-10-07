import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/lib/store.js';
import { createController, initialState } from '../src/events/controller.js';
import { createMockEventsApi, EventsApiError } from '../src/events/api.js';

const memStorage = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v), m }; };
function setup(api = createMockEventsApi(), storage = memStorage(), today = '2026-10-15') {
  const store = createStore(initialState(storage, { today }));
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
  const again = createStore(initialState(x.storage, { today: '2030-01-01' }));
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
  assert.equal(JSON.parse(x.storage.m.get('kc.events.v1')).itinerary.length, 2); // 저장됨
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
