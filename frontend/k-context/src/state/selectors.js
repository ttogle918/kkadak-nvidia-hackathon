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
