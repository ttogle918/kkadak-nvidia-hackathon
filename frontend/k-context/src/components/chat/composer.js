// 입력창 + 보내기 버튼. 입력 노드는 한 번만 만들고 재사용한다(다시 그리면 포커스·IME 조합이 끊긴다).
import { h, render } from '../../lib/dom.js';
import { shouldSubmit, canSend } from './logic.js';

/**
 * @param {{t:Function, onInput(value:string):void, onSubmit():void}} p
 * @returns {{el:HTMLElement, input:HTMLElement, sync(state):void, relabel():void, destroy():void}}
 */
export function createComposer({ t, onInput, onSubmit }) {
  let composing = false;
  const input = h('input', {
    type: 'text', class: 'chat-composer__input', autocomplete: 'off', enterkeyhint: 'send',
    'aria-label': t('chat.input_label'), placeholder: t('chat.placeholder'),
    oninput: (e) => onInput(e.target.value),
    oncompositionstart: () => { composing = true; },
    oncompositionend: () => { composing = false; },
    onkeydown: (e) => {
      if (!shouldSubmit(e, composing)) return; // IME 조합 중·Shift+Enter 는 무시
      e.preventDefault?.();
      onSubmit();
    },
  });
  const sendBtn = h('button', { type: 'button', class: 'chat-composer__send', dataset: { act: 'send' }, onclick: () => onSubmit() }, t('chat.send'));
  const el = h('div', { class: 'chat-composer' }, input, sendBtn);

  return {
    el,
    input,
    /** store 상태를 입력창에 반영한다. 사용자가 치는 중에는 값을 덮어쓰지 않는다(같으면 건드리지 않음). */
    sync(state) {
      if (input.value !== state.input) input.value = state.input;
      const busy = !!state.sending;
      input.disabled = busy;
      sendBtn.disabled = !canSend(state);
      input.setAttribute('aria-busy', String(busy));
    },
    /** 언어가 바뀌었을 때 라벨만 바꾼다. */
    relabel() {
      input.setAttribute('placeholder', t('chat.placeholder'));
      input.setAttribute('aria-label', t('chat.input_label'));
      render(sendBtn, t('chat.send'));
    },
    destroy() { composing = false; },
  };
}
