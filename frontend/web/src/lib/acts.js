// data-act 클릭 위임 — 공통 액션 + 챗봇 액션 + 페이지 액션
import { CHAT_ACTS } from "../components/chat/chat.js";
import { renderDemo } from "../components/layout/demo-panel.js";
import { renderNet } from "../components/layout/shell.js";
import { openLegend } from "../components/modals/legend-modal.js";
import { closeModal } from "../components/modals/modal.js";
import { openMore } from "../components/modals/more-modal.js";
import { APP, setState, writeURL } from "./state.js";
import { applyTheme } from "./theme.js";

export const COMMON_ACTS = {
  ...CHAT_ACTS,
  theme: () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"),
  legend: openLegend, more: openMore,
  "modal-close": closeModal,
  "modal-bg": (el, e) => { if (e.target === el) closeModal(); },
  "demo-toggle": () => { APP.demoOpen = !APP.demoOpen; renderDemo(); },
  "demo-state": el => setState(el.dataset.v),
  "demo-net": () => { APP.net = APP.net === "offline" ? "online" : "offline"; writeURL(); renderNet(); renderDemo(); }
};
export function bindActs(pageActs) {
  document.addEventListener("click", e => {
    const el = e.target.closest("[data-act]"); if (!el) return;
    const fn = pageActs[el.dataset.act] || COMMON_ACTS[el.dataset.act]; if (fn) fn(el, e);
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") { closeModal(); if (pageActs["ctx-close"]) pageActs["ctx-close"](); } });
  addEventListener("online", () => { APP.net = "online"; renderNet(); renderDemo(); });
  addEventListener("offline", () => { APP.net = "offline"; renderNet(); renderDemo(); });
}
