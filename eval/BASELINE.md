# 기준선 (Sprint 3 / T307)

> **주의: 평가셋은 사람 검수 전(`reviewed: false`, H10 미완료)이다.** 아래 "정답 일치"·재현율은 검수 전 기대값 기준이며,
> 기대값이 틀렸을 수 있다. 결과를 맞추려고 기대 정답을 고치지 않았다(다르게 나온 것은 "발견"으로만 기록).
> 이후 T311·T323 은 이 문서와 같은 구성(아래 "측정 구성")으로 재측정한다.

## Stage 1 게이트 상태
- D15 사람 승인 대기 — 기준선(이 문서)은 사람이 승인하기 전까지 확정이 아니다. T311 이후 단계는 승인 뒤에 진행한다.

## 측정 환경
| 항목 | 값 |
|---|---|
| 측정일 | 2026-10-09 (UTC 11:59 ~ 12:18) |
| git head | `fb46d928af29b0fc0bde3fc080c45f6ad93c760c` (작업 트리에 평가 코드·drafts 미커밋 상태) |
| 모델 | provider 설정 그대로 (`deploy/llm.chat.yaml` 의 `chat` feature, `openai/gpt-oss-20b`). env 재정의(`CHAT_MODEL`·`SCHEDULE_MODEL`) 없음 |
| LLM 설정 해시(sha256) | `f57cece065fc29ce8e2072866eb39f915533c960d9ecdb7607e7e290d1f9df14` |
| 호출 파라미터 | 없음(temperature·seed·response_format 미지정 — 현재 코드 그대로) |
| 캐시 | 끔 |
| 색인(`var/index/kcontext.db`) | total 7,713 · fts_enabled True · jongno 4,265 · jung 2,261 · gangnam 846 · mapo 683 (tier S 7,713) |
| 결과 파일 | `eval/results/baseline-offline-20261009-115921.json` · `baseline-pipeline-20261009-115925.json` · `baseline-api-20261009-121143.json` |

### 측정 구성 (T311·T323 이 같게 쓴다)
- 파이프라인 층: `eval/drafts/schedule.json` 의 기대 `ok` 케이스 18개 × 3회 = 54 실행, 캐시 끔.
- API 층: 고정 10케이스 × 3회 = 30 실행, 캐시 끔, backend `uvicorn backend.app:app --port 8000` 직접 기동.
- API 층 고정 10케이스: `sch_ko_basic_01, sch_ko_ampm_01, sch_ko_range_01, sch_ko_multiday_01, sch_ko_header_01, sch_ko_hotel_01, sch_ko_noyear_01, sch_ko_long_01, sch_en_basic_01, sch_en_hotel_01`

- 기준선은 전체 env 전달 방식으로 측정됐다. 측정 당시 셸에 KC_*·LLM_*·APP_*·키 관련 변수는 0개였고(코디네이터 확인, 이름만), 자식은 .env 를 core.llm 허용 목록 로더로 읽으므로 제품 경로와 같은 조건이다. 측정기는 이후 허용 목록 방식으로 고쳤다.

### 실제 호출 수
- 측정기 상한(예상 최대): 파이프라인 108 + API 90 = 198 (승인 상한 210 이내).
- 실제(추정): 현재 코드는 일정 이해에서 재시도가 없어 파이프라인 54회(실행당 1회). API 는 실행당 일정 이해 1회(30회) + 일반 챗봇 폴백 1회 = 31회. **합계 약 85회.** 측정기가 호출 수를 직접 세지는 않으므로 추정이다.
- 429·중단 없음(`interrupted: false`).

## 결정적 세트 (LLM 없음, `baseline-offline`)
| suite | 통과 | 비고 |
|---|---|---|
| gate | 22/24 | 실패 2건(아래 알려진 실패) |
| mentions | 13/13 | |
| judge | 18/18 | |
| guard | 7/7 | |

## 일정 이해 지표 (§6.1)
| 지표 | 파이프라인 층 (54 실행, 18 케이스) | API 층 (30 실행, 10 케이스) |
|---|---|---|
| 폴백 건수·률 | 2 / 54 = 3.7% (`fallback_llm` 1 · `fallback_unverified` 1) | 1 / 30 = 3.3% (`fallback_chat` 1) |
| 변동 케이스 수 | 8 / 18 | 4 / 10 |
| 일정 개수 변동률 | 16.7% | 13.3% |
| 정답 일치 건수·률 | 35 / 54 = 64.8% | 17 / 30 = 56.7% |
| 앵커 재현율 | 0.743 | 0.778 |
| 앵커 정밀도 | 1.000 | 0.980 |
| 지연 p50 (전체) | 9,961 ms | 6,543 ms |
| 지연 p95 (전체) | 27,145 ms | 46,615 ms |
| 지연 p50 / p95 (성공 실행만) | 9,932 / 26,543 ms | 6,543 / 46,615 ms |
| 좌표 부착률 | 0.910 | 0.880 |

### 문제 코드 분포 (상위 10, 건수)
| 순위 | 파이프라인 층 | API 층 |
|---|---|---|
| 1 | DAY_UNTIMED 46 | DAY_UNTIMED 24 |
| 2 | QUOTE_NOT_FOUND 23 | QUOTE_NOT_FOUND 13 |
| 3 | AMPM_ASSUMED 9 | AMPM_ASSUMED 6 |
| 4 | COORD_UNKNOWN 7 | COORD_UNKNOWN 6 |
| 5 | FREE_SLOTS_INCOMPLETE 6 | EVENTS_UNAVAILABLE 3 |
| 6 | TIME_WITHOUT_DATE 6 | FREE_SLOTS_INCOMPLETE 3 |
| 7 | YEAR_UNKNOWN 6 | TIME_WITHOUT_DATE 3 |
| 8 | TIME_NOT_IN_QUOTE 2 | YEAR_UNKNOWN 3 |
| 9 | DATE_NOT_IN_QUOTE 1 | (이하 없음) |
| 10 | LLM_FAILED 1 · NO_ANCHOR_VERIFIED 1 | |

### 측정에서 나온 실패·발견 (기대 정답은 고치지 않음)
- 파이프라인 `sch_ko_basic_01` 3회차: `fallback_llm`(`LLM_FAILED`, 60,156 ms). 전송 한도 `timeout_s: 60` 에 걸린 것으로 보인다(응답 원문은 기록하지 않음). 재시도 없음.
- 파이프라인 `sch_ko_header_01` 2회차: `fallback_unverified`(`QUOTE_NOT_FOUND` ×3 → `NO_ANCHOR_VERIFIED`). 앵커는 나왔으나 인용 검증을 못 통과.
- API `sch_ko_multiday_01` 2회차: `fallback_chat`(일반 챗봇으로 폴백).
- `sch_ko_long_01`: 3회 모두 앵커 1개(기대 5개) → 정답 일치 0/3. 일관되게 놓침 — 입력이 길 때의 재현율 문제로 보이며 검수 전 기대값이라 확정은 아니다.
- `sch_en_hotel_01`: 3회 모두 date 불일치(실제 from 이 null 이라 to 의 날짜로 비교됨) — 기대값 또는 match 규칙(숙소 date=체크인) 검수 필요(H10).
- 변동이 큰 케이스(파이프라인): `sch_ko_basic_01`·`sch_ko_ampm_01`·`sch_ko_pm_01`·`sch_ko_header_01`·`sch_ko_hotel_02`·`sch_ko_outdict_01`·`sch_en_basic_01`·`sch_en_list_01` 등 앵커 개수가 회차마다 다르다.
- 전체 실행에서 `TIMEOUT_S`(90초)에 걸린 실행은 0. 파이프라인 최대 60.2초(위 LLM_FAILED), API 최대 58.2초(`sch_ko_ampm_01`, 성공).

## 알려진 실패 (`eval/kc.py run --check --known-failures` 가 제외)
- `known-failure: gate/gate_t_nodate_places` — 날짜 없이 장소만 나열한 일정 문장을 게이트(`looks_like_schedule`)가 일정으로 인정하지 않음(재현율 쪽 누락). 규칙 기반 게이트의 한계로, 평가셋이 사람 검수 전이라 기대값 확정도 H10 후.
- `known-failure: gate/gate_f_date_place_q` — 날짜·장소가 들어 있지만 질문인 문장을 게이트가 일정으로 통과시킴(정밀도 쪽 오탐). 같은 사유.
- 위 둘은 Stage 1 에서 코드를 고치지 않으므로 기록만 한다. 일정 이해(LLM) 측정의 폴백·불일치는 위 "발견" 절에 있다(결정적 세트 실패가 아니므로 known-failure 줄이 아님).

## §6.2 목표 (T311 이 달성해야 하는 값)
기준선: 파이프라인 F0=2 · C0=8 · E0=35 · N=54, API F0=1 · C0=4 · E0=17 · N=30.

| 항목 | 파이프라인 층 | API 층 | 계산 |
|---|---|---|---|
| 폴백 건수 | **≤ 1** | **≤ 0** | min(⌊F0/2⌋, ⌊N×0.05⌋): 파이프라인 min(1, 2)=1, API min(0, 1)=0 |
| 변동 케이스 수 | **≤ 4** | **≤ 2** | ⌊C0/2⌋ |
| 정답 일치 건수 | **≥ 33** | **≥ 15** | E0 − 2 |
| `TIMEOUT_S` 에 걸린 성공 실행 | 0 | — | 기준선 0 |
| 캐시 켬 재요청 변동 | 0 | 0 | 구조상 |
| 결정적 세트 | gate 22/24 외 전부(gate 22건·mentions 13·judge 18·guard 7) 계속 통과 | | |

## §6.4 시간 예산
- L = 기준선 파이프라인 **성공 실행** p95 = 26.543 s.
- L × 1.5 = 39.8 → ⌈⌉ = 40 → `T_llm` = min(75, max(20, 40)) = **40초**.

| 이름 | 값 | 계산 |
|---|---|---|
| F 프론트 요청 상한 | 100초 | 고정 |
| R backend 파이프라인 한도 | 90초 | F − 10 |
| B 파이프라인 안 LLM 예산 | 75초 | R − 15 |
| T_llm LLM 1회 한도 | **40초** | min(75, max(20, ⌈26.543 × 1.5⌉)) |
| 재시도 허용 | 첫 시도 경과 e ≤ **35초** | e + T_llm ≤ B |
| 일반 챗봇 진입 | 파이프라인 경과 s ≤ **55초** | s + T_llm ≤ F − 5 |

지연 과다 아님(L×1.5 < 75). 참고: API 층 p95 46.6초는 F 100초 이내지만, 기준선 T_llm 40초를 넘는 성공 실행이 API 에 있다(`sch_ko_ampm_01` 58초, `sch_ko_header_01` 47초 — 일반 챗봇 연쇄 가능성은 미확인). T_llm 40초로 줄이면 이런 느린 호출은 시간 초과로 바뀔 수 있으므로 T311 에서 폴백률을 함께 본다.

## S5~S7 켬·끔 (근거: `docs/spikes/llm_params.md` 결론 표 + 이번 측정)
| 수단 | 판정 | 근거 |
|---|---|---|
| S5 temperature 0 | **켬** | 스파이크: 공급자 수용, 5회 중 4회 동일(부분 확인). 기준선 C0=8>0 (§6.3 조건 충족). 공식 범위 0~1 |
| S6 seed 7 | **끔** | 스파이크: temperature 0 + seed 7 이 5회 중 3회만 동일 → "5회 동일" 조건 미충족. 켜려면 사람 결정 |
| S7 json_object | **끔** | 이번 측정의 폴백 중 `LLM_BAD_JSON`·`LLM_UNEXPECTED_SHAPE` 비율 0/3 (파이프라인 폴백 `LLM_FAILED` 1·`NO_ANCHOR_VERIFIED` 1, API 폴백 1건은 코드 미확인) = 0% < 30%. 스파이크도 해석 실패 0/25 |
| S8 reasoning_effort low | **T311 에서 판단 (후보 메모)** | 스파이크에서 토큰(288~400 vs 570~1,880)·지연(5~11초 vs 8~45초) 감소 확인. 추출 정확도는 미평가 — T311 에서 정답 일치로 확인 |
| S9 max_tokens · S10 NO_ANCHOR_VERIFIED 재시도 | T311 에서 판단 | 이번 측정에서 `NO_ANCHOR_VERIFIED` 1건 관찰(S10 후보) |

참고(T308 입력): 스파이크 메모에 따라 `temperature` 허용 범위는 서버 문서(0~1)로, `max_tokens` 상한은 문서(4096)로 맞출지 검토.

## 한계
- 평가셋 `reviewed: false` — 정답 일치·재현율의 절대값은 검수 후 달라질 수 있다.
- 반복 3회, 케이스당 표본이 작아 변동 지표의 오차가 크다(노이즈 허용 2건은 §6.2 에 반영).
- 실제 호출 수는 추정이며 API 층의 폴백 원인 코드는 결과 파일에 없다.
- 결과 파일에는 키·LLM 원문·reply 를 넣지 않았다(`nvapi-`·`Bearer`·`NVIDIA_API_KEY` grep 0건).
