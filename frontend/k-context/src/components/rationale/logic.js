// rationale 모듈의 순수 로직(DOM 없음).
import { showsNow, showsOld } from '../../state/selectors.js';

/** 마지막 요청만 유효하게 하는 가드(경쟁 상태 방지). */
export function createLatestGuard() {
  let n = 0;
  return { next: () => ++n, isCurrent: (token) => token === n, invalidate: () => { n += 1; } };
}

/** mode 와 선택 상태에서 근거를 보여 줄 카드 id 목록(옛날 먼저). */
export function activeCardIds(state) {
  const ids = [];
  if (showsOld(state.mode) && state.selectedSeg) ids.push(state.selectedSeg);
  if (showsNow(state.mode) && state.selectedNow) ids.push(state.selectedNow);
  return ids;
}

/** 여러 카드의 getRationale 응답을 칩/항목으로 합친다. 같은 key 는 먼저 온 것이 이긴다. */
export function mergeRationale(list) {
  const chips = [];
  const items = {};
  for (const r of list) {
    for (const c of r?.chips ?? []) if (!chips.some((x) => x.key === c.key)) chips.push(c);
    for (const [k, v] of Object.entries(r?.items ?? {})) if (!(k in items)) items[k] = v;
  }
  return { chips, items };
}

/**
 * 깔때기 행: 첫 행이 채택, 나머지가 탈락 사유(숫자). 모두 숫자일 때만 막대를 그린다.
 * 반환: [{k, v, kind:'adopted'|'dropped', ratio}] 또는 null(깔때기가 아님).
 */
export function funnelRows(rows) {
  if (!rows?.length) return null;
  const nums = rows.map((r) => Number(r.v));
  if (nums.some((n) => !Number.isFinite(n))) return null;
  const max = Math.max(...nums, 1);
  return rows.map((r, i) => ({ k: r.k, v: r.v, kind: i === 0 ? 'adopted' : 'dropped', ratio: nums[i] / max }));
}

/**
 * 충돌 해결 행에 채택/버림 표시를 단다. "✓" 가 든 행이 채택이고 나머지는 버림(참고).
 * 어느 행에도 ✓ 가 없으면(미해결 충돌) 아무것도 표시하지 않는다 — 해결된 척하지 않는다.
 */
export function conflictMarks(rows, valueText) {
  const texts = (rows ?? []).map((r) => String(valueText(r.v)));
  if (!texts.some((x) => x.includes('✓'))) return (rows ?? []).map(() => null);
  return texts.map((x) => (x.includes('✓') ? 'adopted' : 'dropped'));
}

/** 현재 열린 항목. key 가 없거나 항목이 없으면 null. */
export function openItem(merged, key) {
  return key && Object.hasOwn(merged.items, key) ? { key, ...merged.items[key] } : null;
}

/** 걸러낸 주장 목록(지금 카드의 rejected): 화면에 올라온 카드 id 순. */
export function rejectedFor(cards, ids) {
  return ids.flatMap((id) => (cards?.find((c) => c.id === id)?.rejected ?? []));
}
