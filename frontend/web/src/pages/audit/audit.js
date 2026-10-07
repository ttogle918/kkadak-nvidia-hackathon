// 감사 기록 · 에이전트 콘솔 — 페이지 로직
import { injectSprite } from "../../components/icons/sprite.js";
import { mountLayout } from "../../components/layout/app-layout.js";
import { renderDemo } from "../../components/layout/demo-panel.js";
import { renderShell } from "../../components/layout/shell.js";
import { bindActs } from "../../lib/acts.js";
import { $, esc, ic, pv } from "../../lib/dom.js";
import { APP, DATA, LABELS, readURL } from "../../lib/state.js";
import { initTheme } from "../../lib/theme.js";
import "../../data/audit.js";
import { view, outside, humanBar } from "./view.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: audit ================= */
const UI = { sel: "EV-0407", filter: new URLSearchParams(location.search).get("filter") || "all", detail: false };
if (!["all", "blocked", "decision", "agent"].includes(UI.filter)) UI.filter = "all";
const sk = (h, w) => '<div class="sk" style="height:' + h + 'px;width:' + (w || "100%") + '"></div>';
const FILTERS = { all: "전체", blocked: "차단", decision: "사람 결정", agent: "에이전트 활동" };
const RES = { approved: ["hum", "user-check", "사람 승인"], rejected: ["no", "x", "반려"], allow: ["ok", "check", "허용"], blocked: ["no", "ban", "차단"] };
const blocked = () => APP.state === "empty" || APP.state === "loading" || APP.state === "error";
function visible() { return blocked() ? [] : DATA.events.filter(e => UI.filter === "all" || e.kind === UI.filter); }
function cur() { return visible().find(x => x.id === UI.sel) || visible()[0]; }
const resTag = r => '<span class="res ' + RES[r][0] + '">' + ic(RES[r][1]) + RES[r][2] + '</span>';
function renderHead() {
  const s = APP.state;
  const alert = s === "blocked" ? '<div class="alert alert-blocked" role="alert">' + ic("ban") + '<div><b>오늘 차단 4건</b><p>모두 에이전트의 호출이나 문서 속 지시문에서 시작됐고 실행되지 않았습니다.</p></div></div>'
    : s === "error" ? '<div class="alert alert-error" role="alert">' + ic("alert") + '<div><b>감사 저장소 중단 · ' + esc(DATA.error.code) + '</b><p>' + esc(DATA.error.message) + '. 이 동안의 행동은 로컬에 임시 기록 후 복구 시 반영됩니다.</p></div></div>' : "";
  $("#au-head").innerHTML = '<h1>' + esc(LABELS.nav.audit) + '</h1><p>' + (blocked() ? "" : "추가만 가능한 기록입니다. 수정이나 삭제 권한은 누구에게도 없습니다.") + '</p>' +
    '<div class="chips" role="tablist">' + Object.entries(FILTERS).map(([k, l]) => '<button class="chip" role="tab" data-act="filter" data-v="' + k + '" aria-selected="' + (UI.filter === k) + '" style="' + (UI.filter === k ? "background:var(--ink);color:var(--on-ink);border-color:var(--ink)" : "") + '">' + l + '</button>').join("") + '</div>' + alert;
}
function renderList() {
  const s = APP.state, el = $("#au-list");
  if (s === "loading") { el.innerHTML = sk(60) + sk(60) + sk(60) + sk(60) + sk(60); return; }
  const L = visible();
  if (!L.length) { el.innerHTML = '<div class="empty"><span class="empty-ic">' + ic("audit") + '</span><h3>' + (s === "empty" ? "기록이 없습니다" : s === "error" ? "기록을 불러오지 못했습니다" : "조건에 맞는 기록이 없습니다") + '</h3><p>' + (s === "error" ? "연결이 복구되면 자동으로 다시 받습니다." : "행동이 발생하면 시각과 행위자와 함께 기록됩니다.") + '</p></div>'; return; }
  const c = cur();
  el.innerHTML = '<div class="ev-h" aria-hidden="true"><span>시각</span><span>행위자</span><span>행동</span><span>결과</span></div>' + L.map(e => '<button class="ev" data-act="sel" data-id="' + e.id + '" aria-current="' + (c && c.id === e.id) + '"><span class="tm">' + e.t.slice(0, 5) + '</span><span class="who">' + ic(e.who === "사람" ? "user" : e.who === "에이전트" ? "bot" : "cpu") + esc(e.who) + ' <span class="mono" style="font-weight:600;color:var(--tx-2)">' + esc(e.whoId) + '</span></span><span class="act">' + esc(e.act) + '<small>' + esc(e.obj) + '</small></span>' + resTag(e.res) + '</button>').join("");
}
function renderDetail() {
  const s = APP.state, el = $("#au-detail");
  el.classList.toggle("open", UI.detail && !blocked());
  const back = '<button class="btn btn-sm det-back" data-act="back">' + ic("chev") + '목록</button>';
  if (s === "loading") { el.innerHTML = sk(36, "60%") + sk(120) + sk(160); return; }
  const e = cur();
  if (!e) { el.innerHTML = back + '<div class="empty"><span class="empty-ic">' + ic("search") + '</span><h3>선택한 기록이 없습니다</h3><p>기록을 고르면 원본 레코드를 볼 수 있습니다.</p></div>'; return; }
  el.innerHTML = back +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><span class="mono" style="font-weight:800;color:var(--tx-2)">' + e.id + '</span>' + resTag(e.res) + (e.kind === "blocked" ? pv("blocked", null, "sm") : "") + '</div>' +
    '<h2 class="det-title">' + esc(e.act) + '</h2>' +
    '<dl class="dl"><dt>시각</dt><dd class="mono">2026-10-03 ' + e.t + '</dd><dt>행위자</dt><dd>' + esc(e.who) + ' · <span class="mono">' + esc(e.whoId) + '</span></dd><dt>대상</dt><dd>' + esc(e.obj) + '</dd><dt>비고</dt><dd>' + esc(e.note) + '</dd></dl>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">원본 레코드</div><pre class="rec mono">' + esc(e.rec) + '</pre></section>' +
    (e.kind === "blocked" ? '<a class="btn btn-sm" style="align-self:flex-start" href="security.html">' + ic("security") + '관련 정책 보기</a>' : "");
}
function renderPage() { renderHead(); renderList(); renderDetail(); }
const PAGE_ACTS = {
  filter: el => { UI.filter = el.dataset.v; renderPage(); },
  sel: el => { UI.sel = el.dataset.id; UI.detail = true; renderPage(); },
  back: () => { UI.detail = false; renderDetail(); }
};

initTheme(); readURL();
renderShell([LABELS.nav.audit]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
