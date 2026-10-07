// 앱 셸 — 사이드바 · 탑바 · 하단 탭바 · 네트워크 바
import { $, count, esc, ic, pv } from "../../lib/dom.js";
import { APP, DATA, HREF, LABELS, NAV, TABS } from "../../lib/state.js";
import { renderThemeBtn } from "../../lib/theme.js";

export function renderShell(crumbs) {
  const u = DATA.shell.user;
  $("#sidebar").innerHTML = `
    <div class="sb-brand"><span class="sb-mark">${ic("logo")}</span><span class="sb-name">${esc(LABELS.app)}</span></div>
    <div class="sb-nav">${NAV.map(g => `<div class="sb-grp">${esc(LABELS.navGroups[g.g])}</div>` + g.items.map(k =>
      `<a class="sb-link" href="${HREF[k]}"${k === APP.page ? ' aria-current="page"' : ""}>${ic(k)}<span class="lbl">${esc(LABELS.nav[k])}</span><span class="lbl-s">${esc(LABELS.navShort[k])}</span>${count(k)}</a>`).join("")).join("")}</div>
    <div class="sb-foot">
      <div class="sb-legend">${pv("untrusted", null, "sm")}${pv("draft", null, "sm")}${pv("approved", null, "sm")}</div>
      <div class="sb-user"><span class="avatar">${esc(u.initial)}</span><span class="sb-user-txt">${esc(u.role)}<small>${esc(u.id)}</small></span></div>
    </div>`;
  $("#tabbar").innerHTML = TABS.map(k =>
    `<a class="tab" href="${HREF[k]}"${k === APP.page ? ' aria-current="page"' : ""}>${ic(k)}<span>${esc(LABELS.navShort[k])}</span>${count(k)}</a>`).join("") +
    `<button class="tab" data-act="more"${TABS.includes(APP.page) ? "" : ' aria-current="page"'}>${ic("more")}<span>${esc(LABELS.navShort.more)}</span></button>`;
  $("#topbar").innerHTML = `
    <span class="sb-mark tb-mobile-brand">${ic("logo")}</span>
    <div class="tb-crumb">${crumbs.map((c, i) => i < crumbs.length - 1 ? `<span class="grp">${esc(c)}</span><span class="sep">/</span>` : `<span class="cur">${esc(c)}</span>`).join("")}</div>
    <span class="tb-sp"></span>
    <span class="net" id="net-ind"></span>
    <button class="icon-btn" data-act="legend" aria-label="출처 상태 범례">${ic("info")}</button>
    <button class="icon-btn" data-act="theme" id="theme-btn" aria-label="테마 전환"></button>`;
  renderNet(); renderThemeBtn();
}
export function renderNet() {
  const off = APP.net === "offline";
  const ind = $("#net-ind");
  if (ind) { ind.className = "net" + (off ? " off" : ""); ind.innerHTML = `<i></i><span class="net-l">${off ? "불안정" : "연결됨"}</span>`; }
  const b = $("#netbar"); b.hidden = !off;
  b.innerHTML = `${ic("wifi-off")}<span>네트워크 불안정 · 마지막 동기화 ${esc(DATA.shell.lastSync)} · 결정은 기기에 보관했다가 연결되면 전송합니다</span>`;
}
