// kc-chat-bundle/v2 수용(T314): 검증기(v1·v2·틀린 v2 필드·접두어), 이동 구간 목록 문구, 근거 표시, schedule 출처 줄, 점선.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, byClass } from './_fakedom_ctsl.js';

installFakeDom();
let innerHtmlWrites = 0;
Object.defineProperty(El.prototype, 'innerHTML', { set() { innerHtmlWrites += 1; }, get() { return ''; } });
const baseReplace = El.prototype.replaceChildren;
El.prototype.replaceChildren = function replaceChildren(...nodes) { return baseReplace.call(this, ...nodes.map((n) => (typeof n === 'string' ? { nodeType: 3, text: n } : n))); };

const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');
const { validateChatBundle, MAX } = await import('../src/api/bundle.js');
const { CHAT_BUNDLE_SAMPLE } = await import('../src/data/chat-bundle.js');
const { buildLegList, legTimeText } = await import('../src/components/map/route-list.js');
const { buildBundleSvg } = await import('../src/components/map/chat-layer.js');
const { pinLinks, rationaleFor } = await import('../src/lib/chat-bundle.js');
const { bundleTimelineNode } = await import('../src/components/timeline/bundle-view.js');
const { bundleCardNodes } = await import('../src/components/cards/bundle-view.js');
const ko = createT(() => 'ko');
const en = createT(() => 'en');
const EVIL = '<img src=x onerror=alert(1)>';

const L = (k, e = k) => ({ ko: k, en: e });
const rat = (key) => ({ card_id: key, chips: [{ key: 'why', tone: 'old', label: L('◆ 근거 있음', '◆ Grounded') }], items: { why: { title: L('왜'), text: L('본문', 'body'), rows: [{ k: L('k'), v: L('v') }] } } });
const leg = (over = {}) => ({ from: '창덕궁', to: '북촌', from_ll: [37.58, 126.99], to_ll: [37.58, 126.98], straight_m: 850, walk_min: 14, provider: 'kakao', estimated: false, ...over });
function v2(edit) {
  const raw = structuredClone(CHAT_BUNDLE_SAMPLE);
  raw.schema = 'kc-chat-bundle/v2';
  raw.schedule = { source: 'llm', attempts: 1, model: 'm', prompt_sha: 'x', cache_created_at: null };
  raw.routes = [{ id: 'day1', day: 1, date: '2026-10-10', legs: [leg()], skipped: [] }];
  raw.rationale = { 'mention:story_a': rat('mention:story_a') };
  raw.events_rationale = { 'event:e1': rat('event:e1') };
  raw.story_routes_note = L('이야기 길 없음 — 근거 좌표가 있는 이야기가 없어요', 'No story route — no stories with grounded coordinates');
  edit?.(raw);
  return raw;
}
const ok = (raw) => { const r = validateChatBundle(raw); assert.equal(r.ok, true, r.reason); return r.bundle; };
const flat = (n) => n.text;

test('v1 묶음: 그대로 통과, v2 필드는 비어 있고 v2 필드가 와도 무시한다', () => {
  const b = ok(structuredClone(CHAT_BUNDLE_SAMPLE));
  assert.equal(b.schema, 'kc-chat-bundle/v1');
  assert.deepEqual([b.routes, b.rationale, b.events_rationale, b.story_routes_note, b.schedule], [[], {}, {}, null, null]);
  const raw = v2(); raw.schema = 'kc-chat-bundle/v1';
  const b1 = ok(raw);
  assert.deepEqual([b1.routes, b1.rationale, b1.story_routes_note], [[], {}, null]);
  assert.equal(b1.schedule.source, 'llm'); // schedule 은 v1 가산 필드로도 온다
});

test('v1 화면: 이동 구간은 "정보 없음", 점선 없음, 근거는 못 찾음', () => {
  const b = ok(structuredClone(CHAT_BUNDLE_SAMPLE));
  const list = buildLegList(b, ko, 'ko');
  assert.match(flat(list), /이동 구간 정보 없음/);
  assert.equal(list.find((e) => e.dataset?.note === 'story-routes').length, 0);
  assert.equal(pinLinks(b).length, 0);
  assert.equal(buildBundleSvg(b, ko, null).find((e) => (e.attrs?.class ?? '').includes('map-straight')).length, 0);
  assert.equal(rationaleFor(b, 'story_a'), null);
});

test('정상 v2: 모든 v2 필드가 정리된 복사본으로 들어온다', () => {
  const b = ok(v2());
  assert.equal(b.schema, 'kc-chat-bundle/v2');
  assert.equal(b.routes[0].legs[0].straight_m, 850);
  assert.deepEqual(b.routes[0].legs[0].from_ll, [37.58, 126.99]);
  assert.deepEqual(Object.keys(b.rationale), ['mention:story_a']);
  assert.deepEqual(Object.keys(b.events_rationale), ['event:e1']);
  assert.equal(b.rationale['mention:story_a'].chips[0].label.en, '◆ Grounded');
  assert.equal(b.story_routes_note.ko.startsWith('이야기 길 없음'), true);
  assert.equal(rationaleFor(b, 'story_a').card_id, 'mention:story_a');
  assert.equal(rationaleFor(b, 'e1').card_id, 'event:e1');
  assert.equal(rationaleFor(b, 'zzz'), null);
});

test('틀린 v2 필드는 그 필드만 비운다(v1 필드·다른 v2 필드는 그대로)', () => {
  const cases = [
    ['routes', (r) => { r.routes[0].legs[0].straight_m = 'far'; }, (b) => assert.deepEqual(b.routes, [])],
    ['routes 배열 아님', (r) => { r.routes = 'x'; }, (b) => assert.deepEqual(b.routes, [])],
    ['leg 좌표 범위', (r) => { r.routes[0].legs[0].from_ll = [999, 0]; }, (b) => assert.deepEqual(b.routes, [])],
    ['rationale 값 모양', (r) => { r.rationale['mention:story_a'].chips[0].tone = 'blue'; }, (b) => assert.deepEqual(b.rationale, {})],
    ['rationale 맵 아님', (r) => { r.rationale = [1]; }, (b) => assert.deepEqual(b.rationale, {})],
    ['events_rationale', (r) => { r.events_rationale = 5; }, (b) => assert.deepEqual(b.events_rationale, {})],
    ['schedule.source', (r) => { r.schedule.source = 'magic'; }, (b) => assert.equal(b.schedule, null)],
    ['story_routes_note', (r) => { r.story_routes_note = 7; }, (b) => assert.equal(b.story_routes_note, null)],
  ];
  for (const [name, edit, check] of cases) {
    const b = ok(v2(edit));
    check(b);
    assert.equal(b.itinerary.anchors.length, CHAT_BUNDLE_SAMPLE.itinerary.anchors.length, name);
    if (!name.startsWith('routes') && !name.startsWith('leg')) assert.equal(b.routes.length, 1, name);
    if (!name.startsWith('rationale')) assert.deepEqual(Object.keys(b.rationale), ['mention:story_a'], name);
  }
});

test('v1 필드가 틀리면 ok:false (v2 여부와 무관)', () => {
  const raw = v2(); raw.itinerary = { anchors: 'x' };
  assert.equal(validateChatBundle(raw).ok, false);
  const raw2 = v2(); raw2.schema = 'kc-chat-bundle/v3';
  assert.equal(validateChatBundle(raw2).ok, false);
});

test('근거 맵은 접두어가 맞는 키만 남긴다(교차 접두어·접두어 없음·__proto__ 는 버림)', () => {
  const raw = v2((r) => {
    r.rationale['event:e9'] = rat('event:e9'); // rationale 맵에 event: → 버림
    r.rationale.story_b = rat('story_b'); // 접두어 없음 → 버림
    r.rationale['mention:'] = rat('mention:');
    r.events_rationale['mention:story_z'] = rat('mention:story_z');
    r.events_rationale.bare = rat('bare');
    Object.defineProperty(r.rationale, '__proto__', { value: rat('x'), enumerable: true });
  });
  const b = ok(raw);
  assert.deepEqual(Object.keys(b.rationale), ['mention:story_a']);
  assert.deepEqual(Object.keys(b.events_rationale), ['event:e1']);
  assert.equal(Object.getPrototypeOf(b.rationale), Object.prototype);
});

test('상한: routes 7 · legs 20 · 근거 100 · chips 8 · rows 12', () => {
  const b = ok(v2((r) => {
    r.routes = Array.from({ length: 10 }, (_, i) => ({ id: `d${i}`, day: i + 1, date: null, legs: Array.from({ length: 30 }, () => leg()), skipped: [] }));
    r.rationale = {};
    for (let i = 0; i < 130; i += 1) r.rationale[`mention:s${i}`] = rat(`mention:s${i}`);
    r.rationale['mention:s0'].chips = Array.from({ length: 12 }, (_, i) => ({ key: `c${i}`, tone: 'now', label: L('x') }));
    r.rationale['mention:s0'].items.why.rows = Array.from({ length: 20 }, () => ({ k: L('k'), v: L('v') }));
  }));
  assert.equal(b.routes.length, MAX.routes);
  assert.equal(b.routes[0].legs.length, MAX.legs);
  assert.equal(Object.keys(b.rationale).length, MAX.rationale);
  assert.equal(b.rationale['mention:s0'].chips.length, MAX.chips);
  assert.equal(b.rationale['mention:s0'].items.why.rows.length, MAX.rows);
});

test('이동 구간 문구: walk_min 없음 -> 이동시간 확인 필요, estimated -> 예상, 확정 도보는 예상 없음', () => {
  assert.equal(legTimeText(leg({ walk_min: null }), ko), '이동시간 확인 필요');
  assert.equal(legTimeText(leg({ walk_min: 14, estimated: true }), ko), '도보 14분 (예상)');
  assert.equal(legTimeText(leg({ walk_min: 14, estimated: true }), en), 'Walk 14 min (estimated)');
  assert.equal(legTimeText(leg({ walk_min: 14 }), ko), '도보 14분');
  const b = ok(v2((r) => {
    r.routes[0].legs = [leg(), leg({ from: 'B', to: 'C', walk_min: null, estimated: true }), leg({ from: 'C', to: 'D', walk_min: 9, estimated: true })];
    r.routes[0].skipped = [{ from: 'D', to: 'E', reason: '좌표 없음' }, { from: 'E', to: 'F', reason: '시각 없음' }];
  }));
  const list = buildLegList(b, ko, 'ko');
  const t = flat(list);
  assert.match(t, /DAY 1 · 2026-10-10/);
  assert.match(t, /창덕궁 → 북촌 · 직선거리 850m · 도보 14분/);
  assert.match(t, /B → C · 직선거리 850m · 이동시간 확인 필요/);
  assert.match(t, /C → D · 직선거리 850m · 도보 9분 \(예상\)/);
  assert.match(t, /D → E · 건너뜀 · 좌표 없음/);
  assert.match(t, /E → F · 건너뜀 · 시각 없음/);
  assert.equal(list.find((e) => e.dataset?.skipped === 'true').length, 2);
});

test('story_routes_note: 이야기 길 없음을 밝힌다(언어별), 서버 문자열은 텍스트 노드로만', () => {
  const b = ok(v2((r) => { r.routes[0].legs[0].from = EVIL; }));
  assert.match(flat(buildLegList(b, ko, 'ko')), /이야기 길 없음 — 근거 좌표가 있는 이야기가 없어요/);
  assert.match(flat(buildLegList(b, en, 'en')), /No story route/);
  const list = buildLegList(b, ko, 'ko');
  assert.equal(list.find((e) => e.tag === 'img').length, 0);
  assert.match(flat(list), /<img src=x/);
  assert.equal(innerHtmlWrites, 0);
});

test('v2 에 routes 가 비어도 "정보 없음" + 이야기 길 문구', () => {
  const b = ok(v2((r) => { r.routes = []; }));
  const t = flat(buildLegList(b, ko, 'ko'));
  assert.match(t, /이동 구간 정보 없음/);
  assert.match(t, /이야기 길 없음/);
});

test('지도 점선: v2 routes 가 있을 때만, 같은 날 이웃 핀 사이 + "직선 연결(실제 길 아님)" 글자 라벨', () => {
  const b = ok(v2((r) => { r.routes[0].legs = [leg({ from_ll: [37.57964694739535, 126.99099980677127], to_ll: [37.5734371942191, 126.989775723896] })]; }));
  const links = pinLinks(b);
  assert.ok(links.length >= 1);
  assert.ok(links.every((l) => Number.isInteger(l.day)));
  const svg = buildBundleSvg(b, ko, null);
  const lines = svg.find((e) => (e.attrs?.class ?? '').includes('map-straight') && e.tag === 'path');
  assert.equal(lines.length, links.length);
  assert.ok(lines.every((p) => p.attrs['stroke-dasharray']));
  assert.match(flat(svg), /직선 연결\(실제 길 아님\)/);
});

test('schedule 출처 줄(타임라인만): cache -> 이전 결과 재사용(시각), rules -> 규칙으로 정리, llm 이면 없음, 카드에는 없음', () => {
  const mk = (sch) => ok(v2((r) => { r.schedule = sch; }));
  const cache = mk({ source: 'cache', attempts: 0, model: null, prompt_sha: 'x', cache_created_at: '2026-10-09T01:02:03Z' });
  assert.match(flat(bundleTimelineNode(cache, 1, ko)), /이전 결과 재사용 \(2026-10-09T01:02:03Z\)/);
  assert.doesNotMatch(bundleCardNodes(cache, ko).filter(Boolean).map(flat).join(' '), /재사용|규칙으로/); // 카드에는 두지 않는다(중복 방지)
  const rules = mk({ source: 'rules', attempts: 0, model: null, prompt_sha: 'x', cache_created_at: null });
  assert.match(flat(bundleTimelineNode(rules, 1, ko)), /규칙으로 정리\(장소 사전 이름만\)/);
  assert.doesNotMatch(bundleCardNodes(rules, ko).filter(Boolean).map(flat).join(' '), /규칙으로/);
  assert.match(flat(bundleTimelineNode(rules, 1, en)), /Organized by rules/);
  const llm = mk({ source: 'llm', attempts: 1, model: 'm', prompt_sha: 'x', cache_created_at: null });
  assert.doesNotMatch(flat(bundleTimelineNode(llm, 1, ko)), /재사용|규칙으로/);
  assert.doesNotMatch(bundleCardNodes(llm, ko).filter(Boolean).map(flat).join(' '), /재사용|규칙으로/);
  const none = ok(structuredClone(CHAT_BUNDLE_SAMPLE));
  assert.doesNotMatch(flat(bundleTimelineNode(none, 1, ko)), /재사용/);
});

// --- 근거 mount ---
const rationale = await import('../src/components/rationale/index.js');
async function mountRationale(bundle, over) {
  const store = createStore(createInitialState({ chatBundle: bundle, mode: 'now', ...over }));
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api });
  await actions.loadAll();
  store.setState(over);
  const t = createT(() => store.getState().lang);
  const root = new El('section', 'html');
  rationale.mount(root, { store, api, t, actions });
  await new Promise((r) => setTimeout(r, 5));
  return { root, store };
}

test('근거 표시: v1 은 숨김, v2 는 선택 항목(언급 mention:/행사 event:)의 근거, 없으면 "근거 없음"', async () => {
  const v1 = await mountRationale(ok(structuredClone(CHAT_BUNDLE_SAMPLE)), { selectedNow: 'story_a' });
  assert.equal(v1.root.find((e) => e.dataset?.status === 'hidden').length, 1);
  assert.match(flat(v1.root), /MOCK 예시는 숨김/);

  const b = ok(v2());
  const m = await mountRationale(b, { selectedNow: 'story_a' });
  assert.equal(m.root.find((e) => e.dataset?.act === 'chip').length, 1);
  assert.match(flat(m.root), /◆ 근거 있음/);

  const e = await mountRationale(b, { selectedNow: 'e1' });
  assert.match(flat(e.root), /◆ 근거 있음/);

  const none = await mountRationale(b, { selectedNow: 'unknown_card' });
  assert.equal(none.root.find((x) => x.dataset?.act === 'chip').length, 0);
  assert.match(flat(none.root), /이 카드의 판단 근거 없음/);
});

const CHANGDEOK = [37.57964694739535, 126.99099980677127];
const IKSEON = [37.5734371942191, 126.989775723896];
const GYEONGBOK = [37.577613288258206, 126.97689786832184];

test('B1: skipped.to 가 빈 문자열("시각 없음")이어도 routes 전체가 살아 있고 문구는 from 만 + 사유', () => {
  const b = ok(v2((r) => {
    r.routes = [
      { id: 'day1', day: 1, date: '2026-10-15', legs: [leg()], skipped: [{ from: '익선동', to: '', reason: '시각 없음' }] },
      { id: 'day2', day: 2, date: '2026-10-16', legs: [leg({ from: 'B', to: 'C' })], skipped: [] },
    ];
  }));
  assert.equal(b.routes.length, 2);
  assert.equal(b.routes[0].legs.length, 1);
  assert.equal(b.routes[0].skipped[0].to, '');
  assert.equal(b.routes[1].date, '2026-10-16');
  const t = flat(buildLegList(b, ko, 'ko'));
  assert.match(t, /익선동 · 건너뜀 · 시각 없음/);
  assert.doesNotMatch(t, /익선동 → /);
  assert.match(t, /DAY 2 · 2026-10-16/);
  // 문자열이 아닌 to 는 여전히 route 를 버린다
  assert.deepEqual(ok(v2((r) => { r.routes[0].skipped = [{ from: 'a', to: 5, reason: 'x' }]; })).routes, []);
});

test('W4: 점선 쌍은 routes.legs 의 from_ll·to_ll 과 같다(입력 순서와 무관), skipped·숙소는 잇지 않는다', () => {
  const b = ok(v2((r) => {
    r.routes = [{ id: 'day1', day: 1, date: '2026-10-15', legs: [leg({ from: '익선동', to: '창덕궁', from_ll: IKSEON, to_ll: CHANGDEOK })], skipped: [{ from: '창덕궁', to: '경복궁', reason: '좌표 없음' }] }];
  }));
  const links = pinLinks(b);
  assert.deepEqual(links, [{ from: 'pin2', to: 'pin1', day: 1 }]);
  const svg = buildBundleSvg(b, ko, null);
  assert.equal(svg.find((e) => e.tag === 'path' && (e.attrs?.class ?? '').includes('map-straight')).length, 1);
  assert.deepEqual(pinLinks(ok(v2((r) => { r.routes = [{ id: 'd', day: 1, date: null, legs: [leg({ from_ll: null, to_ll: GYEONGBOK })], skipped: [] }]; }))), []);
});

test('W5: 칩 키가 __proto__·constructor·toString 이어도 렌더가 끝나고, 위험 키 칩만 버린다', async () => {
  const mk = (key) => ({ key, tone: 'old', label: L('칩') });
  const b = ok(v2((r) => {
    r.rationale['mention:story_a'].chips = [mk('__proto__'), mk('constructor'), mk('prototype'), mk('toString'), mk('why')];
  }));
  assert.deepEqual(b.rationale['mention:story_a'].chips.map((c) => c.key), ['toString', 'why']);
  const { openItem } = await import('../src/components/rationale/logic.js');
  assert.equal(openItem({ chips: [], items: {} }, 'toString'), null);
  assert.equal(openItem({ chips: [], items: {} }, '__proto__'), null);
  const m = await mountRationale(b, { selectedNow: 'story_a' });
  assert.equal(m.root.find((e) => e.dataset?.act === 'chip').length, 2);
});
