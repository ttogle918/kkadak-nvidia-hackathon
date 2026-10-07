// 현장 모바일 · 에이전트 콘솔 — 페이지 로직
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
import "../../data/field.js";
import { view, outside, humanBar } from "./view.js";
import { openCodeModal } from "./code-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: field ================= */
const UI = { done: {}, ups: DATA.seed.slice(), n: 3 };
const sk = (h, w) => '<div class="sk" style="height:' + h + 'px;width:' + (w || "100%") + '"></div>';
const blocked = () => APP.state === "loading" || APP.state === "error";
const doneT = id => UI.done[id] || (APP.state === "approved" && id === "T1");
const curT = () => DATA.tasks.find(t => !doneT(t.id));
function renderHead() {
  const s = APP.state;
  const alert = s === "blocked" ? '<div class="alert alert-blocked" role="alert">' + ic("ban") + '<div><b>올린 사진 1건 격리</b><p>memo_line3.jpg의 글자에 시스템을 향한 지시가 있어 판단에서 제외했습니다. 작업에는 영향이 없습니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>'
    : s === "error" ? '<div class="alert alert-error" role="alert">' + ic("alert") + '<div><b>연결 중단 · ' + esc(DATA.error.code) + '</b><p>' + esc(DATA.error.message) + '. 입력은 기기에 보관했다가 연결되면 보냅니다.</p></div></div>' : "";
  $("#fd-head").innerHTML = '<h1>' + esc(LABELS.nav.field) + '</h1><p>' + esc(DATA.site.where) + ' · ' + DATA.site.shift + '</p>' + alert;
}
function upStatus(u) {
  if (APP.state === "running" && u === UI.ups[0]) return '<span class="up-st"><span class="spin"></span>전송 중</span>';
  if (u.st === "queued" && APP.net !== "offline") return '<span class="up-st">' + ic("check") + '전송됨</span>';
  if (u.st === "queued") return '<span class="up-st q">' + ic("clock") + '연결 대기</span>';
  return '<span class="up-st">' + ic("check") + '전송됨</span>';
}
function renderBody() {
  const s = APP.state, el = $("#fd-col");
  if (s === "loading") { el.innerHTML = sk(110) + sk(96) + sk(96); return; }
  const cur = curT(), off = APP.net === "offline" || s === "error";
  const tasks = DATA.tasks.map(t => {
    const d = doneT(t.id), isNow = cur && cur.id === t.id;
    return '<div class="tsk' + (d ? " done" : isNow ? " now" : "") + '"><span class="tsk-n">' + (d ? ic("check") : t.id.slice(1)) + '</span><div class="tsk-b"><span class="tsk-t">' + esc(t.t) + '</span><span class="tsk-m">' + esc(t.m) + ' · 근거 ' + esc(t.src) + '</span>' + (d ? pv("approved", DATA.shell.user.id + " · 14:05", "sm") : pv("draft", null, "sm")) + '</div></div>';
  }).join("");
  el.innerHTML =
    '<section class="fd-sec"><div class="sec-t">현장 입력' + (off ? " · 오프라인 보관" : "") + '</div><div class="cap">' +
    '<button data-act="photo">' + ic("camera") + '사진</button><button data-act="voice">' + ic("mic") + '음성 메모</button><button data-act="code">' + ic("edit") + '에러코드</button></div>' +
    '<p style="color:var(--tx-2);font-size:var(--fs-sm);font-weight:500">올린 내용은 모두 검증 전 입력으로 인박스에 들어갑니다. 에이전트는 이 내용을 명령으로 받지 않습니다.</p></section>' +
    '<section class="fd-sec"><div class="sec-t">내 작업 ' + DATA.tasks.length + ' ' + pv("draft", null, "sm") + '</div>' + tasks + '</section>' +
    '<section class="fd-sec"><div class="sec-t">올린 내용 ' + UI.ups.length + '</div>' + (UI.ups.length ? UI.ups.map(u => '<div class="up"><div class="up-top"><span class="mono" style="font-size:var(--fs-xs);font-weight:700;color:var(--tx-2)">' + u.id + '</span><span class="up-t">' + esc(u.kind) + ' · ' + esc(u.t) + '</span>' + upStatus(u) + '</div><div class="up-top">' + pv(u.prov === "blocked" && s === "blocked" ? "blocked" : "untrusted", null, "sm") + '<span class="mono" style="font-size:var(--fs-xs);color:var(--tx-3);font-weight:700">' + u.time + '</span></div></div>').join("") :
      '<div class="empty"><span class="empty-ic">' + ic("camera") + '</span><h3>올린 내용이 없습니다</h3><p>사진, 음성, 에러코드를 올리면 여기에 표시됩니다.</p></div>') + '</section>';
}
function renderBar() {
  const s = APP.state, bar = $("#human-bar"), cur = curT();
  const tag = '<span class="human-tag">' + ic("user") + esc(LABELS.humanOnly) + '</span>';
  if (!cur) { bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">오늘 배정된 작업을 모두 확인했습니다</span></div><div class="hb-actions"><a class="btn" href="audit.html">' + ic("audit") + '감사 기록</a></div>'; return; }
  const dis = blocked() || s === "running" ? " disabled" : "";
  bar.innerHTML = '<div class="hb-id">' + tag + '<span class="hb-cap">' + esc(cur.t) + '을(를) 직접 마쳤다면 완료를 확인하세요.</span></div><div class="hb-actions"><button class="btn btn-primary" data-act="done"' + dis + '>' + ic("check") + '<span class="lbl-long">작업 완료 확인</span><span class="lbl-short">완료</span></button></div>';
}
function renderPage() { renderHead(); renderBody(); renderBar(); }
function addUp(kind, t) {
  UI.n++; const now = new Date(), hh = String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
  UI.ups.unshift({ id: "UP-" + UI.n, kind, t, time: hh, st: APP.net === "offline" ? "queued" : "sent", prov: "untrusted" });
  renderPage(); toast(kind + " " + (APP.net === "offline" ? "보관 · 연결되면 전송합니다" : "전송 · 인박스에 검증 전 입력으로 등록"), "check");
}
const PAGE_ACTS = {
  photo: () => $("#photo-in").click(),
  voice: () => addUp("음성 메모", "voice_" + String(UI.n + 1) + ".m4a"),
  code: () => openCodeModal(),
  "code-ok": () => { const c = $("#c-code").value.trim(); if (!c) return; const d = $("#c-dev").value.trim() || "미지정"; closeModal(); addUp("에러코드", c + " · " + d); },
  done: () => { const t = curT(); UI.done[t.id] = 1; renderPage(); toast(t.t + " 완료 확인 · 감사 기록에 남았습니다", "user-check"); }
};
$("#photo-in").addEventListener("change", e => { const f = e.target.files[0]; if (f) addUp("사진", f.name); e.target.value = ""; });

initTheme(); readURL();
renderShell([LABELS.nav.field]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
