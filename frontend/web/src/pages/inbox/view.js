// 신호 인박스 · 에이전트 콘솔 — 페이지 본문 마크업 (셸·사이드바는 layout/app-layout.js 가 감싼다)
export const view = `
    <section class="ib-head" id="ib-head" data-screen-label="인박스 헤더"></section>
    <div class="ib-body">
      <aside class="ib-list" id="ib-list" aria-label="신호 목록"></aside>
      <main class="ib-detail" id="ib-detail" aria-label="신호 상세"></main>
    </div>
`;
export const outside = ``;
export const humanBar = true;
