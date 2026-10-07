// 앱 골격: 슬롯 div 를 만들고 반응형 배치는 CSS(layout.css)가 한다. 모듈을 mount 하는 일은 main.js 몫이다.
//
// 데스크톱(>=900px) 3열        왼쪽 [chat / timeline]   가운데 [map / cards]   오른쪽 [rationale / securitylog]
// 모바일(<900px)               지도가 바탕, cards 는 지도 위에 겹침, 나머지 4개는 아래 시트의 탭(chat·timeline·rationale·securitylog)
//
// 슬롯 이름 = 모듈 이름 = SLOT_NAMES. 각 슬롯은 <section class="slot slot-<name>" data-slot="<name>"> 이다.
import { h, on } from '../../lib/dom.js';

export const SLOT_NAMES = ['topbar', 'chat', 'timeline', 'map', 'cards', 'rationale', 'securitylog'];
export const SHEET_TABS = ['chat', 'timeline', 'rationale', 'securitylog'];

const slot = (name, extra) => h('section', { class: ['slot', `slot-${name}`, extra], dataset: { slot: name }, 'aria-label': name });

/**
 * @param {HTMLElement} root #app
 * @param {{store, t, actions}} ctx
 * @returns {{slots: Record<string, HTMLElement>, destroy(): void}}
 */
export function mountAppShell(root, ctx) {
  const { store, t, actions } = ctx;
  const slots = Object.fromEntries(SLOT_NAMES.map((n) => [n, slot(n)]));
  const tabs = h('nav', { class: 'mtabs', 'aria-label': 'sheet tabs' });

  const app = h('div', { class: 'app' },
    h('header', { class: 'app__top' }, slots.topbar),
    h('main', { class: 'app__main' },
      h('div', { class: 'col col-left' }, slots.chat, slots.timeline),
      h('div', { class: 'col col-center' }, slots.map, slots.cards),
      h('div', { class: 'col col-right' }, slots.rationale, slots.securitylog)),
    tabs);
  root.replaceChildren(app);

  function drawTabs() {
    const s = store.getState();
    app.dataset.mtab = s.mobileTab;
    app.dataset.sheet = s.sheetOpen ? 'open' : 'closed';
    tabs.replaceChildren(...SHEET_TABS.map((n) => h('button', {
      type: 'button', class: ['mtabs__btn', s.sheetOpen && s.mobileTab === n && 'is-on'],
      dataset: { act: 'mtab', value: n }, 'aria-pressed': String(s.sheetOpen && s.mobileTab === n),
    }, t(`tab.${n}`))));
  }

  const offClick = on(tabs, 'click', '[data-act="mtab"]', (_e, el) => {
    const s = store.getState();
    // 열려 있는 탭을 다시 누르면 시트를 닫는다
    if (s.sheetOpen && s.mobileTab === el.dataset.value) actions.setSheetOpen(false);
    else actions.setMobileTab(el.dataset.value);
  });

  drawTabs();
  const offStore = store.select((s) => [s.mobileTab, s.sheetOpen, s.lang], drawTabs, { equals: (a, b) => a.every((v, i) => v === b[i]) });

  return {
    slots,
    destroy() {
      offClick();
      offStore();
      root.replaceChildren();
    },
  };
}
