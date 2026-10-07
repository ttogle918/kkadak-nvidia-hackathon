// 출처 샘플. 계약 형식(AGENT_CONTEXT 3.3 sources[]). 모든 문구·URL 은 자리표시("○○", example.org)이며 실제 서지가 아니다.
// bib: 계약에 없는 확장 필드 — url 이 없는 문헌의 서지 문자열(목업의 bib).
// 목업의 TAGS t1~t5 는 doc_01~doc_05 로 옮겼다.

export const SOURCES = {
  doc_01: {
    id: 'doc_01', tier: 'S', name: '조선왕조실록 (예시)', locator: '○○ ○년 ○월 ○일',
    url: '', bib: '○○실록 권○ · 자리 표시용 서지',
    published: '○○', collected_at: '2026-10-05', quote: '「○○○○ 행차 ○○…」 (예시 원문 구절)',
  },
  doc_02: {
    id: 'doc_02', tier: 'A', name: '서울지명사전 (예시)', locator: 'p.214',
    url: '', bib: '서울지명사전, 자리 표시용 서지, p.214',
    published: '○○', collected_at: '2026-10-05', quote: '「○○ 일대에 ○○ 물길이 있었다」 (예시 구절)',
  },
  doc_03: {
    id: 'doc_03', tier: 'B', name: '한국관광공사 TourAPI', locator: '2026-10-05 갱신',
    url: 'https://example.org/tourapi/○○',
    published: '2026-10-05', collected_at: '2026-10-05', quote: '행사명 ○○ 야장 / 기간 10/15–10/18 (예시)',
  },
  doc_04: {
    id: 'doc_04', tier: 'B', name: '종로구청 공지', locator: '2026-10-02 게시',
    url: 'https://example.org/jongno/notice/○○',
    published: '2026-10-02', collected_at: '2026-10-05', quote: '○○ 야장 운영 안내, 19:30 시작 (예시)',
  },
  doc_05: {
    id: 'doc_05', tier: 'B', name: '포스터에서 읽음', locator: '중구청 게시물 첨부',
    url: 'https://example.org/jung/board/○○ · 첨부 poster.jpg',
    published: '○○', collected_at: '2026-10-05', quote: '포스터 이미지에서 읽은 날짜·시간·장소 (예시)',
  },
  // 아래 3건은 목업 3종 지금 카드(8b·8c)의 태그 문구에서 추가했다. quote 는 자리표시.
  doc_06: {
    id: 'doc_06', tier: 'B', name: '종로구청 공지', locator: '2026-10-04 게시',
    url: 'https://example.org/jongno/notice/△△',
    published: '2026-10-04', collected_at: '2026-10-05', quote: '△△ 시장 행사 안내 (예시)',
  },
  doc_07: {
    id: 'doc_07', tier: 'B', name: '종로구청 공지', locator: '2026-10-03 게시',
    url: 'https://example.org/jongno/notice/◇◇',
    published: '2026-10-03', collected_at: '2026-10-05', quote: '◇◇ 공연은 운영 (예시)',
  },
  doc_08: {
    id: 'doc_08', tier: 'C', name: '주최 측 게시물', locator: 'social.example.com',
    url: 'https://social.example.com/○○',
    published: '○○', collected_at: '2026-10-05', quote: '◇◇ 공연은 우천 시 취소 (예시)',
  },
};

/** id 목록 -> 출처 객체 복사본 배열(순서 유지). 카드의 sources 를 만들 때 쓴다. */
export function pickSources(ids) {
  return ids.map((id) => {
    if (!SOURCES[id]) throw new Error(`알 수 없는 출처 id: ${id}`);
    return { ...SOURCES[id] };
  });
}
