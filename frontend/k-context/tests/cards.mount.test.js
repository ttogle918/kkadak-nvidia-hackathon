// cards 모듈 mount: 가짜 DOM 에서 렌더·클릭→상태 전이·팝오버·destroy 를 확인한다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { El, installDom, fire, byAct } from './_cr_fakedom.js';

const document = installDom();
const { mount } = await import('../src/components/cards/index.js');
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');

async function setup(overrides = {}) {
  const store = createStore(createInitialState(overrides));
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api });
  const t = createT(() => store.getState().lang);
  await actions.loadAll();
  const root = new El('section');
  const m = mount(root, { store, api, t, actions });
  return { store, api, actions, root, m };
}
const classOf = (el) => String(el.attrs.class ?? '');

test('옛날+지금 카드가 함께 그려지고 destroy 가 비운다', async () => {
  const { root, m } = await setup();
  assert.equal(root.find((e) => e.dataset?.kind === 'old').length, 1);
  assert.equal(root.find((e) => e.dataset?.kind === 'now').length, 1);
  assert.match(root.text, /지금은 덮인 물길 위/);
  assert.match(root.text, /설 A/);
  assert.match(root.text, /○○ 야장/);
  m.destroy();
  assert.equal(root.children.length, 0);
  assert.equal((document.listeners.keydown || []).length, 0);
});

test('mode 가 now 면 옛날 카드는 없다', async () => {
  const { root } = await setup({ mode: 'now' });
  assert.equal(root.find((e) => e.dataset?.kind === 'old').length, 0);
  assert.equal(root.find((e) => e.dataset?.kind === 'now').length, 1);
});

test('몰입 토글: 클릭하면 immersion 이 꺼지고 내레이션이 사라진다', async () => {
  const { root, store } = await setup({ mode: 'old' });
  assert.equal(root.find((e) => classOf(e) === 'cards-narration').length, 1);
  fire(root, 'click', byAct(root, 'toggle-imm'));
  assert.equal(store.getState().immersion, false);
  assert.equal(root.find((e) => classOf(e) === 'cards-narration').length, 0);
  assert.equal(byAct(root, 'toggle-imm').attrs['aria-checked'], 'false');
});

test('출처 태그 4개 이상이면 3개만 보이고 "+N 출처" 를 누르면 펼쳐진다', async () => {
  const { root, store } = await setup({ mode: 'now' }); // card_now_1: 출처 4개
  assert.equal(root.find((e) => e.dataset?.act === 'tag').length, 3);
  const more = byAct(root, 'more-tags');
  assert.match(more.text, /\+1/);
  fire(root, 'click', more);
  assert.equal(store.getState().expandedTags.card_now_1, true);
  assert.equal(root.find((e) => e.dataset?.act === 'tag').length, 4);
  assert.equal(byAct(root, 'more-tags'), undefined);
});

test('태그 클릭 → 팝오버(원문 구절·수집일) → Esc/닫기/바깥 클릭으로 닫힘', async () => {
  const { root, store } = await setup({ mode: 'old' });
  fire(root, 'click', byAct(root, 'tag', (e) => e.dataset.id === 'doc_02'));
  assert.equal(store.getState().selectedTag, 'doc_02');
  const dlg = root.find((e) => e.attrs?.role === 'dialog')[0];
  assert.ok(dlg);
  assert.equal(dlg.attrs['aria-modal'], 'true');
  assert.match(dlg.text, /예시 구절/);
  assert.match(dlg.text, /2026-10-05/);
  assert.match(dlg.text, /서울지명사전/);
  assert.equal(document.activeElement, byAct(root, 'pop-close')); // 포커스가 닫기 버튼으로
  // Esc
  for (const fn of document.listeners.keydown) fn({ key: 'Escape', target: dlg });
  assert.equal(store.getState().selectedTag, null);
  assert.equal(root.find((e) => e.attrs?.role === 'dialog').length, 0);
  // 닫기 버튼
  fire(root, 'click', byAct(root, 'tag'));
  fire(root, 'click', byAct(root, 'pop-close'));
  assert.equal(store.getState().selectedTag, null);
  // 바깥(backdrop) 클릭은 닫고, 안쪽 클릭은 안 닫는다
  fire(root, 'click', byAct(root, 'tag'));
  const backdrop = byAct(root, 'pop-backdrop');
  fire(root, 'click', root.find((e) => e.attrs?.role === 'dialog')[0]);
  assert.notEqual(store.getState().selectedTag, null);
  fire(root, 'click', backdrop);
  assert.equal(store.getState().selectedTag, null);
});

test('Tab 포커스 트랩: 마지막 요소에서 Tab 하면 처음으로 돌아온다(버튼 1개면 그대로)', async () => {
  const { root } = await setup({ mode: 'old' });
  fire(root, 'click', byAct(root, 'tag'));
  let prevented = 0;
  const close = byAct(root, 'pop-close');
  document.activeElement = close;
  for (const fn of document.listeners.keydown) fn({ key: 'Tab', shiftKey: false, preventDefault: () => prevented++ });
  assert.equal(prevented, 1);
  document.activeElement = null; // 팝오버 밖 포커스도 안으로 끌어온다
  for (const fn of document.listeners.keydown) fn({ key: 'Tab', shiftKey: false, preventDefault: () => prevented++ });
  assert.equal(document.activeElement, close);
});

test('사실 번호 호버/포커스 → hoverFact, 마우스를 떼면 해제, 하이라이트는 클래스로만 바뀐다', async () => {
  const { root, store } = await setup({ mode: 'old' });
  const ref = byAct(root, 'fact-ref', (e) => e.dataset.factRef === '2');
  fire(root, 'mouseover', ref);
  assert.equal(store.getState().hoverFact, 2);
  const fact2 = root.find((e) => e.dataset?.ref === '2')[0];
  assert.match(classOf(fact2), /is-hl/);
  assert.ok(byAct(root, 'fact-ref', (e) => e.dataset.factRef === '2') === ref); // 노드가 다시 그려지지 않았다
  fire(root, 'mouseout', ref);
  assert.equal(store.getState().hoverFact, null);
  assert.doesNotMatch(classOf(root.find((e) => e.dataset?.ref === '2')[0]), /is-hl/);
  fire(root, 'focusin', ref);
  assert.equal(store.getState().hoverFact, 2);
  fire(root, 'focusout', ref);
  assert.equal(store.getState().hoverFact, null);
});

test('지금 카드: 추가·건너뛰기가 기존 전이를 쓴다', async () => {
  const { root, store } = await setup({ mode: 'now' });
  fire(root, 'click', byAct(root, 'add'));
  assert.deepEqual([store.getState().added, store.getState().skipped], [true, false]);
  assert.equal(byAct(root, 'add').attrs['aria-pressed'], 'true');
  assert.match(byAct(root, 'add').text, /일정에 추가됨/);
  fire(root, 'click', byAct(root, 'skip'));
  assert.deepEqual([store.getState().added, store.getState().skipped], [false, true]);
});

test('보류 카드: 버튼이 disabled 이고 클릭해도 전이가 없다', async () => {
  const { root, store } = await setup({ mode: 'now', selectedNow: 'card_now_3' });
  const add = byAct(root, 'add');
  assert.equal(add.attrs.disabled, '');
  assert.equal(byAct(root, 'skip').attrs.disabled, '');
  assert.match(add.text, /결정 보류 중/);
  fire(root, 'click', add);
  fire(root, 'click', byAct(root, 'skip'));
  assert.deepEqual([store.getState().added, store.getState().skipped], [false, false]);
  assert.match(root.text, /자료끼리 달라요/); // 경고 박스
});

test('확인 필요 카드: "확인 후 추가" 와 단독 출처 경고', async () => {
  const { root } = await setup({ mode: 'now', selectedNow: 'card_now_2' });
  assert.match(byAct(root, 'add').text, /확인 후 추가/);
  assert.match(root.text, /단독 출처예요/);
});

test('local_context 링크 → selectedSeg 와 mode 가 갱신된다', async () => {
  const { root, store } = await setup({ mode: 'now', selectedSeg: 'card_old_1' });
  fire(root, 'click', byAct(root, 'local'));
  assert.deepEqual([store.getState().selectedSeg, store.getState().mode], ['card_old_4', 'both']);
  assert.equal(root.find((e) => e.dataset?.kind === 'old')[0].dataset.card, 'card_old_4');
});

test('언어를 en 으로 바꾸면 다시 그려진다', async () => {
  const { root, actions } = await setup({ mode: 'now' });
  actions.setLang('en');
  assert.match(root.text, /Night Market/);
  assert.match(root.text, /Add to itinerary/);
});

test('왜 골랐나요 → 근거 첫 칩을 연다', async () => {
  const { root, store } = await setup({ mode: 'now' });
  fire(root, 'click', byAct(root, 'why-pick'));
  await new Promise((r) => setTimeout(r, 5));
  assert.equal(store.getState().openEvidence, 'funnel');
});

test('왜 골랐나요: 응답 전에 카드가 바뀌면 근거를 열지 않는다(경쟁 상태)', async () => {
  const { root, store, actions } = await setup({ mode: 'now' });
  fire(root, 'click', byAct(root, 'why-pick'));
  actions.selectNow('card_now_2');
  await new Promise((r) => setTimeout(r, 5));
  assert.equal(store.getState().openEvidence, null);
});

test('API 문자열은 텍스트로만 들어간다(태그가 요소가 되지 않는다)', async () => {
  const { root, store } = await setup({ mode: 'old' });
  const cards = structuredClone(store.getState().data.cards);
  cards.find((c) => c.id === 'card_old_4').title = '<img src=x onerror=alert(1)>';
  store.setState({ data: { ...store.getState().data, cards } });
  assert.equal(root.find((e) => e.tag === 'img').length, 0);
  assert.match(root.text, /<img src=x/);
});
