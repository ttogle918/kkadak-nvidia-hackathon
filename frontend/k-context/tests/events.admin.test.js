import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire, byClass, tick } from './_fakedom_ctsl.js';

installFakeDom();
const { createAdmin, mountAdmin } = await import('../src/events/admin.js');
const { EventsApiError } = await import('../src/events/api.js');

const REVIEW = {
  generated_at: '2026-10-07T12:00',
  new_or_changed: [{ id: 'ev:1', title: '○○ 공연', verification: 'verified', last_verified_at: '2026-10-07T12:00', links: ['https://a.invalid/x', 'javascript:alert(1)'], changes: [{ field: 'start_date', old: 'a', new: 'b', detected_at: '2026-10-07T13:00', importance: 'major' }] }],
  conflicts: [{ id: 'ev:2', title: '△△ 전시', verification: 'conflict', last_verified_at: null, links: [], conflicts: [{ field: 'start_date', values: [{ value: '2026-10-16', kind: 'official_api' }, { value: '2026-10-17', kind: 'official_api' }] }] }],
  missing_info: [{ id: 'ev:3', title: '□□ 행사', verification: 'needs_check', last_verified_at: null, links: [], missing: ['dates', 'venue'] }],
  eligibility_check: [{ id: 'ev:4', title: '▽▽ 강좌', verification: 'verified', last_verified_at: null, links: [], reasons: ['참여조건이 확인되지 않음 — 원문 확인 필요'] }],
  collection_errors: [{ source_id: 'seoul_openapi', name: '서울시 문화행사', error: 'RuntimeError: 서버 오류', consecutive_failures: 2, next_retry_at: '2026-10-07T12:10', last_success_at: '2026-10-06T12:00' }],
  stale_sources: [], reports_pending: [],
  manual_links: [{ source_id: 'caci', name: '중구문화재단', links: [{ name: '월별일정', url: 'https://www.caci.or.kr/x' }], notes: '메모', last_check: null, due: true }],
};
const SOURCES = { sources: [{ id: 'seoul_openapi', name: '서울시 문화행사', url: 'https://data.seoul.go.kr/', method: 'api', status: 'implemented', notes: 'n' }, { id: 'caci', name: '중구문화재단', url: 'https://www.caci.or.kr/', method: 'manual', status: 'manual_only', notes: 'n' }], runs: { seoul_openapi: { last_success_at: '2026-10-06T12:00' } }, link_checks: {} };
const REPORTS = { reports: [{ id: 'rpt_1', kind: 'new_event', status: 'pending', official_link: 'https://a.invalid/n', reason: '사유입니다 충분히', fields: { title: '○○' }, entry_id: null, submitted_at: '2026-10-07T11:00' }, { id: 'rpt_0', kind: 'other', status: 'accepted', official_link: 'https://a.invalid/o', reason: 'r', fields: {}, submitted_at: 'x', decided_by: 'human:demo', decided_at: '2026-10-07T11:30' }] };

function fakeApi(over = {}) {
  const calls = [];
  const rec = (n, v) => async (...a) => { calls.push([n, ...a]); return typeof v === 'function' ? v(...a) : v; };
  return { calls, demo: false, admin: { review: rec('review', REVIEW), sources: rec('sources', SOURCES), reports: rec('reports', REPORTS), decide: rec('decide', {}), refresh: rec('refresh', { run: { ok: true, fetched: 3 } }), linkCheck: rec('linkCheck', {}), ...over } };
}
const mem = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v), m }; };
function setup(api = fakeApi(), session = mem()) {
  const admin = createAdmin({ api, session });
  const root = new El('div', 'html');
  mountAdmin(root, { admin, api });
  return { admin, root, api, session };
}
const get = (x) => x.admin.store.getState();
const click = (root, act, id) => fire(root.find((e) => e.dataset?.act === act && (id == null || e.dataset.id === id))[0], 'click');

test('토큰 없이는 서버를 부르지 않는다', async () => {
  const x = setup();
  assert.equal(await x.admin.load(), false);
  assert.equal(x.api.calls.length, 0);
  assert.match(x.root.text, /관리자 토큰이 올바르지 않거나/);
});

test('토큰은 이 탭(sessionStorage)에만 저장하고 입력창에서 복원한다', () => {
  const x = setup();
  const input = x.root.find((e) => e.attrs?.id === 'ad-token')[0];
  input.value = ' secret-token ';
  fire(input, 'input');
  assert.equal(get(x).token, 'secret-token');
  assert.equal(JSON.parse(x.session.m.get('kc.admin.token')), 'secret-token');
  const again = setup(fakeApi(), x.session);
  assert.equal(get(again).token, 'secret-token');
  assert.equal(input.attrs.type, 'password');
});

test('불러오기: 검토 목록 여덟 영역이 보인다', async () => {
  const x = setup();
  x.admin.setToken('tok');
  await x.admin.load();
  const text = x.root.text;
  for (const s of ['신규·변경 행사', '정보 충돌', '누락된 정보', '참여조건 확인 필요', '수집 오류', '오래된 수집', '제보·수정 요청', '수동 확인이 필요한 공식 링크', '출처 현황']) assert.match(text, new RegExp(s), s);
  assert.match(text, /○○ 공연/);
  assert.match(text, /시작일: a → b \(major\)/);
  assert.match(text, /2026-10-16 \(official_api\) \/ 2026-10-17 \(official_api\)/);
  assert.match(text, /날짜, 장소/);
  assert.match(text, /연속 실패: 2/);
  assert.match(text, /RuntimeError: 서버 오류/);
  assert.ok(x.api.calls.every((c) => c[1] === 'tok')); // 토큰은 인자로만 전달
});

test('위험한 링크는 링크로 만들지 않는다', async () => {
  const x = setup();
  x.admin.setToken('tok');
  await x.admin.load();
  const anchors = x.root.find((e) => e.tag === 'a');
  assert.equal(anchors.filter((a) => (a.attrs.href ?? '').startsWith('javascript')).length, 0);
  assert.ok(anchors.some((a) => a.attrs.href === 'https://a.invalid/x' && a.attrs.rel === 'noopener noreferrer'));
});

test('제보 승인·반려: 신원은 보내지 않고 처리 후 다시 불러온다', async () => {
  const x = setup();
  x.admin.setToken('tok');
  await x.admin.load();
  click(x.root, 'approve', 'rpt_1');
  await tick(); await tick();
  const d = x.api.calls.find((c) => c[0] === 'decide');
  assert.deepEqual(d, ['decide', 'tok', 'rpt_1', 'approve', '']);
  assert.ok(x.api.calls.filter((c) => c[0] === 'review').length >= 2);
  click(x.root, 'reject', 'rpt_1');
  await tick(); await tick();
  assert.equal(x.api.calls.filter((c) => c[0] === 'decide')[1][3], 'reject');
  assert.match(x.root.text, /human:demo/); // 이미 처리된 제보는 처리자만 표시
  assert.equal(x.root.find((e) => e.dataset?.act === 'approve').length, 1); // 대기 건에만 버튼
});

test('수동 재수집·수동 확인 기록', async () => {
  const x = setup();
  x.admin.setToken('tok');
  await x.admin.load();
  click(x.root, 'refresh', 'seoul_openapi');
  await tick(); await tick();
  assert.deepEqual(x.api.calls.find((c) => c[0] === 'refresh'), ['refresh', 'tok', 'seoul_openapi', false]);
  assert.match(x.root.text, /수집 결과: seoul_openapi — ok \(3\)/);
  assert.equal(x.root.find((e) => e.dataset?.act === 'refresh').length, 1); // 자동 수집이 구현된 출처에만
  click(x.root, 'check', 'caci');
  await tick(); await tick();
  assert.deepEqual(x.api.calls.find((c) => c[0] === 'linkCheck'), ['linkCheck', 'tok', 'caci', '']);
});

test('재수집 실패 결과는 오류 문구로 보인다', async () => {
  const api = fakeApi({ refresh: async () => ({ run: { ok: false, error: 'SeoulApiError: 키 없음' } }) });
  const x = setup(api);
  x.admin.setToken('tok');
  await x.admin.load();
  click(x.root, 'refresh', 'seoul_openapi');
  await tick(); await tick();
  assert.match(x.root.text, /수집 결과: seoul_openapi — SeoulApiError: 키 없음/);
});

test('오류 구분: 403 은 토큰 안내, 네트워크는 연결 안내, 그 밖은 일반 오류', async () => {
  for (const [code, status, re] of [['forbidden', 403, /토큰이 올바르지 않거나/], ['network', 0, /서버에 연결하지 못했습니다/], ['internal_error', 500, /처리하지 못했습니다/]]) {
    const x = setup(fakeApi({ review: async () => { throw new EventsApiError(code, status, 'x'); } }));
    x.admin.setToken('tok');
    assert.equal(await x.admin.load(), false);
    assert.match(x.root.text, re);
    assert.equal(get(x).loading, false);
  }
});

test('영어 전환', async () => {
  const x = setup();
  x.admin.setToken('tok');
  await x.admin.load();
  click(x.root, 'lang', undefined);
  fire(x.root.find((e) => e.dataset?.act === 'lang' && e.dataset.value === 'en')[0], 'click');
  assert.match(x.root.text, /Admin — event review/);
  assert.match(x.root.text, /Collection errors/);
});
