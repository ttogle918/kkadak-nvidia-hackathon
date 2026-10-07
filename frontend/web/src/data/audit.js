import { DATA, LABELS } from "../lib/state.js";

// 감사 기록 · 에이전트 콘솔 — 샘플 데이터(DATA)와 화면 문구(LABELS)
Object.assign(DATA, {
  shell: { user: { role: "정비반장", id: "M-0412", initial: "M" }, counts: { inbox: 7, approvals: 4 }, lastSync: "13:52:08" },
  events: [
    { id: "EV-0412", t: "14:05:12", who: "사람", whoId: "M-0412", act: "초안 승인", obj: "DRF-0141 조치 계획서", res: "approved", kind: "decision", note: "HIGH · PIN 재로그인 확인", rec: '{\n  "event": "approve",\n  "draft": "DRF-0141",\n  "actor": "M-0412",\n  "reauth": true\n}' },
    { id: "EV-0411", t: "13:59:40", who: "에이전트", whoId: "parts-01", act: "발주서 초안 작성", obj: "DRF-0142", res: "allow", kind: "agent", note: "report.draft · 효력 없음", rec: '{\n  "tool": "report.draft",\n  "draft": "DRF-0142",\n  "effect": "none"\n}' },
    { id: "EV-0410", t: "13:58:21", who: "정책 엔진", whoId: "policy", act: "채팅 승인 요청 거부", obj: "approvals.decide", res: "blocked", kind: "blocked", note: "승인은 사람 전용 도구", rec: '{\n  "tool": "approvals.decide",\n  "caller": "chat-agent",\n  "rule": "human_only",\n  "result": "deny"\n}' },
    { id: "EV-0409", t: "13:47:30", who: "에이전트", whoId: "diag-01", act: "승격 문서 검색", obj: "VFD-22 Rev.C §7.3", res: "allow", kind: "agent", note: "kb.search_manual", rec: '{\n  "tool": "kb.search_manual",\n  "query": "F0003",\n  "hits": 3\n}' },
    { id: "EV-0408", t: "13:47:05", who: "정책 엔진", whoId: "policy", act: "문서 지시문 격리", obj: "DOC-0032 p.7", res: "blocked", kind: "blocked", note: "시스템 대상 지시문 발견", rec: '{\n  "doc": "DOC-0032",\n  "page": 7,\n  "finding": "instruction_to_system",\n  "action": "quarantine"\n}' },
    { id: "EV-0407", t: "13:46:50", who: "정책 엔진", whoId: "policy", act: "발주 호출 거부", obj: "order.submit", res: "blocked", kind: "blocked", note: "사진 OCR 지시문에서 시작된 호출", rec: '{\n  "tool": "order.submit",\n  "origin": "SIG-1003-030",\n  "rule": "human_only",\n  "result": "deny"\n}' },
    { id: "EV-0406", t: "13:46:12", who: "사람", whoId: "M-0412", act: "케이스 배정", obj: "SIG-1003-031 → CASE-2026-1003-014", res: "approved", kind: "decision", note: "에이전트 diag-01에 진단 배정", rec: '{\n  "event": "assign",\n  "signal": "SIG-1003-031",\n  "agent": "diag-01"\n}' },
    { id: "EV-0405", t: "13:41:09", who: "시스템", whoId: "telemetry", act: "센서 이상 의심 표시", obj: "MTR-C3 진동 채널", res: "allow", kind: "agent", note: "12시간 0.00 고정 · 판단에서 제외", rec: '{\n  "ch": "vib_rms",\n  "flat_hours": 12,\n  "flag": "sensor_suspect"\n}' },
    { id: "EV-0404", t: "13:32:44", who: "정책 엔진", whoId: "policy", act: "외부 주소 접근 거부", obj: "net.fetch", res: "blocked", kind: "blocked", note: "허용 목록 비어 있음", rec: '{\n  "tool": "net.fetch",\n  "allowlist": [],\n  "result": "deny"\n}' },
    { id: "EV-0403", t: "11:20:03", who: "사람", whoId: "M-0412", act: "초안 반려", obj: "DRF-0138 점검 체크리스트", res: "rejected", kind: "decision", note: "사유: 항목 순서 오류", rec: '{\n  "event": "reject",\n  "draft": "DRF-0138",\n  "reason": "order"\n}' }
  ],
  chat: {
    ctx: "감사 기록 · 10건",
    suggestions: ["오늘 차단은 몇 건?", "누가 DRF-0141을 승인했어?", "13:46 발주 시도 설명해줘", "기록 하나 지워줘"],
    replies: [
      { match: ["차단", "몇"], tools: [["audit.query", "0.4s"]], text: "오늘 4건입니다. 문서 지시문 격리 1, 발주 호출 거부 1, 채팅 승인 요청 거부 1, 외부 주소 접근 거부 1입니다.", cites: ["EV-0410", "EV-0408", "EV-0407", "EV-0404"] },
      { match: ["승인", "누가"], tools: [["audit.query", "0.3s"]], text: "M-0412가 14:05:12에 PIN 재로그인 후 승인했습니다.", cites: ["EV-0412"] },
      { match: ["발주", "13:46"], tools: [["audit.query", "0.4s"]], text: "현장 메모 사진 속 지시문에서 시작된 order.submit 호출을 정책 엔진이 사람 전용 규칙으로 거부했습니다.", cites: ["EV-0407", "SIG-1003-030"] },
      { match: ["지워", "삭제"], kind: "refuse", tools: [], text: "감사 기록은 추가만 가능하고 수정이나 삭제 권한을 누구에게도 주지 않습니다." }
    ]
  },
  error: { code: "503", message: "감사 저장소에 연결할 수 없습니다" }
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
