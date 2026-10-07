// 보안 로그 샘플(OpenShell 로그를 화면에 옮긴 형태). kind:
//   ok        허용됨          deny      거부(정책 위반 시도)
//   pend      차단됨 · 승인 대기 — 사람만 approve/reject 로 바꿀 수 있다
//   approved  사람이 승인       rejected  사람이 거절
// decided_by 는 서버가 채운다(요청에서 받지 않는다). 샘플에서는 사람이 결정하기 전이라 null.

export const AUDIT_LOG = [
  { id: 'log_001', time: '09:41:02', kind: 'ok', text: { ko: '종로구청', en: 'Jongno-gu Office' }, decided_by: null },
  { id: 'log_002', time: '09:41:04', kind: 'ok', text: { ko: '한국관광공사 TourAPI', en: 'Korea Tourism Org. TourAPI' }, decided_by: null },
  {
    id: 'log_003', time: '09:41:06', kind: 'pend',
    text: { ko: 'blog.example.com · 허용 목록에 없음', en: 'blog.example.com · not on the allow list' }, decided_by: null,
  },
  {
    id: 'log_004', time: '09:42:18', kind: 'deny',
    text: { ko: '파일 읽기 시도 → 거부 · /secret/travel-key.txt · 허용된 폴더 밖', en: 'File read attempt → denied · /secret/travel-key.txt · outside allowed folder' }, decided_by: null,
  },
];
