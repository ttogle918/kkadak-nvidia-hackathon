// 대상 맵 · 에이전트 콘솔 — 페이지 로직
import { injectSprite } from "../../components/icons/sprite.js";
import { mountLayout } from "../../components/layout/app-layout.js";
import { renderDemo } from "../../components/layout/demo-panel.js";
import { renderShell } from "../../components/layout/shell.js";
import { bindActs } from "../../lib/acts.js";
import { $, esc, ic, pv } from "../../lib/dom.js";
import { APP, DATA, LABELS, readURL } from "../../lib/state.js";
import { initTheme } from "../../lib/theme.js";
import "../../data/map.js";
import { view, outside, humanBar } from "./view.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: map ================= */
const UI = { sel: "INV-C3", filter: "all", detail: false };
const sk = (h, w) => '<div class="sk" style="height:' + h + 'px;width:' + (w || "100%") + '"></div>';
const FILTERS = { all: "전체", issue: "이상·주의", noev: "근거 없음" };
const isIssue = e => e.st !== "ok";
function show(id) { const e = DATA.eq[id]; return UI.filter === "all" || (UI.filter === "issue" && isIssue(e)) || (UI.filter === "noev" && (e.prov === "noev" || !e.man || e.man[1] !== "promoted")); }
function blocked() { return APP.state === "empty" || APP.state === "loading" || APP.state === "error"; }
function cur() { return blocked() ? null : DATA.eq[UI.sel] ? UI.sel : "INV-C3"; }
function renderHead() {
  const s = APP.state, n = Object.values(DATA.eq).filter(isIssue).length;
  const alert = s === "blocked" ? '<div class="alert alert-blocked" role="alert">' + ic("ban") + '<div><b>INV-C3 주변 신호 격리 1건</b><p>현장 메모 사진의 지시문은 판단에서 제외했습니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>'
    : s === "error" ? '<div class="alert alert-error" role="alert">' + ic("alert") + '<div><b>설비 마스터 중단 · ' + esc(DATA.error.code) + '</b><p>' + esc(DATA.error.message) + '.</p></div></div>' : "";
  $("#mp-head").innerHTML = '<h1>' + esc(LABELS.nav.map) + '</h1><p>' + (blocked() ? "" : "설비 6대 · 이상·주의 " + n + "대. 상태는 신호와 승격된 문서에서만 계산합니다.") + '</p>' +
    '<div class="chips" role="tablist">' + Object.entries(FILTERS).map(([k, l]) => '<button class="chip" role="tab" data-act="filter" data-v="' + k + '" aria-selected="' + (UI.filter === k) + '" style="' + (UI.filter === k ? "background:var(--ink);color:var(--on-ink);border-color:var(--ink)" : "") + '">' + l + '</button>').join("") + '</div>' + alert;
}
function renderMap() {
  const s = APP.state, el = $("#mp-map");
  if (s === "loading") { el.innerHTML = sk(110) + sk(110); return; }
  if (blocked()) { el.innerHTML = '<div class="empty"><span class="empty-ic">' + ic("map") + '</span><h3>' + (s === "empty" ? "등록된 설비가 없습니다" : "설비를 불러오지 못했습니다") + '</h3><p>' + (s === "error" ? "연결이 복구되면 자동으로 다시 받습니다." : "설비를 등록하면 라인별 배치가 표시됩니다.") + '</p></div>'; return; }
  const c = cur(); let any = false;
  const html = DATA.lines.map(l => {
    const ids = l.eq.filter(show); if (!ids.length) return ""; any = true;
    return '<div class="ln"><div class="ln-h">' + esc(l.name) + '<small>' + l.id + '</small></div><div class="ln-row">' + ids.map(id => {
      const e = DATA.eq[id], run = s === "running" && id === "INV-C3";
      return '<button class="eq" data-act="sel" data-id="' + id + '" aria-current="' + (c === id) + '"><div class="eq-top"><span class="eq-id">' + id + '</span></div><div class="eq-n">' + esc(e.name) + '</div>' +
        '<div class="eq-top">' + (run ? '<span class="spin"></span><b style="font-size:var(--fs-sm)">에이전트 진단 중</b>' : '<span class="eq-st ' + e.st + '"><i></i>' + esc(e.stl) + '</span>') + '</div></button>';
    }).join("") + '</div></div>';
  }).join("");
  el.innerHTML = any ? html : '<div class="empty"><span class="empty-ic">' + ic("search") + '</span><h3>조건에 맞는 설비가 없습니다</h3><p>필터를 바꿔 보세요.</p></div>';
}
function renderDetail() {
  const s = APP.state, el = $("#mp-detail");
  el.classList.toggle("open", UI.detail && !blocked());
  const back = '<button class="btn btn-sm det-back" data-act="back">' + ic("chev") + '목록</button>';
  if (s === "loading") { el.innerHTML = sk(36, "60%") + sk(120) + sk(160); return; }
  const id = cur();
  if (!id) { el.innerHTML = back + '<div class="empty"><span class="empty-ic">' + ic("search") + '</span><h3>선택한 설비가 없습니다</h3><p>설비를 고르면 연결된 신호와 문서를 볼 수 있습니다.</p></div>'; return; }
  const e = DATA.eq[id];
  const man = e.man ? '<li><b>' + esc(e.man[0]) + '</b>' + (e.man[1] === "promoted" ? pv("approved", "승격됨", "sm") : pv("untrusted", "승격 대기", "sm")) + '<a class="cite-link" href="knowledge.html">지식 온보딩 ' + ic("ext") + '</a></li>' : '<li><b>연결된 문서 없음</b>' + pv("noev", "근거 없음", "sm") + '</li>';
  el.innerHTML = back +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><span class="eq-id">' + id + '</span><span class="eq-st ' + e.st + '"><i></i>' + esc(e.stl) + '</span></div>' +
    '<h2 class="det-title">' + esc(e.name) + '</h2>' +
    '<dl class="kvs"><dt>모델</dt><dd class="mono">' + esc(e.model) + '</dd><dt>위치</dt><dd>' + esc(e.pos) + '</dd><dt>상태 출처</dt><dd>' + pv(e.prov, null, "sm") + '</dd></dl>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">연결된 신호 ' + e.sig.length + '</div><ul class="rel">' + e.sig.map(x => '<li><b class="mono">' + x[0] + '</b>' + esc(x[1]) + '<a class="cite-link" href="inbox.html">인박스에서 보기 ' + ic("ext") + '</a></li>').join("") + '</ul></section>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">연결된 문서</div><ul class="rel">' + man + '</ul></section>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">정비 이력</div>' + (e.hist.length ? '<ul class="rel">' + e.hist.map(h => '<li><b class="mono">' + h[0] + '</b>' + esc(h[1]) + '</li>').join("") + '</ul>' : '<p style="color:var(--tx-2);font-weight:500;font-size:var(--fs-sm)">등록된 이력이 없습니다.</p>') + '</section>' +
    (e.caseId ? '<a class="btn btn-primary" style="align-self:flex-start" href="case.html">' + ic("case") + '열린 케이스 ' + esc(e.caseId) + '</a>' : "");
}
function renderPage() { renderHead(); renderMap(); renderDetail(); }
const PAGE_ACTS = {
  filter: el => { UI.filter = el.dataset.v; renderPage(); },
  sel: el => { UI.sel = el.dataset.id; UI.detail = true; renderPage(); },
  back: () => { UI.detail = false; renderDetail(); }
};

initTheme(); readURL();
renderShell([LABELS.nav.map]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
