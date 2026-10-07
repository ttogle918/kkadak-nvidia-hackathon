// 경로 구간·지금 레이어 계산(순수 함수)과 SVG 노드 빌더.
// 규칙: 옛날/지금 레이어는 mode 로, 지도 전체는 day 로 투명도를 바꾼다. 구간 선 모양은 딱지·weak 로 정한다(색만으로 구분하지 않는다).
import { h } from '../../lib/dom.js';

/** mode -> 레이어 투명도. 보이지 않는 레이어는 클릭·포커스도 막는다(호출자가 interactive 로 판단). */
export function modeOpacity(mode) {
  return { old: mode === 'now' ? 0 : 1, now: mode === 'old' ? 0 : 1 };
}

/** day -> 지도 전체 투명도. 샘플 데이터는 selectedNow 카드가 속한 날(slot.day, 없으면 1일차)만 또렷하고 나머지는 흐리다(목업 0.12). */
export function dayOpacity(day, nowCard) {
  return (nowCard?.slot?.day ?? 1) === day ? 1 : 0.12;
}

/**
 * 구간 한 개의 선 스타일.
 * - 이야기 있음: 기록=실선 · 전승=긴 점선 · 추정(또는 weak)=점선(점). 선택하면 +3 굵게·불투명·헤일로.
 * - 이야기 없음(card_id=null): 가늘고 흐린 회색, 클릭 불가.
 * - dim: 선택하지 않은 경로의 구간 — 겹쳐 그리되 흐리고 클릭 불가.
 */
export function segStyle({ selected = false, weak = false, badge = null, hasStory = true, dim = false }) {
  if (!hasStory) {
    return { w: 4, op: dim ? 0.2 : 0.55, halo: 0, dash: 'none', clickable: false, tone: 'plain' };
  }
  let w = 6;
  let dash = 'none';
  if (weak || badge === '추정') { w = 5; dash = '1 9'; } else if (badge === '전승') dash = '13 6';
  if (dim) return { w, op: 0.25, halo: 0, dash, clickable: false, tone: 'old' };
  return { w: selected ? w + 3 : w, op: selected ? 1 : 0.78, halo: selected ? 0.9 : 0.55, dash, clickable: true, tone: 'old' };
}

/** [x,y] 배열 -> SVG path d. */
export function pathD(points) {
  return points.map(([x, y], i) => `${i ? 'L' : 'M'}${x} ${y}`).join(' ');
}

/**
 * 좌표 변환기. 'schematic' 이면 [x,y] 그대로, 그 외(실제 API 의 [lat,lng])는 모든 점의 bbox 를 지도 안쪽(40..560 × 60..640)에 맞춘다.
 * 샘플은 lat/lng 가 없다 — 실제 좌표를 지어내지 않고, 실제 API 가 올 때를 위한 대비일 뿐이다.
 */
export function makeProjector(space, allPoints) {
  if (space === 'schematic' || !allPoints.length) return (p) => p;
  const lats = allPoints.map((p) => p[0]);
  const lngs = allPoints.map((p) => p[1]);
  const [la0, la1, ln0, ln1] = [Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)];
  const sc = Math.min(520 / Math.max(ln1 - ln0, 1e-9), 580 / Math.max(la1 - la0, 1e-9));
  return ([lat, lng]) => [Math.round(40 + (lng - ln0) * sc), Math.round(640 - (lat - la0) * sc)];
}

/** 구간 식별 키(경로 사이 같은 구간을 한 번만 그리려고). */
const segKey = (s) => s.card_id ?? JSON.stringify(s.coords);

/**
 * 그릴 구간 목록: 선택하지 않은 경로에만 있는 구간(dim) 먼저, 선택 경로 구간(active)을 위에.
 * @returns {{seg, routeId, active:boolean}[]}
 */
export function layeredSegments(routes, selectedRouteId) {
  const sel = routes.find((r) => r.id === selectedRouteId) ?? routes[0];
  if (!sel) return [];
  const have = new Set(sel.segments.map(segKey));
  const out = [];
  for (const r of routes) {
    if (r === sel) continue;
    for (const s of r.segments) {
      if (have.has(segKey(s))) continue;
      have.add(segKey(s));
      out.push({ seg: s, routeId: r.id, active: false });
    }
  }
  return [...out, ...sel.segments.map((s) => ({ seg: s, routeId: sel.id, active: true }))];
}

/** 점들의 중심(평균). */
export function centroid(points) {
  const n = points.length || 1;
  return [Math.round(points.reduce((a, p) => a + p[0], 0) / n), Math.round(points.reduce((a, p) => a + p[1], 0) / n)];
}

/** 선택한 경로 구간 한 개의 노드. 이야기 있는 구간만 button 역할을 갖는다. */
export function buildSegment({ d, style, cardId, label, selected, interactive }) {
  const clickable = style.clickable && interactive && cardId;
  return h('g', {
    class: ['map-seg', `map-seg--${style.tone}`, selected && 'is-selected', !clickable && 'is-static'],
    role: clickable ? 'button' : null,
    tabindex: clickable ? '0' : null,
    'aria-label': clickable ? label : null,
    'aria-pressed': clickable ? String(!!selected) : null,
    'aria-hidden': clickable ? null : 'true',
    dataset: clickable ? { act: 'seg', card: cardId, fk: `seg:${cardId}` } : null,
  },
  h('path', { class: 'map-seg__halo', d, 'stroke-opacity': style.halo, 'stroke-width': 14, fill: 'none' }),
  h('path', {
    class: 'map-seg__line', d, 'stroke-width': style.w, 'stroke-opacity': style.op, fill: 'none',
    'stroke-dasharray': style.dash === 'none' ? null : style.dash,
  }),
  clickable ? h('path', { class: 'map-seg__hit', d, 'stroke-width': 22, fill: 'none' }) : null);
}

const GLYPH = { 확인됨: '✓', '확인 필요': '!', 보류: 'Ⅱ' };
export const nowGlyph = (badge) => GLYPH[badge] ?? '●';

/**
 * 지금 카드 핀. geometry.type: segment=구역(굵은 반투명 + 점선) · approx=대략 원(점선 테두리 + 기호) · point=링.
 * @param {{card, pts:number[][], selected:boolean, interactive:boolean, label:string, opacity:number}} a
 */
export function buildNowPin({ card, pts, selected, interactive, label, opacity }) {
  const type = card.geometry?.type;
  const [cx, cy] = centroid(pts);
  let shape;
  if (type === 'segment' && pts.length > 1) {
    const d = pathD(pts);
    shape = [
      h('path', { class: 'map-zone__halo', d, 'stroke-width': 26, fill: 'none', 'stroke-linecap': 'round' }),
      h('path', { class: 'map-zone__line', d, 'stroke-width': 3, fill: 'none', 'stroke-dasharray': '1 7', 'stroke-linecap': 'round' }),
    ];
  } else if (type === 'approx') {
    const r = approxRadius(card.geometry.radius_m);
    shape = [
      h('circle', { class: 'map-approx__area', cx, cy, r, 'stroke-dasharray': '4 4' }),
      h('circle', { class: 'map-approx__core', cx, cy, r: 9 }),
      h('text', { class: 'map-approx__glyph', x: cx, y: cy + 4 }, nowGlyph(card.badge)),
    ];
  } else {
    shape = [h('circle', { class: 'map-point__ring', cx, cy, r: 8 })];
  }
  return h('g', {
    class: ['map-now', `map-now--${type ?? 'point'}`, selected && 'is-selected'],
    role: interactive ? 'button' : null, tabindex: interactive ? '0' : null,
    'aria-label': interactive ? label : null, 'aria-pressed': interactive ? String(!!selected) : null,
    'aria-hidden': interactive ? null : 'true',
    opacity,
    dataset: interactive ? { act: 'now', card: card.id, fk: `now:${card.id}` } : null,
  }, shape, interactive ? h('circle', { class: 'map-now__hit', cx, cy, r: 26 }) : null);
}

/** 대략 위치의 반지름(svg px). 샘플 radius_m 150 -> 45(목업은 44). */
export function approxRadius(radiusM) {
  return Math.min(60, Math.max(20, Math.round((radiusM ?? 150) * 0.3)));
}
