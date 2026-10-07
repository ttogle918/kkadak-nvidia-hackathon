// 케이스 작업 · 에이전트 콘솔 — 페이지 본문 마크업 (셸·사이드바는 layout/app-layout.js 가 감싼다)
export const view = `
    <section class="case-head" id="case-head" data-screen-label="케이스 헤더"></section>
    <div class="case-tabs" id="case-tabs" role="tablist"></div>
    <div class="case-body">
      <aside class="col col-ctx" id="col-ctx" data-pane="ctx" aria-label="입력과 맥락"></aside>
      <main class="col col-tl" id="col-tl" data-pane="progress" aria-label="에이전트 진행"></main>
      <aside class="col col-cc" id="col-cc" data-pane="concl" aria-label="결론과 초안"></aside>
    </div>
`;
export const outside = `<div class="ctx-bd" id="ctx-bd" data-act="ctx-close" hidden></div>`;
export const humanBar = true;
