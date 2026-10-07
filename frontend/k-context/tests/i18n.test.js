import { test } from 'node:test';
import assert from 'node:assert/strict';
import { translate, createT, DICTS, normalizeLang, bindDocumentLang } from '../src/lib/i18n.js';
import { createStore } from '../src/lib/store.js';

test('ko/en 사전의 키가 정확히 같다', () => {
  const ko = Object.keys(DICTS.ko).sort();
  const en = Object.keys(DICTS.en).sort();
  assert.deepEqual(ko, en);
  for (const k of ko) {
    assert.ok(DICTS.ko[k] !== '', `ko ${k} 비어 있음`);
    assert.ok(DICTS.en[k] !== '', `en ${k} 비어 있음`);
  }
});

test('사전 키 · {ko,en} · 그대로 문자열', () => {
  assert.equal(translate('ko', 'topbar.mode.old'), '옛날');
  assert.equal(translate('en', 'topbar.mode.old'), 'Old');
  assert.equal(translate('en', { ko: '안녕', en: 'Hello' }), 'Hello');
  assert.equal(translate('ko', { ko: '안녕', en: 'Hello' }), '안녕');
  assert.equal(translate('en', '○○ 야장'), '○○ 야장');
  assert.equal(translate('ko', null), '');
});

test('{name} 보간과 알 수 없는 언어는 ko', () => {
  assert.equal(translate('en', 'topbar.day', { n: 2 }), 'DAY 2');
  assert.equal(translate('xx', 'card.more_sources', { n: 3 }), '+3 출처');
  assert.equal(normalizeLang('fr'), 'ko');
  assert.equal(translate('ko', 'topbar.day'), 'DAY {n}'); // 값이 없으면 자리표시 유지
});

test('{en} 이 빠진 객체는 ko 로 대체', () => {
  assert.equal(translate('en', { ko: '한글만' }), '한글만');
});

test('createT 는 현재 언어를 따라간다', () => {
  const st = createStore({ lang: 'ko' });
  const t = createT(() => st.getState().lang);
  assert.equal(t('card.old'), '옛날 카드');
  st.setState({ lang: 'en' });
  assert.equal(t('card.old'), 'OLD · STORY');
});

test('bindDocumentLang 은 <html lang> 을 맞춘다', () => {
  const doc = { documentElement: { lang: '' } };
  const st = createStore({ lang: 'ko' });
  bindDocumentLang(st, doc);
  assert.equal(doc.documentElement.lang, 'ko');
  st.setState({ lang: 'en' });
  assert.equal(doc.documentElement.lang, 'en');
});

test('모듈 플레이스홀더용 키가 모든 모듈에 있다', () => {
  for (const m of ['map', 'cards', 'chat', 'timeline', 'rationale', 'securitylog']) assert.ok(DICTS.ko[`module.${m}`], m);
});
