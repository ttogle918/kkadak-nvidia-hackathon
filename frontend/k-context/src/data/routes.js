// 경로 샘플(A·B·C). 계약 형식(AGENT_CONTEXT 3.3 경로 JSON). 목업의 구간 s1~s4 가 경로 A 다.
// 숫자(분·미터)는 예시다. B·C 는 A 의 구간을 일부만 쓴 자리표시 경로.
// 확장 필드: segments[].coords(구간 선, 지도 좌표계 [x,y] — 카드가 없는 연결 구간(card_id=null)도 그릴 수 있게),
//            segments[].label_xy(이름표 위치). 카드가 있는 구간의 선은 카드 geometry 와 같다.
//
// selectedSeg(store)는 구간의 card_id 이다. card_id 가 null 인 구간(연결 도로)은 선택할 수 없다.

const seg = (name, card_id, length_m, walk_min, weak, coords, label_xy) => ({ name, card_id, length_m, walk_min, weak, coords, label_xy });

const S1 = seg({ ko: '왕이 지나던 길 (예시)', en: "King's Passage (sample)" }, 'card_old_1', 240, 4, false, [[90, 70], [210, 100], [300, 100]], [100, 50]);
const S2 = seg({ ko: '백성이 피해 다닌 뒷골목 (예시)', en: 'Back Alley (sample)' }, 'card_old_2', 130, 2, true, [[300, 100], [300, 170], [300, 230]], [312, 172]);
const S3 = seg({ ko: '연결 도로', en: 'Connecting road' }, null, 100, 2, false, [[300, 230], [400, 230]], null);
const S4 = seg({ ko: '지금은 덮인 물길 위 (예시)', en: 'Over the Covered Stream (sample)' }, 'card_old_4', 70, 1, false, [[400, 230], [470, 230]], [372, 242]);

export const ROUTES = [
  {
    id: 'A', theme: { ko: '왕의 길 (예시)', en: "King's Road (sample)" },
    walk_min: 18, delta_min: 4, story_count: 3, badge_mix: { 기록: 1, 추정: 1, 전승: 1 },
    badges: ['추천'],
    recommend_reason: { ko: '저녁 약속까지 40분 남아서 A를 권해요 (예시)', en: 'You have 40 minutes before dinner, so A fits best (sample)' },
    segments: [S1, S2, S3, S4],
  },
  {
    id: 'B', theme: { ko: '큰길 (예시)', en: 'Main road (sample)' },
    walk_min: 14, delta_min: 0, story_count: 2, badge_mix: { 기록: 1, 전승: 1 },
    badges: ['가장 빠름'],
    recommend_reason: { ko: '가장 빠른 길이에요 (예시)', en: 'The fastest route (sample)' },
    segments: [S1, S3, S4].map((s) => ({ ...s })),
  },
  {
    id: 'C', theme: { ko: '골목길 (예시)', en: 'Back lanes (sample)' },
    walk_min: 22, delta_min: 8, story_count: 2, badge_mix: { 추정: 1, 전승: 1 },
    badges: ['이야기 가장 많음'],
    recommend_reason: { ko: '이야기가 가장 많은 길이에요 (예시)', en: 'The route with the most stories (sample)' },
    segments: [S2, S3, S4].map((s) => ({ ...s })),
  },
];
