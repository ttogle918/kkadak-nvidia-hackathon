// 현장 모바일 · 에이전트 콘솔 — 페이지 본문 마크업 (셸·사이드바는 layout/app-layout.js 가 감싼다)
export const view = `
    <section class="fd-head" id="fd-head" data-screen-label="현장 헤더"></section>
    <main class="fd-body"><div class="fd-col" id="fd-col"></div></main>
`;
export const outside = `<input type="file" id="photo-in" accept="image/*" capture="environment" hidden>`;
export const humanBar = true;
