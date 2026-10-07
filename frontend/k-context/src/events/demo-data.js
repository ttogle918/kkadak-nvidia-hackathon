// 데모 데이터. 전부 합성이며 실제 행사가 아니다(모든 항목 demo:true, 제목에 "(데모)").
// 서버 응답(backend /api/events/search 의 events[])과 같은 모양이라 화면이 그대로 그린다.
const DEMO_LINK = { url: 'https://example.invalid/demo', source_name: '데모 출처(합성)', kind: 'demo', quote: '합성 예시 — 실제 행사가 아니다', published_at: null, ai_extracted: false, location: null };
const base = {
  title_en: '', description: '', organizer: '', operator: '',
  venue: { name: '○○ 홀 (데모)', address: '', lat: 37.5665, lng: 126.9780, district: '', in_target: 'yes' },
  price: { kind: 'unknown', text: '' },
  reservation: { required: 'unknown', link: '', deadline: null, status: 'unknown', note: '' },
  eligibility: { audience: '', age_limit: '', resident_only: 'unknown', foreigner: 'unknown', restrictions: [] },
  participation: { status: 'unverified', reasons: ['참여조건이 확인되지 않음 — 원문 확인 필요'], foreigner: 'unknown', needs_check: true },
  language: { languages: [], english_guidance: 'unknown', english_subtitles: 'unknown', site_english_page: 'unknown' },
  lifecycle: 'scheduled', verification: 'needs_check', needs_check: ['sessions', 'price', 'reservation', 'eligibility', 'language'],
  conflicts: [], independent_sources: 1, links: [DEMO_LINK],
  published_at: null, modified_at: null, collected_at: '2026-10-07', last_verified_at: '2026-10-07T12:00', demo: true,
  interest_match: [],
};
const sched = (o) => ({ start_date: '2026-10-16', end_date: '2026-10-16', sessions: [], weekly_closed_days: [], closed_dates: [], holiday_rule: '', entry_cutoff: '', hours_text: '', timezone: 'Asia/Seoul', ...o });

export const DEMO_EVENTS = [
  {
    ...base, id: 'demo:1', title: '(데모) 저녁 공연', event_type: '공연',
    schedule: sched({ sessions: [{ date: '2026-10-16', start_time: '19:00', end_time: '20:30', venue_name: '○○ 홀 (데모)', in_target: 'yes', note: '' }] }),
    price: { kind: 'paid', text: '합성 요금 안내' },
    reservation: { required: 'yes', link: 'https://example.invalid/demo-reserve', deadline: '2026-10-15', status: 'open', note: '' },
    eligibility: { audience: '누구나', age_limit: '', resident_only: 'unknown', foreigner: 'unknown', restrictions: [] },
    participation: { status: 'stated_open', reasons: ['출처가 누구나 참여할 수 있다고 적음'], foreigner: 'unknown', needs_check: true },
    verification: 'verified', needs_check: ['foreigner', 'language'],
  },
  {
    ...base, id: 'demo:2', title: '(데모) 주민 대상 강좌', event_type: '교육',
    venue: { ...base.venue, name: '△△ 문화센터 (데모)', lat: 37.5701, lng: 126.9840 },
    schedule: sched({ start_date: '2026-10-14', end_date: '2026-10-20', sessions: [{ date: '2026-10-17', start_time: '10:00', end_time: '12:00', venue_name: '△△ 문화센터 (데모)', in_target: 'yes', note: '' }] }),
    eligibility: { audience: '중구민', age_limit: '', resident_only: 'yes', foreigner: 'unknown', restrictions: [{ kind: 'resident', text: '중구민', reason: '거주 조건: 중구민' }] },
    participation: { status: 'restricted', reasons: ['거주 조건: 중구민'], foreigner: 'unknown', needs_check: false },
    needs_check: ['price', 'reservation', 'language'],
  },
  {
    ...base, id: 'demo:3', title: '(데모) 상설 전시', event_type: '전시',
    venue: { ...base.venue, name: '□□ 전시관 (데모)', lat: null, lng: null },
    schedule: sched({ start_date: '2026-10-01', end_date: '2026-10-31', weekly_closed_days: [0], hours_text: '10:00–18:00 (합성)' }),
    language: { languages: [], english_guidance: 'unknown', english_subtitles: 'unknown', site_english_page: 'yes' },
    needs_check: ['sessions', 'price', 'reservation', 'eligibility', 'language'],
  },
];

export const DEMO_COVERAGE = {
  complete: false, note: '데모 데이터입니다 — 실제 수집 결과가 아니다', entries_built_at: null,
  sources: [{ id: 'demo', name: '데모 출처(합성)', method: 'demo', status: 'demo', url: '', last_success_at: null, last_error: null }],
};

export const DEMO_PLANS = [
  { id: 'demo_plan_1', title: '(데모) 점심', date: '2026-10-16', start: '12:00', end: '13:30', lat: 37.5640, lng: 126.9770, source: 'demo' },
  { id: 'demo_plan_2', title: '(데모) 호텔 체크인', date: '2026-10-16', start: '22:00', end: '23:00', lat: 37.5600, lng: 126.9800, source: 'demo' },
];
