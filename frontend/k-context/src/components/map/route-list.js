// 경로 A·B·C 카드와 구간 목록(길찾기 안내처럼 순서대로). 목록 항목 클릭은 지도 구간 클릭과 같은 selectSeg 로 간다.
import { h } from '../../lib/dom.js';
import { BADGE_KEY, circled } from '../../lib/format.js';
import { routeDays, isV2Bundle } from '../../lib/chat-bundle.js';

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
        title: t(r.recommend_reason), dataset: { act: 'route', id: r.id, fk: `route:${r.id}` },
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

/** 한 구간의 이동시간 문구: walk_min 이 없으면 "이동시간 확인 필요", 직선 추정이면 "예상"을 붙인다(D16 — 표시에만 쓴다). */
export function legTimeText(leg, t) {
  if (leg.walk_min == null) return t('map.leg.unknown');
  return leg.estimated ? t('map.leg.walk_est', { n: leg.walk_min }) : t('map.leg.walk', { n: leg.walk_min });
}

const SKIP_KEYS = { '좌표 없음': 'map.leg.skip.coord', '시각 없음': 'map.leg.skip.time' };

/**
 * 채팅 묶음의 "이동 구간" 영역(날짜별). v1 이거나 구간이 없으면 "이동 구간 정보 없음".
 * 장소 이름·이유는 서버 문자열이므로 사전 조회(t) 없이 텍스트 노드로만 넣는다. 이야기 길은 지어내지 않고 story_routes_note 만 밝힌다(D18).
 */
export function buildLegList(bundle, t, lang = 'ko') {
  const days = routeDays(bundle);
  const note = isV2Bundle(bundle) ? bundle.story_routes_note : null;
  const noteText = note ? (note[lang] ?? note.ko ?? note.en) : null;
  const hasAny = days.some((d) => d.legs.length || d.skipped.length);
  return h('section', { class: 'map-legs', 'aria-label': t('map.legs.title'), dataset: { module: 'legs' } },
    h('h3', { class: 'map-legs__title' }, t('map.legs.title')),
    hasAny ? days.filter((d) => d.legs.length || d.skipped.length).map((d) => h('div', { class: 'map-legs__day', dataset: { route: d.id } },
      h('div', { class: 'map-legs__dayhead' }, d.day ? `DAY ${d.day}` : d.id, d.date ? ` · ${d.date}` : ''),
      h('ul', { class: 'map-legs__list' },
        d.legs.map((l) => h('li', { class: 'map-leg', dataset: { estimated: String(l.estimated), walk: l.walk_min == null ? 'none' : 'some' } },
          h('span', { class: 'map-leg__path' }, `${l.from} → ${l.to}`),
          h('span', { class: 'map-leg__meta' }, ` · ${t('map.leg.straight', { m: l.straight_m })} · `, legTimeText(l, t)))),
        d.skipped.map((x) => h('li', { class: 'map-leg is-skipped', dataset: { skipped: 'true' } },
          h('span', { class: 'map-leg__path' }, x.to ? `${x.from} → ${x.to}` : x.from),
          h('span', { class: 'map-leg__meta' }, ` · ${SKIP_KEYS[x.reason] ? t(SKIP_KEYS[x.reason]) : (x.reason ?? '')}`)))))) : h('p', { class: 'cb-empty', role: 'status', dataset: { empty: 'legs' } }, t('map.legs.none')),
    noteText ? h('p', { class: 'cb-empty', dataset: { note: 'story-routes' } }, noteText) : null);
}
