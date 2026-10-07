// 챗봇 일정 묶음(검증을 통과한 bundle)에서 화면용 값을 뽑는 순수 함수. DOM 을 만지지 않는다.
// 타임라인·지도·카드 모듈이 같은 규칙을 쓰도록 lib 에 둔다(모듈끼리 import 하지 않는다).
// 입력은 api/bundle.js 의 validateChatBundle 이 정리한 bundle 이다.

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
export const hasCoord = (a) => !!a && isNum(a.lat) && isNum(a.lng) && Math.abs(a.lat) <= 90 && Math.abs(a.lng) <= 180;

const hhmm = (ts) => /T(\d{2}:\d{2})/.exec(ts ?? '')?.[1] ?? null;
const ymd = (ts) => /^(\d{4}-\d{2}-\d{2})/.exec(ts ?? '')?.[1] ?? null;
const bothLang = (s) => ({ ko: s, en: s });

/** "HH:MM–HH:MM" / "HH:MM ~" / "" (시각을 모르면 빈 문자열). */
export function timeLabel(from, to) {
  const f = hhmm(from);
  const e = hhmm(to);
  if (f && e) return `${f}–${e}`;
  if (f) return `${f} ~`;
  return '';
}

const dayDiff = (a, b) => Math.round((Date.parse(`${a}T00:00:00Z`) - Date.parse(`${b}T00:00:00Z`)) / 86400000);

/** 날짜 계산의 기준일: trip.from, 없으면 앵커·빈 시간 시각 중 가장 이른 날짜. 없으면 null. */
function baseDate(bundle) {
  if (bundle?.trip?.from) return bundle.trip.from;
  const ds = [...(bundle?.itinerary?.anchors ?? []), ...(bundle?.itinerary?.free_slots ?? [])].map((x) => ymd(x.from)).filter(Boolean).sort();
  return ds[0] ?? null;
}

/** 시각 문자열 -> 몇째 날(1~). 기준일이 없거나 기준일보다 앞이면 null. */
function dayOfStamp(ts, base) {
  const d = ymd(ts);
  if (!d || !base) return null;
  const n = dayDiff(d, base) + 1;
  return n >= 1 ? n : null;
}

/** DAY 번호 → 날짜 'M/D'. day 0(날짜 미확인)이나 기준일 없음이면 ''. */
export function bundleDayDate(bundle, day) {
  const base = baseDate(bundle);
  if (!base || !Number.isInteger(day) || day < 1) return '';
  const d = new Date(Date.parse(`${base}T00:00:00Z`) + (day - 1) * 86400000);
  return `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
}

/**
 * 묶음의 일정 행 전체(날짜 미정은 day 0). 행: {id, day, kind:'anchor'|'free', status:'original'|'free',
 * time, sortKey, title:{ko,en}|string(사전 키), sub:{ko,en}|string|null, subKey?, timeUnknown}.
 * 호텔은 체크인·체크아웃 시각이 있으면 각 날짜에 한 행씩, 없으면 날짜 미정에 한 행.
 */
export function bundleRows(bundle) {
  const base = baseDate(bundle);
  const rows = [];
  (bundle?.itinerary?.anchors ?? []).forEach((a, i) => {
    const name = bothLang(a.name);
    if (a.type === 'hotel') {
      const din = dayOfStamp(a.from, base) ?? a.day;
      const dout = dayOfStamp(a.to, base);
      if (a.from || a.to) {
        if (a.from) rows.push({ id: `b_a${i}_in`, day: din ?? 0, kind: 'anchor', status: 'original', time: timeLabel(a.from, null), sortKey: a.from, title: name, sub: 'timeline.bundle.checkin', timeUnknown: !hhmm(a.from) });
        if (a.to) rows.push({ id: `b_a${i}_out`, day: dout ?? 0, kind: 'anchor', status: 'original', time: timeLabel(a.to, null), sortKey: a.to, title: name, sub: 'timeline.bundle.checkout', timeUnknown: !hhmm(a.to) });
        return;
      }
      rows.push({ id: `b_a${i}`, day: a.day ?? 0, kind: 'anchor', status: 'original', time: '', sortKey: '', title: name, sub: 'timeline.bundle.hotel', timeUnknown: false });
      return;
    }
    const day = a.day ?? dayOfStamp(a.from, base) ?? 0;
    const time = timeLabel(a.from, a.to);
    rows.push({ id: `b_a${i}`, day, kind: 'anchor', status: 'original', time, sortKey: a.from ?? '', title: name, sub: time ? null : 'timeline.bundle.no_time', timeUnknown: !time });
  });
  (bundle?.itinerary?.free_slots ?? []).forEach((f, i) => {
    const day = f.day ?? dayOfStamp(f.from, base) ?? 0;
    rows.push({
      id: `b_f${i}`, day, kind: 'free', status: 'free', time: timeLabel(f.from, f.to), sortKey: f.from ?? '',
      title: 'timeline.free', near: f.near, assumption: f.assumption, inferred: f.inferred, sub: null, timeUnknown: false,
    });
  });
  return rows;
}

/** 일정에 나오는 날짜 목록(오름차순, 날짜 미정 0 은 맨 뒤). */
export function bundleDays(bundle) {
  const ds = new Set(bundleRows(bundle).map((r) => r.day));
  const real = [...ds].filter((d) => d >= 1).sort((a, b) => a - b);
  return ds.has(0) ? [...real, 0] : real;
}

/** 그 날의 행(시각 있는 것 먼저 시각순, 없는 것은 입력 순서대로 뒤). */
export function bundleTimelineFor(bundle, day) {
  const rows = bundleRows(bundle).filter((r) => r.day === day);
  const timed = rows.filter((r) => r.sortKey).sort((a, b) => (a.sortKey < b.sortKey ? -1 : a.sortKey > b.sortKey ? 1 : 0));
  return [...timed, ...rows.filter((r) => !r.sortKey)];
}

/** 이름이 같은 앵커의 실록 언급 묶음({anchor, mentions, found_articles, found_truncated}) 또는 null. */
export function mentionEntryFor(bundle, name) {
  return (bundle?.mentions?.anchors ?? []).find((r) => r.anchor.name === name) ?? null;
}

/** 지도 핀: 좌표(lat/lng)가 있는 앵커만. 좌표 없는 앵커는 여기에 없다(목록·카드에만 나온다). */
export function bundlePins(bundle) {
  const pins = [];
  (bundle?.itinerary?.anchors ?? []).forEach((a, i) => {
    if (!hasCoord(a)) return;
    const entry = mentionEntryFor(bundle, a.name);
    const mentions = entry?.mentions ?? [];
    pins.push({
      key: `pin${i}`, name: a.name, type: a.type, day: a.day, lat: a.lat, lng: a.lng, mentions,
      count: entry?.found_articles ?? mentions.length,
      atLeast: !!entry?.found_truncated,
    });
  });
  return pins;
}

/** 정보창에 들어갈 내용(문자열만). 상위 1건의 왕·날짜(음력 표기 그대로)·한글 요약·한문 원문·출처 태그·링크. */
export function pinInfo(pin) {
  const top = pin.mentions[0] ?? null;
  return {
    name: pin.name,
    count: pin.count,
    atLeast: pin.atLeast,
    top: top && {
      king: top.king, dateLabel: top.date_label, summary: top.title_summary, quote: top.quote,
      tier: top.tier, sourceName: top.source_name, url: top.url,
    },
  };
}

/** 앵커별 실록 언급 카드 묶음(언급이 있는 앵커만, 일정 순서대로). 같은 이름이 두 번 나와도 한 번만. */
export function mentionGroups(bundle) {
  const seen = new Set();
  const out = [];
  for (const a of bundle?.itinerary?.anchors ?? []) {
    if (seen.has(a.name)) continue;
    seen.add(a.name);
    const entry = mentionEntryFor(bundle, a.name);
    if (entry?.mentions.length) out.push({ name: a.name, day: a.day, count: entry.found_articles ?? entry.mentions.length, atLeast: !!entry.found_truncated, mentions: entry.mentions });
  }
  return out;
}

/** 행사 카드 상태: 목록과 "아직 못 찾음" 여부. events 가 null(검색 불가)이어도 비어 있음으로 본다 — 지어내지 않는다. */
export function eventsView(bundle) {
  const list = bundle?.events?.events ?? [];
  return { items: list.map((e) => ({ ...e, unverified: e.tier == null || e.tier === 'C' })), empty: list.length === 0, unavailable: bundle?.events == null };
}

const PROBLEM_KEYS = {
  TIME_FORMAT: 'bundle.problem.time', TIME_NOT_IN_QUOTE: 'bundle.problem.time', TIME_WITHOUT_DATE: 'bundle.problem.time',
  DATE_FORMAT: 'bundle.problem.date', DATE_NOT_IN_QUOTE: 'bundle.problem.date', DATE_INVALID: 'bundle.problem.date',
  COORD_UNKNOWN: 'bundle.problem.coord', OVERLAP: 'bundle.problem.overlap', LONG_SPAN: 'bundle.problem.long_span',
  DAY_UNTIMED: 'bundle.problem.untimed', FREE_SLOTS_INCOMPLETE: 'bundle.problem.free_incomplete',
  EVENTS_UNAVAILABLE: 'bundle.problem.events', TRUNCATED: 'bundle.problem.truncated',
};

/** problems -> [{code, key|null, message}]. key 가 있으면 화면이 사전 문구를 쓰고, 없으면 서버 message 를 그대로(textContent 로) 보인다. 같은 key 는 한 번만. */
export function problemLines(bundle) {
  const seen = new Set();
  const out = [];
  for (const p of bundle?.problems ?? []) {
    const key = PROBLEM_KEYS[p.code] ?? null;
    if (key) {
      if (seen.has(key)) continue;
      seen.add(key);
    }
    out.push({ code: p.code, key, message: p.message });
  }
  return out;
}
