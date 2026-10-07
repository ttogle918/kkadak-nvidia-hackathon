// 메시지 목록 렌더. API 문자열은 전부 h() 의 자식(텍스트 노드)으로만 넣는다.
import { h } from '../../lib/dom.js';
import { messageView } from './logic.js';

/** 말풍선 1개. 에이전트 메시지의 assume(가정 한 줄)·blocked(차단 응답)를 구분해 그린다. */
export function messageNode(m, t) {
  const v = messageView(m, t);
  return h('div', { class: ['chat-msg', `chat-msg--${v.role}`, v.blocked && 'chat-msg--blocked'], dataset: { role: v.role, blocked: v.blocked ? 'true' : null } },
    v.blocked ? h('span', { class: 'chat-msg__flag' }, '⊘ ', t('chat.blocked')) : null,
    h('div', { class: 'chat-msg__bubble' }, v.text),
    v.assume
      ? h('div', { class: 'chat-msg__assume' }, h('span', { class: 'chat-msg__assume-tag' }, t('chat.assumption')), v.assume)
      : null);
}

/**
 * @param {{messages:object[], sending:boolean, failed:null|{text:string,error:string}, t:Function, onRetry?:Function}} p
 * @returns {Node[]}
 */
export function messageListNodes({ messages, sending, failed, t, onRetry }) {
  const nodes = messages.map((m) => messageNode(m, t));
  if (sending) nodes.push(h('div', { class: 'chat-status', role: 'status', dataset: { state: 'sending' } }, t('chat.sending')));
  if (failed) {
    nodes.push(h('div', { class: 'chat-error', role: 'alert', dataset: { state: 'error' } },
      h('span', { class: 'chat-error__text' }, '✕ ', t('chat.error'), failed.error ? ` (${failed.error})` : ''),
      h('button', { type: 'button', class: 'chat-error__retry', dataset: { act: 'retry' }, onclick: onRetry }, t('chat.retry'))));
  }
  return nodes;
}
