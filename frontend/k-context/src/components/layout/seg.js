// 세그먼트 버튼 묶음(톱바·설정 패널 공용). 선택된 값은 aria-pressed 로도 알린다.
import { h } from '../../lib/dom.js';

export function seg(items, current, act, labelOf) {
  return h('div', { class: 'seg', role: 'group' },
    items.map((v) => h('button', {
      type: 'button', class: ['seg__btn', v === current && 'is-on'], dataset: { act, value: v }, 'aria-pressed': String(v === current),
    }, labelOf(v))));
}
