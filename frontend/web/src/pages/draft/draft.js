// 초안 검토 · 에이전트 콘솔 — 페이지 로직
import { injectSprite } from "../../components/icons/sprite.js";
import { mountLayout } from "../../components/layout/app-layout.js";
import { renderDemo } from "../../components/layout/demo-panel.js";
import { renderShell } from "../../components/layout/shell.js";
import { closeModal, onModalClose, openModal } from "../../components/modals/modal.js";
import { toast } from "../../components/toast.js";
import { bindActs } from "../../lib/acts.js";
import { $, esc, ic, pv } from "../../lib/dom.js";
import { APP, DATA, LABELS, readURL, setState } from "../../lib/state.js";
import { initTheme } from "../../lib/theme.js";
import "../../data/draft.js";
import { view, outside, humanBar } from "./view.js";
import { modalHead } from "../../components/modals/modal-head.js";
import { openPinModal } from "../../components/modals/pin-modal.js";
import { openReasonModal } from "../../components/modals/reason-modal.js";
import { openReviseModal } from "../../components/modals/revise-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: draft ================= */
const UI = { lang: "ko", srcLang: "en", active: "s1", checks: {}, noev: {} };
let streamT = null;
const SRC = Object.fromEntries(DATA.sources.map(d => [d.id, d]));
const isPhone = () => matchMedia("(max-width:599.98px)").matches;
const sk = (h, w) => `<div class="sk" style="height:${h}px;width:${w || "100%"}"></div>`;
const S = () => APP.state;
const locked = () => ["approved", "running", "loading", "empty", "rejected"].includes(S());
const ckKey = id => UI.lang + ":" + id;
const isChecked = id => S() === "approved" || !!UI.checks[ckKey(id)];
function gate(lang) {
  const L = lang || UI.lang, must = DATA.sentences.filter(s => s.must);
  const done = S() === "approved" ? must.length : must.filter(s => UI.checks[L + ":" + s.id]).length;
  const noevPending = S() === "approved" ? 0 : DATA.sentences.filter(s => !s.cite && !UI.noev[s.id]).length;
  return { done, total: must.length, noevPending, ok: done === must.length && noevPending === 0 && !["error", "running", "loading", "empty"].includes(S()) };
}
function markTok(text, tok) {
  const t = esc(text); if (!tok) return t;
  const k = esc(tok); const i = t.indexOf(k); if (i < 0) return t;
  return t.slice(0, i) + `<mark class="tok">${k}</mark>` + t.slice(i + k.length);
}

function renderHead() {
  const d = DATA.draft, s = S();
  if (s === "loading") { $("#dh").innerHTML = `${sk(18, "240px")}${sk(34, "60%")}${sk(48, "70%")}`; return; }
  if (s === "empty") { $("#dh").innerHTML = `<div class="dh-row"><span class="dh-id">—</span></div><h1 class="dh-title">선택된 초안 없음</h1>`; return; }
  const g = gate();
  const state = s === "approved" ? pv("approved", `${DATA.approval.by} · ${DATA.approval.at}`) : s === "running" ? `<span class="runpill rp-run"><span class="spin"></span>에이전트 수정 중</span>` : pv("draft", "효력 없음");
  const langBtns = Object.keys(LABELS.langs).map(k => { const gg = gate(k); return `<button data-act="lang" data-v="${k}" aria-pressed="${UI.lang === k}">${esc(LABELS.langs[k])}<small>${gg.done}/${gg.total}</small></button>`; }).join("");
  const srcBtns = Object.keys(LABELS.srcLangs).map(k => `<button data-act="srclang" data-v="${k}" aria-pressed="${UI.srcLang === k}">${esc(LABELS.srcLangs[k])}</button>`).join("");
  const alert = s === "blocked" ? `<div class="alert alert-blocked" role="alert">${ic("ban")}<div><b>에이전트의 승인 상태 변경 시도 차단</b><p><span class="mono">${esc(DATA.blocked.tool)}(${esc(DATA.blocked.args)})</span> · ${esc(DATA.blocked.rule)}. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>`
    : s === "error" ? `<div class="alert alert-error" role="alert">${ic("alert")}<div><b>근거 원문을 불러오지 못했습니다 · ${esc(DATA.error.code)}</b><p>${esc(DATA.error.message)}. 원문 대조 없이 승인할 수 없습니다.</p></div></div>`
    : s === "rejected" ? `<div class="alert alert-error" role="status">${ic("x")}<div><b>반려됨 · ${esc(DATA.shell.user.role)} ${esc(DATA.shell.user.id)}</b><p>사유: ${esc(UI.rejectReason || "")}</p></div></div>` : "";
  $("#dh").innerHTML = `
    <div class="dh-row"><span class="dh-id">${esc(d.id)} · ${esc(d.type)}</span><span class="sev sev-${d.risk}">${d.risk}</span>${state}
      <span class="gate">${ic("check")}${esc(LABELS.mustCheck)} ${g.done}/${g.total}<span class="gate-bar"><i style="width:${g.done / g.total * 100}%"></i></span></span></div>
    <h1 class="dh-title">${esc(d.title)}</h1>
    <div class="dh-meta"><span>${esc(LABELS.case)} <a href="case.html"><b>${esc(d.caseId)}</b></a></span><span class="m-hide">${esc(LABELS.target)} <b>${esc(d.target)}</b></span>
      <span class="m-hide">${esc(LABELS.agent)} <b>${esc(d.agent)}</b></span><span>${esc(LABELS.version)} <b>${esc(d.version)}</b></span><span class="m-hide">수정 <b>${esc(d.updated)}</b></span></div>
    <div class="lang-row">
      <div class="lang-grp"><span>${esc(LABELS.langDraft)}</span><div class="seg" role="group" aria-label="${esc(LABELS.langDraft)}">${langBtns}</div></div>
      <div class="lang-grp src-only"><span>${esc(LABELS.langSrc)}</span><div class="seg" role="group" aria-label="${esc(LABELS.langSrc)}">${srcBtns}</div></div>
    </div>${alert}`;
}

function sentHTML(st, i) {
  const s = S(), text = st.text[UI.lang], checked = isChecked(st.id), lk = locked() || s === "error";
  const tokTxt = st.tok && !st.tok.whole ? st.tok[UI.lang] : null;
  const streaming = s === "running" && st.id === "s8";
  let html = streaming ? `<span id="stream"></span><span class="caret"></span>` : markTok(text, tokTxt);
  if (checked && tokTxt) html = html.replace('class="tok"', 'class="tok ok"');
  const removed = UI.noev[st.id] === "removed";
  const src = st.cite ? SRC[st.cite.doc] : null;
  const chip = st.cite ? `<span class="cchip">${ic(st.cite.doc === "cmms" ? "history" : "knowledge")}${esc(src.loc.split(" · ")[0])} · ¶${src.paras.findIndex(p => p.id === st.cite.para) + 1}</span>` : pv("noev", "연결된 근거 없음", "sm");
  const transl = UI.lang !== "ko" && UI.lang !== "en" ? pv("draft", "에이전트 번역", "sm") : "";
  const must = st.must ? `<span class="must">${ic("lock")}${esc(LABELS.mustCheck)}${st.warn ? " · 경고 문구" : ""}</span>` : "";
  const cmp = st.must ? (st.tok.whole
      ? `<span class="cmp">${ic("alert")}원문 <b>${esc(st.tok.src)}</b>과 의미·강도 대조</span>`
      : `<span class="cmp">원문 <b>${esc(st.tok.src)}</b>${ic("chev")}${esc(LABELS.langs[UI.lang])} <b>${esc(st.tok[UI.lang])}</b></span>`) : "";
  const chk = st.must ? `<div class="chk-row${checked ? " done" : ""}">${cmp}<button class="chk" data-act="check" data-id="${st.id}" aria-pressed="${checked}"${lk || streaming ? " disabled" : ""}><span class="box">${ic("check")}</span>${checked ? esc(LABELS.checkDone) : esc(LABELS.checkTodo)}</button></div>` : "";
  const noev = !st.cite ? (UI.noev[st.id]
      ? `<div class="noev-acts">${UI.noev[st.id] === "removed" ? `<span class="human-mini">${ic("user")}사람 결정 · 승인본에서 삭제</span>` : `<span class="human-mini">${ic("user")}사람 판단으로 유지 · ${esc(DATA.shell.user.id)}</span>`}${lk ? "" : `<button class="btn btn-sm" data-act="noev-undo" data-id="${st.id}">되돌리기</button>`}</div>`
      : `<p class="noev-note">매뉴얼과 이력에서 이 문장의 근거를 찾지 못했습니다. 승인 전에 삭제하거나 사람 판단으로 유지하세요.</p>
         <div class="noev-acts"><button class="btn btn-sm btn-danger" data-act="noev-remove" data-id="${st.id}"${lk ? " disabled" : ""}>${ic("x")}문장 삭제</button><button class="btn btn-sm" data-act="noev-keep" data-id="${st.id}"${lk ? " disabled" : ""}>${ic("user")}사람 판단으로 유지</button></div>`) : "";
  return `<li class="sent${UI.active === st.id ? " is-active" : ""}${!st.cite && UI.noev[st.id] !== "kept" ? " is-noev" : ""}${removed ? " is-removed" : ""}${st.warn ? " is-warn" : ""}" data-act="sent" data-id="${st.id}" role="button" tabindex="0" aria-pressed="${UI.active === st.id}">
    <span class="sn">${i + 1}</span>
    <div><p class="stx">${html}</p><div class="smeta">${chip}${must}${transl}</div>${chk}${noev}</div></li>`;
}

function renderDoc() {
  const s = S(), el = $("#dv-doc");
  if (s === "loading") { el.innerHTML = sk(28, "40%") + sk(420) + sk(160); return; }
  if (s === "empty") { el.innerHTML = `<div class="empty"><span class="empty-ic">${ic("draft")}</span><h3>검토할 초안이 없습니다</h3><p>승인 큐나 케이스 화면에서 초안을 고르면 여기에서 원문과 대조하며 검토합니다.</p><a class="btn" href="approvals.html">${ic("approvals")}승인 큐 열기</a></div>`; return; }
  const d = DATA.draft, ap = s === "approved";
  el.innerHTML = `
    <div class="col-h"><h2>${ic("draft")}${esc(LABELS.draft)} · ${esc(LABELS.langs[UI.lang])}</h2><span class="col-note">문장을 누르면 근거 위치가 강조됩니다</span></div>
    <article class="pvbox ${ap ? "pvbox-approved" : "pvbox-draft"}">
      <div class="doc-h"><div style="display:flex;gap:8px;flex-wrap:wrap">${ap ? pv("approved", `${DATA.approval.by} · ${DATA.approval.at}`, "sm") : pv("draft", d.version, "sm")}</div>
        <h3>${esc(d.title)}</h3><p>${esc(d.target)} · 문장 ${DATA.sentences.length} · 근거 연결 ${DATA.sentences.filter(x => x.cite).length}</p></div>
      <ol class="sents">${DATA.sentences.map(sentHTML).join("")}</ol>
    </article>
    <section style="display:flex;flex-direction:column;gap:10px" id="rev">
      <div class="col-h"><h2>${ic("history")}${esc(LABELS.revisions)} ${DATA.revisions.length}</h2></div>
      <ul class="rev">${DATA.revisions.map(r => `<li><div class="rev-top"><span class="rev-v">${r.v}</span>${r.who === "agent" ? pv("draft", r.by, "sm") : `<span class="human-mini">${ic("user")}${esc(r.by)}</span>`}<span class="rev-at">${esc(r.at)}</span></div>
        <p>${esc(r.text)}</p>${r.diff ? `<div class="diff">${r.diff.map(([t, x]) => `<div class="${t}"><span>${t === "d" ? "−" : "+"}</span><span>${esc(x)}</span></div>`).join("")}</div>` : ""}</li>`).join("")}</ul>
    </section>`;
  if (s === "running") startStream(DATA.sentences[7].text[UI.lang]);
}

function paraHTML(doc, p) {
  const st = DATA.sentences.find(x => x.id === UI.active);
  const hl = st && st.cite && st.cite.para === p.id;
  const lang = doc.noEn ? "ko" : UI.srcLang;
  let t = esc(p[lang]);
  if (hl) { const k = esc(st.cite.hl[lang]); t = t.replace(k, `<mark>${k}</mark>`); }
  return `<div class="para${hl ? " is-hl" : ""}${p.warn ? " is-warn" : ""}" id="para-${p.id}"><span class="para-id">¶ ${esc(p.id)}${hl ? ` · 문장 ${DATA.sentences.indexOf(st) + 1}의 근거` : ""}${lang === "ko" && !doc.noEn ? pv("draft", "참고 번역", "sm") : ""}</span>${t}</div>`;
}
function srcDocHTML(doc, only) {
  return `<div class="src-doc"><div class="src-h"><b>${esc(doc.name)}</b><span class="loc">${esc(doc.loc)}</span>${pv("approved", `승격 · ${doc.approvedBy} · ${doc.approvedAt.slice(0, 10)}`, "sm")}</div>
    ${(only ? doc.paras.filter(p => p.id === only) : doc.paras).map(p => paraHTML(doc, p)).join("")}</div>`;
}
function renderSrc(scroll) {
  const s = S(), el = $("#dv-src");
  const head = `<div class="col-h"><h2>${ic("knowledge")}${esc(LABELS.source)}</h2><span class="col-note">승격된 문서만 근거로 사용</span></div>`;
  if (s === "loading") { el.innerHTML = head + sk(200) + sk(260); return; }
  if (s === "empty") { el.innerHTML = head + `<div class="empty"><span class="empty-ic">${ic("knowledge")}</span><h3>표시할 원문 없음</h3><p>초안을 고르면 연결된 근거 원문이 이곳에 나란히 열립니다.</p></div>`; return; }
  if (s === "error") { el.innerHTML = head + `<div class="empty"><span class="empty-ic">${ic("alert")}</span><h3>근거 원문을 불러오지 못했습니다</h3><p>${esc(DATA.error.message)} (${esc(DATA.error.code)}). 대조 체크가 잠겨 있습니다.</p><button class="btn" data-act="reload">${ic("retry")}${esc(LABELS.actions.reload)}</button></div>`; return; }
  el.innerHTML = head + DATA.sources.map(d => srcDocHTML(d)).join("");
  if (scroll) { const st = DATA.sentences.find(x => x.id === UI.active); const p = st && st.cite && $("#para-" + st.cite.para); if (p) el.scrollTo({ top: p.offsetTop - el.offsetTop - 90, behavior: "smooth" }); }
}
function openSheet(id) {
  const st = DATA.sentences.find(x => x.id === id), i = DATA.sentences.indexOf(st);
  const body = st.cite ? srcDocHTML(SRC[st.cite.doc], st.cite.para) : `<div class="noev">${pv("noev", "연결된 근거 없음")}<p>이 문장에는 근거 원문이 없습니다.</p></div>`;
  openModal(`${modalHead(`문장 ${i + 1}의 근거`)}
    <p style="font-weight:700">${esc(st.text[UI.lang])}</p>
    <div class="seg" role="group">${Object.keys(LABELS.srcLangs).map(k => `<button data-act="srclang" data-v="${k}" aria-pressed="${UI.srcLang === k}">${esc(LABELS.srcLangs[k])}</button>`).join("")}</div>
    <div class="sheet-src">${body}</div>
    ${st.must ? `<button class="chk" data-act="check" data-id="${st.id}" aria-pressed="${isChecked(st.id)}"${locked() || S() === "error" ? " disabled" : ""} style="justify-content:center;min-height:56px"><span class="box">${ic("check")}</span>${isChecked(st.id) ? esc(LABELS.checkDone) : esc(LABELS.checkTodo)}</button>` : ""}`);
  UI.sheet = id;
}

function renderBar() {
  const s = S(), A = LABELS.actions, g = gate(), ap = DATA.approval;
  const tag = `<span class="human-tag">${ic("user")}${esc(LABELS.humanOnly)}</span>`;
  const approveBtn = dis => `<button class="btn btn-primary" data-act="approve"${dis ? " disabled" : ""}>${ic("lock")}<span class="lbl-long">${esc(A.approve)}</span><span class="lbl-short">${esc(A.approveShort)}</span><span class="reauth">재로그인</span></button>`;
  const rr = dis => `<button class="btn btn-danger" data-act="reject"${dis ? " disabled" : ""}>${ic("x")}${esc(A.reject)}</button><button class="btn" data-act="revise"${dis ? " disabled" : ""}>${ic("edit")}<span class="lbl-long">${esc(A.revise)}</span><span class="lbl-short">${esc(A.reviseShort)}</span></button>`;
  let cap, acts;
  if (s === "approved") { cap = `${DATA.draft.id} ${LABELS.langs[UI.lang]}본이 확정되었습니다.`; acts = `${pv("approved", `${ap.by} · ${ap.at}`, "lg")}<a class="btn hb-hide-m" href="audit.html">${ic("audit")}감사 기록</a>`; }
  else if (s === "rejected") { cap = "반려 사유가 에이전트에게 전달되었습니다."; acts = `<button class="btn" data-act="undo">되돌리기</button>`; }
  else if (s === "running") { cap = "에이전트가 수정 중입니다. 끝나야 대조와 승인을 할 수 있습니다."; acts = `<button class="btn btn-danger" data-act="stop">${ic("stop")}${esc(A.stop)}</button>${approveBtn(true)}`; }
  else if (s === "error") { cap = "근거 원문 없이 승인할 수 없습니다."; acts = `<button class="btn" data-act="reload">${ic("retry")}<span class="lbl-long">${esc(A.reload)}</span><span class="lbl-short">다시</span></button>${rr(false)}${approveBtn(true)}`; }
  else if (s === "loading" || s === "empty") { cap = s === "empty" ? "검토할 초안이 없습니다." : "불러오는 중…"; acts = rr(true) + approveBtn(true); }
  else {
    const left = [g.done < g.total ? `원문 대조 ${g.total - g.done}건 남음` : "", g.noevPending ? `근거 없는 문장 ${g.noevPending}건 처리 필요` : ""].filter(Boolean).join(" · ");
    cap = g.ok ? `${LABELS.langs[UI.lang]}본 대조 완료 · 승인할 수 있습니다.` : `${left} · 끝나야 승인 버튼이 켜집니다.`;
    acts = rr(false) + approveBtn(!g.ok);
  }
  $("#human-bar").innerHTML = `<div class="hb-id">${tag}<span class="hb-cap">${esc(cap)}</span></div><div class="hb-actions">${acts}</div>`;
}

function startStream(text) {
  stopStream(); let i = 0; const el = $("#stream"); if (!el) return;
  streamT = setInterval(() => { i = Math.min(text.length, i + 1); el.textContent = text.slice(0, i); if (i >= text.length) { clearInterval(streamT); setTimeout(() => { if (S() === "running" && $("#stream")) startStream(text); }, 2200); } }, 55);
}
function stopStream() { if (streamT) clearInterval(streamT); streamT = null; }
function renderPage() { stopStream(); const sc = $("#dv-doc").scrollTop; renderHead(); renderDoc(); renderSrc(); renderBar(); $("#dv-doc").scrollTop = sc; }
function refresh() { const sc = $("#dv-doc").scrollTop, ss = $("#dv-src").scrollTop; renderHead(); renderDoc(); renderSrc(); renderBar(); $("#dv-doc").scrollTop = sc; $("#dv-src").scrollTop = ss; }

function openApprove() {
  const d = DATA.draft;
  openPinModal({
    title: "재로그인 필요", icon: "lock", flow: true, act: "approve-ok", label: "확인 후 승인", labelIcon: "user-check",
    alert: { title: `고위험 승인 · ${d.type} ${LABELS.langs[UI.lang]}본`, text: `원문 대조 ${gate().total}건 완료. 승인하면 ${d.id} ${d.version}이(가) 효력을 갖고 현장에 배포됩니다.` }
  });
}
function openReject() {
  openReasonModal({
    title: "반려 사유", chips: ["원문과 수치 불일치", "경고 문구 약함", "번역 오류", "절차 누락"],
    fieldId: "reason", fieldLabel: "사유 (필수 · 에이전트에게 전달되고 감사 기록에 남습니다)",
    error: "사유를 입력하세요.", act: "reject-ok", label: "반려"
  });
}
function openRevise() {
  const st = DATA.sentences.find(x => x.id === UI.active), i = DATA.sentences.indexOf(st);
  openReviseModal({
    lead: "에이전트가 요청을 반영해 새 버전을 만듭니다. 새 버전도 초안이며 대조 체크는 초기화됩니다.",
    target: `문장 ${i + 1}: ${st.text[UI.lang]}`, placeholder: "예: 측정 후 결과를 기록하는 단계를 추가"
  });
}

const PAGE_ACTS = {
  sent: el => { UI.active = el.dataset.id; if (isPhone()) { refresh(); openSheet(UI.active); } else { refresh(); renderSrc(true); } },
  check: el => { if (el.disabled) return; const k = ckKey(el.dataset.id); UI.checks[k] = !UI.checks[k]; refresh(); if (UI.sheet && $("#modal-root .modal")) openSheet(UI.sheet); },
  lang: el => { UI.lang = el.dataset.v; refresh(); },
  srclang: el => { UI.srcLang = el.dataset.v; refresh(); if ($("#modal-root .modal") && UI.sheet) openSheet(UI.sheet); },
  "noev-remove": el => { UI.noev[el.dataset.id] = "removed"; refresh(); },
  "noev-keep": el => { UI.noev[el.dataset.id] = "kept"; refresh(); toast("사람 판단으로 유지 · 감사 기록에 남았습니다", "user"); },
  "noev-undo": el => { delete UI.noev[el.dataset.id]; refresh(); },
  approve: el => { if (!el.disabled) openApprove(); },
  "approve-ok": () => { if ($("#pin").value.length < 4) { $("#pin-err").hidden = false; return; } closeModal(); setState("approved"); toast(`${DATA.draft.id} 승인 · 감사 기록에 남았습니다`, "user-check"); },
  reject: el => { if (!el.disabled) openReject(); },
  reason: el => { $("#reason").value = el.dataset.v; },
  "reject-ok": () => { const v = $("#reason").value.trim(); if (!v) { $("#reason-err").hidden = false; return; } UI.rejectReason = v; closeModal(); setState("rejected"); toast("반려됨 · 사유가 에이전트에게 전달되었습니다", "x"); },
  revise: el => { if (!el.disabled) openRevise(); },
  "revise-ok": () => { closeModal(); UI.checks = {}; setState("running"); toast("수정 요청 전송 · 에이전트가 새 버전을 작성합니다", "edit"); },
  stop: () => { setState("normal"); toast("사람이 수정 작업을 중단했습니다", "stop"); },
  reload: () => { setState("loading"); setTimeout(() => setState("normal"), 900); },
  undo: () => setState("normal")
};
onModalClose(() => { UI.sheet = null; });
document.addEventListener("keydown", e => { if ((e.key === "Enter" || e.key === " ") && e.target.matches(".sent")) { e.preventDefault(); PAGE_ACTS.sent(e.target); } });

initTheme(); readURL();
renderShell([LABELS.nav.draft, DATA.draft.id]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
