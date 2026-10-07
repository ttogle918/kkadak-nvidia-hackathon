// 출처 태그 줄: `[등급] 이름 · 위치`. 3개 초과면 "+N 출처" 로 접고 누르면 펼친다.
import { h } from '../../lib/dom.js';
import { numberedSourceLabel } from '../../lib/format.js';
import { splitTags } from './logic.js';

/**
 * @param {object} card 카드(sources 사용)
 * @param {{t:Function, expanded:boolean, openId:string|null, hoverFact:number|null}} view
 */
export function renderSourceTags(card, { t, expanded, openId, hoverFact }) {
  const { shown, hidden } = splitTags(card.sources, expanded);
  return h('div', { class: 'cards-sources' },
    h('div', { class: 'cards-label' }, t('card.sources')),
    h('div', { class: 'cards-tags' },
      shown.map(({ src, n }) => h('button', {
        type: 'button',
        class: ['src-tag', 'cards-tag', openId === src.id && 'is-open', hoverFact === n && 'is-hl'],
        dataset: { act: 'tag', id: src.id, n, fk: `tag:${card.id}:${src.id}` },
        'data-grade': src.tier,
        'aria-haspopup': 'dialog',
      }, numberedSourceLabel(src, n - 1))),
      hidden > 0 && h('button', {
        type: 'button', class: 'cards-more', dataset: { act: 'more-tags', card: card.id, fk: `more:${card.id}` },
      }, t('card.more_sources', { n: hidden }))));
}
