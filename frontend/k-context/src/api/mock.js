// mock API — data/ 의 샘플을 돌려준다. 호출마다 깊은 복사본을 주므로 호출자가 바꿔도 원본은 안전하다.
// 사람 승인(decideAudit)은 backend 의 "사람 전용 승인 API" 와 같은 개념이다: 신원(누가 승인했나)은
// 인자로 받지 않고 서버가 채운다(여기서는 'human:mock').
import { SOURCES } from '../data/sources.js';
import { CARDS } from '../data/cards.js';
import { ROUTES } from '../data/routes.js';
import { ITINERARY } from '../data/itinerary.js';
import { MESSAGES } from '../data/messages.js';
import { AUDIT_LOG } from '../data/auditlog.js';
import { NOW_RATIONALE, storyRationale } from '../data/rationale.js';
import { CHAT_BUNDLE_SAMPLE, CHAT_REPLY_SAMPLE, LOOKS_LIKE_ITINERARY } from '../data/chat-bundle.js';
import { validateChatBundle } from './bundle.js';

const clone = (v) => structuredClone(v);
const hhmmss = (d = new Date()) => d.toTimeString().slice(0, 8);
// 목업 send() 와 같은 규칙: secret|.txt|key 가 들어 있으면 공격 프롬프트로 본다.
const ATTACK = /secret|\.txt|key/i;

const REPLY_BLOCKED = {
  ko: '허용된 범위가 아니라 접근할 수 없습니다. 공개 관광 데이터로 계속 답하겠습니다.',
  en: 'That is outside the permitted scope, so I cannot access it. I will keep answering from public tourism data.',
};
const REPLY_OK = {
  ko: '1일차 저녁 7시 이후가 비어 있어 익선동 근처 확인된 야장 1곳을 제안했어요 (예시). 넣을지는 직접 정해 주세요.',
  en: 'You are free after 7 pm on day 1, so I suggested 1 confirmed night market near Ikseon-dong (sample). It is up to you whether to add it.',
};

/** @param {{latencyMs?: number}} opts latencyMs: 응답 지연(ms). 테스트는 0. */
export function createMockApi({ latencyMs = 60 } = {}) {
  const wait = () => (latencyMs > 0 ? new Promise((r) => setTimeout(r, latencyMs)) : Promise.resolve());
  // 인스턴스별 가변 상태 — 대화와 감사 로그는 호출로 쌓인다
  const messages = clone(MESSAGES);
  const audit = clone(AUDIT_LOG);
  let seq = audit.length;
  let mseq = messages.length;

  const findCard = (id) => CARDS.find((c) => c.id === id);

  return {
    mode: 'mock',

    async getItinerary() {
      await wait();
      return clone(ITINERARY);
    },
    async getRoutes() {
      await wait();
      return clone(ROUTES);
    },
    async getCards() {
      await wait();
      return clone(CARDS);
    },
    async getCard(id) {
      await wait();
      const c = findCard(id);
      if (!c) throw new Error(`카드를 찾을 수 없음: ${id}`);
      return clone(c);
    },
    async getSources() {
      await wait();
      return clone(Object.values(SOURCES));
    },
    async getRationale(cardId) {
      await wait();
      const c = findCard(cardId);
      if (!c) throw new Error(`카드를 찾을 수 없음: ${cardId}`);
      if (c.kind === 'story') return clone(storyRationale(cardId, c.badge, c.sources.length, !!c.alternatives));
      return clone(NOW_RATIONALE[cardId]);
    },
    async getMessages() {
      await wait();
      return clone(messages);
    },
    /**
     * 사용자 메시지 1건을 보내고 답을 받는다. 공격 프롬프트(파일 경로 읽기 요청 등)는 거부하고 deny 로그를 남긴다.
     * 일정 같은 문장(예: "1일차 … 2일차 …")이면 고정 샘플 묶음(예시 표시 포함)을 bundle 로 돌려준다(backend 없이 화면 확인용).
     * context 는 선택(chat-context/v1) — trip 이 있으면 샘플 묶음의 trip 을 그것으로 바꾼다.
     * @returns {{reply:{id:string,role:'agent',text:object,blocked:boolean}, logs:object[], bundle:object|null}}
     */
    async sendMessage(text, context) {
      await wait();
      const t = String(text ?? '').trim();
      if (!t) throw new Error('빈 메시지');
      const atk = ATTACK.test(t);
      const path = (t.match(/\/\S+/) || ['/secret/travel-key.txt'])[0];
      const log = atk
        ? { kind: 'deny', text: { ko: `파일 읽기 시도 → 거부 · ${path} · 허용된 폴더 밖`, en: `File read attempt → denied · ${path} · outside allowed folder` } }
        : { kind: 'ok', text: { ko: '한국관광공사 TourAPI', en: 'Korea Tourism Org. TourAPI' } };
      const entry = { id: `log_${String(++seq).padStart(3, '0')}`, time: hhmmss(), decided_by: null, ...log };
      audit.push(entry);
      messages.push({ id: `msg_${String(++mseq).padStart(3, '0')}`, role: 'user', text: t });
      const wantsBundle = !atk && LOOKS_LIKE_ITINERARY.test(t);
      const reply = { id: `msg_${String(++mseq).padStart(3, '0')}`, role: 'agent', text: atk ? REPLY_BLOCKED : wantsBundle ? CHAT_REPLY_SAMPLE : REPLY_OK, blocked: atk };
      messages.push(reply);
      let bundle = null;
      if (wantsBundle) {
        const raw = clone(CHAT_BUNDLE_SAMPLE);
        if (context?.trip?.from && context?.trip?.to) raw.trip = { from: context.trip.from, to: context.trip.to };
        const v = validateChatBundle(raw);
        bundle = v.ok ? v.bundle : null;
      }
      return clone({ reply, logs: [entry], bundle });
    },
    async getAuditLog() {
      await wait();
      return clone(audit);
    },
    /**
     * 사람 승인/거절. 대기(pend) 항목만 바꿀 수 있다. 결정자는 서버가 채운다(인자로 받지 않는다).
     * @param {string} id 로그 id
     * @param {'approve'|'reject'} decision
     */
    async decideAudit(id, decision) {
      await wait();
      if (decision !== 'approve' && decision !== 'reject') throw new Error(`decision 은 approve|reject: ${decision}`);
      const e = audit.find((x) => x.id === id);
      if (!e) throw new Error(`로그를 찾을 수 없음: ${id}`);
      if (e.kind !== 'pend') throw new Error(`대기 중인 항목만 결정할 수 있음: ${id} (${e.kind})`);
      e.kind = decision === 'approve' ? 'approved' : 'rejected';
      e.decided_by = 'human:mock';
      e.decided_at = hhmmss();
      return clone(e);
    },
  };
}
