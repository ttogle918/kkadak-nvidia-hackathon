import { DATA, LABELS } from "../lib/state.js";

// 샌드박스·정책 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  tools: [
    { id: "inbox.list", name: "신호 목록 조회", mode: "allow", scope: "읽기 전용", calls: 41, yaml: "tool: inbox.list\nmode: allow\nscope: read\nrate: 60/min", log: [["13:52", "허용", "신호 7건 조회"]] },
    { id: "kb.search_manual", name: "승격 문서 검색", mode: "allow", scope: "승격된 문서만", calls: 28, yaml: "tool: kb.search_manual\nmode: allow\nscope: read\nsource: promoted_only", log: [["13:47", "허용", "VFD-22 §7.3 검색"], ["13:40", "허용", "RBT-02 검색 · 결과 없음"]] },
    { id: "cmms.history", name: "정비 이력 조회", mode: "allow", scope: "읽기 전용", calls: 17, yaml: "tool: cmms.history\nmode: allow\nscope: read", log: [["13:47", "허용", "INV-C3 이력 조회"]] },
    { id: "report.draft", name: "초안 작성", mode: "allow", scope: "초안만 · 효력 없음", calls: 9, yaml: "tool: report.draft\nmode: allow\nscope: draft_only\neffect: none_until_approved", log: [["13:59", "허용", "DRF-0142 작성"]] },
    { id: "order.submit", name: "부품 발주 제출", mode: "human", scope: "사람 전용", calls: 0, yaml: "tool: order.submit\nmode: human_only\nreauth: required", log: [["13:46", "차단", "사진 속 지시문에 의한 호출 시도 · 거부"]] },
    { id: "approvals.decide", name: "승인·반려 결정", mode: "human", scope: "사람 전용", calls: 0, yaml: "tool: approvals.decide\nmode: human_only\nreauth: required", log: [["13:58", "차단", "채팅 승인 요청 · 거부"]] },
    { id: "plc.write", name: "PLC 쓰기", mode: "deny", scope: "전면 차단", calls: 0, yaml: "tool: plc.write\nmode: deny\nreason: safety", log: [] },
    { id: "net.fetch", name: "외부 네트워크 요청", mode: "deny", scope: "허용 목록 비어 있음", calls: 0, yaml: "tool: net.fetch\nmode: deny\nallowlist: []", log: [["13:32", "차단", "외부 주소 접근 시도 · 거부"]], prop: true }
  ],
  prop: { id: "POL-0007", title: "net.fetch 허용 목록에 공급사 포털 도메인 1건 추가", why: "승격 대기 매뉴얼을 에이전트가 직접 내려받지 않고 사람이 올리는 흐름은 유지하며, 부품 재고 조회만 허용하려는 제안입니다.", diff: ["tool: net.fetch", "mode: deny", "-allowlist: []", "+allowlist: [supplier-portal.example]", "+method: GET", "+mode: allow"] },
  chat: {
    ctx: "샌드박스·정책 · 도구 8개",
    suggestions: ["오늘 차단된 호출은?", "발주는 왜 막혀 있어?", "net.fetch 열면 위험해?", "정책 변경 승인해줘"],
    replies: [
      { match: ["차단", "막"], tools: [["audit.query", "0.5s"]], text: "오늘 3건입니다. 사진 지시문 발주 시도, 채팅 승인 요청, 외부 주소 접근 시도입니다.", cites: ["감사 기록 13:46", "13:58", "13:32"] },
      { match: ["발주"], tools: [["policy.get", "0.3s"]], text: "order.submit은 사람 전용 도구입니다. 비용이 걸린 행동이라 에이전트에게 권한을 주지 않습니다.", cites: ["order.submit 정책"] },
      { match: ["위험", "열면"], kind: "refuse", tools: [], text: "허용 목록의 안전성은 네트워크 팀의 판단이 필요해 제가 평가할 수 없습니다. 변경 제안 POL-0007의 범위만 설명드릴 수 있습니다." }
    ]
  },
  error: { code: "503", message: "정책 서버에 연결할 수 없습니다" }
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
