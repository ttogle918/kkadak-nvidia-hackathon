// map 모듈: 가짜 DOM 위에서 mount/destroy 와 클릭·키보드 -> 상태 전이를 확인한다(실제 렌더·CSS 는 브라우저에서 수동 확인).
import { test } from 'node:test';
import assert from 'node:assert/strict';

class El {
  constructor(tag, ns) { this.tag = tag; this.ns = ns; this.attrs = {}; this.children = []; this.listeners = {}; this.style = {}; this.dataset = {}; this.nodeType = 1; this.parent = null; }
  setAttribute(k, v) { this.attrs[k] = v; }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  addEventListener(t, fn) { (this.listeners[t] ||= []).push(fn); }
  removeEventListener(t, fn) { this.listeners[t] = (this.listeners[t] || []).filter((f) => f !== fn); }
  replaceChildren(...nodes) { this.children = []; nodes.forEach((n) => this.appendChild(n)); }
  contains(n) { for (let x = n; x; x = x.parent) if (x === this) return true; return false; }
  closest(sel) { for (let x = this; x; x = x.parent) if (x.matches?.(sel)) return x; return null; }
  matches(sel) {
    const m = /^\[data-([\w-]+)(?:="([^"]*)")?\]$/.exec(sel);
    if (m) return m[1] in this.dataset && (m[2] == null || this.dataset[m[1]] === m[2]);
    const r = /^\[role="(\w+)"\]\[data-([\w-]+)\]$/.exec(sel);
    return !!r && this.attrs.role === r[1] && r[2] in this.dataset;
  }
  get text() { return this.children.map((c) => c.text).join(''); }
  find(pred, out = []) { if (pred(this)) out.push(this); this.children.forEach((c) => c.find?.(pred, out)); return out; }
}
globalThis.document = {
  createElement: (t) => new El(t, 'html'),
  createElementNS: (ns, t) => new El(t, ns),
  createTextNode: (s) => ({ nodeType: 3, text: s }),
};

const { createStore } = await import('../src/lib/store.js');
const { createApi } = await import('../src/api/index.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createT } = await import('../src/lib/i18n.js');
const map = await import('../src/components/map/index.js');

async function setup(over = {}, load = true, openSteps = true) {
  const store = createStore(createInitialState(over));
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api });
  if (load) await actions.loadAll();
  const t = createT(() => store.getState().lang);
  const root = new El('section', 'html');
  const m = map.mount(root, { store, api, t, actions });
  // 구간 목록은 접힌 채로 시작한다 — 목록을 보는 테스트는 먼저 펼친다
  if (load && openSteps) root.listeners.click[0]({ target: root.find((e) => e.dataset?.act === 'toggle-steps')[0] });
  return { store, actions, root, m };
}
const click = (root, el) => root.listeners.click[0]({ target: el });
const acts = (root, act) => root.find((e) => e.dataset?.act === act);

test('로드 전에는 스켈레톤, 로드 후 지도·경로 카드 3개·구간 목록이 그려진다', async () => {
  const { store, actions, root, m } = await setup({}, false);
  assert.equal(root.find((e) => e.attrs?.class === 'map-skeleton').length, 1);
  await actions.loadAll();
  assert.equal(root.find((e) => e.attrs?.class === 'map-skeleton').length, 0);
  assert.equal(acts(root, 'route').length, 3);
  assert.equal(root.find((e) => e.attrs?.class === 'map-steps__list').length, 0, '목록은 접힌 채로 시작');
  click(root, acts(root, 'toggle-steps')[0]);
  assert.equal(root.find((e) => e.tag === 'svg' && e.attrs.class === 'map-svg').length, 1);
  // 선택 경로 A 의 구간 4개 중 이야기 있는 3개만 지도 구간 버튼 + 목록 버튼
  assert.equal(root.find((e) => e.attrs?.role === 'button' && e.dataset.act === 'seg').length, 3);
  assert.equal(root.find((e) => e.attrs?.class?.startsWith('map-step__item')).length, 4);
  assert.equal(store.getState().selectedRoute, 'A');
  m.destroy();
});

test('지도 구간 클릭 -> selectedSeg, 목록 항목 클릭도 같은 전이, 선택 구간은 aria-pressed', async () => {
  const { store, root, m } = await setup();
  const seg2 = root.find((e) => e.dataset?.act === 'seg' && e.dataset.card === 'card_old_2' && e.attrs.role === 'button')[0];
  click(root, seg2);
  assert.equal(store.getState().selectedSeg, 'card_old_2');
  const sel = root.find((e) => e.attrs?.role === 'button' && e.attrs['aria-pressed'] === 'true' && e.dataset.act === 'seg');
  assert.deepEqual(sel.map((e) => e.dataset.card), ['card_old_2']);
  const step1 = root.find((e) => e.tag === 'button' && e.dataset?.fk === 'step:card_old_1')[0];
  click(root, step1);
  assert.equal(store.getState().selectedSeg, 'card_old_1');
  // 이야기 없는 구간 버튼은 disabled
  const plain = root.find((e) => e.tag === 'button' && e.attrs?.disabled !== undefined);
  assert.equal(plain.length, 1);
  m.destroy();
});

test('경로 카드 클릭 -> selectedRoute, 구간 목록이 그 경로로 바뀐다', async () => {
  const { store, root, m } = await setup();
  click(root, acts(root, 'route').find((e) => e.dataset.id === 'B'));
  assert.equal(store.getState().selectedRoute, 'B');
  assert.equal(root.find((e) => e.attrs?.class?.startsWith('map-step__item')).length, 3);
  const pressed = acts(root, 'route').filter((e) => e.attrs['aria-pressed'] === 'true').map((e) => e.dataset.id);
  assert.deepEqual(pressed, ['B']);
  m.destroy();
});

test('키보드 Enter/Space 로 SVG 구간 선택, 다른 키는 무시', async () => {
  const { store, root, m } = await setup();
  const seg = root.find((e) => e.attrs?.role === 'button' && e.dataset?.card === 'card_old_2')[0];
  const key = (k) => root.listeners.keydown[0]({ target: seg, key: k, preventDefault() {} });
  key('Tab');
  assert.equal(store.getState().selectedSeg, 'card_old_4');
  key('Enter');
  assert.equal(store.getState().selectedSeg, 'card_old_2');
  m.destroy();
});

test('mode=now 이면 옛날 구간 버튼이 없고, 지금 핀은 눌러 selectNow', async () => {
  const { store, root, m } = await setup({ mode: 'now' });
  assert.equal(root.find((e) => e.attrs?.role === 'button' && e.dataset?.act === 'seg').length, 0);
  const pin = root.find((e) => e.attrs?.role === 'button' && e.dataset?.act === 'now' && e.dataset.card === 'card_now_2')[0];
  click(root, pin);
  assert.equal(store.getState().selectedNow, 'card_now_2');
  store.setState({ mode: 'old' });
  assert.equal(root.find((e) => e.attrs?.role === 'button' && e.dataset?.act === 'now').length, 0);
  m.destroy();
});

test('언어 전환·day 변경으로 다시 그려지고, 문자열은 텍스트 노드로만 들어간다', async () => {
  const { store, root, m } = await setup();
  assert.match(root.text, /왕이 지나던 길/);
  store.setState({ lang: 'en' });
  assert.match(root.text, /King's Passage/);
  store.setState({ day: 2 });
  assert.equal(root.find((e) => e.tag === 'svg' && e.attrs.class === 'map-svg')[0].dataset.day, '2');
  const dayGroup = root.find((e) => e.attrs?.class === 'map-day')[0];
  assert.equal(dayGroup.attrs.opacity, '0.12');
  m.destroy();
});

test('목록 토글은 열고 닫을 수 있고, destroy 는 구독·리스너를 해제하고 비운다', async () => {
  const { store, root, m } = await setup({}, true, false);
  assert.equal(root.find((e) => e.attrs?.class === 'map-steps__list').length, 0, '기본은 접힘');
  assert.equal(acts(root, 'toggle-steps')[0].attrs['aria-expanded'], 'false');
  click(root, acts(root, 'toggle-steps')[0]);
  assert.equal(root.find((e) => e.attrs?.class === 'map-steps__list').length, 1);
  click(root, acts(root, 'toggle-steps')[0]);
  assert.equal(root.find((e) => e.attrs?.class === 'map-steps__list').length, 0);
  m.destroy();
  assert.equal(root.children.length, 0);
  assert.equal(root.listeners.click.length, 0);
  assert.doesNotThrow(() => store.setState({ day: 3 }));
  assert.equal(root.children.length, 0); // destroy 뒤 재렌더 없음
});
