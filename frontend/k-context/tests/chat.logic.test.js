import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pickText, messageView, shouldSubmit, isComposingEvent, canSend, SUGGESTIONS } from '../src/components/chat/logic.js';
import { translate } from '../src/lib/i18n.js';

const t = (v) => translate('ko', v);

test('pickText: 문자열은 사전 키로 해석하지 않고, {ko,en} 은 t 로 고른다', () => {
  assert.equal(pickText('chat.send', t), 'chat.send'); // 사용자가 키 모양 문자열을 쳐도 그대로
  assert.equal(pickText({ ko: '안녕', en: 'hi' }, t), '안녕');
  assert.equal(pickText(null, t), '');
});

test('messageView: 에이전트만 assume·blocked 를 가진다', () => {
  const a = messageView({ id: '1', role: 'agent', text: { ko: '답', en: 'a' }, assume: { ko: '가정', en: 'as' }, blocked: true }, t);
  assert.deepEqual([a.role, a.text, a.assume, a.blocked], ['agent', '답', '가정', true]);
  const u = messageView({ id: '2', role: 'user', text: 'q', assume: { ko: 'x' }, blocked: true }, t);
  assert.deepEqual([u.role, u.assume, u.blocked], ['user', '', false]);
});

test('shouldSubmit: Enter 만 전송, Shift+Enter·IME 조합 중은 무시', () => {
  assert.equal(shouldSubmit({ key: 'Enter' }), true);
  assert.equal(shouldSubmit({ key: 'Enter', shiftKey: true }), false);
  assert.equal(shouldSubmit({ key: 'Enter', isComposing: true }), false);
  assert.equal(shouldSubmit({ key: 'Enter', keyCode: 229 }), false);
  assert.equal(shouldSubmit({ key: 'Enter' }, true), false);
  assert.equal(shouldSubmit({ key: 'a' }), false);
  assert.equal(isComposingEvent({}, false), false);
});

test('canSend: 빈 입력·전송 중이면 불가', () => {
  assert.equal(canSend({ input: ' ', sending: false }), false);
  assert.equal(canSend({ input: 'a', sending: true }), false);
  assert.equal(canSend({ input: 'a', sending: false }), true);
});

test('예시 질문은 3개이고 공격 시연은 입력창만 채운다(보내기는 사람)', () => {
  assert.equal(SUGGESTIONS.length, 3);
  assert.equal(SUGGESTIONS.find((s) => s.id === 'attack').kind, 'fill');
  assert.equal(SUGGESTIONS.find((s) => s.id === 'evening').kind, 'send');
});
