// 로그 행 1개: 시각 · 아이콘+글자 라벨 · 본문. 차단(pend)에만 승인/거절 버튼.
import { h } from '../../lib/dom.js';
import { metaOf, canDecide, decidedNoteKey } from './logic.js';
import { approveButtons } from './approve-buttons.js';

/** @param {{entry:object, t:Function, busy:boolean, error:string|null}} p */
export function logRowNode({ entry, t, busy = false, error = null }) {
  const meta = metaOf(entry.kind);
  const text = typeof entry.text === 'string' ? entry.text : t(entry.text);
  const note = decidedNoteKey(entry);
  return h('li', { class: 'securitylog-row', dataset: { kind: entry.kind, id: entry.id } },
    h('div', { class: 'securitylog-row__head' },
      h('span', { class: 'securitylog-row__time' }, entry.time),
      h('b', { class: 'securitylog-row__label' }, h('span', { 'aria-hidden': 'true' }, meta.icon, ' '), meta.labelKey ? t(meta.labelKey) : String(entry.kind))),
    h('div', { class: 'securitylog-row__text' }, text, note ? h('span', { class: 'securitylog-row__note' }, ` → ${t(note)}`) : null),
    canDecide(entry) ? approveButtons({ entry, label: text, busy, t }) : null,
    error ? h('div', { class: 'securitylog-row__error', role: 'alert' }, '✕ ', t('securitylog.decide_failed'), ` (${error})`) : null);
}
