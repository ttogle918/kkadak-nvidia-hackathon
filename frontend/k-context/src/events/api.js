// 행사 API 클라이언트. http(실서버) 와 mock(데모 — 응답마다 demo:true) 두 가지, 같은 메서드 이름.
// 관리자 토큰은 관리자 메서드의 헤더로만 보내고 로그·오류 메시지에 싣지 않는다.
import { DEMO_COVERAGE, DEMO_EVENTS } from './demo-data.js';

export class EventsApiError extends Error {
  constructor(code, status, message) {
    super(message || code);
    this.name = 'EventsApiError';
    this.code = code; // 'network' | 서버가 준 code
    this.status = status; // HTTP 상태(네트워크 오류는 0)
  }
}

const LOOPBACK = new Set(['localhost', '127.0.0.1', '[::1]']);
const BACKEND_PORT = '8000'; // 개발용 backend 의 기본 포트. 다른 포트의 로컬 서버로는 보내지 않는다

/**
 * ?base= 로 받은 backend 주소를 검증한다. 같은 출처의 경로("/api")이거나 루프백(localhost·127.0.0.1)의 8000 포트만 받는다.
 * 그 밖의 주소는 버리고 기본값을 쓴다 — 링크 하나로 관리자 토큰이나 일정·숙소 좌표를 다른 서버로 보내지 못하게 한다.
 */
export function safeBase(value, loc = globalThis.location) {
  if (!value) return undefined;
  const v = String(value);
  if (/^\/(?!\/)[\w\-./]*$/.test(v)) return v; // 같은 출처 경로
  try {
    const u = new URL(v);
    if ((u.protocol === 'http:' || u.protocol === 'https:') && LOOPBACK.has(u.hostname) && u.port === BACKEND_PORT
        && !u.username && !u.password) {
      return `${u.origin}${u.pathname.replace(/\/$/, '')}`;
    }
    if (loc && u.origin === loc.origin) return `${u.origin}${u.pathname.replace(/\/$/, '')}`;
  } catch { /* 잘못된 주소는 버린다 */ }
  return undefined;
}

/** 정적 서버(8766)에서 열었으면 같은 호스트의 8000 포트 backend 를 기본으로 본다. */
export function defaultBase(loc = globalThis.location) {
  // 정적 서버(8766)를 로컬에서 열었을 때만 :8000 을 쓴다. 다른 호스트(LAN·원격)는 같은 출처의 /api(프록시)다 — CSP 가 그 밖의 연결을 막는다.
  if (loc && loc.port === '8766' && LOOPBACK.has(loc.hostname)) return `${loc.protocol}//${loc.hostname}:8000/api`;
  return '/api';
}

export function createHttpEventsApi({ baseUrl = defaultBase(), fetchImpl = globalThis.fetch?.bind(globalThis) } = {}) {
  async function call(method, path, { body, token } = {}) {
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (token) headers['X-Admin-Token'] = token;
    let res;
    try {
      res = await fetchImpl(`${baseUrl}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
    } catch {
      throw new EventsApiError('network', 0, 'network');
    }
    let data = null;
    try {
      data = await res.json();
    } catch { /* JSON 이 아니면 아래에서 오류로 */ }
    if (!res.ok) {
      const e = data?.error;
      throw new EventsApiError(e?.code ?? 'http_error', res.status, e?.message ?? `HTTP ${res.status}`);
    }
    if (data == null) throw new EventsApiError('bad_response', res.status, 'bad_response');
    return data;
  }
  const q = (o) => {
    const p = new URLSearchParams(Object.entries(o).filter(([, v]) => v != null && v !== ''));
    const s = p.toString();
    return s ? `?${s}` : '';
  };
  return {
    mode: 'http', baseUrl, demo: false,
    search: (body) => call('POST', '/events/search', { body }),
    detail: (id, { lang = 'ko', demo = false } = {}) => call('GET', `/events/${encodeURIComponent(id)}${q({ lang, demo: demo ? 'true' : '' })}`),
    coverage: () => call('GET', '/events/coverage'),
    addToPlan: (body) => call('POST', '/events/itinerary/add', { body }),
    removeFromPlan: (body) => call('POST', '/events/itinerary/remove', { body }),
    savedChanges: (ids, since) => call('POST', '/events/saved-changes', { body: since ? { ids, since } : { ids } }),
    submitReport: (body) => call('POST', '/reports', { body }),
    admin: {
      review: (token) => call('GET', '/admin/review', { token }),
      sources: (token) => call('GET', '/admin/sources', { token }),
      reports: (token, status) => call('GET', `/admin/reports${q({ status })}`, { token }),
      decide: (token, id, decision, note = '') => call('POST', `/admin/reports/${encodeURIComponent(id)}/decision`, { token, body: { decision, note } }),
      refresh: (token, sourceId) => call('POST', `/admin/refresh/${encodeURIComponent(sourceId)}`, { token, body: {} }),
      linkCheck: (token, sourceId, note = '') => call('POST', `/admin/link-checks/${encodeURIComponent(sourceId)}`, { token, body: { note } }),
    },
  };
}

const clone = (v) => structuredClone(v);

/** 데모 API: 서버 없이 화면을 볼 수 있다. 모든 행사가 demo:true 이고 실제 수집·검증과 무관하다. */
export function createMockEventsApi() {
  const reports = [];
  const overlap = (e, trip) => !(e.schedule.end_date < trip.from || e.schedule.start_date > trip.to);
  return {
    mode: 'mock', baseUrl: '', demo: true,
    async search(body) {
      const events = DEMO_EVENTS.filter((e) => overlap(e, body.trip)).map((e) => {
        const days = [];
        for (let d = body.trip.from; d <= body.trip.to; d = new Date(Date.parse(`${d}T00:00:00Z`) + 86400000).toISOString().slice(0, 10)) {
          if (d >= e.schedule.start_date && d <= e.schedule.end_date) {
            const sessions = e.schedule.sessions.filter((s) => s.date === d);
            const closed = e.schedule.weekly_closed_days.includes((new Date(`${d}T00:00:00Z`).getUTCDay() + 6) % 7);
            days.push({ date: d, state: closed ? 'no' : sessions.length ? 'yes' : 'unknown', reason: closed ? '정기 휴무 요일' : sessions.length ? '회차 있음' : '기간 안 — 회차·운영 시간 확인 필요', sessions: sessions.map((s) => ({ start_time: s.start_time, end_time: s.end_time, venue_name: s.venue_name, in_target: s.in_target })) });
          }
        }
        const avail = days.some((x) => x.state === 'yes') ? 'session_match' : 'date_range_unconfirmed';
        const hits = (body.interests ?? []).filter((i) => (e.title + e.event_type).includes(i));
        return { ...clone(e), availability: avail, matching_dates: days, interest_match: hits };
      }).filter((e) => e.matching_dates.some((d) => d.state !== 'no'));
      const suggestions = [];
      if (Array.isArray(body.itinerary)) {
        for (const e of events) {
          for (const d of e.matching_dates) {
            for (const s of d.sessions) {
              suggestions.push({
                entry_id: e.id, title: e.title, date: d.date, session: { start_time: s.start_time, end_time: s.end_time, assumed_end: false },
                after_item_id: null, before_item_id: null, extra_minutes: null, extra_basis: 'none', extra_status: 'needs_check',
                route: { provider: 'none', mode: 'walk', estimated: false, legs: { prev_to_event: null, event_to_next: null, prev_to_next: null }, from: 'none' },
                status: 'check_needed', reasons: [{ code: 'travel_unknown', ko: '이동시간 확인 필요', en: 'Travel time needs checking' }],
                reservation: e.reservation, participation: e.participation, verification: e.verification, last_verified_at: e.last_verified_at, links: e.links,
              });
            }
          }
        }
      }
      const points = events.filter((e) => e.venue.lat != null).map((e) => ({ id: e.id, title: e.title, lat: e.venue.lat, lng: e.venue.lng, availability: e.availability, participation: e.participation.status }));
      return {
        generated_at: '데모', timezone: 'Asia/Seoul', events, suggestions, excluded: [], problems: [], catalog_empty: false,
        coverage: clone(DEMO_COVERAGE), map: { origin: body.origin ?? null, points, unlocated: events.filter((e) => e.venue.lat == null).map((e) => e.id) },
        counts: { events: events.length, excluded: 0 },
      };
    },
    async detail(id) {
      const e = DEMO_EVENTS.find((x) => x.id === id);
      if (!e) throw new EventsApiError('not_found', 404, 'not_found');
      return { ...clone(e), history: [], stories: [], coverage: clone(DEMO_COVERAGE) };
    },
    async coverage() { return { coverage: clone(DEMO_COVERAGE) }; },
    async addToPlan(body) {
      const e = DEMO_EVENTS.find((x) => x.id === body.entry_id);
      const s = e?.schedule.sessions.find((x) => x.date === body.date && x.start_time === body.start_time);
      if (!e || !s) throw new EventsApiError('not_found', 404, 'not_found');
      const id = `evt:${e.id}:${s.date}:${s.start_time}`;
      const item = { id, title: e.title, date: s.date, start: s.start_time, end: s.end_time ?? s.start_time, lat: e.venue.lat, lng: e.venue.lng, source: 'catalog', entry_id: e.id, end_assumed: !s.end_time };
      const items = body.itinerary.some((i) => i.id === id) ? body.itinerary : [...body.itinerary, item];
      items.sort((a, b) => (a.date + a.start).localeCompare(b.date + b.start));
      return { itinerary: items, suggestion: { entry_id: e.id, status: 'check_needed' } };
    },
    async removeFromPlan(body) {
      return { itinerary: body.itinerary.filter((i) => !(i.id === body.item_id && i.source === 'catalog')) };
    },
    async savedChanges() { return { saved: [] }; },
    async submitReport(body) {
      const r = { id: `rpt_demo_${reports.length + 1}`, status: 'pending', ...body };
      reports.push(r);
      return { report: r };
    },
    admin: {
      async review() { throw new EventsApiError('forbidden', 403, 'demo'); },
      async sources() { throw new EventsApiError('forbidden', 403, 'demo'); },
      async reports() { throw new EventsApiError('forbidden', 403, 'demo'); },
      async decide() { throw new EventsApiError('forbidden', 403, 'demo'); },
      async refresh() { throw new EventsApiError('forbidden', 403, 'demo'); },
      async linkCheck() { throw new EventsApiError('forbidden', 403, 'demo'); },
    },
  };
}

export function createEventsApi({ mode = 'http', baseUrl, fetchImpl } = {}) {
  if (mode === 'mock') return createMockEventsApi();
  if (mode === 'http') return createHttpEventsApi({ baseUrl, fetchImpl });
  throw new Error(`알 수 없는 api mode: ${mode} (http|mock)`);
}
