// 출처 태그 상세(팝오버/바텀 시트): 등급 · 이름 · 위치 · 원문 구절 · 서지/URL · 수집일.
// 모든 문자열은 h() 의 자식(텍스트 노드)으로만 넣는다. URL 은 클릭 가능한 링크로 만들지 않고 텍스트로만 보여 준다
// (외부 주소로 나가지 않는다 — 샌드박스 데모에서 네트워크가 막혀 있다).
import { h } from '../../lib/dom.js';
import { sourceLabel } from '../../lib/format.js';

const row = (k, v) => v ? [h('dt', null, k), h('dd', null, v)] : null;

/**
 * @param {object} src 출처
 * @param {{t:Function, facts:{mark:string,text:any}[]}} v facts: 이 출처가 받치는 사실 층 문장들
 */
export function renderSourcePopover(src, { t, facts = [] }) {
  const titleId = 'cards-pop-title';
  return h('div', { class: 'cards-pop', dataset: { act: 'pop-backdrop' } },
    h('div', {
      class: 'cards-pop__dialog', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': titleId, dataset: { src: src.id },
    },
    h('div', { class: 'cards-pop__grab', 'aria-hidden': 'true' }),
    h('header', { class: 'cards-pop__head' },
      h('span', { class: 'src-tag cards-pop__grade', 'data-grade': src.tier }, src.tier),
      h('b', { id: titleId, class: 'cards-pop__name' }, src.name)),
    h('div', { class: 'cards-pop__label' }, sourceLabel(src)),
    h('div', { class: 'cards-label' }, t('card.tag_detail.quote')),
    h('blockquote', { class: 'cards-pop__quote' }, src.quote || t('cards.popover.none')),
    h('dl', { class: 'cards-pop__meta' },
      row(t('card.tag_detail.url'), src.url || src.bib),
      src.url && src.bib ? row(t('cards.popover.bib'), src.bib) : null,
      row(t('cards.popover.published'), src.published),
      row(t('card.tag_detail.collected'), src.collected_at),
      facts.length > 0 ? [h('dt', null, t('cards.popover.supports')), h('dd', null, facts.map((f) => h('div', null, `${f.mark} `, t(f.text))))] : null),
    h('button', { type: 'button', class: 'cards-btn cards-pop__close', dataset: { act: 'pop-close', fk: 'pop-close' } }, t('card.tag_detail.close'))));
}
