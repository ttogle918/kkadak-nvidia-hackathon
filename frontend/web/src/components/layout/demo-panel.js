// 데모 상태 전환 패널
import { $, esc } from "../../lib/dom.js";
import { APP, DEMO_MAIN, DEMO_SUB, LABELS } from "../../lib/state.js";

export function renderDemo() {
  const b = k => `<button class="demo-b" data-act="demo-state" data-v="${k}" aria-pressed="${APP.state === k}">${esc(LABELS.demo[k])}</button>`;
  $("#demo").innerHTML = `
    <div class="demo-panel" ${APP.demoOpen ? "" : "hidden"}>
      <div class="demo-grp">STATE</div><div class="demo-row">${DEMO_MAIN.map(b).join("")}</div>
      <div class="demo-grp">SCREEN</div><div class="demo-row">${DEMO_SUB.map(b).join("")}
      <button class="demo-b" data-act="demo-net" aria-pressed="${APP.net === "offline"}">${esc(LABELS.demo.offline)}</button></div>
    </div>
    <button class="demo-pill" data-act="demo-toggle" aria-expanded="${APP.demoOpen}">DEMO · ${esc(LABELS.demo[APP.state] || APP.state)}</button>`;
}
export function placeDemo() { const a = [$("#human-bar"), $("#tabbar")].find(e => e && e.getBoundingClientRect().height > 0); const b = a ? Math.max(0, innerHeight - a.getBoundingClientRect().top) + 12 : 20; document.documentElement.style.setProperty("--float-b", b + "px"); }
if (window.ResizeObserver) addEventListener("DOMContentLoaded", () => { const hb = $("#human-bar"); if (hb) new ResizeObserver(placeDemo).observe(hb); });
addEventListener("load", placeDemo);
addEventListener("resize", () => placeDemo());
