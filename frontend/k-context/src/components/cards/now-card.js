// 지금 카드: 상태 딱지 · 들어갈 자리 · +분/체류 · 왜 맞나 · 확인 항목 · 경고 · 포스터 · 가 봐야 아는 것 · 로컬 맥락 · 버튼.
import { h } from '../../lib/dom.js';
import { betweenText, checkGlyph, nowButtons, onlyText } from './logic.js';
import { renderBadge } from './badge.js';
import { renderSourceTags } from './source-tags.js';

const stat = (value, label, t) => h('div', { class: 'cards-stat' },
  h('div', { class: 'cards-stat__num' }, String(value), h('small', null, t('card.min'))),
  h('div', { class: 'cards-stat__label' }, label));

/**
 * @param {object} card 지금 카드
 * @param {{t, added:boolean, skipped:boolean, expanded:boolean, openId:string|null}} v
 */
export function renderNowCard(card, v) {
  const { t } = v;
  const btn = nowButtons(card.badge, { added: v.added, skipped: v.skipped });
  const only = onlyText(card, t);
  const slot = card.slot;
  const when = slot ? `${t('cards.day', { n: slot.day })}${slot.at ? ` · ${slot.at}` : ''}` : '';
  const between = betweenText(slot?.between, t);
  const lc = card.local_context;

  return h('article', { class: ['cards-card', 'cards-card--now', card.badge === '보류' && 'is-hold'], dataset: { card: card.id, kind: 'now' }, 'aria-label': t('card.now') },
    h('header', { class: 'cards-head' },
      h('span', { class: 'cards-kind cards-kind--now' }, `● ${t('card.now')}`),
      renderBadge(card.badge, t),
      only && h('span', { class: 'cards-only' }, only)),
    h('div', null,
      when && h('div', { class: 'cards-when' }, when),
      h('h3', { class: 'cards-title' }, t(card.title),
        card.kind_label && h('span', { class: 'cards-kindlabel' }, t(card.kind_label))),
      between && h('div', { class: 'cards-place' }, t('cards.slot_between', { where: between }))),

    // 경고 박스: 단독 출처 / 자료 충돌. 점선 + 글리프로 구분
    card.warning && h('div', { class: 'cards-warning', role: 'note' },
      h('b', null, `! ${t(card.warning.title)}`), h('div', null, t(card.warning.body))),

    (card.time_cost_min != null || card.stay_min != null) && h('div', { class: 'cards-stats' },
      card.time_cost_min != null && stat(`+${card.time_cost_min}`, t('card.detour'), t),
      card.stay_min != null && stat(card.stay_min, t('card.stay'), t)),

    card.why_fits?.length > 0 && h('section', null,
      h('div', { class: 'cards-label cards-label--now' }, t('card.why_fits')),
      h('ul', { class: 'cards-list' }, card.why_fits.map((w) => h('li', null, t(w)))),
      h('button', { type: 'button', class: 'cards-link', dataset: { act: 'why-pick', fk: 'why' } }, t('card.why_pick'))),

    card.checks?.length > 0 && h('section', null,
      h('div', { class: 'cards-label cards-label--now' }, t('cards.checks')),
      h('ul', { class: 'cards-checks' }, card.checks.map((c) => h('li', { class: `cards-check is-${c.level}` },
        h('b', { class: 'cards-check__glyph', 'aria-hidden': 'true' }, checkGlyph(c.level)),
        h('span', { class: 'sr-only' }, t(`cards.level.${c.level}`)),
        t(c.text))))),

    card.poster?.read && h('section', { class: 'cards-poster' },
      h('div', { class: 'cards-poster__thumb', 'aria-hidden': 'true' }, t('cards.poster_thumb')),
      h('div', null, h('div', { class: 'cards-label' }, t('card.poster')), t(card.poster.read))),

    card.caveats?.length > 0 && h('section', null,
      h('div', { class: 'cards-label' }, t('card.unknown')),
      h('div', { class: 'cards-chips' }, card.caveats.map((c) => h('span', { class: 'cards-chip' }, t(c))))),

    lc && h('div', { class: 'cards-local' },
      h('span', { class: 'cards-label cards-label--old' }, `${t('cards.local_context')} ◆`),
      h('div', null, t(lc.text)),
      lc.story_card_id && h('button', {
        type: 'button', class: 'cards-link cards-link--old', dataset: { act: 'local', id: lc.story_card_id, fk: 'local' },
      }, t('cards.local_go'))),

    renderSourceTags(card, { t, expanded: !!v.expanded, openId: v.openId, hoverFact: null }),

    card.valid?.as_of && h('div', { class: 'cards-asof' }, t('cards.as_of', { date: card.valid.as_of })),

    h('div', { class: 'cards-actions' },
      h('button', {
        type: 'button', class: ['cards-btn', 'cards-btn--primary', btn.primary.kind === 'hold' && 'is-hold'],
        dataset: { act: 'add', kind: btn.primary.kind, fk: 'add' }, disabled: btn.primary.disabled, 'aria-disabled': btn.primary.disabled ? 'true' : null,
        'aria-pressed': btn.primary.kind === 'added' ? 'true' : null,
      }, t(btn.primary.labelKey)),
      h('button', {
        type: 'button', class: 'cards-btn', dataset: { act: 'skip', fk: 'skip' },
        disabled: btn.skip.disabled, 'aria-disabled': btn.skip.disabled ? 'true' : null,
      }, t(btn.skip.labelKey))),
    card.badge === '보류' && h('div', { class: 'cards-hold-note' }, t('cards.hold_note')));
}
