// 상단 바: 로고 · 보기(옛날/지금/둘 다) · 날짜(DAY) · 일정 최소 변경 · 언어 · 테마.
// 상태를 직접 바꾸지 않고 ctx.actions 를 부른다. 레이아웃 전용이라 다른 모듈과 무관하다.
import { h, render, on } from '../../lib/dom.js';

const MODES = ['old', 'now', 'both'];
const LANGS = ['ko', 'en'];
const THEMES = ['auto', 'light', 'dark'];
const DAYS = [1, 2, 3]; // 샘플 일정은 DAY 1~3

function seg(items, current, act, labelOf) {
  return h('div', { class: 'seg', role: 'group' },
    items.map((v) => h('button', {
      type: 'button', class: ['seg__btn', v === current && 'is-on'], dataset: { act, value: v }, 'aria-pressed': String(v === current),
    }, labelOf(v))));
}

/** @returns {{destroy(): void}} */
export function mount(root, ctx) {
  const { store, t, actions } = ctx;

  const logo = h('svg', { class: 'topbar__logo', viewBox: '0 0 24 24', width: 22, height: 22, 'aria-hidden': 'true' },
    h('rect', { x: 5, y: 5, width: 14, height: 14, rx: 2, fill: 'var(--c-old)', transform: 'rotate(45 12 12)' }),
    h('circle', { cx: 12, cy: 12, r: 3.4, fill: 'var(--c-now)' }));

  function draw() {
    const s = store.getState();
    render(root, h('div', { class: 'topbar' },
      h('div', { class: 'topbar__brand' }, logo, h('span', { class: 'topbar__title' }, t('app.title')), h('span', { class: 'topbar__tagline' }, t('app.tagline'))),
      h('div', { class: 'topbar__group', 'aria-label': t('topbar.mode') }, seg(MODES, s.mode, 'set-mode', (m) => t(`topbar.mode.${m}`))),
      h('div', { class: 'topbar__group' }, seg(DAYS, s.day, 'set-day', (d) => t('topbar.day', { n: d }))),
      h('div', { class: 'topbar__spacer' }),
      h('button', {
        type: 'button', class: ['chip-toggle', s.minimizeChanges && 'is-on'], dataset: { act: 'toggle-min' }, 'aria-pressed': String(s.minimizeChanges),
      }, t('topbar.minimize')),
      h('div', { class: 'topbar__group', 'aria-label': t('topbar.theme') }, seg(THEMES, s.theme, 'set-theme', (m) => t(`topbar.theme.${m}`))),
      h('div', { class: 'topbar__group', 'aria-label': t('topbar.lang') }, seg(LANGS, s.lang, 'set-lang', (l) => t(`topbar.lang.${l}`)))));
  }

  const offClick = on(root, 'click', '[data-act]', (_e, el) => {
    const { act, value } = el.dataset;
    if (act === 'set-mode') actions.setMode(value);
    else if (act === 'set-day') actions.setDay(value);
    else if (act === 'set-lang') actions.setLang(value);
    else if (act === 'set-theme') actions.setTheme(value);
    else if (act === 'toggle-min') actions.toggleMinimize();
  });

  draw();
  const offStore = store.select(
    (s) => [s.mode, s.day, s.lang, s.theme, s.minimizeChanges],
    draw,
    { equals: (a, b) => a.every((v, i) => v === b[i]) },
  );

  return {
    destroy() {
      offClick();
      offStore();
      root.replaceChildren();
    },
  };
}
