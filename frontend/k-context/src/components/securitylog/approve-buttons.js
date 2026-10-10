// [승인][거절] 버튼. 이 파일은 그리기만 한다 — 호출은 index.js 의 클릭 핸들러(사람이 누른 것)에서만 일어난다.
import { h } from '../../lib/dom.js';

/** @param {{entry:object, label:string, busy:boolean, t:Function, closed?:boolean}} p  closed: 공개 모드(getMeta().decisions === 'closed') — 버튼 대신 안내 문구 */
export function approveButtons({ entry, label, busy, t, closed = false }) {
  if (closed) return h('p', { class: 'securitylog-closed', role: 'note' }, t('log.decision_closed'));
  const btn = (decision, cls, key) => h('button', {
    type: 'button', class: ['securitylog-btn', cls], disabled: busy ? true : null,
    dataset: { act: 'decide', id: entry.id, value: decision },
    'aria-label': `${t(key)}: ${label}`,
  }, t(key));
  return h('div', { class: 'securitylog-actions', role: 'group', 'aria-label': t('log.human_only') },
    btn('approve', 'securitylog-btn--approve', 'log.approve'),
    btn('reject', 'securitylog-btn--reject', 'log.reject'));
}
