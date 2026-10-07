import { test } from 'node:test';
import assert from 'node:assert/strict';
import { esc } from '../src/lib/dom.js';

// 최소 가짜 DOM — h()/on() 의 분기만 검증한다(실제 브라우저 동작은 수동 확인).
class El {
  constructor(tag, ns) { this.tag = tag; this.ns = ns; this.attrs = {}; this.children = []; this.listeners = {}; this.style = {}; this.dataset = {}; this.nodeType = 1; this.parent = null; }
  setAttribute(k, v) { this.attrs[k] = v; }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  addEventListener(t, fn) { (this.listeners[t] ||= []).push(fn); }
  removeEventListener(t, fn) { this.listeners[t] = (this.listeners[t] || []).filter((f) => f !== fn); }
  replaceChildren() { this.children = []; }
  contains(n) { for (let x = n; x; x = x.parent) if (x === this) return true; return false; }
  closest(sel) { for (let x = this; x; x = x.parent) if (x.matches?.(sel)) return x; return null; }
  matches(sel) { const m = /^\[data-(\w+)\]$/.exec(sel); return !!m && m[1] in this.dataset; }
}
globalThis.document = {
  createElement: (t) => new El(t, 'html'),
  createElementNS: (ns, t) => new El(t, ns),
  createTextNode: (s) => ({ nodeType: 3, text: s }),
};
const { h, render, on } = await import('../src/lib/dom.js');

test('esc 는 5개 문자를 이스케이프하고 null 을 빈 문자열로', () => {
  assert.equal(esc('<a href="x">&\'</a>'), '&lt;a href=&quot;x&quot;&gt;&amp;&#39;&lt;/a&gt;');
  assert.equal(esc(null), '');
  assert.equal(esc(0), '0');
});

test('h: 속성·자식·중첩 배열·무시값', () => {
  let clicked = 0;
  const el = h('div', { class: ['a', false, 'b'], id: 'x', hidden: true, off: false, nil: null, dataset: { act: 'go' }, onClick: () => clicked++, style: { color: 'red' } },
    'text', [h('span', null, 1), [null, false, 'deep']]);
  assert.equal(el.attrs.class, 'a b');
  assert.equal(el.attrs.id, 'x');
  assert.equal(el.attrs.hidden, '');
  assert.ok(!('off' in el.attrs) && !('nil' in el.attrs));
  assert.equal(el.dataset.act, 'go');
  assert.equal(el.style.color, 'red');
  el.listeners.click[0]();
  assert.equal(clicked, 1);
  assert.equal(el.children.length, 3); // 'text', span, 'deep'
  assert.equal(el.children[1].children[0].text, '1');
});

test('h: svg 태그는 SVG 네임스페이스로 만든다, 문자열은 텍스트 노드(HTML 해석 안 함)', () => {
  assert.equal(h('path', { d: 'M0 0' }).ns, 'http://www.w3.org/2000/svg');
  assert.equal(h('div').ns, 'html');
  const el = h('p', null, '<img src=x onerror=alert(1)>');
  assert.equal(el.children[0].text, '<img src=x onerror=alert(1)>');
});

test('render 는 자식을 교체한다', () => {
  const root = h('div', null, 'old');
  render(root, h('b'), 'x');
  assert.equal(root.children.length, 2);
});

test('on: 위임 — 일치하는 조상에서 handler 호출, 해제 가능', () => {
  const root = h('div');
  const btn = h('button', { dataset: { act: 'go' } });
  const inner = h('i');
  btn.appendChild(inner);
  root.appendChild(btn);
  const seen = [];
  const off = on(root, 'click', '[data-act]', (_e, el) => seen.push(el.dataset.act));
  root.listeners.click[0]({ target: inner });
  root.listeners.click[0]({ target: root }); // 매칭 없음
  assert.deepEqual(seen, ['go']);
  off();
  assert.equal(root.listeners.click.length, 0);
});
