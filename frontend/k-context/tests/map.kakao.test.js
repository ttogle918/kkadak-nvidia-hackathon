// 카카오 렌더러: 렌더러 선택·폴백·좌표 건너뜀·textContent 경로·경고에 키 없음. 가짜 window/document 만 쓴다(네트워크·키 없음).
import { test } from 'node:test';
import assert from 'node:assert/strict';

class El {
  constructor(tag) { this.tag = tag; this.attrs = {}; this.children = []; this.listeners = {}; this.style = {}; this.dataset = {}; this.nodeType = 1; this.parent = null; }
  setAttribute(k, v) { this.attrs[k] = v; }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  addEventListener(t, fn) { (this.listeners[t] ||= []).push(fn); }
  removeEventListener() {}
  replaceChildren(...n) { this.children = []; n.forEach((x) => this.appendChild(typeof x === 'string' ? { nodeType: 3, text: x } : x)); }
  get text() { return this.children.map((c) => c.text).join(''); }
  find(pred, out = []) { if (pred(this)) out.push(this); this.children.forEach((c) => c.find?.(pred, out)); return out; }
}
// innerHTML 에 쓰면 기록되도록 setter 를 건다
let innerHtmlWrites = 0;
Object.defineProperty(El.prototype, 'innerHTML', { set() { innerHtmlWrites += 1; }, get() { return ''; } });
globalThis.document = {
  createElement: (t) => new El(t),
  createElementNS: (ns, t) => new El(t),
  createTextNode: (s) => ({ nodeType: 3, text: s }),
  head: new El('head'),
};

const { loadKakaoSdk, readKey, sdkUrl } = await import('../src/lib/kakao-sdk.js');
const { selectRenderer } = await import('../src/components/map/renderer.js');
const { collectGeo, computeBounds, createKakaoView, DEFAULT_CENTER, validLatLng, getMyLocation, MOCK_MY_LOCATION } = await import('../src/components/map/kakao-view.js');
const map = await import('../src/components/map/index.js');
const { createStore } = await import('../src/lib/store.js');
const { createApi } = await import('../src/api/index.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createT } = await import('../src/lib/i18n.js');

const KEY = 'SECRET_TEST_KEY_abc123';
const tick = () => new Promise((r) => setTimeout(r, 0));

/** 가짜 SDK: 스크립트 삽입 시 behavior 에 따라 onload/onerror 를 부른다. */
function fakeEnv({ key = KEY, behavior = 'ok', hasGlobal = true } = {}) {
  const inserted = [];
  const doc = { head: { appendChild: (s) => { inserted.push(s); queueMicrotask(() => { if (behavior === 'error') s.onerror?.(); else if (behavior === 'ok') { if (hasGlobal) win.kakao = makeKakao(); s.onload?.(); } }); } }, createElement: (t) => ({ tag: t }) };
  const win = { KC_KAKAO_JS_KEY: key };
  return { win, doc, inserted };
}

function makeKakao() {
  const log = { markers: [], lines: [], infos: [], overlays: [], map: null };
  class LatLng { constructor(a, b) { this.lat = a; this.lng = b; } }
  class Map { constructor(host, o) { this.host = host; this.o = o; log.map = this; } relayout() {} setBounds(b) { this.bounds = b; } setCenter(c) { this.center = c; } setLevel() {} }
  class Marker { constructor(o) { this.o = o; log.markers.push(this); } setMap(m) { this.map = m; } }
  class Polyline { constructor(o) { this.o = o; log.lines.push(this); } setMap(m) { this.map = m; } }
  class InfoWindow { constructor(o) { this.o = o; log.infos.push(this); } open() {} close() {} }
  class CustomOverlay { constructor(o) { this.o = o; log.overlays.push(this); } setMap(m) { this.map = m; } }
  class LatLngBounds { constructor() { this.pts = []; } extend(p) { this.pts.push(p); } }
  const handlers = [];
  return { log, handlers, maps: { load: (cb) => cb(), LatLng, Map, Marker, Polyline, InfoWindow, LatLngBounds, CustomOverlay, event: { addListener: (target, type, fn) => handlers.push({ e: target, t: type, fn }) } } };
}

test('키 없음 -> SVG 폴백, 경고 한 줄, 스크립트 삽입 없음', async () => {
  const { win, doc, inserted } = fakeEnv({ key: null });
  const warns = [];
  const r = await selectRenderer({ win, doc, warn: (m) => warns.push(m) });
  assert.equal(r.kind, 'svg');
  assert.equal(warns.length, 1);
  assert.equal(inserted.length, 0);
  assert.equal(readKey({ KC_KAKAO_JS_KEY: 'JAVASCRIPT_KEY_HERE' }), null, '자리표시자는 키 없음');
});

test('SDK 로드 실패 / kakao 전역 부재 / 타임아웃 -> 폴백, 경고에 키 없음', async () => {
  for (const [behavior, hasGlobal] of [['error', true], ['ok', false], ['never', true]]) {
    const { win, doc } = fakeEnv({ behavior, hasGlobal });
    const warns = [];
    const r = await selectRenderer({ win, doc, warn: (m) => warns.push(m), timeoutMs: 20 });
    assert.equal(r.kind, 'svg', behavior);
    assert.equal(warns.length, 1);
    assert.ok(!warns[0].includes(KEY), '경고에 키 값 없음');
    assert.ok(!warns[0].includes('appkey'), '경고에 URL 없음');
  }
});

test('키 있음 + 로드 성공 -> 카카오 렌더러, URL 은 dapi.kakao.com autoload=false', async () => {
  const { win, doc, inserted } = fakeEnv();
  const warns = [];
  const r = await selectRenderer({ win, doc, warn: (m) => warns.push(m) });
  assert.equal(r.kind, 'kakao');
  assert.equal(warns.length, 0);
  assert.equal(inserted.length, 1);
  assert.ok(inserted[0].src.startsWith('https://dapi.kakao.com/v2/maps/sdk.js?appkey='));
  assert.ok(inserted[0].src.endsWith('&autoload=false'));
  assert.equal(sdkUrl('a b'), 'https://dapi.kakao.com/v2/maps/sdk.js?appkey=a%20b&autoload=false');
  assert.ok((await loadKakaoSdk({ win: {}, doc })).reason);
});

const CARD = (id, over) => ({ id, kind: 'now', title: id, badge: '확인됨', place: { name: id, lat: null, lng: null }, geometry: { type: 'point', space: 'geo', coords: [] }, ...over });
const t = createT(() => 'ko');
const stateWith = (cards, routes = []) => ({ selectedRoute: 'A', data: { cards, routes } });

test('lat/lng null·범위 밖 항목은 건너뛴다 (mock 은 전부 null -> 빈 결과)', () => {
  const g = collectGeo(stateWith([
    CARD('a', { place: { name: '덕수궁', lat: 37.56556, lng: 126.97489 } }),
    CARD('b'),
    CARD('c', { place: { name: 'x', lat: 999, lng: 0 } }),
    CARD('d', { geometry: { type: 'point', space: 'schematic', coords: [[300, 200]] } }),
  ], [{ id: 'A', segments: [
    { card_id: 'a', coords: [[37.56556, 126.97489], [37.56541, 126.97273]] },
    { card_id: 'b', coords: [[null, null], [37.5, 126.9]] },
    { card_id: 'd', coords: [[300, 200], [310, 210]] },
  ] }]), t);
  assert.deepEqual(g.markers.map((m) => m.title), ['덕수궁']);
  assert.equal(g.lines.length, 1);
  assert.equal(validLatLng([null, 1]), false);
});

test('앵커 좌표가 모두 null 이면 기본 중심만 + 좌표 없음 상태, 마커·선 없음', async () => {
  const { win, doc } = fakeEnv();
  const r = await selectRenderer({ win, doc });
  const store = createStore(createInitialState());
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  await createActions({ store, api }).loadAll();
  const view = createKakaoView(r.kakao, new El('div'), t);
  const st0 = store.getState();
  const noGeo = { ...st0, data: { ...st0.data, itinerary: { ...st0.data.itinerary, anchors: st0.data.itinerary.anchors.map((a) => ({ ...a, lat: null, lng: null })) } } };
  view.update(noGeo);
  const log = r.kakao.log;
  assert.equal(log.markers.length + log.lines.length, 0);
  assert.equal(log.map.o.center.lat, DEFAULT_CENTER.lat);
  assert.match(view.status.text, /좌표 없음/);
});

test('샘플 좌표(덕수궁·정동제일교회): 마커·폴리라인 생성, 텍스트는 title 속성/textContent 로만', async () => {
  const { win, doc } = fakeEnv();
  const r = await selectRenderer({ win, doc });
  const evil = '<img src=x onerror=alert(1)>';
  const st = stateWith([
    CARD('a', { place: { name: '덕수궁', lat: 37.56556, lng: 126.97489 } }),
    CARD('b', { place: { name: evil, lat: 37.56541, lng: 126.97273 } }),
  ], [{ id: 'A', segments: [{ card_id: 'a', coords: [[37.56556, 126.97489], [37.56541, 126.97273]] }] }]);
  const before = innerHtmlWrites;
  const view = createKakaoView(r.kakao, new El('div'), t);
  view.update(st);
  const { log, handlers } = r.kakao;
  assert.equal(log.markers.length, 2);
  assert.equal(log.lines.length, 1);
  assert.equal(log.markers[1].o.title, evil, '문자열 그대로 속성에(해석되지 않음)');
  handlers.find((h) => h.e === log.markers[1]).fn();
  const content = log.infos[0].o.content;
  assert.equal(typeof content, 'object', 'InfoWindow content 는 문자열이 아니라 DOM 노드');
  assert.equal(content.text, evil, 'textContent(텍스트 노드)로만 들어감');
  assert.equal(innerHtmlWrites, before, 'innerHTML 미사용');
  assert.equal(view.status.text, '');
});

test('map.mount: 카카오 선택 시 SVG 대신 카카오 호스트, 실패 시 SVG 유지', async () => {
  for (const ok of [true, false]) {
    const { win, doc } = fakeEnv({ behavior: ok ? 'ok' : 'error' });
    const mapRenderer = selectRenderer({ win, doc, warn() {} });
    const store = createStore(createInitialState());
    const api = createApi({ mode: 'mock', latencyMs: 0 });
    const actions = createActions({ store, api });
    await actions.loadAll();
    const root = new El('section');
    root.contains = () => false; // 포커스 복원 경로 우회
    const m = map.mount(root, { store, api, t, actions, mapRenderer });
    await tick(); await tick();
    assert.equal(root.find((e) => e.attrs?.class === 'map-kakao').length, ok ? 1 : 0);
    assert.equal(root.find((e) => e.attrs?.class === 'map-svg').length, ok ? 0 : 1);
    m.destroy();
  }
});

const ANC = (type, name, lat, lng, day) => ({ type, name: { ko: name, en: name }, lat, lng, day });
const stAnc = (anchors, extra = {}) => ({ day: 1, selectedRoute: 'A', data: { cards: [], routes: [], itinerary: { anchors } }, ...extra });

test('앵커 -> 마커 변환: [lat,lng] 순서, kind, title=t(name), null 앵커는 건너뜀', () => {
  const g = collectGeo(stAnc([
    ANC('hotel', '숙소', 37.5704, 126.9921), ANC('visit', '창덕궁', 37.5796, 126.991, 1), ANC('visit', '신촌', null, null, 1),
  ]), t);
  assert.deepEqual(g.markers, [
    { lat: 37.5704, lng: 126.9921, title: '숙소', kind: 'hotel' },
    { lat: 37.5796, lng: 126.991, title: '창덕궁', kind: 'visit' },
  ]);
  assert.ok(g.markers.every((m) => m.lat > 33 && m.lat < 39 && m.lng > 124 && m.lng < 132), '서울 위도/경도 순서');
});

test('day 필터: hotel 은 항상, visit 은 선택한 날만. 카드와 같은 자리는 중복 제외', () => {
  const anchors = [ANC('hotel', '숙소', 37.57, 126.99), ANC('visit', 'D1', 37.58, 126.99, 1), ANC('visit', 'D2', 37.577, 126.976, 2)];
  assert.deepEqual(collectGeo(stAnc(anchors, { day: 2 }), t).markers.map((m) => m.title), ['숙소', 'D2']);
  assert.deepEqual(collectGeo(stAnc(anchors, { day: 3 }), t).markers.map((m) => m.title), ['숙소']);
  const dup = collectGeo({ ...stAnc(anchors), data: { cards: [CARD('c', { place: { name: '카드', lat: 37.58, lng: 126.99 } })], routes: [], itinerary: { anchors } } }, t);
  assert.deepEqual(dup.markers.map((m) => m.title), ['카드', '숙소']);
});

test('computeBounds: 순수, [lat,lng], 무효 점 무시, 빈 입력 null', () => {
  assert.equal(computeBounds([]), null);
  assert.equal(computeBounds([[null, 1]]), null);
  assert.deepEqual(computeBounds([[37.5, 127.0], [37.6, 126.9], [999, 0]]), { sw: [37.5, 126.9], ne: [37.6, 127.0] });
});

test('mock 앵커: 5곳 마커 + setBounds, 좌표 없음 문구 숨김 / 1개면 중심만', async () => {
  const { win, doc } = fakeEnv();
  const r = await selectRenderer({ win, doc });
  const store = createStore(createInitialState());
  await createActions({ store, api: createApi({ mode: 'mock', latencyMs: 0 }) }).loadAll();
  const view = createKakaoView(r.kakao, new El('div'), t);
  view.update(store.getState()); // day 1: 숙소 + 창덕궁 + 익선동
  assert.deepEqual(r.kakao.log.markers.map((m) => m.o.title), ['숙소 · 종로3가', '창덕궁', '익선동']);
  assert.ok(r.kakao.log.map.bounds.pts.length >= 2);
  assert.equal(view.status.text, '');
  const one = makeKakao();
  const v2 = createKakaoView(one, new El('div'), t);
  v2.update(stAnc([ANC('hotel', '숙소', 37.57, 126.99)]));
  assert.equal(one.log.markers.length, 1);
  assert.ok(one.log.map.bounds, '일정 1개 + 내 위치 = 2점이라 setBounds');
});

test('내 위치(예시): 별도 레이어, [lat,lng], 예시 라벨, bounds 포함, day 무관, geolocation 미사용, textContent', async () => {
  let geoTouched = 0;
  Object.defineProperty(globalThis, 'navigator', { configurable: true, value: { get geolocation() { geoTouched += 1; return {}; } } });
  const before = innerHtmlWrites;
  assert.deepEqual(getMyLocation(), MOCK_MY_LOCATION);
  assert.equal(MOCK_MY_LOCATION.lat, DEFAULT_CENTER.lat);
  assert.equal(MOCK_MY_LOCATION.lng, DEFAULT_CENTER.lng);
  assert.equal(collectGeo(stAnc([]), t).markers.length, 0, '내 위치는 collectGeo 결과에 섞이지 않음');
  for (const day of [1, 2, 3]) {
    const k = makeKakao();
    const view = createKakaoView(k, new El('div'), t);
    view.update(stAnc([ANC('visit', '창덕궁', 37.5796, 126.991, 1)], { day }));
    assert.equal(k.log.overlays.length, 1, 'day ' + day + ' 에도 항상 표시');
    const ov = k.log.overlays[0];
    assert.equal(ov.o.position.lat, 37.56556);
    assert.equal(ov.o.position.lng, 126.97489);
    assert.equal(ov.o.content.attrs.title, '내 위치 (예시)');
    assert.equal(ov.o.content.find((e) => e.attrs?.class === 'map-kakao__me-label')[0].text, '내 위치 (예시)', '텍스트 노드로만');
    assert.ok(k.log.markers.every((m) => m.o.title !== '내 위치 (예시)'), '일반 마커와 별개');
    if (day !== 1) assert.equal(k.log.markers.length, 0);
    assert.ok(ov.map, 'setMap 됨');
  }
  const k = makeKakao();
  createKakaoView(k, new El('div'), t).update(stAnc([ANC('visit', '창덕궁', 37.5796, 126.991, 1)]));
  const pts = k.log.map.bounds.pts;
  assert.ok(pts.some((p) => p.lat === 37.56556 && p.lng === 126.97489), 'bounds 에 내 위치 포함');
  assert.ok(pts.some((p) => p.lat === 37.5796), 'bounds 에 일정 포함');
  const en = createT(() => 'en');
  const ke = makeKakao();
  createKakaoView(ke, new El('div'), en).update(stAnc([]));
  assert.equal(ke.log.overlays[0].o.content.attrs.title, 'My location (sample)');
  // 일정 없음: 내 위치만 + 일정 좌표 없음 문구
  const k0 = makeKakao();
  const v0 = createKakaoView(k0, new El('div'), t);
  v0.update(stAnc([]));
  assert.match(v0.status.text, /일정 좌표 없음/);
  assert.equal(k0.log.map.bounds, undefined, '점 하나면 중심만');
  // CustomOverlay 없는 SDK: title 만 있는 Marker 로 대체
  const kn = makeKakao();
  delete kn.maps.CustomOverlay;
  createKakaoView(kn, new El('div'), t).update(stAnc([]));
  assert.equal(kn.log.markers[0].o.title, '내 위치 (예시) · MOCK'); // MOCK 표시 추가로 갱신: Marker 는 title 만 보이므로 MOCK 을 붙인다
  assert.equal(geoTouched, 0, 'navigator.geolocation 접근 없음');
  assert.equal(innerHtmlWrites, before, 'innerHTML 미사용');
  delete globalThis.navigator;
});
