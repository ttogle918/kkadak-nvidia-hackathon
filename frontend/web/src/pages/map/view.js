// 대상 맵 · 에이전트 콘솔 — 페이지 본문 마크업 (셸·사이드바는 layout/app-layout.js 가 감싼다)
export const view = `
    <section class="mp-head" id="mp-head" data-screen-label="대상 맵 헤더"></section>
    <div class="mp-body">
      <section class="mp-map" id="mp-map" aria-label="설비 배치"></section>
      <aside class="mp-detail" id="mp-detail" aria-label="설비 상세"></aside>
    </div>
`;
export const outside = ``;
export const humanBar = false;
