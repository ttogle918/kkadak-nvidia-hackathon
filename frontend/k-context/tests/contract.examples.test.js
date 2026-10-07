// 공통 계약 예제 테스트 — domains/kcontext/contract/examples 의 JSON 을 프론트 검증기(src/api/schema.js)로 돌린다.
// Python 검증기(domains/kcontext/contract)와 같은 예제 파일을 공유해서 두 구현이 어긋나면 한쪽이 깨진다.
//
// 한계(알려진 차이):
//  - schema.js 의 isCoord 는 "숫자 2개짜리 배열"인지만 본다. 좌표 순서([lat,lng] 인지)·범위를 구분하지 못한다.
//    그래서 bad/ 예제는 양쪽이 모두 잡는 위반(필수 필드 누락·딱지 불일치·빈 sources·segment 1점·slot.day 누락 등)만 넣고,
//    좌표 범위·REJECT_REASONS·ROUTE_BADGES·estimated bool·facts.ref·radius_m 은 Python 전용 테스트가 맡는다.
//  - 현재 schema.js 는 story 카드에 narration 을 필수로 요구한다(계약 보충 5 는 null 허용, T219 가 고친다).
//    그래서 정상 예제의 story 카드는 narration 이 있는 것만 둔다.
//  - verdict.json·situation.json 은 프론트에 검증기가 없어 Python 쪽만 검사한다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { validateCard, validateRoute, validateSource } from '../src/api/schema.js';

const EX = fileURLToPath(new URL('../../../domains/kcontext/contract/examples/', import.meta.url));
const load = (path) => JSON.parse(readFileSync(path, 'utf8'));
const jsonFiles = (dir) => readdirSync(dir).filter((f) => f.endsWith('.json')).sort();

const run = (kind, obj, cardIds = null) => {
  if (kind === 'card') return validateCard(obj);
  if (kind === 'route') return validateRoute(obj, cardIds);
  if (kind === 'source') return validateSource(obj);
  throw new Error(`알 수 없는 kind: ${kind}`);
};

const GOOD = [
  ['card_story.json', 'card'],
  ['card_now.json', 'card'],
  ['route.json', 'route'],
  ['source.json', 'source'],
];

for (const [file, kind] of GOOD) {
  test(`정상 예제 ${file} 는 문제 0건`, () => {
    const obj = load(EX + file);
    const cardIds = kind === 'route' ? ['card_example_story', 'card_example_now'] : null;
    assert.deepEqual(run(kind, obj, cardIds), []);
  });
}

test('정상 예제는 모두 합성 표시(○○)를 가진다', () => {
  for (const file of ['card_story.json', 'card_now.json', 'route.json']) {
    assert.ok(readFileSync(EX + file, 'utf8').includes('○○'), file);
  }
});

const BAD_DIR = EX + 'bad/';
const badFiles = jsonFiles(BAD_DIR);

test('bad 예제가 있다', () => {
  assert.ok(badFiles.length >= 5, `bad 예제 ${badFiles.length}개`);
});

for (const file of badFiles) {
  test(`bad 예제 ${file} 는 문제 1건 이상`, () => {
    const { kind, obj, expect } = load(BAD_DIR + file);
    assert.ok(['card', 'route', 'source'].includes(kind), `kind ${kind}`);
    assert.ok(Array.isArray(expect) && expect.length > 0, 'expect 는 비어 있지 않은 배열');
    const cardIds = kind === 'route' ? ['card_example_story'] : null;
    const problems = run(kind, obj, cardIds);
    assert.ok(problems.length >= 1, `${file}: 문제가 잡히지 않음`);
  });
}
