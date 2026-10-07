import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { installFakeDom, El, fire, byClass, tick } from './_fakedom_ctsl.js';

installFakeDom();
globalThis.fetch = async () => { throw new TypeError('offline'); };
const { boot: bootEvents } = await import('../src/events/main.js');
const { boot: bootAdmin, createAdmin, mountAdmin } = await import('../src/events/admin.js');
const { createStore } = await import('../src/lib/store.js');
const { createController, initialState } = await import('../src/events/controller.js');
const { createMockEventsApi } = await import('../src/events/api.js');
const { mountEvents } = await import('../src/events/view.js');

test('?base= 로 받은 외부 주소는 쓰지 않는다(events·admin 둘 다)', async () => {
  const root = () => new El('div', 'html');
  const e = await bootEvents(root(), '?api=http&base=https://evil.example/api');
  assert.doesNotMatch(e.api.baseUrl, /evil/);
  const a = await bootAdmin(root(), '?base=https://evil.example/api');
  assert.doesNotMatch(a.api.baseUrl, /evil/);
  const ok = await bootEvents(root(), '?api=http&base=http://127.0.0.1:8000/api');
  assert.equal(ok.api.baseUrl, 'http://127.0.0.1:8000/api');
  const other = await bootEvents(root(), '?api=http&base=http://127.0.0.1:9999/api');
  assert.doesNotMatch(other.api.baseUrl, /9999/);
});

test('두 페이지 모두 CSP 가 있고 외부 연결·스크립트를 허용하지 않는다', () => {
  for (const f of ['events.html', 'admin.html']) {
    const html = readFileSync(new URL(`../${f}`, import.meta.url), 'utf8');
    const csp = /Content-Security-Policy"\s+content="([^"]+)"/.exec(html)?.[1];
    assert.ok(csp, f);
    assert.match(csp, /default-src 'none'/);
    assert.match(csp, /script-src 'self'/);
    assert.match(csp, /connect-src 'self' http:\/\/localhost:\* http:\/\/127\.0\.0\.1:\*/);
    assert.doesNotMatch(csp, /unsafe-inline|unsafe-eval|https:\/\/\*/);
    assert.doesNotMatch(csp, /(?:^|\s)\*(?:\s|;|$)/); // 출처 자리에 와일드카드 단독 사용 금지(포트 와일드카드는 루프백 한정)
    assert.doesNotMatch(html, /<script(?![^>]*src=)[^>]*>[^<]/); // 인라인 스크립트 없음
  }
});

test('관리자 메모가 승인 요청에 실린다', async () => {
  const calls = [];
  const api = { demo: false, admin: {
    review: async () => ({ new_or_changed: [], conflicts: [], missing_info: [], eligibility_check: [], collection_errors: [], stale_sources: [], reports_pending: [], manual_links: [] }),
    sources: async () => ({ sources: [], runs: {}, link_checks: {} }),
    reports: async () => ({ reports: [{ id: 'rpt_1', kind: 'other', status: 'pending', official_link: 'https://a.invalid/x', reason: '사유입니다 충분', fields: {}, submitted_at: 'x' }] }),
    decide: async (...a) => { calls.push(a); return {}; },
  } };
  const admin = createAdmin({ api });
  const root = new El('div', 'html');
  mountAdmin(root, { admin, api });
  admin.setToken('tok');
  await admin.load();
  const note = root.find((e) => e.dataset?.note === 'rpt_1')[0];
  note.value = '공식 링크 확인함';
  fire(root.find((e) => e.dataset?.act === 'approve')[0], 'click');
  await tick(); await tick();
  assert.deepEqual(calls[0], ['tok', 'rpt_1', 'approve', '공식 링크 확인함']);
});

const mem = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) }; };
function mountDemo(api = createMockEventsApi()) {
  const storage = mem();
  const store = createStore(initialState(storage, { today: '2026-10-16', demo: api.demo }));
  const controller = createController({ store, api, storage });
  const root = new El('div', 'html');
  mountEvents(root, { store, api, controller });
  return { store, controller, root };
}

test('데모 행사는 공식 출처로 확인됨 배지를 달지 않는다', async () => {
  const x = mountDemo();
  x.controller.setForm({ from: '2026-10-16', to: '2026-10-19' });
  await x.controller.search();
  assert.doesNotMatch(x.root.text, /공식 출처로 확인됨/);
  assert.match(x.root.text, /\(데모\)/);
});

test('오래된 마지막 확인은 취소가 아니라는 표시와 함께 보인다', async () => {
  const api = createMockEventsApi();
  const orig = api.search;
  api.search = async (b) => { const r = await orig(b); r.events[0].stale = true; return r; };
  const x = mountDemo(api);
  x.controller.setForm({ from: '2026-10-16', to: '2026-10-19' });
  await x.controller.search();
  assert.match(x.root.text, /마지막 확인이 오래됨/);
  assert.match(x.root.text, /취소는 아님/);
});

test('지도의 행사 점은 키보드(Enter·Space)로 열 수 있다', async () => {
  const x = mountDemo();
  x.controller.setForm({ from: '2026-10-16', to: '2026-10-19' });
  await x.controller.search();
  const pt = x.root.find((e) => e.dataset?.act === 'detail' && (e.attrs?.class ?? '').includes('ev-pt'))[0];
  assert.equal(pt.attrs.tabindex, '0');
  fire(pt, 'keydown', { key: 'Tab' });
  assert.equal(x.store.getState().selectedId, null);
  fire(pt, 'keydown', { key: 'Enter' });
  await tick();
  assert.ok(x.store.getState().selectedId);
});

test('합성 이야기는 데모 표시와 함께 나온다', async () => {
  const api = createMockEventsApi();
  api.detail = async (id) => ({ ...(await createMockEventsApi().detail(id)), stories: [{ id: 's', title: '○○ 길', synthetic: true, facts: [{ kind: 'fact', text: '합성 사실', sources: [{ tier: 'A', name: 'x', locator: 'y' }] }], lore: [], inference: [], experience: { text: '걸어 본다' }, record_prompt: { text: '남긴다' } }] });
  const x = mountDemo(api);
  x.controller.setForm({ from: '2026-10-16', to: '2026-10-19' });
  await x.controller.search();
  await x.controller.openDetail('demo:1');
  const stories = byClass(x.root, 'ev-stories')[0];
  assert.match(stories.text, /데모/);
  assert.match(stories.text, /서비스 제안/);
});

test('?base= 를 바꾼 관리자 화면은 저장된 토큰을 자동으로 보내지 않는다', async () => {
  const calls = [];
  globalThis.sessionStorage = { getItem: (k) => (k === 'kc.admin.token' ? JSON.stringify('saved-token') : null), setItem() {}, removeItem() {} };
  globalThis.fetch = async (url, init) => { calls.push([url, init?.headers?.['X-Admin-Token']]); throw new TypeError('offline'); };
  await bootAdmin(new El('div', 'html'), '?base=http://127.0.0.1:8000/api');
  assert.equal(calls.length, 0);
  await bootAdmin(new El('div', 'html'), '');
  await tick();
  assert.ok(calls.length >= 1 && calls.every((c) => c[1] === 'saved-token'));
  delete globalThis.sessionStorage;
});

test('index 화면도 ?base= 를 검증한다', () => {
  const src = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  assert.match(src, /safeBase\(q\.get\('base'\)\)/);
  assert.doesNotMatch(src, /[^(]q\.get\('base'\) \|\|/);
});
