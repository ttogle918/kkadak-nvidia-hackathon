// timeline 순수 로직 — 목업의 tl 계산을 옮긴 것. 행 필터·상태는 state/selectors.js 의 timelineFor 를 쓴다.
import { timelineFor } from '../../state/selectors.js';

/**
 * status -> 라벨 키·기호. 색만으로 구분하지 않도록 선 모양(CSS data-status)과 라벨·기호를 함께 쓴다.
 * tagKey 가 null 이면 라벨을 따로 붙이지 않는다(빈 시간은 제목이 곧 라벨).
 */
export const STATUS_META = {
  original: { tagKey: 'timeline.original', glyph: '■' },
  free: { tagKey: null, glyph: '▨' },
  proposed: { tagKey: 'timeline.proposal', glyph: '◌' },
  added: { tagKey: 'timeline.added', glyph: '✓' },
  skipped: { tagKey: 'timeline.skipped', glyph: '–' },
};

/** 일정에 나오는 날짜 목록(anchors 의 day 와 timeline 의 day 의 합집합, 오름차순). */
export function dayTabs(itinerary) {
  const days = new Set();
  for (const a of itinerary?.anchors ?? []) if (Number.isInteger(a.day)) days.add(a.day);
  for (const d of itinerary?.timeline ?? []) if (Number.isInteger(d.day)) days.add(d.day);
  return [...days].sort((a, b) => a - b);
}

/** trip.from('YYYY-MM-DD') + (day-1) 일 -> 'M/D'. 형식이 틀리면 ''. */
export function dayDate(trip, day) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trip?.from ?? '');
  if (!m || !Number.isInteger(day)) return '';
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]) + day - 1));
  return `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
}

/** 그 날 방문지 이름(아직 {ko,en} 일 수 있다 — 호출자가 t 로 푼다). */
export function dayAnchorNames(itinerary, day) {
  return (itinerary?.anchors ?? []).filter((a) => a.type === 'visit' && a.day === day).map((a) => a.name);
}

/**
 * 화면용 값. 결정(added/skipped)은 selectedNow 카드의 제안 행에만 적용된다.
 * @returns {{day:number, date:string, tabs:number[], rows:object[], empty:boolean, anchors:object[]}}
 */
export function timelineView(state) {
  const it = state.data?.itinerary ?? null;
  const day = state.day;
  const rows = timelineFor(it, day, state).map((r) => ({ ...r, meta: STATUS_META[r.status] ?? STATUS_META.original }));
  return {
    day,
    date: dayDate(it?.trip, day),
    tabs: dayTabs(it),
    rows,
    empty: rows.length === 0,
    anchors: dayAnchorNames(it, day),
  };
}
