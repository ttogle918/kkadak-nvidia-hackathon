import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/lib/store.js';

test('setState 는 얕은 병합이고 새 객체를 만든다(불변)', () => {
  const st = createStore({ a: 1, b: { x: 1 } });
  const before = st.getState();
  st.setState({ a: 2 });
  assert.equal(before.a, 1);
  assert.equal(st.getState().a, 2);
  assert.equal(st.getState().b, before.b);
  assert.notEqual(st.getState(), before);
  assert.throws(() => { 'use strict'; st.getState().a = 9; }, TypeError);
});

test('함수형 patch 와 변경 없음(알림 생략)', () => {
  const st = createStore({ n: 1 });
  let calls = 0;
  st.subscribe(() => calls++);
  st.setState((s) => ({ n: s.n + 1 }));
  st.setState({ n: 2 }); // 같은 값
  assert.equal(calls, 1);
  assert.equal(st.getState().n, 2);
});

test('subscribe 는 (state, prev) 를 받고 해제할 수 있다', () => {
  const st = createStore({ n: 0 });
  const seen = [];
  const off = st.subscribe((s, p) => seen.push([p.n, s.n]));
  st.setState({ n: 1 });
  off();
  st.setState({ n: 2 });
  assert.deepEqual(seen, [[0, 1]]);
});

test('select 는 파생값이 바뀔 때만 부르고 fire 옵션이 있다', () => {
  const st = createStore({ a: 1, b: 1 });
  const seen = [];
  st.select((s) => s.a, (v, p) => seen.push([p, v]), { fire: true });
  st.setState({ b: 2 }); // a 는 그대로
  st.setState({ a: 5 });
  assert.deepEqual(seen, [[undefined, 1], [1, 5]]);
});

test('배열·객체는 새 참조로 넣어야 알림이 간다', () => {
  const st = createStore({ list: [] });
  let calls = 0;
  st.subscribe(() => calls++);
  st.setState((s) => ({ list: [...s.list, 1] }));
  assert.equal(calls, 1);
});
