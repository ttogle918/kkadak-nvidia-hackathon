// 복사해서 config.local.js 로 저장하고 값을 채운다 (config.local.js 는 gitignore — 커밋 금지).
//   cp config.local.example.js config.local.js
// 카카오 개발자 콘솔의 "JavaScript 키"만 넣는다. REST API 키는 지도 SDK 에 쓰지 않는다(넣지 말 것).
// 보안선은 키 비밀이 아니라 콘솔의 "JavaScript SDK 도메인" 등록이다 (예: http://localhost:8766).
window.KC_KAKAO_JS_KEY = 'JAVASCRIPT_KEY_HERE';
// 배포 API 주소(선택). 같은 출처 경로("/api") 또는 https:// 절대 URL 만 받는다. 비우면 로컬 기본값(:8000 또는 /api).
// 배포 시에는 T424 가 dist/ 쪽에서 값을 채운다 — 로컬에서는 쓰지 않는다.
// window.KC_API_BASE = 'https://example.invalid/api';
