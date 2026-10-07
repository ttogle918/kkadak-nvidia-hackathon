import { DATA, LABELS } from "../lib/state.js";

// 일정·배치 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  day: { from: 14, to: 22, label: "10/03 · B조" },
  people: [
    { id: "M-0412", role: "정비반장", shift: "14:00–22:00", fixed: [[14.0, 14.5, "라인 2 정지 확인"]], plan: [[14.5, 15.0, "LOTO 잠금·표지", "T1"], [16.5, 17.0, "조치 결과 확인", "T4"]] },
    { id: "M-0455", role: "전기 정비원", shift: "14:00–16:00", fixed: [], plan: [[15.0, 16.0, "절연 저항 측정", "T2"]] },
    { id: "M-0388", role: "기계 정비원", shift: "14:00–22:00", fixed: [[14.0, 15.5, "CMP-01 점검"]], plan: [[16.0, 16.5, "PMP-07 압력 점검", "T3"]] }
  ],
  tasks: [
    { id: "T1", name: "LOTO 잠금·표지 (INV-C3)", who: "M-0412", at: "14:30–15:00" },
    { id: "T2", name: "모터 케이블 절연 저항 측정", who: "M-0455", at: "15:00–16:00" },
    { id: "T3", name: "PMP-07 압력 점검", who: "M-0388", at: "16:00–16:30" },
    { id: "T4", name: "조치 결과 확인", who: "M-0412", at: "16:30–17:00" }
  ],
  why: ["INV-C3 정지가 길어질수록 라인 2 출하가 늦어져 LOTO와 측정을 먼저 배치", "M-0455는 16:00 교대 종료라 측정을 15:00–16:00에 끝내도록 배치", "PMP-07은 하한 여유 0.2 bar라 오늘 안에 점검"],
  cite: { doc: "VFD-22 Rev.C", loc: "§7.3 p.88", quote: "Check motor cable insulation before restarting the drive." },
  chat: {
    ctx: "일정·배치 · 10/03 B조",
    suggestions: ["가장 빡빡한 시간대는?", "측정을 왜 15시로 잡았어?", "M-0455 야근 가능해?", "배치 확정해줘"],
    replies: [
      { match: ["빡빡", "시간대"], tools: [["schedule.load", "0.4s"]], text: "15:00–16:00입니다. M-0455의 측정이 교대 종료 직전에 끝납니다. 지연되면 M-0388로 넘기는 대안을 제안할 수 있습니다.", cites: ["T2"] },
      { match: ["왜", "측정", "15"], tools: [["kb.search_manual", "0.8s"]], text: "재기동 전 절연 확인이 필요하다는 매뉴얼 문구와 M-0455의 교대 시간을 근거로 했습니다.", cites: ["VFD-22 Rev.C §7.3 p.88"] },
      { match: ["야근", "연장"], kind: "refuse", tools: [], text: "근무 연장 가능 여부는 근태 시스템 정보가 없어 답할 수 없습니다. 반장님이 직접 확인해 주세요." }
    ]
  },
  error: { code: "503", message: "근태·작업지시 서버에 연결할 수 없습니다" }
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
