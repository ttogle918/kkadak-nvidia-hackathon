import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { configuredBase, readSession, writeSession, SESSION_KEY } from '../src/lib/api-base.js';
import { createHttpApi, errorText, parseRetryAfter } from '../src/api/http.js';
import { resolveApi, DEFAULT_CHAT_BASE } from '../src/api/index.js';
import { defaultBase, createHttpEventsApi } from '../src/events/api.js';
import { approveButtons } from '../src/components/securitylog/approve-buttons.js';
import { createT } from '../src/lib/i18n.js';
import { installFakeDom } from './_fakedom_ctsl.js';

installFakeDom();

const TOK = 'A'.repeat(43);
const TOK2 = 'B'.repeat(43);

function memStorage(initial = {}) {
  const m = new Map(Object.entries(initial));
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), m };
}
function withStorage(st, fn) {
  const had = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage');
  Object.defineProperty(globalThis, 'sessionStorage', { value: st, configurable: true, writable: true });
  const restore = () => { if (had) Object.defineProperty(globalThis, 'sessionStorage', had); else delete globalThis.sessionStorage; };
  return Promise.resolve(fn()).finally(restore);
}
const jres = (status, body, headers = {}) => ({ ok: status < 400, status, headers: { get: (k) => headers[k] ?? null }, json: async () => body });
async function withFetch(impl, fn) {
  const saved = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init = {}) => { calls.push({ url, init }); return impl(url, init, calls); };
  try { return await fn(calls); } finally { globalThis.fetch = saved; }
}
const REPLY = { reply: { role: 'assistant', text: 'ok' }, logs: [] };

test('configuredBase: 허용·거부표', () => {
  const ok = [['/api', '/api'], ['/api/', '/api'], ['https://x.example/api', 'https://x.example/api'], ['https://x.example/api/', 'https://x.example/api'], ['https://x.example', 'https://x.example']];
  for (const [i, o] of ok) assert.equal(configuredBase({ KC_API_BASE: i }), o, i);
  const bad = ['http://x.example/api', '//evil.example/api', 'javascript:alert(1)', 'https://u:p@x.example/api', 'https://x.example/api?a=1', 'https://x.example/api#h', 'ftp://x/a', '', 'api', '/a b', 5, null, undefined, {}];
  for (const b of bad) assert.equal(configuredBase({ KC_API_BASE: b }), undefined, String(b));
  assert.equal(configuredBase({}), undefined);
});

test('세션 저장소: 읽기·쓰기 실패해도 throw 하지 않고, 형식이 틀리면 없음', async () => {
  await withStorage(memStorage({ [SESSION_KEY]: 'short' }), () => assert.equal(readSession(), null));
  await withStorage(memStorage({ [SESSION_KEY]: TOK }), () => assert.equal(readSession(), TOK));
  const boom = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() { throw new Error('denied'); } };
  await withStorage(boom, () => { assert.equal(readSession(), null); writeSession(TOK); writeSession(null); });
});

test('토큰이 없으면 헤더 없이 보내고, 401 no_session 이면 발급·저장 후 재시도, 이후 요청은 재사용한다', async () => {
  const st = memStorage();
  await withStorage(st, () => withFetch(async (url, init) => {
    if (url.endsWith('/session')) return jres(201, { session: TOK, ttl_s: 7200 });
    return init.headers?.['X-KC-Session'] === TOK ? jres(200, REPLY) : jres(401, { error: { code: 'no_session' } });
  }, async (calls) => {
    const api = createHttpApi({ baseUrl: 'https://b.example/api' });
    await api.sendMessage('안녕');
    await api.sendMessage('또');
    assert.deepEqual(calls.map((c) => `${c.init.method ?? 'GET'} ${c.url}`), ['POST https://b.example/api/messages', 'POST https://b.example/api/session', 'POST https://b.example/api/messages', 'POST https://b.example/api/messages']);
    assert.equal(calls[0].init.headers['X-KC-Session'], undefined);
    assert.equal(calls[2].init.headers['X-KC-Session'], TOK);
    assert.equal(calls[3].init.headers['X-KC-Session'], TOK);
    assert.equal(st.getItem(SESSION_KEY), TOK);
  }));
});

test('로컬 모드(401 없음): 발급 요청 없이 한 번만 보낸다', async () => {
  await withStorage(memStorage(), () => withFetch(async () => jres(200, REPLY), async (calls) => {
    await createHttpApi({ baseUrl: '/api' }).sendMessage('a');
    assert.equal(calls.length, 1);
  }));
});

test('저장된 토큰이 있으면 발급하지 않고, GET 에도 헤더를 싣는다', async () => {
  await withStorage(memStorage({ [SESSION_KEY]: TOK }), () => withFetch(async () => jres(200, []), async (calls) => {
    const api = createHttpApi({ baseUrl: '/api' });
    await api.getMessages();
    await api.getAuditLog();
    assert.equal(calls.length, 2);
    for (const c of calls) assert.equal(c.init.headers['X-KC-Session'], TOK);
  }));
});

test('저장소가 막혀도 동작한다(메모리 토큰으로 계속)', async () => {
  const boom = { getItem() { throw new Error('x'); }, setItem() { throw new Error('x'); }, removeItem() { throw new Error('x'); } };
  await withStorage(boom, () => withFetch(async (url, init) => {
    if (url.endsWith('/session')) return jres(201, { session: TOK });
    return init.headers?.['X-KC-Session'] === TOK ? jres(200, REPLY) : jres(401, { error: { code: 'no_session' } });
  }, async (calls) => {
    const api = createHttpApi({ baseUrl: '/api' });
    const r = await api.sendMessage('a');
    await api.sendMessage('b');
    assert.equal(r.reply.text, 'ok');
    assert.equal(calls.filter((c) => c.url.endsWith('/session')).length, 1);
    assert.equal(calls[3].init.headers['X-KC-Session'], TOK);
  }));
});

test('발급 실패(구 backend 404 등)여도 헤더 없이 보낸다', async () => {
  await withStorage(memStorage(), () => withFetch(async (url) => (url.endsWith('/session') ? jres(404, { error: { code: 'not_found' } }) : jres(401, { error: { code: 'no_session' } })), async (calls) => {
    const api = createHttpApi({ baseUrl: '/api' });
    await assert.rejects(api.sendMessage('a'), (e) => e.code === 'no_session');
    assert.equal(calls.filter((c) => c.url.endsWith('/messages')).length, 2);
    assert.equal(calls[2].init.headers['X-KC-Session'], undefined);
  }));
});

test('401 no_session 이면 토큰을 버리고 새로 받아 한 번만 재시도한다', async () => {
  const st = memStorage({ [SESSION_KEY]: TOK });
  await withStorage(st, () => withFetch(async (url, init) => {
    if (url.endsWith('/session')) return jres(201, { session: TOK2 });
    return init.headers['X-KC-Session'] === TOK ? jres(401, { error: { code: 'no_session', message: '서버 원문' } }) : jres(200, REPLY);
  }, async (calls) => {
    const api = createHttpApi({ baseUrl: '/api' });
    const r = await api.sendMessage('a');
    assert.equal(r.reply.text, 'ok');
    assert.deepEqual(calls.map((c) => c.url), ['/api/messages', '/api/session', '/api/messages']);
    assert.equal(st.getItem(SESSION_KEY), TOK2);
  }));
  // 재시도도 401 이면 한 번만 더 시도하고 오류
  await withStorage(memStorage({ [SESSION_KEY]: TOK }), () => withFetch(async (url) => (url.endsWith('/session') ? jres(201, { session: TOK2 }) : jres(401, { error: { code: 'no_session' } })), async (calls) => {
    const api = createHttpApi({ baseUrl: '/api' });
    await assert.rejects(api.sendMessage('a'), (e) => e.code === 'no_session' && e.i18nKey === 'error.no_session');
    assert.equal(calls.filter((c) => c.url.endsWith('/messages')).length, 2);
  }));
});

test('429·503·403 은 고정 문구이고 서버 message 는 쓰지 않는다. Retry-After 반영', async () => {
  const t = createT(() => 'ko');
  const cases = [
    [429, 'rate_limited', { 'Retry-After': '12' }, 12],
    [503, 'daily_limit', {}, null],
    [403, 'disabled_in_public', {}, null],
    [429, 'busy', {}, null],
  ];
  for (const [status, code, headers, wait] of cases) {
    await withStorage(memStorage({ [SESSION_KEY]: TOK }), () => withFetch(async () => jres(status, { error: { code, message: 'INTERNAL <b>secret</b>' } }, headers), async () => {
      const api = createHttpApi({ baseUrl: '/api' });
      await assert.rejects(api.sendMessage('a'), (e) => {
        assert.equal(e.code, code);
        assert.equal(e.status, status);
        assert.doesNotMatch(e.message, /INTERNAL|secret/);
        assert.equal(e.retryAfterS ?? null, wait);
        const txt = errorText(e, t);
        assert.doesNotMatch(txt, /INTERNAL|secret/);
        if (wait) assert.match(txt, /12초/);
        return true;
      });
    }));
  }
  assert.equal(parseRetryAfter('abc'), null);
  assert.equal(parseRetryAfter('99999'), 3600);
  assert.equal(parseRetryAfter('0'), 1);
  assert.equal(parseRetryAfter(null), null);
});

test('getMeta: kc-meta/v1 만 받는다', async () => {
  await withStorage(memStorage(), async () => {
    await withFetch(async () => jres(200, { schema: 'kc-meta/v1', public: true, decisions: 'closed', reports: 'closed' }), async () => {
      assert.deepEqual(await createHttpApi({ baseUrl: '/api' }).getMeta(), { public: true, decisions: 'closed', reports: 'closed' });
    });
    await withFetch(async () => jres(200, { schema: 'x' }), async () => {
      await assert.rejects(createHttpApi({ baseUrl: '/api' }).getMeta(), (e) => e.code === 'bad_response');
    });
  });
});

test('배포 주소: resolveApi 와 행사 기본 주소가 configuredBase 를 우선한다. ?base= 규칙은 불변', async () => {
  globalThis.KC_API_BASE = 'https://api.example/api';
  try {
    const api = await resolveApi({ mode: 'chat' });
    assert.equal(api.baseUrl, 'https://api.example/api');
    assert.equal(defaultBase({ port: '8766', hostname: 'localhost', protocol: 'http:' }), 'https://api.example/api');
    assert.equal(createHttpEventsApi({}).baseUrl, 'https://api.example/api');
  } finally {
    delete globalThis.KC_API_BASE;
  }
  assert.equal((await resolveApi({ mode: 'chat' })).baseUrl, DEFAULT_CHAT_BASE);
  assert.equal(defaultBase({ port: '8766', hostname: 'localhost', protocol: 'http:' }), 'http://localhost:8000/api');
  assert.equal(defaultBase({ port: '443', hostname: 'x.example', protocol: 'https:' }), '/api');
});

test('mock 모드와 auto(backend 없음)는 네트워크 없이 mock 으로, 세션을 발급하지 않는다', async () => {
  await withStorage(memStorage(), () => withFetch(async () => { throw new TypeError('offline'); }, async (calls) => {
    const m = await resolveApi({ mode: 'mock', latencyMs: 0 });
    assert.equal(m.mode, 'mock');
    const a = await resolveApi({ mode: 'auto', latencyMs: 0, probeMs: 50 });
    assert.equal(a.mode, 'mock');
    assert.ok(calls.every((c) => !c.url.endsWith('/session')));
    assert.equal(calls.length, 1); // probe 한 번뿐
    assert.equal(calls[0].init.headers, undefined); // probe 는 세션 헤더 없이
  }));
});

test('행사 API: 저장된 세션이 있으면 헤더로 보내고, 제한 오류는 서버 message 를 쓰지 않는다', async () => {
  await withStorage(memStorage({ [SESSION_KEY]: TOK }), async () => {
    const seen = [];
    const impl = async (url, init) => { seen.push(init.headers); return jres(429, { error: { code: 'rate_limited', message: 'LEAK' } }, { 'Retry-After': '7' }); };
    const api = createHttpEventsApi({ baseUrl: '/api', fetchImpl: impl });
    await assert.rejects(api.coverage(), (e) => e.code === 'rate_limited' && e.status === 429 && e.retryAfterS === 7 && !/LEAK/.test(e.message));
    assert.equal(seen[0]['X-KC-Session'], TOK);
  });
  await withStorage(memStorage(), async () => {
    const seen = [];
    const api = createHttpEventsApi({ baseUrl: '/api', fetchImpl: async (u, init) => { seen.push(init.headers); return jres(200, { coverage: {} }); } });
    await api.coverage();
    assert.equal(seen[0]['X-KC-Session'], undefined);
  });
});

test('승인 닫힘: 버튼 대신 안내 문구(textContent), 열림이면 기존 버튼', () => {
  const t = createT(() => 'ko');
  const closed = approveButtons({ entry: { id: 'e1' }, label: 'x', busy: false, t, closed: true });
  assert.equal(closed.tagName?.toLowerCase?.() ?? closed.tag, 'p');
  const flat = JSON.stringify(closed, (k, v) => (k === 'parent' || k === 'ownerDocument' ? undefined : v));
  assert.match(flat, /공개 데모에서는 승인과 거절을 할 수 없어요/);
  assert.doesNotMatch(flat, /securitylog-btn/);
  const open = approveButtons({ entry: { id: 'e1' }, label: 'x', busy: false, t });
  assert.match(JSON.stringify(open, (k, v) => (k === 'parent' ? undefined : v)), /securitylog-btn--approve/);
});

test('두 HTML: config.local.js 가 모듈 스크립트보다 앞이고 CSP 는 로컬 그대로', () => {
  for (const f of ['events.html', 'admin.html', 'index.html']) {
    const html = readFileSync(new URL(`../${f}`, import.meta.url), 'utf8');
    const cfg = html.indexOf('<script src="config.local.js"></script>');
    const mod = html.indexOf('<script type="module"');
    assert.ok(cfg > 0 && mod > cfg, f);
  }
  for (const f of ['events.html', 'admin.html']) {
    const html = readFileSync(new URL(`../${f}`, import.meta.url), 'utf8');
    assert.match(html, /connect-src 'self' http:\/\/localhost:\* http:\/\/127\.0\.0\.1:\*;/);
  }
});

test('i18n 새 키가 ko/en 에 모두 있다', () => {
  const k = ['error.rate_limited', 'error.rate_limited_wait', 'error.busy', 'error.daily_limit', 'error.disabled_in_public', 'error.no_session', 'log.decision_closed'];
  const tk = createT(() => 'ko'); const te = createT(() => 'en');
  for (const key of k) { assert.notEqual(tk(key), key); assert.notEqual(te(key), key); }
  assert.match(te('error.rate_limited_wait', { s: 5 }), /5 seconds/);
});
