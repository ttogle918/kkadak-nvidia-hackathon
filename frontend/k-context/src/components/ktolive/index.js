// ktolive 모듈: "한국관광공사 관광정보(원문)" 별도 절. 지도·서울 API 행사 카드와 섞지 않고, 이미지는 그리지 않는다.
// 텍스트는 h() 의 자식(= 텍스트 노드)으로만 넣는다 — HTML 해석 없음. 묶음에 kto_live 가 없으면 절 자체가 없다.
import { h, render } from '../../lib/dom.js';
import { ktoView } from './logic.js';

export function mount(root, ctx) {
  const { store } = ctx;
  const t = (x, p) => ctx.t(x, p);

  function draw() {
    const view = ktoView(store.getState().chatBundle, t);
    root.hidden = view.state === 'none';
    if (view.state === 'none') { render(root); return; }
    let body;
    if (view.state === 'unavailable') {
      body = h('p', { class: 'ktolive__note', role: 'status' }, t('ktolive.unavailable'));
    } else if (!view.items.length) {
      body = h('p', { class: 'ktolive__note', role: 'status' }, t('ktolive.empty'));
    } else {
      body = h('ul', { class: 'ktolive__list' }, view.items.map((it) => h('li', { class: 'ktolive__item' },
        h('dl', { class: 'ktolive__fields' }, it.fields.map((f) => [h('dt', { class: 'ktolive__label' }, f.label), h('dd', { class: 'ktolive__value', dataset: { f: f.key } }, f.value)])),
        h('p', { class: 'ktolive__attr' }, it.attribution))));
    }
    const link = view.sourceUrl
      ? h('a', { class: 'ktolive__link', href: view.sourceUrl, rel: 'noopener noreferrer', target: '_blank' }, t('ktolive.link'))
      : null;
    render(root, h('div', { class: 'ktolive', dataset: { state: view.state } }, h('h3', { class: 'ktolive__title' }, t('ktolive.title')), body, link));
  }

  draw();
  const off = store.subscribe((s, prev) => { if (s.chatBundle !== prev.chatBundle || s.lang !== prev.lang) draw(); });
  return { destroy() { off(); root.replaceChildren(); } };
}
