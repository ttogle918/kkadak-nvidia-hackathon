// 챗봇 묶음 순수 로직: 타임라인 선택자·핀 수집·정보창 내용·행사 상태·핀 좌표 변환.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateChatBundle } from '../src/api/bundle.js';
import { CHAT_BUNDLE_SAMPLE } from '../src/data/chat-bundle.js';
import {
  bundleDays, bundleTimelineFor, bundlePins, pinInfo, mentionGroups, eventsView, problemLines, timeLabel, bundleDayDate,
} from '../src/lib/chat-bundle.js';
import { projectPins } from '../src/components/map/chat-layer.js';

const B = () => validateChatBundle(structuredClone(CHAT_BUNDLE_SAMPLE)).bundle;

test('timeLabel', () => {
  assert.equal(timeLabel('2026-10-15T10:00', '2026-10-15T12:30'), '10:00–12:30');
  assert.equal(timeLabel('2026-10-15T19:00', null), '19:00 ~');
  assert.equal(timeLabel(null, null), '');
  assert.equal(timeLabel('2026-10-15', null), '');
});

test('타임라인: 날짜별 행(시각순), 호텔은 체크인/아웃 날짜에, 빈 시간은 가정 문구 포함', () => {
  const b = B();
  assert.deepEqual(bundleDays(b), [1, 2, 3, 4]);
  const d1 = bundleTimelineFor(b, 1);
  assert.deepEqual(d1.map((r) => r.title.ko ?? r.title), ['창덕궁', '익선동', '숙소 · 종로3가 (예시)', 'timeline.free']);
  assert.equal(d1[0].time, '10:00–12:30');
  assert.equal(d1[2].sub, 'timeline.bundle.checkin');
  const free = d1[3];
  assert.equal(free.status, 'free');
  assert.equal(free.assumption.ko, '1일차 저녁 7시 이후가 비어 있다고 봤어요.');
  assert.equal(free.inferred, true);
  assert.equal(bundleTimelineFor(b, 4).at(0).sub, 'timeline.bundle.checkout');
  assert.equal(bundleDayDate(b, 2), '10/16');
});

test('타임라인: 시각 없는 앵커는 사실대로 표시(timeUnknown), 날짜 없으면 날짜 미정(0)', () => {
  const b = B();
  const d2 = bundleTimelineFor(b, 2);
  assert.equal(d2[0].timeUnknown, true);
  assert.equal(d2[0].sub, 'timeline.bundle.no_time');
  const loose = { ...b, trip: null, itinerary: { anchors: [{ type: 'visit', name: '어딘가', day: null, from: null, to: null, lat: null, lng: null }], free_slots: [] } };
  assert.deepEqual(bundleDays(loose), [0]);
  assert.equal(bundleTimelineFor(loose, 0).length, 1);
});

test('핀 수집: 좌표 없는 앵커(호텔·신촌)는 제외, 있는 3곳만', () => {
  const pins = bundlePins(B());
  assert.deepEqual(pins.map((p) => p.name), ['창덕궁', '익선동', '경복궁']);
  assert.deepEqual(pins.map((p) => p.count), [2, 0, 1]);
  const none = { ...B(), itinerary: { anchors: [{ type: 'visit', name: '신촌', lat: null, lng: null }], free_slots: [] } };
  assert.deepEqual(bundlePins(none), []);
});

test('정보창 내용: 이름·건수·상위 1건(왕·날짜 음력 표기 그대로·요약·원문·출처·링크)', () => {
  const p = bundlePins(B())[0];
  const info = pinInfo(p);
  assert.equal(info.name, '창덕궁');
  assert.equal(info.count, 2);
  assert.equal(info.top.king, '○○왕 (예시)');
  assert.match(info.top.dateLabel, /음력/);
  assert.match(info.top.summary, /한글 요약/);
  assert.match(info.top.quote, /한문 원문/);
  assert.equal(info.top.tier, 'A');
  assert.equal(info.top.url, 'https://example.invalid/sillok/sample_a1');
  const empty = pinInfo(bundlePins(B())[1]);
  assert.equal(empty.top, null);
  assert.equal(empty.count, 0);
});

test('실록 카드 묶음은 언급이 있는 앵커만, 행사 상태는 tier C/미확인을 가른다', () => {
  const b = B();
  assert.deepEqual(mentionGroups(b).map((g) => g.name), ['창덕궁', '경복궁']);
  const ev = eventsView(b);
  assert.equal(ev.empty, false);
  assert.equal(ev.items[0].unverified, true);
  const none = eventsView({ ...b, events: null });
  assert.deepEqual([none.empty, none.unavailable], [true, true]);
  const noTier = eventsView({ ...b, events: { events: [{ title: 't', links: [], tier: null }], problems: [] } });
  assert.equal(noTier.items[0].unverified, true);
  const ok = eventsView({ ...b, events: { events: [{ title: 't', links: [], tier: 'A' }], problems: [] } });
  assert.equal(ok.items[0].unverified, false);
});

test('problems: 알려진 코드는 사전 키로(같은 키 한 번), 모르는 코드는 서버 문구 그대로', () => {
  const lines = problemLines({ problems: [
    { code: 'TIME_FORMAT', message: 'a' }, { code: 'TIME_NOT_IN_QUOTE', message: 'b' }, { code: 'ZZZ', message: '그대로' },
  ] });
  assert.deepEqual(lines.map((l) => l.key), ['bundle.problem.time', null]);
  assert.equal(lines[1].message, '그대로');
});

test('핀 좌표 변환: viewBox 안, 한 점은 가운데, 북쪽이 위', () => {
  const pins = bundlePins(B());
  const at = projectPins(pins);
  for (const [x, y] of at.values()) assert.ok(x >= 0 && x <= 600 && y >= 0 && y <= 700);
  assert.ok(at.get(pins[0].key)[1] < at.get(pins[1].key)[1], '창덕궁이 익선동보다 북쪽(위)');
  assert.deepEqual([...projectPins([pins[0]]).values()][0], [300, 350]);
  assert.equal(projectPins([]).size, 0);
});
