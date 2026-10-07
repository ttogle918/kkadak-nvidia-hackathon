// map 모듈: 개략 지도(SVG) + 경로 A·B·C 카드 + 구간 목록. 계약: mount(root, ctx) -> {destroy()}.
// 읽는 상태: mode day selectedSeg selectedRoute selectedNow lang data loaded. 쓰는 액션: selectSeg selectRoute selectNow.
// 다른 components/* 를 import 하지 않는다. 변경이 있으면 가볍게 전체 재렌더하고, 포커스(data-fk)와 목록 스크롤은 되살린다.
import { h, on, render } from '../../lib/dom.js';
import { cardById, routeById } from '../../state/selectors.js';
import { VIEW_BOX, buildBaseMap } from './base-map.js';
import { buildLabel, nowLabelSpec, segLabelSpec, stripGlyph } from './labels.js';
import {
  approxRadius, buildNowPin, buildSegment, centroid, dayOpacity, layeredSegments, makeProjector, modeOpacity, pathD, segStyle,
} from './route-layer.js';
import { buildRouteCards, buildStepList } from './route-list.js';

const WATCH = (s) => [s.mode, s.day, s.selectedSeg, s.selectedRoute, s.selectedNow, s.lang, s.data, s.loaded];
const same = (a, b) => a.every((v, i) => Object.is(v, b[i]));

/** 지도 SVG. state 와 t 만으로 만드는 순수 렌더(노드 반환). */
export function buildMapSvg(state, t) {
  const { mode, day, selectedSeg, selectedRoute, selectedNow, lang, data } = state;
  const { itinerary, routes } = data;
  const cardOf = (id) => cardById(state, id);
  const op = modeOpacity(mode);
  const nowCard = cardOf(selectedNow);
  const dayOp = dayOpacity(day, nowCard);
  const oldOn = op.old > 0;
  const nowOn = op.now > 0;

  // 좌표 변환(샘플은 schematic 이라 그대로)
  const segs = layeredSegments(routes, selectedRoute);
  const spaceOf = (s) => cardOf(s.card_id)?.geometry?.space ?? 'schematic';
  const allGeo = segs.filter(({ seg }) => spaceOf(seg) !== 'schematic').flatMap(({ seg }) => seg.coords);
  const projFor = (space) => makeProjector(space, allGeo);

  const oldNodes = [];
  const oldLabels = [];
  for (const { seg, active } of segs) {
    const card = cardOf(seg.card_id);
    const pts = seg.coords.map(projFor(spaceOf(seg)));
    const selected = active && !!seg.card_id && seg.card_id === selectedSeg;
    const style = segStyle({ selected, weak: seg.weak, badge: card?.badge ?? null, hasStory: !!seg.card_id, dim: !active });
    oldNodes.push({ selected, node: buildSegment({
      d: pathD(pts), style, cardId: seg.card_id, selected, interactive: oldOn,
      label: t('map.aria.seg', { name: t(seg.name), badge: card ? stripGlyph(t(`badge.${card.badge}`)) : '', n: seg.walk_min }),
    }) });
    if (active && seg.label_xy && seg.card_id) {
      const glyph = card?.badge === '기록' ? '◆ ' : '◇ ';
      oldLabels.push({ selected, node: buildLabel(segLabelSpec({ text: glyph + t(seg.name), xy: seg.label_xy, selected, weak: seg.weak, lang })) });
    }
  }
  // 선택된 구간이 맨 위에 오도록
  oldNodes.sort((a, b) => Number(a.selected) - Number(b.selected));

  const lms = itinerary.landmarks ?? [];
  const lmLabel = (l) => (l.label ? t(l.label) : '');
  const poiNodes = lms.filter((l) => l.kind === 'poi').flatMap((l) => [
    h('g', { class: 'map-poi', transform: `translate(${l.xy[0]} ${l.xy[1]}) rotate(45)` }, h('rect', { x: -6, y: -6, width: 12, height: 12 })),
    h('text', { class: 'map-poi__label', x: l.xy[0] - 12, y: l.xy[1] + 4 }, lmLabel(l)),
  ]);
  const dotNodes = lms.filter((l) => l.kind === 'dot').flatMap((l) => [
    h('circle', { class: 'map-dot__halo', cx: l.xy[0], cy: l.xy[1], r: 14 }),
    h('circle', { class: 'map-dot', cx: l.xy[0], cy: l.xy[1], r: 6.5 }),
  ]);
  const anchorNodes = lms.filter((l) => l.kind === 'anchor').flatMap((l) => [
    h('rect', { class: 'map-anchor', x: l.xy[0] - 8, y: l.xy[1] - 8, width: 16, height: 16 }),
    h('text', { class: 'map-name', x: l.xy[0] + 14, y: l.xy[1] - 8 }, lmLabel(l)),
  ]);
  const hotelNodes = lms.filter((l) => l.kind === 'hotel').flatMap((l) => [
    h('rect', { class: 'map-hotel', x: l.xy[0] - 8, y: l.xy[1] - 8, width: 16, height: 16 }),
    h('text', { class: 'map-hotel__h', x: l.xy[0], y: l.xy[1] + 4 }, 'H'),
    h('text', { class: 'map-name map-name--sub', x: l.xy[0], y: l.xy[1] + 22, 'text-anchor': 'middle' }, lmLabel(l)),
  ]);
  const mutedNodes = lms.filter((l) => l.kind === 'muted').map((l) => h('circle', { class: 'map-muted', cx: l.xy[0], cy: l.xy[1], r: 6 }));
  const isMutedAt = (p) => lms.some((l) => l.kind === 'muted' && l.xy[0] === p[0] && l.xy[1] === p[1]);

  // 지금 카드: 지도에 그릴 수 있는 것(schematic 좌표)만. 같은 자리의 탈락 후보 점이 있으면 핀을 겹치지 않는다.
  const nowNodes = [];
  const nowLabels = [];
  for (const card of (state.data.cards ?? []).filter((c) => c.kind === 'now' && c.geometry?.coords?.length)) {
    const pts = card.geometry.coords.map(projFor(card.geometry.space ?? 'schematic'));
    if (card.geometry.type === 'point' && isMutedAt(pts[0])) continue;
    // 선택한 날의 카드가 아니면 흐리게(지도 전체 day 투명도와 별개)
    const dim = card.slot?.day === day ? 1 : 0.4;
    const [cx, cy] = centroid(pts);
    const name = t(card.place?.name ?? card.title);
    const labelText = `● ${name} · ${stripGlyph(t(`badge.${card.badge}`))}`;
    nowNodes.push(buildNowPin({
      card, pts, selected: card.id === selectedNow, interactive: nowOn, opacity: dim,
      label: t('map.aria.pin', { name: t(card.title), badge: stripGlyph(t(`badge.${card.badge}`)) }),
    }));
    const lop = dim;
    if (card.geometry.type === 'segment') {
      nowLabels.push({ op: lop, node: buildLabel(nowLabelSpec({ text: labelText, x: cx, y: cy - 2, lang, align: 'right', tone: 'now-dim' })) });
    } else if (card.geometry.type === 'approx') {
      const r = approxRadius(card.geometry.radius_m);
      nowLabels.push({ op: lop, node: buildLabel(nowLabelSpec({ text: labelText, x: cx - 80, y: cy - r - 7, lang, tone: 'now-line', dashed: true })) });
    }
    if (card.time_cost_min != null && card.geometry.type === 'segment') {
      nowLabels.push({ op: lop, node: buildLabel(nowLabelSpec({ text: t('map.label.plus', { n: card.time_cost_min }), x: cx + 12, y: cy + 10, lang, tone: 'now-on', minW: 70 })) });
    }
  }
  const wb = itinerary.walk_back;
  const walkNodes = wb?.coords?.length
    ? [h('path', { class: 'map-walkback', d: pathD(wb.coords), fill: 'none', 'stroke-dasharray': '7 6' })]
    : [];
  const walkLabel = wb?.label && wb.coords.length
    ? [buildLabel(nowLabelSpec({ text: t(wb.label), x: wb.coords.at(-1)[0] + 20, y: wb.coords.at(-1)[1] + 10, lang, kind: 'walk', tone: 'now-line' }))]
    : [];

  return h('svg', {
    class: 'map-svg', viewBox: VIEW_BOX, preserveAspectRatio: 'xMidYMid meet', role: 'group', 'aria-label': t('map.aria.map'),
    dataset: { mode, day },
  },
  buildBaseMap(t),
  h('g', { class: 'map-day', opacity: dayOp },
    h('g', { class: 'map-layer map-layer--now', opacity: op.now, 'pointer-events': nowOn ? null : 'none', 'aria-hidden': nowOn ? null : 'true' },
      walkNodes, nowNodes, mutedNodes),
    h('g', { class: 'map-layer map-layer--old', opacity: op.old, 'pointer-events': oldOn ? null : 'none', 'aria-hidden': oldOn ? null : 'true' },
      oldNodes.map((o) => o.node), poiNodes),
    dotNodes, anchorNodes),
  h('g', { class: 'map-fixed' }, hotelNodes),
  h('g', { class: 'map-day', opacity: dayOp },
    h('g', { class: 'map-labels map-labels--old', opacity: op.old, 'aria-hidden': 'true' }, oldLabels.map((l) => l.node)),
    h('g', { class: 'map-labels map-labels--now', opacity: op.now, 'aria-hidden': 'true' },
      nowLabels.map((l) => h('g', { opacity: l.op }, l.node)), walkLabel)));
}

/** 범례(선 모양으로 딱지를 구분 — 색에만 의존하지 않는다). */
function buildLegend(t) {
  const line = (dash, w, round) => h('svg', { width: 22, height: 6, 'aria-hidden': 'true' },
    h('path', { d: 'M1 3H21', 'stroke-width': w, 'stroke-dasharray': dash, 'stroke-linecap': round ? 'round' : null, class: 'map-legend__line' }));
  return h('div', { class: 'map-legend', 'aria-label': t('map.legend.title'), role: 'group' },
    h('span', {}, line(null, 4, true), t('badge.기록')),
    h('span', {}, line('9 4', 4, false), t('badge.전승')),
    h('span', {}, line('1 5', 3, true), t('badge.추정')),
    h('span', {}, h('i', { class: 'map-legend__approx' }), t('map.legend.approx')));
}

function buildSkeleton(t) {
  return h('div', { class: 'map-skeleton', role: 'status', 'aria-busy': 'true', 'aria-label': t('map.loading') },
    h('div', { class: 'map-skeleton__bar' }), h('div', { class: 'map-skeleton__bar' }), h('div', { class: 'map-skeleton__map' }));
}

/**
 * @param {HTMLElement} root app-shell 이 준 슬롯 div
 * @param {{store, api, t, actions}} ctx
 */
export function mount(root, ctx) {
  const { store, t, actions } = ctx;
  // 지도가 메인이므로 구간 목록은 접힌 채로 시작한다(데스크톱·모바일 공통)
  let stepsOpen = false;
  let destroyed = false;

  function draw() {
    if (destroyed) return;
    const prevScroll = root.querySelector?.('.map-steps__list')?.scrollTop ?? 0;
    const active = globalThis.document?.activeElement;
    const focusKey = active && root.contains(active) ? active.dataset?.fk : null;
    const s = store.getState();
    const ready = s.loaded && s.data.itinerary && s.data.routes?.length && s.data.cards;
    if (!ready) {
      render(root, h('div', { class: 'map' }, buildSkeleton(t)));
      return;
    }
    const route = routeById(s, s.selectedRoute) ?? s.data.routes[0];
    render(root, h('div', { class: 'map', dataset: { module: 'map' } },
      buildRouteCards(s.data.routes, route.id, t),
      h('div', { class: 'map-stage' }, buildMapSvg(s, t), buildLegend(t)),
      buildStepList({ route, selectedSeg: s.selectedSeg, cardOf: (id) => cardById(s, id), t, open: stepsOpen })));
    // 포커스·스크롤 복원
    const list = root.querySelector?.('.map-steps__list');
    if (list) list.scrollTop = prevScroll;
    if (focusKey && root.querySelectorAll) {
      const el = [...root.querySelectorAll('[data-fk]')].find((e) => e.dataset.fk === focusKey);
      el?.focus?.({ preventScroll: true });
    }
  }

  function act(el) {
    const d = el.dataset;
    if (d.act === 'seg') actions.selectSeg(d.card);
    else if (d.act === 'route') actions.selectRoute(d.id);
    else if (d.act === 'now') actions.selectNow(d.card);
    else if (d.act === 'toggle-steps') { stepsOpen = !stepsOpen; draw(); }
  }

  const offClick = on(root, 'click', '[data-act]', (_e, el) => act(el));
  // SVG 의 role=button 은 Enter/Space 를 직접 처리한다(HTML button 은 브라우저가 click 으로 바꿔 준다)
  const offKey = on(root, 'keydown', '[role="button"][data-act]', (e, el) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault?.(); act(el); }
  });
  const offStore = store.select(WATCH, draw, { equals: same, fire: true });

  return {
    destroy() {
      destroyed = true;
      offStore();
      offClick();
      offKey();
      root.replaceChildren();
    },
  };
}
