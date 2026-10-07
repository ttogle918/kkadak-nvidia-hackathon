// 행사 찾기 화면의 순수 로직(DOM 없음). 날짜는 Asia/Seoul 기준 문자열(YYYY-MM-DD / HH:MM)로만 다룬다.
// 모르는 값은 추측하지 않고 '확인 필요' 문구로 바꾼다. 계산(이동시간·운영일)은 서버가 하고 여기서는 표시만 한다.

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;
const toMin = (hhmm) => Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5));

export function isDate(s) {
  if (typeof s !== 'string' || !DATE_RE.test(s)) return false;
  const d = new Date(`${s}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
}
export const isTime = (s) => typeof s === 'string' && TIME_RE.test(s);

/** 오늘 날짜(서울). 브라우저 시간대가 달라도 서울 날짜를 준다. */
export function seoulToday(now = new Date()) {
  const p = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit' }).format(now);
  return p; // en-CA 는 YYYY-MM-DD
}

export function addDays(date, n) {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

// ---------- 입력 검증·요청 만들기 ----------
const num = (v) => (v === '' || v == null ? null : Number(v));

/** 폼 값 → {ok, errors, request}. errors 의 키: dates, origin, max_extra, duration. */
export function validateForm(form, itinerary = []) {
  const errors = {};
  if (!isDate(form.from) || !isDate(form.to) || form.from > form.to) errors.dates = 'form.error.dates';
  const lat = num(form.lat);
  const lng = num(form.lng);
  if ((lat == null) !== (lng == null) || (lat != null && !(Number.isFinite(lat) && lat >= -90 && lat <= 90 && Number.isFinite(lng) && lng >= -180 && lng <= 180))) {
    errors.origin = 'form.error.number';
  }
  const maxExtra = form.maxExtra === '' || form.maxExtra == null ? 30 : Number(form.maxExtra);
  if (!Number.isInteger(maxExtra) || maxExtra < 0 || maxExtra > 240) errors.max_extra = 'form.error.number';
  const dur = num(form.duration);
  if (dur != null && !(Number.isInteger(dur) && dur >= 1 && dur <= 720)) errors.duration = 'form.error.number';
  if (Object.keys(errors).length) return { ok: false, errors, request: null };
  const interests = [...new Set(String(form.interests ?? '').split(',').map((x) => x.trim()).filter(Boolean))].map((x) => x.slice(0, 40)).slice(0, 20);
  const request = {
    trip: { from: form.from, to: form.to },
    interests,
    max_extra_minutes: maxExtra,
    require_interest: !!form.requireInterest,
    itinerary: planPayload(itinerary),
  };
  const name = String(form.originName ?? '').trim().slice(0, 80);
  if (lat != null || name) request.origin = { name, lat, lng };
  if (dur != null) request.assumed_duration_min = dur;
  return { ok: true, errors: {}, request };
}

/** 서버로 보낼 일정(표시용 키는 보존하되 서버가 받는 키만 남긴다: id,title,date,start,end,lat,lng + source/entry_id/end_assumed). */
export function planPayload(items) {
  return items.map((p) => {
    const o = { id: p.id, title: p.title ?? '', date: p.date, start: p.start, end: p.end };
    if (typeof p.lat === 'number' && typeof p.lng === 'number') { o.lat = p.lat; o.lng = p.lng; }
    for (const k of ['source', 'entry_id', 'end_assumed']) if (p[k] != null) o[k] = p[k];
    return o;
  });
}

export function validatePlan(p) {
  if (!isDate(p.date) || !isTime(p.start) || !isTime(p.end) || toMin(p.start) >= toMin(p.end)) return false;
  if (p.lat != null && p.lat !== '' && !(Number.isFinite(Number(p.lat)) && Math.abs(Number(p.lat)) <= 90)) return false;
  return true;
}

let planSeq = 0;
export function newPlan(p) {
  const lat = num(p.lat);
  const lng = num(p.lng);
  const plan = { id: `plan_${Date.now().toString(36)}_${++planSeq}`, title: String(p.title ?? '').trim().slice(0, 120), date: p.date, start: p.start, end: p.end, source: 'user' };
  if (lat != null && lng != null) { plan.lat = lat; plan.lng = lng; }
  return plan;
}

export const sortPlans = (items) => [...items].sort((a, b) => (a.date + a.start).localeCompare(b.date + b.start));

// ---------- 표시 문구 ----------
const unknownText = (t) => t('common.unknown');

export function weekdayList(days, t) {
  return days.map((d) => t(`weekday.${d}`)).join('·');
}

export function eventWhen(ev, t) {
  const s = ev.schedule;
  const range = s.start_date ? (s.end_date && s.end_date !== s.start_date ? `${s.start_date} ~ ${s.end_date}` : s.start_date) : unknownText(t);
  const sessions = s.sessions.length
    ? s.sessions.map((x) => `${x.date} ${x.start_time ?? ''}${x.end_time ? `–${x.end_time}` : ''}`.trim()).join(' / ')
    : '';
  return { range, sessions };
}

export function closuresText(ev, t) {
  const s = ev.schedule;
  const parts = [];
  if (s.weekly_closed_days.length) parts.push(`${weekdayList(s.weekly_closed_days, t)}`);
  if (s.closed_dates.length) parts.push(s.closed_dates.join(', '));
  if (s.holiday_rule) parts.push(s.holiday_rule);
  return parts.join(' · ');
}

export const priceLabel = (ev, t) => {
  const p = ev.price;
  return { kind: t(`price.${p.kind}`), text: p.text };
};

export function reservationInfo(ev, t) {
  const r = ev.reservation;
  return {
    required: t(`res.required.${r.required}`),
    status: t(`res.${r.status}`),
    link: r.link || '',
    deadline: r.deadline || '',
    note: r.note || '',
    tone: r.status === 'closed' || r.status === 'full' ? 'bad' : r.status === 'open' || r.status === 'not_required' ? 'ok' : 'warn',
  };
}

/** 참여조건 배지들. 확인되지 않은 것을 가능으로 표시하지 않는다. */
export function participationBadges(ev, t) {
  const p = ev.participation;
  const out = [{ kind: p.status, tone: p.status === 'restricted' ? 'bad' : p.status === 'stated_open' ? 'ok' : 'warn', text: t(`part.${p.status}`) }];
  out.push({ kind: `foreigner_${p.foreigner}`, tone: p.foreigner === 'allowed' ? 'ok' : p.foreigner === 'excluded' ? 'bad' : 'warn', text: t(`part.foreigner.${p.foreigner}`) });
  return out;
}

export const verificationBadge = (ev, t) => ({
  kind: ev.verification,
  tone: ev.verification === 'verified' ? 'ok' : ev.verification === 'conflict' ? 'bad' : 'warn',
  text: t(`verify.${ev.verification}`),
});

export function languageInfo(ev, t) {
  const l = ev.language;
  return {
    event: l.languages.length ? l.languages.join(', ') : t('lang.event.unknown'),
    guidance: t(`lang.guidance.${l.english_guidance}`),
    subtitles: t(`lang.subtitles.${l.english_subtitles}`),
    site: t(`lang.site.${l.site_english_page}`), // 홈페이지 영어 페이지는 행사 진행 언어와 다르다 — 별도 줄
  };
}

export const needsCheckLabels = (ev, t) => ev.needs_check.map((k) => t(`check.${k}`)).filter((x) => !x.startsWith('check.'));

export function suggestionLabels(s, t) {
  const extra = s.extra_minutes != null ? t('sug.extra', { n: s.extra_minutes }) : t('sug.extra.unknown');
  return {
    extra,
    estimated: s.route.estimated && s.extra_minutes != null ? ` (${t('sug.estimated')})` : '',
    basis: t(`sug.basis.${s.extra_basis}`),
    status: t(`sug.status.${s.status}`),
    after: s.after_item_id ? null : t('sug.first'),
    provider: s.route.provider === 'none' ? t('sug.none_provider') : `${t('sug.provider')}: ${s.route.provider}`,
    tone: s.status === 'fit' ? 'ok' : s.status === 'no_fit' ? 'bad' : 'warn',
  };
}

// ---------- 변경 표시 ----------
export function describeChange(c, t) {
  const f = t(`field.${c.field}`);
  const show = (v) => (v == null || v === '' || (Array.isArray(v) && !v.length) ? t('common.none') : Array.isArray(v) ? JSON.stringify(v) : String(v));
  return `${f.startsWith('field.') ? c.field : f}: ${show(c.old)} → ${show(c.new)}`;
}

// ---------- 저장한 행사 ----------
export function saveEvent(saved, ev, nowIso) {
  return { ...saved, [ev.id]: { id: ev.id, title: ev.title, savedAt: nowIso, seenAt: nowIso } };
}
export function unsaveEvent(saved, id) {
  const next = { ...saved };
  delete next[id];
  return next;
}
/** 서버가 준 변경 목록을 저장 항목에 붙인다. seenAt 이후 변경만 배지가 된다. */
export function applyChanges(saved, serverSaved) {
  const by = Object.fromEntries(serverSaved.map((s) => [s.entry_id, s]));
  return Object.fromEntries(Object.entries(saved).map(([id, it]) => {
    const s = by[id];
    return [id, { ...it, changes: s ? s.changes.filter((c) => c.detected_at > it.seenAt) : [], hasMajor: !!s?.has_major }];
  }));
}
export function ackChanges(saved, id, nowIso) {
  return saved[id] ? { ...saved, [id]: { ...saved[id], seenAt: nowIso, changes: [], hasMajor: false } } : saved;
}
export const oldestSeen = (saved) => Object.values(saved).map((x) => x.seenAt).sort()[0] ?? null;
export const nowSeoulIso = (now = new Date()) => {
  const f = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(now);
  return f.replace(' ', 'T');
};

// ---------- 지도(타일 없음, 상대 위치) ----------
/** 위·경도를 SVG 좌표로. 경도는 cos(위도) 로 줄여 비율을 맞춘다. 점이 하나뿐이면 가운데. */
export function projectPoints(points, { width = 360, height = 240, pad = 28 } = {}) {
  const pts = points.filter((p) => typeof p.lat === 'number' && typeof p.lng === 'number');
  if (!pts.length) return [];
  const lat0 = (pts.reduce((a, p) => a + p.lat, 0) / pts.length) * (Math.PI / 180);
  const kx = Math.cos(lat0);
  const xs = pts.map((p) => p.lng * kx);
  const ys = pts.map((p) => p.lat);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const spanX = x1 - x0 || 1e-9;
  const spanY = y1 - y0 || 1e-9;
  const scale = Math.min((width - 2 * pad) / spanX, (height - 2 * pad) / spanY);
  const single = pts.length === 1 || (x1 - x0 < 1e-9 && y1 - y0 < 1e-9);
  return pts.map((p, i) => ({
    ...p,
    x: single ? width / 2 : pad + (xs[i] - x0) * scale + ((width - 2 * pad) - spanX * scale) / 2,
    y: single ? height / 2 : height - pad - (ys[i] - y0) * scale - ((height - 2 * pad) - spanY * scale) / 2,
  }));
}

// ---------- 저장소(안전) ----------
export function safeStorage(kind = 'local') {
  try {
    const s = kind === 'session' ? globalThis.sessionStorage : globalThis.localStorage;
    s?.setItem('__kc_probe', '1');
    s?.removeItem('__kc_probe');
    return s ?? null;
  } catch {
    return null;
  }
}
export function loadJson(storage, key, fallback) {
  try {
    const raw = storage?.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}
export function saveJson(storage, key, value) {
  try {
    storage?.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

/** 지도 점 모음: 출발 위치 · 행사 · 내 일정(좌표 있는 것만). */
export function mapPoints(result, itinerary, form) {
  const out = [];
  const lat = num(form.lat);
  const lng = num(form.lng);
  if (lat != null && lng != null) out.push({ id: 'origin', kind: 'origin', title: form.originName || '', lat, lng });
  (result?.map?.points ?? []).forEach((p, i) => out.push({ id: p.id, kind: 'event', n: i + 1, title: p.title, lat: p.lat, lng: p.lng }));
  itinerary.filter((p) => typeof p.lat === 'number').forEach((p) => out.push({ id: p.id, kind: 'plan', title: p.title, lat: p.lat, lng: p.lng }));
  return out;
}

/** 서버가 준 링크는 http(s) 만 href 로 쓴다(javascript: 등 차단). */
export function safeHref(u) {
  try {
    const url = new URL(String(u));
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : '';
  } catch {
    return '';
  }
}
