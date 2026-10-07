// 챗봇이 정리한 일정의 카드: "실록에 이런 기록이 있어요"(앵커별 간이 카드)와 주변 행사(간이형).
// 실록 언급은 이야기(story)라고 쓰지 않는다. 행사가 없으면 사실대로 "아직 못 찾았다(데이터 준비 중)" 를 보인다.
import { h } from '../../lib/dom.js';
import { mockBadge } from '../../lib/mock-badge.js';
import { eventsView, mentionGroups } from '../../lib/chat-bundle.js';
import { eventNode, mentionGroupNode } from '../../lib/chat-bundle-view.js';

/** @returns {Node[]} 카드 영역에 그릴 노드들 */
export function bundleCardNodes(bundle, t, { mock = bundle.sample ? 'mock' : null } = {}) {
  const groups = mentionGroups(bundle);
  const ev = eventsView(bundle);
  return [
    h('section', { class: 'cb-section', dataset: { section: 'mentions' } },
      h('div', { class: 'cb-section__head' }, t('bundle.cards.record_title'), bundle.sample ? h('span', { class: 'cb-flag', dataset: { flag: 'sample' } }, t('bundle.sample')) : null, mock ? mockBadge(t, { kind: mock }) : null),
      groups.length ? groups.map((g) => mentionGroupNode(g, t)) : h('p', { class: 'cb-empty', dataset: { empty: 'mentions' } }, t('bundle.cards.no_record')),
      h('p', { class: 'cb-empty' }, t('bundle.cards.coverage')),
      bundle.coverage_note ? h('p', { class: 'cb-empty', dataset: { note: 'coverage' } }, bundle.coverage_note) : null),
    h('section', { class: 'cb-section', dataset: { section: 'events' } },
      h('div', { class: 'cb-section__head' }, t('bundle.events.title')),
      ev.empty ? h('p', { class: 'cb-empty', dataset: { empty: 'events' } }, t('bundle.events.none'))
        : h('ul', { class: 'cb-list' }, ev.items.map((e) => eventNode(e, t)))),
  ];
}
