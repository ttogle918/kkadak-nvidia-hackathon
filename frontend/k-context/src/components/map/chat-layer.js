// 챗봇이 정리한 일정의 SVG 지도: 기본 지도 위에 좌표가 있는 앵커만 핀으로 그린다(옛길 선·고정 샘플 지점 없음).
// 좌표 변환은 위경도 bbox 를 viewBox 안쪽에 맞추되 경도는 cos(위도)로 보정한다. 정보창은 지도 아래에 붙는 HTML 패널(textContent).
import { h } from '../../lib/dom.js';
import { bundlePins, pinInfo, pinLinks } from '../../lib/chat-bundle.js';
import { pinInfoNode } from '../../lib/chat-bundle-view.js';
import { VIEW_BOX, buildBaseMap } from './base-map.js';

/** pins -> key => [x,y] (viewBox 0 0 600 700). 한 점뿐이거나 거의 겹치면 가운데에 둔다. */
export function projectPins(pins) {
  if (!pins.length) return new Map();
  const lat0 = pins.reduce((a, p) => a + p.lat, 0) / pins.length;
  const k = Math.cos((lat0 * Math.PI) / 180);
  const xs = pins.map((p) => p.lng * k);
  const ys = pins.map((p) => p.lat);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const MIN_SPAN = 0.004; // 약 400m — 이보다 좁으면 과확대하지 않는다
  const spanX = Math.max(x1 - x0, MIN_SPAN);
  const spanY = Math.max(y1 - y0, MIN_SPAN);
  const sc = Math.min(440 / spanX, 520 / spanY);
  const cx = (x0 + x1) / 2;
  const cy = (y0 + y1) / 2;
  const out = new Map();
  pins.forEach((p, i) => out.set(p.key, [Math.round(300 + (xs[i] - cx) * sc), Math.round(350 - (ys[i] - cy) * sc)]));
  return out;
}

/** @returns {SVGElement} */
export function buildBundleSvg(bundle, t, selectedKey) {
  const pins = bundlePins(bundle);
  const at = projectPins(pins);
  const links = pinLinks(bundle);
  return h('svg', { class: 'map-svg map-svg--bundle', viewBox: VIEW_BOX, preserveAspectRatio: 'xMidYMid meet', role: 'group', 'aria-label': t('map.bundle.aria') },
    buildBaseMap(t),
    // 같은 날 이웃 핀의 점선(D16: 직선 연결일 뿐 실제 길이 아니다). 모양(점선)과 글자 라벨로 구분하고 색에만 의존하지 않는다.
    links.length ? [
      links.map((l) => {
        const [x1, y1] = at.get(l.from);
        const [x2, y2] = at.get(l.to);
        return h('path', { class: 'map-straight', d: `M${x1} ${y1} L${x2} ${y2}`, fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-dasharray': '3 7', 'stroke-linecap': 'round', opacity: 0.6, dataset: { day: l.day } });
      }),
      h('text', { class: 'map-name map-name--sub map-straight__label', x: 16, y: 684 }, `┈ ${t('map.bundle.straight_note')}`),
    ] : null,
    pins.map((p) => {
      const [x, y] = at.get(p.key);
      const on = p.key === selectedKey;
      return h('g', {
        class: ['map-pin', on && 'is-selected', p.type === 'hotel' && 'map-pin--hotel'], role: 'button', tabindex: '0',
        'aria-label': t('map.bundle.pin_aria', { name: p.name, n: p.count }), 'aria-pressed': String(on),
        dataset: { act: 'pin', key: p.key, fk: `pin:${p.key}` },
      },
      h('circle', { class: 'map-pin__hit', cx: x, cy: y, r: 24 }),
      h('path', { class: 'map-pin__shape', d: `M${x} ${y} l-9 -22 a11 11 0 1 1 18 0 z` }),
      h('circle', { class: 'map-pin__dot', cx: x, cy: y - 26, r: 4 }),
      h('text', { class: 'map-name', x: x + 14, y: y - 22 }, p.name));
    }));
}

/** 선택한 핀의 정보창(지도 아래 패널). key 가 없거나 모르는 핀이면 null. */
export function buildPinPanel(bundle, key, t) {
  const pin = key ? bundlePins(bundle).find((p) => p.key === key) : null;
  if (!pin) return null;
  return h('div', { class: 'map-pinpanel', role: 'dialog', 'aria-label': t('map.bundle.panel_aria', { name: pin.name }) },
    h('button', { type: 'button', class: 'map-pinpanel__close', dataset: { act: 'pin-close' }, 'aria-label': t('map.bundle.close') }, '×'),
    pinInfoNode(pinInfo(pin), t));
}

/** 핀이 하나도 없을 때의 안내(좌표 없는 앵커는 타임라인·카드에만 나온다). */
export const bundleHasPins = (bundle) => bundlePins(bundle).length > 0;
