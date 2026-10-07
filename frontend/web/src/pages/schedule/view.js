// 일정·배치 · 에이전트 콘솔 — 페이지 본문 마크업 (셸·사이드바는 layout/app-layout.js 가 감싼다)
export const view = `
    <section class="sc-head" id="sc-head" data-screen-label="일정·배치 헤더"></section>
    <div class="sc-body">
      <section class="sc-board" id="sc-board" aria-label="오늘 배치"></section>
      <aside class="sc-side" id="sc-side" aria-label="배치 제안"></aside>
    </div>
`;
export const outside = ``;
export const humanBar = true;
