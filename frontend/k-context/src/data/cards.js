// 카드 샘플(옛날 3 + 지금 3). 계약 형식(AGENT_CONTEXT 3.3 카드 JSON)을 따르고, 아래 확장 필드를 더한다.
// 문자열 필드는 string 또는 {ko,en} — ctx.t() 가 둘 다 처리한다(실제 API 는 language 에 맞는 string 을 줄 수 있다).
//
// 확장 필드(계약 외, 목업 화면에 필요해서 추가 — 정식 채택은 AGENT_CONTEXT 3.3 수정 후):
//   era            옛날: 시대 표기              facts[]   옛날: 사실 층 문장 {text, ref} (ref = sources 의 1부터 센 번호)
//   alternatives   옛날 이설 병기 [{label,text}]  checks[]  지금: 확인 항목 {level:'ok'|'warn'|'bad', text}
//   poster         지금: {read: 포스터에서 읽은 내용}  only  지금: 유효 범위 문구   warning  {title, body} 경고 박스
//   kind_label     지금: 야장/시장/공연 같은 종류 라벨
//   geometry.space 'schematic' 이면 coords 가 목업 지도 좌표계(viewBox 0 0 600 700)의 [x,y] — 실제 API 는 [lat,lng]
//   place.lat/lng  샘플은 null(실제 좌표를 지어내지 않는다)
import { pickSources } from './sources.js';

const SCH = 'schematic';
const EX = { ko: '○○ (예시)', en: '○○ (sample)' };
const factsBody = (facts) => ({
  ko: facts.map((f) => f.text.ko).join(' '),
  en: facts.map((f) => f.text.en).join(' '),
});

const oldFacts1 = [
  { text: { ko: '이 구간은 ○○ 기록에 행차로로 나온다.', en: 'This section appears in ○○ records as a processional road.' }, ref: 1 },
  { text: { ko: '길 폭은 ○○ 정도였다고 적혀 있다.', en: 'Its width is noted as about ○○.' }, ref: 2 },
];
const oldFacts2 = [
  { text: { ko: '옛길과 대체로 겹친다고 추정된다.', en: 'It is presumed to roughly overlap the old road.' }, ref: 1 },
  { text: { ko: '직접 기록은 확인되지 않았다.', en: 'No direct record has been found.' }, ref: 1 },
];
const oldFacts4 = [
  { text: { ko: '이 길 아래로 ○○ 물길이 흐르던 것으로 전해진다.', en: 'A stream is said to have run beneath this road.' }, ref: 1 },
  { text: { ko: '물길이 덮인 시기는 자료마다 달라 두 설이 있다.', en: 'Sources differ on when it was covered, so two accounts exist.' }, ref: 2 },
];

const base = {
  place: null, slot: null, time_cost_min: null, stay_min: null, valid: null,
  why_fits: [], caveats: [], local_context: null, narration: null, rejected: [],
  era: null, facts: [], alternatives: null, checks: [], poster: null, only: null, warning: null, kind_label: null,
  user_state: 'proposed',
};
const place = (ko, en) => ({ name: { ko, en }, lat: null, lng: null });

export const CARDS = [
  // ---- 옛날 (이야기 길) ----
  {
    ...base, id: 'card_old_1', kind: 'story',
    title: { ko: '왕이 지나던 길 (예시)', en: "The King's Passage (sample)" },
    place: place('○○로 ○○ 구간', '○○-ro, section ○○'),
    geometry: { type: 'segment', coords: [[90, 70], [210, 100], [300, 100]], basis: EX, space: SCH },
    era: { ko: '○○ 시대', en: '○○ era' },
    facts: oldFacts1, body: factsBody(oldFacts1), badge: '기록',
    sources: pickSources(['doc_01', 'doc_02']),
    narration: {
      ko: '당신은 지금 ○○년의 이 길에 서 있습니다. 앞쪽으로 행렬의 먼지가 일고 있습니다…',
      en: 'You are standing on this road in the year ○○. Dust rises ahead where the procession passes…',
    },
  },
  {
    ...base, id: 'card_old_2', kind: 'story',
    title: { ko: '백성이 피해 다닌 뒷골목 (예시)', en: 'The Back Alley Locals Avoided (sample)' },
    place: place('○○ 뒷골목', '○○ back alley'),
    geometry: { type: 'segment', coords: [[300, 100], [300, 170], [300, 230]], basis: EX, space: SCH },
    era: { ko: '○○ 시대', en: '○○ era' },
    facts: oldFacts2, body: factsBody(oldFacts2), badge: '추정',
    sources: pickSources(['doc_02']),
    narration: {
      ko: '당신은 지금 ○○년의 이 골목에 서 있습니다. 큰길을 피한 발걸음들이 이곳으로 모입니다…',
      en: 'You are in this alley in the year ○○. Footsteps that avoided the main road gather here…',
    },
  },
  {
    ...base, id: 'card_old_4', kind: 'story',
    title: { ko: '지금은 덮인 물길 위 (예시)', en: 'Above the Covered Stream (sample)' },
    place: place('○○ 물길 옛 자리', 'Former ○○ stream bed'),
    geometry: { type: 'segment', coords: [[400, 230], [470, 230]], basis: EX, space: SCH },
    era: { ko: '○○ 시대', en: '○○ era' },
    facts: oldFacts4, body: factsBody(oldFacts4), badge: '전승',
    sources: pickSources(['doc_02', 'doc_01']),
    alternatives: [
      { label: { ko: '설 A', en: 'Account A' }, text: { ko: '○○ 시기에 덮임 (자료 ①)', en: 'Covered in ○○ (source ①)' } },
      { label: { ko: '설 B', en: 'Account B' }, text: { ko: '△△ 시기에 덮임 (자료 ②)', en: 'Covered in △△ (source ②)' } },
    ],
    narration: {
      ko: '당신은 지금 ○○년의 이 길에 서 있습니다. 발밑으로 물소리가 지나갑니다…',
      en: 'You are standing on this road in the year ○○. Water murmurs beneath your feet…',
    },
  },

  // ---- 지금 (지금의 한국) ----
  {
    ...base, id: 'card_now_1', kind: 'now',
    title: { ko: '○○ 야장', en: '○○ Night Market' }, kind_label: { ko: '야장', en: 'NIGHT MKT' },
    place: place('야장 골목 ○○', 'Night-market alley ○○'),
    geometry: { type: 'segment', coords: [[470, 232], [470, 328]], radius_m: null, basis: { ko: '주소 (예시)', en: 'address (sample)' }, space: SCH },
    body: { ko: '익선동에서 야장 골목까지 들렀다 가는 제안입니다 (예시).', en: 'A suggested detour from Ikseon-dong to the night-market alley (sample).' },
    badge: '확인됨',
    sources: pickSources(['doc_03', 'doc_04', 'doc_05', 'doc_02']),
    slot: { day: 1, at: '19:30', between: [{ ko: '익선동', en: 'Ikseon-dong' }, { ko: '숙소', en: 'hotel' }] },
    time_cost_min: 12, stay_min: 70,
    valid: { from: '2026-10-15', to: '2026-10-18', as_of: '2026-10-05' },
    only: { ko: '여행 기간에만 열림', en: 'Only during your trip' },
    why_fits: [
      { ko: '관심사와 일치: 한국 음식, 로컬 문화', en: 'Matches: Korean food, local culture' },
      { ko: '여행 날짜에 열림 (10/15–18)', en: 'Open on your travel dates (10/15–18)' },
      { ko: '일정을 거의 바꾸지 않음 (빈 시간 안)', en: 'Barely changes your plan (fits free time)' },
    ],
    checks: [
      { level: 'ok', text: { ko: '공식 출처', en: 'Official source' } },
      { level: 'ok', text: { ko: '날짜 확인됨', en: 'Date confirmed' } },
      { level: 'ok', text: { ko: '2일 전 갱신', en: 'Updated 2 days ago' } },
    ],
    poster: { read: { ko: '날짜 10/15–18 · 19:30 시작 · ○○ 골목 (예시)', en: 'Oct 15–18 · from 19:30 · ○○ alley (sample)' } },
    caveats: [
      { ko: '현금만 가능', en: 'Cash only' },
      { ko: '대기 있음', en: 'Possible queue' },
      { ko: '우천 시 미운영', en: 'Closed if raining' },
    ],
    local_context: {
      text: { ko: '이 골목의 지명은 ○○에서 왔다고 전해집니다.', en: "This alley's name is said to come from ○○." },
      story_card_id: 'card_old_4',
    },
    rejected: [
      {
        claim: { ko: '포스터: 19:00 시작', en: 'Poster: starts 19:00' },
        reason: { ko: '나중에 올라온 공식 변경 공지(19:30)를 채택, 포스터 시간은 참고로 남김', en: 'Chose the later official notice (19:30); kept the poster time as reference' },
      },
    ],
  },
  {
    ...base, id: 'card_now_2', kind: 'now',
    title: { ko: '△△ 시장 행사', en: '△△ Market Event' }, kind_label: { ko: '시장', en: 'MARKET' },
    place: place('○○동 일대', '○○-dong area'),
    geometry: { type: 'approx', coords: [[140, 290]], radius_m: 150, basis: { ko: '포스터 문구 (예시)', en: 'poster text (sample)' }, space: SCH },
    body: { ko: '경복궁과 광화문 사이에 들를 수 있는 시장 행사입니다 (예시).', en: 'A market event you could drop into between Gyeongbokgung and Gwanghwamun (sample).' },
    badge: '확인 필요',
    sources: pickSources(['doc_06', 'doc_05']),
    slot: { day: 2, at: '13:00', between: [{ ko: '경복궁', en: 'Gyeongbokgung' }, { ko: '광화문', en: 'Gwanghwamun' }] },
    time_cost_min: 8, stay_min: null,
    valid: { from: '2026-10-16', to: '2026-10-16', as_of: '2026-10-05' },
    only: { ko: '여행 기간에만 열림', en: 'Only during your trip' },
    why_fits: [
      { ko: '관심사와 일치: 한국 음식', en: 'Matches: Korean food' },
      { ko: '여행 날짜에 열림 (10/16)', en: 'Open on your travel dates (10/16)' },
      { ko: '일정을 거의 바꾸지 않음 (+8분)', en: 'Barely changes your plan (+8 min)' },
    ],
    checks: [
      { level: 'ok', text: { ko: '공식 출처', en: 'Official source' } },
      { level: 'warn', text: { ko: '날짜 불분명 (종료일 미기재)', en: 'Date unclear (no end date)' } },
      { level: 'warn', text: { ko: '출처 1건 (단독)', en: 'Single source' } },
    ],
    poster: { read: { ko: '10/16 · 시간 미기재 · ○○동 일대 (예시)', en: 'Oct 16 · time not stated · ○○-dong area (sample)' } },
    caveats: [{ ko: '위치 현장 확인', en: 'Confirm location on site' }, { ko: '대기 있음', en: 'Possible queue' }],
    warning: {
      title: { ko: '단독 출처예요', en: 'Single source' },
      body: { ko: '공식 게시물이 한 곳뿐이고 종료 시간이 적혀 있지 않습니다. 정확한 위치는 현장 확인이 필요해요.', en: 'Only one official post exists and it has no end time. Confirm the exact location on site.' },
    },
  },
  {
    ...base, id: 'card_now_3', kind: 'now',
    title: { ko: '◇◇ 공연', en: '◇◇ Performance' }, kind_label: { ko: '공연', en: 'SHOW' },
    place: place('○○ 공연장', '○○ venue'),
    geometry: { type: 'point', coords: [[540, 190]], basis: { ko: '주소 (예시)', en: 'address (sample)' }, space: SCH },
    body: { ko: '신촌 일정 이후에 볼 수 있는 공연입니다 (예시).', en: 'A performance you could see after your Sinchon plans (sample).' },
    badge: '보류',
    sources: pickSources(['doc_07', 'doc_08']),
    slot: { day: 3, at: '18:00', between: [{ ko: '신촌 일정 이후', en: 'after Sinchon' }] },
    time_cost_min: 22, stay_min: null,
    valid: { from: '2026-10-17', to: '2026-10-17', as_of: '2026-10-05' },
    only: { ko: '오늘 하루만', en: 'Today only' },
    why_fits: [
      { ko: '관심사와 일치: 로컬 문화', en: 'Matches: local culture' },
      { ko: '여행 날짜에 열림 (10/17)', en: 'Open on your travel dates (10/17)' },
      { ko: '추가 이동이 큼 (+22분)', en: 'Large detour (+22 min)' },
    ],
    checks: [
      { level: 'ok', text: { ko: '공식 출처', en: 'Official source' } },
      { level: 'bad', text: { ko: '취소·변경 정보 충돌', en: 'Conflicting cancel/change info' } },
      { level: 'warn', text: { ko: '1일 전 갱신 · 재확인 필요', en: 'Updated 1 day ago · recheck' } },
    ],
    poster: { read: { ko: '10/17 · 18:00 · ○○ 공연장 (예시)', en: 'Oct 17 · 18:00 · ○○ venue (sample)' } },
    caveats: [{ ko: '우천 시 취소 여부', en: 'Cancelled if rain? unknown' }, { ko: '현금만 가능', en: 'Cash only' }],
    warning: {
      title: { ko: '자료끼리 달라요', en: 'Sources disagree' },
      body: { ko: '구청 공지에는 "운영", 주최 측 게시물에는 "우천 시 취소"로 올라와 있어 확정하지 않았습니다.', en: 'The district notice says "operating" while the organizer post says "cancelled if rain", so this is not confirmed.' },
    },
  },
];
