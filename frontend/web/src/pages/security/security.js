// 샌드박스·정책 · 에이전트 콘솔 — 페이지 로직
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
import "../../data/security.js";
import { view, outside, humanBar } from "./view.js";
import { openPinModal } from "../../components/modals/pin-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: security ================= */
const UI = { sel: "net.fetch", filter: "all", detail: false, done: null };
const sk = (h, w) => '<div class="sk" style="height:' + h + 'px;width:' + (w || "100%") + '"></div>';
const FILTERS = { all: "전체", allow: "허용", human: "사람 전용", deny: "차단" };
const MODE = { allow: "허용", human: "사람 전용", deny: "차단" };
const blocked = () => APP.state === "empty" || APP.state === "loading" || APP.state === "error";
const applied = () => UI.done === "ok" || APP.state === "approved";
function mode(t) { return t.prop && applied() ? "allow" : t.mode; }
function visible() { return blocked() ? [] : DATA.tools.filter(t => UI.filter === "all" || mode(t) === UI.filter); }
function cur() { return visible().find(x => x.id === UI.sel) || visible()[0]; }
const modeTag = m => '<span class="mode ' + m + '"><i></i>' + (m === "human" ? ic("user") : "") + MODE[m] + '</span>';
function renderHead() {
  const s = APP.state;
  const alert = s === "blocked" ? '<div class="alert alert-blocked" role="alert">' + ic("ban") + '<div><b>정책이 호출 3건을 차단</b><p>발주 시도, 채팅 승인 요청, 외부 주소 접근입니다. 모두 감사 기록에 남았습니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>'
    : s === "error" ? '<div class="alert alert-error" role="alert">' + ic("alert") + '<div><b>정책 서버 중단 · ' + esc(DATA.error.code) + '</b><p>' + esc(DATA.error.message) + '. 연결이 끊긴 동안 에이전트는 모든 도구가 차단됩니다.</p></div></div>' : "";
  $("#se-head").innerHTML = '<h1>' + esc(LABELS.nav.security) + '</h1><p>' + (blocked() ? "" : "에이전트는 샌드박스 안에서만 도구를 씁니다. 비용이나 설비에 영향을 주는 행동은 사람 전용입니다.") + '</p>' +
    '<div class="chips" role="tablist">' + Object.entries(FILTERS).map(([k, l]) => '<button class="chip" role="tab" data-act="filter" data-v="' + k + '" aria-selected="' + (UI.filter === k) + '" style="' + (UI.filter === k ? "background:var(--ink);color:var(--on-ink);border-color:var(--ink)" : "") + '">' + l + '</button>').join("") + '</div>' + alert;
}
function renderList() {
  const s = APP.state, el = $("#se-list");
  if (s === "loading") { el.innerHTML = sk(86) + sk(86) + sk(86) + sk(86); return; }
  const L = visible();
  if (!L.length) { el.innerHTML = '<div class="empty"><span class="empty-ic">' + ic("security") + '</span><h3>' + (s === "empty" ? "등록된 도구가 없습니다" : s === "error" ? "정책을 불러오지 못했습니다" : "조건에 맞는 도구가 없습니다") + '</h3><p>' + (s === "error" ? "연결이 복구되면 자동으로 다시 받습니다." : "필터를 바꿔 보세요.") + '</p></div>'; return; }
  const c = cur();
  el.innerHTML = L.map(t => '<button class="tl" data-act="sel" data-id="' + t.id + '" aria-current="' + (c && c.id === t.id) + '"><div class="tl-top"><span class="tl-id">' + t.id + '</span>' + modeTag(mode(t)) + '</div><div class="tl-m">' + esc(t.name) + ' · ' + esc(t.prop && applied() ? "허용 목록 1건" : t.scope) + '</div>' + (t.prop && !applied() ? '<div class="tl-top">' + pv("draft", "변경 제안", "sm") + '</div>' : "") + '</button>').join("");
}
function renderDetail() {
  const s = APP.state, el = $("#se-detail");
  el.classList.toggle("open", UI.detail);
  const back = '<button class="btn btn-sm det-back" data-act="back">' + ic("chev") + '목록</button>';
  if (s === "loading") { el.innerHTML = sk(36, "60%") + sk(120) + sk(160); return; }
  const t = cur();
  if (!t) { el.innerHTML = back + '<div class="empty"><span class="empty-ic">' + ic("search") + '</span><h3>선택한 도구가 없습니다</h3><p>도구를 고르면 정책 원문과 최근 호출을 볼 수 있습니다.</p></div>'; return; }
  const m = mode(t), P = DATA.prop;
  const yaml = t.prop && (t.prop && !applied()) ? t.yaml : t.prop ? P.diff.filter(x => x[0] !== "-").map(x => x.replace(/^\+/, "")).filter(x => x !== "mode: deny").join("\n") : t.yaml;
  el.innerHTML = back +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><span class="tl-id">' + t.id + '</span>' + modeTag(m).replace("margin-left:auto", "") + '</div>' +
    '<h2 class="det-title">' + esc(t.name) + '</h2>' +
    '<dl class="dl"><dt>범위</dt><dd>' + esc(t.scope) + '</dd><dt>오늘 호출</dt><dd class="mono">' + t.calls + '건</dd></dl>' +
    (m === "human" ? '<div class="alert alert-blocked">' + ic("ban") + '<div><b>에이전트는 호출할 수 없음</b><p>이 도구는 사람이 직접 실행하며 재로그인이 필요합니다. 어떤 입력도 이 규칙을 바꾸지 못합니다.</p></div></div>' : "") +
    (t.prop && !applied() ? '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">변경 제안 ' + P.id + ' ' + pv("draft", null, "sm") + '</div><p style="font-weight:600;line-height:1.5">' + esc(P.title) + '</p><p style="color:var(--tx-2);font-size:var(--fs-sm);font-weight:500;line-height:1.5">' + esc(P.why) + '</p><pre class="yaml mono">' + P.diff.map(x => x[0] === "+" ? '<span class="add">' + esc(x) + '</span>' : esc(x)).join("\n") + '</pre></section>'
      : '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">정책 원문' + (t.prop ? " " + pv("approved", DATA.shell.user.id + " · 14:05", "sm") : "") + '</div><pre class="yaml mono">' + esc(yaml) + '</pre></section>') +
    '<section style="display:flex;flex-direction:column;gap:8px"><div class="sec-t">최근 호출 ' + t.log.length + '</div>' + (t.log.length ? '<ul class="lg">' + t.log.map(l => '<li><span class="mono">' + l[0] + ' · ' + l[1] + '</span>' + esc(l[2]) + '</li>').join("") + '</ul>' : '<p style="color:var(--tx-2);font-weight:500;font-size:var(--fs-sm)">최근 호출이 없습니다.</p>') + '</section>';
}
function renderBar() {
  const s = APP.state, bar = $("#human-bar"), P = DATA.prop;
  const tag = '<span class="human-tag">' + ic("user") + esc(LABELS.humanOnly) + '</span>';
  if (blocked() && s !== "error") { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">결정할 정책 변경이 없습니다.</span></div>'; return; }
  if (applied()) { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">' + P.id + ' 적용됨 · 감사 기록에 남았습니다</span></div><div class="hb-actions">' + pv("approved", DATA.shell.user.id + " · 14:05", "lg") + '<a class="btn" href="audit.html">' + ic("audit") + '감사 기록</a></div>'; return; }
  if (UI.done === "no") { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">' + P.id + ' 반려됨 · 정책은 그대로입니다</span></div><div class="hb-actions"><button class="btn" data-act="undo">' + ic("retry") + '되돌리기</button></div>'; return; }
  const dis = s === "loading" || s === "error" || s === "running" ? " disabled" : "";
  bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">정책 변경 ' + P.id + '이 대기 중입니다. 적용하려면 사번과 PIN을 다시 확인합니다.</span></div><div class="hb-actions"><button class="btn btn-danger" data-act="reject"' + dis + '>' + ic("x") + '반려</button><button class="btn btn-primary" data-act="apply"' + dis + '>' + ic("lock") + '<span class="lbl-long">정책 변경 적용</span><span class="lbl-short">적용</span><span class="reauth">재로그인</span></button></div>';
}
function renderPage() { renderHead(); renderList(); renderDetail(); renderBar(); }
const PAGE_ACTS = {
  filter: el => { UI.filter = el.dataset.v; renderPage(); },
  sel: el => { UI.sel = el.dataset.id; UI.detail = true; renderPage(); },
  back: () => { UI.detail = false; renderDetail(); },
  undo: () => { UI.done = null; renderPage(); },
  apply: () => openPinModal({ title: "재로그인 후 적용", lead: `${DATA.prop.id} · ${DATA.prop.title}`, act: "apply-ok", label: "적용" }),
  "apply-ok": () => { if ($("#pin").value.length < 4) { $("#pin-err").hidden = false; return; } UI.done = "ok"; closeModal(); renderPage(); toast(DATA.prop.id + " 적용 · 감사 기록에 남았습니다", "user-check"); },
  reject: () => { UI.done = "no"; renderPage(); toast(DATA.prop.id + " 반려 · 감사 기록에 남았습니다", "x"); }
};

initTheme(); readURL();
renderShell([LABELS.nav.security]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
