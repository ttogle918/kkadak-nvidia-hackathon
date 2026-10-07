// cards/rationale 테스트용 가짜 DOM. 브라우저 레이아웃·CSS 는 검증하지 않는다(수동 확인).
export class El {
  constructor(tag) {
    this.tag = tag; this.attrs = {}; this.children = []; this.listeners = {}; this.style = {}; this.dataset = {};
    this.nodeType = 1; this.parent = null; this.focused = false;
  }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k] ?? null; }
  removeAttribute(k) { delete this.attrs[k]; }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  addEventListener(t, fn) { (this.listeners[t] ||= []).push(fn); }
  removeEventListener(t, fn) { this.listeners[t] = (this.listeners[t] || []).filter((f) => f !== fn); }
  replaceChildren(...nodes) { this.children = []; nodes.forEach((n) => this.appendChild(n)); }
  contains(n) { for (let x = n; x; x = x.parent) if (x === this) return true; return false; }
  closest(sel) { for (let x = this; x; x = x.parent) if (x.matches?.(sel)) return x; return null; }
  matches(sel) { const m = /^\[data-([\w-]+)(?:="([^"]*)")?\]$/.exec(sel); return !!m && m[1] in this.dataset && (m[2] == null || this.dataset[m[1]] === m[2]); }
  querySelector(sel) { return this.find((e) => e !== this && e.matches(sel))[0] ?? null; }
  querySelectorAll(sel) { return this.find((e) => e !== this && e.matches(sel)); }
  focus() { globalThis.document.activeElement = this; }
  get text() { return this.children.map((c) => c.text).join(''); }
  find(pred, out = []) { if (pred(this)) out.push(this); this.children.forEach((c) => c.find?.(pred, out)); return out; }
}

export function installDom() {
  const docListeners = {};
  globalThis.document = {
    activeElement: null,
    createElement: (t) => new El(t),
    createElementNS: (ns, t) => new El(t),
    createTextNode: (s) => ({ nodeType: 3, text: s }),
    addEventListener: (t, fn) => { (docListeners[t] ||= []).push(fn); },
    removeEventListener: (t, fn) => { docListeners[t] = (docListeners[t] || []).filter((f) => f !== fn); },
    listeners: docListeners,
  };
  return globalThis.document;
}

/** root 의 click 리스너에 target 을 넘겨 이벤트를 흉내 낸다(on() 위임이 closest 로 data-act 를 찾는다). */
export function fire(root, type, target, extra = {}) {
  for (const fn of [...(root.listeners[type] || [])]) fn({ target, preventDefault() {}, ...extra });
}
export const byAct = (root, act, extra = () => true) => root.find((e) => e.dataset?.act === act && extra(e))[0];
export const textOf = (el) => el.text;
