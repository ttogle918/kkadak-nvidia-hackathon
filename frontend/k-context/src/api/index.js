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
import { createHttpApi } from './http.js';

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
