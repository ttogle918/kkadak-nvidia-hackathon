// 지도 렌더러 선택: 카카오 키가 있고 SDK 가 로드되면 'kakao', 아니면 기존 SVG('svg')로 자동 폴백.
// 폴백 사유는 콘솔 경고 한 줄(키 값 없음). 결과는 한 번만 계산해 공유한다.
import { loadKakaoSdk } from '../../lib/kakao-sdk.js';

let memo = null;

/** @returns {Promise<{kind:'kakao', kakao:object}|{kind:'svg', reason:string}>} */
export function selectRenderer(opts = {}) {
  const warn = opts.warn ?? ((m) => console.warn(m));
  const win = opts.win ?? globalThis.window;
  if (!win) return Promise.resolve({ kind: 'svg', reason: '브라우저 환경이 아님' }); // node: 조용히 SVG
  return loadKakaoSdk({ ...opts, win }).then((r) => {
    if (r.kakao) return { kind: 'kakao', kakao: r.kakao };
    warn(`[map] 카카오맵 대신 SVG 지도 사용: ${r.reason}`);
    return { kind: 'svg', reason: r.reason };
  });
}

/** 앱 전체에서 한 번만 선택(재마운트해도 SDK 를 다시 넣지 않는다). */
export function sharedRenderer() {
  memo ??= selectRenderer();
  return memo;
}
export function resetSharedRenderer() { memo = null; } // 테스트용
