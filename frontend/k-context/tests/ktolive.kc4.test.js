// T435: 한국관광공사 관광정보(원문) 절 — 값 불변·출처 유형·링크·unavailable·절 없음·지도 분리·textContent
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { installFakeDom, El } from './_fakedom_ctsl.js';

installFakeDom();
let innerHtmlWrites = 0;
Object.defineProperty(El.prototype, 'innerHTML', { set() { innerHtmlWrites += 1; }, get() { return ''; } });
const baseReplace = El.prototype.replaceChildren;
El.prototype.replaceChildren = function replaceChildren(...nodes) { return baseReplace.call(this, ...nodes.map((n) => (typeof n === 'string' ? { nodeType: 3, text: n } : n))); };

const { validateChatBundle } = await import('../src/api/bundle.js');
const { CHAT_BUNDLE_SAMPLE } = await import('../src/data/chat-bundle.js');
const { ktoView } = await import('../src/components/ktolive/logic.js');
const { mount } = await import('../src/components/ktolive/index.js');
const { createStore } = await import('../src/lib/store.js');
const { createInitialState } = await import('../src/state/initial.js');
const { createT } = await import('../src/lib/i18n.js');
const ko = (await import('../src/i18n/ko.js')).default;
const en = (await import('../src/i18n/en.js')).default;

const ATT = { Type3: '출처: 한국관광공사 TourAPI · 공공누리 제3유형(변경금지)', Type1: '출처: 한국관광공사 TourAPI · 공공누리 제1유형(출처표시)' };
const SRC = 'https://www.data.go.kr/data/15101578/openapi.do';
const ITEM = { contentid: '1', title: '<b>축제</b>', addr1: '서울 종로구', addr2: '1층', eventstartdate: '20261001', eventenddate: '20261031', tel: '02-000', progresstype: '진행', lDongSignguCd: '110', cpyrhtDivCd: 'Type1' };
const live = (over = {}) => ({ status: 'ok', reason: null, fetched_at: '2026-10-10T10:00:00+09:00', total: 1, items: [ITEM], attribution: ATT, source_url: SRC, ...over });
const mk = (kto) => { const raw = structuredClone(CHAT_BUNDLE_SAMPLE); raw.schema = 'kc-chat-bundle/v2'; if (kto !== undefined) raw.kto_live = kto; const r = validateChatBundle(raw); assert.ok(r.ok); return r.bundle; };
const t = createT(() => 'ko');
const walk = (n, acc = []) => { acc.push(n); (n.children ?? []).forEach((c) => walk(c, acc)); return acc; };

test('검증기: 계약 키만 복사, 모르는 키·문자열 아닌 값 버림, items 20', () => {
  const b = mk(live({ items: Array.from({ length: 30 }, () => ({ ...ITEM, mapx: '127', firstimage: 'http://x/y.jpg', tel: 5 })), extra: 1 }));
  assert.equal(b.kto_live.items.length, 20);
  assert.deepEqual(Object.keys(b.kto_live.items[0]).sort(), ['addr1', 'addr2', 'contentid', 'cpyrhtDivCd', 'eventenddate', 'eventstartdate', 'lDongSignguCd', 'progresstype', 'title'].sort());
  assert.ok(!('extra' in b.kto_live));
  assert.equal(mk(live({ status: 'weird' })).kto_live, null);
  assert.equal(mk(undefined).kto_live, null);
});

test('값 불변: 입력 문자열 = 출력 문자열', () => {
  const v = ktoView(mk(live()), t);
  const f = Object.fromEntries(v.items[0].fields.map((x) => [x.key, x.value]));
  assert.equal(f.title, '<b>축제</b>');
  assert.equal(f.addr, '서울 종로구 1층');
  assert.equal(f.period, '20261001–20261031');
  assert.equal(f.tel, '02-000');
  assert.equal(v.sourceUrl, SRC);
});

test('출처 문구: 유형별, 모르는 값·없음은 Type3', () => {
  const v = ktoView(mk(live({ items: [{ ...ITEM, cpyrhtDivCd: 'Type1' }, { ...ITEM, cpyrhtDivCd: 'Type3' }, { ...ITEM, cpyrhtDivCd: 'Type9' }, { ...ITEM, cpyrhtDivCd: undefined }] })), t);
  assert.deepEqual(v.items.map((i) => i.attribution), [ATT.Type1, ATT.Type3, ATT.Type3, ATT.Type3]);
});

test('필드 없음이면 절 없음 · unavailable · 0건', () => {
  assert.equal(ktoView(mk(undefined), t).state, 'none');
  assert.equal(ktoView(null, t).state, 'none');
  assert.equal(ktoView(mk(live({ status: 'unavailable', reason: 'limit', items: [] })), t).state, 'unavailable');
  const z = ktoView(mk(live({ items: [], total: 0 })), t);
  assert.equal(z.state, 'ok'); assert.equal(z.items.length, 0);
});

test('문구', () => {
  assert.equal(ko['ktolive.title'], '한국관광공사 관광정보(원문)');
  assert.equal(en['ktolive.title'], 'Korea Tourism Organization data (original text)');
  assert.equal(ko['ktolive.unavailable'], '지금 확인할 수 없음');
  assert.equal(ko['ktolive.empty'], '이 기간의 관광공사 행사 정보가 없습니다');
  assert.equal(ko['ktolive.link'], '원문 출처 보기');
  for (const k of Object.keys(ko)) if (k.startsWith('ktolive.')) assert.ok(en[k], k);
});

function draw(kto) {
  const store = createStore(createInitialState({ chatBundle: kto === undefined ? null : mk(kto) }));
  const root = document.createElement('section');
  mount(root, { store, t: createT(() => store.getState().lang) });
  return { store, root };
}
const textOf = (root) => walk(root).filter((n) => n.nodeType === 3).map((n) => n.text ?? n.textContent ?? '').join('|');

test('mount: 항목·출처 문구·링크 속성·스크립트 문자열은 글자로, innerHTML 쓰기 없음', () => {
  const before = innerHtmlWrites;
  const evil = '<script>alert(1)</script>';
  const { root } = draw(live({ items: [{ ...ITEM, title: evil }] }));
  const txt = textOf(root);
  assert.ok(txt.includes(evil));
  assert.ok(txt.includes(ATT.Type1));
  assert.ok(txt.includes('한국관광공사 관광정보(원문)'));
  const a = walk(root).find((n) => n.tag === 'a');
  assert.equal(a.attrs.href, SRC);
  assert.equal(a.attrs.rel, 'noopener noreferrer');
  assert.equal(a.attrs.target, '_blank');
  assert.equal(walk(root).filter((n) => n.tag === 'img').length, 0);
  assert.equal(innerHtmlWrites, before);
});

test('mount: unavailable·0건·없음', () => {
  assert.ok(textOf(draw(live({ status: 'unavailable', items: [] })).root).includes('지금 확인할 수 없음'));
  assert.ok(textOf(draw(live({ items: [] })).root).includes('이 기간의 관광공사 행사 정보가 없습니다'));
  const none = draw(undefined).root;
  assert.equal(textOf(none), '');
});

test('지도·행사 모듈은 kto_live 를 읽지 않는다', () => {
  const dirs = ['src/components/map', 'src/components/cards', 'src/lib'];
  for (const d of dirs) for (const f of readdirSync(new URL(`../${d}/`, import.meta.url))) {
    if (!f.endsWith('.js')) continue;
    assert.ok(!readFileSync(new URL(`../${d}/${f}`, import.meta.url), 'utf8').includes('kto_live'), `${d}/${f}`);
  }
});

test('mock 예시 묶음에 kto_live 없음', () => {
  assert.ok(!('kto_live' in CHAT_BUNDLE_SAMPLE));
});

test('상한을 넘는 값은 자르지 않고 그 항목을 버린다(D29 ② 변경금지)', () => {
  const long = { ...ITEM, contentid: '2', title: '가'.repeat(301) };
  const b = mk(live({ items: [ITEM, long], total: 2 }));
  assert.deepEqual(b.kto_live.items.map((x) => x.contentid), ['1']);
  assert.equal(b.kto_live.items[0].title, ITEM.title);
  assert.ok(!JSON.stringify(b.kto_live).includes('…'));
});
