// API 진입점. 모듈은 ctx.api 로만 데이터에 접근한다(직접 data/ 를 import 하지 않는다).
//
// 모든 메서드는 Promise 를 돌려준다. 시그니처(mock 과 http 가 같다):
//   getItinerary()                -> Itinerary(data/itinerary.js)
//   getRoutes()                   -> Route[]                (A·B·C)
//   getCards()                    -> Card[]                 (옛날 3 + 지금 3)
//   getCard(id)                   -> Card                   (없으면 reject)
//   getSources()                  -> Source[]
//   getRationale(cardId)          -> {card_id, chips, items} (data/rationale.js)
//   getMessages()                 -> Message[]
//   sendMessage(text)             -> {reply: Message, logs: AuditEntry[]}
//   getAuditLog()                 -> AuditEntry[]
//   decideAudit(id, decision)     -> AuditEntry             (decision: 'approve'|'reject', 사람 전용)
import { createMockApi } from './mock.js';
import { createHttpApi, probeBackend } from './http.js';

/** 챗봇 backend 기본 주소: uvicorn 기본 포트. backend CORS 기본 허용 origin 은 http://localhost:8766. */
export const DEFAULT_CHAT_BASE = 'http://localhost:8000/api';

export const API_METHODS = [
  'getItinerary', 'getRoutes', 'getCards', 'getCard', 'getSources', 'getRationale',
  'getMessages', 'sendMessage', 'getAuditLog', 'decideAudit',
];

/**
 * 실제 모드('chat'·'http')에서 backend 로 보내는 메서드. 나머지(itinerary·routes·cards·sources·card·rationale)는 예시를 쓰지 않고
 * 빈 값을 돌려준다(D17) — 화면 데이터의 출처는 채팅 묶음이다.
 */
export const HTTP_METHODS = ['getMessages', 'sendMessage', 'getAuditLog', 'decideAudit'];

/**
 * 화면 데이터의 출처 종류(표시용 메타 — 응답을 감싸지 않는다). api.dataKinds[키] 값:
 *  'mock'    프론트 data/ 의 고정 예시   'fixture' 서버가 주지만 backend/fixtures/screen 의 고정 예시(mock 과 같은 내용)
 *  'server'  실제 서버 응답              'none'    아직 서버에 없음(호출하면 ApiNotImplementedError)
 *  'empty'   예시 없음 — 빈 값           'bundle'  채팅 묶음 안에서 온다(별도 호출 없음)
 * 키: itinerary·routes·cards·sources·rationale·messages·audit. 'empty'·'bundle'·'server' 는 MOCK 이 아니다.
 */
const REAL_KINDS = { itinerary: 'empty', routes: 'empty', cards: 'empty', sources: 'empty', rationale: 'bundle', messages: 'server', audit: 'server' };
export const DATA_KINDS = {
  mock: { itinerary: 'mock', routes: 'mock', cards: 'mock', sources: 'mock', rationale: 'mock', messages: 'mock', audit: 'mock' },
  chat: { ...REAL_KINDS },
  http: { ...REAL_KINDS },
};

/** 실제 모드의 "예시 없음" 메서드. 카드·근거는 서버 호출 없이 not_found. */
function emptyMethods() {
  const notFound = () => Object.assign(new Error('찾을 수 없습니다'), { code: 'not_found' });
  return {
    async getItinerary() { return { anchors: [], free_slots: [], timeline: [], landmarks: [] }; },
    async getRoutes() { return []; },
    async getCards() { return []; },
    async getCard(id) { throw notFound(id); }, // eslint-disable-line no-unused-vars
    async getSources() { return []; },
    async getRationale(cardId) { throw notFound(cardId); }, // eslint-disable-line no-unused-vars
  };
}

/** @param {{mode?:'mock'|'http'|'chat', baseUrl?:string, latencyMs?:number}} opts */
export function createApi({ mode = 'mock', baseUrl, latencyMs } = {}) {
  if (mode === 'mock') return { ...createMockApi({ latencyMs }), dataKinds: { ...DATA_KINDS.mock } };
  if (mode === 'http' || mode === 'chat') {
    // 실제 모드: HTTP_METHODS 만 backend. 예시는 쓰지 않는다(빈 값).
    const http = createHttpApi({ baseUrl });
    const api = { ...emptyMethods(), mode, baseUrl: http.baseUrl, dataKinds: { ...DATA_KINDS[mode] } };
    for (const n of HTTP_METHODS) api[n] = http[n];
    return api;
  }
  throw new Error(`알 수 없는 api mode: ${mode} (mock|http|chat)`);
}

/**
 * 기본 진입점. mode 가 'auto' 이면 backend 를 한 번 찔러 보고(probe) 떠 있으면 'chat', 아니면 'mock' 으로 간다.
 * 명시 모드(mock|http|chat)는 그대로 쓴다 — 'chat' 을 강제하면 backend 가 없어도 mock 으로 넘어가지 않는다.
 * 폴백은 부팅 시점에 한 번만 정한다(실행 중 오류를 mock 답으로 덮지 않는다). 결과 api.mode 로 어느 쪽인지 알 수 있다.
 * @param {{mode?:'auto'|'mock'|'http'|'chat', baseUrl?:string, latencyMs?:number, probeMs?:number}} opts
 */
export async function resolveApi({ mode = 'auto', baseUrl, latencyMs, probeMs } = {}) {
  // 명시 chat·http 에 base 가 없으면 auto 와 같은 기본 주소(같은 출처 /api 는 정적 서버로 가서 501 이 난다)
  if (mode !== 'auto') return createApi({ mode, baseUrl: mode === 'mock' ? baseUrl : baseUrl || DEFAULT_CHAT_BASE, latencyMs });
  const base = baseUrl || DEFAULT_CHAT_BASE;
  const up = await probeBackend(base, probeMs);
  return up ? createApi({ mode: 'chat', baseUrl: base, latencyMs }) : createApi({ mode: 'mock', latencyMs });
}
