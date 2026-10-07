// 고위험 결정 재인증 모달 — 사번 + PIN. 확인 버튼의 data-act 는 호출한 페이지가 처리한다 (PIN 검사는 페이지 액션에서)
import { esc, ic, pv } from "../../lib/dom.js";
import { DATA } from "../../lib/state.js";
import { modalCancel, modalHead } from "./modal-head.js";
import { openModal } from "./modal.js";

/**
 * @param {object} o
 * @param {string} o.title      머리글
 * @param {string} [o.icon]     머리글 아이콘
 * @param {string} [o.lead]     한 줄 설명 (평문)
 * @param {{title:string,text:string}} [o.alert]  경고 상자 (평문)
 * @param {boolean} [o.flow]    초안 → 승인자 출처 배지 행 표시
 * @param {string} o.act        확인 버튼 data-act
 * @param {string} o.label      확인 버튼 문구
 * @param {string} [o.labelIcon="lock"]
 */
export function openPinModal({ title, icon, lead, alert, flow, act, label, labelIcon = "lock" }) {
  const u = DATA.shell.user;
  openModal(`${modalHead(title, icon)}
    ${alert ? `<div class="alert alert-error" style="color:var(--tx-1)">${ic("alert")}<div><b>${esc(alert.title)}</b><p>${esc(alert.text)}</p></div></div>` : ""}
    ${lead ? `<p style="color:var(--tx-2);font-weight:500">${esc(lead)}</p>` : ""}
    ${flow ? `<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">${pv("draft")}${ic("chev")}${pv("approved", `${u.role} ${u.id}`)}</div>` : ""}
    <label class="field">사번 ${esc(u.id)} · PIN<input class="input" id="pin" type="password" inputmode="numeric" autocomplete="one-time-code" placeholder="4자리 이상" data-autofocus></label>
    <p id="pin-err" style="color:var(--crit-tx);font-weight:700;font-size:var(--fs-sm)" hidden>PIN을 4자리 이상 입력하세요.</p>
    <div class="modal-acts">${modalCancel}<button class="btn btn-primary" data-act="${act}">${ic(labelIcon)}${esc(label)}</button></div>`);
}
