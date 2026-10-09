// 실제 모드(예시 데이터 없음)의 빈 상태·오류 상태 안내 한 줄. 서버 오류 문구는 쓰지 않고 고정 문구만 보인다.
import { h } from './dom.js';

/**
 * @param {'empty'|'error'} screen realScreen() 의 결과  @param {'timeline'|'cards'|'map'} area  @param {Function} t
 * @param {string} cls 영역별 기존 빈 문구 클래스
 */
export function realNote(screen, area, t, cls = 'cb-empty') {
  return h('p', { class: cls, role: 'status', dataset: { real: screen, area } }, t(screen === 'error' ? 'real.error' : `real.empty.${area}`));
}
