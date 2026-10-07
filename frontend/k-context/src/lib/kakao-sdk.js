// 카카오맵 JS SDK 동적 로더. 외부 스크립트는 dapi.kakao.com 하나뿐이다. 키는 config.local.js(gitignore)에서만 온다.
// 경고 문구에는 키·URL 을 넣지 않는다(고정 문구만).
// [확인 필요] autoload=false + kakao.maps.load(cb) 사용법: 공식 가이드(https://apis.map.kakao.com/web/guide/) 본문에서
//   확인하지 못했다(WebFetch 없음, 2026-10-07). 관례적 사용법으로 구현했고, 어긋나면 타임아웃 → SVG 폴백으로 끝난다.

export const SDK_ORIGIN = 'https://dapi.kakao.com';
export const KEY_PLACEHOLDER = 'JAVASCRIPT_KEY_HERE';
export const LOAD_TIMEOUT_MS = 8000;

/** window.KC_KAKAO_JS_KEY 를 읽는다. 없거나 자리표시자면 null. */
export function readKey(win) {
  const k = win?.KC_KAKAO_JS_KEY;
  if (typeof k !== 'string') return null;
  const v = k.trim();
  return v && v !== KEY_PLACEHOLDER ? v : null;
}

export function sdkUrl(key) {
  return `${SDK_ORIGIN}/v2/maps/sdk.js?appkey=${encodeURIComponent(key)}&autoload=false`;
}

/**
 * SDK 를 불러 초기화한다. 항상 resolve(절대 reject 안 함).
 * @returns {Promise<{kakao:object}|{reason:string}>} reason 은 고정 문구(키 미포함)
 */
export function loadKakaoSdk({ win = globalThis.window, doc = globalThis.document, timeoutMs = LOAD_TIMEOUT_MS, setT = setTimeout, clearT = clearTimeout } = {}) {
  const key = readKey(win);
  if (!win || !doc) return Promise.resolve({ reason: '브라우저 환경이 아님' });
  if (!key) return Promise.resolve({ reason: '카카오 키 없음(config.local.js)' });
  return new Promise((resolve) => {
    let done = false;
    let timer = null;
    const finish = (r) => { if (done) return; done = true; clearT(timer); resolve(r); };
    timer = setT(() => finish({ reason: 'SDK 로드 시간 초과' }), timeoutMs);
    const ready = () => {
      const kk = win.kakao;
      if (!kk?.maps || typeof kk.maps.load !== 'function') { finish({ reason: 'kakao 전역 없음' }); return; }
      try { kk.maps.load(() => finish(win.kakao?.maps?.Map ? { kakao: win.kakao } : { reason: 'kakao.maps 초기화 실패' })); } catch { finish({ reason: 'kakao.maps.load 오류' }); }
    };
    try {
      const s = doc.createElement('script');
      s.src = sdkUrl(key);
      s.async = true;
      s.onload = ready;
      s.onerror = () => finish({ reason: 'SDK 스크립트 로드 실패(도메인 등록·네트워크 확인)' });
      (doc.head ?? doc.body ?? doc.documentElement).appendChild(s);
    } catch { finish({ reason: 'SDK 스크립트 삽입 실패' }); }
  });
}
