// 표시용 순수 함수. 출처 태그 문구 · 딱지 분류. 카드/지도/근거 모듈이 같은 규칙을 쓰도록 한 곳에 둔다.

const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];

/** 1 -> ①. 범위 밖이면 (n). */
export function circled(n) {
  return CIRCLED[n - 1] ?? `(${n})`;
}

/** 출처 태그 문구: "[등급] 출처 이름 · 위치" (AGENT_CONTEXT 3.3). */
export function sourceLabel(src) {
  const loc = src.locator ? ` · ${src.locator}` : '';
  return `[${src.tier}] ${src.name}${loc}`;
}

/** 번호 붙은 태그 문구: "① [A] 서울지명사전 (예시) · p.214". index 는 0부터. */
export function numberedSourceLabel(src, index) {
  return `${circled(index + 1)} ${sourceLabel(src)}`;
}

export const STORY_BADGES = ['기록', '전승', '추정'];
export const NOW_BADGES = ['확인됨', '확인 필요', '보류'];

/** 딱지 -> 카드 종류. 알 수 없으면 null. */
export function badgeKind(badge) {
  if (STORY_BADGES.includes(badge)) return 'story';
  if (NOW_BADGES.includes(badge)) return 'now';
  return null;
}

/** 딱지 -> CSS 에서 쓰는 영문 키(data-badge). */
export const BADGE_KEY = {
  기록: 'record',
  전승: 'lore',
  추정: 'presumed',
  확인됨: 'confirmed',
  '확인 필요': 'verify',
  보류: 'hold',
};
