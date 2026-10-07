// 현장 모바일 — 에러코드 입력 모달 (이 페이지에서만 쓴다). 확인 버튼의 code-ok 는 field.js 가 처리한다
import { ic } from "../../lib/dom.js";
import { modalCancel, modalHead } from "../../components/modals/modal-head.js";
import { openModal } from "../../components/modals/modal.js";

export function openCodeModal() {
  openModal(`${modalHead("에러코드 입력")}
    <label class="field">설비<input class="input" id="c-dev" value="INV-C3"></label>
    <label class="field">코드<input class="input" id="c-code" placeholder="예: F0003" data-autofocus></label>
    <div class="modal-acts">${modalCancel}<button class="btn btn-primary" data-act="code-ok">${ic("send")}올리기</button></div>`);
}
