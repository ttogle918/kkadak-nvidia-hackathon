// 설정 패널(톱바 기어 + layout/settings.js) 테스트: 열기/닫기 · Esc · 포커스 복귀 · 승인 대기 알림 점. 가짜 DOM 위(실제 렌더·CSS 는 수동 확인).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { El, installDom, fire, byAct } from './_cr_fakedom.js';

installDom();
const topbar = await import('../src/components/layout/topbar.js');
const settings = await import('../src/components/layout/settings.js');
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');
const { pendingCount } = await import('../src/state/selectors.js');

async function setup(overrides = {}) {
  const store = createStore(createInitialState(overrides));
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api });
  const t = createT(() => store.getState().lang);
  await actions.loadAll();
  const ctx = { store, api, t, actions };
  const top = new El('section');
  const set = new El('section');
  const a = topbar.mount(top, ctx);
  const b = settings.mount(set, ctx);
  return { store, actions, top, set, destroy: () => { b.destroy(); a.destroy(); } };
}
const gearOf = (top) => byAct(top, 'open-settings');

test('톱바: 기어 버튼만 있고 언어·테마·최소 변경은 옮겨졌다', async () => {
  const { top, set } = await setup();
  assert.ok(gearOf(top));
  assert.equal(top.find((e) => ['set-lang', 'set-theme', 'toggle-min'].includes(e.dataset?.act)).length, 0);
  assert.equal(set.find((e) => ['set-lang', 'set-theme', 'toggle-min'].includes(e.dataset?.act)).length, 2 + 3 + 1);
});

test('기어 클릭 → settingsOpen 토글, 닫기 버튼으로 닫힘', async () => {
  const { store, top, set } = await setup();
  assert.equal(store.getState().settingsOpen, false);
  fire(top, 'click', gearOf(top));
  assert.equal(store.getState().settingsOpen, true);
  assert.equal(gearOf(top).attrs['aria-expanded'], 'true');
  assert.equal(document.activeElement?.dataset?.fk, 'close', '열리면 닫기 버튼으로 포커스');
  fire(set, 'click', byAct(set, 'close-settings'));
  assert.equal(store.getState().settingsOpen, false);
});

test('Esc 로 닫히고 기어 버튼으로 포커스가 돌아온다', async () => {
  const before = (document.listeners.keydown ?? []).length;
  const { store, top, destroy } = await setup();
  assert.equal(document.listeners.keydown.length, before + 1);
  gearOf(top).focus();
  fire(top, 'click', gearOf(top));
  document.listeners.keydown.forEach((fn) => fn({ key: 'Escape', target: top }));
  assert.equal(store.getState().settingsOpen, false);
  assert.equal(document.activeElement?.dataset?.act, 'open-settings');
  destroy();
  assert.equal(document.listeners.keydown.length, before, 'destroy 가 Esc 리스너를 해제');
});

test('설정 안의 토글이 actions 를 부른다(언어·테마·최소 변경)', async () => {
  const { store, set } = await setup();
  fire(set, 'click', byAct(set, 'set-lang', (e) => e.dataset.value === 'en'));
  fire(set, 'click', byAct(set, 'set-theme', (e) => e.dataset.value === 'dark'));
  fire(set, 'click', byAct(set, 'toggle-min'));
  const s = store.getState();
  assert.deepEqual([s.lang, s.theme, s.minimizeChanges], ['en', 'dark', false]);
});

test('승인 대기 로그가 있으면 기어에 알림 점+숫자, aria-label 에 개수', async () => {
  const { store, top } = await setup();
  const n = pendingCount(store.getState().logs);
  assert.ok(n >= 1, '샘플 로그에 승인 대기가 있다');
  const badge = top.find((e) => e.dataset?.role === 'pending')[0];
  assert.equal(badge.text, String(n));
  assert.match(gearOf(top).attrs['aria-label'], new RegExp(`${n}`));
  store.setState({ logs: [] });
  assert.equal(top.find((e) => e.dataset?.role === 'pending').length, 0);
  assert.equal(gearOf(top).attrs['aria-label'], '설정');
});

test('pendingCount: pend 만 센다', () => {
  assert.equal(pendingCount([{ kind: 'pend' }, { kind: 'ok' }, { kind: 'pend' }, { kind: 'approved' }]), 2);
  assert.equal(pendingCount(undefined), 0);
});
