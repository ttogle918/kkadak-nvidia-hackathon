// 일정 샘플: 사용자 상황(계약 3.3 입력) + 지도 랜드마크 + DAY 1 타임라인.
// 확장 필드: anchors[].xy / landmarks[] 는 목업 지도 좌표계(viewBox 0 0 600 700)의 [x,y]. lat/lng 는 샘플에서 null.
//           timeline[] 은 날짜별 화면용 행. item.only 가 있으면 그 조건일 때만 보인다(state/selectors.js timelineFor).
// 목업은 DAY 1 만 채워져 있다. DAY 2·3 은 timeline 에 항목이 없으며 모듈이 빈 상태를 보여 준다.

export const ITINERARY = {
  trip: { from: '2026-10-15', to: '2026-10-18' },
  anchors: [
    { type: 'hotel', name: { ko: '숙소 · 종로3가', en: 'Hotel · Jongno 3-ga' }, lat: null, lng: null, xy: [110, 330], from: '2026-10-15T15:00', to: '2026-10-18T11:00' },
    { type: 'visit', name: { ko: '창덕궁', en: 'Changdeokgung' }, day: 1, lat: null, lng: null, xy: [90, 70], from: '2026-10-15T10:00', to: '2026-10-15T12:30' },
    { type: 'visit', name: { ko: '익선동', en: 'Ikseon-dong' }, day: 1, lat: null, lng: null, xy: [470, 230], from: '2026-10-15T14:00', to: '2026-10-15T17:00' },
    { type: 'visit', name: { ko: '경복궁', en: 'Gyeongbokgung' }, day: 2, lat: null, lng: null, xy: null },
    { type: 'visit', name: { ko: '광화문', en: 'Gwanghwamun' }, day: 2, lat: null, lng: null, xy: null },
    { type: 'visit', name: { ko: '신촌', en: 'Sinchon' }, day: 3, lat: null, lng: null, xy: null },
  ],
  free_slots: [
    {
      day: 1, from: '2026-10-15T19:00', to: '2026-10-15T23:00', near: { ko: '익선동', en: 'Ikseon-dong' }, inferred: true,
      assumption: { ko: '1일차 저녁 7시 이후가 비어 있다고 봤어요.', en: 'I assumed you are free after 7 pm on day 1.' },
    },
  ],
  party: { size: 2, kids: false, mobility_limited: false, luggage: false },
  language: 'ko',
  interests: [{ ko: '한국 음식', en: 'Korean food' }, { ko: '로컬 문화', en: 'local culture' }],
  minimize_changes: true,
  // 지도에 그릴 고정 지점. kind: 'anchor'(검은 사각) · 'hotel'(H) · 'poi'(마름모) · 'dot'(검은 점) · 'muted'(회색 점 = 탈락 후보)
  landmarks: [
    { id: 'lm_changdeok', kind: 'anchor', xy: [90, 70], label: { ko: '창덕궁', en: 'Changdeokgung' } },
    { id: 'lm_ikseon', kind: 'anchor', xy: [470, 230], label: { ko: '익선동', en: 'Ikseon-dong' } },
    { id: 'lm_hotel', kind: 'hotel', xy: [110, 330], label: { ko: '숙소 · 종로3가', en: 'Hotel · Jongno 3-ga' } },
    { id: 'lm_well', kind: 'poi', xy: [250, 150], label: { ko: '우물 터 (예시)', en: 'Well site (sample)' } },
    { id: 'lm_dot', kind: 'dot', xy: [300, 150], label: null },
    { id: 'lm_m1', kind: 'muted', xy: [190, 165], label: null },
    { id: 'lm_m2', kind: 'muted', xy: [540, 190], label: null },
    { id: 'lm_m3', kind: 'muted', xy: [60, 190], label: null },
  ],
  // 숙소까지 돌아가는 경로(지도의 파란 점선)와 그 이름표
  walk_back: {
    coords: [[470, 230], [470, 330], [110, 330]],
    label: { ko: '숙소까지 도보 18분 · 막차 23:40', en: '18 min walk to hotel · last train 23:40' },
  },
  timeline: [
    {
      day: 1,
      items: [
        { id: 'tl_1', time: '08:30', kind: 'original', title: { ko: '숙소 출발', en: 'Leave hotel' }, sub: { ko: '종로3가', en: 'Jongno 3-ga' } },
        { id: 'tl_2', time: '10:00–12:30', kind: 'original', title: { ko: '창덕궁', en: 'Changdeokgung' }, sub: '' },
        { id: 'tl_3', time: '14:00–17:00', kind: 'original', title: { ko: '익선동', en: 'Ikseon-dong' }, sub: '' },
        { id: 'tl_4', time: '19:00 ~', kind: 'free', only: 'not_added', title: { ko: '빈 시간', en: 'Free time' }, sub: { ko: '· 약 4시간', en: '· ~4h' } },
        { id: 'tl_5', time: '19:30', kind: 'proposal', card_id: 'card_now_1', title: { ko: '○○ 야장', en: '○○ Night market' }, sub: { ko: '+12분 · 70분', en: '+12 min · 70 min' } },
        { id: 'tl_6', time: '21:00 ~', kind: 'free', only: 'added', title: { ko: '빈 시간', en: 'Free time' }, sub: { ko: '· 숙소 도보 18분', en: '· hotel 18 min' } },
        { id: 'tl_7', time: '22:30', kind: 'original', title: { ko: '숙소 도착', en: 'Back at hotel' }, sub: { ko: '종로3가', en: 'Jongno 3-ga' } },
      ],
    },
  ],
};
