// cards 모듈의 순수 로직. DOM 을 만지지 않으므로 node 테스트에서 그대로 검증한다.
import { BADGE_KEY, circled } from '../../lib/format.js';
import { showsNow, showsOld } from '../../state/selectors.js';

/** 출처 태그를 접기 전에 보여 주는 최대 개수 (AGENT_CONTEXT 3.4 요소 8, 목업 tg()). */
export const MAX_TAGS = 3;

/**
 * 출처 태그 접기. n 은 원래 순서의 1부터 센 번호(① ② …)라서 접어도 번호가 바뀌지 않는다.
 * @returns {{shown: {src: object, n: number}[], hidden: number}}
 */
export function splitTags(sources, expanded, max = MAX_TAGS) {
  const all = (sources ?? []).map((src, i) => ({ src, n: i + 1 }));
  if (expanded || all.length <= max) return { shown: all, hidden: 0 };
  return { shown: all.slice(0, max), hidden: all.length - max };
}

/**
 * 딱지 -> 모양. 색만으로 구분하지 않도록 글리프와 테두리 모양을 함께 정한다.
 * key 는 base.css 의 data-badge 값, border 는 'solid' | 'dashed'.
 */
const SHAPES = {
  기록: { glyph: '◆', border: 'solid' },
  전승: { glyph: '◇', border: 'solid' },
  추정: { glyph: '◇', border: 'dashed' },
  확인됨: { glyph: '✓', border: 'solid' },
  '확인 필요': { glyph: '!', border: 'solid' },
  보류: { glyph: 'Ⅱ', border: 'dashed' },
};
export function badgeShape(badge) {
  const s = SHAPES[badge];
  return s ? { key: BADGE_KEY[badge], ...s } : { key: 'unknown', glyph: '?', border: 'dashed' };
}

/**
 * 지금 카드 버튼 상태. 보류 카드는 둘 다 비활성(결정할 수 없다).
 * primary.kind: 'add' | 'add_after_check' | 'added' | 'hold'
 */
export function nowButtons(badge, { added = false, skipped = false } = {}) {
  if (badge === '보류') {
    return {
      primary: { kind: 'hold', labelKey: 'card.hold', disabled: true },
      skip: { labelKey: 'card.skip', disabled: true },
    };
  }
  const primary = added
    ? { kind: 'added', labelKey: 'card.added', disabled: true }
    : badge === '확인 필요'
      ? { kind: 'add_after_check', labelKey: 'card.add_after_check', disabled: false }
      : { kind: 'add', labelKey: 'card.add', disabled: false };
  const skip = skipped
    ? { labelKey: 'card.skipped', disabled: true }
    : { labelKey: 'card.skip', disabled: false };
  return { primary, skip };
}

/** 확인 항목 수준 -> 글리프(색에 의존하지 않는다). */
export const CHECK_GLYPH = { ok: '✓', warn: '!', bad: '✕' };
export const checkGlyph = (level) => CHECK_GLYPH[level] ?? '·';

/** slot.between(문자열|{ko,en} 배열) -> 번역된 문구. 1개면 그대로, 2개면 "A → B". */
export function betweenText(between, t) {
  const parts = (between ?? []).map((b) => t(b)).filter(Boolean);
  return parts.join(' → ');
}

/** 지금 카드의 "오늘 하루만/여행 기간에만" 문구. only 가 문자열/객체로 오면 그대로 쓴다. */
export function onlyText(card, t) {
  return card.only ? t(card.only) : '';
}

/** mode 와 선택 상태로 화면에 올릴 카드를 고른다. */
export function visibleCards(state) {
  const cards = state.data?.cards ?? [];
  const byId = (id) => (id ? cards.find((c) => c.id === id) ?? null : null);
  const old = showsOld(state.mode) ? byId(state.selectedSeg) : null;
  const now = showsNow(state.mode) ? byId(state.selectedNow) : null;
  return { old: old && old.kind === 'story' ? old : null, now: now && now.kind === 'now' ? now : null };
}

/** source id 로 출처를 찾는다: 받아 둔 sources 가 먼저, 없으면 카드에 박힌 sources. */
export function findSource(state, id) {
  if (!id) return null;
  const global = state.data?.sources?.find?.((s) => s.id === id);
  if (global) return global;
  for (const c of state.data?.cards ?? []) {
    const hit = c.sources?.find((s) => s.id === id);
    if (hit) return hit;
  }
  return null;
}

/** 이 출처가 받치는 사실 층 문장들: [{n, text}] (n 은 ①… 번호). 옛날 카드에만 있다. */
export function supportingFacts(card, sourceId) {
  if (!card?.facts) return [];
  return card.facts
    .filter((f) => card.sources?.[f.ref - 1]?.id === sourceId)
    .map((f) => ({ n: f.ref, text: f.text, mark: circled(f.ref) }));
}

/** 마지막 요청만 유효하게 하는 가드(경쟁 상태 방지). next() 로 번호를 받고 isCurrent(번호) 로 확인한다. */
export function createLatestGuard() {
  let n = 0;
  return { next: () => ++n, isCurrent: (token) => token === n, invalidate: () => { n += 1; } };
}

/** http(s) 가 아닌 URL(javascript: 등)은 링크로 만들지 않는다. 지금은 텍스트로만 보여 주지만 규칙은 남겨 둔다. */
export function isSafeHttpUrl(url) {
  return /^https?:\/\/\S+$/i.test(String(url ?? ''));
}
