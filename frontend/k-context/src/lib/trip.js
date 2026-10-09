// 여행 기간(선택 보조 입력, D22). 값은 화면 입력 또는 URL ?trip= 에서만 온다 — 예시(MOCK) 일정의 기간은 쓰지 않는다.
// 순수 함수 + 저장소(localStorage) 접근은 try/catch 로 감싼다(실패해도 화면은 돈다).

const KEY = 'kc.trip';
const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

/** 실제 달력에 있는 YYYY-MM-DD 인가. */
export function isDateStr(v) {
  if (typeof v !== 'string') return false;
  const m = DATE_RE.exec(v);
  if (!m) return false;
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  return d.getUTCFullYear() === +m[1] && d.getUTCMonth() === +m[2] - 1 && d.getUTCDate() === +m[3];
}

/**
 * {from,to} 입력 -> {trip, error}. 둘 다 비면 {trip:null, error:false}(정상 상태).
 * 형식 오류·한쪽만 입력·시작 > 끝이면 {trip:null, error:true} — 요청에 싣지 않는다.
 */
export function evalTrip(input) {
  const from = typeof input?.from === 'string' ? input.from : '';
  const to = typeof input?.to === 'string' ? input.to : '';
  if (!from && !to) return { trip: null, error: false };
  if (!isDateStr(from) || !isDateStr(to) || from > to) return { trip: null, error: true };
  return { trip: { from, to }, error: false };
}

/** URL 의 ?trip=YYYY-MM-DD..YYYY-MM-DD -> {from,to} | null(없거나 모양이 다르면). 틀린 값은 입력칸에 올리지 않는다. */
export function tripFromSearch(search) {
  let raw = null;
  try { raw = new URLSearchParams(search).get('trip'); } catch { return null; }
  const m = /^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$/.exec(raw ?? '');
  return m ? { from: m[1], to: m[2] } : null;
}

function store() {
  try { return globalThis.localStorage ?? null; } catch { return null; }
}

/** 저장된 입력값. 읽기 실패·모양 이상이면 빈 값. */
export function loadStoredTrip() {
  try {
    const o = JSON.parse(store()?.getItem(KEY) ?? 'null');
    const ok = (v) => v === '' || isDateStr(v);
    if (o && typeof o === 'object' && ok(o.from) && ok(o.to)) return { from: o.from ?? '', to: o.to ?? '' };
  } catch { /* 저장소를 못 쓰면 기억하지 않을 뿐 */ }
  return { from: '', to: '' };
}

export function saveStoredTrip(input) {
  try { store()?.setItem(KEY, JSON.stringify({ from: input.from ?? '', to: input.to ?? '' })); } catch { /* 무시 */ }
}

/** 부팅 시 초기 입력: URL 이 우선, 없으면 저장값. */
export function initialTripInput(search) {
  return tripFromSearch(search) ?? loadStoredTrip();
}
