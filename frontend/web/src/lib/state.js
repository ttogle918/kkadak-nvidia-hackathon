// 페이지 공통 상태(APP)와 DATA/LABELS 저장소. 페이지는 data/<key>.js 로 채운다
import { renderDemo } from "../components/layout/demo-panel.js";

export const NAV = [
  { g: "work", items: ["home", "inbox", "case", "draft", "approvals"] },
  { g: "know", items: ["knowledge", "map", "schedule"] },
  { g: "ctrl", items: ["security", "audit"] },
  { g: "field", items: ["field"] }
];
export const HREF = { home: "index.html", inbox: "inbox.html", case: "case.html", draft: "draft.html", approvals: "approvals.html", knowledge: "knowledge.html", map: "map.html", schedule: "schedule.html", security: "security.html", audit: "audit.html", field: "field.html" };
export const TABS = ["home", "inbox", "approvals", "map"];
export const DEMO_MAIN = ["normal", "running", "blocked", "approved"];
export const DEMO_SUB = ["empty", "loading", "error"];
export const APP = { page: document.body.dataset.page, renderPage: null, state: "normal", net: navigator.onLine === false ? "offline" : "online", demoOpen: false };
export function readURL() {
  const p = new URLSearchParams(location.search), s = p.get("state");
  if ([...DEMO_MAIN, ...DEMO_SUB, "rejected"].includes(s)) APP.state = s;
  if (p.get("net") === "offline") APP.net = "offline";
  if (p.get("theme") === "light" || p.get("theme") === "dark") document.documentElement.dataset.theme = p.get("theme");
}
export function writeURL() {
  const p = new URLSearchParams(location.search);
  APP.state === "normal" ? p.delete("state") : p.set("state", APP.state);
  APP.net === "offline" ? p.set("net", "offline") : p.delete("net");
  const q = p.toString(); history.replaceState(null, "", location.pathname + (q ? "?" + q : "") + location.hash);
}
export function setState(s) { APP.state = s; writeURL(); renderDemo(); if (APP.renderPage) APP.renderPage(); }

// 페이지 데이터 저장소 — data/<key>.js 가 Object.assign 으로 채운다
export const DATA = {};
export const LABELS = {};
