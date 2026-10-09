// rationale 모듈: 판단 근거 태그 줄(작은 pill) + 태그를 누르면 뜨는 작은 팝오버(깔때기엔 걸러낸 것 포함). 데이터는 api.getRationale(cardId).
// 계약: mount(root, ctx) -> {destroy()}. 다른 components/* 를 import 하지 않는다.
import { h, on, render } from '../../lib/dom.js';
import { mockBadge } from '../../lib/mock-badge.js';
import { mockRegions } from '../../state/selectors.js';
import { renderChips } from './chips.js';
import { renderEvidencePanel, renderRejected } from './evidence-panel.js';
import { isV2Bundle, mergeBundleRationale, rationaleFor } from '../../lib/chat-bundle.js';
import { activeCardIds, createLatestGuard, mergeRationale, openItem, rejectedFor } from './logic.js';

/**
 * @param {HTMLElement} root app-shell 이 준 슬롯 div
 * @param {{store, api, t, actions}} ctx
 */
export function mount(root, ctx) {
  const { store, api, actions } = ctx;
  const t = (x, p) => ctx.t(x, p);
  const guard = createLatestGuard();
  // status: 'idle'(카드 없음) | 'loading' | 'ready' | 'error'
  let model = { status: 'idle', ids: '', merged: { chips: [], items: {} } };

  let focusAfter = null; // 닫은 뒤 포커스를 돌려줄 태그의 fk

  function draw() {
    const s = store.getState();
    const ids = activeCardIds(s);
    const item = openItem(model.merged, s.openEvidence);
    const ae = globalThis.document?.activeElement;
    const keepFk = focusAfter ?? (ae && root.contains?.(ae) ? ae.dataset?.fk : null);
    focusAfter = null;

    let content = null;
    const mr = mockRegions(s, api);
    const bundle = s.chatBundle;
    const v2 = !!bundle && isV2Bundle(bundle);
    if (mr.hideRationale && !v2) { // 챗봇이 정리한 일정이 있으면 mock 판단 근거는 숨긴다(실제 결과와 섞이지 않게)
      render(root, h('div', { class: 'rationale', dataset: { status: 'hidden' } }, h('div', { class: 'rationale-note', role: 'status' }, t('mock.rationale.hidden'))));
      return;
    }
    if (v2 && !model.merged.chips.length) { // 묶음 근거: 고른 항목이 없으면 안내, 있는데 근거가 없으면 사실대로 밝힌다
      content = h('div', { class: 'rationale-note', role: 'status', dataset: { empty: ids.length ? 'no-rationale' : 'no-card' } }, t(ids.length ? 'rationale.none_for_card' : 'rationale.no_card'));
    } else if (model.status === 'loading') content = h('div', { class: 'rationale-note' }, t('app.loading'));
    else if (model.status === 'error') content = h('div', { class: 'rationale-note is-error', role: 'alert' }, t('rationale.error'));
    else if (model.merged.chips.length) {
      content = [
        mr.rationale ? h('div', { class: 'mock-row', dataset: { module: 'rationale-mock' } }, mockBadge(t, { kind: mr.rationale, note: true })) : null,
        renderChips(model.merged.chips, { t, openKey: item ? item.key : null }),
        // 깔때기 팝오버에는 걸러낸 주장과 이유를 함께 둔다
        item ? renderEvidencePanel(item, { t, extra: item.key === 'funnel' && !v2 ? renderRejected(rejectedFor(s.data?.cards, ids), { t }) : null }) : null,
      ];
    }
    render(root, h('div', { class: 'rationale', dataset: { status: model.status } }, content));
    if (keepFk) {
      const find = (el) => {
        for (const c of el.children ?? []) {
          if (c.nodeType !== 1) continue;
          if (c.dataset?.fk === keepFk) return c;
          const hit = find(c);
          if (hit) return hit;
        }
        return null;
      };
      find(root)?.focus?.();
    }
  }

  /** 카드 선택이 바뀌면 다시 받는다. 늦게 도착한 이전 응답은 버린다. */
  async function load() {
    const ids = activeCardIds(store.getState());
    const key = ids.join(',');
    const token = guard.next();
    const bundle = store.getState().chatBundle;
    if (bundle && isV2Bundle(bundle)) { // v2 묶음: 서버를 부르지 않고 묶음 안 근거를 찾는다(언급 카드 mention:, 행사 event:)
      const found = ids.map((id) => rationaleFor(bundle, id)).filter(Boolean);
      model = { status: found.length ? 'ready' : 'idle', ids: key, merged: mergeBundleRationale(found) };
      draw();
      return;
    }
    if (!ids.length || bundle) { // v1 묶음이 있으면 근거를 받지 않는다(숨김)
      model = { status: 'idle', ids: key, merged: { chips: [], items: {} } };
      draw();
      return;
    }
    model = { status: 'loading', ids: key, merged: { chips: [], items: {} } };
    draw();
    const results = await Promise.allSettled(ids.map((id) => api.getRationale(id)));
    if (!guard.isCurrent(token)) return; // 그 사이 선택이 바뀌었다
    const ok = results.filter((r) => r.status === 'fulfilled').map((r) => r.value);
    model = ok.length
      ? { status: 'ready', ids: key, merged: mergeRationale(ok) }
      : { status: 'error', ids: key, merged: { chips: [], items: {} } };
    draw();
  }

  const closeFrom = (fk) => {
    focusAfter = fk;
    actions.closeEvidence();
  };
  const offClick = on(root, 'click', '[data-act]', (_e, el) => {
    if (el.dataset.act === 'chip') {
      // 열려 있는 태그를 다시 누르면 닫는다
      if (store.getState().openEvidence === el.dataset.key) closeFrom(el.dataset.fk);
      else actions.openEvidence(el.dataset.key);
    } else if (el.dataset.act === 'close') {
      closeFrom(`chip:${store.getState().openEvidence}`);
    }
  });

  // Esc · 바깥 클릭으로 닫기(포커스가 어디 있든 먹도록 document 에 건다. 없으면 root)
  const doc = globalThis.document?.addEventListener ? globalThis.document : root;
  const onKey = (e) => {
    const k = store.getState().openEvidence;
    if (e.key === 'Escape' && k != null) closeFrom(`chip:${k}`);
  };
  let justOpened = false; // 다른 모듈의 버튼("왜 이걸 골랐나요?")이 같은 클릭에서 연 팝오버를 바로 닫지 않게 한다
  const onOutside = (e) => {
    if (justOpened || store.getState().openEvidence == null) return;
    if (root.contains?.(e.target)) return;
    actions.closeEvidence();
  };
  doc.addEventListener('keydown', onKey);
  doc.addEventListener('click', onOutside);

  const idsOf = (s) => activeCardIds(s).join(',');
  load();
  const offStore = store.subscribe((s, prev) => {
    if (s.openEvidence != null && s.openEvidence !== prev.openEvidence) {
      justOpened = true;
      setTimeout(() => { justOpened = false; }, 0);
    }
    if (idsOf(s) !== idsOf(prev) || !!s.chatBundle !== !!prev.chatBundle) load();
    else if (s.openEvidence !== prev.openEvidence || s.chatBundle !== prev.chatBundle || s.lang !== prev.lang || s.data !== prev.data) draw();
  });

  return {
    destroy() {
      guard.invalidate();
      offStore();
      offClick();
      doc.removeEventListener('keydown', onKey);
      doc.removeEventListener('click', onOutside);
      root.replaceChildren();
    },
  };
}
