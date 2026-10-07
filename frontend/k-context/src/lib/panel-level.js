// 하단 패널(.cards-zone) 높이 단계의 순수 계산. DOM 을 만지지 않는다(테스트가 직접 부른다).
//   collapsed 접힘(핸들+제목 한 줄) / default 기본(가운데 열의 약 1/3) / expanded 펼침(약 70%)

export const PANEL_LEVELS = ['collapsed', 'default', 'expanded'];
export const COLLAPSED_PX = 48; // tokens.css 의 --panel-collapsed-h 와 같은 값
export const PANEL_FRAC = { default: 1 / 3, expanded: 0.7 };
/** aria-valuenow 에 쓰는 퍼센트(가운데 열 높이 대비). min/max 는 접힘·펼침 값. */
export const PANEL_PERCENT = { collapsed: 5, default: 33, expanded: 70 };
export const PANEL_MIN = PANEL_PERCENT.collapsed;
export const PANEL_MAX = PANEL_PERCENT.expanded;

export const isLevel = (v) => PANEL_LEVELS.includes(v);

/** 한 단계 위(+1)/아래(-1). 양 끝에서는 그대로. */
export function stepLevel(level, dir) {
  const i = PANEL_LEVELS.indexOf(isLevel(level) ? level : 'default');
  const next = Math.min(PANEL_LEVELS.length - 1, Math.max(0, i + (dir > 0 ? 1 : dir < 0 ? -1 : 0)));
  return PANEL_LEVELS[next];
}

/** Enter/Space: 접힘이면 기본으로, 그 밖에는 접힘으로 (펼침 -> 기본). */
export function toggleLevel(level) {
  if (level === 'collapsed') return 'default';
  if (level === 'expanded') return 'default';
  return 'collapsed';
}

/** 단계의 높이(px). containerH 는 가운데 열 높이. */
export function levelHeight(level, containerH) {
  if (level === 'collapsed') return COLLAPSED_PX;
  return Math.round(containerH * (PANEL_FRAC[level] ?? PANEL_FRAC.default));
}

/** 드래그 중 높이를 [접힘, 펼침] 범위로 자른다. */
export function clampHeight(px, containerH) {
  return Math.min(levelHeight('expanded', containerH), Math.max(COLLAPSED_PX, px));
}

/** 놓은 높이에서 가장 가까운 단계. */
export function snapLevel(px, containerH) {
  let best = 'default';
  let bestD = Infinity;
  for (const lv of PANEL_LEVELS) {
    const d = Math.abs(levelHeight(lv, containerH) - px);
    if (d < bestD) { best = lv; bestD = d; }
  }
  return best;
}

/** 시작 높이에서 포인터가 위로(dy<0) 움직인 만큼 키운 높이. */
export const dragHeight = (startH, startY, curY, containerH) => clampHeight(startH + (startY - curY), containerH);
