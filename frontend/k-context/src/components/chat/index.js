// chat 모듈: 대화 목록 · 예시 질문 · 입력창. 계약: mount(root, ctx) -> {destroy()}.
// 전송은 actions.trySend(→ api.sendMessage) 만 쓴다. 응답은 actions 가 messages·logs 에 반영한다.
import { h, on, render } from '../../lib/dom.js';
import { messageListNodes } from './message-list.js';
import { suggestionsNode } from './suggestions.js';
import { createComposer } from './composer.js';
import { SUGGESTIONS, canSend } from './logic.js';

/**
 * @param {HTMLElement} root app-shell 이 준 슬롯 div
 * @param {{store, api, t, actions}} ctx
 */
export function mount(root, ctx) {
  const { store, t, actions } = ctx;
  let failed = null; // 마지막 전송 실패: {text, error}
  let inflight = false; // 중복 전송 방지(상태 sending 과 함께 이중 방어)
  let destroyed = false;

  const list = h('div', { class: 'chat-list', role: 'log', 'aria-live': 'polite', 'aria-label': t('chat.log_label') });
  const suggestHost = h('div', { class: 'chat-suggest-host' });
  const composer = createComposer({
    t,
    onInput: (v) => actions.setInput(v),
    onSubmit: () => submit(),
  });
  const wrap = h('div', { class: 'chat', dataset: { module: 'chat' } },
    list, h('div', { class: 'chat-foot' }, suggestHost, composer.el));
  render(root, wrap);

  /** 전송. text 를 주면 그 문장(재시도), 없으면 입력창 값. */
  async function submit(text, { retry = false } = {}) {
    const s = store.getState();
    if (inflight || s.sending) return null;
    if (text == null && !canSend(s)) return null;
    inflight = true;
    failed = null;
    const sentText = String(text ?? s.input).trim();
    let r;
    try {
      r = await actions.trySend(sentText, { retry });
    } finally {
      inflight = false;
    }
    if (destroyed) return r;
    if (!r.ok && r.reason === 'error') failed = { text: sentText, error: r.error };
    drawList();
    composer.sync(store.getState());
    if (r.ok) composer.input.focus?.();
    return r;
  }

  function drawList() {
    const s = store.getState();
    render(list, messageListNodes({
      messages: s.messages, sending: s.sending, failed, t,
      onRetry: () => submit(failed?.text, { retry: true }),
    }));
    // 새 메시지가 오면 맨 아래로 — 스크롤하는 건 슬롯(root)이다
    root.scrollTop = root.scrollHeight;
  }
  function drawSuggest() {
    render(suggestHost, suggestionsNode(t));
  }

  const offClick = on(root, 'click', '[data-act="suggest"]', (_e, el) => {
    const def = SUGGESTIONS.find((x) => x.id === el.dataset.id);
    if (!def) return;
    const text = t(def.textKey);
    if (def.kind === 'send') {
      submit(text);
    } else {
      // 채우기만 한다 — 보내는 것은 사람이 보내기를 눌러서
      actions.setInput(text);
      composer.input.focus?.();
    }
  });

  drawList();
  drawSuggest();
  composer.sync(store.getState());

  const eq = (a, b) => a.every((v, i) => v === b[i]);
  const offList = store.select((s) => [s.messages, s.sending, s.lang], () => { drawList(); }, { equals: eq });
  const offLang = store.select((s) => s.lang, () => { drawSuggest(); composer.relabel(); });
  const offInput = store.select((s) => [s.input, s.sending], () => composer.sync(store.getState()), { equals: eq });

  return {
    destroy() {
      destroyed = true;
      offClick(); offList(); offLang(); offInput();
      composer.destroy();
      root.replaceChildren();
    },
  };
}
