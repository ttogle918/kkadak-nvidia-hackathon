import { test } from 'node:test';
import assert from 'node:assert/strict';
import { KO, EN, makeT } from '../src/events/i18n.js';
import * as L from '../src/events/logic.js';

const t = makeT('ko');
const te = makeT('en');

test('i18n: ko/en 키가 1:1 이고 빈 문자열 외에는 모두 채워져 있다', () => {
  assert.deepEqual(Object.keys(KO).sort(), Object.keys(EN).sort());
  for (const k of Object.keys(KO)) if (k !== 'lang.site.unknown') assert.ok(KO[k] && EN[k], k);
  assert.equal(t('nope.key'), 'nope.key');
  assert.equal(te('results.count', { n: 3 }), '3');
  assert.equal(t('results.count', { n: 3 }), '3건');
});

test('날짜: 서울 날짜·달력 검사·일수 더하기', () => {
  assert.equal(L.isDate('2026-10-07'), true);
  for (const bad of ['2026-13-01', '2026-02-30', '2026-1-7', '어제', null]) assert.equal(L.isDate(bad), false);
  assert.equal(L.seoulToday(new Date('2026-10-06T15:30:00Z')), '2026-10-07'); // UTC 로는 6일, 서울은 7일
  assert.equal(L.addDays('2026-10-31', 1), '2026-11-01');
  assert.equal(L.nowSeoulIso(new Date('2026-10-06T15:30:00Z')), '2026-10-07T00:30');
});

const form = (o = {}) => ({ from: '2026-10-15', to: '2026-10-18', originName: '', lat: '', lng: '', interests: '', maxExtra: '', duration: '', requireInterest: false, ...o });

test('폼 검증: 정상 요청과 오류', () => {
  const ok = L.validateForm(form({ interests: ' 공연, 전시,공연 ', originName: '○○ 호텔', lat: '37.56', lng: '126.98', duration: '90', maxExtra: '20' }));
  assert.equal(ok.ok, true);
  assert.deepEqual(ok.request.interests, ['공연', '전시']);
  assert.deepEqual(ok.request.origin, { name: '○○ 호텔', lat: 37.56, lng: 126.98 });
  assert.equal(ok.request.assumed_duration_min, 90);
  assert.equal(ok.request.max_extra_minutes, 20);
  assert.equal(L.validateForm(form()).request.max_extra_minutes, 30); // 기본값
  assert.equal('origin' in L.validateForm(form()).request, false);
  assert.equal(L.validateForm(form({ from: '2026-10-19' })).errors.dates, 'form.error.dates');
  assert.equal(L.validateForm(form({ from: '' })).ok, false);
  assert.ok(L.validateForm(form({ lat: '37' })).errors.origin); // 위도만
  assert.ok(L.validateForm(form({ lat: '95', lng: '10' })).errors.origin);
  assert.ok(L.validateForm(form({ maxExtra: '999' })).errors.max_extra);
  assert.ok(L.validateForm(form({ maxExtra: '1.5' })).errors.max_extra);
  assert.ok(L.validateForm(form({ duration: '0' })).errors.duration);
  assert.equal(L.validateForm(form({ interests: 'x,'.repeat(40) })).request.interests.length <= 20, true);
});

test('일정: 검증·생성·정렬·서버 전송 형태', () => {
  assert.equal(L.validatePlan({ date: '2026-10-16', start: '10:00', end: '12:00' }), true);
  assert.equal(L.validatePlan({ date: '2026-10-16', start: '12:00', end: '10:00' }), false);
  assert.equal(L.validatePlan({ date: '2026-10-16', start: '10:00', end: '25:00' }), false);
  assert.equal(L.validatePlan({ date: '2026-10-16', start: '10:00', end: '12:00', lat: '99' }), false);
  const p = L.newPlan({ title: ' 점심 ', date: '2026-10-16', start: '12:00', end: '13:00', lat: '37.5', lng: '127' });
  assert.equal(p.title, '점심');
  assert.equal(p.lat, 37.5);
  assert.notEqual(p.id, L.newPlan({ title: 'x', date: '2026-10-16', start: '12:00', end: '13:00' }).id);
  const a = { id: 'a', date: '2026-10-16', start: '14:00', end: '15:00' };
  const b = { id: 'b', date: '2026-10-15', start: '20:00', end: '21:00', lat: 1, lng: 2, source: 'catalog', entry_id: 'ev:1', end_assumed: true, junk: 1 };
  assert.deepEqual(L.sortPlans([a, b]).map((x) => x.id), ['b', 'a']);
  assert.deepEqual(L.planPayload([b])[0], { id: 'b', title: '', date: '2026-10-15', start: '20:00', end: '21:00', lat: 1, lng: 2, source: 'catalog', entry_id: 'ev:1', end_assumed: true });
});

const ev = (o = {}) => ({
  id: 'ev:1', title: '○○ 공연',
  schedule: { start_date: '2026-10-16', end_date: '2026-10-18', sessions: [{ date: '2026-10-16', start_time: '19:00', end_time: '20:30' }], weekly_closed_days: [0], closed_dates: ['2026-10-17'], holiday_rule: '' },
  price: { kind: 'unknown', text: '' }, reservation: { required: 'unknown', status: 'unknown', link: '', deadline: null, note: '' },
  participation: { status: 'unverified', reasons: [], foreigner: 'unknown' },
  language: { languages: [], english_guidance: 'unknown', english_subtitles: 'unknown', site_english_page: 'yes' },
  verification: 'needs_check', needs_check: ['price', 'language', 'bogus'], ...o,
});

test('표시: 모르는 값은 확인 필요, 확정 표현을 쓰지 않는다', () => {
  const e = ev();
  assert.equal(L.priceLabel(e, t).kind, '요금 확인 필요');
  assert.equal(L.reservationInfo(e, t).required, '예약 필요 여부 확인 필요');
  assert.equal(L.reservationInfo(e, t).tone, 'warn');
  assert.deepEqual(L.participationBadges(e, t).map((b) => b.tone), ['warn', 'warn']);
  assert.match(L.participationBadges(e, t)[0].text, /확인 필요/);
  assert.deepEqual(L.needsCheckLabels(e, t), ['요금', '진행 언어']); // 모르는 키는 버린다
  assert.equal(L.verificationBadge(e, t).tone, 'warn');
  assert.equal(L.verificationBadge(ev({ verification: 'verified' }), t).tone, 'ok');
  assert.equal(L.verificationBadge(ev({ verification: 'conflict' }), t).tone, 'bad');
});

test('표시: 영어 홈페이지가 있어도 행사 진행 언어는 확인 필요로 남는다', () => {
  const info = L.languageInfo(ev(), t);
  assert.equal(info.event, '진행 언어 확인 필요');
  assert.equal(info.guidance, '영어 안내 확인 필요');
  assert.match(info.site, /행사 진행 언어와 다름/);
  const ok = L.languageInfo(ev({ language: { languages: ['한국어', 'English'], english_guidance: 'yes', english_subtitles: 'no', site_english_page: 'unknown' } }), t);
  assert.equal(ok.event, '한국어, English');
  assert.equal(ok.site, '');
});

test('표시: 참여 제한·무료·예약 마감 톤', () => {
  const r = ev({ participation: { status: 'restricted', reasons: ['거주 조건: 중구민'], foreigner: 'excluded' } });
  assert.deepEqual(L.participationBadges(r, t).map((b) => b.tone), ['bad', 'bad']);
  assert.equal(L.priceLabel(ev({ price: { kind: 'free', text: '' } }), t).kind, '무료(출처 표기)');
  assert.equal(L.reservationInfo(ev({ reservation: { required: 'yes', status: 'closed', link: 'https://x.invalid', deadline: '2026-10-06', note: '' } }), t).tone, 'bad');
  assert.equal(L.reservationInfo(ev({ reservation: { required: 'no', status: 'not_required', link: '', deadline: null, note: '' } }), t).tone, 'ok');
});

test('표시: 날짜·휴무 문구', () => {
  const w = L.eventWhen(ev(), t);
  assert.equal(w.range, '2026-10-16 ~ 2026-10-18');
  assert.equal(w.sessions, '2026-10-16 19:00–20:30');
  assert.equal(L.eventWhen(ev({ schedule: { start_date: null, end_date: null, sessions: [] } }), t).range, '확인 필요');
  assert.equal(L.closuresText(ev(), t), '월 · 2026-10-17');
  assert.equal(L.closuresText(ev({ schedule: { weekly_closed_days: [], closed_dates: [], holiday_rule: '' } }), t), '');
});

const sug = (o = {}) => ({ extra_minutes: 7, extra_basis: 'formula', status: 'fit', after_item_id: 'a', route: { provider: 'table', estimated: false }, ...o });

test('제안 문구: 이동시간 확인 필요·추정 표시·경로 서비스 없음', () => {
  assert.equal(L.suggestionLabels(sug(), t).extra, '추가 이동시간 7분');
  const u = L.suggestionLabels(sug({ extra_minutes: null, route: { provider: 'none', estimated: false }, status: 'check_needed' }), t);
  assert.equal(u.extra, '이동시간 확인 필요');
  assert.equal(u.provider, '연결된 경로 서비스 없음');
  assert.equal(u.tone, 'warn');
  assert.equal(L.suggestionLabels(sug({ route: { provider: 'x', estimated: true } }), t).estimated, ' (추정값)');
  assert.equal(L.suggestionLabels(sug({ after_item_id: null }), t).after, '앞 일정 없음');
  assert.equal(L.suggestionLabels(sug({ status: 'no_fit' }), t).tone, 'bad');
});

test('저장한 행사: 변경 배지는 확인한 시각 이후만', () => {
  let saved = L.saveEvent({}, { id: 'ev:1', title: '○○ 공연' }, '2026-10-07T12:00');
  saved = L.saveEvent(saved, { id: 'ev:2', title: '△△ 전시' }, '2026-10-07T12:00');
  const server = [{ entry_id: 'ev:1', has_major: true, changes: [
    { field: 'start_date', old: '2026-10-16', new: '2026-10-17', detected_at: '2026-10-07T13:00', importance: 'major' },
    { field: 'title', old: 'a', new: 'b', detected_at: '2026-10-07T11:00', importance: 'minor' }] }];
  const applied = L.applyChanges(saved, server);
  assert.equal(applied['ev:1'].changes.length, 1);
  assert.equal(applied['ev:1'].hasMajor, true);
  assert.deepEqual(applied['ev:2'].changes, []);
  assert.equal(L.describeChange(applied['ev:1'].changes[0], t), '시작일: 2026-10-16 → 2026-10-17');
  assert.equal(L.describeChange({ field: 'sessions', old: [], new: [['2026-10-17', '19:00']], detected_at: 'x' }, t).startsWith('회차: 없음 →'), true);
  const acked = L.ackChanges(applied, 'ev:1', '2026-10-07T14:00');
  assert.deepEqual(acked['ev:1'].changes, []);
  assert.equal(acked['ev:1'].seenAt, '2026-10-07T14:00');
  assert.equal(L.oldestSeen(acked), '2026-10-07T12:00');
  assert.deepEqual(Object.keys(L.unsaveEvent(acked, 'ev:1')), ['ev:2']);
  assert.equal(L.oldestSeen({}), null);
  assert.equal(L.ackChanges(saved, 'none', 'x'), saved);
});

test('지도: 좌표 투영(범위 안·한 점·같은 점·위도 보정)', () => {
  const pts = [{ id: 'a', lat: 37.56, lng: 126.98 }, { id: 'b', lat: 37.58, lng: 127.0 }, { id: 'c', lat: null, lng: null }];
  const p = L.projectPoints(pts, { width: 360, height: 240, pad: 28 });
  assert.equal(p.length, 2);
  for (const q of p) { assert.ok(q.x >= 28 - 1e-6 && q.x <= 332 + 1e-6); assert.ok(q.y >= 28 - 1e-6 && q.y <= 212 + 1e-6); }
  assert.ok(p[1].y < p[0].y); // 북쪽(위도 큼)이 위
  assert.ok(p[1].x > p[0].x);
  const one = L.projectPoints([pts[0]]);
  assert.deepEqual([one[0].x, one[0].y], [180, 120]);
  const same = L.projectPoints([pts[0], { ...pts[0], id: 'z' }]);
  assert.deepEqual([same[0].x, same[0].y], [180, 120]);
  assert.deepEqual(L.projectPoints([]), []);
  // 같은 위도·경도 차이가 위도 보정(cos)으로 가로가 더 짧아진다
  const sq = L.projectPoints([{ id: 'a', lat: 37.5, lng: 127.0 }, { id: 'b', lat: 37.51, lng: 127.01 }], { width: 400, height: 400, pad: 0 });
  assert.ok(Math.abs(sq[1].x - sq[0].x) < Math.abs(sq[0].y - sq[1].y));
});

test('지도 점 모음: 출발·행사·일정(좌표 있는 것만)', () => {
  const res = { map: { points: [{ id: 'ev:1', title: '○○', lat: 1, lng: 2 }] } };
  const pts = L.mapPoints(res, [{ id: 'p1', title: '점심', lat: 3, lng: 4 }, { id: 'p2', title: '좌표 없음' }], { lat: '37.5', lng: '127', originName: '호텔' });
  assert.deepEqual(pts.map((p) => p.kind), ['origin', 'event', 'plan']);
  assert.deepEqual(L.mapPoints(null, [], { lat: '', lng: '' }), []);
});

test('저장소: 예외가 나도 화면은 계속 된다', () => {
  const bad = { getItem() { throw new Error('x'); }, setItem() { throw new Error('x'); } };
  assert.deepEqual(L.loadJson(bad, 'k', { a: 1 }), { a: 1 });
  assert.equal(L.saveJson(bad, 'k', 1), false);
  assert.deepEqual(L.loadJson(null, 'k', []), []);
  const mem = new Map();
  const ok = { getItem: (k) => mem.get(k) ?? null, setItem: (k, v) => mem.set(k, v) };
  assert.equal(L.saveJson(ok, 'k', { z: 1 }), true);
  assert.deepEqual(L.loadJson(ok, 'k', null), { z: 1 });
  mem.set('bad', '{not json');
  assert.deepEqual(L.loadJson(ok, 'bad', 7), 7);
});
