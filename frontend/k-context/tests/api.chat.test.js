import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createApi, resolveApi, DEFAULT_CHAT_BASE, API_METHODS, HTTP_METHODS } from '../src/api/index.js';
import { createHttpApi } from '../src/api/http.js';
import { createT } from '../src/lib/i18n.js';
import { messageView } from '../src/components/chat/logic.js';

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

const jsonRes = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
function fake(res) {
  const calls = [];
  globalThis.fetch = async (url, init) => { calls.push({ url, init }); return typeof res === 'function' ? res(url, init) : res; };
  return calls;
}
const BASE = 'http://x/api';

test('getMessages: GET {base}/messages, 배열 반환', async () => {
  const calls = fake(jsonRes(200, []));
  assert.deepEqual(await createHttpApi({ baseUrl: BASE }).getMessages(), []);
  assert.equal(calls[0].url, `${BASE}/messages`);
  assert.equal(calls[0].init.method, 'GET');
});

test('sendMessage 정상: POST JSON {text} 만 전송, reply.text 는 문자열', async () => {
  const calls = fake(jsonRes(200, { reply: { id: 'msg_002', role: 'agent', text: '안녕' }, logs: [{ id: 'a' }] }));
  const r = await createHttpApi({ baseUrl: BASE }).sendMessage('경복궁?');
  assert.equal(r.reply.text, '안녕');
  assert.equal(r.logs.length, 1);
  const { url, init } = calls[0];
  assert.equal(url, `${BASE}/messages`);
  assert.equal(init.method, 'POST');
  assert.equal(init.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(init.body), { text: '경복궁?' }); // 신원 필드 없음
  assert.equal(init.headers.Authorization, undefined);
});

test('차단 응답: reply.text 가 {ko,en}, blocked 유지, 화면 로직이 둘 다 그린다', async () => {
  const text = { ko: '허용된 범위가 아닙니다', en: 'Outside scope' };
  fake(jsonRes(200, { reply: { id: 'm', role: 'agent', text, blocked: true }, logs: [] }));
  const { reply } = await createHttpApi({ baseUrl: BASE }).sendMessage('x');
  assert.equal(reply.blocked, true);
  assert.equal(messageView(reply, createT(() => 'ko')).text, text.ko);
  assert.equal(messageView(reply, createT(() => 'en')).text, text.en);
  assert.equal(messageView({ role: 'agent', text: '평문' }, createT(() => 'en')).text, '평문');
});

test('오류 코드별 문구와 e.code, 서버 본문은 노출하지 않는다', async () => {
  const cases = [
    [429, 'busy', /잠시 후 다시 시도/],
    [503, 'llm_unavailable', /아직 설정되지 않았습니다/],
    [422, 'bad_text', /입력을 확인/],
    [502, 'pipeline_failed', /답을 만들지 못했습니다/],
  ];
  for (const [status, code, re] of cases) {
    fake(jsonRes(status, { error: { code, message: 'SECRET nvapi-123 /etc/passwd' } }));
    await assert.rejects(() => createHttpApi({ baseUrl: BASE }).sendMessage('x'), (e) => {
      assert.equal(e.code, code);
      assert.match(e.message, re);
      assert.ok(!e.message.includes('SECRET') && !e.message.includes('nvapi'));
      return true;
    });
  }
  fake(jsonRes(500, '<html>trace</html>'));
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getMessages(), (e) => e.code === 'http_error' && !e.message.includes('trace'));
});

test('네트워크 실패는 code=network', async () => {
  globalThis.fetch = async () => { throw new TypeError('boom http://secret'); };
  await assert.rejects(() => createHttpApi({ baseUrl: BASE }).getMessages(), (e) => e.code === 'network' && !e.message.includes('secret'));
});

test('타임아웃: 응답이 없으면 abort 되어 code=timeout (90초 이내)', async () => {
  const { REQUEST_TIMEOUT_MS } = await import('../src/api/http.js');
  assert.ok(REQUEST_TIMEOUT_MS <= 90_000);
  const realSet = globalThis.setTimeout;
  globalThis.setTimeout = (fn, ms, ...a) => realSet(fn, ms === REQUEST_TIMEOUT_MS ? 5 : ms, ...a); // 대기 시간만 단축
  try {
    globalThis.fetch = (url, init) => new Promise((_, reject) => {
      init.signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
    });
    await assert.rejects(() => createHttpApi({ baseUrl: BASE }).sendMessage('x'), (e) => e.code === 'timeout');
  } finally { globalThis.setTimeout = realSet; }
});

test("'chat' 모드: HTTP_METHODS(챗봇+카드·출처·근거)만 http, 나머지는 mock", async () => {
  const mock = createApi({ mode: 'mock', latencyMs: 0 });
  const chat = createApi({ mode: 'chat', baseUrl: BASE, latencyMs: 0 });
  assert.equal(chat.mode, 'chat');
  for (const n of API_METHODS) assert.equal(typeof chat[n], 'function', n);
  const http = createHttpApi({ baseUrl: BASE });
  for (const n of API_METHODS) assert.equal(chat[n].length, mock[n].length, `${n} 인자 개수`);
  const calls = fake(jsonRes(200, []));
  // 목록 밖 메서드는 fetch 를 부르지 않고 mock 데이터를 돌려준다
  assert.ok((await chat.getItinerary()) && (await chat.getAuditLog()) && (await chat.getRoutes()));
  assert.equal(calls.length, 0);
  await chat.getMessages();
  assert.equal(calls.length, 1);
  assert.equal(typeof http.getMessages, 'function');
});

test('resolveApi auto: backend 가 응답하면 chat(기본 주소로 probe)', async () => {
  const calls = fake(jsonRes(200, []));
  const api = await resolveApi({ mode: 'auto' });
  assert.equal(api.mode, 'chat');
  assert.equal(api.baseUrl, DEFAULT_CHAT_BASE);
  assert.equal(calls[0].url, `${DEFAULT_CHAT_BASE}/messages`);
});

test('resolveApi auto: 연결 실패·비정상 응답·배열 아님이면 mock 으로 폴백', async () => {
  fake(() => { throw new TypeError('fetch failed'); });
  assert.equal((await resolveApi({ latencyMs: 0 })).mode, 'mock');
  fake(jsonRes(500, { error: { code: 'x' } }));
  assert.equal((await resolveApi({ latencyMs: 0 })).mode, 'mock');
  fake(jsonRes(200, { not: 'array' }));
  assert.equal((await resolveApi({ latencyMs: 0 })).mode, 'mock');
});

test('resolveApi: 명시 모드는 probe 없이 그대로(chat 강제는 backend 없어도 chat)', async () => {
  const calls = fake(() => { throw new TypeError('fetch failed'); });
  assert.equal((await resolveApi({ mode: 'mock', latencyMs: 0 })).mode, 'mock');
  assert.equal((await resolveApi({ mode: 'chat', baseUrl: BASE })).mode, 'chat');
  assert.equal(calls.length, 0);
});
