import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire, byAct, byClass, tick } from './_fakedom_ctsl.js';

installFakeDom();
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');
const securitylog = await import('../src/components/securitylog/index.js');

async function setup({ wrap } = {}) {
  const store = createStore(createInitialState());
  const base = createApi({ mode: 'mock', latencyMs: 0 });
  const calls = [];
  const real = base.decideAudit.bind(base);
  const api2 = { ...base, async decideAudit(...args) { calls.push(args); if (wrap) return wrap(...args); return real(...args); } };
  const actions = createActions({ store, api: api2 });
  const ctx = { store, api: api2, t: createT(() => store.getState().lang), actions };
  await actions.loadAll();
  const root = new El('section', 'html');
  const m = securitylog.mount(root, ctx);
  return { store, root, m, calls };
}
const rows = (root) => byClass(root, 'securitylog-row');

test('mount: 4행, 차단 행에만 버튼 2개, 시각·기호+라벨 표시', async () => {
  const { root } = await setup();
  assert.equal(rows(root).length, 4);
  assert.deepEqual(rows(root).map((r) => r.dataset.kind), ['ok', 'ok', 'pend', 'deny']);
  assert.equal(byAct(root, 'decide').length, 2);
  assert.ok(rows(root)[2].find((e) => e.dataset?.act === 'decide').length === 2);
  assert.match(rows(root)[2].text, /09:41:06/);
  assert.match(rows(root)[2].text, /⚠차단됨 · 승인 대기|⚠ ?차단됨/);
  assert.match(rows(root)[3].text, /⊘ ?거부/);
  assert.equal(byClass(root, 'securitylog__list')[0].attrs['aria-live'], 'polite');
  assert.equal(root.scrollTop, root.scrollHeight);
});

test('[승인] 클릭 -> decideAudit(id, "approve") 인자 2개뿐, 상태 갱신, 버튼 제거', async () => {
  const { store, root, calls } = await setup();
  fire(byAct(root, 'decide', 'approve')[0], 'click', { isTrusted: true });
  await tick(); await tick();
  assert.deepEqual(calls, [['log_003', 'approve']]);
  const entry = store.getState().logs.find((l) => l.id === 'log_003');
  assert.equal(entry.kind, 'approved');
  assert.equal(entry.decided_by, 'human:mock'); // 서버(mock)가 채움
  assert.equal(byAct(root, 'decide').length, 0);
  assert.match(rows(root)[2].text, /승인됨/);
  assert.match(rows(root)[2].text, /사람이 승인/);
});

test('[거절] 클릭 -> rejected', async () => {
  const { store, root, calls } = await setup();
  fire(byAct(root, 'decide', 'reject')[0], 'click');
  await tick(); await tick();
  assert.deepEqual(calls, [['log_003', 'reject']]);
  assert.equal(store.getState().logs[2].kind, 'rejected');
});

test('합성 클릭(isTrusted=false)과 알 수 없는 결정값은 무시한다', async () => {
  const { root, calls } = await setup();
  fire(byAct(root, 'decide', 'approve')[0], 'click', { isTrusted: false });
  const bad = byAct(root, 'decide', 'reject')[0];
  bad.dataset.value = 'delete';
  fire(bad, 'click');
  await tick();
  assert.equal(calls.length, 0);
});

test('중복 클릭은 한 번만 보낸다 / 실패하면 오류 문구', async () => {
  const { root, calls, store } = await setup({ wrap: async () => { throw new Error('nope'); } });
  const btn = byAct(root, 'decide', 'approve')[0];
  fire(btn, 'click');
  fire(byAct(root, 'decide', 'approve')[0], 'click');
  await tick(); await tick();
  assert.equal(calls.length, 1);
  assert.equal(byClass(root, 'securitylog-row__error').length, 1);
  assert.equal(store.getState().logs[2].kind, 'pend');
  assert.equal(byAct(root, 'decide').length, 2); // 다시 누를 수 있다
});

test('새 로그가 오면 행이 늘고 스크롤된다 / 접기·펼치기', async () => {
  const { store, root } = await setup();
  root.scrollTop = 0;
  store.setState((s) => ({ logs: [...s.logs, { id: 'log_9', time: '10:00:00', kind: 'ok', text: '추가', decided_by: null }] }));
  assert.equal(rows(root).length, 5);
  assert.equal(root.scrollTop, root.scrollHeight);
  const toggle = byAct(root, 'toggle')[0];
  assert.equal(toggle.attrs['aria-expanded'], 'true');
  fire(toggle, 'click');
  assert.equal(store.getState().securityOpen, false);
  assert.equal(rows(root).length, 0);
  assert.equal(byAct(root, 'toggle')[0].attrs['aria-expanded'], 'false');
});

test('destroy', async () => {
  const { store, root, m } = await setup();
  m.destroy();
  assert.equal(root.children.length, 0);
  store.setState({ logs: [] });
  assert.equal(root.children.length, 0);
});
