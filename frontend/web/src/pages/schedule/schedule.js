// 일정·배치 · 에이전트 콘솔 — 페이지 로직
import { injectSprite } from "../../components/icons/sprite.js";
import { mountLayout } from "../../components/layout/app-layout.js";
import { renderDemo } from "../../components/layout/demo-panel.js";
import { renderShell } from "../../components/layout/shell.js";
import { closeModal } from "../../components/modals/modal.js";
import { toast } from "../../components/toast.js";
import { bindActs } from "../../lib/acts.js";
import { $, esc, ic, pv } from "../../lib/dom.js";
import { APP, DATA, LABELS, readURL } from "../../lib/state.js";
import { initTheme } from "../../lib/theme.js";
import "../../data/schedule.js";
import { view, outside, humanBar } from "./view.js";
import { openReasonModal } from "../../components/modals/reason-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: schedule ================= */
const UI = { done: null };
const sk = (h, w) => '<div class="sk" style="height:' + h + 'px;width:' + (w || "100%") + '"></div>';
const D = DATA.day, SPAN = D.to - D.from;
const blocked = () => APP.state === "empty" || APP.state === "loading" || APP.state === "error";
const fmt = h => String(Math.floor(h)).padStart(2, "0") + ":" + (h % 1 ? "30" : "00");
const confirmed = () => UI.done === "ok" || APP.state === "approved";
function pct(a, b) { return 'left:' + ((a - D.from) / SPAN * 100) + '%;width:' + ((b - a) / SPAN * 100) + '%'; }
function renderHead() {
  const s = APP.state;
  const alert = s === "blocked" ? '<div class="alert alert-blocked" role="alert">' + ic("ban") + '<div><b>배치 충돌 1건 차단</b><p>M-0455 교대 종료(16:00) 이후로 배치하려는 안을 정책이 막았습니다. 근무 연장은 사람이 결정합니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>'
    : s === "error" ? '<div class="alert alert-error" role="alert">' + ic("alert") + '<div><b>근태 연동 중단 · ' + esc(DATA.error.code) + '</b><p>' + esc(DATA.error.message) + '. 마지막 동기화 ' + DATA.shell.lastSync + ' 기준으로 표시합니다.</p></div></div>' : "";
  $("#sc-head").innerHTML = '<h1>' + esc(LABELS.nav.schedule) + '</h1><p>' + (blocked() && s !== "error" ? "" : D.label + " · 에이전트가 만든 배치안은 초안입니다. 확정은 사람이 합니다.") + '</p>' + alert;
}
function renderBoard() {
  const s = APP.state, el = $("#sc-board");
  if (s === "loading") { el.innerHTML = sk(120) + sk(120) + sk(120); return; }
  if (s === "empty") { el.innerHTML = '<div class="empty"><span class="empty-ic">' + ic("schedule") + '</span><h3>배치할 작업이 없습니다</h3><p>케이스에서 조치 계획이 승인되면 작업이 여기에 들어옵니다.</p></div>'; return; }
  const ok = confirmed(), axis = [];
  for (let h = D.from; h <= D.to; h += 2) axis.push('<span>' + String(h).padStart(2, "0") + '</span>');
  el.innerHTML = DATA.people.map(p => '<div class="pp"><div class="pp-h"><b>' + esc(p.role) + '</b><small>' + p.id + '</small><span class="shift">근무 ' + p.shift + '</span></div>' +
    '<div class="axis">' + axis.join("") + '</div><div class="track" role="img" aria-label="' + esc(p.role) + ' 시간대별 배치">' +
    p.fixed.map(f => '<span class="seg-b fix" style="' + pct(f[0], f[1]) + '"></span>').join("") +
    p.plan.map(f => '<span class="seg-b" style="' + pct(f[0], f[1]) + (ok ? ";background:var(--pv-ap-bd)" : "") + '"></span>').join("") + '</div>' +
    p.fixed.map(f => '<div class="tk"><span class="tm">' + fmt(f[0]) + '–' + fmt(f[1]) + '</span><span class="nm">' + esc(f[2]) + '</span>' + pv("approved", "확정", "sm") + '</div>').join("") +
    p.plan.map(f => '<div class="tk"><span class="tm">' + fmt(f[0]) + '–' + fmt(f[1]) + '</span><span class="nm">' + esc(f[2]) + '</span>' + (ok ? pv("approved", DATA.shell.user.id + " · 14:05", "sm") : (s === "running" ? '<span class="spin"></span>' : pv("draft", null, "sm"))) + '</div>').join("") + '</div>').join("");
}
function renderSide() {
  const s = APP.state, el = $("#sc-side");
  if (s === "loading") { el.innerHTML = sk(36, "60%") + sk(120) + sk(100); return; }
  if (blocked() && s !== "error") { el.innerHTML = '<div class="empty"><span class="empty-ic">' + ic("search") + '</span><h3>배치 제안이 없습니다</h3><p>작업이 들어오면 에이전트가 제안을 만듭니다.</p></div>'; return; }
  const c = DATA.cite, ok = confirmed();
  el.innerHTML = '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><span class="sg-id mono">DRF-0150</span>' + (ok ? pv("approved", DATA.shell.user.id + " · 14:05", "sm") : pv("draft", null, "sm")) + '</div>' +
    '<h2 class="det-title">B조 작업 4건 배치안</h2>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">배치 근거</div><ul class="why">' + DATA.why.map(t => '<li>' + ic("check") + '<span>' + esc(t) + '</span></li>').join("") + '</ul></section>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">작업 ' + DATA.tasks.length + '</div>' + DATA.tasks.map(t => '<div class="tk"><span class="tm">' + t.at + '</span><span class="nm">' + esc(t.name) + '</span><span class="mono" style="color:var(--tx-2)">' + t.who + '</span></div>').join("") + '</section>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">근거 1</div><div class="cites"><div class="cite"><div class="cite-top"><b>' + esc(c.doc) + '</b><span class="cite-loc mono">' + esc(c.loc) + '</span></div><blockquote class="cite-q">“<mark>' + esc(c.quote) + '</mark>”</blockquote><div class="cite-foot">' + pv("approved", "승격 문서", "sm") + '<a class="cite-link" href="draft.html">원문 위치 ' + ic("ext") + '</a></div></div></div></section>';
}
function renderBar() {
  const s = APP.state, bar = $("#human-bar");
  const tag = '<span class="human-tag">' + ic("user") + esc(LABELS.humanOnly) + '</span>';
  if (blocked() && s !== "error") { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">확정할 배치안이 없습니다.</span></div>'; return; }
  if (confirmed()) { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">배치 확정됨 · 담당자에게 작업지시가 전달됩니다</span></div><div class="hb-actions">' + pv("approved", DATA.shell.user.id + " · 14:05", "lg") + '<a class="btn" href="audit.html">' + ic("audit") + '감사 기록</a></div>'; return; }
  if (UI.done === "no") { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">반려됨 · 사유가 에이전트에 전달되어 재배치합니다</span></div><div class="hb-actions"><button class="btn" data-act="undo">' + ic("retry") + '되돌리기</button></div>'; return; }
  const dis = s === "loading" || s === "error" || s === "running" ? " disabled" : "";
  bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">작업 4건과 담당자를 확인하고 배치를 확정합니다.</span></div><div class="hb-actions"><button class="btn btn-danger" data-act="reject"' + dis + '>' + ic("x") + '반려</button><button class="btn btn-primary" data-act="confirm"' + dis + '>' + ic("check") + '<span class="lbl-long">배치 확정</span><span class="lbl-short">확정</span></button></div>';
}
function renderPage() { renderHead(); renderBoard(); renderSide(); renderBar(); }
const PAGE_ACTS = {
  confirm: () => { UI.done = "ok"; renderPage(); toast("배치 확정 · 작업지시를 전달했습니다", "user-check"); },
  undo: () => { UI.done = null; renderPage(); },
  reject: () => openReasonModal({ title: "배치안 반려", hint: "반려 사유는 에이전트에 전달되어 재배치에 쓰입니다.", act: "reject-ok", label: "반려" }),
  "reject-ok": () => { UI.done = "no"; closeModal(); renderPage(); toast("배치안 반려 · 감사 기록에 남았습니다", "x"); }
};

initTheme(); readURL();
renderShell([LABELS.nav.schedule]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
