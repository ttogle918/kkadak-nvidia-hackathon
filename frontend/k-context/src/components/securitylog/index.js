// securitylog 모듈: 허용/거부/차단/승인/거절 로그와 사람 전용 승인 버튼. 계약: mount(root, ctx) -> {destroy()}.
// 쓰기 규칙: actions.decide(id, decision) 는 아래 클릭 핸들러(사람이 누른 버튼)에서만 부른다. 신원 인자는 없다 — 서버가 채운다.
import { h, on, render } from '../../lib/dom.js';
import { logRowNode } from './log-row.js';
import { DECISIONS, canDecide, countByKind } from './logic.js';

/**
 * @param {HTMLElement} root app-shell 이 준 슬롯 div
 * @param {{store, api, t, actions}} ctx
 */
export function mount(root, ctx) {
  const { store, t, actions } = ctx;
  const busy = new Set(); // 결정 요청 중인 로그 id (중복 클릭 방지)
  const errors = new Map(); // id -> 오류 문구
  let destroyed = false;
  let lastCount = -1;

  function draw() {
    const s = store.getState();
    const open = !!s.securityOpen;
    const pending = countByKind(s.logs).pend;
    render(root, h('div', { class: 'securitylog', dataset: { module: 'securitylog', open: open ? 'true' : 'false' } },
      h('div', { class: 'securitylog__head' },
        h('button', {
          type: 'button', class: 'securitylog__toggle', dataset: { act: 'toggle' },
          'aria-expanded': String(open), 'aria-label': t(open ? 'securitylog.collapse' : 'securitylog.expand'),
        }, h('span', { 'aria-hidden': 'true' }, open ? '▾ ' : '▸ '), t('module.securitylog')),
        pending > 0 ? h('span', { class: 'securitylog__pending' }, t('securitylog.pending_count', { n: pending })) : null,
        h('span', { class: 'securitylog__live' }, h('i', { class: 'securitylog__dot', 'aria-hidden': 'true' }), t('securitylog.live'))),
      open ? h('ul', { class: 'securitylog__list', role: 'log', 'aria-live': 'polite', 'aria-label': t('securitylog.list_label') },
        s.logs.map((entry) => logRowNode({ entry, t, busy: busy.has(entry.id), error: errors.get(entry.id) ?? null }))) : null,
      open ? h('p', { class: 'securitylog__note' }, t('securitylog.note')) : null));
    // 새 로그가 오면 맨 아래로 — 스크롤하는 건 슬롯(root)이다
    if (open && s.logs.length !== lastCount) root.scrollTop = root.scrollHeight;
    lastCount = s.logs.length;
  }

  const offClick = on(root, 'click', '[data-act]', async (e, el) => {
    const act = el.dataset.act;
    if (act === 'toggle') {
      actions.setSecurityOpen(!store.getState().securityOpen);
      return;
    }
    if (act !== 'decide') return;
    // 스크립트가 만든 합성 클릭(isTrusted=false)은 사람의 결정이 아니다
    if (e.isTrusted === false) return;
    const { id, value: decision } = el.dataset;
    const entry = store.getState().logs.find((l) => l.id === id);
    if (!entry || !canDecide(entry) || !DECISIONS.includes(decision) || busy.has(id)) return;
    busy.add(id);
    errors.delete(id);
    draw();
    try {
      await actions.decide(id, decision); // 인자는 id 와 결정뿐 — 신원은 서버가 주입한다
    } catch (err) {
      errors.set(id, String(err?.message ?? err));
    } finally {
      busy.delete(id);
      if (!destroyed) draw();
    }
  });

  draw();
  const off = store.select((s) => [s.logs, s.securityOpen, s.lang], draw, { equals: (a, b) => a.every((v, i) => v === b[i]) });
  return { destroy() { destroyed = true; off(); offClick(); root.replaceChildren(); } };
}
