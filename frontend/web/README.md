# web/ — 모듈화한 프론트엔드

`frontend/*.html`(페이지마다 자체 완결 1파일)을 CSS · 컴포넌트 · 페이지 로직으로 나눈 것이다.
프레임워크·번들러 없이 **네이티브 ES 모듈**로 돌아간다. 원본 `frontend/*.html` 은 그대로 남겨 두었다(비교 기준).

## 실행
ES 모듈은 `file://` 로 열면 막힌다. 정적 서버로 연다.

```bash
cd frontend/web && python3 -m http.server 8765    # http://127.0.0.1:8765/case.html?state=blocked
```

`?state=normal|running|blocked|approved|rejected|empty|loading|error`, `?net=offline`, `?theme=light` 는 원본과 같다.

## 구조
```
web/
  <page>.html            진입점. 제목 + CSS 2개 + 모듈 스크립트 1개뿐 (index.html 은 data-page="home")
  src/
    styles/
      common.css         @import 목록 — 순서가 곧 캐스케이드 순서
      common/*.css       토큰 · 레이아웃 · 버튼 · 출처 배지 · 사람 전용 바 · 모달 · 반응형 · 챗 …
      pages/<page>.css   페이지 전용 스타일
    lib/
      state.js           APP · DATA · LABELS · NAV/HREF · setState/readURL/writeURL
      dom.js             $ · esc · ic · pv (출처 배지)
      theme.js · acts.js 테마 / data-act 클릭 위임(공통 + 챗 + 페이지 액션)
    components/
      layout/            app-layout(골격) · shell(사이드바·탑바·탭바) · demo-panel
      modals/            modal(바탕) · modal-head · legend · more · pin · reason · revise
      chat/chat.js       플로팅 어시스턴트
      icons/sprite.js    SVG 스프라이트 (아이콘 추가는 여기)
      toast.js
    data/<page>.js       샘플 DATA · LABELS  (나중에 API 응답으로 바꿀 자리)
    pages/<page>/
      <page>.js          페이지 로직(renderPage · PAGE_ACTS · 초기화)
      view.js            페이지 본문 마크업
      code-modal.js …    그 페이지에서만 쓰는 모달 (지금은 field 만)
```

## 규칙
- 공통 모달은 `components/modals/` 에 두고 **문구·데이터는 인자로** 받는다. 페이지는 호출만 한다.
  - `openPinModal` 재인증 / `openReasonModal` 사유 입력 / `openReviseModal` 수정 요청
  - 확인 버튼의 `data-act`(예: `approve-ok`)와 입력 id(`pin`, `why`, `reason`, `revise`)는 페이지 `PAGE_ACTS` 가 읽는다.
- 한 페이지에서만 쓰는 모달은 `pages/<page>/` 안에 둔다. 두 페이지 이상이 쓰게 되면 `components/modals/` 로 올린다.
- 모달이 닫힐 때 페이지 상태를 비워야 하면 `onModalClose(fn)` 을 쓴다 (`closeModal` 을 덮어쓰지 말 것 — 모듈 import 는 재할당 불가).
- 페이지 모듈은 import 직후 `mountLayout()` 을 부른다. 그 뒤에야 `$("#...")` 를 쓸 수 있다.
- 색·출처 상태 6종·상태 7종 같은 디자인 규칙은 `frontend/CLAUDE.md` 의 "디자인 규칙" 이 그대로 적용된다.
  (그 문서의 "파일 형식 · 공통 블록 복사" 절은 이 구조에서는 해당 없음 — 공통은 `lib/`·`components/`·`styles/common/` 한 곳에 있다.)

## 기술 스택을 정하면
컴포넌트가 `(인자) => HTML 문자열` 함수라 React/Vue/Svelte 로 옮기기 쉽다: `components/modals/*` → 모달 컴포넌트,
`data/*` → API/목 데이터, `pages/*/view.js` → 페이지 템플릿, `styles/` → 그대로 CSS(또는 CSS Modules).
