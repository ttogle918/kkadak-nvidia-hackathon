# domains/<name>/ — 미션 공개 후 채우는 슬롯

```
domains/<name>/
  data/      # 시드·합성·공개 데이터 (원본은 읽기 전용으로 취급)
  tools/     # 이 도메인의 MCP 도구 (mcp_server/tools/ 에서 등록)
  skills/    # 이 도메인의 제품 스킬(SKILL.md) — 필요하면 최상위 skills/ 로 승격
  evals/     # 평가 케이스 (if문 테스트 통과 여부 점검 대상)
```
뼈대(`core/`)를 고치지 않고 도메인만 추가하는 것이 목표다. `core/` 를 고쳐야 한다면 `docs/DECISIONS.md` 에 이유부터 적는다.
