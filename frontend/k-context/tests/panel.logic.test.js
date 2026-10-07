// 하단 패널 단계 전이·스냅 계산(순수 함수)과 store 액션.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PANEL_LEVELS, COLLAPSED_PX, stepLevel, toggleLevel, levelHeight, clampHeight, snapLevel, dragHeight, isLevel,
} from '../src/lib/panel-level.js';
import { createStore } from '../src/lib/store.js';
import { createInitialState } from '../src/state/initial.js';
import { createActions } from '../src/state/actions.js';

test('stepLevel: 한 단계씩 오르내리고 양 끝에서 멈춘다', () => {
  assert.deepEqual(PANEL_LEVELS, ['collapsed', 'default', 'expanded']);
  assert.equal(stepLevel('collapsed', 1), 'default');
  assert.equal(stepLevel('default', 1), 'expanded');
  assert.equal(stepLevel('expanded', 1), 'expanded');
  assert.equal(stepLevel('expanded', -1), 'default');
  assert.equal(stepLevel('default', -1), 'collapsed');
  assert.equal(stepLevel('collapsed', -1), 'collapsed');
  assert.equal(stepLevel('이상한값', 1), 'expanded', '모르는 값은 기본으로 보고 계산');
  assert.equal(stepLevel('default', 0), 'default');
});

test('toggleLevel: 접힘<->기본, 펼침은 기본으로', () => {
  assert.equal(toggleLevel('collapsed'), 'default');
  assert.equal(toggleLevel('default'), 'collapsed');
  assert.equal(toggleLevel('expanded'), 'default');
});

test('levelHeight: 1/3 · 70% · 48px', () => {
  assert.equal(levelHeight('collapsed', 900), COLLAPSED_PX);
  assert.equal(levelHeight('default', 900), 300);
  assert.equal(levelHeight('expanded', 1000), 700);
});

test('clampHeight·dragHeight: 접힘~펼침 범위, 위로 끌면 커진다', () => {
  assert.equal(clampHeight(10, 900), 48);
  assert.equal(clampHeight(5000, 900), 630);
  assert.equal(dragHeight(300, 500, 400, 900), 400); // 100px 위로
  assert.equal(dragHeight(300, 500, 700, 900), 100); // 200px 아래로
  assert.equal(dragHeight(300, 500, 1500, 900), 48);
});

test('snapLevel: 가장 가까운 단계로(경계는 높이 중간)', () => {
  assert.equal(snapLevel(48, 900), 'collapsed');
  assert.equal(snapLevel(150, 900), 'collapsed'); // 48 과 300 의 중간 174 미만
  assert.equal(snapLevel(180, 900), 'default');
  assert.equal(snapLevel(300, 900), 'default');
  assert.equal(snapLevel(450, 900), 'default'); // 300 과 630 의 중간 465 미만
  assert.equal(snapLevel(480, 900), 'expanded');
  assert.equal(snapLevel(630, 900), 'expanded');
});

test('액션: setPanelLevel(유효값만)·stepPanel, 기본 default', () => {
  const store = createStore(createInitialState());
  const actions = createActions({ store, api: {} });
  assert.equal(store.getState().panelLevel, 'default');
  actions.setPanelLevel('collapsed');
  assert.equal(store.getState().panelLevel, 'collapsed');
  actions.setPanelLevel('bogus');
  assert.equal(store.getState().panelLevel, 'collapsed', '잘못된 값은 무시');
  actions.stepPanel(1); actions.stepPanel(1); actions.stepPanel(1);
  assert.equal(store.getState().panelLevel, 'expanded');
  actions.stepPanel(-1);
  assert.equal(store.getState().panelLevel, 'default');
  assert.equal(isLevel('default'), true);
});

test('선택 카드가 바뀌어도 접어 둔 패널은 그대로(자동 펼침 없음)', () => {
  const store = createStore(createInitialState({ panelLevel: 'collapsed' }));
  const actions = createActions({ store, api: {} });
  actions.selectSeg('card_old_1'); actions.selectNow('card_now_2');
  assert.equal(store.getState().panelLevel, 'collapsed');
});
