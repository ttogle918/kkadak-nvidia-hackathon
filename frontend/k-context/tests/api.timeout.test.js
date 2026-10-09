import test from 'node:test';
import assert from 'node:assert/strict';
import { REQUEST_TIMEOUT_MS } from '../src/api/http.js';

// sprint-3 §6.4: F(프론트) 100초 > R(backend 파이프라인) 90초 > B(LLM 예산) 75초. 프론트가 먼저 끊으면 고정 문구를 못 받는다.
const BACKEND_PIPELINE_LIMIT_MS = 90_000;

test('프론트 요청 상한은 100초이고 backend 파이프라인 한도보다 10초 길다', () => {
  assert.equal(REQUEST_TIMEOUT_MS, 100_000);
  assert.equal(REQUEST_TIMEOUT_MS - BACKEND_PIPELINE_LIMIT_MS, 10_000);
});
