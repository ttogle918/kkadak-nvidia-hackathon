# eval/

평가셋과 결과(`eval/results/`). `testset.json` 의 기대 정답 변경은 사람 승인 사항(훅이 차단한다).
각 케이스는 "에이전트 없이 규칙만으로도 통과하는가"를 점검한다 — 통과하면 에이전트 가치를 검증하지 못한다.
**규칙만으로 통과하는 세트(gate·judge·guard·mentions)는 에이전트 성능 지표가 아니라 회귀 기준이다.**

## 실행 (입구는 `eval/kc.py` 하나, `eval/` 은 패키지가 아니다)
```
uv run python eval/kc.py run [--set eval/testset.json] [--drafts eval/drafts] [--suites gate,mentions,judge,guard]
    [--db var/index/kcontext.db] [--out eval/results] [--label NAME] [--check] [--known-failures FILE]
uv run python eval/kc.py validate [--drafts eval/drafts]    # kc-eval/v1 형식 검증, 문제 있으면 1
uv run python eval/kc.py stability | snapshot-mentions | gen-judge   # 각각 T305·T302·T303 모듈(없으면 종료 2)
```
- 세트: `--set` 이 있으면 그 파일(`{"schema", "reviewed": true, "suites": {...}}`), 없으면 `eval/drafts/*.json`
  (`reviewed: false`, 경고 출력). 없는 세트의 suite 는 `skipped`(실패 아님).
- 결과: `eval/results/<label>-<YYYYmmdd-HHMMSS>.json` (`kc-eval-result/v1`). 키·LLM 원문은 담지 않는다.
- `--check`: 실패가 있으면 종료 1. `--known-failures` 파일의 `` `known-failure: <suite>/<id>` `` 줄은 제외.
- 종료 코드: 0 정상 · 1 실패/검증 문제 · 2 사용법·세트 읽기 오류·모르는 suite·모듈 없음.

## suite 와 지표 (sprint-3 §6.1)
- gate: `backend.schedule_gate.looks_like_schedule` — 정밀도·재현율.
- mentions: 색인 조회 `reason` + `top[].article_id` 순서 비교 — 스냅샷 일치·no_match·잘림·precision@3(라벨 있을 때만).
- judge: `observation_from_dict` → `build_entries` → `search_events`. 제목으로 비교, `excluded` 사유는 앞부분 일치,
  `unresolved_conflict_fields` 는 `{행사 제목: [필드명]}`(예 `price_kind`). 함정별 통과율.
- guard: `screen` + `understand(text, complete=<불리면 실패>)`. **`"kind": "guard"` 인 judge 케이스와
  schedule 세트의 `problems_include` 에 `INJECTION_BLOCKED` 가 있는 케이스는 guard 가 처리하고 `run_judge` 는 건너뛴다.**
- 앵커 비교 규칙은 `kc_eval/match.py` 한 곳(`match_anchors`)이다. 안정성 지표(T305)도 이것을 쓴다.
