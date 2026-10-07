// 폰 하단 탭 '더보기' 시트
import { modalHead } from "./modal-head.js";
import { openModal } from "./modal.js";
import { esc, ic } from "../../lib/dom.js";
import { APP, HREF, LABELS, NAV, TABS } from "../../lib/state.js";

export function openMore() {
  const rest = NAV.flatMap(g => g.items).filter(k => !TABS.includes(k));
  openModal(`${modalHead(LABELS.nav.more)}
    <div class="sheet-nav">${rest.map(k => `<a href="${HREF[k]}"${k === APP.page ? ' aria-current="page"' : ""}>${ic(k)}${esc(LABELS.nav[k])}</a>`).join("")}</div>
    <button class="btn" data-act="theme">${ic("sun")}테마 전환</button>`);
}
