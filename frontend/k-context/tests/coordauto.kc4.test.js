import { test } from 'node:test';
import assert from 'node:assert/strict';
import { problemLines } from '../src/lib/chat-bundle.js';
import ko from '../src/i18n/ko.js';
import en from '../src/i18n/en.js';

const anchors = [{ name: '서울상상나라' }, { name: '다른곳' }];

test('COORD_AUTO: 이름이 앵커와 같으면 .named, 서버 문구는 쓰지 않는다', () => {
  const lines = problemLines({ itinerary: { anchors }, problems: [
    { code: 'COORD_AUTO', message: '서울상상나라: 공공 데이터 좌표(사람 확인 전)' },
    { code: 'COORD_AUTO', message: '서울상상나라: 공공 데이터 좌표(사람 확인 전)' },
    { code: 'COORD_AUTO', message: '다른곳: x' },
  ] });
  assert.deepEqual(lines.map((l) => [l.key, l.params?.name]), [
    ['bundle.problem.coord_auto.named', '서울상상나라'], ['bundle.problem.coord_auto.named', '다른곳'],
  ]);
});

test('COORD_AUTO: 앵커에 없는 이름은 이름 없는 고정 문구', () => {
  const [l] = problemLines({ itinerary: { anchors }, problems: [{ code: 'COORD_AUTO', message: '<b>x</b>: y' }] });
  assert.equal(l.key, 'bundle.problem.coord_auto');
  assert.ok(!('params' in l));
});

test('i18n: 고정 문구 "공공 데이터 좌표(사람 확인 전)" · en 도 두 키 모두 있다', () => {
  assert.equal(ko['bundle.problem.coord_auto'], '공공 데이터 좌표(사람 확인 전)');
  assert.equal(ko['bundle.problem.coord_auto.named'], '{name}: 공공 데이터 좌표(사람 확인 전)');
  for (const k of ['bundle.problem.coord_auto', 'bundle.problem.coord_auto.named']) assert.ok(en[k]);
});
