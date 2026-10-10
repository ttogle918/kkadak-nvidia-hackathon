// securitylog 순수 로직 — 로그 분류와 승인 가능 여부.

/** kind -> 라벨 키·기호. 색(CSS)만 쓰지 않고 기호+글자 라벨을 항상 함께 보인다. */
export const LOG_META = {
  ok: { icon: '✓', labelKey: 'log.ok' },
  deny: { icon: '⊘', labelKey: 'log.deny' },
  pend: { icon: '⚠', labelKey: 'log.pend' },
  approved: { icon: '✓', labelKey: 'log.approved' },
  rejected: { icon: '✕', labelKey: 'log.rejected' },
};

export const KNOWN_KINDS = Object.keys(LOG_META);

/** 알 수 없는 kind 는 거부(deny)처럼 보수적으로 표시하지 않고 그대로 두되 버튼은 절대 주지 않는다. */
export function metaOf(kind) {
  return LOG_META[kind] ?? { icon: '?', labelKey: null };
}

/** 사람의 결정을 받을 수 있는 항목은 승인 대기(pend)뿐이다. */
export function canDecide(entry) {
  return entry?.kind === 'pend';
}

/** 버튼이 보낼 수 있는 결정. 이 두 값 외에는 호출하지 않는다. */
export const DECISIONS = ['approve', 'reject'];

/** 결정 뒤에 붙이는 안내 키(승인됨/거절됨 항목만). */
export function decidedNoteKey(entry) {
  if (entry?.kind === 'approved') return 'log.decided_approved';
  if (entry?.kind === 'rejected') return 'log.decided_rejected';
  return null;
}

/** 종류별 건수 — 헤더 요약(대기 건수)에 쓴다. */
export function countByKind(logs) {
  const c = Object.fromEntries(KNOWN_KINDS.map((k) => [k, 0]));
  for (const l of logs ?? []) if (l.kind in c) c[l.kind] += 1;
  return c;
}

const atMs = (e) => (typeof e?.at === 'string' ? Date.parse(e.at) : NaN);

/** 최신 우선: at 내림차순, 같은 at 은 id 오름차순, at 없는(또는 잘못된) 항목은 원래 순서로 맨 뒤. 원본은 바꾸지 않는다. */
export function sortNewestFirst(entries) {
  const list = Array.isArray(entries) ? entries : [];
  const withAt = [];
  const without = [];
  for (const e of list) (Number.isFinite(atMs(e)) ? withAt : without).push(e);
  withAt.sort((a, b) => atMs(b) - atMs(a) || (String(a.id) < String(b.id) ? -1 : String(a.id) > String(b.id) ? 1 : 0));
  return [...withAt, ...without];
}

let seoulFmt = null;
/** ISO 시각 -> Asia/Seoul 'MM-DD HH:MM:SS'. 해석할 수 없으면 null. */
export function formatWhen(at) {
  if (typeof at !== 'string' || at.length > 40) return null;
  const ms = Date.parse(at);
  if (!Number.isFinite(ms)) return null;
  seoulFmt ??= new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Seoul', hourCycle: 'h23',
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
  const p = Object.fromEntries(seoulFmt.formatToParts(new Date(ms)).map((x) => [x.type, x.value]));
  return `${p.month}-${p.day} ${p.hour}:${p.minute}:${p.second}`;
}
