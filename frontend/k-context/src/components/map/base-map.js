// 기반 지도(정적): 블록·큰길·물길. 목업의 #mBase 를 h() 로 옮겼다. 좌표계는 viewBox 0 0 600 700.
// 색은 전부 map.css 의 클래스(토큰 변수)가 정한다. 가장자리 빈 곳이 보이지 않게 바탕을 크게 깐다.
import { h } from '../../lib/dom.js';

export const VIEW_BOX = '0 0 600 700';

const BLOCKS = [[20, 30, 80, 60], [130, 130, 140, 70], [330, 40, 130, 60], [40, 250, 70, 60], [330, 150, 110, 50],
  [170, 255, 110, 50], [340, 250, 100, 70], [500, 130, 80, 150], [40, 340, 520, 60]];
const ROADS = ['M-100 120H700', 'M-100 330H700', 'M90 -100V500', 'M300 -100V500', 'M470 -100V500', 'M-100 65L700 5'];
const WATER = 'M-100 222C150 245 300 210 700 232';

/** @param {(k:string)=>string} t */
export function buildBaseMap(t) {
  return h('g', { class: 'map-base', 'aria-hidden': 'true' },
    h('rect', { class: 'map-base__bg', x: -300, y: -300, width: 1200, height: 1300 }),
    h('g', { class: 'map-base__blocks' }, BLOCKS.map(([x, y, w, ht]) => h('rect', { x, y, width: w, height: ht }))),
    h('g', { class: 'map-base__roads', fill: 'none', 'stroke-linecap': 'round' }, ROADS.map((d) => h('path', { d }))),
    h('path', { class: 'map-base__water', d: WATER, fill: 'none' }),
    h('text', { class: 'map-base__water-label', x: 500, y: 256 }, t('map.water')));
}
