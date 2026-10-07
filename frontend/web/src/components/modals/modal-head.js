// 모달 머리글 — 제목(+선택 아이콘)과 닫기 버튼. 모든 모달이 이걸로 시작한다
import { esc, ic } from "../../lib/dom.js";

export const modalHead = (title, icon) =>
  `<div class="modal-x"><h2>${icon ? ic(icon) + " " : ""}${esc(title)}</h2><button class="icon-btn" data-act="modal-close" aria-label="닫기">${ic("x")}</button></div>`;

export const modalCancel = `<button class="btn" data-act="modal-close">취소</button>`;
