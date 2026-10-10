// 배포 주소 설정(config.local.js 의 window.KC_API_BASE)과 세션 토큰 저장소 도우미.
// 설정값은 같은 출처 경로("/api") 또는 https: 절대 URL 만 받는다 — 그 밖은 버린다(사용자 입력이 아니라 배포 설정이지만 방어적으로 검증).

export const SESSION_KEY = 'kc.session';
export const SESSION_HEADER = 'X-KC-Session';
/** 서버가 발급하는 토큰 형식(43자 urlsafe). 틀린 형식은 "없음"으로 본다. */
export const TOKEN_RE = /^[A-Za-z0-9_-]{43}$/;

/** window.KC_API_BASE 를 검증해 정규화한 주소를 돌려준다. 없거나 허용 밖이면 undefined. */
export function configuredBase(win = globalThis) {
  const v = win?.KC_API_BASE;
  if (typeof v !== 'string' || !v) return undefined;
  if (/^\/(?!\/)[\w\-./]*$/.test(v)) return v.replace(/\/+$/, '') || undefined; // 같은 출처 경로
  try {
    const u = new URL(v);
    if (u.protocol !== 'https:' || u.username || u.password || u.search || u.hash || !u.hostname) return undefined;
    return `${u.origin}${u.pathname.replace(/\/+$/, '')}`;
  } catch {
    return undefined;
  }
}

function storage() {
  try {
    return globalThis.sessionStorage ?? null;
  } catch {
    return null;
  }
}

/** 저장된 세션 토큰. 저장소가 막혔거나 형식이 틀리면 null. 어떤 실패도 throw 하지 않는다. */
export function readSession() {
  try {
    const v = storage()?.getItem(SESSION_KEY);
    return typeof v === 'string' && TOKEN_RE.test(v) ? v : null;
  } catch {
    return null;
  }
}

/** 토큰 저장(token 이 null 이면 삭제). 실패해도 화면은 동작한다. */
export function writeSession(token) {
  try {
    const s = storage();
    if (!s) return;
    if (token == null) s.removeItem(SESSION_KEY);
    else s.setItem(SESSION_KEY, token);
  } catch { /* 저장소를 못 써도 메모리 토큰으로 계속 */ }
}
