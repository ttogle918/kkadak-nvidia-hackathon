// rationale 모듈: 판단 근거 칩 줄 + 선택한 근거 패널 + 걸러낸 것. 데이터는 api.getRationale(cardId).
// 계약: mount(root, ctx) -> {destroy()}. 다른 components/* 를 import 하지 않는다.
import { h, on, render } from '../../lib/dom.js';
import { renderChips } from './chips.js';
import { renderEvidencePanel, renderRejected } from './evidence-panel.js';
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

  function draw() {
    const s = store.getState();
    const ids = activeCardIds(s);
    const item = openItem(model.merged, s.openEvidence);
    const ae = globalThis.document?.activeElement;
    const keepFk = ae && root.contains?.(ae) ? ae.dataset?.fk : null;

    let content;
    if (model.status === 'loading') content = h('div', { class: 'rationale-note' }, t('app.loading'));
    else if (model.status === 'error') content = h('div', { class: 'rationale-note is-error', role: 'alert' }, t('rationale.error'));
    else if (!model.merged.chips.length) content = h('div', { class: 'rationale-note' }, t('rationale.no_card'));
    else {
      content = [
        h('div', { class: 'rationale-label' }, t('rationale.chips_label')),
        renderChips(model.merged.chips, { t, openKey: item ? item.key : null }),
        item ? renderEvidencePanel(item, { t }) : h('div', { class: 'rationale-note' }, t('rationale.empty')),
        renderRejected(rejectedFor(s.data?.cards, ids), { t }),
      ];
    }
    render(root, h('div', { class: 'rationale', dataset: { status: model.status } },
      h('h2', { class: 'rationale-title' }, t('rationale.title')), content));
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
    if (!ids.length) {
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

  const offClick = on(root, 'click', '[data-act]', (_e, el) => {
    if (el.dataset.act === 'chip') {
      // 열려 있는 칩을 다시 누르면 닫는다
      if (store.getState().openEvidence === el.dataset.key) actions.closeEvidence();
      else actions.openEvidence(el.dataset.key);
    } else if (el.dataset.act === 'close') {
      actions.closeEvidence();
    }
  });

  const onKey = (e) => {
    if (e.key === 'Escape' && store.getState().openEvidence != null && root.contains?.(e.target)) actions.closeEvidence();
  };
  root.addEventListener('keydown', onKey);

  const idsOf = (s) => activeCardIds(s).join(',');
  load();
  const offStore = store.subscribe((s, prev) => {
    if (idsOf(s) !== idsOf(prev)) load();
    else if (s.openEvidence !== prev.openEvidence || s.lang !== prev.lang || s.data !== prev.data) draw();
  });

  return {
    destroy() {
      guard.invalidate();
      offStore();
      offClick();
      root.removeEventListener('keydown', onKey);
      root.replaceChildren();
    },
  };
}
