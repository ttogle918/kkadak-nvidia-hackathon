// 판단 근거 칩 줄. 칩은 토글 버튼(aria-pressed). 옛날/지금 색은 data-tone 으로 나눈다.
import { h } from '../../lib/dom.js';

export function renderChips(chips, { t, openKey }) {
  return h('div', { class: 'rationale-chips', role: 'group', 'aria-label': t('rationale.chips_label') },
    chips.map((c) => h('button', {
      type: 'button', class: ['rationale-chip', openKey === c.key && 'is-on'], 'aria-pressed': String(openKey === c.key),
      dataset: { act: 'chip', key: c.key, tone: c.tone, fk: `chip:${c.key}` },
    }, t(c.label))));
}
