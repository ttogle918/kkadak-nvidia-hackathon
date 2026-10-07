import { DATA, LABELS } from "../lib/state.js";

// 홈 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  home: { site: "2공장", date: "2026-10-03 (토)", shift: "B조 · 14:00–22:00", updated: "14:05:12" },
  approvals: { count: 4, reauth: 3, oldest: "38분", items: [
    { id: "DRF-0139", type: "정책 YAML 변경", title: "sbx-maint-diag 최소 권한 적용", risk: "HIGH", reauth: true, wait: "38분", old: true, agent: "policy-01", href: "security.html" },
    { id: "DRF-0138", type: "안전 수칙 번역", title: "LOTO 절차 · 베트남어", risk: "MEDIUM", reauth: false, wait: "25분", agent: "lang-01", href: "draft.html?id=DRF-0138" },
    { id: "DRF-0141", type: "조치 계획서", title: "INV-C3 과전류 조치 순서", risk: "HIGH", reauth: true, wait: "12분", agent: "diag-01", href: "draft.html?id=DRF-0141" },
    { id: "DRF-0142", type: "부품 발주서", title: "모터 케이블 4C×6㎟ 15 m · 1식", risk: "HIGH", reauth: true, wait: "12분", agent: "diag-01", href: "approvals.html?id=DRF-0142" } ] },
  cases: { count: 3, items: [
    { id: "CASE-2026-1003-014", title: "컨베이어 #3 인버터 F0003 과전류", sev: "HIGH", status: "wait", note: "초안 3건 · 사람 결정 대기" },
    { id: "CASE-2026-1003-012", title: "도장 부스 배기팬 진동 상승", sev: "MEDIUM", status: "running", note: "4/9단계 · 센서 이력 조회 중" },
    { id: "CASE-2026-1003-009", title: "AGV-07 충전 실패 반복", sev: "MEDIUM", status: "wait", note: "원인 가설 2 · 확인 필요" } ] },
  signals: { count: 7, window: "지난 1시간", kinds: [ ["code", "에러코드", 3], ["sensor", "센서", 2], ["doc", "문서", 1], ["photo", "사진", 1], ["log", "로그", 0], ["voice", "음성", 0] ],
    latest: [
      { t: "14:02", kind: "센서", title: "압축기 C-2 토출 온도 98 °C", src: "telemetry · LINE-1" },
      { t: "13:58", kind: "문서", title: "신규 기종 RX-40 매뉴얼.pdf 업로드", src: "업로드 · 설비기술" } ] },
  knowledge: { ready: 17, review: 3, none: 5, total: 25, docsPending: 2, pendingDoc: "RX-40 Service Manual (EN) · 추출 312항목 중 검수 41%" },
  blocked: { count: 2, window: "24시간", items: [
    { t: "13:48:20", tool: "erp.submit_order", why: "사람 전용 도구 · 업로드 사진 OCR 지시문", injection: true, caseId: "CASE-2026-1003-014" },
    { t: "13:47:26", tool: "web.fetch", why: "외부 도메인 egress 거부", injection: false, caseId: "CASE-2026-1003-014" } ] },
  blockedExtra: { t: "14:04:51", tool: "fs.read", why: "/etc/gateway/secrets 경로 접근 거부", injection: true, caseId: "CASE-2026-1003-012" },
  recentDecision: { id: "DRF-0141", type: "조치 계획서", by: "정비반장 M-0412", at: "14:22" },
  chat: {
    ctx: "홈 · 2공장 · 2026-10-03",
    suggestions: ["가장 오래 기다린 승인은?", "오늘 차단된 시도 요약", "미온보딩 대상은?", "발주서 전부 승인해줘"],
    replies: [
      { match: ["오래", "대기"], tools: [["approvals.list", "0.4s"]], text: "DRF-0139 정책 YAML 변경 제안이 38분째 대기 중입니다. 위험 등급 HIGH이고 재로그인이 필요합니다. 요청 에이전트는 policy-01입니다.", cites: ["승인 큐 · DRF-0139"], link: ["security.html", "정책 변경 보기"] },
      { match: ["차단", "막힌", "공격"], tools: [["audit.query", "0.6s"]], text: "24시간 동안 2건입니다. 13:48 erp.submit_order는 사람 전용 도구라 막혔고, 업로드 사진의 OCR 지시문에서 시작돼 주입 의심으로 표시됐습니다. 13:47 web.fetch는 외부 도메인이라 막혔습니다.", cites: ["감사 기록 13:48:20", "감사 기록 13:47:26"], link: ["audit.html?filter=blocked", "감사 기록 열기"] },
      { match: ["미온보딩", "온보딩", "커버리지"], tools: [["targets.list", "0.5s"]], text: "25개 대상 중 5개가 미온보딩입니다. 이 대상들은 승격된 매뉴얼이 없어 에이전트가 진단 판단을 하지 않습니다. RX-40 매뉴얼이 검수 41% 단계입니다.", cites: ["대상 맵 · 2공장", "지식 온보딩 · RX-40"], link: ["knowledge.html", "지식 온보딩 열기"] }
    ]
  }
});

Object.assign(LABELS, {
  app: "에이전트 콘솔",
  home: "오늘 현황", case: "케이스", signal: "신호", target: "대상", draft: "초안",
  cards: { approvals: "승인 대기", cases: "진행 중 케이스", signals: "새 신호", knowledge: "지식 커버리지", blocked: "최근 차단된 시도" },
  kindIcon: { code: "cpu", sensor: "activity", doc: "draft", photo: "camera", log: "plan", voice: "mic" },
  cov: { ready: "판단 가능", review: "검수 중", none: "미온보딩" },
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
