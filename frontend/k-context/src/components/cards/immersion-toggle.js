// 몰입 층 켬/끔 스위치. 접근성: role=switch + aria-checked, 상태는 글자로도 적는다.
import { h } from '../../lib/dom.js';

export function renderImmersionToggle({ t, on }) {
  return h('div', { class: 'cards-imm-head' },
    h('span', { class: 'cards-label' }, t('card.immersion')),
    h('button', {
      type: 'button', class: ['cards-switch', on && 'is-on'], role: 'switch', 'aria-checked': String(!!on),
      dataset: { act: 'toggle-imm', fk: 'imm' },
    },
    h('span', { class: 'cards-switch__knob', 'aria-hidden': 'true' }),
    h('span', { class: 'cards-switch__text' }, on ? t('card.on') : t('card.off'))));
}
