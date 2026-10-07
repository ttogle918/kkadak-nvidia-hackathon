// 부팅 스모크: 가짜 DOM 위에서 boot() 가 에러 없이 끝나고 모든 슬롯에 모듈이 렌더되는지 본다.
// (실제 브라우저 렌더·CSS 는 검증하지 않는다 — 수동 확인)
import { test } from 'node:test';
import assert from 'node:assert/strict';

class El {
  constructor(tag, ns) { this.tag = tag; this.ns = ns; this.attrs = {}; this.children = []; this.listeners = {}; this.style = {}; this.dataset = {}; this.nodeType = 1; this.parent = null; }
  setAttribute(k, v) { this.attrs[k] = v; }
  removeAttribute(k) { delete this.attrs[k]; }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  addEventListener(t, fn) { (this.listeners[t] ||= []).push(fn); }
  removeEventListener(t, fn) { this.listeners[t] = (this.listeners[t] || []).filter((f) => f !== fn); }
  replaceChildren(...nodes) { this.children = []; nodes.forEach((n) => this.appendChild(n)); }
  contains(n) { for (let x = n; x; x = x.parent) if (x === this) return true; return false; }
  closest(sel) { for (let x = this; x; x = x.parent) if (x.matches?.(sel)) return x; return null; }
  matches(sel) { const m = /^\[data-([\w-]+)(?:="([^"]*)")?\]$/.exec(sel); return !!m && m[1] in this.dataset && (m[2] == null || this.dataset[m[1]] === m[2]); }
  get text() { return this.children.map((c) => (c.nodeType === 3 ? c.text : c.text)).join(''); }
  find(pred, out = []) { if (pred(this)) out.push(this); this.children.forEach((c) => c.find?.(pred, out)); return out; }
}
const documentElement = new El('html', 'html');
globalThis.document = {
  documentElement,
  getElementById: () => new El('div', 'html'), // 모듈 로드 시 자동 boot() 가 쓰는 더미 루트
  createElement: (t) => new El(t, 'html'),
  createElementNS: (ns, t) => new El(t, ns),
  createTextNode: (s) => ({ nodeType: 3, text: s }),
};
globalThis.location = { search: '' };

test('boot: 슬롯 8개(오른쪽 열 없음)에 모듈이 마운트되고 데이터가 로드된다', async () => {
  const { boot } = await import('../src/main.js');
  const root = new El('div', 'html');
  const app = await boot(root, '?lang=en&mode=now');
  const s = app.ctx.store.getState();
  assert.equal(s.loaded, true);
  assert.equal(s.lang, 'en');
  assert.equal(s.mode, 'now');
  assert.equal(documentElement.lang, 'en');
  const slots = root.find((e) => e.dataset?.slot);
  assert.deepEqual(slots.map((e) => e.dataset.slot).sort(), ['cards', 'chat', 'map', 'rationale', 'securitylog', 'settings', 'timeline', 'topbar']);
  assert.equal(root.find((e) => /col-right/.test(e.attrs?.class ?? '')).length, 0, '오른쪽 열이 없다');
  for (const name of ['chat', 'timeline', 'map', 'cards', 'rationale', 'securitylog', 'settings']) {
    const slot = slots.find((e) => e.dataset.slot === name);
    // 실제 모듈이 무언가를 그렸는지(플레이스홀더든 실제 렌더든)만 본다
    assert.equal(slot.find((e) => e !== slot).length > 0, true, `${name} 렌더`);
  }
  // 상단 바 버튼 -> actions -> store
  const top = slots.find((e) => e.dataset.slot === 'topbar');
  const btn = top.find((e) => e.dataset?.act === 'set-mode' && e.dataset.value === 'old')[0];
  top.find((e) => e.listeners?.click)[0].listeners.click[0]({ target: btn });
  assert.equal(app.ctx.store.getState().mode, 'old');
  // 모바일 탭 -> 시트
  const tab = root.find((e) => e.dataset?.act === 'mtab' && e.dataset.value === 'timeline')[0];
  const nav = root.find((e) => e.attrs?.class === 'mtabs')[0];
  nav.listeners.click[0]({ target: tab });
  assert.deepEqual([app.ctx.store.getState().mobileTab, app.ctx.store.getState().sheetOpen], ['timeline', true]);
  nav.listeners.click[0]({ target: root.find((e) => e.dataset?.act === 'mtab' && e.dataset.value === 'timeline')[0] });
  assert.equal(app.ctx.store.getState().sheetOpen, false);
  // 모바일 탭은 대화·일정 두 개뿐(근거·보안은 카드 안 태그·설정 패널로 옮겼다)
  assert.deepEqual(root.find((e) => e.dataset?.act === 'mtab').map((e) => e.dataset.value), ['chat', 'timeline']);
  // 하단 패널: 기본 단계 + 핸들(separator) 이 cards-zone 안에 있고, ^ 로 펼침 -> store.panelLevel
  assert.equal(s.panelLevel, 'default');
  const zone = root.find((e) => e.attrs?.class === 'cards-zone')[0];
  assert.equal(zone.dataset.level, 'default');
  assert.equal(zone.find((e) => e.attrs?.role === 'separator').length, 1);
  const up = root.find((e) => e.dataset?.act === 'panel-up')[0];
  up.listeners.click[0]();
  assert.equal(app.ctx.store.getState().panelLevel, 'expanded');
  assert.equal(zone.dataset.level, 'expanded');
  // 기어 버튼 -> 설정 패널 열림(data-open) -> 바깥(backdrop) 클릭으로 닫힘
  const layer = root.find((e) => e.attrs?.class === 'settings-layer')[0];
  assert.equal(layer.dataset.open, 'false');
  const gear = root.find((e) => e.dataset?.act === 'open-settings')[0];
  const top2 = root.find((e) => e.dataset?.slot === 'topbar')[0];
  top2.find((e) => e.listeners?.click)[0].listeners.click[0]({ target: gear });
  assert.equal(app.ctx.store.getState().settingsOpen, true);
  assert.equal(layer.dataset.open, 'true');
  assert.equal(layer.find((e) => e.dataset?.slot === 'securitylog').length, 1, '보안 로그는 설정 패널 안');
  const backdrop = root.find((e) => e.dataset?.act === 'settings-backdrop')[0];
  layer.listeners.click[0]({ target: backdrop });
  assert.equal(app.ctx.store.getState().settingsOpen, false);
  assert.equal(layer.dataset.open, 'false');
  app.destroy();
});

test('모듈 mount 가 던져도 슬롯에 에러 박스만 남기고 앱은 계속 뜬다', async () => {
  const { mountSafely } = await import('../src/main.js');
  const slot = new El('section', 'html');
  const origErr = console.error;
  console.error = () => {};
  try {
    const m = mountSafely('map', { mount() { throw new Error('boom'); } }, slot, { t: (k, p) => `${k}:${p?.name}` });
    assert.equal(slot.find((e) => e.attrs?.class === 'module-error').length, 1);
    assert.doesNotThrow(() => m.destroy());
  } finally {
    console.error = origErr;
  }
});
