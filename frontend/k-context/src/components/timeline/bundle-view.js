// 챗봇이 정리한 일정(chatBundle)의 타임라인. 고정 샘플 일정과 구분되도록 제목·"챗봇이 정리했어요" 표시를 둔다.
// 행 모양은 기존 timelineRowNode 를 재사용한다. 외부 문자열은 전부 텍스트 노드로만 들어간다.
import { h } from '../../lib/dom.js';
import { bundleDayDate, bundleDays, bundleTimelineFor, problemLines } from '../../lib/chat-bundle.js';
import { STATUS_META } from './logic.js';
import { timelineRowNode } from './timeline-row.js';

function rowNode(r, t) {
  const node = timelineRowNode({ ...r, meta: STATUS_META[r.status] }, t);
  if (r.kind !== 'free') return node;
  // 빈 시간: 추정 가정 문구(assumption)와 가까운 곳을 한 줄 덧붙인다
  const bits = [r.near ? t(r.near) : null, r.assumption ? t(r.assumption) : null, r.inferred ? t('timeline.bundle.inferred') : null].filter(Boolean);
  if (bits.length) node.appendChild(h('div', { class: 'timeline-row__note' }, bits.join(' · ')));
  return node;
}

/** @param {object} bundle 검증된 chatBundle  @param {number} day 선택한 날(없는 날이면 첫 날로 본다) */
export function bundleTimelineNode(bundle, day, t) {
  const days = bundleDays(bundle);
  const cur = days.includes(day) ? day : (days[0] ?? 0);
  const rows = bundleTimelineFor(bundle, cur);
  const date = bundleDayDate(bundle, cur);
  const problems = problemLines(bundle);
  return h('div', { class: 'timeline timeline--bundle', dataset: { module: 'timeline', source: 'chat-bundle' } },
    h('div', { class: 'timeline__head' },
      h('span', { class: 'timeline__title' }, t('timeline.bundle.title')),
      bundle.sample ? h('span', { class: 'cb-flag', dataset: { flag: 'sample' } }, t('bundle.sample')) : null,
      h('button', { type: 'button', class: 'timeline-min', dataset: { act: 'clear-bundle' } }, t('timeline.bundle.back'))),
    days.length ? h('div', { class: 'timeline-days', role: 'tablist', 'aria-label': t('timeline.days') },
      days.map((d) => h('button', {
        type: 'button', role: 'tab', class: ['timeline-days__btn', d === cur && 'is-on'], 'aria-selected': String(d === cur),
        dataset: { act: 'day', value: d },
      }, d === 0 ? t('timeline.bundle.undated') : t('topbar.day', { n: d })))) : null,
    days.length ? h('div', { class: 'timeline__day' }, cur === 0 ? t('timeline.bundle.undated') : `DAY ${cur}`, date ? h('span', { class: 'timeline__date' }, ` · ${date}`) : null) : null,
    rows.length ? h('ol', { class: 'timeline__rows' }, rows.map((r) => rowNode(r, t)))
      : h('p', { class: 'timeline__empty', role: 'status' }, t('timeline.empty')),
    problems.length ? h('ul', { class: 'timeline-problems', 'aria-label': t('timeline.bundle.problems') },
      problems.map((p) => h('li', { class: 'timeline-problems__item', dataset: { code: p.code } }, p.key ? t(p.key) : p.message))) : null);
}
