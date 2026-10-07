// 챗봇 일정 묶음(kc-chat-bundle/v1) 고정 샘플 — backend 없이 화면을 보기 위한 예시다. `sample: true` 로 화면이 "예시" 를 표시한다.
// 좌표는 data/itinerary.js 의 실제 장소 좌표를 쓴다(창덕궁·익선동·경복궁). 실록 기록은 지어내지 않는다:
// 왕·날짜·요약·원문 구절은 전부 자리표시(○○, "(예시)")이고 링크는 열 수 없는 example.invalid 다. 실제 사실로 읽히면 안 된다.

const SRC = { id: 'sillok_sample', name: '조선왕조실록 (예시)', tier: 'A', locator: '(예시) ○○권 ○○번' };
const mention = (id, king, date) => ({
  article_id: id, king, date_label: date, calendar: 'lunar',
  title_summary: '(예시) 한국사DB 한글 요약 자리 — 원문이 아니다',
  title_is_summary: true,
  quote: '(예시) 한문 원문 구절 자리',
  lang: 'orig', locator: SRC.locator, url: `https://example.invalid/sillok/${id}`, tier: SRC.tier,
  source: { ...SRC, url: `https://example.invalid/sillok/${id}` },
});

export const CHAT_BUNDLE_SAMPLE = {
  schema: 'kc-chat-bundle/v1', generated_at: '2026-10-07T00:00:00Z', status: 'ok', sample: true,
  trip: { from: '2026-10-15', to: '2026-10-18' },
  itinerary: {
    anchors: [
      { type: 'hotel', name: '숙소 · 종로3가 (예시)', day: null, from: '2026-10-15T15:00', to: '2026-10-18T11:00', lat: null, lng: null, source_quote: '(예시)' },
      { type: 'visit', name: '창덕궁', day: 1, from: '2026-10-15T10:00', to: '2026-10-15T12:30', lat: 37.57964694739535, lng: 126.99099980677127, source_quote: '(예시)' },
      { type: 'visit', name: '익선동', day: 1, from: '2026-10-15T14:00', to: '2026-10-15T17:00', lat: 37.5734371942191, lng: 126.989775723896, source_quote: '(예시)' },
      { type: 'visit', name: '경복궁', day: 2, from: null, to: null, lat: 37.577613288258206, lng: 126.97689786832184, source_quote: '(예시)' },
      { type: 'visit', name: '신촌', day: 3, from: null, to: null, lat: null, lng: null, source_quote: '(예시)' },
    ],
    free_slots: [
      {
        day: 1, from: '2026-10-15T19:00', to: '2026-10-15T23:00', near: '익선동', inferred: true,
        assumption: { ko: '1일차 저녁 7시 이후가 비어 있다고 봤어요.', en: 'I assumed you are free after 7 pm on day 1.' },
      },
    ],
  },
  mentions: {
    schema: 'kc-mention/v1',
    anchors: [
      { anchor: { name: '창덕궁', lat: 37.57964694739535, lng: 126.99099980677127, day: 1 }, mentions: [mention('sample_a1', '○○왕 (예시)', '○○년 ○월 ○일 (음력, 예시)'), mention('sample_a2', '○○왕 (예시)', '○○년 ○월 ○일 (음력, 예시)')], reason: null, found_articles: 2, found_truncated: false },
      { anchor: { name: '경복궁', lat: 37.577613288258206, lng: 126.97689786832184, day: 2 }, mentions: [mention('sample_b1', '○○왕 (예시)', '○○년 ○월 ○일 (음력, 예시)')], reason: null, found_articles: 1, found_truncated: false },
      { anchor: { name: '익선동', lat: 37.5734371942191, lng: 126.989775723896, day: 1 }, mentions: [], reason: 'no_match', found_articles: 0, found_truncated: false },
    ],
  },
  events: {
    events: [{
      id: 'sample:1', title: '(예시) 저녁 야외 공연', event_type: '공연',
      schedule: { start_date: '2026-10-16', end_date: '2026-10-16' }, venue: { name: '○○ 광장 (예시)' },
      links: [{ url: 'https://example.invalid/event/sample-1', source_name: '검색 수집 (예시)', kind: 'search', tier: 'C' }], demo: true,
    }],
    excluded: [], problems: [], coverage: { complete: false, note: '예시 데이터입니다' },
  },
  cards: [],
  problems: [
    { code: 'TIME_WITHOUT_DATE', message: '경복궁: 시각을 확인하지 못했어요 (예시)' },
    { code: 'COORD_UNKNOWN', message: '신촌: 장소 사전에 없어 좌표를 비워 둠' },
  ],
  coverage_note: '예시 묶음입니다. 실제 기록이 아닙니다.',
};

export const CHAT_REPLY_SAMPLE = {
  ko: '일정 4개를 정리했어요. 실록에서 언급된 기록 3건, 주변 행사 1건을 찾았어요. (예시 응답 — 실제 검색 결과가 아닙니다)',
  en: 'I organized 4 stops. I found 3 Sillok records and 1 nearby event. (Sample response — not a real search result)',
};

/** 일정을 정리해 달라는 문장인가(mock 전용 규칙). 첫날 저녁 같은 일반 질문은 해당하지 않는다. */
export const LOOKS_LIKE_ITINERARY = /(\d\s*일\s*차|day\s*\d|일정\s*(을|좀)?\s*(짜|정리|만들|추천)|itinerary|plan my)/i;
