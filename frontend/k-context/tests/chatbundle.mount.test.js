// 챗봇 묶음 화면: 타임라인·카드·지도(SVG·카카오) mount, 주입 문자열이 DOM 텍스트로만 들어가는지.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installFakeDom, El, fire, byAct, byClass } from './_fakedom_ctsl.js';

installFakeDom();
let innerHtmlWrites = 0;
Object.defineProperty(El.prototype, 'innerHTML', { set() { innerHtmlWrites += 1; }, get() { return ''; } });

// 실제 DOM 의 replaceChildren 은 문자열도 받는다(가짜 DOM 은 노드만) — 테스트 쪽에서 맞춘다
const baseReplace = El.prototype.replaceChildren;
El.prototype.replaceChildren = function replaceChildren(...nodes) { return baseReplace.call(this, ...nodes.map((n) => (typeof n === 'string' ? { nodeType: 3, text: n } : n))); };

const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createActions } = await import('../src/state/actions.js');
const { createApi } = await import('../src/api/index.js');
const { createT } = await import('../src/lib/i18n.js');
const { validateChatBundle } = await import('../src/api/bundle.js');
const { CHAT_BUNDLE_SAMPLE } = await import('../src/data/chat-bundle.js');
const { pinInfoNode, mentionNode, eventNode } = await import('../src/lib/chat-bundle-view.js');
const { pinInfo, bundlePins } = await import('../src/lib/chat-bundle.js');
const { createKakaoView } = await import('../src/components/map/kakao-view.js');
const timeline = await import('../src/components/timeline/index.js');
const cards = await import('../src/components/cards/index.js');
const map = await import('../src/components/map/index.js');

const EVIL = '<img src=x onerror=alert(1)>';
const mk = (edit) => { const raw = structuredClone(CHAT_BUNDLE_SAMPLE); edit?.(raw); return validateChatBundle(raw).bundle; };

async function setup(bundle, over = {}) {
  const store = createStore(createInitialState({ chatBundle: bundle, ...over }));
  const api = createApi({ mode: 'mock', latencyMs: 0 });
  const actions = createActions({ store, api });
  await actions.loadAll();
  const t = createT(() => store.getState().lang);
  return { store, actions, ctx: { store, api, t, actions }, t };
}
const all = (root, pred) => root.find(pred);
const texts = (root) => root.text;
/** 어떤 요소도 EVIL 문자열을 태그(img)로 만들지 않았다 — 텍스트 노드로만 존재. */
const noInjected = (root) => assert.equal(all(root, (e) => e.tag === 'img').length, 0);

test('타임라인: 챗봇 일정 제목·예시 표시·행·빈 시간 가정 문구·사실 표시', async () => {
  const { store, ctx } = await setup(mk());
  store.setState({ day: 1 });
  const root = new El('section', 'html');
  timeline.mount(root, ctx);
  assert.match(texts(root), /챗봇이 정리한 일정/);
  assert.equal(byClass(root, 'cb-flag').length, 1);
  const rows = byClass(root, 'timeline-row');
  assert.equal(rows.length, 4);
  assert.match(rows[0].text, /창덕궁/);
  assert.match(rows[0].text, /10:00–12:30/);
  const free = rows.find((r) => r.dataset.status === 'free');
  assert.match(free.text, /1일차 저녁 7시 이후가 비어 있다고 봤어요/);
  assert.match(free.text, /추정/);
  assert.equal(byAct(root, 'day').length, 4);
  // DAY 2: 시각을 확인하지 못한 앵커 + problems 의 사실 표시
  fire(byAct(root, 'day', '2')[0], 'click');
  assert.equal(store.getState().day, 2);
  assert.match(texts(root), /시각을 확인하지 못했어요/);
  assert.match(texts(root), /시각을 확인하지 못한 일정이 있어요/);
});

test('타임라인: 주입 문자열은 텍스트로만, en 전환, "예시 일정 보기" 로 복귀', async () => {
  const bundle = mk((r) => { r.itinerary.anchors[1].name = EVIL; r.problems.push({ code: 'ZZZ', message: EVIL }); });
  const { store, ctx } = await setup(bundle, { day: 1 });
  const root = new El('section', 'html');
  timeline.mount(root, ctx);
  assert.ok(texts(root).includes(EVIL));
  noInjected(root);
  store.setState({ lang: 'en' });
  assert.match(texts(root), /Itinerary organized by the chatbot/);
  fire(byAct(root, 'clear-bundle')[0], 'click');
  assert.equal(store.getState().chatBundle, null);
  assert.match(texts(root), /Leave hotel/, '고정 샘플 일정으로 복귀');
});

test('카드: 앵커별 실록 기록 카드(요약·원문·왕·날짜·작은 출처 태그·안전한 링크), 이야기라고 쓰지 않는다', async () => {
  const { ctx } = await setup(mk());
  const root = new El('section', 'html');
  cards.mount(root, ctx);
  const groups = root.find((e) => e.dataset?.kind === 'mention');
  assert.deepEqual(groups.map((g) => g.dataset.anchor), ['창덕궁', '경복궁']);
  assert.match(groups[0].text, /실록에서 언급된 기록 2건/);
  assert.match(root.text, /실록에 이런 기록이 있어요/);
  assert.match(root.text, /한글 요약\(원문 아님\)/);
  assert.match(root.text, /한문 원문 · 국역 없음/);
  assert.match(root.text, /음력/);
  const tag = byClass(groups[0], 'cb-srctag')[0];
  assert.equal(tag.text, '[A] 조선왕조실록 (예시)');
  assert.equal(tag.dataset['grade'] ?? tag.attrs['data-grade'], 'A');
  const a = root.find((e) => e.tag === 'a')[0];
  assert.equal(a.attrs.target, '_blank');
  assert.equal(a.attrs.rel, 'noopener noreferrer');
  assert.match(a.attrs.href, /^https:/);
  assert.ok(!/이야기라|story/i.test(root.text.replace('이야기로 풀어 쓴 것이 아니에요', '')), '이야기라고 쓰지 않는다');
});

test('카드: 주입 문자열·위험 URL 은 텍스트/링크 없음으로만', async () => {
  const bundle = mk((r) => {
    const m = r.mentions.anchors[0].mentions[0];
    m.title_summary = EVIL; m.quote = EVIL; m.king = EVIL; m.url = 'javascript:alert(1)'; m.source.name = EVIL;
    r.events.events[0].title = EVIL; r.events.events[0].venue.name = EVIL;
    r.events.events[0].links[0].url = 'javascript:alert(1)';
  });
  const { ctx } = await setup(bundle);
  const root = new El('section', 'html');
  cards.mount(root, ctx);
  noInjected(root);
  assert.ok(root.text.includes(EVIL));
  for (const a of root.find((e) => e.tag === 'a')) assert.match(a.attrs.href, /^https?:/);
  assert.equal(root.find((e) => e.tag === 'a' && /javascript/i.test(e.attrs.href ?? '')).length, 0);
  assert.equal(innerHtmlWrites, 0);
});

test('카드: 행사 — tier C 는 "검색 수집 · 미확인" 딱지, tier A 는 딱지 없음, 행사 없으면 사실대로', async () => {
  const { ctx, store } = await setup(mk());
  const root = new El('section', 'html');
  cards.mount(root, ctx);
  const ev = root.find((e) => e.dataset?.kind === 'event');
  assert.equal(ev.length, 1);
  assert.match(ev[0].text, /\(예시\) 저녁 야외 공연/);
  assert.match(ev[0].text, /2026-10-16/);
  assert.match(ev[0].text, /○○ 광장/);
  assert.match(ev[0].text, /\[C\] 검색 수집 \(예시\)/);
  assert.equal(root.find((e) => e.dataset?.flag === 'unverified').length, 1);
  assert.match(ev[0].text, /공식 링크/);
  store.setState({ chatBundle: mk((r) => { r.events.events[0].links[0].tier = 'A'; }) });
  assert.equal(root.find((e) => e.dataset?.flag === 'unverified').length, 0);
  store.setState({ chatBundle: mk((r) => { r.events = { events: [], excluded: [], problems: [], coverage: {} }; }) });
  assert.equal(root.find((e) => e.dataset?.empty === 'events').length, 1);
  assert.match(root.text, /주변 행사를 아직 찾지 못했어요\(데이터 준비 중\)/);
  store.setState({ chatBundle: mk((r) => { r.events = null; }) });
  assert.match(root.text, /주변 행사를 아직 찾지 못했어요/);
  assert.equal(root.find((e) => e.dataset?.kind === 'event').length, 0);
});

test('정보창 노드: 이름·건수·왕·날짜·요약·원문·출처 태그·링크, 주입은 텍스트', async () => {
  const { t } = await setup(mk());
  const bundle = mk((r) => { r.mentions.anchors[0].mentions[0].quote = EVIL; r.itinerary.anchors[1].name = EVIL; r.mentions.anchors[0].anchor.name = EVIL; });
  const node = pinInfoNode(pinInfo(bundlePins(bundle)[0]), t);
  assert.ok(node.text.includes(EVIL));
  assert.equal(node.find((e) => e.tag === 'img').length, 0);
  assert.match(node.text, /실록 언급 2건/);
  assert.match(node.text, /○○왕 \(예시\)/);
  assert.match(node.text, /한글 요약\(원문 아님\)/);
  assert.match(node.text, /\[A\] 조선왕조실록 \(예시\)/);
  assert.equal(node.find((e) => e.tag === 'a').length, 1);
  const none = pinInfoNode(pinInfo(bundlePins(mk())[1]), t);
  assert.match(none.text, /실록 언급 기록을 찾지 못했어요/);
  assert.ok(mentionNode && eventNode);
});

test('지도(SVG): 좌표 있는 앵커만 핀, 누르면 정보창 패널, 다시 누르거나 닫기로 닫힘, 옛길 선 없음', async () => {
  const { ctx, store } = await setup(mk());
  const root = new El('section', 'html');
  map.mount(root, ctx);
  const pins = byAct(root, 'pin');
  assert.equal(pins.length, 3, '호텔·신촌(좌표 없음) 제외');
  assert.equal(root.find((e) => e.attrs?.class === 'map-seg').length, 0);
  assert.equal(byClass(root, 'map-pinpanel').length, 0);
  fire(pins[0], 'click');
  const panel = byClass(root, 'map-pinpanel')[0];
  assert.match(panel.text, /창덕궁/);
  assert.match(panel.text, /실록 언급 2건/);
  assert.equal(byAct(root, 'pin')[0].attrs['aria-pressed'], 'true');
  fire(byAct(root, 'pin-close')[0], 'click');
  assert.equal(byClass(root, 'map-pinpanel').length, 0);
  // 일정이 바뀌면 열린 정보창은 닫힌다
  fire(byAct(root, 'pin')[1], 'click');
  assert.equal(byClass(root, 'map-pinpanel').length, 1);
  store.setState({ chatBundle: mk((r) => { r.itinerary.anchors.length = 1; }) });
  assert.equal(byClass(root, 'map-pinpanel').length, 0);
  assert.equal(byAct(root, 'pin').length, 0);
  assert.match(root.text, /좌표가 확인된 장소가 없어요/);
});

test('지도(SVG): chatBundle 이 없으면 기존 mock 화면 그대로(경로 카드 3개)', async () => {
  const { ctx } = await setup(null);
  const root = new El('section', 'html');
  map.mount(root, ctx);
  assert.equal(byAct(root, 'route').length, 3);
  assert.equal(byAct(root, 'pin').length, 0);
});

/** 가짜 kakao SDK. */
function fakeKakao() {
  const log = { markers: [], infos: [], lines: [], handlers: [] };
  class LatLng { constructor(a, b) { this.lat = a; this.lng = b; } }
  class MapC { constructor(host, o) { this.o = o; } relayout() {} setBounds(b) { this.bounds = b; } setCenter(c) { this.center = c; } setLevel() {} }
  class Marker { constructor(o) { this.o = o; log.markers.push(this); } setMap(m) { this.map = m; } }
  class Polyline { constructor() { log.lines.push(this); } setMap() {} }
  class InfoWindow { constructor(o) { this.o = o; log.infos.push(this); } open() {} close() {} }
  class LatLngBounds { extend() {} }
  return { log, maps: { LatLng, Map: MapC, Marker, Polyline, InfoWindow, LatLngBounds, event: { addListener: (target, type, fn) => log.handlers.push({ target, type, fn }) } } };
}

test('지도(카카오): 좌표 있는 앵커에만 마커, 선 없음, 클릭하면 정보창 DOM(textContent)', async () => {
  const { t } = await setup(null);
  const kakao = fakeKakao();
  const view = createKakaoView(kakao, new El('div', 'html'), t);
  const bundle = mk((r) => { r.mentions.anchors[0].mentions[0].king = EVIL; });
  view.update({ chatBundle: bundle, data: {}, day: 1 });
  assert.equal(kakao.log.markers.length, 3);
  assert.equal(kakao.log.lines.length, 0);
  assert.deepEqual(kakao.log.markers.map((m) => m.o.title), ['창덕궁', '익선동', '경복궁']);
  kakao.log.handlers[0].fn();
  const content = kakao.log.infos[0].o.content;
  assert.ok(content.text.includes(EVIL));
  assert.equal(content.find((e) => e.tag === 'img').length, 0);
  assert.match(content.text, /실록 언급 2건/);
  assert.equal(innerHtmlWrites, 0);
  // 좌표 없는 일정만 있으면 핀 없음 + 안내
  view.update({ chatBundle: mk((r) => { r.itinerary.anchors.length = 1; }), data: {}, day: 1 });
  assert.match(view.status.text, /좌표가 확인된 장소가 없어요/);
});
