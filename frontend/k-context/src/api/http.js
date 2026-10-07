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

/** 요청 타임아웃(ms). LLM 응답이 느릴 수 있어 넉넉하되 90초 이내. */
export const REQUEST_TIMEOUT_MS = 80_000;

/** backend 오류 code -> 화면용 문구. 서버가 준 message 는 쓰지 않는다(내부 문구·세부가 새지 않게). */
const ERROR_MESSAGES = {
  busy: '잠시 후 다시 시도해 주세요',
  llm_unavailable: '챗봇이 아직 설정되지 않았습니다',
  bad_text: '입력을 확인해 주세요 (1~2000자)',
  pipeline_failed: '답을 만들지 못했습니다. 잠시 후 다시 시도해 주세요',
  timeout: '응답이 너무 오래 걸립니다. 잠시 후 다시 시도해 주세요',
  network: '서버에 연결할 수 없습니다',
  bad_response: '서버 응답을 해석하지 못했습니다',
};

function apiError(code, status) {
  const e = new Error(ERROR_MESSAGES[code] ?? `요청에 실패했습니다 (${status ?? '?'})`);
  e.code = code;
  if (status != null) e.status = status;
  return e;
}

/** JSON 요청. 실패는 항상 {code, message(고정 문구)} 를 가진 Error 로 바꾼다. */
async function requestJson(baseUrl, path, { method = 'GET', body, timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let res;
  try {
    res = await fetch(`${baseUrl}${path}`, {
      method,
      signal: ctrl.signal,
      ...(body === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
    });
  } catch (e) {
    throw apiError(ctrl.signal.aborted ? 'timeout' : 'network');
  } finally {
    clearTimeout(timer);
  }
  let data;
  try {
    data = await res.json();
  } catch {
    data = undefined;
  }
  if (!res.ok) {
    const code = typeof data?.error?.code === 'string' ? data.error.code : 'http_error';
    throw apiError(code, res.status);
  }
  if (data === undefined) throw apiError('bad_response', res.status);
  return data;
}

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
    /** GET /messages -> Message[] (backend/routers/messages.py) */
    async getMessages() {
      const data = await requestJson(baseUrl, '/messages');
      if (!Array.isArray(data)) throw apiError('bad_response');
      return data;
    },
    /** POST /messages {text} -> {reply, logs}. reply.text 는 문자열(정상) 또는 {ko,en}(차단). 신원은 보내지 않는다. */
    async sendMessage(text) {
      const data = await requestJson(baseUrl, '/messages', { method: 'POST', body: { text } });
      if (!data || typeof data.reply !== 'object' || data.reply === null) throw apiError('bad_response');
      return { reply: data.reply, logs: Array.isArray(data.logs) ? data.logs : [] };
    },
    getAuditLog: nope('getAuditLog'),
    async decideAudit(id, decision) { // eslint-disable-line no-unused-vars
      throw new ApiNotImplementedError('decideAudit', baseUrl);
    },
  };
}
