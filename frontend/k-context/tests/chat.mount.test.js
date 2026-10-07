import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire, byAct, byClass, tick } from './_fakedom_ctsl.js';

installFakeDom();
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');
const chat = await import('../src/components/chat/index.js');

async function setup({ api } = {}) {
  const store = createStore(createInitialState());
  const realApi = api ?? createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api: realApi });
  const ctx = { store, api: realApi, t: createT(() => store.getState().lang), actions };
  await actions.loadAll();
  const root = new El('section', 'html');
  const m = chat.mount(root, ctx);
  const input = root.find((e) => e.tag === 'input')[0];
  return { store, ctx, root, m, input, api: realApi };
}
const bubbles = (root) => byClass(root, 'chat-msg');

test('mount: 샘플 4건 — 차단 응답은 data-blocked 와 라벨, 가정 한 줄은 assume', async () => {
  const { root } = await setup();
  const msgs = bubbles(root);
  assert.equal(msgs.length, 4);
  assert.equal(msgs[3].dataset.blocked, 'true');
  assert.match(msgs[3].text, /차단됨/);
  assert.equal(byClass(root, 'chat-msg__assume').length, 1);
  assert.equal(root.dataset?.module, undefined);
  assert.equal(root.find((e) => e.dataset?.module === 'chat').length, 1); // 스모크 테스트가 찾는 표식
  assert.equal(root.scrollTop, root.scrollHeight); // 하단 자동 스크롤
});

test('destroy: 슬롯을 비우고 구독을 끊는다', async () => {
  const { store, root, m } = await setup();
  m.destroy();
  assert.equal(root.children.length, 0);
  store.setState({ messages: [] }); // 던지지 않고, 다시 그리지도 않는다
  assert.equal(root.children.length, 0);
});

test('입력: input 이벤트는 store.input 으로, 조합 중 Enter 는 무시, 조합 끝난 Enter 는 전송', async () => {
  const { store, input, root } = await setup();
  input.value = '안녕';
  fire(input, 'input');
  assert.equal(store.getState().input, '안녕');
  fire(input, 'compositionstart');
  fire(input, 'keydown', { key: 'Enter' });
  assert.equal(store.getState().messages.length, 4); // 조합 중 — 전송 안 됨
  fire(input, 'compositionend');
  fire(input, 'keydown', { key: 'Enter', isComposing: true });
  fire(input, 'keydown', { key: 'Enter', keyCode: 229 });
  assert.equal(store.getState().messages.length, 4);
  const e = fire(input, 'keydown', { key: 'Enter' });
  assert.equal(e.defaultPrevented, true);
  assert.equal(store.getState().sending, true);
  assert.equal(store.getState().input, '');
  await tick(); await tick();
  assert.equal(store.getState().messages.length, 6);
  assert.equal(store.getState().sending, false);
  assert.equal(bubbles(root).length, 6);
});

test('중복 전송 방지: 전송 중 다시 눌러도 api.sendMessage 는 한 번', async () => {
  let calls = 0;
  const base = createApi({ mode: 'mock', latencyMs: 0 });
  const api = { ...base, async sendMessage(x) { calls += 1; await tick(); return base.sendMessage(x); } };
  const { store, input, root } = await setup({ api });
  store.setState({ input: '질문' });
  const btn = byAct(root, 'send')[0];
  fire(btn, 'click');
  fire(btn, 'click');
  fire(input, 'keydown', { key: 'Enter' });
  assert.equal(input.disabled, true); // 전송 중 입력 비활성
  assert.equal(btn.disabled, true);
  await tick(); await tick(); await tick();
  assert.equal(calls, 1);
  assert.equal(store.getState().messages.filter((m) => m.role === 'user').length, 3); // 샘플 2 + 새 1
});

test('예시 질문: 저녁은 바로 전송, 공격 시연·붙여넣기는 입력창만 채운다', async () => {
  const { store, root } = await setup();
  fire(byAct(root, 'suggest', 'attack')[0], 'click');
  assert.match(store.getState().input, /secret/);
  assert.equal(store.getState().messages.length, 4); // 보내지 않음
  assert.equal(root.find((e) => e.tag === 'input')[0].value, store.getState().input);
  fire(byAct(root, 'suggest', 'paste')[0], 'click');
  assert.match(store.getState().input, /○○/);
  assert.equal(byAct(root, 'suggest').length, 3);
  store.setState({ input: '' });
  fire(byAct(root, 'suggest', 'evening')[0], 'click');
  await tick(); await tick();
  const ms = store.getState().messages;
  assert.equal(ms.at(-2).text, '첫날 저녁에 뭐하지?');
  assert.equal(ms.at(-1).role, 'agent');
});

test('공격 프롬프트를 보내면 차단 응답과 deny 로그가 추가된다', async () => {
  const { store, root, input } = await setup();
  fire(byAct(root, 'suggest', 'attack')[0], 'click');
  const before = store.getState().logs.length;
  fire(input, 'keydown', { key: 'Enter' });
  await tick(); await tick();
  const s = store.getState();
  assert.equal(s.messages.at(-1).blocked, true);
  assert.equal(s.logs.length, before + 1);
  assert.equal(s.logs.at(-1).kind, 'deny');
  assert.equal(bubbles(root).at(-1).dataset.blocked, 'true');
});

test('실패: 오류 메시지와 재시도 — 재시도는 사용자 말풍선을 중복 만들지 않는다', async () => {
  const base = createApi({ mode: 'mock', latencyMs: 0 });
  let fail = true;
  const api = { ...base, async sendMessage(x) { if (fail) throw new Error('boom'); return base.sendMessage(x); } };
  const { store, root, input } = await setup({ api });
  input.value = '질문';
  fire(input, 'input');
  fire(input, 'keydown', { key: 'Enter' });
  await tick(); await tick();
  assert.equal(store.getState().sending, false);
  assert.equal(byClass(root, 'chat-error').length, 1);
  assert.match(byClass(root, 'chat-error')[0].text, /boom/);
  const users = () => store.getState().messages.filter((m) => m.text === '질문').length;
  assert.equal(users(), 1);
  fail = false;
  fire(byAct(root, 'retry')[0], 'click');
  await tick(); await tick();
  assert.equal(users(), 1);
  assert.equal(store.getState().messages.at(-1).role, 'agent');
  assert.equal(byClass(root, 'chat-error').length, 0);
});

test('언어 전환: 문구가 바뀌고 입력 값은 유지된다', async () => {
  const { store, root, input } = await setup();
  store.setState({ input: '유지' });
  assert.equal(input.value, '유지');
  store.setState({ lang: 'en' });
  assert.equal(input.value, '유지');
  assert.equal(byAct(root, 'suggest', 'evening')[0].text, 'What should I do on the first evening?');
  assert.equal(byAct(root, 'send')[0].text, 'Send');
});
