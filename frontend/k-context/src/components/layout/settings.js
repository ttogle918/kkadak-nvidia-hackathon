// 설정 패널의 머리말과 설정: 제목 · 닫기 · 일정 최소 변경 · 테마 · 언어. 보안 로그는 같은 패널 안의 securitylog 슬롯이 그린다.
// 열림 상태는 store.settingsOpen (여는 쪽은 톱바 기어, 바깥 클릭 닫기는 app-shell). 여기서는 Esc·닫기 버튼·포커스를 맡는다.
// 레이아웃 전용이라 다른 모듈과 무관하다. 상태는 actions 로만 바꾼다.
import { h, render, on } from '../../lib/dom.js';
import { seg } from './seg.js';

const LANGS = ['ko', 'en'];
const THEMES = ['auto', 'light', 'dark'];
const doc = () => globalThis.document;

/** @returns {{destroy(): void}} */
export function mount(root, ctx) {
  const { store, t, actions } = ctx;
  let opener = null; // 열기 직전 포커스 — 닫을 때 돌려준다

  function draw() {
    const s = store.getState();
    const ae = doc()?.activeElement;
    const keepFk = ae && root.contains?.(ae) ? ae.dataset?.fk : null;
    render(root, h('div', { class: 'settings' },
      h('header', { class: 'settings__head' },
        h('h2', { id: 'settings-title', class: 'settings__title' }, t('settings.title')),
        h('button', { type: 'button', class: 'settings__close', dataset: { act: 'close-settings', fk: 'close' }, 'aria-label': t('settings.close') }, '✕')),
      h('div', { class: 'settings__rows' },
        h('div', { class: 'settings__row' },
          h('span', { class: 'settings__label' }, t('topbar.minimize')),
          h('button', {
            type: 'button', class: ['chip-toggle', s.minimizeChanges && 'is-on'], dataset: { act: 'toggle-min', fk: 'min' }, 'aria-pressed': String(s.minimizeChanges),
          }, s.minimizeChanges ? t('settings.on') : t('settings.off'))),
        h('div', { class: 'settings__row' },
          h('span', { class: 'settings__label' }, t('topbar.theme')),
          h('div', { 'aria-label': t('topbar.theme') }, seg(THEMES, s.theme, 'set-theme', (m) => t(`topbar.theme.${m}`)))),
        h('div', { class: 'settings__row' },
          h('span', { class: 'settings__label' }, t('topbar.lang')),
          h('div', { 'aria-label': t('topbar.lang') }, seg(LANGS, s.lang, 'set-lang', (l) => t(`topbar.lang.${l}`)))))));
    if (keepFk) {
      const hit = [...(root.querySelectorAll?.('[data-fk]') ?? [])].find((e) => e.dataset.fk === keepFk);
      hit?.focus?.();
    }
  }

  const close = () => actions.setSettingsOpen(false);
  const offClick = on(root, 'click', '[data-act]', (_e, el) => {
    const { act, value } = el.dataset;
    if (act === 'close-settings') close();
    else if (act === 'toggle-min') actions.toggleMinimize();
    else if (act === 'set-theme') actions.setTheme(value);
    else if (act === 'set-lang') actions.setLang(value);
  });

  // Esc 로 닫기: 포커스가 어디 있든 먹도록 document 에 건다(없으면 root)
  const onKey = (e) => {
    if (e.key === 'Escape' && store.getState().settingsOpen) close();
  };
  const keyTarget = doc()?.addEventListener ? doc() : root;
  keyTarget.addEventListener('keydown', onKey);

  draw();
  const offStore = store.subscribe((s, prev) => {
    if (s.settingsOpen !== prev.settingsOpen) {
      if (s.settingsOpen) {
        opener = doc()?.activeElement ?? null;
        draw();
        root.querySelector?.('[data-fk="close"]')?.focus?.();
      } else {
        draw();
        // 기어 버튼으로 포커스 복귀(열 때 포커스가 있던 요소, 없어졌으면 기어를 찾는다)
        const back = opener && opener.isConnected !== false ? opener : doc()?.querySelector?.('[data-act="open-settings"]');
        back?.focus?.();
        opener = null;
      }
    } else if (s.lang !== prev.lang || s.theme !== prev.theme || s.minimizeChanges !== prev.minimizeChanges) {
      draw();
    }
  });

  return {
    destroy() {
      offStore();
      offClick();
      keyTarget.removeEventListener('keydown', onKey);
      root.replaceChildren();
    },
  };
}
