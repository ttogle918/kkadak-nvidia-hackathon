// 선택한 근거 항목 패널: 제목 · 설명 · 행(rows). 깔때기(채택/탈락 수)와 충돌 해결(채택/버림)은 표시를 더한다.
import { h } from '../../lib/dom.js';
import { conflictMarks, funnelRows } from './logic.js';

const markText = { adopted: 'rationale.row_adopted', dropped: 'rationale.row_dropped' };

function renderFunnel(rows, t) {
  return h('ul', { class: 'rationale-funnel' }, rows.map((r) => h('li', { class: `rationale-funnel__row is-${r.kind}` },
    h('span', { class: 'rationale-funnel__k' }, `${r.kind === 'adopted' ? '✓' : '✕'} ${t(r.k)}`),
    h('span', { class: 'rationale-funnel__bar', 'aria-hidden': 'true' },
      h('i', { style: { width: `${Math.max(4, Math.round(r.ratio * 100))}%` } })),
    h('b', { class: 'rationale-funnel__v' }, t(r.v)))));
}

function renderRows(item, t) {
  const marks = conflictMarks(item.rows, t);
  return h('dl', { class: 'rationale-rows' }, item.rows.map((r, i) => h('div', { class: ['rationale-row', marks[i] && `is-${marks[i]}`], dataset: { mark: marks[i] } },
    h('dt', null, t(r.k)),
    h('dd', null, t(r.v), marks[i] && h('span', { class: `rationale-mark is-${marks[i]}` }, ` ${marks[i] === 'adopted' ? '✓' : '✕'} ${t(markText[marks[i]])}`)))));
}

export function renderEvidencePanel(item, { t }) {
  const funnel = item.key === 'funnel' ? funnelRows(item.rows) : null;
  return h('section', { class: 'rationale-panel', role: 'region', 'aria-live': 'polite', 'aria-label': t('rationale.title') },
    h('header', { class: 'rationale-panel__head' },
      h('b', { class: 'rationale-panel__title' }, t(item.title)),
      h('button', { type: 'button', class: 'rationale-close', dataset: { act: 'close', fk: 'close' }, 'aria-label': t('rationale.close') }, '✕')),
    h('p', { class: 'rationale-panel__text' }, t(item.text)),
    funnel ? renderFunnel(funnel, t) : item.rows?.length > 0 && renderRows(item, t));
}

/** 걸러낸 주장 + 이유(지금 카드의 rejected). */
export function renderRejected(list, { t }) {
  if (!list.length) return null;
  return h('section', { class: 'rationale-rejected' },
    h('div', { class: 'rationale-label' }, t('rationale.rejected')),
    h('ul', null, list.map((r) => h('li', { class: 'rationale-rejected__item' },
      h('div', { class: 'rationale-rejected__claim' }, `✕ ${t(r.claim)}`),
      h('div', { class: 'rationale-rejected__reason' }, `${t('rationale.reason')}: ${t(r.reason)}`)))));
}
