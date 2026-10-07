// 홈 · 에이전트 콘솔 — 페이지 로직
import { injectSprite } from "../../components/icons/sprite.js";
import { mountLayout } from "../../components/layout/app-layout.js";
import { renderDemo } from "../../components/layout/demo-panel.js";
import { renderShell } from "../../components/layout/shell.js";
import { bindActs } from "../../lib/acts.js";
import { $, count, esc, ic, pv } from "../../lib/dom.js";
import { APP, DATA, LABELS, readURL, setState } from "../../lib/state.js";
import { initTheme } from "../../lib/theme.js";
import "../../data/index.js";
import { view, outside, humanBar } from "./view.js";

// 셸 요소가 있어야 아래 최상위 코드가 DOM 을 만질 수 있다
mountLayout({ view, outside, humanBar });
injectSprite();

/* ================= PAGE: home ================= */
const sk = (h, w) => `<div class="sk" style="height:${h}px;width:${w || "100%"}"></div>`;
const head = (k, icon, href) => `<a class="kc-h" href="${href}"><h2>${ic(icon)}${esc(LABELS.cards[k])}</h2>${ic("chev")}</a>`;
const emptyRow = t => `<div class="kc-empty">${ic("check")}${esc(t)}</div>`;

function cardApprovals(s) {
  const A = DATA.approvals;
  let items = A.items, count = A.count, reauth = A.reauth;
  if (s === "approved") { items = A.items.filter(x => x.id !== DATA.recentDecision.id); count = items.length; reauth = items.filter(x => x.reauth).length; }
  if (s === "empty") { items = []; count = 0; reauth = 0; }
  const done = s === "approved" ? `<div class="kc-tags">${pv("approved", `방금 ${DATA.recentDecision.id} ${DATA.recentDecision.type} · ${DATA.recentDecision.by} · ${DATA.recentDecision.at}`, "sm")}</div>` : "";
  return `<section class="kcard k-ap">${head("approvals", "approvals", "approvals.html")}
    <div class="kc-num"><b>${count}</b><span>재로그인 필요 ${reauth}${items.length ? ` · 최장 대기 ${esc(A.oldest)}` : ""}</span></div>${done}
    ${items.length ? `<ul class="rows">${items.map(x => `<li><a class="row" href="${x.href}"><span><span class="row-s">${esc(x.id)} · ${esc(x.type)} · ${esc(x.agent)}</span><span class="row-t">${esc(x.title)}</span></span>
      <span class="row-r"><span class="row-w${x.old ? " old" : ""}">${ic("clock")} ${esc(x.wait)}</span></span>
      <span class="row-tags">${pv("draft", null, "sm")}<span class="sev sev-${x.risk}">${x.risk}</span>${x.reauth ? `<span class="reauth reauth-o">${ic("lock")}재로그인</span>` : ""}</span></a></li>`).join("")}</ul>` : emptyRow("승인을 기다리는 초안이 없습니다")}
  </section>`;
}
function cardBlocked(s) {
  const B = DATA.blocked;
  let items = s === "empty" ? [] : s === "blocked" ? [DATA.blockedExtra, ...B.items] : B.items;
  return `<section class="kcard k-bk${s === "blocked" ? " is-alert" : ""}">${head("blocked", "ban", "audit.html?filter=blocked")}
    <div class="kc-num"><b>${items.length}</b><span>${esc(B.window)} · 주입 의심 ${items.filter(x => x.injection).length}</span></div>
    ${items.length ? `<ul class="rows">${items.map(x => `<li><a class="row" href="audit.html?filter=blocked"><span><span class="row-s">${esc(x.t)} · ${esc(x.caseId)}</span><span class="row-t mono">${esc(x.tool)}</span></span><span></span>
      <span class="row-tags">${pv("blocked", null, "sm")}${x.injection ? pv("untrusted", "주입 의심", "sm") : ""}</span><span class="row-s" style="grid-column:1/-1;margin:0">${esc(x.why)}</span></a></li>`).join("")}</ul>` : emptyRow("차단된 시도가 없습니다")}
  </section>`;
}
function cardCases(s) {
  let items = DATA.cases.items.map(x => ({ ...x }));
  if (s === "running") items.forEach(x => { x.status = "running"; x.note = x.id.endsWith("014") ? "수정 요청 반영 중" : x.note; });
  if (s === "blocked") items[0] = { ...items[0], status: "blocked", note: "정책 차단 2건 · 검토 필요" };
  if (s === "empty") items = [];
  const st = { running: `<span class="rp rp-run"><span class="spin"></span>실행 중</span>`, wait: `<span class="rp rp-wait">${ic("user")}사람 결정 대기</span>`, blocked: `<span class="rp rp-blk">${ic("ban")}차단</span>` };
  return `<section class="kcard k-case">${head("cases", "case", "case.html")}
    <div class="kc-num"><b>${items.length}</b><span>실행 중 ${items.filter(x => x.status === "running").length} · 대기 ${items.filter(x => x.status === "wait").length}</span></div>
    ${items.length ? `<ul class="rows">${items.map(x => `<li><a class="row" href="case.html?id=${x.id}"><span><span class="row-s">${esc(x.id)}</span><span class="row-t">${esc(x.title)}</span></span><span class="row-r"><span class="sev sev-${x.sev}">${x.sev}</span></span>
      <span class="row-tags">${st[x.status]}<span class="row-s" style="margin:0;align-self:center">${esc(x.note)}</span></span></a></li>`).join("")}</ul>` : emptyRow("진행 중인 케이스가 없습니다")}
  </section>`;
}
function cardSignals(s) {
  const G = DATA.signals, z = s === "empty";
  return `<section class="kcard k-sig">${head("signals", "inbox", "inbox.html")}
    <div class="kc-num"><b>${z ? 0 : G.count}</b><span>${esc(G.window)}</span></div>
    <div class="kc-tags">${pv("untrusted", "에이전트가 검증 전", "sm")}</div>
    <div class="kinds">${G.kinds.map(([k, l, n]) => { const v = z ? 0 : n; return `<div class="kind-t${v ? "" : " zero"}"><span>${ic(LABELS.kindIcon[k])}${esc(l)}</span><b>${v}</b></div>`; }).join("")}</div>
    ${z ? emptyRow("새 신호가 없습니다") : `<ul class="rows">${G.latest.map(x => `<li><a class="row" href="inbox.html"><span><span class="row-s">${esc(x.t)} · ${esc(x.kind)} · ${esc(x.src)}</span><span class="row-t">${esc(x.title)}</span></span>${ic("chev")}</a></li>`).join("")}</ul>`}
  </section>`;
}
function cardKnowledge(s) {
  const K = DATA.knowledge;
  if (s === "error") return `<section class="kcard k-kn">${head("knowledge", "knowledge", "knowledge.html")}
    <div class="alert alert-error kc-err">${ic("alert")}<div><b>커버리지를 불러오지 못했습니다 · 503</b><p>지식 저장소 응답 없음. 다른 카드는 정상입니다.</p><div style="margin-top:10px"><button class="btn btn-sm" data-act="retry">${ic("retry")}다시 시도</button></div></div></div></section>`;
  const r = s === "empty" ? { ready: 0, review: 0, none: K.total } : K;
  const pct = Math.round(r.ready / K.total * 100);
  const w = n => (n / K.total * 100).toFixed(1) + "%";
  return `<section class="kcard k-kn">${head("knowledge", "knowledge", "knowledge.html")}
    <div class="kc-num"><b>${pct}%</b><span>${r.ready}/${K.total} 대상 판단 가능</span></div>
    <div class="cov">
      <div class="cov-bar" role="img" aria-label="판단 가능 ${r.ready}, 검수 중 ${r.review}, 미온보딩 ${r.none}"><i class="cov-ok" style="width:${w(r.ready)}"></i><i class="cov-rv" style="width:${w(r.review)}"></i><i class="cov-no" style="width:${w(r.none)}"></i></div>
      <div class="cov-leg">${pv("approved", null, "sm")}<span>${esc(LABELS.cov.ready)}</span><b>${r.ready}</b>${pv("draft", null, "sm")}<span>${esc(LABELS.cov.review)}</span><b>${r.review}</b>${pv("untrusted", null, "sm")}<span>${esc(LABELS.cov.none)}</span><b>${r.none}</b></div>
      ${s === "empty" ? "" : `<p class="cov-note">${ic("info")}<span>검수 대기 문서 ${K.docsPending} · ${esc(K.pendingDoc)}. 승격 전 문서는 판단에 쓰지 않습니다.</span></p>`}
    </div></section>`;
}

function renderPage() {
  const s = APP.state, H = DATA.home, el = $("#home");
  const top = `<div class="home-h"><h1>${esc(LABELS.home)}</h1><div class="home-meta"><span><b>${esc(H.site)}</b></span><span>${esc(H.date)}</span><span>${esc(H.shift)}</span><span>갱신 <b>${esc(H.updated)}</b></span></div></div>`;
  if (s === "loading") { el.innerHTML = top + `<div class="grid">${["k-ap", "k-bk", "k-case", "k-sig", "k-kn"].map(k => `<div class="${k}">${sk(k === "k-ap" ? 340 : 280)}</div>`).join("")}</div>`; return; }
  const alert = s === "blocked" ? `<div class="alert alert-blocked" role="alert">${ic("ban")}<div><b>방금 정책 차단 · 주입 공격 의심</b><p>${esc(DATA.blockedExtra.t)} ${esc(DATA.blockedExtra.tool)} · ${esc(DATA.blockedExtra.why)}. <a href="audit.html?filter=blocked">감사 기록 보기</a></p></div></div>`
    : s === "error" ? `<div class="alert alert-error" role="alert">${ic("alert")}<div><b>일부 데이터를 불러오지 못했습니다</b><p>지식 커버리지 카드만 영향을 받았습니다.</p></div></div>`
    : s === "empty" ? `<div class="alert alert-ok" role="status">${ic("check")}<div><b>처리할 항목이 없습니다</b><p>새 신호가 들어오면 에이전트가 케이스를 열고 이 화면에 표시합니다.</p></div></div>` : "";
  el.innerHTML = top + alert + `<div class="grid">${cardApprovals(s)}${cardBlocked(s)}${cardCases(s)}${cardSignals(s)}${cardKnowledge(s)}</div>`;
}
const PAGE_ACTS = { retry: () => { setState("loading"); setTimeout(() => setState("normal"), 800); } };

initTheme(); readURL();
renderShell([LABELS.nav.home]);
renderDemo(); bindActs(PAGE_ACTS); APP.renderPage = renderPage;
renderPage();
