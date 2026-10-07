// 승인 큐 · 에이전트 콘솔 — 페이지 로직
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
import "../../data/approvals.js";
import { view, outside, humanBar } from "./view.js";
import { openPinModal } from "../../components/modals/pin-modal.js";
import { openReasonModal } from "../../components/modals/reason-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: approvals ================= */
const UI = { sel: "DRF-0141", filter: "all", detail: false, done: {} };
const sk = (h, w) => '<div class="sk" style="height:' + h + 'px;width:' + (w || "100%") + '"></div>';
const FILTERS = { all: "전체", high: "고위험", low: "일반", done: "처리됨" };
const NOW = "14:05";
function status(g) { return UI.done[g.id] ? UI.done[g.id].v : (APP.state === "approved" ? "approved" : "pending"); }
function visible() {
  const s = APP.state; if (s === "empty" || s === "loading" || s === "error") return [];
  return DATA.items.filter(g => ({ all: 1, high: g.risk === "HIGH", low: g.risk !== "HIGH", done: status(g) !== "pending" })[UI.filter]);
}
function cur() { return visible().find(x => x.id === UI.sel) || visible()[0]; }
function stPv(g) {
  const st = status(g);
  if (st === "approved") return pv("approved", DATA.shell.user.id + " · " + NOW, "sm");
  if (st === "rejected") return '<span class="pv pv-blocked pv-sm">' + ic("x") + '<span class="pv-l">반려</span><span class="pv-x">' + DATA.shell.user.id + '</span></span>';
  return pv("draft", null, "sm");
}
function renderHead() {
  const s = APP.state, n = DATA.items.filter(g => status(g) === "pending").length;
  const alert = s === "blocked" ? '<div class="alert alert-blocked" role="alert">' + ic("ban") + '<div><b>에이전트 승인 시도 차단 1건</b><p>채팅에서 발주서 승인 요청이 들어왔지만 승인은 사람 전용입니다. 감사 기록에 남겼습니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>'
    : s === "error" ? '<div class="alert alert-error" role="alert">' + ic("alert") + '<div><b>승인 큐 중단 · ' + esc(DATA.error.code) + '</b><p>' + esc(DATA.error.message) + '. 결정은 연결이 복구된 뒤에 할 수 있습니다.</p></div></div>' : "";
  $("#ap-head").innerHTML = '<h1>' + esc(LABELS.nav.approvals) + '</h1><p>' + (s === "empty" || s === "loading" ? "" : "대기 " + n + "건 · 에이전트 초안은 사람이 승인하기 전까지 효력이 없습니다. HIGH는 재로그인이 필요합니다.") + '</p>' +
    '<div class="chips" role="tablist">' + Object.entries(FILTERS).map(([k, l]) => '<button class="chip" role="tab" data-act="filter" data-v="' + k + '" aria-selected="' + (UI.filter === k) + '" style="' + (UI.filter === k ? "background:var(--ink);color:var(--on-ink);border-color:var(--ink)" : "") + '">' + l + '</button>').join("") + '</div>' + alert;
}
function renderList() {
  const s = APP.state, el = $("#ap-list");
  if (s === "loading") { el.innerHTML = sk(96) + sk(96) + sk(96); return; }
  const L = visible();
  if (!L.length) { el.innerHTML = '<div class="empty"><span class="empty-ic">' + ic("approvals") + '</span><h3>' + (s === "empty" ? "승인 대기 항목이 없습니다" : s === "error" ? "승인 큐를 불러오지 못했습니다" : "조건에 맞는 항목이 없습니다") + '</h3><p>' + (s === "error" ? "연결이 복구되면 자동으로 다시 받습니다." : "에이전트가 초안을 제출하면 여기에 표시됩니다.") + '</p></div>'; return; }
  el.innerHTML = L.map(g => '<button class="aq" data-act="sel" data-id="' + g.id + '" aria-current="' + (cur() && cur().id === g.id) + '">' +
    '<div class="aq-top"><span class="aq-id">' + g.id + '</span><span class="sev sev-' + g.risk + '">' + g.risk + '</span>' + (g.reauth && status(g) === "pending" ? '<span class="reauth reauth-o">' + ic("lock") + '재로그인</span>' : "") + '<span class="aq-time">' + g.time + '</span></div>' +
    '<div class="aq-t">' + esc(g.title) + '</div><div class="aq-m">' + esc(g.type) + ' · ' + esc(g.caseId) + '</div>' +
    '<div class="aq-top">' + stPv(g) + '</div></button>').join("");
}
function citeHTML(c) {
  const t = c.src === "manual" ? "untrusted" : "approved", tag = c.src === "manual" ? "" : "";
  return '<div class="cite"><div class="cite-top"><b>' + esc(c.doc) + '</b><span class="cite-loc mono">' + esc(c.loc) + '</span></div><blockquote class="cite-q">“<mark>' + esc(c.quote) + '</mark>”</blockquote>' +
    (c.src === "manual" ? '<div class="cite-foot">' + pv("approved", "승격 문서", "sm") + '<a class="cite-link" href="draft.html?doc=vfd-22&amp;loc=' + encodeURIComponent(c.loc) + '">원문 위치 ' + ic("ext") + '</a></div>' : '<div class="cite-foot">' + pv("approved", "정비 이력", "sm") + '</div>') + '</div>';
}
function renderDetail() {
  const s = APP.state, el = $("#ap-detail");
  el.classList.toggle("open", UI.detail);
  const back = '<button class="btn btn-sm det-back" data-act="back">' + ic("chev") + '목록</button>';
  if (s === "loading") { el.innerHTML = sk(36, "60%") + sk(120) + sk(160); return; }
  const g = cur();
  if (!g) { el.innerHTML = back + '<div class="empty"><span class="empty-ic">' + ic("search") + '</span><h3>선택한 항목이 없습니다</h3><p>왼쪽 목록에서 항목을 고르면 초안 요약과 근거를 볼 수 있습니다.</p></div>'; return; }
  el.innerHTML = back +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><span class="aq-id">' + g.id + '</span><span class="sev sev-' + g.risk + '">' + g.risk + '</span>' + stPv(g) + '</div>' +
    '<h2 class="det-title">' + esc(g.title) + '</h2>' +
    '<div style="display:flex;gap:6px 18px;flex-wrap:wrap;font-size:var(--fs-sm);color:var(--tx-2);font-weight:600"><span>종류 <b class="mono" style="color:var(--tx-1)">' + esc(g.type) + '</b></span><span>작성 <b class="mono" style="color:var(--tx-1)">' + esc(g.by) + '</b></span><span>케이스 <a class="mono" href="case.html">' + esc(g.caseId) + '</a></span></div>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">초안 요약 ' + pv("draft", null, "sm") + '</div><ul class="ap-sum">' + g.sum.map(t => '<li>' + ic("check") + '<span>' + esc(t) + '</span></li>').join("") + '</ul>' +
    '<a class="btn btn-sm" style="align-self:flex-start" href="draft.html">' + ic("draft") + '전체 초안 검토</a></section>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">근거 ' + g.cites.length + '</div><div class="cites">' + g.cites.map(citeHTML).join("") + '</div></section>';
}
function renderBar() {
  const s = APP.state, g = cur(), bar = $("#human-bar");
  const tag = '<span class="human-tag">' + ic("user") + esc(LABELS.humanOnly) + '</span>';
  if (!g) { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">결정할 항목이 없습니다.</span></div>'; return; }
  const st = status(g);
  if (st !== "pending") {
    bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">' + g.id + (st === "approved" ? " 승인됨 · 감사 기록에 남았습니다" : " 반려됨 · 에이전트에 사유가 전달됩니다") + '</span></div><div class="hb-actions">' + stPv(g) + '<a class="btn" href="audit.html">' + ic("audit") + '감사 기록</a></div>'; return;
  }
  const dis = s === "loading" || s === "error" || s === "running" ? " disabled" : "";
  bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">' + (g.reauth ? "HIGH 위험 항목입니다. 승인하려면 사번과 PIN을 다시 확인합니다." : "일반 항목입니다. 내용을 확인하고 결정하세요.") + '</span></div><div class="hb-actions">' +
    '<button class="btn btn-danger" data-act="reject"' + dis + '>' + ic("x") + '반려</button>' +
    '<button class="btn btn-primary" data-act="approve"' + dis + '>' + ic(g.reauth ? "lock" : "check") + '<span class="lbl-long">승인</span><span class="lbl-short">승인</span>' + (g.reauth ? '<span class="reauth">재로그인</span>' : "") + '</button></div>';
}
function renderPage() { renderHead(); renderList(); renderDetail(); renderBar(); }
function finish(v, msg, icon) { UI.done[UI.sel] = { v: v }; closeModal(); renderPage(); toast(msg, icon); }
const PAGE_ACTS = {
  filter: el => { UI.filter = el.dataset.v; renderPage(); },
  sel: el => { UI.sel = el.dataset.id; UI.detail = true; renderPage(); },
  back: () => { UI.detail = false; renderDetail(); },
  approve: () => {
    const g = cur(); UI.sel = g.id;
    if (!g.reauth) { finish("approved", g.id + " 승인 · 감사 기록에 남았습니다", "user-check"); return; }
    openPinModal({ title: "재로그인 후 승인", lead: `${g.id} · ${g.title}`, act: "approve-ok", label: "승인" });
  },
  "approve-ok": () => { if ($("#pin").value.length < 4) { $("#pin-err").hidden = false; return; } finish("approved", UI.sel + " 승인 · 감사 기록에 남았습니다", "user-check"); },
  reject: () => openReasonModal({ title: "초안 반려", hint: "반려 사유는 에이전트에 전달되어 재작성에 쓰입니다.", act: "reject-ok", label: "반려" }),
  "reject-ok": () => finish("rejected", UI.sel + " 반려 · 사유를 에이전트에 전달했습니다", "x")
};

initTheme(); readURL();
renderShell([LABELS.nav.approvals]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
