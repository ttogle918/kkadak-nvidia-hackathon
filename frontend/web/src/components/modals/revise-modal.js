// 수정 요청 모달 — 에이전트에게 다시 작성을 요청한다
import { esc, ic } from "../../lib/dom.js";
import { modalCancel, modalHead } from "./modal-head.js";
import { openModal } from "./modal.js";

/**
 * @param {object} o
 * @param {string} o.lead         설명 (평문)
 * @param {string} o.placeholder  입력 예시
 * @param {string} [o.target]     수정 대상 한 줄 (읽기 전용 입력, 평문)
 */
export function openReviseModal({ lead, placeholder, target }) {
  openModal(`${modalHead("수정 요청")}
    <p style="color:var(--tx-2);font-weight:500">${esc(lead)}</p>
    ${target ? `<label class="field">대상 문장<input class="input" value="${esc(target)}" readonly></label>` : ""}
    <label class="field">요청 내용<textarea class="input" id="revise" data-autofocus placeholder="${esc(placeholder)}"></textarea></label>
    <div class="modal-acts">${modalCancel}<button class="btn btn-primary" data-act="revise-ok">${ic("edit")}요청 보내기</button></div>`);
}
