// store 초기 상태. 키는 목업(K-Context.dc.html)의 state 에서 도출했다. 표는 README 의 "store 상태 키".
//
//   목업 state        -> 이 프로젝트
//   lang              -> lang
//   mode              -> mode            'old' | 'now' | 'both'
//   day               -> day             1 | 2 | 3
//   seg               -> selectedSeg     선택한 옛날 구간의 card_id (예: 'card_old_4'). 없으면 null
//   tag               -> selectedTag     열어 둔 출처 태그의 source id (예: 'doc_03'). 없으면 null
//   ev                -> openEvidence    판단 근거 패널에서 연 항목 key. 없으면 null
//   imm               -> immersion       몰입 층 켬/끔
//   min               -> minimizeChanges 일정 최소 변경 토글
//   added / skipped   -> added / skipped 지금 카드(selectedNow)를 일정에 넣었는지/건너뛰었는지
//   hn                -> hoverFact       사실 층 문장 하이라이트(출처 번호 1~) 또는 null
//   exp               -> expandedTags    {[카드 id]: true} — "+N 출처" 를 펼친 카드
//   sec               -> securityOpen    보안 로그 패널(데스크톱 ⚙) 열림
//   input / msgs / logs -> input / messages / logs
//
// 이 프로젝트에서 새로 생긴 키: data(api 로 받은 원본), loaded/error, sending, selectedRoute, selectedNow,
//   mobileTab/sheetOpen(모바일 시트), theme, settingsOpen, panelLevel(하단 패널 높이 단계).

/** @param {object} overrides 테스트·URL 파라미터로 덮어쓸 값 */
export function createInitialState(overrides = {}) {
  return {
    // --- 화면 설정 ---
    lang: 'ko',
    theme: 'auto', // 'auto' | 'light' | 'dark'  (auto = prefers-color-scheme)
    mode: 'both',
    day: 1,
    minimizeChanges: true,
    immersion: true,
    // --- 선택·열림 ---
    selectedRoute: 'A', // 경로 id
    selectedSeg: 'card_old_4', // 옛날 구간 card_id | null
    selectedNow: 'card_now_1', // 지금 카드 id | null
    selectedTag: null,
    expandedTags: {},
    openEvidence: null,
    hoverFact: null,
    securityOpen: true,
    settingsOpen: false, // 설정 패널(보안 로그·언어·테마·최소 변경) 열림
    // --- 일정 결정(selectedNow 카드에 대한 것) ---
    added: false,
    skipped: false,
    // --- 대화·로그 ---
    input: '',
    messages: [],
    logs: [],
    sending: false,
    // --- api 로 받은 원본 (loadAll 이 채운다) ---
    data: { itinerary: null, routes: null, cards: null, sources: null },
    loaded: false,
    error: null,
    // --- 하단 패널 높이 단계 ---
    panelLevel: 'default', // 'collapsed' | 'default' | 'expanded'
    // --- 모바일 시트 ---
    mobileTab: 'chat', // 'chat' | 'timeline'
    sheetOpen: false,
    ...overrides,
  };
}

export const STATE_KEYS = Object.keys(createInitialState());
