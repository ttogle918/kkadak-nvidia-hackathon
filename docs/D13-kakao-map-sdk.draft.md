# D13(초안) — 카카오맵 JS SDK 를 map 모듈의 선택 렌더러로 추가한다 (2026-10-07)
> D11 의 후속. D 번호는 사람이 정해 DECISIONS.md 에 합친다(팀원이 번호를 쓸 수 있음). 상태: 초안, 미승인.

- **결정**: map 모듈에 '렌더러 선택'을 둔다. 카카오 JavaScript 키가 있고 SDK 가 로드되면 카카오 렌더러, 아니면 기존 SVG 렌더러(D11)로 자동 폴백한다. SVG 렌더러는 그대로다.
- **키 보관**: `frontend/k-context/config.local.js`(gitignore)의 `window.KC_KAKAO_JS_KEY`. 레포에는 자리표시자 `config.local.example.js` 만 둔다. URL 파라미터로 키를 받지 않는다(히스토리·로그 노출). JavaScript 키는 브라우저에 노출되는 값이므로 **보안선은 비밀 유지가 아니라 콘솔의 JavaScript SDK 도메인 제한**이다. 지도 SDK 에 REST API 키는 쓰지 않는다. 콘솔 경고·로그에 키·URL 을 출력하지 않는다.
- **폴백**: 키 없음 / 스크립트 로드 실패 / `kakao` 전역 부재 / `kakao.maps.load` 오류 / 8초 타임아웃 → SVG, 콘솔 경고 한 줄(고정 문구).
- **외부 스크립트**: `https://dapi.kakao.com/v2/maps/sdk.js?appkey=<키>&autoload=false` 하나뿐. SDK 가 내부에서 타일·추가 리소스를 다른 호스트에서 받을 수 있다 [확인 필요]. 배포 시 CSP·허용 목록(OpenShell 정책 포함) 필요 여부·도메인 목록 [확인 필요].
- **렌더**: 마커·폴리라인은 `[lat,lng]`(계약 3.3). lat/lng 가 null 인 항목은 건너뛰고, 하나도 없으면 기본 중심(덕수궁 37.56556,126.97489 — 카카오맵 MCP 길찾기 링크 좌표, 2026-10-07)과 '좌표 없음' 표시. 텍스트는 textContent·Marker.title 로만 넣고 innerHTML 은 쓰지 않는다.
- **일정 앵커 마커(2026-10-07)**: `itinerary.anchors` 의 유효 lat/lng 를 마커로 추가한다(hotel 은 항상, visit 은 선택한 DAY 만, 카드 마커와 같은 자리는 중복 제외). 마커가 2개 이상이면 `setBounds` 로 한 화면에 담고, 1개면 중심만, 0개면 기본 중심 + '좌표 없음'. 좌표는 카카오맵 MCP 길찾기 응답 링크의 sp/ep 값(창덕궁·익선동·경복궁·광화문). 숙소는 실제 위치 데이터가 없어 종로3가역 1호선 좌표를 '대표 좌표(근사)'로 쓴다. 신촌은 대상 구 밖이라 null. 카드·경로(예시)에는 좌표를 붙이지 않는다(가짜 이야기).
- **mock 내 위치(2026-10-07)**: `getMyLocation()` 이 샘플 좌표 `MOCK_MY_LOCATION`(덕수궁 부근, 기본 중심과 같은 값)을 반환하고, 파란 점+반투명 원 CustomOverlay 로 '내 위치 (예시)' 라벨과 함께 항상 표시·fit bounds 포함한다. `navigator.geolocation` 은 쓰지 않는다. 실제 위치 전환은 이 함수만 교체.
- **대안**: OSM 타일 — 이용 정책 미확인(D11). 키 없이 SVG 만 — 실지도 부재.

## [확인 필요]
- `autoload=false` + `kakao.maps.load(cb)` 사용법: 공식 가이드 본문에서 확인하지 못했다(관례대로 구현, 어긋나면 폴백).
- 쿼터·약관: '개발자 계정 기준 첫 활성화 앱에만 무료 쿼터'라고만 들었고, 구체 수치와 출처 표기 조항은 문서에서 확인 못 함.
- 카카오 마커·InfoWindow API 세부(InfoWindow content 의 DOM 노드 허용 등)는 실제 SDK 로 확인 전.
- CSP·허용 목록(위).

## 사람 선행
1. 카카오 개발자 콘솔에서 앱 생성.
2. 카카오맵 사용 설정 ON.
3. 플랫폼 > Web > JavaScript SDK 도메인에 `http://localhost:8766` 등록(`http://127.0.0.1:8766` 은 별도 도메인 — 쓰려면 따로 등록).
4. `config.local.js` 에 JavaScript 키 입력.
