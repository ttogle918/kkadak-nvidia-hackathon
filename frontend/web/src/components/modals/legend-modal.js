// 출처 상태 범례 모달
import { esc, pv } from "../../lib/dom.js";
import { LABELS } from "../../lib/state.js";
import { modalHead } from "./modal-head.js";
import { openModal } from "./modal.js";

export function openLegend() {
  openModal(`${modalHead("출처 상태")}
    <div>${Object.keys(LABELS.prov).map(k => `<div class="legend-row">${pv(k)}<p>${esc(LABELS.provDesc[k])}</p></div>`).join("")}</div>`);
}
