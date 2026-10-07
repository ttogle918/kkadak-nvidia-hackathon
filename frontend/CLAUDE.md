# 에이전트 AI 해커톤 UI 키트 — 작업 규칙

완성: index.html, case.html, draft.html. 남은 페이지: inbox, approvals, knowledge, map, security, audit, schedule, field.

## 파일 형식 (사용자 지정, DC 아님)
- 페이지마다 자체 완결 `.html` 1개. CSS/JS 인라인, 외부 CDN·웹폰트·원격 이미지 금지. 시스템 폰트, 인라인 SVG 아이콘.
- `write_file`로 작성. Design Component(.dc.html) 쓰지 않는다.

## 공통 블록 (글자 그대로 동일해야 함)
case.html에서 그대로 복사한다. 손으로 다시 쓰지 말 것.
1. CSS: `/* ================= COMMON v1` ~ `/* ================= /COMMON v1 ================= */`
2. 아이콘 스프라이트: `<svg width="0" height="0"` ~ `</symbol>\n</svg>`
3. JS: `/* ================= COMMON JS v1` ~ `/* ================= /COMMON JS v1 ================= */`
작성법: 새 페이지를 `/*@@COMMON_CSS@@*/`, `<!--@@SPRITE@@-->`, `/*@@COMMON_JS@@*/` 자리표시자로 쓰고 run_script로 case.html에서 잘라 넣는다. 공통을 바꿀 땐 case.html을 고친 뒤 모든 파일에 동기화하고 동일성 검사.
- 새 아이콘이 필요하면 case.html 스프라이트에 추가 후 전 파일 동기화.

## 페이지 골격
- `<body data-page="KEY">` (KEY는 COMMON JS의 HREF 키: home, inbox, case, draft, approvals, knowledge, map, schedule, security, audit, field)
- 셸 요소: `#sidebar`, `.main > #topbar, #netbar, (페이지 본문), #human-bar(사람 결정이 있는 페이지만)`, `#tabbar`, `#demo`, `#modal-root`, `#toast`
- script 순서: `const DATA = {...}` (맨 위, shell/chat 포함) → `const LABELS = {...}` (공통 키 nav, navShort, navGroups, prov, provDesc, demo, humanOnly, app 필수) → COMMON JS → 페이지 JS
- 페이지 JS: `renderPage()` 정의(APP.state 읽어 렌더), `PAGE_ACTS` 객체(data-act 핸들러), 끝에 `initTheme(); readURL(); renderShell([...crumbs]); renderDemo(); bindActs(PAGE_ACTS); renderPage();`
- `DATA.chat = { ctx, suggestions[4], replies[{match[], tools[[name,dur]], text, cites[], kind?:"refuse", link?:[href,label]}] }` — 챗봇(오른쪽 하단 FAB)은 공통 JS가 자동 생성. 마지막 제안은 "~승인해줘"로 두어 사람 전용 차단 응답을 보여준다.
- 페이지 CSS는 `/* ================= PAGE: KEY ================= */` 아래. 열 컨테이너 자식은 `flex-shrink:0`.

## 상태 (모든 페이지)
APP.state: normal / running / blocked / approved / empty / loading / error (+ rejected). `?state=`, `?net=offline`, `?theme=light` 지원. 데모 패널은 공통.

## 디자인 규칙
- 출처 상태 6종은 `pv(type, extra, "sm"|"lg")` 배지와 `.pvbox-*` 박스로만 표시: untrusted(회색 점선+빗금), draft(청록 점선), approved(초록 #76b900 실선, 승인자·시각 필수), blocked(빨강 실선), noev(보라 도트), sensor(노랑 점선+빗금).
- 강조색 #ff1f4b(빨강): 주요 버튼(승인 포함), 로고, 현재 메뉴. 긍정/승인 상태는 초록 #76b900. 색 늘리지 말 것.
- 사람 전용 영역: `.human-bar` + `.human-tag`(흑백 반전). 고위험 승인 = `.reauth` 재로그인 표시 + PIN 모달.
- 에이전트 주장엔 `.cite`(문서·위치·원문 인용). 중간 과정(계획/도구 호출/실패/재시도/차단)을 보여준다.
- 큰 글자(본문 16px, 배지 13px 이상, 제목 28–30px), 터치 48px 이상, hover 의존 금지, 이모지 금지.
- 반응형: 데스크톱 >1024 사이드바 / 600–1024 아이콘 레일 / <600 하단 탭바. 표는 폰에서 카드 목록. 본문 가로 스크롤 금지(YAML·로그는 자기 컨테이너에서만 스크롤). 폰의 필터는 하단 시트(openModal).
- 샘플 도메인: 산업 설비 보전(2공장, INV-C3 VFD-22, F0003, 영문 매뉴얼). 실제 회사명·인명 금지(역할+사번 사용: 정비반장 M-0412).
- 작성 후 ready_for_verification으로 확인.
