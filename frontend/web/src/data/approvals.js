import { DATA, LABELS } from "../lib/state.js";

// 승인 큐 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  items: [
    { id: "DRF-0141", type: "조치 계획서", title: "INV-C3 과전류 조치 순서 6단계", risk: "HIGH", reauth: true, time: "13:58", caseId: "CASE-2026-1003-014", by: "diag-01",
      sum: ["라인 2 전원 차단 후 잠금·표지 부착 (LOTO)", "모터 케이블 절연 저항 측정, 기준 미달 시 교체", "가속 시간 파라미터 P1.08 점검 · 변경값은 사람이 확정"],
      cites: [{ src: "manual", doc: "VFD-22 Rev.C", loc: "§7.3 p.88", quote: "F0003: Overcurrent during acceleration. Check motor cable insulation and acceleration time." }, { src: "history", doc: "정비 이력 2026-09-12", loc: "WO-8841", quote: "INV-C3 F0003 발생, 케이블 단자 재체결 후 복귀" }] },
    { id: "DRF-0142", type: "부품 발주서", title: "모터 케이블 4C×6㎟ 15 m · 1식 · ₩412,000", risk: "HIGH", reauth: true, time: "13:59", caseId: "CASE-2026-1003-014", by: "parts-01",
      sum: ["수량 15 m는 현재 케이블 길이에 여유 2 m 포함", "재고 시스템 조회: 현 재고 0 m", "발주는 사람 전용 도구 · 승인 시에만 제출"],
      cites: [{ src: "manual", doc: "VFD-22 Rev.C", loc: "§3.2 p.21", quote: "Use shielded 4-core cable, cross-section 6 mm² for 15 kW motors." }] },
    { id: "DRF-0143", type: "인수인계 메모", title: "C조 인계: 라인 2 컨베이어 #3 정지 중", risk: "LOW", reauth: false, time: "14:01", caseId: "CASE-2026-1003-014", by: "diag-01",
      sum: ["정지 시각과 현재 잠금 상태", "미완료 항목: 절연 저항 측정, 발주 승인"],
      cites: [{ src: "history", doc: "케이스 타임라인", loc: "13:47~14:00", quote: "F0003 수신, 정지, 진단 배정" }] },
    { id: "DRF-0139", type: "점검 체크리스트", title: "PMP-07 압력 하한 근접 점검 4항목", risk: "LOW", reauth: false, time: "11:20", caseId: "CASE-2026-1003-009", by: "diag-01",
      sum: ["토출 압력 게이지 현장 확인", "필터 차압 확인"],
      cites: [{ src: "manual", doc: "PMP-07 매뉴얼", loc: "§5.1 p.34", quote: "Inspect the strainer if outlet pressure drops below the low limit." }] }
  ],
  chat: {
    ctx: "승인 큐 · 4건",
    suggestions: ["가장 위험한 승인은?", "발주서 근거가 뭐야?", "왜 재로그인이 필요해?", "발주서 승인해줘"],
    replies: [
      { match: ["위험", "급한", "먼저"], tools: [["approvals.list", "0.3s"]], text: "DRF-0141 조치 계획서와 DRF-0142 발주서가 HIGH입니다. 둘 다 재로그인이 필요합니다.", cites: ["DRF-0141", "DRF-0142"] },
      { match: ["근거", "발주"], tools: [["kb.search_manual", "0.9s"]], text: "VFD-22 Rev.C §3.2에 6 mm² 4심 차폐 케이블 규격이 있습니다. 수량 15 m는 현재 길이에 여유 2 m를 더한 값입니다.", cites: ["VFD-22 Rev.C §3.2 p.21"] },
      { match: ["재로그인", "PIN"], tools: [], text: "HIGH 위험 승인은 비용이나 설비 정지에 직결되어 사번과 PIN을 다시 확인합니다.", cites: [] }
    ]
  },
  error: { code: "503", message: "승인 큐 서버에 연결할 수 없습니다" }
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
