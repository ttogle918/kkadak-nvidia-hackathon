// 경로 A·B·C 카드와 구간 목록(길찾기 안내처럼 순서대로). 목록 항목 클릭은 지도 구간 클릭과 같은 selectSeg 로 간다.
import { h } from '../../lib/dom.js';
import { BADGE_KEY, circled } from '../../lib/format.js';

/** 구간의 한 줄 요약: 사실 층 첫 문장 -> 본문 -> 빈 문자열. 값은 string 또는 {ko,en}. */
export function stepLine(card, t) {
  if (!card) return '';
  const first = card.facts?.[0]?.text;
  return t(first ?? card.body ?? '');
}

/** 경로 딱지 구성 문구 "◆ 기록 1 · ◇ 전승 1". */
export function badgeMixText(mix, t) {
  return Object.entries(mix ?? {}).map(([k, n]) => `${t(`badge.${k}`)} ${n}`).join(' · ');
}

/** 경로 선택 카드 한 줄 묶음. */
export function buildRouteCards(routes, selectedId, t) {
  return h('div', { class: 'map-routes', role: 'group', 'aria-label': t('map.routes.title') },
    routes.map((r) => {
      const on = r.id === selectedId;
      return h('button', {
        type: 'button', class: ['map-route', on && 'is-on'], 'aria-pressed': String(on),
        dataset: { act: 'route', id: r.id, fk: `route:${r.id}` },
      },
      h('span', { class: 'map-route__head' },
        h('span', { class: 'map-route__id' }, r.id),
        h('span', { class: 'map-route__theme' }, t(r.theme)),
        (r.badges ?? []).map((b) => h('span', { class: 'map-route__chip' }, t(`route.badge.${b}`)))),
      h('span', { class: 'map-route__meta' },
        t('map.route.walk', { n: r.walk_min }), ' · ', t('map.route.delta', { n: r.delta_min }), ' · ', t('map.route.stories', { n: r.story_count })),
      h('span', { class: 'map-route__mix' }, badgeMixText(r.badge_mix, t)),
      h('span', { class: 'map-route__reason' }, t(r.recommend_reason)));
    }));
}

/** 구간 목록. cardOf(card_id) -> 카드|null. */
export function buildStepList({ route, selectedSeg, cardOf, t, open }) {
  const items = route.segments.map((s, i) => {
    const card = s.card_id ? cardOf(s.card_id) : null;
    const story = !!s.card_id;
    const on = story && s.card_id === selectedSeg;
    return h('li', { class: 'map-step__item' },
      h('button', {
        type: 'button', class: ['map-step', on && 'is-on', !story && 'is-plain'],
        disabled: !story, 'aria-current': on ? 'true' : null,
        dataset: story ? { act: 'seg', card: s.card_id, fk: `step:${s.card_id}` } : null,
      },
      h('span', { class: 'map-step__no' }, circled(i + 1)),
      h('span', { class: 'map-step__body' },
        h('span', { class: 'map-step__name' }, t(s.name)),
        h('span', { class: 'map-step__meta' }, t('map.step.meta', { m: s.length_m, n: s.walk_min }),
          s.weak ? ` · ${t('map.step.weak')}` : ''),
        story
          ? h('span', { class: 'map-step__line' }, stepLine(card, t))
          : h('span', { class: 'map-step__line' }, t('map.step.plain'))),
      card && BADGE_KEY[card.badge] ? h('span', { class: 'badge', dataset: { badge: BADGE_KEY[card.badge] } }, t(`badge.${card.badge}`)) : null));
  });
  return h('div', { class: 'map-steps' },
    h('button', {
      type: 'button', class: 'map-steps__toggle', 'aria-expanded': String(open),
      dataset: { act: 'toggle-steps', fk: 'toggle-steps' },
    }, `${open ? '▾' : '▸'} ${t('map.steps.title')} · ${route.id}`),
    open ? h('ol', { class: 'map-steps__list' }, items) : null);
}
