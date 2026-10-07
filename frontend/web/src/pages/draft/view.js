// 초안 검토 · 에이전트 콘솔 — 페이지 본문 마크업 (셸·사이드바는 layout/app-layout.js 가 감싼다)
export const view = `
    <section class="dh" id="dh" data-screen-label="초안 헤더"></section>
    <div class="dv">
      <main class="dv-col dv-doc" id="dv-doc" aria-label="초안 문서"></main>
      <aside class="dv-col dv-src" id="dv-src" aria-label="근거 원문"></aside>
    </div>
`;
export const outside = ``;
export const humanBar = true;
