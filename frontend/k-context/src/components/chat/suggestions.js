// 예시 질문 버튼 3개. 클릭 동작은 호출한 쪽(index.js)이 정한다 — 여기서는 그리기만.
import { h } from '../../lib/dom.js';
import { SUGGESTIONS } from './logic.js';

/** @returns {HTMLElement} */
export function suggestionsNode(t) {
  return h('div', { class: 'chat-suggest', role: 'group', 'aria-label': t('chat.suggest.label') },
    SUGGESTIONS.map((s) => h('button', {
      type: 'button', class: ['chat-suggest__btn', s.dashed && 'chat-suggest__btn--attack'],
      dataset: { act: 'suggest', id: s.id },
    }, t(s.labelKey))));
}
