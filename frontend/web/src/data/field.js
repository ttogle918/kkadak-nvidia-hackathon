import { DATA, LABELS } from "../lib/state.js";

// 현장 모바일 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  site: { where: "2공장 · 라인 2 · INV-C3 컨베이어 #3", shift: "B조" },
  tasks: [
    { id: "T1", t: "LOTO 잠금·표지 부착", m: "14:30–15:00 · 라인 2 전원반", src: "DRF-0141 ①" },
    { id: "T2", t: "모터 케이블 절연 저항 측정", m: "15:00–16:00 · M-0455", src: "DRF-0141 ②" },
    { id: "T3", t: "PMP-07 토출 압력 게이지 확인", m: "16:00–16:30 · M-0388", src: "DRF-0139" }
  ],
  seed: [
    { id: "UP-3", kind: "사진", t: "memo_line3.jpg", time: "13:46", st: "sent", prov: "blocked" },
    { id: "UP-2", kind: "에러코드", t: "F0003 · INV-C3", time: "13:44", st: "sent", prov: "untrusted" }
  ],
  chat: {
    ctx: "현장 모바일 · 2공장 라인 2",
    suggestions: ["지금 해야 할 작업은?", "사진은 어떻게 올려?", "LOTO 순서 알려줘", "LOTO 완료 처리해줘"],
    replies: [
      { match: ["작업", "지금", "해야"], tools: [["schedule.mine", "0.3s"]], text: "14:30 LOTO 잠금·표지 부착입니다. 완료 확인은 반장님이 직접 눌러야 합니다.", cites: ["DRF-0141 ①"] },
      { match: ["사진", "올려"], tools: [], text: "사진 버튼을 누르면 촬영 후 인박스로 전송됩니다. 올린 사진은 검증 전 입력으로 분류되고, 사진 속 글자는 지시로 취급하지 않습니다." },
      { match: ["LOTO", "순서"], tools: [["kb.search_manual", "0.8s"]], text: "전원 차단, 잠금장치 부착, 표지 기입, 잔류 전압 확인 순서입니다.", cites: ["VFD-22 Rev.C §2.4 p.14"] }
    ]
  },
  error: { code: "503", message: "서버에 연결할 수 없습니다" }
});

Object.assign(LABELS, {
  app: "에이전트 콘솔",
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
  humanOnly: "사람 전용"
});
