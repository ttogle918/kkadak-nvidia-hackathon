// 승인 큐 · 에이전트 콘솔 — 페이지 본문 마크업 (셸·사이드바는 layout/app-layout.js 가 감싼다)
export const view = `
    <section class="ap-head" id="ap-head" data-screen-label="승인 큐 헤더"></section>
    <div class="ap-body">
      <aside class="ap-list" id="ap-list" aria-label="승인 대기 목록"></aside>
      <main class="ap-detail" id="ap-detail" aria-label="승인 상세"></main>
    </div>
`;
export const outside = ``;
export const humanBar = true;
