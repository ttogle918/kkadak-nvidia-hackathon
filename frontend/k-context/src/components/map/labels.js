// 지도 이름표. 너비 계산과 라벨 사양을 순수 함수로 두고(테스트 가능), 노드는 buildLabel 이 만든다.
// 너비는 목업(K-Context.dc.html)의 labels 로직을 그대로 옮겼다: 글자 수 × 글자당 너비 + 여백. 한글이 영문보다 넓다.
import { h } from '../../lib/dom.js';

/** 종류별 글자당 너비(ko/en)와 좌우 여백. seg=옛날 구간 이름표, zone=지금 구역/행사 라벨, walk=숙소 복귀 라벨 */
export const LABEL_METRIC = {
  seg: { ko: 9.6, en: 5.8, pad: 16 },
  zone: { ko: 10.5, en: 6, pad: 16 },
  walk: { ko: 9.5, en: 5.6, pad: 14 },
};
export const LABEL_H = 20;

/** 이름표 박스 너비(px, svg 좌표). */
export function labelWidth(text, lang, kind = 'seg') {
  const m = LABEL_METRIC[kind] ?? LABEL_METRIC.seg;
  return Math.round(String(text ?? '').length * (lang === 'en' ? m.en : m.ko) + m.pad);
}

/** 맨 앞의 한 글자 기호("✓ 확인됨" -> "확인됨"). 지도 라벨에서는 ● 로 대체하므로 딱지 기호를 뗀다. */
export function stripGlyph(text) {
  return String(text ?? '').replace(/^\S\s/, '');
}

/** 옛날 구간 이름표 사양. selected 면 반전(바탕 갈색·글자 흰색), 추정(weak) 구간은 점선 테두리. */
export function segLabelSpec({ text, xy, selected, weak, lang }) {
  const [x, y] = xy;
  return {
    x, y, w: labelWidth(text, lang, 'seg'), tx: x + 8, ty: y + 14, text,
    tone: selected ? 'old-on' : 'old', dashed: !!weak,
  };
}

/** 지금 이름표 사양. align='right' 면 box 오른쪽 끝이 x, 'center' 면 가운데가 x, 'left' 면 왼쪽 끝이 x. */
export function nowLabelSpec({ text, x, y, lang, kind = 'zone', align = 'left', tone = 'now-dim', dashed = false, minW = 0 }) {
  const w = Math.max(minW, labelWidth(text, lang, kind));
  const left = align === 'right' ? x - w : align === 'center' ? Math.round(x - w / 2) : x;
  return { x: left, y, w, tx: left + 8, ty: y + 14, text, tone, dashed };
}

/** 사양 -> <g class="map-label"> (rect + text). */
export function buildLabel(spec) {
  return h('g', { class: ['map-label', `map-label--${spec.tone}`] },
    h('rect', { x: spec.x, y: spec.y, width: spec.w, height: LABEL_H, rx: 3, 'stroke-dasharray': spec.dashed ? '3 2' : null }),
    h('text', { x: spec.tx, y: spec.ty }, spec.text));
}
