import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createEventsApi, createHttpEventsApi, createMockEventsApi, defaultBase, EventsApiError } from '../src/events/api.js';

function fakeFetch(responder) {
  const calls = [];
  const f = async (url, init) => {
    calls.push({ url, ...init });
    return responder(url, init, calls.length);
  };
  f.calls = calls;
  return f;
}
const json = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });

test('http: 검색은 POST /events/search 에 JSON 본문, 관리자 헤더는 붙이지 않는다', async () => {
  const f = fakeFetch(() => json(200, { events: [] }));
  const api = createHttpEventsApi({ baseUrl: 'http://x/api', fetchImpl: f });
  const out = await api.search({ trip: { from: '2026-10-15', to: '2026-10-18' } });
  assert.deepEqual(out, { events: [] });
  const c = f.calls[0];
  assert.equal(c.url, 'http://x/api/events/search');
  assert.equal(c.method, 'POST');
  assert.equal(c.headers['Content-Type'], 'application/json');
  assert.equal('X-Admin-Token' in c.headers, false);
  assert.equal(JSON.parse(c.body).trip.from, '2026-10-15');
});

test('http: 상세·저장 변경·제보·일정 추가·취소 경로', async () => {
  const f = fakeFetch(() => json(200, { ok: 1 }));
  const api = createHttpEventsApi({ baseUrl: '/api', fetchImpl: f });
  await api.detail('ev:abc', { lang: 'en', demo: true });
  await api.savedChanges(['ev:1'], '2026-10-07T12:00');
  await api.savedChanges(['ev:1']);
  await api.submitReport({ kind: 'other' });
  await api.addToPlan({ entry_id: 'e' });
  await api.removeFromPlan({ item_id: 'i' });
  await api.coverage();
  assert.deepEqual(f.calls.map((c) => `${c.method} ${c.url}`), [
    'GET /api/events/ev%3Aabc?lang=en&demo=true',
    'POST /api/events/saved-changes', 'POST /api/events/saved-changes', 'POST /api/reports',
    'POST /api/events/itinerary/add', 'POST /api/events/itinerary/remove', 'GET /api/events/coverage',
  ]);
  assert.deepEqual(JSON.parse(f.calls[1].body), { ids: ['ev:1'], since: '2026-10-07T12:00' });
  assert.deepEqual(JSON.parse(f.calls[2].body), { ids: ['ev:1'] });
  assert.equal(f.calls[0].body, undefined);
});

test('http: 관리자 요청에만 토큰 헤더를 보내고, 결정 본문에 신원은 없다', async () => {
  const f = fakeFetch(() => json(200, {}));
  const api = createHttpEventsApi({ baseUrl: '/api', fetchImpl: f });
  await api.admin.review('tok');
  await api.admin.reports('tok', 'pending');
  await api.admin.decide('tok', 'rpt_1', 'approve', '메모');
  await api.admin.refresh('tok', 'seoul_openapi', true);
  await api.admin.linkCheck('tok', 'caci', '확인');
  await api.admin.sources('tok');
  assert.ok(f.calls.every((c) => c.headers['X-Admin-Token'] === 'tok'));
  assert.equal(f.calls[1].url, '/api/admin/reports?status=pending');
  assert.deepEqual(JSON.parse(f.calls[2].body), { decision: 'approve', note: '메모' });
  assert.equal('reviewer' in JSON.parse(f.calls[2].body), false);
  assert.deepEqual(JSON.parse(f.calls[3].body), { sample: true });
});

test('http: 오류 응답은 code·status 를 가진 EventsApiError, 네트워크 실패는 network', async () => {
  const api = createHttpEventsApi({ baseUrl: '/api', fetchImpl: fakeFetch(() => json(403, { error: { code: 'forbidden', message: '닫힘' } })) });
  await assert.rejects(api.admin.review('x'), (e) => e instanceof EventsApiError && e.code === 'forbidden' && e.status === 403 && e.message === '닫힘');
  const net = createHttpEventsApi({ baseUrl: '/api', fetchImpl: async () => { throw new TypeError('Failed to fetch'); } });
  await assert.rejects(net.search({}), (e) => e.code === 'network' && e.status === 0);
  const html = createHttpEventsApi({ baseUrl: '/api', fetchImpl: async () => ({ ok: false, status: 502, json: async () => { throw new Error('x'); } }) });
  await assert.rejects(html.search({}), (e) => e.status === 502 && e.code === 'http_error');
  const empty = createHttpEventsApi({ baseUrl: '/api', fetchImpl: async () => ({ ok: true, status: 200, json: async () => { throw new Error('x'); } }) });
  await assert.rejects(empty.search({}), (e) => e.code === 'bad_response');
});

test('토큰이 오류 메시지·객체에 남지 않는다', async () => {
  const api = createHttpEventsApi({ baseUrl: '/api', fetchImpl: fakeFetch(() => json(403, { error: { code: 'forbidden', message: '관리자 토큰이 올바르지 않다' } })) });
  try {
    await api.admin.review('secret-token-value');
  } catch (e) {
    assert.equal(JSON.stringify({ m: e.message, c: e.code, s: e.status }).includes('secret-token-value'), false);
  }
});

test('기본 주소: 정적 서버(8766)면 같은 호스트의 8000 포트', () => {
  assert.equal(defaultBase({ port: '8766', protocol: 'http:', hostname: '127.0.0.1' }), 'http://127.0.0.1:8000/api');
  assert.equal(defaultBase({ port: '8000', protocol: 'http:', hostname: 'x' }), '/api');
  assert.equal(defaultBase(null), '/api');
});

test('createEventsApi: 모드 선택과 잘못된 모드', () => {
  assert.equal(createEventsApi({ mode: 'mock' }).demo, true);
  assert.equal(createEventsApi({ mode: 'http', fetchImpl: async () => {} }).demo, false);
  assert.throws(() => createEventsApi({ mode: 'x' }));
});

test('mock: 모든 행사가 데모이고 날짜·휴무·회차가 반영된다', async () => {
  const api = createMockEventsApi();
  const r = await api.search({ trip: { from: '2026-10-16', to: '2026-10-19' }, interests: ['공연'] });
  assert.ok(r.events.length >= 2 && r.events.every((e) => e.demo === true && e.title.startsWith('(데모)')));
  assert.equal(r.coverage.complete, false);
  const concert = r.events.find((e) => e.id === 'demo:1');
  assert.equal(concert.availability, 'session_match');
  assert.deepEqual(concert.interest_match, ['공연']);
  const exhibit = r.events.find((e) => e.id === 'demo:3');
  assert.equal(exhibit.availability, 'date_range_unconfirmed');
  const monday = exhibit.matching_dates.find((d) => d.date === '2026-10-19'); // 월요일 휴무
  assert.equal(monday.state, 'no');
  assert.deepEqual(r.map.unlocated, ['demo:3']);
  const none = await api.search({ trip: { from: '2026-12-01', to: '2026-12-02' } });
  assert.deepEqual(none.events, []);
});

test('mock: 일정 추가는 한 번만, 취소는 행사 항목만, 관리자 API 는 막힘', async () => {
  const api = createMockEventsApi();
  const itin = [{ id: 'p1', title: '점심', date: '2026-10-16', start: '12:00', end: '13:00', source: 'user' }];
  const a = await api.addToPlan({ entry_id: 'demo:1', date: '2026-10-16', start_time: '19:00', itinerary: itin });
  assert.equal(a.itinerary.length, 2);
  const again = await api.addToPlan({ entry_id: 'demo:1', date: '2026-10-16', start_time: '19:00', itinerary: a.itinerary });
  assert.equal(again.itinerary.length, 2);
  const id = a.itinerary[1].id;
  assert.equal((await api.removeFromPlan({ item_id: id, itinerary: a.itinerary })).itinerary.length, 1);
  assert.equal((await api.removeFromPlan({ item_id: 'p1', itinerary: a.itinerary })).itinerary.length, 2);
  await assert.rejects(api.addToPlan({ entry_id: 'demo:9', date: 'x', start_time: 'y', itinerary: [] }), (e) => e.code === 'not_found');
  await assert.rejects(api.admin.review('t'), (e) => e.code === 'forbidden');
  assert.equal((await api.submitReport({ kind: 'other' })).report.status, 'pending');
});
