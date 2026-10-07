// chat·timeline·securitylog 테스트가 같이 쓰는 가짜 DOM(파일명 앞 _ 는 node --test 가 테스트로 실행하지 않게 하려는 것).
// 브라우저 레이아웃·CSS 는 검증하지 않는다 — h()/on() 이 쓰는 최소 표면과 이벤트 버블링만 흉내 낸다.
export class El {
  constructor(tag, ns) {
    this.tag = tag; this.ns = ns; this.attrs = {}; this.children = []; this.listeners = {}; this.style = {};
    this.dataset = {}; this.nodeType = 1; this.parent = null; this.scrollTop = 0; this.scrollHeight = 1000; this.disabled = false; this.value = '';
  }
  setAttribute(k, v) { this.attrs[k] = v; if (k === 'disabled') this.disabled = true; if (k === 'value') this.value = v; }
  removeAttribute(k) { delete this.attrs[k]; }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  addEventListener(t, fn) { (this.listeners[t] ||= []).push(fn); }
  removeEventListener(t, fn) { this.listeners[t] = (this.listeners[t] || []).filter((f) => f !== fn); }
  replaceChildren(...nodes) { this.children = []; nodes.forEach((n) => this.appendChild(n)); }
  contains(n) { for (let x = n; x; x = x.parent) if (x === this) return true; return false; }
  closest(sel) { for (let x = this; x; x = x.parent) if (x.matches?.(sel)) return x; return null; }
  matches(sel) {
    const m = /^\[data-([\w-]+)(?:="([^"]*)")?\]$/.exec(sel);
    return !!m && m[1] in this.dataset && (m[2] == null || this.dataset[m[1]] === m[2]);
  }
  focus() { globalThis.document.activeElement = this; }
  get text() { return this.children.map((c) => c.text ?? '').join(''); }
  find(pred, out = []) { if (pred(this)) out.push(this); this.children.forEach((c) => c.find?.(pred, out)); return out; }
  querySelectorAll(sel) { return this.find((e) => e.matches(sel)); }
  get cls() { return this.attrs.class ?? ''; }
}

export function installFakeDom() {
  globalThis.document = {
    activeElement: null,
    documentElement: new El('html', 'html'),
    getElementById: () => new El('div', 'html'),
    createElement: (t) => new El(t, 'html'),
    createElementNS: (ns, t) => new El(t, ns),
    createTextNode: (s) => ({ nodeType: 3, text: String(s) }),
  };
  globalThis.location = { search: '' };
}

/** el 에서 시작해 부모로 버블링하며 type 리스너를 부른다. */
export function fire(el, type, ev = {}) {
  const e = { type, target: el, preventDefault() { this.defaultPrevented = true; }, ...ev };
  for (let x = el; x; x = x.parent) for (const fn of [...(x.listeners?.[type] ?? [])]) fn(e);
  return e;
}
export const byAct = (root, act, value) => root.find((e) => e.dataset?.act === act && (value == null || e.dataset.value === value || e.dataset.id === value));
export const byClass = (root, cls) => root.find((e) => (e.attrs?.class ?? '').split(' ').includes(cls));
export const tick = () => new Promise((r) => setTimeout(r, 0));
