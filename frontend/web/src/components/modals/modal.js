// 모달 열기/닫기 — 모든 모달의 바탕
import { $ } from "../../lib/dom.js";

export function openModal(html) { $("#modal-root").innerHTML = `<div class="modal-bg" data-act="modal-bg"><div class="modal" role="dialog" aria-modal="true">${html}</div></div>`; const f = $("#modal-root [data-autofocus]"); if (f) f.focus(); }
const closeHooks = [];
// 모달이 닫힐 때마다 실행할 정리 함수를 등록한다 (페이지가 자기 상태를 비울 때)
export function onModalClose(fn) { closeHooks.push(fn); }
export function closeModal() { $("#modal-root").innerHTML = ""; closeHooks.forEach(fn => fn()); }
