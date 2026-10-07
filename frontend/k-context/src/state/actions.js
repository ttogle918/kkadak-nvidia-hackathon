// 상태 전이 모음. 모듈들이 같은 동작을 따로 구현하지 않도록 ctx.actions 로 공유한다.
// 쓰기 규칙: 에이전트가 쓰는 도구는 draft 만 만든다. 여기서도 decide() 는 "사람이 누른 버튼" 에서만 호출한다
// (신원은 서버가 정하므로 인자로 받지 않는다).
import { normalizeLang } from '../lib/i18n.js';

export function createActions({ store, api }) {
  const { getState, setState } = store;
  let seq = 0;
  const localId = (p) => `${p}_local_${++seq}`;

  return {
    /** api 에서 원본을 한 번에 받아 store 에 넣는다. main.js 가 부팅할 때 부른다. */
    async loadAll() {
      try {
        const [itinerary, routes, cards, sources, messages, logs] = await Promise.all([
          api.getItinerary(), api.getRoutes(), api.getCards(), api.getSources(), api.getMessages(), api.getAuditLog(),
        ]);
        setState({ data: { itinerary, routes, cards, sources }, messages, logs, loaded: true, error: null });
      } catch (e) {
        setState({ loaded: false, error: String(e?.message ?? e) });
      }
    },

    setLang: (lang) => setState({ lang: normalizeLang(lang) }),
    setTheme: (theme) => setState({ theme: ['auto', 'light', 'dark'].includes(theme) ? theme : 'auto' }),
    setMode: (mode) => {
      if (['old', 'now', 'both'].includes(mode)) setState({ mode });
    },
    setDay: (day) => setState({ day: Number(day) }),
    toggleMinimize: () => setState((s) => ({ minimizeChanges: !s.minimizeChanges })),
    toggleImmersion: () => setState((s) => ({ immersion: !s.immersion })),
    setSecurityOpen: (securityOpen) => setState({ securityOpen: !!securityOpen }),
    /** 설정 패널 열기/닫기(톱바의 기어 버튼). */
    setSettingsOpen: (settingsOpen) => setState({ settingsOpen: !!settingsOpen }),

    /** 옛날 구간 선택(card_id). null 이면 해제. 선택이 바뀌면 근거 패널·하이라이트는 초기화한다. */
    selectSeg: (cardId) => setState({ selectedSeg: cardId, hoverFact: null, openEvidence: null }),
    selectRoute: (id) => setState({ selectedRoute: id }),
    selectNow: (cardId) => setState({ selectedNow: cardId, added: false, skipped: false, openEvidence: null }),
    /** 지금 카드의 "이 골목의 지명은…" 링크 → 연결된 옛날 카드를 고르고 둘 다 보기로 (목업 openLocal). */
    openLocalContext: (storyCardId) => setState({ selectedSeg: storyCardId, hoverFact: null, mode: 'both' }),

    openTag: (sourceId) => setState({ selectedTag: sourceId }),
    closeTag: () => setState({ selectedTag: null }),
    expandTags: (cardId) => setState((s) => ({ expandedTags: { ...s.expandedTags, [cardId]: true } })),
    openEvidence: (key) => setState({ openEvidence: key }),
    closeEvidence: () => setState({ openEvidence: null }),
    setHoverFact: (n) => setState({ hoverFact: n ?? null }),

    /** 선택된 지금 카드를 일정에 추가/건너뛰기(제안 상태 변경 — 원래 일정은 바뀌지 않는다). */
    addSelected: () => setState({ added: true, skipped: false }),
    skipSelected: () => setState({ skipped: true, added: false }),

    setInput: (input) => setState({ input }),

    /** 메시지 전송. text 를 생략하면 input 을 쓴다. 공격 프롬프트 거부는 api 가 판정하고 logs 에 deny 가 온다. */
    async send(text) {
      const s0 = getState();
      const t = String(text ?? s0.input).trim();
      if (!t || s0.sending) return null;
      setState((s) => ({ messages: [...s.messages, { id: localId('msg'), role: 'user', text: t }], input: '', sending: true }));
      try {
        const { reply, logs } = await api.sendMessage(t);
        setState((s) => ({ messages: [...s.messages, reply], logs: [...s.logs, ...logs], sending: false }));
        return reply;
      } catch (e) {
        setState({ sending: false, error: String(e?.message ?? e) });
        return null;
      }
    },

    /**
     * send 와 같은 전이이되 결과를 돌려준다(chat 모듈이 실패 표시·재시도에 쓴다). 기존 send 는 바꾸지 않았다.
     * retry=true 면 사용자 말풍선을 다시 만들지 않고 입력창도 건드리지 않는다.
     * @returns {Promise<{ok:true, reply:object}|{ok:false, reason:'empty'|'busy'|'error', error?:string}>}
     */
    async trySend(text, { retry = false } = {}) {
      const s0 = getState();
      const t = String(text ?? s0.input).trim();
      if (!t) return { ok: false, reason: 'empty' };
      if (s0.sending) return { ok: false, reason: 'busy' };
      setState((s) => ({
        messages: retry ? s.messages : [...s.messages, { id: localId('msg'), role: 'user', text: t }],
        input: retry ? s.input : '',
        sending: true,
      }));
      try {
        const { reply, logs } = await api.sendMessage(t);
        setState((s) => ({ messages: [...s.messages, reply], logs: [...s.logs, ...logs], sending: false }));
        return { ok: true, reply };
      } catch (e) {
        setState({ sending: false });
        return { ok: false, reason: 'error', error: String(e?.message ?? e) };
      }
    },

    /** 사람 승인/거절 버튼의 핸들러. decision: 'approve' | 'reject'. */
    async decide(id, decision) {
      const entry = await api.decideAudit(id, decision);
      setState((s) => ({ logs: s.logs.map((l) => (l.id === entry.id ? entry : l)) }));
      return entry;
    },

    setMobileTab: (mobileTab) => setState({ mobileTab, sheetOpen: true }),
    setSheetOpen: (sheetOpen) => setState({ sheetOpen: !!sheetOpen }),
  };
}
