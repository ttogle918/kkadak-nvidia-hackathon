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

/** @param {{mode?:'mock'|'http', baseUrl?:string, latencyMs?:number}} opts */
export function createApi({ mode = 'mock', baseUrl, latencyMs } = {}) {
  if (mode === 'mock') return createMockApi({ latencyMs });
  if (mode === 'http') return createHttpApi({ baseUrl });
  if (mode === 'chat') {
    // 하이브리드: 챗봇(getMessages·sendMessage)만 실제 backend, 나머지는 mock.
    const http = createHttpApi({ baseUrl });
    return { ...createMockApi({ latencyMs }), mode: 'chat', baseUrl: http.baseUrl, getMessages: http.getMessages, sendMessage: http.sendMessage };
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
  if (mode !== 'auto') return createApi({ mode, baseUrl, latencyMs });
  const base = baseUrl || DEFAULT_CHAT_BASE;
  const up = await probeBackend(base, probeMs);
  return up ? createApi({ mode: 'chat', baseUrl: base, latencyMs }) : createApi({ mode: 'mock', latencyMs });
}
