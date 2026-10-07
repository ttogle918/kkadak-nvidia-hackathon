// 모든 페이지 공통 골격: 사이드바 · 탑바 · 네트워크 바 · (본문) · 사람 전용 바 · 하단 탭바 · 데모/모달/토스트 루트
export function mountLayout({ view, outside = "", humanBar = false }) {
  const bar = humanBar ? '    <div class="human-bar" id="human-bar" aria-label="사람 전용 결정 영역"></div>\n' : "";
  document.body.insertAdjacentHTML("beforeend", `
<div class="app">
  <nav class="sidebar" id="sidebar" aria-label="주 메뉴"></nav>
  <div class="main">
    <header class="topbar" id="topbar"></header>
    <div class="netbar" id="netbar" role="status" hidden></div>
${view}
${bar}  </div>
  <nav class="tabbar" id="tabbar" aria-label="하단 탭"></nav>
</div>
${outside}
<div class="demo" id="demo"></div>
<div id="modal-root"></div>
<div class="toast" id="toast" role="status" hidden></div>`);
}
