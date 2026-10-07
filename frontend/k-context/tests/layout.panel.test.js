// 하단 패널 핸들(app-shell): ^/v 버튼 · 키보드 · pointer 드래그 · aria. 가짜 DOM 위(실제 높이·CSS 는 수동 확인).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { El, installDom } from './_cr_fakedom.js';

installDom();
const { mountAppShell } = await import('../src/components/layout/app-shell.js');
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createT } = await import('../src/lib/i18n.js');

function setup(overrides = {}) {
  const store = createStore(createInitialState(overrides));
  const actions = createActions({ store, api: {} });
  const t = createT(() => store.getState().lang);
  const root = new El('div');
  const shell = mountAppShell(root, { store, t, actions });
  const act = (a) => root.find((e) => e.dataset?.act === a)[0];
  const zone = root.find((e) => (e.attrs?.class ?? '') === 'cards-zone')[0];
  const main = root.find((e) => e.tag === 'main')[0];
  main.clientHeight = 900;
  return { store, shell, root, zone, grip: act('panel-grip'), up: act('panel-up'), down: act('panel-down') };
}
const press = (el, key) => { const e = { key, preventDefault() { this.prevented = true; } }; el.listeners.keydown.forEach((f) => f(e)); return e; };
const ptr = (el, type, y, extra = {}) => el.listeners[type]?.forEach((f) => f({ clientY: y, button: 0, pointerId: 1, ...extra }));

test('기본 단계 default: 핸들은 zone 안 첫 자식, aria 속성이 맞다', () => {
  const { zone, grip, up, down } = setup();
  assert.equal(zone.dataset.level, 'default');
  assert.equal(zone.children[0].attrs.class, 'panel-handle');
  assert.equal(grip.attrs.role, 'separator');
  assert.equal(grip.attrs['aria-orientation'], 'horizontal');
  assert.equal(grip.attrs.tabindex, '0');
  assert.deepEqual([grip.attrs['aria-valuenow'], grip.attrs['aria-valuemin'], grip.attrs['aria-valuemax']], ['33', '5', '70']);
  assert.equal(grip.attrs['aria-valuetext'], '기본');
  assert.match(up.attrs['aria-label'], /펼치기/);
  assert.match(down.attrs['aria-label'], /줄이기/);
  assert.equal(up.attrs['aria-expanded'], 'false');
  assert.equal(down.attrs['aria-expanded'], 'true');
});

test('^ / v 버튼: 한 단계씩, 접힘에서 ^ 로 펼치기, 끝에서는 비활성', () => {
  const { store, zone, up, down } = setup();
  down.listeners.click[0]();
  assert.equal(store.getState().panelLevel, 'collapsed');
  assert.equal(zone.dataset.level, 'collapsed');
  assert.equal(down.disabled, true);
  assert.equal(down.attrs.disabled, '');
  assert.equal(down.attrs['aria-expanded'], 'false');
  up.listeners.click[0]();
  assert.equal(store.getState().panelLevel, 'default');
  assert.equal(down.attrs.disabled, undefined);
  up.listeners.click[0]();
  assert.equal(zone.dataset.level, 'expanded');
  assert.equal(up.attrs['aria-expanded'], 'true');
  assert.equal(up.disabled, true);
});

test('키보드: 위/아래 화살표는 단계 이동, Enter·Space 는 접힘<->기본', () => {
  const { store, grip } = setup();
  const e = press(grip, 'ArrowUp');
  assert.equal(e.prevented, true);
  assert.equal(store.getState().panelLevel, 'expanded');
  assert.equal(grip.attrs['aria-valuenow'], '70');
  press(grip, 'ArrowDown'); press(grip, 'ArrowDown');
  assert.equal(store.getState().panelLevel, 'collapsed');
  assert.equal(grip.attrs['aria-valuenow'], '5');
  press(grip, 'Enter');
  assert.equal(store.getState().panelLevel, 'default');
  press(grip, ' ');
  assert.equal(store.getState().panelLevel, 'collapsed');
  press(grip, 'a');
  assert.equal(store.getState().panelLevel, 'collapsed');
});

test('드래그: 임시 높이는 인라인 style, 놓으면 가장 가까운 단계로 스냅하고 style 은 비운다', () => {
  const { store, zone, grip } = setup();
  zone.getBoundingClientRect = () => ({ height: 300 });
  ptr(grip, 'pointerdown', 600);
  assert.equal(zone.dataset.dragging, 'true');
  ptr(grip, 'pointermove', 400); // 200px 위로 -> 500px
  assert.equal(zone.style.height, '500px');
  ptr(grip, 'pointerup', 400);
  assert.equal(store.getState().panelLevel, 'expanded'); // 500 은 300 보다 630 에 가깝다
  assert.equal(zone.style.height, '');
  assert.equal(zone.dataset.dragging, undefined);
});

test('드래그: 아래로 끌어 접힘, 범위 밖은 잘림, 취소하면 단계 그대로', () => {
  const { store, zone, grip } = setup();
  zone.getBoundingClientRect = () => ({ height: 300 });
  ptr(grip, 'pointerdown', 300); ptr(grip, 'pointermove', 900);
  assert.equal(zone.style.height, '48px');
  ptr(grip, 'pointerup', 900);
  assert.equal(store.getState().panelLevel, 'collapsed');
  ptr(grip, 'pointerdown', 300); ptr(grip, 'pointermove', -2000);
  assert.equal(zone.style.height, '630px');
  ptr(grip, 'pointercancel', 0);
  assert.equal(store.getState().panelLevel, 'collapsed');
  assert.equal(zone.style.height, '');
});

test('탭(거의 안 움직임)은 단계를 바꾸지 않고, move 는 드래그 중이 아니면 무시, 보조 버튼은 시작 안 함', () => {
  const { store, zone, grip } = setup();
  zone.getBoundingClientRect = () => ({ height: 300 });
  ptr(grip, 'pointermove', 100);
  assert.equal(zone.style.height ?? '', '');
  ptr(grip, 'pointerdown', 300); ptr(grip, 'pointerup', 301);
  assert.equal(store.getState().panelLevel, 'default');
  ptr(grip, 'pointerdown', 300, { button: 2 });
  assert.equal(zone.dataset.dragging, undefined);
});

test('접힘 상태에서 선택 카드가 바뀌어도 자동으로 펼치지 않고, 접힘 제목·언어가 갱신된다', () => {
  const { store, zone, grip } = setup({ panelLevel: 'collapsed' });
  assert.equal(zone.dataset.level, 'collapsed');
  assert.equal(grip.text, '카드');
  store.setState({ selectedNow: 'card_now_2' });
  assert.equal(store.getState().panelLevel, 'collapsed');
  store.setState({ lang: 'en' });
  assert.equal(grip.attrs['aria-valuetext'], 'Collapsed');
  assert.match(grip.attrs['aria-label'], /Resize/);
});

test('destroy: 핸들 리스너·구독 해제', () => {
  const { store, shell, grip, up } = setup();
  shell.destroy();
  assert.equal(grip.listeners.keydown.length, 0);
  assert.equal(up.listeners.click.length, 0);
  assert.doesNotThrow(() => store.setState({ panelLevel: 'expanded' }));
});
