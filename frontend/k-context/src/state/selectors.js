// 상태에서 화면용 값을 뽑는 순수 함수. 모듈이 같은 규칙을 쓰도록 여기에 둔다(모듈끼리 import 하지 않는다).

/** 카드 id -> 카드. data.cards 가 아직 없으면 null. */
export function cardById(state, id) {
  return state.data.cards?.find((c) => c.id === id) ?? null;
}

/** mode 가 옛날을 보이는가 / 지금을 보이는가. */
export const showsOld = (mode) => mode !== 'now';
export const showsNow = (mode) => mode !== 'old';

/** 경로 id 로 경로 찾기. */
export function routeById(state, id) {
  return state.data.routes?.find((r) => r.id === id) ?? null;
}

/** 해당 day 의 지금 카드들. */
export function nowCardsForDay(state, day) {
  return (state.data.cards ?? []).filter((c) => c.kind === 'now' && c.slot?.day === day);
}

/**
 * 타임라인 행 계산. item.only 조건('added'|'not_added')을 걸러내고,
 * proposal 행에는 status('proposed'|'added'|'skipped')를 붙인다. 결정은 selectedNow 카드에만 적용된다.
 * 반환 행: {...item, status} — status 는 'original' | 'free' | 'proposed' | 'added' | 'skipped'.
 */
export function timelineFor(itinerary, day, { added, skipped, selectedNow }) {
  const dayRow = itinerary?.timeline?.find((d) => d.day === day);
  if (!dayRow) return [];
  return dayRow.items
    .filter((it) => !(it.only === 'added' && !added) && !(it.only === 'not_added' && added))
    .map((it) => {
      if (it.kind !== 'proposal') return { ...it, status: it.kind };
      const mine = it.card_id === selectedNow;
      const status = mine && added ? 'added' : mine && skipped ? 'skipped' : 'proposed';
      return { ...it, status };
    });
}

/** 승인 대기(pend) 보안 로그 개수 — 설정 버튼의 알림 표시에 쓴다. */
export function pendingCount(logs) {
  return (logs ?? []).filter((l) => l.kind === 'pend').length;
}

// ---- MOCK(가짜 데이터) 표시 판정. 화면 어디에 MOCK 딱지를 붙일지는 여기서만 정한다 ----
// 규칙: ① api.dataKinds[키] 가 'mock'·'fixture' 이거나 모르면(없음) MOCK 으로 본다(실제라고 단정하지 않는다).
//       ② chatBundle 이 있으면 타임라인·지도 핀·카드는 그 묶음이 기준이다 — 서버가 준 묶음(sample 아님, api.mode !== 'mock')만 실제.
//       ③ chatBundle 이 있으면 mock 판단 근거(rationale)는 숨긴다(실제 결과와 섞이지 않게).

/** 데이터 키의 종류: 'mock'|'fixture'|'server'|'none'. dataKinds 가 없으면 'mock'. */
export const dataKindOf = (api, key) => api?.dataKinds?.[key] ?? 'mock';
const isMockKind = (k) => k === 'mock' || k === 'fixture' || k == null;

/** chatBundle 이 없으면 null, 있으면 'server'(실제) | 'mock'(sample 이거나 backend 없는 mock api). */
export function bundleKind(state, api) {
  if (!state.chatBundle) return null;
  return state.chatBundle.sample === true || api?.mode === 'mock' || api?.mode == null ? 'mock' : 'server';
}

/**
 * 영역별 MOCK 여부.
 * 반환: {timeline, routes, map, cards, rationale: 'mock'|'fixture'|null, hideRationale, myLocation}
 *  - routes: 경로 A·B·C 탭 줄(묶음 화면에는 없다)   - map: 지도의 선·핀   - myLocation: 지도의 '내 위치'(항상 예시 좌표)
 */
export function mockRegions(state, api) {
  const bk = bundleKind(state, api);
  const kind = (key) => { const k = dataKindOf(api, key); return isMockKind(k) ? (k === 'fixture' ? 'fixture' : 'mock') : null; };
  if (bk) {
    const m = bk === 'mock' ? 'mock' : null;
    return { timeline: m, routes: null, map: m, cards: m, rationale: null, hideRationale: true, myLocation: 'mock' };
  }
  return { timeline: kind('itinerary'), routes: kind('routes'), map: kind('routes') ?? kind('itinerary'), cards: kind('cards'), rationale: kind('rationale'), hideRationale: false, myLocation: 'mock' };
}

/**
 * 상단 상태: 'all-mock'(백엔드 미연결 — 전체 MOCK) | 'bundle'(챗봇이 정리한 일정, 실제 서버) | 'mock'(서버는 연결됐지만 화면은 MOCK).
 */
export function screenStatus(state, api) {
  if (api?.mode == null || api.mode === 'mock') return 'all-mock';
  return bundleKind(state, api) === 'server' ? 'bundle' : 'mock';
}
