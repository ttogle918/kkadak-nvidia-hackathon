import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire, byClass, tick } from './_fakedom_ctsl.js';

installFakeDom();
const { createStore } = await import('../src/lib/store.js');
const { createController, initialState } = await import('../src/events/controller.js');
const { createMockEventsApi, EventsApiError } = await import('../src/events/api.js');
const { mountEvents } = await import('../src/events/view.js');

const mem = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) }; };
function setup({ api = createMockEventsApi(), lang } = {}) {
  const storage = mem();
  const store = createStore(initialState(storage, { today: '2026-10-16' }));
  if (lang) store.setState({ lang });
  const controller = createController({ store, api, storage, now: () => new Date('2026-10-07T03:00:00Z') });
  const root = new El('div', 'html');
  const view = mountEvents(root, { store, api, controller });
  return { store, controller, root, view, api };
}
const byId = (root, id) => root.find((e) => e.attrs?.id === id)[0];
const acts = (root, act) => root.find((e) => e.dataset?.act === act);
const clickAct = (root, act, id) => { const el = acts(root, act).find((e) => id == null || e.dataset.id === id); fire(el, 'click'); return el; };
const cards = (root) => byClass(root, 'ev-card');
const type = (root, id, value) => { const el = byId(root, id); el.value = value; fire(el, 'input'); };
async function search(x, from = '2026-10-16', to = '2026-10-19') {
  type(x.root, 'f-from', from); type(x.root, 'f-to', to);
  fire(byClass(x.root, 'ev-form')[0], 'submit');
  await tick(); await tick();
}

test('데모 모드: 데모 배너가 보이고 서버 모드에서는 보이지 않는다', () => {
  const demo = setup();
  assert.match(byClass(demo.root, 'ev-demo')[0].text, /데모 데이터/);
  assert.equal(byClass(demo.root, 'ev-demo')[0].hidden, false);
  const real = setup({ api: { ...createMockEventsApi(), demo: false } });
  assert.equal(byClass(real.root, 'ev-demo')[0].text, '');
  assert.equal(byClass(real.root, 'ev-demo')[0].hidden, true);
});

test('폼 기본값: 서울 오늘부터 3일, 결과 영역은 비어 있다', () => {
  const x = setup();
  assert.equal(byId(x.root, 'f-from').value, '2026-10-16');
  assert.equal(byId(x.root, 'f-to').value, '2026-10-19');
  assert.equal(cards(x.root).length, 0);
  assert.match(x.root.text, /수집 범위/);
  assert.match(x.root.text, /지역의 모든 행사가 아닙니다/);
});

test('검색: 카드마다 참여조건·검증·마지막 검증 시각이 보이고, 확정 표현을 쓰지 않는다', async () => {
  const x = setup();
  await search(x);
  assert.equal(cards(x.root).length, 3);
  const text = x.root.text;
  assert.match(text, /\(데모\) 저녁 공연/);
  assert.match(text, /출처가 "누구나"라고 적음/); // 출처가 적은 것만 가능으로 표시
  assert.match(text, /참여 제한/); // 거주민 전용
  assert.match(text, /거주 조건: 중구민/);
  assert.match(text, /참여조건 확인 필요/);
  assert.match(text, /외국인 참여 조건 확인 필요/);
  assert.match(text, /마지막 검증: 2026-10-07T12:00/);
  assert.doesNotMatch(text, /참여 가능합니다|모든 행사입니다/);
  assert.match(text, /요금 확인 필요/);
});

test('검색: 잘못된 날짜는 요청 없이 오류 문구', async () => {
  const x = setup();
  await search(x, '2026-10-20', '2026-10-16');
  assert.equal(cards(x.root).length, 0);
  assert.match(byClass(x.root, 'ev-form')[0].text, /여행 시작일과 종료일을 올바르게/);
});

test('검색: 서버 연결 실패 안내와 빈 결과', async () => {
  const bad = { ...createMockEventsApi(), async search() { throw new EventsApiError('network', 0, 'n'); } };
  const x = setup({ api: bad });
  await search(x);
  assert.match(x.root.text, /서버에 연결하지 못했습니다/);
  const y = setup();
  await search(y, '2027-01-01', '2027-01-02');
  assert.match(y.root.text, /조건에 맞는 행사가 없습니다/);
});

test('상세: 날짜·장소·요금·예약·참여조건·언어·출처·마지막 검증을 보여 준다', async () => {
  const x = setup();
  await search(x);
  clickAct(x.root, 'detail', 'demo:1');
  await tick();
  const detail = byClass(x.root, 'ev-detail')[0].text;
  for (const label of ['날짜·시간', '장소', '요금', '예약', '참여조건', '언어', '출처', '마지막 검증']) assert.match(detail, new RegExp(label), label);
  assert.match(detail, /2026-10-16 19:00–20:30/);
  assert.match(detail, /예약 필요/);
  assert.match(detail, /신청 마감: 2026-10-15/);
  assert.match(detail, /데모 출처\(합성\)/);
  assert.match(detail, /진행 언어 확인 필요/);
  assert.match(detail, /확인이 필요한 항목/);
  assert.ok(byClass(x.root, 'ev-card').some((c) => c.cls.includes('is-selected')));
  clickAct(x.root, 'close');
  assert.doesNotMatch(byClass(x.root, 'ev-detail')[0].text, /신청 마감/);
});

test('상세: 영어 홈페이지가 있어도 행사 진행 언어는 확인 필요로 남는다', async () => {
  const x = setup();
  await search(x);
  clickAct(x.root, 'detail', 'demo:3');
  await tick();
  const d = byClass(x.root, 'ev-detail')[0].text;
  assert.match(d, /홈페이지에 영어 페이지가 있음\(행사 진행 언어와 다름\)/);
  assert.match(d, /진행 언어 확인 필요/);
  assert.match(d, /영어 안내 확인 필요/);
  assert.match(d, /휴무: 월/);
  assert.match(d, /회차·시간 확인 필요/);
});

test('언어 전환: 영어 화면', async () => {
  const x = setup();
  await search(x);
  clickAct(x.root, 'lang', undefined);
  fire(x.root.find((e) => e.dataset?.act === 'lang' && e.dataset.value === 'en')[0], 'click');
  assert.match(x.root.text, /Find events in Jung-gu/);
  assert.match(x.root.text, /Only events confirmed from the sources we collect/);
  assert.match(x.root.text, /Eligibility needs checking/);
});

test('지도: 좌표 있는 행사는 점, 없는 행사는 안내 문구', async () => {
  const x = setup();
  await search(x);
  const pts = byClass(x.root, 'ev-pt');
  assert.equal(pts.filter((p) => p.cls.includes('is-event')).length, 2);
  assert.match(byClass(x.root, 'ev-map')[0].text, /좌표 없는 행사 1건은 지도에 표시되지 않습니다/);
  fire(pts.find((p) => p.cls.includes('is-event')), 'click');
  await tick();
  assert.ok(get(x).selectedId);
});
const get = (x) => x.store.getState();

test('일정: 기존 일정 입력 → 행사 제안 → 추가 → 취소(행사 항목만)', async () => {
  const x = setup();
  type(x.root, 'p-title', '점심'); type(x.root, 'p-date', '2026-10-16'); type(x.root, 'p-start', '12:00'); type(x.root, 'p-end', '13:00');
  fire(byClass(x.root, 'ev-planform')[0], 'submit');
  assert.equal(get(x).itinerary.length, 1);
  assert.match(byClass(x.root, 'ev-plan')[0].text, /점심/);
  assert.equal(byId(x.root, 'p-title').value, ''); // 입력 후 비움
  await search(x);
  clickAct(x.root, 'detail', 'demo:1');
  await tick();
  assert.match(byClass(x.root, 'ev-detail')[0].text, /일정에 넣을 수 있는 회차/);
  assert.match(byClass(x.root, 'ev-detail')[0].text, /이동시간 확인 필요/); // 경로 서비스 없음 → 계산하지 않는다
  assert.match(byClass(x.root, 'ev-detail')[0].text, /연결된 경로 서비스 없음/);
  clickAct(x.root, 'add-session');
  await tick(); await tick();
  assert.equal(get(x).itinerary.filter((p) => p.source === 'catalog').length, 1);
  assert.match(byClass(x.root, 'ev-plan')[0].text, /\[행사\]/);
  assert.ok(acts(x.root, 'plan-rm').length === 1);
  clickAct(x.root, 'plan-rm');
  await tick(); await tick();
  assert.equal(get(x).itinerary.filter((p) => p.source === 'catalog').length, 0);
  assert.equal(get(x).itinerary.length, 1);
});

test('일정 입력 오류는 안내만 하고 일정을 만들지 않는다', () => {
  const x = setup();
  type(x.root, 'p-date', '2026-10-16'); type(x.root, 'p-start', '14:00'); type(x.root, 'p-end', '13:00');
  fire(byClass(x.root, 'ev-planform')[0], 'submit');
  assert.equal(get(x).itinerary.length, 0);
  assert.match(byClass(x.root, 'ev-plan')[0].text, /날짜·시작·종료\(시작 < 종료\)를 확인하세요/);
});

test('저장한 행사와 변경 배지', async () => {
  const x = setup();
  await search(x);
  clickAct(x.root, 'save', 'demo:1');
  assert.match(byClass(x.root, 'ev-saved')[0].text, /\(데모\) 저녁 공연/);
  x.api.savedChanges = async () => ({ saved: [{ entry_id: 'demo:1', has_major: true, changes: [{ field: 'start_date', old: '2026-10-16', new: '2026-10-17', detected_at: '2999-01-01T00:00', importance: 'major' }] }] });
  clickAct(x.root, 'check-saved');
  await tick(); await tick();
  const saved = byClass(x.root, 'ev-saved')[0].text;
  assert.match(saved, /변경됨/);
  assert.match(saved, /시작일: 2026-10-16 → 2026-10-17/);
  clickAct(x.root, 'ack', 'demo:1');
  assert.doesNotMatch(byClass(x.root, 'ev-saved')[0].text, /변경됨/);
  clickAct(x.root, 'save', 'demo:1'); // 저장 취소
  assert.match(byClass(x.root, 'ev-saved')[0].text, /저장한 행사가 없습니다/);
});

test('제보: 접수 문구, 즉시 공개되지 않는다는 안내', async () => {
  const x = setup();
  assert.match(byClass(x.root, 'ev-report')[0].text, /검토 후에만 공개 데이터에 반영/);
  type(x.root, 'r-official_link', 'https://example.invalid/n/1'); type(x.root, 'r-reason', '공식 공지로 확인한 행사입니다');
  type(x.root, 'r-title', '○○ 행사');
  fire(byClass(x.root, 'ev-reportform')[0], 'submit');
  await tick();
  assert.match(byClass(x.root, 'ev-report')[0].text, /접수했습니다\. 검토 대기 중입니다/);
  const y = setup();
  fire(byClass(y.root, 'ev-reportform')[0], 'submit');
  await tick();
  assert.match(byClass(y.root, 'ev-report')[0].text, /공식 링크\(필수\)/);
});

test('XSS: 서버 문자열은 텍스트로만, javascript: 링크는 링크로 만들지 않는다', async () => {
  const api = createMockEventsApi();
  const orig = api.search;
  api.search = async (b) => {
    const r = await orig(b);
    r.events[0].title = '<img src=x onerror=alert(1)>';
    return r;
  };
  api.detail = async (id) => {
    const d = await createMockEventsApi().detail(id);
    d.links = [{ url: 'javascript:alert(1)', source_name: '<b>x</b>', kind: 'official_api', quote: '<script>x</script>', ai_extracted: true, location: '첨부 1쪽' }, { url: 'https://ok.invalid/x', source_name: 'ok', kind: 'official_api', quote: 'q' }];
    return d;
  };
  const x = setup({ api });
  await search(x);
  assert.ok(x.root.text.includes('<img src=x onerror=alert(1)>'));
  assert.equal(x.root.find((e) => e.tag === 'img').length, 0);
  clickAct(x.root, 'detail', 'demo:1');
  await tick();
  const anchors = x.root.find((e) => e.tag === 'a');
  assert.deepEqual(anchors.filter((a) => (a.attrs.href ?? '').startsWith('javascript')).length, 0);
  assert.ok(anchors.some((a) => a.attrs.href === 'https://ok.invalid/x' && a.attrs.rel === 'noopener noreferrer' && a.attrs.target === '_blank'));
  const d = byClass(x.root, 'ev-detail')[0].text;
  assert.match(d, /AI 추출값\(검토 대상\)/);
  assert.match(d, /첨부 1쪽/);
  assert.equal(x.root.find((e) => e.tag === 'script').length, 0);
});

test('unmount 는 던지지 않는다', () => {
  const x = setup();
  assert.doesNotThrow(() => x.view.destroy());
});
