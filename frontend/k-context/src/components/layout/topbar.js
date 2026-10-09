// 상단 바: 로고 · 보기(옛날/지금/둘 다) · 날짜(DAY) · 설정(기어) 버튼.
// 언어·테마·일정 최소 변경과 보안 로그는 설정 패널(layout/settings.js)로 옮겼다. 기어에는 승인 대기 로그 수를 알림 점으로 단다.
// 상태를 직접 바꾸지 않고 ctx.actions 를 부른다. 레이아웃 전용이라 다른 모듈과 무관하다.
import { h, render, on } from '../../lib/dom.js';
import { isRealApi, pendingCount, screenStatus } from '../../state/selectors.js';
import { mockBadge } from '../../lib/mock-badge.js';
import { seg } from './seg.js';
import { evalTrip } from '../../lib/trip.js';

const MODES = ['old', 'now', 'both'];
const DAYS = [1, 2, 3]; // 샘플 일정은 DAY 1~3

/** 기어 아이콘(인라인 SVG, 장식이라 aria-hidden) */
function gearIcon() {
  return h('svg', { class: 'topbar__gear-icon', viewBox: '0 0 24 24', width: 20, height: 20, 'aria-hidden': 'true', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' },
    h('circle', { cx: 12, cy: 12, r: 3.2 }),
    h('path', { d: 'M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.8 1.8M16.7 16.7l1.8 1.8M5.5 18.5l1.8-1.8M16.7 7.3l1.8-1.8' }));
}

/** 지금 화면이 MOCK 인지 실제 서버 결과인지 한 줄로. 실제(bundle·empty)일 때는 MOCK 딱지를 붙이지 않는다. */
export function statusNode(status, t) {
  return h('div', { class: 'topbar__status', role: 'status', dataset: { status } },
    status === 'bundle' || status === 'empty' || status === 'error' ? null : mockBadge(t),
    h('span', { class: 'topbar__status-text' }, t(`mock.status.${status === 'all-mock' ? 'all' : status}`)));
}

/** 여행 기간 입력(선택 보조 — 비어 있는 것이 정상). 실제 모드에서만 그린다. */
export function tripNode(tripInput, t) {
  const bad = evalTrip(tripInput).error;
  const field = (which, label) => h('label', { class: 'topbar__trip-field' },
    h('span', { class: 'topbar__trip-label' }, t(label)),
    h('input', { type: 'date', class: 'topbar__trip-input', value: tripInput?.[which] ?? '', dataset: { trip: which }, 'aria-invalid': bad ? 'true' : null, 'aria-describedby': 'trip-help' }));
  return h('div', { class: 'topbar__trip', dataset: { module: 'trip' } },
    h('span', { class: 'topbar__trip-title' }, t('trip.title')),
    field('from', 'trip.from'), h('span', { 'aria-hidden': 'true' }, '~'), field('to', 'trip.to'),
    h('span', { class: 'topbar__trip-help', id: 'trip-help' }, t('trip.help')),
    bad ? h('span', { class: 'topbar__trip-error', role: 'alert', dataset: { trip: 'invalid' } }, t('trip.invalid')) : null);
}

/** @returns {{destroy(): void}} */
export function mount(root, ctx) {
  const { store, t, actions, api } = ctx;

  const logo = h('svg', { class: 'topbar__logo', viewBox: '0 0 24 24', width: 22, height: 22, 'aria-hidden': 'true' },
    h('rect', { x: 5, y: 5, width: 14, height: 14, rx: 2, fill: 'var(--c-old)', transform: 'rotate(45 12 12)' }),
    h('circle', { cx: 12, cy: 12, r: 3.4, fill: 'var(--c-now)' }));

  function draw() {
    const s = store.getState();
    const pend = pendingCount(s.logs);
    const keep = globalThis.document?.activeElement?.dataset?.act === 'open-settings';
    const keepTrip = globalThis.document?.activeElement?.dataset?.trip;
    render(root, h('div', { class: 'topbar' },
      h('div', { class: 'topbar__brand' }, logo, h('span', { class: 'topbar__title' }, t('app.title')), h('span', { class: 'topbar__tagline' }, t('app.tagline'))),
      h('div', { class: 'topbar__group', 'aria-label': t('topbar.mode') }, seg(MODES, s.mode, 'set-mode', (m) => t(`topbar.mode.${m}`))),
      h('div', { class: 'topbar__group' }, seg(DAYS, s.day, 'set-day', (d) => t('topbar.day', { n: d }))),
      h('div', { class: 'topbar__spacer' }),
      isRealApi(api) ? tripNode(s.tripInput, t) : null,
      statusNode(screenStatus(s, api), t),
      h('button', {
        type: 'button', class: 'topbar__gear', dataset: { act: 'open-settings', pending: pend }, 'aria-haspopup': 'dialog', 'aria-expanded': String(!!s.settingsOpen),
        'aria-label': pend > 0 ? t('topbar.settings_pending', { n: pend }) : t('topbar.settings'),
      }, gearIcon(), pend > 0 ? h('span', { class: 'topbar__badge', dataset: { role: 'pending' }, 'aria-hidden': 'true' }, String(pend)) : null)));
    if (keepTrip) root.querySelector?.(`[data-trip="${keepTrip === 'to' ? 'to' : 'from'}"]`)?.focus?.();
    if (keep) root.querySelector?.('[data-act="open-settings"]')?.focus?.();
  }

  const offClick = on(root, 'click', '[data-act]', (_e, el) => {
    const { act, value } = el.dataset;
    if (act === 'set-mode') actions.setMode(value);
    else if (act === 'set-day') actions.setDay(value);
    else if (act === 'open-settings') actions.setSettingsOpen(!store.getState().settingsOpen);
  });

  const offChange = on(root, 'change', '[data-trip]', (_e, el) => {
    const cur = store.getState().tripInput ?? { from: '', to: '' };
    const v = typeof el.value === 'string' ? el.value : '';
    if (el.dataset.trip === 'from') actions.setTripInput(v, cur.to);
    else if (el.dataset.trip === 'to') actions.setTripInput(cur.from, v);
  });

  draw();
  const offStore = store.select(
    (s) => [s.mode, s.day, s.lang, s.settingsOpen, pendingCount(s.logs), s.chatBundle, s.tripInput?.from, s.tripInput?.to, s.error],
    draw,
    { equals: (a, b) => a.every((v, i) => v === b[i]) },
  );

  return {
    destroy() {
      offClick();
      offChange();
      offStore();
      root.replaceChildren();
    },
  };
}
