// 다국어. 문자열은 세 가지 형태로 들어온다.
//  1) 사전 키        t('topbar.mode.old')            -> src/i18n/{ko,en}.js 에서 찾는다
//  2) {ko, en} 객체  t({ko:'안녕', en:'Hello'})       -> 샘플 데이터·API 응답이 쓰는 형태
//  3) 그 외 문자열    t('○○ 야장')                   -> 사전에 없으면 그대로 돌려준다(API 가 이미 한 언어로 준 문자열)
// {name} 자리표시는 params 로 채운다.
import ko from '../i18n/ko.js';
import en from '../i18n/en.js';

export const LANGS = ['ko', 'en'];
export const DEFAULT_LANG = 'ko';
export const DICTS = { ko, en };

export function normalizeLang(lang) {
  return LANGS.includes(lang) ? lang : DEFAULT_LANG;
}

function interpolate(text, params) {
  if (!params) return text;
  return text.replace(/\{(\w+)\}/g, (m, k) => (k in params ? String(params[k]) : m));
}

/** 순수 함수 버전. 테스트와 비-DOM 코드가 쓴다. */
export function translate(lang, input, params) {
  const l = normalizeLang(lang);
  if (input == null) return '';
  let out;
  if (typeof input === 'string') {
    const d = DICTS[l];
    out = Object.hasOwn(d, input) ? d[input] : Object.hasOwn(DICTS[DEFAULT_LANG], input) ? DICTS[DEFAULT_LANG][input] : input;
  } else if (typeof input === 'object') {
    out = input[l] ?? input[DEFAULT_LANG] ?? input.en ?? '';
  } else {
    out = String(input);
  }
  return interpolate(String(out), params);
}

/** 현재 언어를 getLang() 으로 읽는 t 를 만든다. 모듈은 ctx.t 로 받는다. */
export function createT(getLang) {
  return (input, params) => translate(getLang(), input, params);
}

/** store.lang 이 바뀔 때 <html lang> 을 맞춘다. 해제 함수 반환. */
export function bindDocumentLang(store, doc = globalThis.document) {
  const apply = (lang) => {
    if (doc && doc.documentElement) doc.documentElement.lang = normalizeLang(lang);
  };
  return store.select((s) => s.lang, apply, { fire: true });
}
