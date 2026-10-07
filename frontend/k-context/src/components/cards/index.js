// cards 모듈: 옛날 카드(selectedSeg) · 지금 카드(selectedNow) · 출처 태그 상세 팝오버.
// 계약: mount(root, ctx) -> {destroy()}. 다른 components/* 를 import 하지 않는다.
import { h, on, render } from '../../lib/dom.js';
import { renderOldCard } from './old-card.js';
import { renderNowCard } from './now-card.js';
import { renderSourcePopover } from './source-popover.js';
import { bundleCardNodes } from './bundle-view.js';
import { mockBadge } from '../../lib/mock-badge.js';
import { mockRegions } from '../../state/selectors.js';
import { createLatestGuard, findSource, nowButtons, supportingFacts, visibleCards } from './logic.js';

const BODY_KEYS = ['lang', 'mode', 'selectedSeg', 'selectedNow', 'immersion', 'expandedTags', 'added', 'skipped', 'data', 'loaded', 'selectedTag', 'chatBundle'];
const POP_KEYS = ['lang', 'selectedTag', 'data', 'selectedSeg'];

const changed = (a, b, keys) => keys.some((k) => !Object.is(a[k], b[k]));
const doc = () => globalThis.document;

/** el 아래에서 조건에 맞는 첫 요소(테스트용 가짜 DOM 에도 있는 children 만 쓴다). */
function findIn(el, pred) {
  for (const c of el?.children ?? []) {
    if (c.nodeType !== 1) continue;
    if (pred(c)) return c;
    const hit = findIn(c, pred);
    if (hit) return hit;
  }
  return null;
}
function collect(el, pred, out = []) {
  for (const c of el?.children ?? []) {
    if (c.nodeType !== 1) continue;
    if (pred(c)) out.push(c);
    collect(c, pred, out);
  }
  return out;
}
const focusables = (el) => collect(el, (c) => c.tag === 'button' || c.tagName === 'BUTTON');

/**
 * @param {HTMLElement} root app-shell 이 준 슬롯 div
 * @param {{store, api, t, actions}} ctx
 */
export function mount(root, ctx) {
  const { store, api, actions } = ctx;
  const t = (x, p) => ctx.t(x, p);
  const body = h('div', { class: 'cards' });
  const host = h('div', { class: 'cards-pop-host' });
  root.replaceChildren(body, host);

  let lastTagFk = null; // 팝오버를 연 태그 — 닫을 때 포커스를 돌려준다
  const whyGuard = createLatestGuard();

  const focusFk = (fk) => {
    const el = fk && findIn(body, (c) => c.dataset?.fk === fk);
    if (el && typeof el.focus === 'function') el.focus();
  };

  function drawBody() {
    const s = store.getState();
    if (s.chatBundle) { // 챗봇이 정리한 일정이 있으면 그 기록·행사 카드를 보인다(샘플 카드 대신)
      render(body, bundleCardNodes(s.chatBundle, t, { mock: mockRegions(s, api).cards }));
      return;
    }
    // 다시 그리면 포커스가 사라지므로 fk 를 기억했다가 되돌린다
    const ae = doc()?.activeElement;
    const keepFk = ae && body.contains?.(ae) ? ae.dataset?.fk : null;
    const { old, now } = visibleCards(s);
    const nodes = [];
    if (old) {
      nodes.push(renderOldCard(old, {
        t, immersion: s.immersion, hoverFact: s.hoverFact, expanded: !!s.expandedTags[old.id], openId: s.selectedTag,
      }));
    }
    if (now) {
      nodes.push(renderNowCard(now, {
        t, added: s.added, skipped: s.skipped, expanded: !!s.expandedTags[now.id], openId: s.selectedTag,
      }));
    }
    const mk = mockRegions(s, api).cards;
    if (nodes.length && mk) nodes.unshift(h('div', { class: 'mock-row', dataset: { module: 'cards-mock' } }, mockBadge(t, { kind: mk, note: true })));
    if (!nodes.length) nodes.push(h('div', { class: 'cards-empty' }, s.loaded ? t('cards.empty') : t('app.loading')));
    render(body, nodes);
    if (keepFk) focusFk(keepFk);
  }

  /** 사실 문장 강조는 전체를 다시 그리지 않고 클래스만 바꾼다(호버 중인 요소가 사라지지 않게). */
  function patchHover() {
    const n = store.getState().hoverFact;
    for (const el of collect(body, (c) => c.dataset?.ref != null)) {
      const cls = String(el.getAttribute?.('class') ?? el.attrs?.class ?? '').split(' ').filter((x) => x && x !== 'is-hl');
      if (String(n) === el.dataset.ref) cls.push('is-hl');
      el.setAttribute('class', cls.join(' '));
    }
    for (const el of collect(body, (c) => c.dataset?.act === 'tag')) {
      const cls = String(el.getAttribute?.('class') ?? el.attrs?.class ?? '').split(' ').filter((x) => x && x !== 'is-hl');
      if (n != null && String(n) === el.dataset.n) cls.push('is-hl');
      el.setAttribute('class', cls.join(' '));
    }
  }

  function drawPopover() {
    const s = store.getState();
    const src = findSource(s, s.selectedTag);
    if (!src) {
      host.replaceChildren();
      return;
    }
    const old = visibleCards(s).old ?? s.data?.cards?.find((c) => c.id === s.selectedSeg) ?? null;
    const already = !!findIn(host, (c) => c.dataset?.src === src.id);
    render(host, renderSourcePopover(src, { t, facts: supportingFacts(old, src.id) }));
    // 새로 열릴 때만 닫기 버튼으로 포커스를 옮긴다(언어 전환으로 다시 그릴 때는 건드리지 않는다)
    const close = findIn(host, (c) => c.dataset?.act === 'pop-close');
    if (!already && close?.focus) close.focus();
  }

  const closePopover = () => {
    if (store.getState().selectedTag == null) return;
    actions.closeTag();
    focusFk(lastTagFk);
  };

  // --- 클릭 위임 ---
  const offClick = on(root, 'click', '[data-act]', (e, el) => {
    const s = store.getState();
    switch (el.dataset.act) {
      case 'toggle-imm': actions.toggleImmersion(); break;
      case 'tag': lastTagFk = el.dataset.fk; actions.openTag(el.dataset.id); break;
      case 'fact-ref': if (el.dataset.id) { lastTagFk = null; actions.openTag(el.dataset.id); } break;
      case 'more-tags': actions.expandTags(el.dataset.card); break;
      case 'pop-close': closePopover(); break;
      case 'pop-backdrop': if (e.target === el) closePopover(); break;
      case 'local': actions.openLocalContext(el.dataset.id); break;
      case 'add': {
        const now = visibleCards(s).now;
        if (now && !nowButtons(now.badge, s).primary.disabled) actions.addSelected();
        break;
      }
      case 'skip': {
        const now = visibleCards(s).now;
        if (now && !nowButtons(now.badge, s).skip.disabled) actions.skipSelected();
        break;
      }
      case 'why-pick': whyPick(); break;
      default: break;
    }
  });

  /** "왜 이걸 골랐나요?" — 판단 근거 태그의 첫 항목 팝오버를 연다. 응답이 늦게 와도 카드가 바뀌었으면 버린다. */
  async function whyPick() {
    const id = store.getState().selectedNow;
    if (!id) return;
    const token = whyGuard.next();
    try {
      const r = await api.getRationale(id);
      if (!whyGuard.isCurrent(token) || store.getState().selectedNow !== id) return;
      const key = r?.chips?.[0]?.key;
      if (key) actions.openEvidence(key);
    } catch {
      // 근거를 못 받아도 카드는 그대로 둔다
    }
  }

  // --- 사실 문장 하이라이트: 번호에 호버/포커스 ---
  const factNum = (el) => Number(el.dataset.factRef);
  const offs = [
    offClick,
    on(root, 'mouseover', '[data-act="fact-ref"]', (_e, el) => actions.setHoverFact(factNum(el))),
    on(root, 'mouseout', '[data-act="fact-ref"]', () => actions.setHoverFact(null)),
    on(root, 'focusin', '[data-act="fact-ref"]', (_e, el) => actions.setHoverFact(factNum(el))),
    on(root, 'focusout', '[data-act="fact-ref"]', () => actions.setHoverFact(null)),
  ];

  // --- 키보드: Esc 로 닫기 + Tab 포커스 가둠 ---
  const onKey = (e) => {
    if (store.getState().selectedTag == null) return;
    if (e.key === 'Escape') {
      closePopover();
      return;
    }
    if (e.key === 'Tab') {
      const list = focusables(host);
      if (!list.length) return;
      const first = list[0];
      const last = list[list.length - 1];
      const cur = doc()?.activeElement;
      if (!host.contains?.(cur)) {
        e.preventDefault?.();
        first.focus?.();
      } else if (e.shiftKey && cur === first) {
        e.preventDefault?.();
        last.focus?.();
      } else if (!e.shiftKey && cur === last) {
        e.preventDefault?.();
        first.focus?.();
      }
    }
  };
  // 바깥에 포커스가 있어도 Esc 가 먹도록 document 에 건다(없으면 root). 둘 다 걸면 중복 처리되므로 하나만.
  const keyTarget = doc()?.addEventListener ? doc() : root;
  keyTarget.addEventListener('keydown', onKey);

  drawBody();
  drawPopover();
  const offStore = store.subscribe((s, prev) => {
    if (changed(s, prev, BODY_KEYS)) drawBody();
    else if (s.hoverFact !== prev.hoverFact) patchHover();
    if (changed(s, prev, POP_KEYS)) drawPopover();
  });

  return {
    destroy() {
      offStore();
      offs.forEach((off) => off());
      keyTarget.removeEventListener('keydown', onKey);
      whyGuard.invalidate();
      root.replaceChildren();
    },
  };
}
