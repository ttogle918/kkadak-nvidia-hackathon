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

// 문제 코드 -> 사전 키. 서버 message 는 화면에 쓰지 않는다(내부 문구·세부가 새지 않게) — 코드별 고정 문구만.
// 코드 출처: domains/kcontext/schedule/understand.py · pipeline/run.py · backend/chat_story.py 의 _problem( 호출.
const K = 'bundle.problem.';
const PROBLEM_KEYS = {
  TIME_FORMAT: `${K}time`, TIME_NOT_IN_QUOTE: `${K}time`, TIME_WITHOUT_DATE: `${K}time`,
  DATE_FORMAT: `${K}date`, DATE_NOT_IN_QUOTE: `${K}date`, DATE_INVALID: `${K}date`,
  COORD_UNKNOWN: `${K}coord`, YEAR_ASSUMED: `${K}year_assumed`, OVERLAP: `${K}overlap`, LONG_SPAN: `${K}long_span`,
  DAY_UNTIMED: `${K}untimed`, FREE_SLOTS_INCOMPLETE: `${K}free_incomplete`,
  EVENTS_UNAVAILABLE: `${K}events`, TRUNCATED: `${K}truncated`,
  AMPM_ASSUMED: `${K}ampm`, NAME_PARTICLE_STRIPPED: `${K}particle`,
  BAD_FIELD_TYPE: `${K}partial`, CANDIDATE_BAD: `${K}dropped`, QUOTE_MISSING: `${K}dropped`, QUOTE_TOO_LONG: `${K}dropped`,
  QUOTE_NOT_FOUND: `${K}dropped`, NAME_NOT_IN_QUOTE: `${K}partial`, NAME_MISSING: `${K}partial`, ANCHOR_NO_NAME: `${K}partial`,
  TYPE_DOWNGRADED: `${K}type`, TYPE_UNKNOWN: `${K}type`,
  TRIP_INVALID: `${K}trip`, INPUT_EMPTY: `${K}input_empty`, INPUT_TOO_LONG: `${K}input_long`,
  INJECTION_BLOCKED: `${K}injection`, INPUT_SUSPICIOUS: `${K}suspicious`,
  LLM_FAILED: `${K}llm`, LLM_UNAVAILABLE: `${K}llm`, LLM_EMPTY: `${K}llm`, LLM_BAD_JSON: `${K}llm`, LLM_UNEXPECTED_SHAPE: `${K}llm`,
  TOO_MANY_ANCHORS: `${K}too_many`, NO_ANCHOR_VERIFIED: `${K}none_verified`,
  FIELD_DROPPED: `${K}field_dropped`, ROUTE_PROVIDER_REMOTE_REFUSED: `${K}route_off`,
};
/** MENTION_<종류> 는 접두어로 한 문구에 묶는다. */
const MENTION_KEY = `${K}mention`;
const GENERIC_KEY = `${K}generic`;
/** 사용자에게 보이지 않는 내부 동작 코드(재시도·캐시). */
export const HIDDEN_PROBLEM_CODES = ['LLM_RETRY', 'RETRY_SKIPPED_BUDGET', 'CACHE_UNAVAILABLE'];
/** 장소 이름을 붙일 수 있는 코드(이름 키는 `.named`). */
const NAMED = new Set(['COORD_UNKNOWN', 'NAME_PARTICLE_STRIPPED', 'OVERLAP']);

/**
 * 메시지에서 장소 이름을 뽑되, 묶음의 앵커 이름과 정확히 같은 것만 인정한다(아니면 null — 서버 문자열을 화면에 올리지 않는다).
 * COORD_UNKNOWN "이름: …" · NAME_PARTICLE_STRIPPED "원래 → 떼낸 이름: …" · OVERLAP "일정이 겹침: 이름 / 이름".
 */
function problemName(code, message, names) {
  const m = typeof message === 'string' ? message : '';
  let found = [];
  if (code === 'COORD_UNKNOWN') {
    const i = m.indexOf(': ');
    if (i > 0) found = [m.slice(0, i)];
  } else if (code === 'NAME_PARTICLE_STRIPPED') {
    const r = /^.+? → (.+?): /.exec(m);
    if (r) found = [r[1]];
  } else if (code === 'OVERLAP') {
    const r = /^일정이 겹침: (.+) \/ (.+)$/.exec(m);
    if (r) found = [r[1], r[2]];
  }
  return found.length && found.every((n) => names.has(n)) ? found.join(' · ') : null;
}

/**
 * problems -> [{code, key, params?}]. 서버 message 는 쓰지 않는다: 알려진 코드는 고정 문구, 내부 동작 코드는 뺀다, 모르는 코드는 일반 문구.
 * 같은 문구는 한 번만(장소 이름이 붙는 문구는 이름이 다르면 각각).
 */
export function problemLines(bundle) {
  const names = new Set((bundle?.itinerary?.anchors ?? []).map((a) => a.name));
  const seen = new Set();
  const out = [];
  for (const p of bundle?.problems ?? []) {
    const code = String(p.code ?? '');
    if (HIDDEN_PROBLEM_CODES.includes(code)) continue;
    let key = PROBLEM_KEYS[code] ?? (code.startsWith('MENTION_') ? MENTION_KEY : GENERIC_KEY);
    let params;
    if (NAMED.has(code)) {
      const name = problemName(code, p.message, names);
      if (name) { key = `${key}.named`; params = { name }; }
    }
    const id = `${key}|${params?.name ?? ''}`;
    if (seen.has(id)) continue;
    seen.add(id);
    out.push(params ? { code, key, params } : { code, key });
  }
  return out;
}

/** v2 묶음인가(근거 표시·이동 구간 목록의 기준). v1 이면 근거는 숨기고 이동 구간은 "정보 없음". */
export const isV2Bundle = (bundle) => bundle?.schema === 'kc-chat-bundle/v2';

/**
 * 선택한 항목의 근거. kind 가 'mention' 이면 rationale["mention:"+id], 'event' 면 events_rationale["event:"+id] 만 본다.
 * 정확히 일치하는 키만 찾는다(대체 탐색 없음). 없으면 null.
 */
export function rationaleFor(bundle, id, kind) {
  if (!isV2Bundle(bundle) || typeof id !== 'string' || !id) return null;
  const own = (map, key) => (map && Object.hasOwn(map, key) ? map[key] : null);
  if (kind === 'mention') return own(bundle.rationale, `mention:${id}`);
  if (kind === 'event') return own(bundle.events_rationale, `event:${id}`);
  return null;
}

/** 근거 목록 -> {chips, items} (rationale/logic.js 의 mergeRationale 과 같은 규칙: 같은 key 는 먼저 온 것). */
export function mergeBundleRationale(list) {
  const chips = [];
  const items = {};
  for (const r of list) {
    for (const c of r?.chips ?? []) if (!chips.some((x) => x.key === c.key)) chips.push(c);
    for (const [k, v] of Object.entries(r?.items ?? {})) if (!Object.hasOwn(items, k)) items[k] = v;
  }
  return { chips, items };
}

/** 이동 구간 목록용 값: v1·routes 없음 -> []. 날짜별 {id, day, date, legs, skipped}. */
export const routeDays = (bundle) => (isV2Bundle(bundle) ? bundle.routes ?? [] : []);

/**
 * 지도 점선 쌍: routes[].legs 의 from_ll·to_ll 로 만든다(목록과 같은 출처 — 정확히 일치).
 * 좌표가 같은 숙소 아닌 핀에 대응시키고, 좌표가 없거나 핀을 못 찾는 구간·skipped 쌍은 잇지 않는다.
 * "직선 연결(실제 길 아님)" 용 — v2 에 routes 가 있을 때만.
 */
export function pinLinks(bundle) {
  if (!routeDays(bundle).length) return [];
  const pins = bundlePins(bundle).filter((p) => p.type !== 'hotel');
  const find = (ll) => (Array.isArray(ll) ? pins.find((p) => p.lat === ll[0] && p.lng === ll[1]) : null);
  const out = [];
  for (const r of routeDays(bundle)) {
    for (const l of r.legs) {
      const a = find(l.from_ll);
      const b = find(l.to_ll);
      if (a && b && a.key !== b.key) out.push({ from: a.key, to: b.key, day: r.day });
    }
  }
  return out;
}

/**
 * 실록 언급 -> 카드 id. 서버가 언급마다 싣는 card_id 를 그대로 쓴다(추정하지 않는다). card_id 가 없는 언급은 맵에 없다 → 선택 버튼도 없다.
 * Map<mention 객체, card_id>.
 */
export function mentionCardIds(bundle) {
  const out = new Map();
  for (const r of bundle?.mentions?.anchors ?? []) {
    for (const m of r.mentions) if (m.card_id) out.set(m, m.card_id);
  }
  return out;
}

const MONTHS_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/**
 * 서버 시각(UTC ISO "…Z") -> 한국 시간 표시. ko "10월 10일 0:51" · en "Oct 10, 12:51 AM (KST)". 읽을 수 없으면 null(원문을 쓰지 않는다).
 */
export function formatServerTime(iso, lang = 'ko') {
  if (typeof iso !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$/.test(iso)) return null;
  const ms = Date.parse(iso);
  if (!Number.isFinite(ms)) return null;
  const d = new Date(ms + 9 * 3600000); // KST = UTC+9 (서머타임 없음)
  const mo = d.getUTCMonth();
  const day = d.getUTCDate();
  const h24 = d.getUTCHours();
  const mm = String(d.getUTCMinutes()).padStart(2, '0');
  if (lang === 'en') return `${MONTHS_EN[mo]} ${day}, ${h24 % 12 === 0 ? 12 : h24 % 12}:${mm} ${h24 < 12 ? 'AM' : 'PM'} (KST)`;
  return `${mo + 1}월 ${day}일 ${h24}:${mm}`;
}
