// 앱 골격: 슬롯 div 를 만들고 반응형 배치는 CSS(layout.css)가 한다. 모듈을 mount 하는 일은 main.js 몫이다.
//
// 데스크톱(>=900px) 2열        왼쪽 [chat / timeline]   가운데 [map / (rationale 태그 줄 + cards)]
// 모바일(<900px)               지도가 바탕, cards 영역은 지도 위에 겹침, chat·timeline 은 아래 시트의 탭
// 설정 패널                    톱바 기어 버튼(state.settingsOpen)으로 연다. 안에 settings(언어·테마·최소 변경) + securitylog.
//                              데스크톱은 우측 드로어, 모바일은 바닥 시트. 바깥(backdrop) 클릭으로 닫는다.
//
// 슬롯 이름 = 모듈 이름 = SLOT_NAMES. 각 슬롯은 <section class="slot slot-<name>" data-slot="<name>"> 이다.
import { h, on } from '../../lib/dom.js';

export const SLOT_NAMES = ['topbar', 'chat', 'timeline', 'map', 'rationale', 'cards', 'settings', 'securitylog'];
export const SHEET_TABS = ['chat', 'timeline'];

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

  // 설정 패널: 바깥 클릭용 backdrop + 패널(settings 모듈이 머리말·설정, securitylog 모듈이 로그를 그린다)
  const layer = h('div', { class: 'settings-layer', dataset: { open: 'false' } },
    h('div', { class: 'settings-backdrop', dataset: { act: 'settings-backdrop' } }),
    h('aside', { class: 'settings-panel', role: 'dialog', 'aria-labelledby': 'settings-title' }, slots.settings, slots.securitylog));

  const app = h('div', { class: 'app' },
    h('header', { class: 'app__top' }, slots.topbar),
    h('main', { class: 'app__main' },
      h('div', { class: 'col col-left' }, slots.chat, slots.timeline),
      h('div', { class: 'col col-center' }, slots.map, h('div', { class: 'cards-zone' }, slots.rationale, slots.cards))),
    tabs,
    layer);
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

  const offBackdrop = on(layer, 'click', '[data-act="settings-backdrop"]', () => actions.setSettingsOpen(false));
  const drawSettings = () => { layer.dataset.open = store.getState().settingsOpen ? 'true' : 'false'; };

  drawTabs();
  drawSettings();
  const offSettings = store.select((s) => s.settingsOpen, drawSettings);
  const offStore = store.select((s) => [s.mobileTab, s.sheetOpen, s.lang], drawTabs, { equals: (a, b) => a.every((v, i) => v === b[i]) });

  return {
    slots,
    destroy() {
      offClick();
      offBackdrop();
      offSettings();
      offStore();
      root.replaceChildren();
    },
  };
}
