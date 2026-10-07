// 딱지(기록/전승/추정/확인됨/확인 필요/보류). 색 + 글리프 + 테두리 모양으로 구분한다.
import { h } from '../../lib/dom.js';
import { badgeShape } from './logic.js';

export function renderBadge(badge, t) {
  const shape = badgeShape(badge);
  return h('span', {
    class: 'badge cards-badge', 'data-badge': shape.key, 'data-border': shape.border, dataset: { glyph: shape.glyph },
  }, t(`badge.${badge}`));
}
