// DOM 헬퍼. 프레임워크 없이 h() 로 노드를 만들고 on() 으로 이벤트를 위임한다.
// import 시점에는 document 를 만지지 않는다(node 테스트에서 import 가능).

const SVG_NS = 'http://www.w3.org/2000/svg';
// 이 태그들은 SVG 네임스페이스로 만든다(지도 모듈이 인라인 SVG 를 h() 로 그린다).
const SVG_TAGS = new Set([
  'svg', 'g', 'defs', 'use', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline',
  'polygon', 'text', 'tspan', 'linearGradient', 'radialGradient', 'stop', 'clipPath', 'mask', 'pattern',
]);

/** HTML 이스케이프. innerHTML 문자열을 만들 때만 쓴다(가능하면 h() 를 쓰고 textContent 로 넣는다). */
export function esc(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function appendChildren(el, children) {
  for (const c of children) {
    if (c == null || c === false || c === true) continue;
    if (Array.isArray(c)) appendChildren(el, c);
    else if (typeof c === 'object' && 'nodeType' in c) el.appendChild(c);
    else el.appendChild(document.createTextNode(String(c)));
  }
}

/**
 * h(tag, attrs, ...children) -> Element
 * attrs: class(문자열|배열) · style(문자열|객체) · dataset(객체) · onclick 같은 on* 함수 · value/checked(프로퍼티)
 *        그 외는 setAttribute. null/undefined/false 값은 건너뛴다. true 는 빈 속성.
 * children: 문자열(텍스트 노드로 들어가므로 안전)·노드·배열(중첩 가능)·null/false(무시)
 * 사용자·API 문자열은 반드시 children 이나 attrs 로 넣는다(innerHTML 금지).
 */
export function h(tag, attrs, ...children) {
  const el = SVG_TAGS.has(tag) ? document.createElementNS(SVG_NS, tag) : document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k.length > 2 && k.startsWith('on') && typeof v === 'function') {
      el.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (k === 'class') {
      el.setAttribute('class', Array.isArray(v) ? v.filter(Boolean).join(' ') : String(v));
    } else if (k === 'style' && typeof v === 'object') {
      Object.assign(el.style, v);
    } else if (k === 'dataset' && typeof v === 'object') {
      for (const [dk, dv] of Object.entries(v)) if (dv != null) el.dataset[dk] = String(dv);
    } else if (k === 'value' || k === 'checked') {
      el[k] = v;
    } else {
      el.setAttribute(k, v === true ? '' : String(v));
    }
  }
  appendChildren(el, children);
  return el;
}

/** root 의 자식을 모두 nodes 로 교체한다. */
export function render(root, ...nodes) {
  root.replaceChildren();
  appendChildren(root, nodes);
  return root;
}

/**
 * 이벤트 위임. on(root, 'click', '[data-act]', (event, matchedEl) => ...)
 * root 안에서 selector 에 맞는 가장 가까운 조상을 찾아 handler 를 부른다. 반환값은 해제 함수.
 */
export function on(root, type, selector, handler) {
  const listener = (event) => {
    const target = event.target;
    const el = target && typeof target.closest === 'function' ? target.closest(selector) : null;
    if (el && root.contains(el)) handler(event, el);
  };
  root.addEventListener(type, listener);
  return () => root.removeEventListener(type, listener);
}
