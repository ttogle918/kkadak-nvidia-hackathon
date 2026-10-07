// 판단 근거 태그: 카드 곁에 한 줄로 놓이는 작은 원형(pill) 버튼. 누르면 팝오버가 열린다(aria-expanded).
// 색(옛날/지금)만으로 구분하지 않는다 — 라벨 앞 글리프(◆ ◇ ●)와 글자 라벨이 그대로 들어 있다.
import { h } from '../../lib/dom.js';

export function renderChips(chips, { t, openKey }) {
  return h('div', { class: 'rationale-tags', role: 'group', 'aria-label': t('rationale.chips_label') },
    h('span', { class: 'rationale-tags__label' }, t('rationale.title')),
    chips.map((c) => h('button', {
      type: 'button', class: ['rationale-tag', openKey === c.key && 'is-on'],
      'aria-expanded': String(openKey === c.key), 'aria-haspopup': 'dialog',
      dataset: { act: 'chip', key: c.key, tone: c.tone, fk: `chip:${c.key}` },
    }, t(c.label))));
}
