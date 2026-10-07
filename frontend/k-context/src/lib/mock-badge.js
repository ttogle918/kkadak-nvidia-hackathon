// 공통 "MOCK" 딱지. 예시(가짜) 데이터가 보이는 곳마다 같은 모양으로 붙인다.
// kind: 'mock'(프론트 고정 예시) | 'fixture'(서버가 주지만 mock 과 같은 고정 예시). 둘 다 글자는 MOCK 이고 설명 문구만 다르다.
// note: true 면 "예시 데이터 — 실제 아님" 문구를 딱지 옆에 글자로도 보인다(툴팁은 터치·스크린리더에서 안 보이므로).
// 모든 글자는 텍스트 노드 — 읽는 순서대로 "MOCK 예시 데이터 — 실제 아님" 이라 aria-label 이 필요 없다.
import { h } from './dom.js';

export function mockBadge(t, { kind = 'mock', note = false } = {}) {
  const k = kind === 'fixture' ? 'fixture' : 'mock';
  const text = t(k === 'fixture' ? 'mock.badge.fixture' : 'mock.badge.title');
  return h('span', { class: ['mock-badge', note && 'mock-badge--note'], dataset: { mock: k }, title: text },
    h('span', { class: 'mock-badge__pill' }, t('mock.badge')),
    note ? h('span', { class: 'mock-badge__note' }, text) : null);
}
