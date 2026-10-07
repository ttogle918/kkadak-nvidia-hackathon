// 플로팅 에이전트 어시스턴트 — 데이터는 DATA.chat
import { placeDemo } from "../layout/demo-panel.js";
import { $, esc, ic, pv } from "../../lib/dom.js";
import { DATA } from "../../lib/state.js";

/* --- 에이전트 어시스턴트 (플로팅 챗) · 데이터는 DATA.chat --- */
const CHAT = { open: false, busy: false, log: [], listening: false };
const APPROVE_RE = /승인해|승인 처리|결재해|적용해|제출해|발주해/;
export function chatMsgHTML(m) {
  if (m.role === "user") return `<div class="msg-u">${esc(m.text)}</div>`;
  const cls = m.kind === "refuse" ? " refuse" : m.kind === "block" ? " block" : "";
  const badge = m.kind === "refuse" ? pv("noev", "답변 거부", "sm") : m.kind === "block" ? pv("blocked", "사람 전용", "sm") : pv("draft", "답변은 초안", "sm");
  const tools = (m.tools || []).map(t => `<span class="msg-tool">${t.done ? ic("check") : '<span class="spin" style="width:12px;height:12px;border-width:2px"></span>'}${esc(t.name)} · ${t.done ? esc(t.dur) : "실행 중"}</span>`).join("");
  const txt = m.done ? m.text : m.shown;
  return `<div class="msg-a${cls}"><div style="display:flex;gap:6px;flex-wrap:wrap">${badge}</div>${tools ? `<div class="msg-tools">${tools}</div>` : ""}${txt || m.streaming ? `<p class="msg-t">${esc(txt)}${m.streaming ? '<span class="caret"></span>' : ""}</p>` : ""}${m.done && m.cites ? `<div class="msg-cites">${m.cites.map(c => `<span class="msg-cite">${ic("knowledge")}${esc(c)}</span>`).join("")}</div>` : ""}${m.done && m.link ? `<a class="btn btn-sm" href="${m.link[0]}" style="align-self:flex-start">${esc(m.link[1])}${ic("chev")}</a>` : ""}</div>`;
}
export function renderChat() {
  const C = DATA.chat || { ctx: "", suggestions: [] };
  $("#chat-root").innerHTML = `<button class="fab" data-act="chat-toggle" aria-label="에이전트 어시스턴트 열기"${CHAT.open ? " hidden" : ""}>${ic("chat")}</button>
  <section class="chat" role="dialog" aria-label="에이전트 어시스턴트"${CHAT.open ? "" : " hidden"}>
    <div class="chat-h"><span class="sb-mark">${ic("bot")}</span><div style="min-width:0;flex:1"><b>에이전트 어시스턴트</b><div class="chat-ctx">${esc(C.ctx)}</div></div><button class="icon-btn" data-act="chat-toggle" aria-label="닫기">${ic("x")}</button></div>
    <div class="chat-log" id="chat-log"></div>
    <div class="chat-sug">${(C.suggestions || []).map(s => `<button class="chip" data-act="chat-sug" data-v="${esc(s)}">${esc(s)}</button>`).join("")}</div>
    <div class="chat-in"><button class="icon-btn chat-mic" data-act="chat-mic" aria-label="음성 입력">${ic("mic")}</button><textarea class="input" id="chat-input" rows="1" placeholder="질문을 입력하세요"></textarea><button class="btn btn-primary" data-act="chat-send" aria-label="보내기">${ic("send")}</button></div>
    <div class="chat-note">${ic("lock")}승인·결재·정책 적용은 채팅으로 할 수 없습니다</div>
  </section>`;
  renderChatLog();
}
export function renderChatLog() {
  const log = $("#chat-log"); if (!log) return;
  log.innerHTML = CHAT.log.map(chatMsgHTML).join(""); log.scrollTop = log.scrollHeight;
  document.querySelectorAll('#chat-root [data-act="chat-sug"], #chat-root [data-act="chat-send"]').forEach(b => b.disabled = CHAT.busy);
  const mic = $("#chat-root .chat-mic"); if (mic) mic.classList.toggle("on", CHAT.listening);
  const inp = $("#chat-input"); if (inp) inp.placeholder = CHAT.listening ? "듣는 중…" : "질문을 입력하세요";
}
export function chatSend(text) {
  text = (text || "").trim(); if (!text || CHAT.busy) return;
  const C = DATA.chat || { replies: [] };
  CHAT.log.push({ role: "user", text });
  const r = APPROVE_RE.test(text)
    ? { kind: "block", tools: [], text: "승인·결재·정책 적용은 사람만 할 수 있어 채팅으로는 처리하지 않습니다. 사람 전용 바에서 재로그인 후 진행하세요.", link: ["approvals.html", "승인 큐로 이동"] }
    : (C.replies || []).find(x => x.match.some(k => text.includes(k))) || { kind: "refuse", tools: [["kb.search_manual", "0.8s"]], text: "승격된 문서와 승인된 기록에서 이 질문의 근거를 찾지 못했습니다. 근거 없이 답하지 않습니다." };
  const m = { role: "agent", kind: r.kind || "answer", tools: [], text: r.text, shown: "", cites: r.cites, link: r.link, streaming: false, done: false };
  CHAT.log.push(m); CHAT.busy = true; renderChatLog();
  const tools = (r.tools || []).map(([name, dur]) => ({ name, dur, done: false }));
  let i = 0;
  const step = () => {
    if (i < tools.length) { m.tools.push(tools[i]); renderChatLog(); setTimeout(() => { tools[i].done = true; i++; renderChatLog(); step(); }, 650); return; }
    m.streaming = true; let n = 0;
    const t = setInterval(() => { n = Math.min(m.text.length, n + 3); m.shown = m.text.slice(0, n); renderChatLog(); if (n >= m.text.length) { clearInterval(t); m.streaming = false; m.done = true; CHAT.busy = false; renderChatLog(); } }, 30);
  };
  step();
}
export const CHAT_ACTS = {
  "chat-toggle": () => { CHAT.open = !CHAT.open; renderChat(); if (CHAT.open) { const i = $("#chat-input"); if (i) i.focus(); } },
  "chat-sug": el => chatSend(el.dataset.v),
  "chat-send": () => { const i = $("#chat-input"); chatSend(i.value); i.value = ""; },
  "chat-mic": () => { if (CHAT.listening) return; CHAT.listening = true; renderChatLog(); setTimeout(() => { CHAT.listening = false; const i = $("#chat-input"); const s = (DATA.chat && DATA.chat.suggestions || [])[0]; if (i && s) i.value = s; renderChatLog(); }, 1500); }
};
document.addEventListener("keydown", e => {
  if (e.target && e.target.id === "chat-input" && e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); CHAT_ACTS["chat-send"](); }
  if (e.key === "Escape" && CHAT.open) { CHAT.open = false; renderChat(); }
});
addEventListener("DOMContentLoaded", () => {
  const r = document.createElement("div"); r.id = "chat-root"; document.body.appendChild(r);
  const g = (DATA.chat && DATA.chat.greeting) || "현재 화면 기준으로 답합니다. 모든 답에 근거를 붙이고, 근거가 없으면 답하지 않습니다.";
  CHAT.log = [{ role: "agent", kind: "answer", text: g, done: true }];
  renderChat(); placeDemo();
});
