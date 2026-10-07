// 판단 근거(EV) 샘플. getRationale(cardId) 가 돌려주는 형태:
//   { card_id, chips:[{key, tone:'old'|'now', label}], items:{ [key]: {title, text, rows:[{k,v}]} } }
// openEvidence(store) 는 chips[].key 중 하나이거나 null. 문구는 목업의 EV 를 ko/en 으로 옮겼고 숫자·날짜는 예시다.

const L = (ko, en) => ({ ko, en });
const row = (k, v) => ({ k, v });

const GRADE_TEXT = {
  기록: L('원문에 직접 근거가 있는 구간입니다. 사실 층의 문장마다 출처 태그가 붙습니다.', 'This segment has direct grounds in the text. Each sentence of the fact layer carries a source tag.'),
  전승: L('구전이나 후대 문헌으로 전해지는 내용이라 확정하지 않고 "전해진다"로 적었습니다.', 'This comes from oral tradition or later writings, so it is phrased as "is said to" rather than stated as fact.'),
  추정: L('옛길과 대체로 겹친다는 수준이라 점선으로 그렸습니다. 직접 기록은 없습니다.', 'It only roughly overlaps the old road, so it is drawn dotted. There is no direct record.'),
};
const GRADE_NAME = { 기록: L('기록', 'Record'), 전승: L('전승', 'Lore'), 추정: L('추정', 'Presumed') };

const IMM = {
  title: L('몰입 층은 상상', 'The immersion layer is imagination'),
  text: L('몰입 층은 사실이 아니라 상상입니다. 사실 층과 구분해 "상상" 표시를 붙였고 끌 수 있습니다.', 'The immersion layer is imagination, not fact. It is marked "imagined", kept apart from the fact layer, and can be turned off.'),
  rows: [],
};

/** 옛날 카드용: 딱지 + (이설 있으면) 이설 병기 + 상상 표시. */
export function storyRationale(cardId, badge, sourceCount, hasAlt) {
  const chips = [{ key: 'grade', tone: 'old', label: L(`◆ 등급 ${badge}`, `◆ Grade: ${GRADE_NAME[badge].en}`) }];
  const items = {
    grade: {
      title: L(`등급: ${badge}`, `Grade: ${GRADE_NAME[badge].en}`),
      text: GRADE_TEXT[badge],
      rows: [row(L('등급', 'Grade'), GRADE_NAME[badge]), row(L('출처 수', 'Sources'), L(`${sourceCount}건`, String(sourceCount)))],
    },
    imm: IMM,
  };
  if (hasAlt) {
    chips.push({ key: 'alt', tone: 'old', label: L('◇ 이설 병기', '◇ Two accounts') });
    items.alt = {
      title: L('이설 병기', 'Both accounts shown'),
      text: L('자료마다 시기가 달라 두 설을 나란히 보여줍니다. 어느 쪽도 버리지 않았습니다.', 'Sources give different timings, so both accounts are shown side by side. Neither was discarded.'),
      rows: [row(L('설 A', 'Account A'), L('○○ 시기 (자료 ①)', '○○ (source ①)')), row(L('설 B', 'Account B'), L('△△ 시기 (자료 ②)', '△△ (source ②)'))],
    };
  }
  chips.push({ key: 'imm', tone: 'old', label: L('◇ 상상 표시', '◇ Imagined') });
  return { card_id: cardId, chips, items };
}

const NOW_1 = {
  card_id: 'card_now_1',
  chips: [
    { key: 'funnel', tone: 'now', label: L('● 후보 12건 중 채택 2', '● 2 of 12 candidates adopted') },
    { key: 'fit', tone: 'now', label: L('● 관심사 일치', '● Matches interests') },
    { key: 'date', tone: 'now', label: L('● 여행 기간에 열림', '● Open during your trip') },
    { key: 'detour', tone: 'now', label: L('● 동선 +12분', '● +12 min detour') },
    { key: 'src', tone: 'now', label: L('● 공식 출처 2건', '● 2 official sources') },
    { key: 'conflict', tone: 'now', label: L('● 충돌 해결', '● Conflict resolved') },
  ],
  items: {
    funnel: {
      title: L('후보 12건 중 채택 2', '2 of 12 candidates adopted'),
      text: L('후보 12건을 걸러 2건만 제안했습니다. 탈락 사유는 아래와 같습니다. (예시)', 'I filtered 12 candidates down to 2 proposals. Reasons for dropping the rest are below. (sample)'),
      rows: [
        row(L('채택', 'Adopted'), '2'), row(L('기간 종료', 'Already ended'), '5'), row(L('동선에서 너무 멂', 'Too far from route'), '2'),
        row(L('관심사 불일치', 'Interest mismatch'), '2'), row(L('중복', 'Duplicate'), '1'),
      ],
    },
    fit: {
      title: L('관심사 일치', 'Matches your interests'),
      text: L('입력한 관심사 "한국 음식", "로컬 문화"와 이 야장의 종류가 맞습니다.', 'The type of this night market matches your interests "Korean food" and "local culture".'),
      rows: [],
    },
    date: {
      title: L('여행 기간에 열림', 'Open during your trip'),
      text: L('종로구청 공지와 TourAPI 모두 여행 날짜 안에 열린다고 적혀 있습니다.', 'Both the Jongno-gu notice and TourAPI say it is open within your travel dates.'),
      rows: [row(L('여행 기간', 'Trip'), '10/15–18'), row(L('행사 기간', 'Event'), L('10/15–18 (예시)', '10/15–18 (sample)'))],
    },
    detour: {
      title: L('동선 +12분', '+12 min detour'),
      text: L('익선동에서 야장 골목까지 들렀다 가는 거리입니다. 원래 일정은 바뀌지 않습니다.', 'This is the extra distance to drop by the night-market alley from Ikseon-dong. Your original plan is unchanged.'),
      rows: [
        row(L('추가 이동', 'Extra travel'), L('+12분', '+12 min')), row(L('추천 체류', 'Suggested stay'), L('70분', '70 min')),
        row(L('숙소 복귀', 'Back to hotel'), L('도보 18분 · 막차 23:40', '18 min walk · last train 23:40')),
      ],
    },
    src: {
      title: L('공식 출처 2건', '2 official sources'),
      text: L('공식 출처 두 곳이 같은 내용을 말합니다.', 'Two official sources say the same thing.'),
      rows: [
        row(L('[B] 종로구청 공지', '[B] Jongno-gu notice'), L('2026-10-02 게시', 'posted 2026-10-02')),
        row(L('[B] 한국관광공사 TourAPI', '[B] KTO TourAPI'), L('2026-10-05 갱신', 'updated 2026-10-05')),
      ],
    },
    conflict: {
      title: L('충돌 해결', 'Conflict resolved'),
      text: L('포스터와 변경 공지의 시작 시간이 달랐습니다. 나중에 올라온 공식 공지를 택하고 포스터 시간은 참고로 남겼습니다.', 'The poster and the change notice gave different start times. I chose the later official notice and kept the poster time as reference.'),
      rows: [row(L('포스터 · 10/02', 'Poster · 10/02'), L('19:00 (참고)', '19:00 (reference)')), row(L('변경 공지 · 10/05', 'Change notice · 10/05'), L('19:30 ✓ 채택', '19:30 ✓ adopted'))],
    },
  },
};

const NOW_2 = {
  card_id: 'card_now_2',
  chips: [
    { key: 'src', tone: 'now', label: L('● 출처 1건 (단독)', '● 1 source (single)') },
    { key: 'date', tone: 'now', label: L('● 종료일 미기재', '● No end date') },
  ],
  items: {
    src: {
      title: L('출처 1건 (단독)', '1 source (single)'),
      text: L('공식 게시물이 한 곳뿐이라 "확인 필요"로 두었습니다. (예시)', 'Only one official post exists, so it is marked "to verify". (sample)'),
      rows: [row(L('[B] 종로구청 공지', '[B] Jongno-gu notice'), L('2026-10-04 게시', 'posted 2026-10-04')), row(L('[B] 포스터에서 읽음', '[B] Read from poster'), L('중구청 게시물 첨부', 'attached to Jung-gu post'))],
    },
    date: {
      title: L('종료일 미기재', 'No end date'),
      text: L('시작은 10/16 이지만 종료 시간이 적혀 있지 않아 날짜를 확정하지 않았습니다. (예시)', 'It starts on 10/16 but no end time is given, so the date is not confirmed. (sample)'),
      rows: [row(L('행사일', 'Event date'), '10/16'), row(L('종료', 'End'), L('미기재', 'not stated'))],
    },
  },
};

const NOW_3 = {
  card_id: 'card_now_3',
  chips: [{ key: 'conflict', tone: 'now', label: L('● 충돌 미해결 → 보류', '● Unresolved conflict → on hold') }],
  items: {
    conflict: {
      title: L('충돌 미해결 → 보류', 'Unresolved conflict → on hold'),
      text: L('구청 공지의 "운영"과 주최 측 게시물의 "우천 시 취소"가 달라 어느 쪽도 채택하지 않고 보류했습니다. 해결된 척하지 않습니다.', 'The district notice says "operating" and the organizer post says "cancelled if rain". I adopted neither and put it on hold instead of pretending it is resolved.'),
      rows: [row(L('[B] 종로구청 공지 · 10/03', '[B] Jongno-gu notice · 10/03'), L('운영', 'operating')), row(L('[C] 주최 측 게시물', '[C] Organizer post'), L('우천 시 취소', 'cancelled if rain'))],
    },
  },
};

export const NOW_RATIONALE = { card_now_1: NOW_1, card_now_2: NOW_2, card_now_3: NOW_3 };
