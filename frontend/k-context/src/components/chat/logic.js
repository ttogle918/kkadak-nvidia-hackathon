// chat 순수 로직 — DOM 없이 테스트한다.

/** 사용자 입력 문자열은 사전 키로 해석하지 않고 그대로, {ko,en} 객체만 t 로 고른다. */
export function pickText(value, t) {
  if (value == null) return '';
  return typeof value === 'string' ? value : t(value);
}

/** Message -> 화면용 값. */
export function messageView(m, t) {
  const agent = m.role === 'agent';
  return {
    id: m.id,
    role: agent ? 'agent' : 'user',
    text: pickText(m.text, t),
    assume: agent && m.assume ? pickText(m.assume, t) : '',
    blocked: agent && !!m.blocked,
  };
}

/** 한글 IME 조합 중 Enter 는 전송이 아니다(조합 확정용). keyCode 229 는 일부 브라우저의 조합 신호. */
export function isComposingEvent(e, composing = false) {
  return !!composing || !!e?.isComposing || e?.keyCode === 229;
}

/** keydown 이벤트가 전송을 뜻하는가. Shift+Enter 와 IME 조합 중 Enter 는 제외한다. */
export function shouldSubmit(e, composing = false) {
  return e?.key === 'Enter' && !e.shiftKey && !isComposingEvent(e, composing);
}

/** 전송 가능한가 — 비어 있거나 전송 중이면 불가(중복 전송 방지). */
export function canSend({ input, sending }) {
  return !sending && String(input ?? '').trim().length > 0;
}

/** 예시 질문 3개. kind: 'send'(바로 전송) | 'fill'(입력창만 채움 — 보내는 건 사람이 한다). textKey 는 i18n 키. */
export const SUGGESTIONS = [
  { id: 'evening', kind: 'send', labelKey: 'chat.ask_evening', textKey: 'chat.ask_evening' },
  { id: 'attack', kind: 'fill', labelKey: 'chat.suggest.attack', textKey: 'chat.suggest.attack_prompt', dashed: true },
  { id: 'paste', kind: 'fill', labelKey: 'chat.suggest.paste', textKey: 'chat.suggest.paste_text' },
];
