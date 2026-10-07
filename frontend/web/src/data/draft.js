import { DATA, LABELS } from "../lib/state.js";

// 초안 검토 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  draft: { id: "DRF-0141", type: "조치 계획서", title: "INV-C3 과전류 조치 순서", risk: "HIGH", version: "v3", caseId: "CASE-2026-1003-014",
    agent: "diag-01", updated: "2026-10-03 13:52", target: "INV-C3 · 컨베이어 #3 구동 인버터", reauth: true },
  sentences: [
    { id: "s1", must: true, cite: { doc: "m12", para: "p12a", hl: { en: "wait at least 10 minutes", ko: "최소 10분간 기다리십시오" } },
      tok: { src: "10 minutes", ko: "10분", en: "10 minutes", vi: "10 phút", ne: "10 मिनेट" },
      text: { ko: "작업 전 인버터 주전원을 차단하고 잠금·표지(LOTO)를 실시한 뒤 10분 이상 기다린다.",
        en: "Before work, disconnect inverter main power, apply lockout/tagout (LOTO), and wait at least 10 minutes.",
        vi: "Trước khi làm việc, ngắt nguồn chính của biến tần, thực hiện khóa và treo thẻ (LOTO), sau đó chờ ít nhất 10 phút.",
        ne: "काम गर्नु अघि इन्भर्टरको मुख्य बिजुली काट्नुहोस्, लकआउट/ट्यागआउट (LOTO) गर्नुहोस् र कम्तीमा 10 मिनेट पर्खनुहोस्।" } },
    { id: "s2", must: true, cite: { doc: "m12", para: "p12b", hl: { en: "below 50 V DC", ko: "50 V DC 미만" } },
      tok: { src: "below 50 V DC", ko: "50 V DC 미만", en: "below 50 V DC", vi: "dưới 50 V DC", ne: "50 V DC भन्दा कम" },
      text: { ko: "단자를 만지기 전에 DC 버스 전압이 50 V DC 미만인지 테스터로 확인한다.",
        en: "Before touching the terminals, use a tester to confirm the DC bus voltage is below 50 V DC.",
        vi: "Trước khi chạm vào các cực, dùng đồng hồ đo để xác nhận điện áp DC bus dưới 50 V DC.",
        ne: "टर्मिनल छुनु अघि DC बस भोल्टेज 50 V DC भन्दा कम छ भनी टेस्टरले जाँच गर्नुहोस्।" } },
    { id: "s3", cite: { doc: "m188", para: "p188a", hl: { en: "Disconnect the motor cable from output terminals U, V, W", ko: "출력 단자 U, V, W에서 모터 케이블을 분리하십시오" } },
      text: { ko: "모터 케이블을 인버터 출력 단자(U·V·W)에서 분리한다.",
        en: "Disconnect the motor cable from the inverter output terminals (U, V, W).",
        vi: "Tháo cáp động cơ khỏi các cực đầu ra của biến tần (U, V, W).",
        ne: "मोटर केबललाई इन्भर्टरको आउटपुट टर्मिनल (U, V, W) बाट छुट्याउनुहोस्।" } },
    { id: "s4", must: true, cite: { doc: "m188", para: "p188b", hl: { en: "500 V DC megger", ko: "500 V DC 메거" } },
      tok: { src: "500 V DC", ko: "500 V DC", en: "500 V DC", vi: "500 V DC", ne: "500 V DC" },
      text: { ko: "500 V DC 메거로 각 상과 대지 사이의 절연 저항을 측정한다.",
        en: "Measure insulation resistance between each phase and ground with a 500 V DC megger.",
        vi: "Đo điện trở cách điện giữa từng pha và đất bằng megger 500 V DC.",
        ne: "500 V DC मेगरले प्रत्येक फेज र अर्थबीचको इन्सुलेसन प्रतिरोध नाप्नुहोस्।" } },
    { id: "s5", must: true, cite: { doc: "m188", para: "p188c", hl: { en: "Minimum acceptable value: 5 MΩ", ko: "허용 최소값: 5 MΩ" } },
      tok: { src: "5 MΩ", ko: "5 MΩ 미만", en: "below 5 MΩ", vi: "dưới 5 MΩ", ne: "5 MΩ भन्दा कम" },
      text: { ko: "측정값이 5 MΩ 미만이면 모터 케이블을 교체한다.",
        en: "If the reading is below 5 MΩ, replace the motor cable.",
        vi: "Nếu giá trị đo dưới 5 MΩ, thay cáp động cơ.",
        ne: "नापिएको मान 5 MΩ भन्दा कम भए मोटर केबल बदल्नुहोस्।" } },
    { id: "s6", cite: { doc: "cmms", para: "c1", hl: { en: "10.0 s", ko: "10.0 s" } },
      text: { ko: "가속 시간 P1-08은 현재 설정값 10.0 s를 유지한다.",
        en: "Keep acceleration time P1-08 at its current setting of 10.0 s.",
        vi: "Giữ thời gian tăng tốc P1-08 ở giá trị hiện tại 10.0 s.",
        ne: "एक्सेलेरेसन समय P1-08 हालको सेटिङ 10.0 s मै राख्नुहोस्।" } },
    { id: "s7", cite: null,
      text: { ko: "재가동 후 30분간 출력 전류 피크를 관찰한다.",
        en: "After restart, monitor the output current peak for 30 minutes.",
        vi: "Sau khi khởi động lại, theo dõi dòng điện đầu ra đỉnh trong 30 phút.",
        ne: "पुनः सुरु गरेपछि 30 मिनेटसम्म आउटपुट करेन्टको पिक निगरानी गर्नुहोस्।" } },
    { id: "s8", must: true, warn: true, cite: { doc: "m12", para: "p12a", hl: { en: "DC bus capacitors retain charge after power-off", ko: "DC 버스 커패시터는 전원 차단 후에도 전하를 유지합니다" } },
      tok: { src: "WARNING — Hazardous voltage", whole: true },
      text: { ko: "경고: 전원을 차단한 후에도 커패시터에 위험한 전압이 남아 있습니다.",
        en: "WARNING: Hazardous voltage remains in the capacitors after power is disconnected.",
        vi: "CẢNH BÁO: Điện áp nguy hiểm vẫn còn trong tụ điện sau khi ngắt nguồn.",
        ne: "चेतावनी: बिजुली काटेपछि पनि क्यापासिटरमा खतरनाक भोल्टेज रहन्छ।" } }
  ],
  sources: [
    { id: "m12", name: "VFD-22 User Manual Rev.C", loc: "p.12 · 1.2 Safety", approvedBy: "설비기술 T-0207", approvedAt: "2026-09-20 10:05",
      paras: [
        { id: "p12a", warn: true, en: "WARNING — Hazardous voltage. Disconnect all input power and wait at least 10 minutes before servicing. DC bus capacitors retain charge after power-off.",
          ko: "경고 — 위험 전압. 정비 전 모든 입력 전원을 차단하고 최소 10분간 기다리십시오. DC 버스 커패시터는 전원 차단 후에도 전하를 유지합니다." },
        { id: "p12b", en: "Verify the DC bus voltage is below 50 V DC with a tester before touching any terminal.",
          ko: "단자를 만지기 전에 테스터로 DC 버스 전압이 50 V DC 미만인지 확인하십시오." } ] },
    { id: "m188", name: "VFD-22 User Manual Rev.C", loc: "p.188 · 9.7 Insulation test", approvedBy: "설비기술 T-0207", approvedAt: "2026-09-20 10:05",
      paras: [
        { id: "p188a", en: "Disconnect the motor cable from output terminals U, V, W before testing. Never apply a megger to the drive terminals.",
          ko: "시험 전 출력 단자 U, V, W에서 모터 케이블을 분리하십시오. 드라이브 단자에 메거를 절대 연결하지 마십시오." },
        { id: "p188b", en: "Measure phase-to-ground insulation resistance with a 500 V DC megger.",
          ko: "500 V DC 메거로 상-대지 간 절연 저항을 측정하십시오." },
        { id: "p188c", en: "Minimum acceptable value: 5 MΩ. If lower, replace the motor cable or repair the motor.",
          ko: "허용 최소값: 5 MΩ. 이보다 낮으면 모터 케이블을 교체하거나 모터를 수리하십시오." } ] },
    { id: "cmms", name: "정비 이력 · 파라미터 기록", loc: "INV-C3 · P1-08", approvedBy: "정비 1반 M-0215", approvedAt: "2021-04-14 15:30", noEn: true,
      paras: [ { id: "c1", en: "P1-08 Acceleration time = 10.0 s · 2021-04 설치 이후 변경 기록 없음", ko: "P1-08 가속 시간 = 10.0 s · 2021-04 설치 이후 변경 기록 없음" } ] }
  ],
  revisions: [
    { v: "v3", at: "13:52", who: "agent", by: "diag-01", text: "수정 요청 반영 · 대기 시간과 경고 문구를 매뉴얼 p.12 원문에 맞춤",
      diff: [ ["d", "…LOTO를 실시한 뒤 5분 이상 기다린다."], ["a", "…LOTO를 실시한 뒤 10분 이상 기다린다."], ["d", "주의: 커패시터에 전압이 남을 수 있습니다."], ["a", "경고: 전원을 차단한 후에도 커패시터에 위험한 전압이 남아 있습니다."] ] },
    { v: "v2", at: "13:50", who: "human", by: "정비반장 M-0412", text: "수정 요청: 1단계 대기 시간이 매뉴얼과 다릅니다. 경고 문구도 원문 강도로 바꿔 주세요." },
    { v: "v1", at: "13:48", who: "agent", by: "diag-01", text: "초안 생성 · 8문장 · 근거 연결 7" }
  ],
  approval: { by: "정비반장 M-0412", at: "2026-10-03 14:22" },
  chat: {
    ctx: "초안 DRF-0141 v3",
    suggestions: ["대기 시간이 왜 10분이야?", "50 V 기준 원문 보여줘", "30분 관찰 문장 근거는?", "이 초안 승인해줘"],
    replies: [
      { match: ["10분", "대기"], tools: [["kb.search_manual", "0.9s"]], text: "매뉴얼 p.12 안전 절에 정비 전 모든 입력 전원을 차단하고 최소 10분 기다리라고 되어 있습니다. v1의 5분은 원문과 달라 v3에서 10분으로 고쳤습니다.", cites: ["VFD-22 p.12 ¶1", "수정 이력 v3"] },
      { match: ["50", "전압"], tools: [["kb.search_manual", "0.7s"]], text: "원문: Verify the DC bus voltage is below 50 V DC with a tester before touching any terminal. 'below'이므로 초안은 '50 V DC 미만'으로 옮겼습니다.", cites: ["VFD-22 p.12 ¶2"] },
      { match: ["30분", "관찰"], kind: "refuse", tools: [["kb.search_manual", "0.8s"], ["cmms.history", "0.5s"]], text: "재가동 후 30분 관찰 기준은 승격된 매뉴얼과 정비 이력에서 찾지 못했습니다. 이 문장은 근거 없음으로 표시되어 있고, 삭제하거나 사람 판단으로 유지해야 합니다." }
    ]
  },
  blocked: { tool: "drafts.set_status", args: 'id="DRF-0141", status="approved"', rule: "승인 상태 변경은 사람 전용 · 에이전트 호출 불가" },
  error: { code: "503", message: "근거 원문 저장소(kb.internal) 응답 없음" }
});

Object.assign(LABELS, {
  app: "에이전트 콘솔",
  case: "케이스", target: "대상", draft: "초안", source: "근거 원문", agent: "에이전트", version: "버전", revisions: "수정 이력",
  mustCheck: "원문 대조 필수", checkDone: "대조 완료", checkTodo: "대조 확인",
  langDraft: "초안 언어", langSrc: "원문 표시",
  langs: { ko: "한국어", en: "English", vi: "Tiếng Việt", ne: "नेपाली" },
  srcLangs: { en: "원문 EN", ko: "한국어 참고 번역" },
  nav: { home: "홈", inbox: "신호 인박스", case: "케이스", draft: "초안 검토", approvals: "승인 큐", knowledge: "지식 온보딩", map: "대상 맵", schedule: "일정·배치", security: "샌드박스·정책", audit: "감사 기록", field: "현장 모바일", more: "더보기" },
  navShort: { home: "홈", inbox: "인박스", case: "케이스", draft: "초안", approvals: "승인", knowledge: "지식", map: "맵", schedule: "일정", security: "정책", audit: "감사", field: "현장", more: "더보기" },
  navGroups: { work: "작업", know: "지식·대상", ctrl: "통제", field: "현장" },
  prov: { untrusted: "검증 전 입력", draft: "에이전트 초안", approved: "사람 승인", blocked: "정책 차단", noev: "근거 없음", sensor: "센서 이상 의심" },
  provDesc: {
    untrusted: "업로드 문서, 센서값, 외부 텍스트. 단독으로 판단 근거가 되지 않습니다.",
    draft: "에이전트가 만든 결과. 사람이 승인하기 전까지 효력이 없습니다.",
    approved: "승인자 이름과 시각이 기록된 확정본입니다.",
    blocked: "샌드박스 정책이 실행을 막았습니다.",
    noev: "근거를 찾지 못해 에이전트가 답을 거부했습니다.",
    sensor: "값이 고정되거나 범위를 벗어나 판단에서 제외했습니다."
  },
  demo: { normal: "정상", running: "에이전트 실행 중", blocked: "차단 발생", approved: "승인 완료", empty: "빈 상태", loading: "로딩", error: "오류", rejected: "반려됨", offline: "네트워크 불안정" },
  actions: { approve: "조치 계획서 승인", approveShort: "승인", reject: "반려", revise: "수정 요청", reviseShort: "수정", stop: "실행 중단", reload: "원문 다시 불러오기" },
  humanOnly: "사람 전용"
});
