// DOM·문자열 헬퍼 — 출처 배지 pv() 포함
import { DATA, LABELS } from "./state.js";

export const PV_ICON = { untrusted: "untrusted", draft: "bot", approved: "user-check", blocked: "ban", noev: "file-x", sensor: "activity" };
export const $ = s => document.querySelector(s);
export const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const ic = n => `<svg class="ic" aria-hidden="true"><use href="#i-${n}"></use></svg>`;
export const pv = (t, extra, size) => `<span class="pv pv-${t}${size ? " pv-" + size : ""}">${ic(PV_ICON[t])}<span class="pv-l">${esc(LABELS.prov[t])}</span>${extra ? `<span class="pv-x">${esc(extra)}</span>` : ""}</span>`;
export const count = k => DATA.shell.counts[k] ? `<span class="sb-count">${DATA.shell.counts[k]}</span>` : "";
