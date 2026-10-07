// 챗봇 일정 묶음(kc-chat-bundle/v1) 검증·정리. 계약: docs/chat-bundle.contract.md
// 서버가 준 모든 문자열은 신뢰하지 않는다 — 형태가 어긋나면 묶음 전체를 버리고(ok:false), 맞으면 문자열 상한으로 자른 복사본만 쓴다.
// url 은 http/https 만 남긴다(그 외 스킴은 링크 없이 null — 기록 자체는 보인다). 이 파일은 DOM 을 만지지 않는다.

export const BUNDLE_SCHEMA = 'kc-chat-bundle/v1';
export const CONTEXT_SCHEMA = 'chat-context/v1';

/** 문자열 상한(글자 수). 넘으면 잘라 '…' 를 붙인다. */
export const CAP = { name: 80, short: 60, text: 300, quote: 500, url: 500, id: 120, note: 300 };
export const MAX = { anchors: 20, mentionsPerAnchor: 5, events: 30, problems: 30, freeSlots: 40 };
const TIERS = ['S', 'A', 'B', 'C', 'D'];

class Bad extends Error {}
const bad = (why) => { throw new Bad(why); };

export function clip(s, n) {
  const v = String(s);
  return v.length > n ? `${v.slice(0, n - 1)}…` : v;
}

/** http/https 절대 URL 만 통과. 그 외(javascript:, data:, 상대 경로 …)는 null. */
export function safeUrl(u) {
  if (typeof u !== 'string' || !u || u.length > 2000) return null;
  try {
    const p = new URL(u);
    return p.protocol === 'http:' || p.protocol === 'https:' ? p.href : null;
  } catch {
    return null;
  }
}

const isObj = (v) => v != null && typeof v === 'object' && !Array.isArray(v);
const str = (v, cap) => {
  if (v == null) return null;
  if (typeof v !== 'string') bad('문자열이 아님');
  return clip(v, cap);
};
const optStr = (v, cap) => (v == null || v === '' ? null : str(v, cap));
const int = (v) => {
  if (v == null) return null;
  if (!Number.isInteger(v)) bad('정수가 아님');
  return v;
};
const coord = (v, lim) => (typeof v === 'number' && Number.isFinite(v) && Math.abs(v) <= lim ? v : null);
const stamp = (v) => (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$/.test(v) ? v : null);
const date = (v) => (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : null);
const tier = (v) => (TIERS.includes(v) ? v : null);
const arr = (v, max) => {
  if (v == null) return [];
  if (!Array.isArray(v)) bad('배열이 아님');
  return v.slice(0, max);
};
const bi = (v, cap) => {
  if (v == null) return null;
  if (typeof v === 'string') return { ko: clip(v, cap), en: clip(v, cap) };
  if (!isObj(v)) bad('{ko,en} 가 아님');
  const ko = optStr(v.ko, cap);
  const en = optStr(v.en, cap);
  return ko || en ? { ko: ko ?? en, en: en ?? ko } : null;
};

function anchor(a) {
  if (!isObj(a)) bad('anchor 가 객체가 아님');
  const name = optStr(a.name, CAP.name);
  if (!name) return null; // 이름 없는 앵커는 보여줄 것이 없다
  return {
    type: a.type === 'hotel' ? 'hotel' : 'visit',
    name,
    day: int(a.day),
    from: stamp(a.from),
    to: stamp(a.to),
    lat: coord(a.lat, 90),
    lng: coord(a.lng, 180),
    source_quote: optStr(a.source_quote, CAP.text),
  };
}

function freeSlot(f) {
  if (!isObj(f)) bad('free_slot 이 객체가 아님');
  return {
    day: int(f.day),
    from: stamp(f.from),
    to: stamp(f.to),
    near: bi(f.near, CAP.name),
    inferred: f.inferred === true,
    assumption: bi(f.assumption, CAP.text),
  };
}

function mention(m) {
  if (!isObj(m)) bad('mention 이 객체가 아님');
  const src = isObj(m.source) ? m.source : {};
  const out = {
    article_id: optStr(m.article_id, CAP.id),
    king: optStr(m.king, CAP.short),
    date_label: optStr(m.date_label, CAP.short),
    title_summary: optStr(m.title_summary, CAP.text),
    quote: optStr(m.quote, CAP.quote),
    lang: optStr(m.lang, 10),
    locator: optStr(m.locator, CAP.text),
    url: safeUrl(m.url) ? clip(safeUrl(m.url), CAP.url) : null,
    tier: tier(m.tier ?? src.tier),
    source_name: optStr(src.name, CAP.name),
  };
  return out.quote || out.title_summary ? out : null;
}

function mentionsDoc(d) {
  if (d == null) return { anchors: [] };
  if (!isObj(d)) bad('mentions 가 객체가 아님');
  const anchors = arr(d.anchors, MAX.anchors).map((r) => {
    if (!isObj(r) || !isObj(r.anchor)) bad('mentions.anchors[] 형식');
    const name = optStr(r.anchor.name, CAP.name);
    if (!name) return null;
    const found = Number.isInteger(r.found_articles) && r.found_articles >= 0 ? r.found_articles : null;
    return {
      anchor: { name, lat: coord(r.anchor.lat, 90), lng: coord(r.anchor.lng, 180), day: int(r.anchor.day) },
      mentions: arr(r.mentions, MAX.mentionsPerAnchor).map(mention).filter(Boolean),
      found_articles: found,
      found_truncated: r.found_truncated === true,
    };
  });
  return { anchors: anchors.filter(Boolean) };
}

function eventEntry(e) {
  if (!isObj(e)) bad('event 가 객체가 아님');
  const title = optStr(e.title, CAP.text);
  if (!title) return null;
  const sch = isObj(e.schedule) ? e.schedule : {};
  const ven = isObj(e.venue) ? e.venue : {};
  const links = arr(e.links, 5).map((l) => {
    if (!isObj(l)) bad('event.links[] 형식');
    return { url: safeUrl(l.url) ? clip(safeUrl(l.url), CAP.url) : null, source_name: optStr(l.source_name, CAP.name), kind: optStr(l.kind, CAP.short), tier: tier(l.tier) };
  });
  return {
    id: optStr(e.id, CAP.id),
    title,
    start_date: date(sch.start_date) ?? date(e.start_date),
    end_date: date(sch.end_date) ?? date(e.end_date),
    venue_name: optStr(ven.name, CAP.name),
    tier: tier(e.tier) ?? links.find((l) => l.tier)?.tier ?? null,
    links,
    demo: e.demo === true,
  };
}

function eventsDoc(d) {
  if (d == null) return null;
  if (!isObj(d) || !Array.isArray(d.events)) bad('events 형식');
  return {
    events: arr(d.events, MAX.events).map(eventEntry).filter(Boolean),
    problems: arr(d.problems, MAX.problems).map(problem),
    coverage_note: isObj(d.coverage) ? optStr(d.coverage.note, CAP.text) : null,
  };
}

function problem(p) {
  if (!isObj(p)) bad('problem 형식');
  return { code: optStr(p.code, CAP.short) ?? 'UNKNOWN', message: optStr(p.message, CAP.text) ?? '' };
}

/**
 * 응답의 bundle 을 검증한다.
 * @returns {{ok:true, bundle:object}|{ok:false, reason:string}} 정리된 복사본(상한으로 자른 문자열, http/https 만 남긴 url)
 */
export function validateChatBundle(raw) {
  try {
    if (!isObj(raw)) bad('객체가 아님');
    if (raw.schema !== BUNDLE_SCHEMA) bad('schema 불일치');
    if (!isObj(raw.itinerary) || !Array.isArray(raw.itinerary.anchors)) bad('itinerary.anchors 가 배열이 아님');
    const trip = isObj(raw.trip) && date(raw.trip.from) && date(raw.trip.to) ? { from: raw.trip.from, to: raw.trip.to } : null;
    return {
      ok: true,
      bundle: {
        schema: BUNDLE_SCHEMA,
        generated_at: optStr(raw.generated_at, CAP.short),
        status: raw.status === 'no_anchors' ? 'no_anchors' : 'ok',
        sample: raw.sample === true, // 화면 예시(mock fixture) 표시용 — 서버 계약 필드가 아니다
        trip,
        itinerary: {
          anchors: arr(raw.itinerary.anchors, MAX.anchors).map(anchor).filter(Boolean),
          free_slots: arr(raw.itinerary.free_slots, MAX.freeSlots).map(freeSlot),
        },
        mentions: mentionsDoc(raw.mentions),
        events: eventsDoc(raw.events),
        problems: arr(raw.problems, MAX.problems).map(problem),
        coverage_note: optStr(raw.coverage_note, CAP.text),
      },
    };
  } catch (e) {
    if (e instanceof Bad) return { ok: false, reason: e.message };
    throw e;
  }
}

/**
 * 요청에 실을 context 를 만든다(chat-context/v1). 허용 키만: schema·lang·trip{from,to}.
 * trip 이 유효하지 않으면 trip 없이 보낸다. 신원 필드는 없다.
 */
export function buildChatContext({ lang, trip } = {}) {
  const ctx = { schema: CONTEXT_SCHEMA, lang: lang === 'en' ? 'en' : 'ko' };
  if (isObj(trip) && date(trip.from) && date(trip.to) && trip.from <= trip.to) ctx.trip = { from: trip.from, to: trip.to };
  return ctx;
}
