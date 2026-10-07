import { DATA, LABELS } from "../lib/state.js";

// 대상 맵 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  lines: [
    { id: "LINE-1", name: "2공장 · 라인 1", eq: ["INV-C1", "RBT-02", "CMP-01"] },
    { id: "LINE-2", name: "2공장 · 라인 2", eq: ["INV-C3", "MTR-C3", "PMP-07"] }
  ],
  eq: {
    "INV-C1": { name: "컨베이어 #1 인버터", model: "VFD-22", st: "ok", stl: "정상", pos: "라인 1 입구", prov: "approved", man: ["VFD-22 Rev.C", "promoted"], sig: [["SIG-1003-025", "F0007 DC 버스 저전압 · 자동 복귀"]], hist: [["2026-08-30", "팬 청소"]] },
    "RBT-02": { name: "이송 로봇", model: "RBT-02", st: "warn", stl: "근거 없음 · 주의", pos: "라인 1 중간", prov: "noev", man: ["RBT-02 매뉴얼", "review"], sig: [["SIG-1003-027", "E-112 그리퍼 압력 부족"]], hist: [["2026-07-14", "그리퍼 실 교체"]] },
    "CMP-01": { name: "공압 컴프레서", model: "CMP-01", st: "ok", stl: "정상", pos: "유틸리티실", prov: "untrusted", man: null, sig: [["SIG-1003-026", "소음 증가 (음성 메모)"]], hist: [["2026-09-01", "오일 교체"]] },
    "INV-C3": { name: "컨베이어 #3 인버터", model: "VFD-22", st: "fault", stl: "F0003 정지", pos: "라인 2 출구", prov: "untrusted", man: ["VFD-22 Rev.C", "promoted"], sig: [["SIG-1003-031", "F0003 가속 중 과전류"], ["SIG-1003-030", "현장 메모 사진 · 격리"]], hist: [["2026-09-12", "케이블 단자 재체결 (WO-8841)"]], caseId: "CASE-2026-1003-014" },
    "MTR-C3": { name: "컨베이어 #3 모터", model: "M-15K", st: "warn", stl: "센서 이상 의심", pos: "라인 2 출구", prov: "sensor", man: null, sig: [["SIG-1003-029", "진동 12시간 0.00 mm/s 고정"]], hist: [] },
    "PMP-07": { name: "냉각수 펌프", model: "PMP-07", st: "ok", stl: "정상", pos: "라인 2 유틸리티", prov: "untrusted", man: ["PMP-07 매뉴얼", "promoted"], sig: [["SIG-1003-028", "토출 압력 하한 근접"]], hist: [["2026-08-21", "스트레이너 청소"]] }
  },
  chat: {
    ctx: "대상 맵 · 설비 6대",
    suggestions: ["이상 있는 설비는?", "RBT-02 원인 알려줘", "MTR-C3 센서 믿어도 돼?", "INV-C3 정지 해제 승인해줘"],
    replies: [
      { match: ["이상", "문제"], tools: [["map.status", "0.3s"]], text: "INV-C3는 F0003으로 정지, RBT-02는 매뉴얼 미승격, MTR-C3는 센서 이상 의심입니다.", cites: ["SIG-1003-031", "SIG-1003-029"] },
      { match: ["RBT", "원인"], kind: "refuse", tools: [["kb.search_manual", "0.9s"]], text: "RBT-02 매뉴얼은 아직 승격되지 않아 근거로 쓸 수 없습니다.", link: ["knowledge.html", "지식 온보딩에서 승격"] },
      { match: ["MTR", "센서"], tools: [["telemetry.query", "0.6s"]], text: "진동값이 12시간 0.00으로 고정되어 센서 또는 배선 이상으로 보고 진단에서 제외했습니다.", cites: ["SIG-1003-029"] }
    ]
  },
  error: { code: "503", message: "설비 마스터에 연결할 수 없습니다" }
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
