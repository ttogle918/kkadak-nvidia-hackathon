// http API — 실제 backend 연결 자리(스텁). mock.js 와 같은 메서드 이름·시그니처를 가진다.
// 아직 backend 계약이 없어서 모든 메서드가 ApiNotImplementedError 를 던진다.
// 구현할 때: ENDPOINTS 표(제안)를 확정하고 request() 로 채운다. 신원(요청자·승인자)은 클라이언트가 보내지 않는다 — 서버가 세션에서 정한다.

export class ApiNotImplementedError extends Error {
  constructor(method, baseUrl) {
    super(`http API 의 ${method}() 는 아직 구현되지 않았습니다 (baseUrl=${baseUrl}). createApi({mode:'mock'}) 를 쓰세요.`);
    this.name = 'ApiNotImplementedError';
    this.method = method;
  }
}

/** 제안 엔드포인트(미확정). */
export const ENDPOINTS = {
  getItinerary: 'GET /itinerary',
  getRoutes: 'GET /routes',
  getCards: 'GET /cards',
  getCard: 'GET /cards/{id}',
  getSources: 'GET /sources',
  getRationale: 'GET /cards/{id}/rationale',
  getMessages: 'GET /messages',
  sendMessage: 'POST /messages  {text}',
  getAuditLog: 'GET /audit',
  decideAudit: 'POST /audit/{id}/decision  {decision}  — 사람 전용 승인 API',
};

export function createHttpApi({ baseUrl = '/api' } = {}) {
  const nope = (method) => async () => {
    throw new ApiNotImplementedError(method, baseUrl);
  };
  // 인자 개수(length)를 mock 과 맞추기 위해 이름 있는 함수로 둔다.
  return {
    mode: 'http',
    baseUrl,
    getItinerary: nope('getItinerary'),
    getRoutes: nope('getRoutes'),
    getCards: nope('getCards'),
    async getCard(id) { // eslint-disable-line no-unused-vars
      throw new ApiNotImplementedError('getCard', baseUrl);
    },
    getSources: nope('getSources'),
    async getRationale(cardId) { // eslint-disable-line no-unused-vars
      throw new ApiNotImplementedError('getRationale', baseUrl);
    },
    getMessages: nope('getMessages'),
    async sendMessage(text) { // eslint-disable-line no-unused-vars
      throw new ApiNotImplementedError('sendMessage', baseUrl);
    },
    getAuditLog: nope('getAuditLog'),
    async decideAudit(id, decision) { // eslint-disable-line no-unused-vars
      throw new ApiNotImplementedError('decideAudit', baseUrl);
    },
  };
}
