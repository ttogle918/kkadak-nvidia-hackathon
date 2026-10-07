// http API — 실제 backend 연결. mock.js 와 같은 메서드 이름·시그니처를 가진다.
// 연결된 것: getMessages·sendMessage·getCards·getCard·getSources·getRationale. 나머지는 아직 ApiNotImplementedError.
// 구현할 때: ENDPOINTS 표(제안)를 확정하고 request() 로 채운다. 신원(요청자·승인자)은 클라이언트가 보내지 않는다 — 서버가 세션에서 정한다.

import { validateCard, validateSource } from './schema.js';

export class ApiNotImplementedError extends Error {
  constructor(method, baseUrl) {
    super(`http API 의 ${method}() 는 아직 구현되지 않았습니다 (baseUrl=${baseUrl}). createApi({mode:'mock'}) 를 쓰세요.`);
    this.name = 'ApiNotImplementedError';
    this.method = method;
  }
}

/** 엔드포인트. cards·sources·rationale·messages 는 backend 에 있고 나머지는 제안(미확정). */
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
  not_found: '찾을 수 없습니다',
  bad_id: '요청 형식이 올바르지 않습니다',
  internal_error: '서버에서 오류가 발생했습니다',
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

/** 백엔드가 떠 있는지 짧게 확인한다(GET /messages 가 JSON 배열이면 true). 어떤 실패도 throw 하지 않는다. */
export async function probeBackend(baseUrl, timeoutMs = 2500) {
  try {
    const data = await requestJson(baseUrl, '/messages', { timeoutMs });
    return Array.isArray(data);
  } catch {
    return false;
  }
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
    /** GET /cards -> Card[] (backend/routers/screen.py). 형식이 어긋나면 bad_response. */
    async getCards() {
      const data = await requestJson(baseUrl, '/cards');
      if (!Array.isArray(data) || data.some((c) => validateCard(c).length > 0)) throw apiError('bad_response');
      return data;
    },
    async getCard(id) {
      const data = await requestJson(baseUrl, `/cards/${encodeURIComponent(String(id))}`);
      if (validateCard(data).length > 0) throw apiError('bad_response');
      return data;
    },
    /** GET /sources -> Source[] */
    async getSources() {
      const data = await requestJson(baseUrl, '/sources');
      if (!Array.isArray(data) || data.some((s) => validateSource(s).length > 0)) throw apiError('bad_response');
      return data;
    },
    /** GET /cards/{id}/rationale -> {card_id, chips[], items{}} */
    async getRationale(cardId) {
      const data = await requestJson(baseUrl, `/cards/${encodeURIComponent(String(cardId))}/rationale`);
      if (!data || typeof data !== 'object' || !Array.isArray(data.chips) || typeof data.items !== 'object' || data.items === null) throw apiError('bad_response');
      return data;
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
