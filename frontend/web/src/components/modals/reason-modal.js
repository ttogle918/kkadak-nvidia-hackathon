// 사유 입력 모달 — 반려·거부·무시처럼 사람이 이유를 남기는 결정. 입력은 호출한 페이지의 액션이 읽는다
import { esc, ic } from "../../lib/dom.js";
import { modalCancel, modalHead } from "./modal-head.js";
import { openModal } from "./modal.js";

/**
 * @param {object} o
 * @param {string} o.title
 * @param {string} [o.hint]          설명 한 줄 (평문)
 * @param {string[]} [o.chips]       빠른 사유 칩 (data-act="reason" → 페이지가 #<fieldId> 에 채운다)
 * @param {string} [o.fieldId="why"] 입력창 id. 오류 문구는 #<fieldId>-err
 * @param {string} [o.fieldLabel="사유"]
 * @param {string} [o.error]         비었을 때 보여줄 문구. 있으면 `<p id="<fieldId>-err" hidden>` 를 만든다
 * @param {string} o.act             확인 버튼 data-act
 * @param {string} o.label           확인 버튼 문구
 */
export function openReasonModal({ title, hint, chips = [], fieldId = "why", fieldLabel = "사유", error, act, label }) {
  openModal(`${modalHead(title)}
    ${hint ? `<p style="color:var(--tx-2);font-weight:500">${esc(hint)}</p>` : ""}
    ${chips.length ? `<div class="chips">${chips.map(r => `<button class="chip" data-act="reason" data-v="${esc(r)}">${esc(r)}</button>`).join("")}</div>` : ""}
    <label class="field">${esc(fieldLabel)}<textarea class="input" id="${fieldId}" data-autofocus></textarea></label>
    ${error ? `<p id="${fieldId}-err" style="color:var(--crit-tx);font-weight:700;font-size:var(--fs-sm)" hidden>${esc(error)}</p>` : ""}
    <div class="modal-acts">${modalCancel}<button class="btn btn-danger" data-act="${act}">${ic("x")}${esc(label)}</button></div>`);
}
