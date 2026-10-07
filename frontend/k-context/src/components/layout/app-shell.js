// 앱 골격: 슬롯 div 를 만들고 반응형 배치는 CSS(layout.css)가 한다. 모듈을 mount 하는 일은 main.js 몫이다.
//
// 데스크톱(>=900px) 2열        왼쪽 [chat / timeline]   가운데 [map / (rationale 태그 줄 + cards)]
// 모바일(<900px)               지도가 바탕, cards 영역은 지도 위에 겹침, chat·timeline 은 아래 시트의 탭
// 하단 패널                    .cards-zone 위에 핸들 바(드래그·^/v·키보드). 접힘/기본(1/3)/펼침(70%) 단계, 상태는 store.panelLevel
// 설정 패널                    톱바 기어 버튼(state.settingsOpen)으로 연다. 안에 settings(언어·테마·최소 변경) + securitylog.
//                              데스크톱은 우측 드로어, 모바일은 바닥 시트. 바깥(backdrop) 클릭으로 닫는다.
//
// 슬롯 이름 = 모듈 이름 = SLOT_NAMES. 각 슬롯은 <section class="slot slot-<name>" data-slot="<name>"> 이다.
import { h, on } from '../../lib/dom.js';
import { cardById } from '../../state/selectors.js';
import { PANEL_PERCENT, PANEL_MIN, PANEL_MAX, dragHeight, levelHeight, snapLevel, toggleLevel } from '../../lib/panel-level.js';

export const SLOT_NAMES = ['topbar', 'chat', 'timeline', 'map', 'rationale', 'cards', 'settings', 'securitylog'];
export const SHEET_TABS = ['chat', 'timeline'];

const PANEL_DRAG_MIN = 4; // 이 px 미만 움직임은 드래그가 아니라 탭으로 본다

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

  // 하단 패널(.cards-zone) 핸들 바. 높이 단계는 store.panelLevel, 드래그 중 임시 높이는 이 클로저(로컬)에만 둔다.
  // 구성: [separator(막대+제목) | ^ | v]. 버튼·키보드·드래그가 모두 setPanelLevel/stepPanel 로 간다.
  const gripTitle = h('span', { class: 'panel-handle__title' });
  const grip = h('div', {
    class: 'panel-handle__grip', role: 'separator', 'aria-orientation': 'horizontal', tabindex: '0',
    'aria-valuemin': String(PANEL_MIN), 'aria-valuemax': String(PANEL_MAX), dataset: { act: 'panel-grip' },
  }, h('span', { class: 'panel-handle__bar', 'aria-hidden': 'true' }), gripTitle);
  const btnUp = h('button', { type: 'button', class: 'panel-handle__btn', dataset: { act: 'panel-up' } }, h('span', { 'aria-hidden': 'true' }, '▲'));
  const btnDown = h('button', { type: 'button', class: 'panel-handle__btn', dataset: { act: 'panel-down' } }, h('span', { 'aria-hidden': 'true' }, '▼'));
  const handle = h('div', { class: 'panel-handle' }, grip, btnUp, btnDown);
  const zone = h('div', { class: 'cards-zone', dataset: { level: 'default' } }, handle, slots.rationale, slots.cards);

  const app = h('div', { class: 'app' },
    h('header', { class: 'app__top' }, slots.topbar),
    h('main', { class: 'app__main' },
      h('div', { class: 'col col-left' }, slots.chat, slots.timeline),
      h('div', { class: 'col col-center' }, slots.map, zone)),
    tabs,
    layer);
  root.replaceChildren(app);
  const mainEl = app.children?.[1];

  // 핸들 표시를 현재 상태에 맞춘다(요소는 다시 만들지 않는다 — 키보드 포커스·포인터 캡처 유지)
  function drawPanel() {
    const s = store.getState();
    const lv = s.panelLevel;
    zone.dataset.level = lv;
    grip.setAttribute('aria-valuenow', String(PANEL_PERCENT[lv]));
    grip.setAttribute('aria-valuetext', t(`panel.level.${lv}`));
    grip.setAttribute('aria-label', t('panel.handle'));
    btnUp.setAttribute('aria-label', t('panel.up'));
    btnUp.setAttribute('aria-expanded', String(lv === 'expanded'));
    btnDown.setAttribute('aria-label', t('panel.down'));
    btnDown.setAttribute('aria-expanded', String(lv !== 'collapsed'));
    btnUp.disabled = lv === 'expanded';
    btnDown.disabled = lv === 'collapsed';
    if (btnUp.disabled) btnUp.setAttribute('disabled', ''); else btnUp.removeAttribute('disabled');
    if (btnDown.disabled) btnDown.setAttribute('disabled', ''); else btnDown.removeAttribute('disabled');
    // 접힘일 때 보이는 한 줄 제목: 화면에 올린 카드 제목(없으면 패널 이름)
    const id = s.mode === 'old' ? s.selectedSeg : s.selectedNow ?? s.selectedSeg;
    const card = cardById(s, id);
    gripTitle.replaceChildren(document.createTextNode(String(t(card?.title ?? 'panel.title'))));
  }

  const containerH = () => mainEl?.clientHeight || 800;
  let drag = null; // {startY, startH, cur, moved, id}
  const endDrag = () => {
    drag = null;
    zone.style.height = '';
    delete zone.dataset.dragging;
  };
  const offs = [];
  const listen = (el, type, fn) => { el.addEventListener(type, fn); offs.push(() => el.removeEventListener(type, fn)); };
  listen(grip, 'pointerdown', (e) => {
    if (e.button > 0) return; // 마우스 보조 버튼은 무시
    const lv = store.getState().panelLevel;
    const startH = zone.getBoundingClientRect?.().height || levelOf(lv);
    drag = { startY: e.clientY, startH, cur: startH, moved: false };
    zone.dataset.dragging = 'true';
    grip.setPointerCapture?.(e.pointerId);
  });
  listen(grip, 'pointermove', (e) => {
    if (!drag) return;
    drag.cur = dragHeight(drag.startH, drag.startY, e.clientY, containerH());
    if (Math.abs(e.clientY - drag.startY) >= PANEL_DRAG_MIN) drag.moved = true;
    if (drag.moved) zone.style.height = `${drag.cur}px`;
  });
  listen(grip, 'pointerup', (e) => {
    if (!drag) return;
    const { cur, moved } = drag;
    grip.releasePointerCapture?.(e.pointerId);
    endDrag();
    if (moved) actions.setPanelLevel(snapLevel(cur, containerH())); // 놓으면 가장 가까운 단계로 스냅
  });
  listen(grip, 'pointercancel', () => { if (drag) endDrag(); });
  listen(grip, 'keydown', (e) => {
    if (e.key === 'ArrowUp') { e.preventDefault?.(); actions.stepPanel(1); }
    else if (e.key === 'ArrowDown') { e.preventDefault?.(); actions.stepPanel(-1); }
    else if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault?.();
      actions.setPanelLevel(toggleLevel(store.getState().panelLevel));
    }
  });
  listen(btnUp, 'click', () => actions.stepPanel(1));
  listen(btnDown, 'click', () => actions.stepPanel(-1));
  const levelOf = (lv) => levelHeight(lv, containerH());

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
  drawPanel();
  const offSettings = store.select((s) => s.settingsOpen, drawSettings);
  const offPanel = store.select((s) => [s.panelLevel, s.lang, s.mode, s.selectedSeg, s.selectedNow, s.data.cards], drawPanel, { equals: (a, b) => a.every((v, i) => v === b[i]) });
  const offStore = store.select((s) => [s.mobileTab, s.sheetOpen, s.lang], drawTabs, { equals: (a, b) => a.every((v, i) => v === b[i]) });

  return {
    slots,
    destroy() {
      offClick();
      offBackdrop();
      offSettings();
      offStore();
      offPanel();
      offs.forEach((f) => f());
      root.replaceChildren();
    },
  };
}
