// 상태 전이 모음. 모듈들이 같은 동작을 따로 구현하지 않도록 ctx.actions 로 공유한다.
// 쓰기 규칙: 에이전트가 쓰는 도구는 draft 만 만든다. 여기서도 decide() 는 "사람이 누른 버튼" 에서만 호출한다
// (신원은 서버가 정하므로 인자로 받지 않는다).
import { normalizeLang } from '../lib/i18n.js';
import { isLevel, stepLevel } from '../lib/panel-level.js';
import { buildChatContext } from '../api/bundle.js';
import { bundleDays } from '../lib/chat-bundle.js';
import { isRealApi } from './selectors.js';
import { evalTrip, saveStoredTrip } from '../lib/trip.js';
import { sanitizeAuditEntry } from '../api/http.js';

export function createActions({ store, api }) {
  const { getState, setState } = store;
  let seq = 0;
  const localId = (p) => `${p}_local_${++seq}`;

  /**
   * 요청에 실을 context(chat-context/v1): 화면 언어 + 여행 기간.
   * 실제 모드(D22): trip 은 화면 입력·URL 에서만 만든다 — 예시(MOCK) 일정의 기간은 절대 싣지 않는다.
   * mock 모드는 예시 일정을 보여 주는 화면이라 예시 일정의 trip 을 그대로 쓴다(예시 화면 동작 유지).
   */
  const chatContext = () => {
    const s = getState();
    return buildChatContext({ lang: s.lang, trip: isRealApi(api) ? evalTrip(s.tripInput).trip : s.data?.itinerary?.trip });
  };
  /**
   * 응답 bundle 을 상태에 반영하는 패치. 앵커가 있는 새 일정이 오면 chatBundle 과 첫 날짜로 바뀌고,
   * bundle 이 없거나(일반 대화) 앵커가 없으면 기존 화면을 그대로 둔다.
   */
  const bundlePatch = (bundle) => {
    if (!bundle || !bundle.itinerary?.anchors?.length) return {};
    // 실제 모드: 새 묶음이면 이전 선택(근거 패널)을 비운다 — 예시 카드가 아니라 묶음의 카드를 고르게 한다
    const reset = isRealApi(api) ? { selectedSeg: null, selectedNow: null, openEvidence: null } : {};
    return { chatBundle: bundle, day: bundleDays(bundle)[0] ?? getState().day, ...reset };
  };
  /** 실제 모드에서 서버의 보안 로그로 logs 를 바꾼다. 실패하면 false(호출자가 응답에 딸린 로그를 쓴다). */
  const refreshAudit = async () => {
    try {
      setState({ logs: await api.getAuditLog() });
      return true;
    } catch {
      return false;
    }
  };

  /** 실제 모드에서 보안 로그 새로고침이 실패했을 때 응답에 딸린 로그: 항목마다 sanitize 를 거친다(mock 은 그대로). */
  const extraLogs = (logs) => (isRealApi(api) ? (logs ?? []).map(sanitizeAuditEntry).filter(Boolean) : logs);

  return {
    /** api 에서 원본을 한 번에 받아 store 에 넣는다. main.js 가 부팅할 때 부른다. */
    async loadAll() {
      const real = isRealApi(api);
      // 실제 모드: 기본 선택은 없음(예시 카드 id 를 들고 있지 않는다). getCard·getRationale 는 부르지 않는다.
      if (real) setState({ selectedSeg: null, selectedNow: null, openEvidence: null });
      try {
        const [itinerary, routes, cards, sources, messages, logs] = await Promise.all([
          api.getItinerary(), api.getRoutes(), api.getCards(), api.getSources(), api.getMessages(), api.getAuditLog(),
        ]);
        setState({ data: { itinerary, routes, cards, sources }, messages, logs, loaded: true, error: null });
      } catch (e) {
        setState({ loaded: false, error: String(e?.message ?? e) });
      }
    },

    /** 여행 기간 입력(D22). 값은 문자열만 받고 localStorage 에 기억한다(실패해도 무시). */
    setTripInput: (from, to) => {
      const input = { from: typeof from === 'string' ? from : '', to: typeof to === 'string' ? to : '' };
      setState({ tripInput: input });
      saveStoredTrip(input);
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
    /**
     * 묶음의 실록 언급 카드('mention')나 행사 카드('event')를 골라 근거 패널을 채운다(id 는 접두어 없는 카드·행사 id).
     * 하나만 고르고, 보기 모드가 그 종류를 숨기고 있으면 둘 다 보기로 바꾼다.
     */
    selectBundleItem: (kind, id) => setState((s) => {
      if (typeof id !== 'string' || !id) return {};
      const mention = kind === 'mention';
      const mode = (mention && s.mode === 'now') || (!mention && s.mode === 'old') ? 'both' : s.mode;
      return {
        selectedSeg: mention ? id : null, selectedNow: mention ? null : id, mode,
        hoverFact: null, openEvidence: null, added: false, skipped: false,
      };
    }),
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
        const { reply, logs, bundle } = await api.sendMessage(t, chatContext());
        const fresh = isRealApi(api) && (await refreshAudit()); // 실제 모드: 보안 로그는 서버 기록만
        setState((s) => ({ messages: [...s.messages, reply], ...(fresh ? {} : { logs: [...s.logs, ...extraLogs(logs)] }), sending: false, ...bundlePatch(bundle) }));
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
        const { reply, logs, bundle } = await api.sendMessage(t, chatContext());
        const fresh = isRealApi(api) && (await refreshAudit()); // 실제 모드: 보안 로그는 서버 기록만
        setState((s) => ({ messages: [...s.messages, reply], ...(fresh ? {} : { logs: [...s.logs, ...extraLogs(logs)] }), sending: false, ...bundlePatch(bundle) }));
        return { ok: true, reply };
      } catch (e) {
        setState({ sending: false });
        return { ok: false, reason: 'error', error: String(e?.message ?? e) };
      }
    },

    /** 챗봇이 정리한 일정을 닫고 기본(샘플) 화면으로 돌아간다. 읽기 전용 화면 상태만 바꾼다. */
    clearChatBundle: () => setState(isRealApi(api) ? { chatBundle: null, day: 1, selectedSeg: null, selectedNow: null, openEvidence: null } : { chatBundle: null, day: 1 }),

    /** 사람 승인/거절 버튼의 핸들러. decision: 'approve' | 'reject'. */
    async decide(id, decision) {
      const entry = await api.decideAudit(id, decision);
      setState((s) => ({ logs: s.logs.map((l) => (l.id === entry.id ? entry : l)) }));
      return entry;
    },

    /** 하단 패널 높이 단계(핸들 소유는 app-shell). 모르는 값은 무시한다. */
    setPanelLevel: (level) => { if (isLevel(level)) setState({ panelLevel: level }); },
    /** 한 단계 위(+1)/아래(-1). */
    stepPanel: (dir) => setState((s) => ({ panelLevel: stepLevel(s.panelLevel, dir) })),

    setMobileTab: (mobileTab) => setState({ mobileTab, sheetOpen: true }),
    setSheetOpen: (sheetOpen) => setState({ sheetOpen: !!sheetOpen }),
  };
}
