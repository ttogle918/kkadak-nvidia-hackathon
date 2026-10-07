// 토스트
import { $, esc, ic } from "../lib/dom.js";

let toastT;
export function toast(msg, icon) { const t = $("#toast"); t.innerHTML = `${ic(icon || "check")}<span>${esc(msg)}</span>`; t.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => t.hidden = true, 3200); }
