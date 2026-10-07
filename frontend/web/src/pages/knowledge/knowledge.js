// 지식 온보딩 · 에이전트 콘솔 — 페이지 로직
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
import "../../data/knowledge.js";
import { view, outside, humanBar } from "./view.js";
import { openReasonModal } from "../../components/modals/reason-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: knowledge ================= */
const UI = { sel: "DOC-0031", filter: "all", detail: false, done: {} };
const sk = (h, w) => '<div class="sk" style="height:' + h + 'px;width:' + (w || "100%") + '"></div>';
const FILTERS = { all: "전체", review: "승격 대기", promoted: "승격됨", blocked: "격리" };
const NOW = "14:05";
function st(d) { return UI.done[d.id] || (APP.state === "approved" && d.st === "review" ? "promoted" : d.st); }
function visible() {
  const s = APP.state; if (s === "empty" || s === "loading" || s === "error") return [];
  return DATA.docs.filter(d => FILTERS[UI.filter] && (UI.filter === "all" || st(d) === UI.filter));
}
function cur() { return visible().find(x => x.id === UI.sel) || visible()[0]; }
function dPv(d) {
  const t = st(d);
  if (t === "promoted") return pv("approved", (d.by || DATA.shell.user.id) + " · " + (d.at || NOW), "sm");
  if (t === "blocked") return pv("blocked", "격리", "sm");
  if (t === "rejected") return pv("blocked", "승격 거부", "sm");
  return pv("untrusted", "승격 대기", "sm");
}
function renderHead() {
  const s = APP.state, n = DATA.docs.filter(d => st(d) === "review").length;
  const alert = s === "blocked" ? '<div class="alert alert-blocked" role="alert">' + ic("ban") + '<div><b>문서 1건 격리</b><p>DOC-0032 7쪽에 시스템을 향한 지시문이 있습니다. 색인에서 제외했고 감사 기록에 남겼습니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>'
    : s === "error" ? '<div class="alert alert-error" role="alert">' + ic("alert") + '<div><b>색인 서버 중단 · ' + esc(DATA.error.code) + '</b><p>' + esc(DATA.error.message) + '. 승격된 문서 검색은 캐시로 계속됩니다.</p></div></div>' : "";
  $("#kn-head").innerHTML = '<h1>' + esc(LABELS.nav.knowledge) + '</h1><p>' + (s === "empty" || s === "loading" ? "" : "승격 대기 " + n + "건 · 업로드한 문서는 검증 전 입력입니다. 사람이 승격해야 에이전트가 근거로 인용할 수 있습니다.") + '</p>' +
    '<div class="chips" role="tablist">' + Object.entries(FILTERS).map(([k, l]) => '<button class="chip" role="tab" data-act="filter" data-v="' + k + '" aria-selected="' + (UI.filter === k) + '" style="' + (UI.filter === k ? "background:var(--ink);color:var(--on-ink);border-color:var(--ink)" : "") + '">' + l + '</button>').join("") + '</div>' + alert;
}
function renderList() {
  const s = APP.state, el = $("#kn-list");
  if (s === "loading") { el.innerHTML = sk(96) + sk(96) + sk(96); return; }
  const L = visible();
  if (!L.length) { el.innerHTML = '<div class="empty"><span class="empty-ic">' + ic("knowledge") + '</span><h3>' + (s === "empty" ? "등록된 문서가 없습니다" : s === "error" ? "문서를 불러오지 못했습니다" : "조건에 맞는 문서가 없습니다") + '</h3><p>' + (s === "error" ? "연결이 복구되면 자동으로 다시 받습니다." : "설비 매뉴얼을 올리면 색인 후 승격 검토 대기열에 들어옵니다.") + '</p></div>'; return; }
  el.innerHTML = L.map((d, i) => '<button class="kd" data-act="sel" data-id="' + d.id + '" aria-current="' + (cur() && cur().id === d.id) + '">' +
    '<div class="kd-top"><span class="kd-id">' + d.id + '</span><span class="kd-time">' + d.time + '</span></div>' +
    '<div class="kd-t">' + esc(d.name) + '</div><div class="kd-m">' + esc(d.kind) + ' · ' + d.pages + '쪽</div>' +
    '<div class="kd-top">' + (s === "running" && i === 0 ? '<span class="spin"></span><b style="font-size:var(--fs-sm)">에이전트 색인 중</b>' : dPv(d)) + '</div></button>').join("");
}
function citeHTML(c, d) {
  return '<div class="cite"><div class="cite-top"><b>' + esc(c.doc) + '</b><span class="cite-loc mono">' + esc(c.loc) + '</span></div><blockquote class="cite-q">“<mark>' + esc(c.quote) + '</mark>”</blockquote><div class="cite-foot">' + dPv(d) + '</div></div>';
}
function renderDetail() {
  const s = APP.state, el = $("#kn-detail");
  el.classList.toggle("open", UI.detail);
  const back = '<button class="btn btn-sm det-back" data-act="back">' + ic("chev") + '목록</button>';
  if (s === "loading") { el.innerHTML = sk(36, "60%") + sk(120) + sk(160); return; }
  const d = cur();
  if (!d) { el.innerHTML = back + '<div class="empty"><span class="empty-ic">' + ic("search") + '</span><h3>선택한 문서가 없습니다</h3><p>왼쪽 목록에서 문서를 고르면 처리 과정과 추출 문장을 볼 수 있습니다.</p></div>'; return; }
  const t = st(d), steps = d.steps.slice();
  if (t === "promoted" && d.st === "review") { steps[steps.length - 1] = ["ok", "승격 검토", DATA.shell.user.id + " 승격", NOW]; }
  const ico = { ok: "check", fail: "x", now: "clock" };
  el.innerHTML = back +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><span class="kd-id">' + d.id + '</span>' + dPv(d) + '</div>' +
    '<h2 class="det-title">' + esc(d.name) + '</h2>' +
    '<div style="display:flex;gap:6px 18px;flex-wrap:wrap;font-size:var(--fs-sm);color:var(--tx-2);font-weight:600"><span>종류 <b class="mono" style="color:var(--tx-1)">' + esc(d.kind) + '</b></span><span>분량 <b class="mono" style="color:var(--tx-1)">' + d.pages + '쪽</b></span><span>출처 <b style="color:var(--tx-1)">' + esc(d.src) + '</b></span></div>' +
    (t === "blocked" ? '<div class="alert alert-blocked">' + ic("ban") + '<div><b>따르지 않음</b><p>' + esc(d.note) + '</p></div></div>' : d.note && t === "review" ? '<div class="alert alert-ok">' + ic("info") + '<div><p>' + esc(d.note) + '</p></div></div>' : "") +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">처리 과정</div><ul class="pipe">' + steps.map(x => '<li class="' + x[0] + '"><span class="dot">' + ic(ico[x[0]]) + '</span><span>' + esc(x[1]) + '<small>' + esc(x[2]) + '</small></span><span class="tm">' + esc(x[3]) + '</span></li>').join("") + '</ul></section>' +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">추출 문장 ' + d.passages.length + '</div><div class="cites">' + d.passages.map(c => citeHTML(c, d)).join("") + '</div></section>';
}
function renderBar() {
  const s = APP.state, d = cur(), bar = $("#human-bar");
  const tag = '<span class="human-tag">' + ic("user") + esc(LABELS.humanOnly) + '</span>';
  if (!d) { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">결정할 문서가 없습니다.</span></div>'; return; }
  const t = st(d);
  if (t !== "review") {
    bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">' + d.id + (t === "promoted" ? " 승격됨 · 이제 에이전트가 근거로 인용합니다" : t === "rejected" ? " 승격 거부됨" : " 격리됨 · 승격할 수 없습니다") + '</span></div><div class="hb-actions">' + dPv(d) + '<a class="btn" href="audit.html">' + ic("audit") + '감사 기록</a></div>'; return;
  }
  const dis = s === "loading" || s === "error" || s === "running" ? " disabled" : "";
  bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">추출 문장을 확인하고 이 문서를 판단 근거로 승격할지 결정합니다.</span></div><div class="hb-actions">' +
    '<button class="btn btn-danger" data-act="reject"' + dis + '>' + ic("x") + '거부</button>' +
    '<button class="btn btn-primary" data-act="promote"' + dis + '>' + ic("check") + '<span class="lbl-long">근거 문서로 승격</span><span class="lbl-short">승격</span></button></div>';
}
function renderPage() { renderHead(); renderList(); renderDetail(); renderBar(); }
function finish(v, msg, icon) { UI.done[UI.sel] = v; closeModal(); renderPage(); toast(msg, icon); }
const PAGE_ACTS = {
  filter: el => { UI.filter = el.dataset.v; renderPage(); },
  sel: el => { UI.sel = el.dataset.id; UI.detail = true; renderPage(); },
  back: () => { UI.detail = false; renderDetail(); },
  promote: () => { UI.sel = cur().id; finish("promoted", UI.sel + " 승격 · " + DATA.shell.user.id + " · 감사 기록에 남았습니다", "user-check"); },
  reject: () => openReasonModal({ title: "승격 거부", hint: "거부한 문서는 색인에서 제외됩니다. 사유를 적어 주세요.", act: "reject-ok", label: "거부" }),
  "reject-ok": () => finish("rejected", UI.sel + " 승격 거부 · 감사 기록에 남았습니다", "x")
};

initTheme(); readURL();
renderShell([LABELS.nav.knowledge]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
