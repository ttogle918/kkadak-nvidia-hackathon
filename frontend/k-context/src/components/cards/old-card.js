// 옛날 카드: 딱지·시대·제목·장소 / 사실 층(문장마다 출처 번호) / 이설 병기 / 몰입 층(상상) / 출처 태그.
import { h } from '../../lib/dom.js';
import { circled } from '../../lib/format.js';
import { renderBadge } from './badge.js';
import { renderImmersionToggle } from './immersion-toggle.js';
import { renderSourceTags } from './source-tags.js';

/** 사실 층 한 문장 + 출처 번호 버튼. 번호에 호버/포커스하면 이 문장이 강조된다(hoverFact). */
function renderFact(f, { t, hoverFact, card }) {
  const src = card.sources?.[f.ref - 1];
  return h('span', { class: ['cards-fact', hoverFact === f.ref && 'is-hl'], dataset: { ref: f.ref } },
    t(f.text),
    h('button', {
      type: 'button', class: 'cards-fact__ref', dataset: { act: 'fact-ref', factRef: f.ref, id: src?.id },
      'aria-label': t('cards.fact_ref', { n: f.ref }),
    }, circled(f.ref)),
    ' ');
}

/**
 * @param {object} card 옛날 카드
 * @param {{t, immersion:boolean, hoverFact:number|null, expanded:boolean, openId:string|null}} v
 */
export function renderOldCard(card, v) {
  const { t, immersion } = v;
  const alts = card.alternatives ?? [];
  return h('article', { class: 'cards-card cards-card--old', dataset: { card: card.id, kind: 'old' }, 'aria-label': t('card.old') },
    h('header', { class: 'cards-head' },
      h('span', { class: 'cards-kind' }, `◆ ${t('card.old')}`),
      renderBadge(card.badge, t),
      card.era && h('span', { class: 'cards-era' }, t(card.era))),
    h('h3', { class: 'cards-title' }, t(card.title)),
    card.place?.name && h('div', { class: 'cards-place' }, t(card.place.name)),

    // 사실 층: 근거가 있는 문장만. facts 가 없으면 body 를 한 덩어리로.
    h('section', { class: 'cards-fact-layer' },
      h('div', { class: 'cards-label' }, t('card.fact_layer')),
      h('p', { class: 'cards-facts' },
        card.facts?.length ? card.facts.map((f) => renderFact(f, { t, hoverFact: v.hoverFact, card })) : t(card.body))),

    // 이설 병기: 어느 쪽도 버리지 않고 나란히(설 A 실선, 설 B 점선)
    alts.length > 0 && h('section', { class: 'cards-alts', 'aria-label': t('card.alt_accounts') },
      alts.map((a, i) => h('div', { class: ['cards-alt', i > 0 && 'is-dashed'] },
        h('b', { class: 'cards-alt__label' }, t(a.label)),
        h('div', null, t(a.text))))),

    // 몰입 층: 사실이 아니라 상상. 끌 수 있다.
    card.narration && h('section', { class: 'cards-imm' },
      renderImmersionToggle({ t, on: immersion }),
      immersion && h('div', { class: 'cards-narration' },
        h('span', { class: 'cards-imagined' }, t('card.imagined')), ' ', t(card.narration))),

    renderSourceTags(card, { t, expanded: !!v.expanded, openId: v.openId, hoverFact: v.hoverFact }));
}
