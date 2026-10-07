// 화면용 읽기 전용 4종(cards·card·sources·rationale): fixture 드리프트, 응답 검증, resolveApi 의 메서드 단위 라우팅.
import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolveApi, createApi, DEFAULT_CHAT_BASE, HTTP_METHODS } from '../src/api/index.js';
import { createHttpApi } from '../src/api/http.js';
import { validateCard, validateSource } from '../src/api/schema.js';
import { CARDS } from '../src/data/cards.js';
import { SOURCES } from '../src/data/sources.js';
import { NOW_RATIONALE, storyRationale } from '../src/data/rationale.js';

const FIX = new URL('../../../backend/fixtures/screen/', import.meta.url);
const fixture = (n) => JSON.parse(readFileSync(fileURLToPath(new URL(n, FIX)), 'utf8'));
const viaJson = (v) => JSON.parse(JSON.stringify(v));

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });
const jsonRes = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
function fake(handler) {
  const calls = [];
  globalThis.fetch = async (url, init) => { calls.push(url); return handler(url, init); };
  return calls;
}
const BASE = 'http://x/api';

test('fixture JSON 이 프론트 mock 데이터와 같다(드리프트 방지)', () => {
  assert.deepEqual(fixture('cards.json'), viaJson(CARDS));
  assert.deepEqual(fixture('sources.json'), viaJson(Object.values(SOURCES)));
  const rat = {};
  for (const c of CARDS) rat[c.id] = c.kind === 'story' ? storyRationale(c.id, c.badge, c.sources.length, !!c.alternatives) : NOW_RATIONALE[c.id];
  assert.deepEqual(fixture('rationale.json'), viaJson(rat));
});

test('fixture 카드·출처는 validateCard·validateSource 0건', () => {
  for (const c of fixture('cards.json')) assert.deepEqual(validateCard(c), [], c.id);
  for (const s of fixture('sources.json')) assert.deepEqual(validateSource(s), [], s.id);
});

test('http: 4개 메서드가 해당 경로를 GET 하고 id 는 인코딩한다', async () => {
  const cards = fixture('cards.json');
  const calls = fake((url) => {
    if (url.endsWith('/cards')) return jsonRes(200, cards);
    if (url.endsWith('/sources')) return jsonRes(200, fixture('sources.json'));
    if (url.endsWith('/rationale')) return jsonRes(200, fixture('rationale.json')[cards[0].id]);
    return jsonRes(200, cards[0]);
  });
  const h = createHttpApi({ baseUrl: BASE });
  assert.equal((await h.getCards()).length, 6);
  assert.equal((await h.getCard(cards[0].id)).id, cards[0].id);
  assert.equal((await h.getSources()).length, 8);
  assert.equal((await h.getRationale(cards[0].id)).card_id, cards[0].id);
  await h.getCard('a/../b').catch(() => {});
  assert.deepEqual(calls, [`${BASE}/cards`, `${BASE}/cards/${cards[0].id}`, `${BASE}/sources`, `${BASE}/cards/${cards[0].id}/rationale`, `${BASE}/cards/a%2F..%2Fb`]);
});

test('http: 형식이 어긋난 응답은 bad_response, 오류 본문은 새지 않는다', async () => {
  const bad = { ...fixture('cards.json')[0], sources: [] };
  fake(() => jsonRes(200, [bad]));
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getCards(), (e) => e.code === 'bad_response');
  fake(() => jsonRes(200, { not: 'a card' }));
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getCard('x'), (e) => e.code === 'bad_response');
  fake(() => jsonRes(200, [{ id: 'd' }]));
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getSources(), (e) => e.code === 'bad_response');
  fake(() => jsonRes(200, { chips: 1 }));
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getRationale('x'), (e) => e.code === 'bad_response');
  fake(() => jsonRes(404, { error: { code: 'not_found', message: '/home/secret/cards.json' } }));
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getCard('nope'), (e) => e.code === 'not_found' && e.status === 404 && !e.message.includes('secret'));
});

test('resolveApi auto + backend 있음: 4개 메서드는 backend, 나머지는 mock(fetch 없음)', async () => {
  const cards = fixture('cards.json');
  const calls = fake((url) => {
    if (url.endsWith('/messages')) return jsonRes(200, []);
    if (url.endsWith('/cards')) return jsonRes(200, cards);
    if (url.endsWith('/sources')) return jsonRes(200, fixture('sources.json'));
    if (url.endsWith('/rationale')) return jsonRes(200, fixture('rationale.json')[cards[0].id]);
    return jsonRes(200, cards[0]);
  });
  const api = await resolveApi({ mode: 'auto', latencyMs: 0 });
  assert.equal(api.mode, 'chat');
  assert.deepEqual(HTTP_METHODS.slice().sort(), ['getCard', 'getCards', 'getMessages', 'getRationale', 'getSources', 'sendMessage']);
  calls.length = 0;
  await api.getCards(); await api.getCard(cards[0].id); await api.getSources(); await api.getRationale(cards[0].id);
  assert.deepEqual(calls, [`${DEFAULT_CHAT_BASE}/cards`, `${DEFAULT_CHAT_BASE}/cards/${cards[0].id}`, `${DEFAULT_CHAT_BASE}/sources`, `${DEFAULT_CHAT_BASE}/cards/${cards[0].id}/rationale`]);
  calls.length = 0;
  await api.getItinerary(); await api.getRoutes(); await api.getAuditLog();
  await assert.rejects(() => api.decideAudit('nope', 'approve'), /찾을 수 없음/); // mock 의 오류 — fetch 아님
  assert.equal(calls.length, 0);
});

test('resolveApi auto + backend 없음: 전부 mock, ?api=mock·http 는 그대로', async () => {
  const calls = fake(() => { throw new TypeError('fetch failed'); });
  const api = await resolveApi({ mode: 'auto', latencyMs: 0 });
  assert.equal(api.mode, 'mock');
  assert.equal((await api.getCards()).length, 6);
  assert.equal(createApi({ mode: 'mock' }).mode, 'mock');
  assert.equal(createApi({ mode: 'http', baseUrl: BASE }).mode, 'http');
  assert.equal(calls.length, 1); // probe 한 번뿐
});
