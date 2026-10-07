// timeline 모듈: 날짜별 일정(원래/빈 시간/제안/추가함/건너뜀). 계약: mount(root, ctx) -> {destroy()}.
// 읽기 위주 — 쓰는 것은 날짜 전환(setDay)과 "일정을 최소로만 바꾸기" 토글(toggleMinimize)뿐이다.
import { h, on, render } from '../../lib/dom.js';
import { timelineView } from './logic.js';
import { timelineRowNode, legendNode } from './timeline-row.js';
import { bundleTimelineNode } from './bundle-view.js';

/**
 * @param {HTMLElement} root app-shell 이 준 슬롯 div
 * @param {{store, api, t, actions}} ctx
 */
export function mount(root, ctx) {
  const { store, t, actions } = ctx;

  function draw() {
    // 다시 그리면 포커스가 사라지므로 키보드 사용자를 위해 같은 컨트롤로 되돌린다
    const active = globalThis.document?.activeElement;
    const keep = active && root.contains?.(active) && active.dataset?.act ? { act: active.dataset.act, value: active.dataset.value } : null;
    const s = store.getState();
    if (s.chatBundle) {
      render(root, bundleTimelineNode(s.chatBundle, s.day, t));
      restoreFocus(keep);
      return;
    }
    const v = timelineView(s);
    const it = s.data?.itinerary;
    const anchors = v.anchors.map((a) => t(a)).join(' → ');
    render(root, h('div', { class: 'timeline', dataset: { module: 'timeline' } },
      h('div', { class: 'timeline__head' },
        h('span', { class: 'timeline__title' }, t('timeline.title')),
        h('button', {
          type: 'button', class: 'timeline-min', role: 'switch', 'aria-checked': String(!!s.minimizeChanges),
          dataset: { act: 'toggle-min', on: s.minimizeChanges ? 'true' : 'false' },
        }, h('span', { class: 'timeline-min__track', 'aria-hidden': 'true' }, h('span', { class: 'timeline-min__knob' })), t('timeline.minimize'))),
      h('div', { class: 'timeline-days', role: 'tablist', 'aria-label': t('timeline.days') },
        v.tabs.map((d) => h('button', {
          type: 'button', role: 'tab', class: ['timeline-days__btn', d === v.day && 'is-on'], 'aria-selected': String(d === v.day),
          dataset: { act: 'day', value: d },
        }, t('topbar.day', { n: d })))),
      h('div', { class: 'timeline__day' }, `DAY ${v.day}`, v.date ? h('span', { class: 'timeline__date' }, ` · ${v.date}`) : null,
        anchors ? h('span', { class: 'timeline__date' }, ` · ${anchors}`) : null),
      !it ? h('p', { class: 'timeline__empty', role: 'status' }, t('app.loading'))
        : v.empty ? h('p', { class: 'timeline__empty', role: 'status' }, t('timeline.empty'))
          : h('ol', { class: 'timeline__rows' }, v.rows.map((r) => timelineRowNode(r, t))),
      legendNode(t)));
    restoreFocus(keep);
  }

  function restoreFocus(keep) {
    if (!keep) return;
    const again = [...(root.querySelectorAll?.('[data-act]') ?? [])].find((e) => e.dataset.act === keep.act && e.dataset.value === keep.value);
    again?.focus?.();
  }

  const offClick = on(root, 'click', '[data-act]', (_e, el) => {
    if (el.dataset.act === 'toggle-min') actions.toggleMinimize();
    else if (el.dataset.act === 'day') actions.setDay(Number(el.dataset.value));
    else if (el.dataset.act === 'clear-bundle') actions.clearChatBundle();
  });

  draw();
  const eq = (a, b) => a.every((v, i) => v === b[i]);
  const off = store.select(
    (s) => [s.day, s.added, s.skipped, s.selectedNow, s.minimizeChanges, s.lang, s.data.itinerary, s.chatBundle],
    draw, { equals: eq },
  );
  return { destroy() { off(); offClick(); root.replaceChildren(); } };
}
