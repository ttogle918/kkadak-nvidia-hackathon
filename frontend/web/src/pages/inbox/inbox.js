// 신호 인박스 · 에이전트 콘솔 — 페이지 로직
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
import "../../data/inbox.js";
import { view, outside, humanBar } from "./view.js";
import { openReasonModal } from "../../components/modals/reason-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: inbox ================= */
const UI = { sel: "SIG-1003-031", filter: "all", detail: false, ignored: {}, assigned: {} };
const sk = (h, w) => `<div class="sk" style="height:${h}px;width:${w || "100%"}"></div>`;
const FILTERS = { all: "전체", new: "신규", susp: "의심·이상", noev: "근거 없음" };
const isSusp = g => g.inject || g.prov === "sensor";
function visible() {
  const s = APP.state; if (s === "empty" || s === "loading" || s === "error") return [];
  return DATA.signals.filter(g => ({ all: 1, new: g.isNew, susp: isSusp(g), noev: g.noev })[UI.filter] && !UI.ignored[g.id]);
}
function pvOf(g) { return g.inject ? "blocked" : g.prov; }
function renderHead() {
  const s = APP.state, n = DATA.signals.filter(g => !UI.ignored[g.id]).length;
  const alert = s === "blocked" ? `<div class="alert alert-blocked" role="alert">${ic("ban")}<div><b>주입 공격 의심 1건 격리</b><p>SIG-1003-030 사진의 OCR 텍스트에 발주 지시가 있습니다. 판단 근거에서 제외했고 감사 기록에 남겼습니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>`
    : s === "error" ? `<div class="alert alert-error" role="alert">${ic("alert")}<div><b>신호 수집 중단 · ${esc(DATA.error.code)}</b><p>${esc(DATA.error.message)}. 이미 받은 신호는 아래에 보존되어 있습니다.</p></div></div>` : "";
  $("#ib-head").innerHTML = `<h1>${esc(LABELS.nav.inbox)}</h1>
    <p>${s === "empty" || s === "loading" ? "" : "수신 ${n}건 · 모두 검증 전 입력입니다. 에이전트는 분류만 하고, 케이스 배정은 사람이 합니다."}</p>
    <div class="chips" role="tablist">${Object.entries(FILTERS).map(([k, l]) => `<button class="chip" role="tab" data-act="filter" data-v="${k}" aria-selected="${UI.filter === k}" style="${UI.filter === k ? "background:var(--ink);color:var(--on-ink);border-color:var(--ink)" : ""}">${l}</button>`).join("")}</div>${alert}`.replace("\${n}", n);
}
function renderList() {
  const s = APP.state, el = $("#ib-list");
  if (s === "loading") { el.innerHTML = sk(96) + sk(96) + sk(96) + sk(96); return; }
  const L = visible();
  if (!L.length) { el.innerHTML = `<div class="empty"><span class="empty-ic">${ic("inbox")}</span><h3>${s === "empty" ? "수신된 신호가 없습니다" : s === "error" ? "신호를 불러오지 못했습니다" : "조건에 맞는 신호가 없습니다"}</h3><p>${s === "error" ? "연결이 복구되면 자동으로 다시 받습니다." : "새 에러코드, 센서 이상, 현장 메모가 들어오면 여기에 표시됩니다."}</p></div>`; return; }
  el.innerHTML = L.map((g, i) => {
    const proc = s === "running" && i === 0;
    return `<button class="sg" data-act="sel" data-id="${g.id}" aria-current="${UI.sel === g.id}">
      <div class="sg-top">${g.isNew ? '<span class="sg-new" aria-label="신규"></span>' : ""}<span class="sg-id">${g.id}</span><span class="sev sev-${g.sev}">${g.sev}</span><span class="sg-time">${g.time}</span></div>
      <div class="sg-t">${esc(g.title)}</div>
      <div class="sg-m">${esc(g.kind)} · ${esc(g.target)}</div>
      <div class="sg-top">${proc ? `<span class="sg-proc"><span class="spin"></span>에이전트 분류 중</span>` : pv(g.noev ? "noev" : pvOf(g), UI.assigned[g.id] ? "" : "", "sm")}${UI.assigned[g.id] ? pv("approved", "배정 " + DATA.shell.user.id, "sm") : ""}</div>
    </button>`;
  }).join("");
}
function renderDetail() {
  const s = APP.state, el = $("#ib-detail");
  el.classList.toggle("open", UI.detail);
  const back = `<button class="btn btn-sm det-back" data-act="back">${ic("chev")}목록</button>`;
  if (s === "loading") { el.innerHTML = sk(36, "60%") + sk(120) + sk(160); return; }
  const g = visible().find(x => x.id === UI.sel) || visible()[0];
  if (!g) { el.innerHTML = back + `<div class="empty"><span class="empty-ic">${ic("search")}</span><h3>선택한 신호가 없습니다</h3><p>왼쪽 목록에서 신호를 고르면 원문과 에이전트 분류를 볼 수 있습니다.</p></div>`; return; }
  const bx = g.inject ? "blocked" : g.noev ? "noev" : g.prov === "sensor" ? "sensor" : "untrusted";
  el.innerHTML = back + `
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><span class="sg-id">${g.id}</span><span class="sev sev-${g.sev}">${g.sev}</span>${pv(pvOf(g), null)}</div>
    <h2 class="det-title">${esc(g.title)}</h2>
    <div class="ch-meta" style="display:flex;gap:6px 18px;flex-wrap:wrap;font-size:var(--fs-sm);color:var(--tx-2);font-weight:600"><span>종류 <b class="mono" style="color:var(--tx-1)">${esc(g.kind)}</b></span><span>대상 <b class="mono" style="color:var(--tx-1)">${esc(g.target)}</b></span><span>수신 <b class="mono" style="color:var(--tx-1)">${g.time}</b></span></div>
    <section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">원문 · ${esc(g.src)}</div>
      <div class="pvbox pvbox-${bx}"><div class="pvbox-head">${pv(pvOf(g), g.inject ? "지시문 포함" : "", "sm")}</div><div class="pvbox-body"><pre class="raw mono">${esc(g.raw)}</pre></div></div></section>
    ${g.inject ? `<div class="alert alert-blocked">${ic("ban")}<div><b>따르지 않음</b><p>원문 속 지시는 명령이 아니라 데이터입니다. 발주 도구는 사람 전용입니다.</p></div></div>` : ""}
    <section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">에이전트 분류 ${pv("draft", null, "sm")}</div>
      <ul class="tri">${g.tri.map(t => `<li>${ic("check")}<span>${esc(t)}</span></li>`).join("")}</ul></section>`;
}
function renderBar() {
  const s = APP.state, g = visible().find(x => x.id === UI.sel) || visible()[0], bar = $("#human-bar");
  const tag = `<span class="human-tag">${ic("user")}${esc(LABELS.humanOnly)}</span>`;
  if (!g) { bar.innerHTML = `<div class="hb-id">${tag}<span class="hb-cap">결정할 신호가 없습니다.</span></div>`; return; }
  if (UI.assigned[g.id] || s === "approved") {
    bar.innerHTML = `<div class="hb-id">${tag}<span class="hb-cap">${g.id} 케이스 배정됨 · 에이전트 diag-01 진단 시작</span></div><div class="hb-actions">${pv("approved", DATA.shell.user.id + " · 14:02", "lg")}<a class="btn" href="case.html">${ic("case")}케이스 열기</a></div>`; return;
  }
  const dis = s === "loading" || s === "error" || s === "running" ? " disabled" : "";
  const cap = g.inject ? "발주 지시는 따르지 않습니다. 격리 유지 또는 무시를 결정하세요." : "이 신호로 케이스를 열고 에이전트에 진단을 맡길지 사람이 결정합니다.";
  bar.innerHTML = `<div class="hb-id">${tag}<span class="hb-cap">${cap}</span></div><div class="hb-actions">
    <button class="btn btn-danger" data-act="ignore"${dis}>${ic("x")}무시</button>
    ${g.inject ? `<a class="btn" href="audit.html?filter=blocked">${ic("audit")}감사 기록</a>` : `<button class="btn btn-primary" data-act="assign"${dis}>${ic("case")}<span class="lbl-long">케이스 열고 진단 배정</span><span class="lbl-short">배정</span></button>`}</div>`;
}
function renderPage() { renderHead(); renderList(); renderDetail(); renderBar(); }
const PAGE_ACTS = {
  filter: el => { UI.filter = el.dataset.v; renderPage(); },
  sel: el => { UI.sel = el.dataset.id; UI.detail = true; renderPage(); },
  back: () => { UI.detail = false; renderDetail(); },
  ignore: () => openReasonModal({ title: "신호 무시", hint: "무시한 신호도 감사 기록에 남습니다. 사유를 적어 주세요.", act: "ignore-ok", label: "무시" }),
  "ignore-ok": () => { UI.ignored[UI.sel] = 1; closeModal(); UI.detail = false; UI.sel = null; renderPage(); toast("신호를 무시했습니다 · 감사 기록에 남았습니다", "x"); },
  assign: () => { UI.assigned[UI.sel] = 1; renderPage(); toast("케이스 배정 · 에이전트 diag-01이 진단을 시작합니다", "user-check"); }
};

initTheme(); readURL();
renderShell([LABELS.nav.inbox]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
