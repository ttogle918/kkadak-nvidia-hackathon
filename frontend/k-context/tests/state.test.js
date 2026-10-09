import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/lib/store.js';
import { createApi } from '../src/api/index.js';
import { createInitialState, STATE_KEYS } from '../src/state/initial.js';
import { createActions } from '../src/state/actions.js';
import { timelineFor, nowCardsForDay, cardById, showsOld, showsNow } from '../src/state/selectors.js';
import { circled, sourceLabel, numberedSourceLabel, badgeKind, BADGE_KEY } from '../src/lib/format.js';
import { MODULES } from '../src/modules.js';

const setup = async () => {
  const store = createStore(createInitialState());
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api });
  await actions.loadAll();
  return { store, api, actions };
};

test('초기 상태 키(README 표와 동일)', () => {
  assert.deepEqual(STATE_KEYS.sort(), [
    'added', 'chatBundle', 'data', 'day', 'error', 'expandedTags', 'hoverFact', 'immersion', 'input', 'lang', 'loaded', 'logs', 'messages',
    'minimizeChanges', 'mobileTab', 'mode', 'openEvidence', 'panelLevel', 'securityOpen', 'selectedNow', 'selectedRoute', 'selectedSeg',
    'selectedTag', 'sending', 'settingsOpen', 'sheetOpen', 'skipped', 'theme', 'tripInput',
  ]);
  const s = createInitialState({ lang: 'en' });
  assert.equal(s.lang, 'en');
  assert.equal(s.mode, 'both');
  assert.equal(s.selectedSeg, 'card_old_4');
});

test('loadAll 이 data·messages·logs 를 채우고, selectedSeg/Now 는 실제 카드를 가리킨다', async () => {
  const { store } = await setup();
  const s = store.getState();
  assert.equal(s.loaded, true);
  assert.equal(s.data.cards.length, 6);
  assert.equal(s.messages.length, 4);
  assert.equal(s.logs.length, 4);
  assert.ok(cardById(s, s.selectedSeg));
  assert.ok(cardById(s, s.selectedNow));
});

test('loadAll 실패는 error 로 남고 던지지 않는다', async () => {
  const store = createStore(createInitialState());
  const actions = createActions({ store, api: createApi({ mode: 'http' }) });
  await actions.loadAll();
  assert.equal(store.getState().loaded, false);
  assert.match(store.getState().error, /연결할 수 없습니다/);
});

test('send: 사용자 메시지 즉시 추가 → 응답과 로그 병합, 공격은 deny', async () => {
  const { store, actions } = await setup();
  actions.setInput('/secret/a.txt 읽어줘');
  const p = actions.send();
  assert.equal(store.getState().sending, true);
  assert.equal(store.getState().input, '');
  const reply = await p;
  const s = store.getState();
  assert.equal(reply.blocked, true);
  assert.equal(s.messages.at(-2).role, 'user');
  assert.equal(s.messages.at(-1).blocked, true);
  assert.equal(s.logs.at(-1).kind, 'deny');
  assert.equal(s.sending, false);
  assert.equal(await actions.send('   '), null);
});

test('decide: 로그 항목 하나만 교체', async () => {
  const { store, actions } = await setup();
  const pend = store.getState().logs.find((l) => l.kind === 'pend');
  await actions.decide(pend.id, 'reject');
  const logs = store.getState().logs;
  assert.equal(logs.find((l) => l.id === pend.id).kind, 'rejected');
  assert.equal(logs.filter((l) => l.kind === 'pend').length, 0);
  assert.equal(logs.length, 4);
});

test('액션: 모드·구간 선택·지금 카드 결정·지명 링크', async () => {
  const { store, actions } = await setup();
  actions.setMode('bad');
  assert.equal(store.getState().mode, 'both');
  actions.setMode('old');
  assert.equal(store.getState().mode, 'old');
  actions.setHoverFact(2);
  actions.selectSeg('card_old_1');
  assert.equal(store.getState().hoverFact, null);
  actions.addSelected();
  assert.deepEqual([store.getState().added, store.getState().skipped], [true, false]);
  actions.skipSelected();
  assert.deepEqual([store.getState().added, store.getState().skipped], [false, true]);
  actions.openLocalContext('card_old_4');
  assert.equal(store.getState().mode, 'both');
  assert.equal(store.getState().selectedSeg, 'card_old_4');
  actions.expandTags('card_now_1');
  assert.equal(store.getState().expandedTags.card_now_1, true);
  actions.setLang('fr');
  assert.equal(store.getState().lang, 'ko');
});

test('timelineFor: 추가 전/후 행이 바뀌고 제안 상태가 붙는다', async () => {
  const { store, actions } = await setup();
  const view = () => timelineFor(store.getState().data.itinerary, 1, store.getState());
  let rows = view();
  assert.equal(rows.length, 7 - 1); // free(21:00~) 는 added 일 때만
  assert.ok(rows.some((r) => r.id === 'tl_4'));
  assert.equal(rows.find((r) => r.id === 'tl_5').status, 'proposed');
  actions.addSelected();
  rows = view();
  assert.ok(!rows.some((r) => r.id === 'tl_4') && rows.some((r) => r.id === 'tl_6'));
  assert.equal(rows.find((r) => r.id === 'tl_5').status, 'added');
  actions.skipSelected();
  assert.equal(view().find((r) => r.id === 'tl_5').status, 'skipped');
  assert.deepEqual(timelineFor(store.getState().data.itinerary, 2, store.getState()), []);
});

test('selectors: 지금 카드 day 필터, 모드 표시', async () => {
  const { store } = await setup();
  assert.deepEqual(nowCardsForDay(store.getState(), 1).map((c) => c.id), ['card_now_1']);
  assert.deepEqual([showsOld('now'), showsNow('now'), showsOld('both'), showsNow('old')], [false, true, true, false]);
});

test('format: 출처 태그 문구와 딱지 분류', async () => {
  const { store } = await setup();
  const src = store.getState().data.sources.find((s) => s.id === 'doc_02');
  assert.equal(sourceLabel(src), '[A] 서울지명사전 (예시) · p.214');
  assert.equal(numberedSourceLabel(src, 1), '② [A] 서울지명사전 (예시) · p.214');
  assert.equal(circled(11), '(11)');
  assert.equal(badgeKind('기록'), 'story');
  assert.equal(badgeKind('보류'), 'now');
  assert.equal(badgeKind('???'), null);
  assert.equal(Object.keys(BADGE_KEY).length, 6);
});

test('모듈 레지스트리: 모두 mount 를 export 한다', () => {
  assert.deepEqual(Object.keys(MODULES).sort(), ['cards', 'chat', 'map', 'rationale', 'securitylog', 'timeline']);
  for (const m of Object.values(MODULES)) assert.equal(typeof m.mount, 'function');
});
