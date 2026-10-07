// 타임라인 한 행. 구분은 색 + 선 모양(CSS data-status) + 기호 + 텍스트 라벨.
import { h } from '../../lib/dom.js';

/** @param {object} row timelineView().rows[i]  @param {Function} t */
export function timelineRowNode(row, t) {
  const tag = row.meta.tagKey ? t(row.meta.tagKey) : '';
  return h('li', { class: 'timeline-row', dataset: { status: row.status, id: row.id } },
    h('span', { class: 'timeline-row__time' }, row.time),
    h('span', { class: 'timeline-row__body' },
      h('span', { class: 'timeline-row__title' }, t(row.title)),
      row.sub ? h('span', { class: 'timeline-row__sub' }, ' ', t(row.sub)) : null),
    tag ? h('span', { class: 'timeline-row__tag' }, h('span', { 'aria-hidden': 'true' }, row.meta.glyph, ' '), tag) : null);
}

/** 범례(원래·빈 시간·제안·추가함·건너뜀) — 같은 data-status 를 써서 행과 같은 모양을 보인다. */
export function legendNode(t) {
  const items = [['original', 'timeline.original'], ['free', 'timeline.free'], ['proposed', 'timeline.proposal'], ['added', 'timeline.added'], ['skipped', 'timeline.skipped']];
  return h('ul', { class: 'timeline-legend', 'aria-label': t('timeline.legend') },
    items.map(([status, key]) => h('li', { class: 'timeline-legend__item' },
      h('i', { class: 'timeline-legend__swatch', dataset: { status }, 'aria-hidden': 'true' }), t(key))));
}
