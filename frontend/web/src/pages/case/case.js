// 케이스 작업 · 에이전트 콘솔 — 페이지 로직
import { injectSprite } from "../../components/icons/sprite.js";
import { mountLayout } from "../../components/layout/app-layout.js";
import { renderDemo } from "../../components/layout/demo-panel.js";
import { renderShell } from "../../components/layout/shell.js";
import { closeModal } from "../../components/modals/modal.js";
import { toast } from "../../components/toast.js";
import { bindActs } from "../../lib/acts.js";
import { $, esc, ic, pv } from "../../lib/dom.js";
import { APP, DATA, LABELS, readURL, setState } from "../../lib/state.js";
import { initTheme } from "../../lib/theme.js";
import "../../data/case.js";
import { view, outside, humanBar } from "./view.js";
import { openPinModal } from "../../components/modals/pin-modal.js";
import { openReasonModal } from "../../components/modals/reason-modal.js";
import { openReviseModal } from "../../components/modals/revise-modal.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: case ================= */
const UI = { tab: "progress", ctxOpen: false, raw: {} };
let streamT = null;
const SRC_PV = { manual: ["approved", "승격 문서"], history: ["approved", "승인된 기록"], sensor: ["untrusted", "센서값"] };
const SRC_IC = { manual: "knowledge", history: "history", sensor: "activity" };
const confLabel = c => c >= 50 ? "높음" : c >= 20 ? "중간" : "낮음";
const sk = (h, w) => `<div class="sk" style="height:${h}px;width:${w || "100%"}"></div>`;

function stepsFor(s) {
  const T = DATA.timeline;
  if (s === "running") return [...T.slice(0, 7), { ...T[7], status: "running", dur: "…", streaming: true }];
  if (s === "error") return T.slice(0, 5);
  if (s === "blocked") return [...T, ...DATA.blockedSteps];
  return T;
}

function renderHead(s) {
  const c = DATA.case;
  if (s === "loading") { $("#case-head").innerHTML = `${sk(18, "220px")}${sk(34, "70%")}${sk(16, "50%")}`; return; }
  const pill = {
    normal: `<span class="runpill rp-wait">${ic("clock")}초안 3건 · 사람 결정 대기</span>`,
    running: `<span class="runpill rp-run"><span class="spin"></span>에이전트 실행 중 · 8단계째</span>`,
    blocked: `<span class="runpill rp-blk">${ic("ban")}차단 발생 · 검토 필요</span>`,
    approved: `<span class="runpill rp-ok">${ic("user-check")}조치 계획 승인됨</span>`,
    rejected: `<span class="runpill rp-err">${ic("x")}반려됨 · 에이전트 재작업 대기</span>`,
    error: `<span class="runpill rp-err">${ic("alert")}실행 오류</span>`,
    empty: `<span class="runpill rp-wait">${ic("inbox")}신호 대기</span>`
  }[s];
  const alert = s === "blocked" ? `<div class="alert alert-blocked" role="alert">${ic("ban")}<div><b>정책 차단 2건 · 주입 공격 의심 1건</b><p>첨부 사진의 OCR 텍스트에 든 지시로 에이전트가 발주 제출을 시도했고 게이트웨이가 막았습니다. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>`
    : s === "error" ? `<div class="alert alert-error" role="alert">${ic("alert")}<div><b>에이전트 실행이 중단되었습니다 · ${esc(DATA.error.code)}</b><p>${esc(DATA.error.message)}. 지금까지의 기록은 감사 로그에 보존되어 있습니다.</p></div></div>` : "";
  const empty = s === "empty";
  $("#case-head").innerHTML = `
    <div class="ch-row">
      <button class="btn btn-sm ctx-toggle" data-act="ctx-open">${ic("panel")}${esc(LABELS.context)}</button>
      <span class="ch-id">${empty ? "CASE-NEW" : esc(c.id)}</span>
      ${empty ? "" : `<span class="sev sev-${c.severity}">${c.severity}</span>`}
      ${pill}
    </div>
    <h1 class="ch-title">${empty ? "새 케이스 · 연결된 신호 없음" : esc(c.title)}</h1>
    ${empty ? "" : `<div class="ch-meta">
      <span>${esc(LABELS.target)} <b>${esc(DATA.target.id)}</b></span>
      <span>${esc(LABELS.agent)} <b>${esc(c.agent)}</b></span>
      <span class="m-hide">${esc(LABELS.sandbox)} <b>${esc(c.sandbox)}</b></span>
      <span class="m-hide">시작 <b>${esc(c.openedAt)}</b></span>
      <span class="m-hide">경과 <b>${esc(c.elapsed)}</b></span>
    </div>`}
    ${alert}`;
}

function renderTabs(s) {
  const n = s === "loading" || s === "empty" ? "" : stepsFor(s).length;
  const t = (k, l, extra) => `<button class="ctab" role="tab" data-act="tab" data-v="${k}" aria-selected="${UI.tab === k}">${esc(l)}${extra !== "" && extra != null ? `<small>${extra}</small>` : ""}</button>`;
  $("#case-tabs").innerHTML = t("ctx", LABELS.context) + t("progress", LABELS.progress, n) + t("concl", LABELS.conclusion, s === "loading" || s === "empty" || s === "error" ? "" : DATA.hypotheses.length);
  document.querySelectorAll(".col").forEach(c => c.classList.toggle("on", c.dataset.pane === UI.tab));
}

function renderCtx(s) {
  const close = `<button class="icon-btn drawer-close" data-act="ctx-close" aria-label="닫기">${ic("x")}</button>`;
  const head = `<div class="col-h"><h2>${ic("layers")}${esc(LABELS.context)}</h2>${close}</div>`;
  if (s === "loading") { $("#col-ctx").innerHTML = head + sk(190) + sk(120) + sk(160) + sk(200); return; }
  if (s === "empty") { $("#col-ctx").innerHTML = head + `<div class="empty"><span class="empty-ic">${ic("inbox")}</span><h3>연결된 신호가 없습니다</h3><p>인박스에서 신호를 고르거나 직접 입력하면 맥락이 여기에 채워집니다.</p><a class="btn" href="inbox.html">${ic("inbox")}인박스 열기</a></div>`; return; }
  const sg = DATA.signal, t = DATA.target, at = DATA.attachments[0], inj = s === "blocked";
  $("#col-ctx").innerHTML = head + `
    <div class="pvbox pvbox-untrusted">
      <div class="pvbox-head"><span class="sec-t">${esc(LABELS.signal)} · ${esc(sg.kind)}</span>${pv("untrusted", null, "sm")}</div>
      <div class="pvbox-body">
        <div class="sig-code">${esc(sg.code)}</div>
        <div class="sig-msg">${esc(sg.message)}</div>
        <dl class="kv"><dt>출처</dt><dd>${esc(sg.source)}</dd><dt>수신</dt><dd class="mono">${esc(sg.receivedAt)}</dd></dl>
        <pre class="raw">${esc(sg.raw)}</pre>
      </div>
    </div>
    <div class="pvbox pvbox-untrusted">
      <div class="pvbox-head"><span class="sec-t">${esc(LABELS.attachment)} · ${esc(at.kind)}</span>${pv("untrusted", null, "sm")}</div>
      <div class="pvbox-body">
        <div class="att"><span class="att-thumb">${ic("camera")}</span><div><b>${esc(at.name)}</b><p>${esc(at.note)}</p><span class="unused">${ic("ban")}판단 근거로 사용 안 함</span></div></div>
        ${inj ? `<div class="inj">${pv("blocked", "주입 의심", "sm")}<q>${esc(at.injection)}</q></div>` : ""}
      </div>
    </div>
    <section style="display:flex;flex-direction:column;gap:10px">
      <div class="sec-t">${esc(LABELS.target)}<a href="map.html?target=${esc(t.id)}" class="cite-link">맵에서 보기 ${ic("chev")}</a></div>
      <div class="pvbox"><div class="pvbox-body" style="display:flex;flex-direction:column;gap:8px">
        <b style="font-size:var(--fs-md)">${esc(t.name)}</b>
        <div class="path">${t.path.map(esc).join(ic("chev"))}</div>
        <dl class="kv" style="margin:0"><dt>ID</dt><dd class="mono">${esc(t.id)}</dd><dt>모델</dt><dd>${esc(t.model)}</dd><dt>설치</dt><dd class="mono">${esc(t.installed)}</dd><dt>${esc(LABELS.doc)}</dt><dd>${esc(t.manual.name)} (${esc(t.manual.lang)})</dd></dl>
        ${pv("approved", `${t.manual.approvedBy} · ${t.manual.approvedAt}`, "sm")}
      </div></div>
    </section>
    <section style="display:flex;flex-direction:column;gap:10px">
      <div class="sec-t">${esc(LABELS.sensor)} · 24h${pv("untrusted", null, "sm")}</div>
      <div class="sens">${DATA.sensors.map(x => `<div class="sens-row ${x.state}">
        <span class="sens-l">${esc(x.label)}</span><span class="sens-v">${esc(x.value)}<small>${esc(x.unit)}</small></span>
        <span class="sens-n"><span>${esc(x.note)}</span>${x.state === "suspect" ? pv("sensor", null, "sm") : ""}</span></div>`).join("")}</div>
    </section>
    <section style="display:flex;flex-direction:column;gap:10px">
      <div class="sec-t">${esc(LABELS.history)} · 90일</div>
      <ul class="hist">${DATA.history.map(h => `<li><time>${esc(h.date)}</time><b>${esc(h.text)}</b><span>${pv("approved", h.by, "sm")}</span></li>`).join("")}</ul>
    </section>`;
}

const STATUS_IC = { success: "check", failed: "x", blocked: "ban" };
function stepHTML(st, i) {
  const agent = st.kind === "judge" || st.kind === "draft" || st.kind === "plan";
  const cls = st.status === "running" ? "st-running" : st.status === "blocked" ? "st-blocked" : st.status === "failed" ? "st-failed" : agent ? "st-agent" : "";
  const dotIc = st.status === "blocked" ? "ban" : st.status === "failed" ? "x" : { plan: "plan", tool: st.retry || /재시도/.test(st.title) ? "retry" : "tool", judge: "judge", draft: "draft" }[st.kind];
  const statusB = `<span class="status s-${st.status}">${st.status === "running" ? '<span class="spin"></span>' : ic(STATUS_IC[st.status])}${esc(LABELS.status[st.status])}</span>`;
  const sens = st.sensors ? `<div class="mini-sens">${DATA.sensors.map(x => `<div class="ms ${x.state}"><span>${esc(x.label)}</span><b>${esc(x.value)} ${esc(x.unit)}</b>${x.state === "suspect" ? pv("sensor", null, "sm") : ""}</div>`).join("")}</div>` : "";
  const pol = st.policy ? `<div style="display:flex;gap:8px;flex-wrap:wrap">${pv("blocked")}${st.injection ? pv("untrusted", "출처: memo_line3.jpg") : ""}</div><dl class="policy"><dt>정책</dt><dd>${esc(st.policy.name)}</dd><dt>규칙</dt><dd>${esc(st.policy.rule)}</dd></dl>` : "";
  const draftLinks = st.kind === "draft" ? `<div style="display:flex;gap:6px;flex-wrap:wrap">${DATA.drafts.map(d => pv("draft", d.type, "sm")).join("")}</div>` : "";
  const rawOpen = UI.raw[i];
  const raw = st.raw ? `<button class="raw-btn" data-act="raw" data-i="${i}" aria-expanded="${!!rawOpen}">${ic("code")}응답 원문 ${rawOpen ? "접기" : "보기"}</button>${rawOpen ? `<pre class="raw" style="margin:0">${esc(st.raw)}</pre>` : ""}` : "";
  return `<li class="step ${cls}">
    <span class="dot">${ic(dotIc)}</span>
    <div class="card">
      <div class="sc-head"><span class="kind">${LABELS.kinds[st.kind]}</span><span class="sc-title">${esc(st.title)}</span>
        <span class="sc-meta">${statusB}<span>${esc(st.time)}</span><span>${esc(st.dur)}</span></span></div>
      ${st.tool ? `<div class="call"><em>${esc(st.tool)}</em>(${esc(st.args)})</div>` : ""}
      ${pol}
      <p class="sc-body">${st.streaming ? `<span id="stream"></span><span class="caret"></span>` : esc(st.body)}</p>
      ${st.list ? `<ol class="sc-list">${st.list.map(x => `<li>${esc(x)}</li>`).join("")}</ol>` : ""}
      ${sens}${draftLinks}
      ${st.decision ? `<div class="decision">${ic("chev")}다음 행동: ${esc(st.decision)}</div>` : ""}
      ${raw}
    </div></li>`;
}

function renderTimeline(s) {
  const head = (stats) => `<div class="col-h"><h2>${ic("bot")}에이전트 ${esc(LABELS.progress)}</h2>${stats || ""}</div>`;
  if (s === "loading") { $("#col-tl").innerHTML = head() + [1, 2, 3, 4].map(() => `<div style="display:grid;grid-template-columns:44px 1fr;gap:14px"><div class="sk" style="width:44px;height:44px;border-radius:50%"></div>${sk(110)}</div>`).join(""); return; }
  if (s === "empty") { $("#col-tl").innerHTML = head() + `<div class="empty"><span class="empty-ic">${ic("bot")}</span><h3>에이전트가 아직 시작하지 않았습니다</h3><p>신호가 연결되면 계획, 도구 호출, 판단이 이 타임라인에 순서대로 쌓입니다.</p></div>`; return; }
  const st = stepsFor(s);
  const n = k => st.filter(x => k(x)).length;
  const stats = `<div class="tl-stats"><span class="tl-stat">${ic("plan")}${st.length}단계</span><span class="tl-stat">${ic("tool")}도구 ${n(x => x.kind === "tool")}</span>${n(x => x.status === "failed") ? `<span class="tl-stat" style="color:var(--high-tx)">${ic("x")}실패 ${n(x => x.status === "failed")}</span>` : ""}${n(x => x.status === "blocked") ? `<span class="tl-stat" style="color:var(--pv-bk-fg)">${ic("ban")}차단 ${n(x => x.status === "blocked")}</span>` : ""}</div>`;
  let tail = "";
  if (s === "running") tail = `<div class="next-ghost"><i></i><span>다음: 원인 가설 순위 판단 → 초안 생성</span></div>`;
  if (s === "error") tail = `<div class="alert alert-error">${ic("alert")}<div><b>${esc(DATA.error.at)} · 도구 응답 대기 중 연결 끊김</b><p>에이전트 런타임이 ${esc(DATA.error.code)}를 반환했습니다. 재실행하면 6단계부터 이어서 진행합니다.</p><div style="margin-top:10px"><button class="btn btn-sm" data-act="rerun">${ic("retry")}${esc(LABELS.actions.rerun)}</button></div></div></div>`;
  $("#col-tl").innerHTML = head(stats) + `<ol class="tl">${st.map(stepHTML).join("")}</ol>` + tail;
  if (s === "running") startStream(st[st.length - 1].body);
}
function startStream(text) {
  stopStream(); let i = 0; const el = $("#stream"); if (!el) return;
  streamT = setInterval(() => { i = Math.min(text.length, i + 2); el.textContent = text.slice(0, i); if (i >= text.length) { clearInterval(streamT); setTimeout(() => { if (APP.state === "running" && $("#stream")) { el.textContent = ""; startStream(text); } }, 2400); } }, 45);
}
function stopStream() { if (streamT) clearInterval(streamT); streamT = null; }

function citeHTML(c) {
  const [t, tag] = SRC_PV[c.src];
  return `<div class="cite"><div class="cite-top">${ic(SRC_IC[c.src])}<span>${esc(c.doc)}</span><span class="cite-loc">${esc(c.loc)}</span></div>
    <blockquote class="cite-q">“${esc(c.quote)}”</blockquote>
    <div class="cite-foot">${pv(t, tag, "sm")}${c.src === "manual" ? `<a class="cite-link" href="draft.html?doc=vfd-22&amp;loc=${encodeURIComponent(c.loc)}">원문 위치 ${ic("ext")}</a>` : ""}</div></div>`;
}
function hypHTML(h, provisional) {
  return `<article class="hyp">
    <div class="hyp-head"><span class="hyp-id">${h.id}</span><span class="hyp-t">${esc(h.title)}</span>
      <span class="hyp-c">${provisional ? "··" : h.conf + "%"}<small>확신도 ${provisional ? "집계 중" : confLabel(h.conf)}</small></span></div>
    <div class="bar" aria-label="확신도 ${h.conf}%"><i style="width:${provisional ? 0 : h.conf}%"></i></div>
    ${h.summary ? `<p class="hyp-sum">${esc(h.summary)}</p>` : ""}
    <div class="sec-t">근거 ${h.cites.length}</div>
    <div class="cites">${h.cites.map(citeHTML).join("")}</div>
    ${h.counter ? `<div class="counter">${ic("alert")}<span>반대 근거 · ${esc(h.counter)}</span></div>` : ""}
    ${h.next ? `<div class="nextact">${ic("chev")}<span>확인 방법 · ${esc(h.next)}</span></div>` : ""}
  </article>`;
}
function renderConcl(s) {
  const head = `<div class="col-h"><h2>${ic("judge")}${esc(LABELS.conclusion)}</h2>${s === "loading" || s === "empty" ? "" : pv("draft", "효력 없음", "sm")}</div>`;
  if (s === "loading") { $("#col-cc").innerHTML = head + sk(260) + sk(180) + sk(140); return; }
  if (s === "empty") { $("#col-cc").innerHTML = head + `<div class="empty"><span class="empty-ic">${ic("judge")}</span><h3>결론 없음</h3><p>에이전트가 판단을 마치면 원인 가설과 근거, 초안 목록이 표시됩니다.</p></div>`; return; }
  if (s === "error") { $("#col-cc").innerHTML = head + `<div class="empty"><span class="empty-ic">${ic("alert")}</span><h3>실행이 중단되어 결론이 없습니다</h3><p>부분 결과로는 가설을 만들지 않습니다. 재실행 후 다시 확인하세요.</p></div>`; return; }
  const run = s === "running";
  const hyps = run ? DATA.hypotheses.slice(0, 2).map(h => hypHTML(h, true)).join("") : DATA.hypotheses.map(h => hypHTML(h)).join("");
  const refusal = run ? "" : DATA.refusals.map(r => `<div class="noev">${pv("noev", "답변 거부", "sm")}<s>${esc(r.claim)}</s><p>${esc(r.reason)}</p></div>`).join("");
  const ap = DATA.approval;
  const drafts = run ? `<div class="pvbox pvbox-draft"><div class="pvbox-body" style="display:flex;gap:10px;align-items:center;font-weight:700;color:var(--tx-2)"><span class="spin" style="color:var(--pv-dr-fg)"></span>판단이 끝나면 초안이 생성됩니다</div></div>`
    : `<ul class="drafts">${DATA.drafts.map(d => {
        const isAp = s === "approved" && d.id === ap.draftId;
        return `<li><a class="dr${isAp ? " is-ap" : ""}" href="draft.html?id=${d.id}">
          <span><span class="dr-type">${esc(d.id)} · ${esc(d.type)}</span><br><span class="dr-t">${esc(d.title)}</span></span>${ic("chev")}
          <span class="dr-tags">${isAp ? pv("approved", `${ap.by} · ${ap.at.slice(11)}`, "sm") : pv("draft", null, "sm")}<span class="sev sev-${d.risk}">${d.risk}</span>${d.reauth && !isAp ? `<span class="reauth reauth-o">${ic("lock")}재로그인</span>` : ""}</span></a></li>`; }).join("")}</ul>`;
  $("#col-cc").innerHTML = head + `
    <div class="sec-t">${esc(LABELS.hypothesis)} ${run ? "· 잠정" : DATA.hypotheses.length}<span style="font-weight:600">확신도는 에이전트 추정치</span></div>
    ${hyps}${refusal}
    <div class="sec-t" style="margin-top:6px">생성된 ${esc(LABELS.draft)} ${run ? "" : DATA.drafts.length}</div>
    ${drafts}`;
}

function renderBar(s) {
  const A = LABELS.actions, ap = DATA.approval;
  const tag = `<span class="human-tag">${ic("user")}${esc(LABELS.humanOnly)}</span>`;
  let cap = "에이전트는 이 영역을 조작할 수 없습니다. 승인은 사람만 할 수 있습니다.", acts = "";
  const approveBtn = dis => `<button class="btn btn-primary" data-act="approve"${dis ? " disabled" : ""}>${ic("lock")}<span class="lbl-long">${esc(A.approve)}</span><span class="lbl-short">${esc(A.approveShort)}</span><span class="reauth">재로그인</span></button>`;
  const std = dis => `<button class="btn btn-danger" data-act="reject"${dis ? " disabled" : ""}>${ic("x")}${esc(A.reject)}</button>
    <button class="btn" data-act="revise"${dis ? " disabled" : ""}>${ic("edit")}<span class="lbl-long">${esc(A.revise)}</span><span class="lbl-short">${esc(A.reviseShort)}</span></button>
    <a class="btn hb-hide-m" href="draft.html?id=DRF-0141"${dis ? ' aria-disabled="true"' : ""}>${ic("draft")}${esc(A.review)}</a>${approveBtn(dis)}`;
  if (s === "normal" || s === "blocked") acts = std(false);
  if (s === "blocked") cap = "차단 내역을 확인한 뒤 결정하세요. 발주서는 별도 승인 대상입니다.";
  if (s === "loading" || s === "empty") { acts = std(true); cap = s === "empty" ? "검토할 초안이 없습니다." : "불러오는 중…"; }
  if (s === "running") { cap = "에이전트 실행이 끝나야 승인할 수 있습니다."; acts = `<button class="btn btn-danger" data-act="stop">${ic("stop")}${esc(A.stop)}</button><button class="btn" disabled>${ic("edit")}<span class="lbl-long">${esc(A.revise)}</span><span class="lbl-short">${esc(A.reviseShort)}</span></button>${approveBtn(true)}`; }
  if (s === "error") { cap = "실행이 중단되었습니다. 재실행 여부는 사람이 결정합니다."; acts = `<button class="btn" data-act="rerun">${ic("retry")}${esc(A.rerun)}</button>${approveBtn(true)}`; }
  if (s === "approved") { cap = `${ap.draftId} 조치 계획이 확정되었습니다. 발주서는 아직 초안입니다.`; acts = `${pv("approved", `${ap.by} · ${ap.at}`, "lg")}<a class="btn hb-hide-m" href="audit.html?case=${esc(DATA.case.id)}">${ic("audit")}감사 기록</a>`; }
  if (s === "rejected") { cap = `반려 사유: ${UI.rejectReason || "근거 부족"}`; acts = `<span class="pv pv-lg" style="border-color:var(--crit);color:var(--crit-tx);background:var(--crit-dim)">${ic("x")}반려 · ${esc(DATA.shell.user.role)} ${esc(DATA.shell.user.id)}</span><button class="btn" data-act="undo">되돌리기</button>`; }
  $("#human-bar").innerHTML = `<div class="hb-id">${tag}<span class="hb-cap">${esc(cap)}</span></div><div class="hb-actions">${acts}</div>`;
}

function renderPage() {
  stopStream();
  const s = APP.state;
  renderHead(s); renderTabs(s); renderCtx(s); renderTimeline(s); renderConcl(s); renderBar(s);
  setCtx(UI.ctxOpen);
}
function setCtx(open) { UI.ctxOpen = open; $("#col-ctx").classList.toggle("open", open); $("#ctx-bd").hidden = !open; }

function openApprove() {
  const d = DATA.drafts[0];
  openPinModal({
    title: "재로그인 필요", icon: "lock", flow: true, act: "approve-ok", label: "확인 후 승인", labelIcon: "user-check",
    alert: { title: `고위험 승인 · ${d.type}`, text: `승인하면 ${d.id}이(가) 효력을 갖고 작업 지시로 배포됩니다. 승인자 본인 확인이 필요합니다.` }
  });
}
function openReject() {
  openReasonModal({
    title: "반려 사유", chips: ["근거 부족", "조치 순서 오류", "수량·금액 확인 필요", "현장 상황과 다름"],
    fieldId: "reason", fieldLabel: "사유 (필수 · 에이전트에게 전달되고 감사 기록에 남습니다)",
    error: "사유를 5자 이상 입력하세요.", act: "reject-ok", label: "반려"
  });
}
function openRevise() {
  openReviseModal({
    lead: "요청 내용은 에이전트에게 전달되고, 에이전트가 초안을 다시 작성합니다. 결과는 다시 초안 상태로 돌아옵니다.",
    placeholder: "예: 절연 측정 결과를 받은 뒤 교체 여부를 결정하도록 순서 변경"
  });
}

const PAGE_ACTS = {
  tab: el => { UI.tab = el.dataset.v; renderTabs(APP.state); $("#col-" + { ctx: "ctx", progress: "tl", concl: "cc" }[UI.tab]).scrollTop = 0; },
  "ctx-open": () => setCtx(true),
  "ctx-close": () => setCtx(false),
  raw: el => { const i = +el.dataset.i; UI.raw[i] = !UI.raw[i]; const sc = $("#col-tl").scrollTop; renderTimeline(APP.state); $("#col-tl").scrollTop = sc; },
  approve: el => { if (!el.disabled) openApprove(); },
  "approve-ok": () => { const v = $("#pin").value; if (v.length < 4) { $("#pin-err").hidden = false; return; } closeModal(); setState("approved"); toast(`${DATA.approval.draftId} 승인 · 감사 기록에 남았습니다`, "user-check"); },
  reject: el => { if (!el.disabled) openReject(); },
  reason: el => { $("#reason").value = el.dataset.v; },
  "reject-ok": () => { const v = $("#reason").value.trim(); if (v.length < 2) { $("#reason-err").hidden = false; return; } UI.rejectReason = v; closeModal(); setState("rejected"); toast("반려됨 · 사유가 에이전트에게 전달되었습니다", "x"); },
  revise: el => { if (!el.disabled) openRevise(); },
  "revise-ok": () => { closeModal(); setState("running"); toast("수정 요청 전송 · 에이전트가 초안을 다시 작성합니다", "edit"); },
  stop: () => { setState("error"); toast("사람이 실행을 중단했습니다", "stop"); },
  rerun: () => { setState("running"); toast("에이전트 재실행", "retry"); },
  undo: () => setState("normal")
};

initTheme(); readURL();
renderShell([LABELS.case, DATA.case.id]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
