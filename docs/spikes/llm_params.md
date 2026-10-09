확인 날짜: 2026-10-09 (T306, Sprint 3 §6.3 S5~S7). 실호출 25회 (상한 30, H4 승인).

# T306 — LLM 호출 파라미터 (temperature · seed · response_format · reasoning_effort · max_tokens)

본문·키·응답 원문은 적지 않는다. 표의 값은 상태 코드, `finish_reason`, content 길이(자), sha256 앞 12자, `usage`, 지연(ms)뿐이다.

## 1. 대상
| 항목 | 값 | 출처 |
|---|---|---|
| 엔드포인트 | `POST https://integrate.api.nvidia.com/v1/chat/completions` | `deploy/llm.chat.yaml` provider `nvidia`, `core/llm/http_transport.py` 가 `{base_url}/chat/completions` 로 붙임 |
| 모델 | `openai/gpt-oss-20b` | `deploy/llm.chat.yaml` features.chat |
| 현재 코드가 보내는 본문 | `model`, `messages`, `max_tokens`(생성자 기본 2048), `stream: false` 뿐 | `http_transport.py` |
| 호출 입력 | system = `understand.SYSTEM_PROMPT`, user = `wrap("10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야", source="schedule_text").render()` | 입력 prompt tokens 는 매번 434 |
| 키 | `.env` 에서 dotenv 로 읽어 메모리에서만 사용 | 규칙 1 |

## 2. 공식 레퍼런스 (확인 날짜 2026-10-09)
출처: https://build.nvidia.com/openai/gpt-oss-20b/modelcard (페이지에 내장된 OpenAPI 스키마), 보조 https://docs.api.nvidia.com/nim/reference/openai-gpt-oss-20b (SPA 라 스키마 본문은 위 페이지에서 읽음).

| 파라미터 | 문서의 기재 |
|---|---|
| `temperature` | 있음. 기본 1, **0~1**(T308 검증 범위 0..2 보다 좁다) |
| `top_p` | 있음. 기본 1, 0 초과 1 이하. "temperature 와 top_p 를 둘 다 바꾸는 것은 권장하지 않음" |
| `max_tokens` | 있음. 기본 4096, **최대 4096**, 최소 1 (T308 검증 범위 1..32768 보다 좁다) |
| `reasoning_effort` | 있음. enum `low` / `medium` / `high`, 기본 `medium` |
| `stream`, `stop`, `frequency_penalty`, `presence_penalty`, `tools` | 있음 (이번 범위 밖) |
| **`seed`** | **스키마에 없음 (미기재)** |
| **`response_format`** | **스키마에 없음 (미기재)** (`json_object` 문자열도 페이지에 없음) |

즉 seed·response_format 은 "문서상 지원 여부 미확인"이고, 아래 실호출로 동작만 본다.

## 3. 파라미터 하나씩 더한 호출 (기준 위에 1개씩, 각 1회)
| # | 추가한 것 | HTTP | finish | content 자 | sha12 | JSON 해석 | completion tokens | ms |
|---|---|---|---|---|---|---|---|---|
| 1 | (없음, 기준) | 200 | stop | 342 | 7f5ccfef3cdf | 예 | 1084 | 24421 |
| 2 | temperature 0 | 200 | stop | 341 | a7163d038e20 | 예 | 864 | 22771 |
| 3 | top_p 1 | 200 | stop | 341 | a7163d038e20 | 예 | 967 | 22251 |
| 4 | seed 7 | 200 | stop | 368 | d31e705e010e | 예 | 799 | 21710 |
| 5 | response_format json_object | 200 | stop | 335 | 31bf31de56ad | 예 | 1140 | 36025 |
| 6 | reasoning_effort low | 200 | stop | 398 | 014ef315b83b | 예 | 303 | 9420 |
| 7 | max_tokens 1024 | 200 | stop | 349 | cf4ba669fad9 | 예 | 701 | 9788 |
| 8 | max_tokens 4096 | 200 | stop | 349 | cf4ba669fad9 | 예 | 948 | 17428 |

- 8개 모두 **200**: 서버가 어떤 파라미터도 거부하지 않았다(seed·response_format 포함). 무시했는지는 이 표만으로 알 수 없다.
- 모든 응답에 reasoning 필드가 있었고(content 와 별도), 추론 토큰이 completion tokens 대부분을 차지한다(content 330~400자인데 completion 300~1900).
- max_tokens 1024 에서도 `finish_reason` 은 stop — 이 입력의 completion 은 최대 약 1900 토큰(아래 표 #21)까지 나왔으므로 1024 는 일부 실행에서 `length` 로 잘릴 수 있다. 이번 호출에서 잘림은 관측하지 못했다(1024 한도 호출 1회 701토큰).

## 4. 결정성 (각 5회, 같은 입력)
| 구성 | sha12 (호출 순서) | 동일 |
|---|---|---|
| temperature 0 단독 | 0a20df627e9d, a7163d038e20, a7163d038e20, a7163d038e20, a7163d038e20 | **4/5** |
| temperature 0 + seed 7 | d31e705e010e, d31e705e010e, d31e705e010e, 201c380c6589, 847727851172 | **3/5** |

지연(ms): temp0 = 22453 / 18597 / 15078 / 8036 / 14058, temp0+seed7 = 14864 / 12544 / 22442 / 16712 / 19662. completion tokens 는 같은 sha 끼리도 569~1164 로 달라 서버 쪽 추론 경로가 매번 다르다(비결정 원인은 서버 쪽으로 추정, 미확인).

관찰 (sha 만 비교, 해석은 추정):
- 기준(파라미터 없음)을 3회 반복한 sha 는 7f5ccfef3cdf / 847727851172 / cf4ba669fad9 로 **3회 모두 다름**. temperature 0 은 4/5 동일로 분산을 줄였지만 완전 고정은 아니다.
- seed 7 만 넣은 호출(#4, 기본 temperature 1)의 sha d31e705e010e 가 temp0+seed7 3회와 같다. temperature 1 에서 우연히 일치하기 어려워 seed 가 어떤 영향을 준다는 정황이지만, 5회 동일은 아니다.
- temp0 단독(4/5)이 temp0+seed7(3/5)보다 낮지 않다 — 5회 표본으로는 seed 의 추가 효과를 말할 수 없다.

## 5. JSON 해석 (S7 근거)
`understand._parse_llm_json` 로 content 를 해석한 결과.
| 구성 | 호출 수 | JSON 해석 성공 | 지연 ms |
|---|---|---|---|
| 기준 | 3 | 3/3 | 24421, 27265, 11232 |
| response_format json_object | 3 | 3/3 | 36025, 44749, 19488 |
| temp0 + seed7 + json_object + low (합친 구성) | 3 | 3/3 | 6838, 4915, 10906 |

- 이번 입력(짧은 한 문장, 총 25회)에서 **JSON 해석 실패는 어떤 구성에서도 0건**. 기준에서 실패가 재현되지 않아 json_object 의 개선 효과는 측정할 수 없다.
- json_object 는 기준보다 느린 쪽(3회 평균 약 33초 vs 약 21초)이지만 표본 3개 + 추론 토큰 변동이라 "느려진다"고 결론내지 않는다.

## 6. 지연 (ms)
| 구성 | 값 |
|---|---|
| 기준 3회 | 24421 / 27265 / 11232 |
| temp0 6회 (#2 + 5회) | 22771 / 22453 / 18597 / 15078 / 8036 / 14058 |
| reasoning_effort low 단독 1회 | 9420 (completion 303) |
| 합친 구성(low 포함) 3회 | 6838 / 4915 / 10906 (completion 288~400) |
| 전체 25회 최대 | 44749 (json_object, completion 1880) |

reasoning_effort low 를 넣은 4회는 completion 이 288~400 토큰, 5~11초로 나머지(570~1880 토큰, 8~45초)보다 뚜렷이 짧고 빠르다. 단, 추출 결과의 정확도(앵커 내용)는 이 스파이크에서 채점하지 않았다 — 품질 영향은 T311 에서 본다.

## 7. 결론 표 (§6.3 판정용)
| 수단 | 판정 | 근거 | §6.3 조건에 대한 의미 |
|---|---|---|---|
| S5 temperature 0 | **받아들임 · 효과 확인(부분)** | 200. 5회 중 4회 동일(기준 3회는 모두 다름). 완전 고정은 아님 | "받아들임" 조건 충족. 남은 조건은 기준선 C0 > 0 (T307). 공식 범위는 0~1 |
| S6 seed 7 | **받아들임 · 효과 불명** | 200(문서에 없는 파라미터인데 거부되지 않음). temp0+seed7 5회 중 3회 동일 → **"5회 동일" 조건 미충족**. seed 7 단독 sha 가 합친 구성과 같은 정황은 있음 | "temperature 0·seed 5회 동일" 미충족 → **S6 은 켜지 않는 쪽**. 켜려면 사람 결정 |
| S7 json_object | **받아들임 · 효과 불명** | 200(문서에 없음). 해석 실패는 모든 구성에서 0/25 라 개선을 측정 못 함 | 기준선 폴백 중 `LLM_BAD_JSON`·`LLM_UNEXPECTED_SHAPE` ≥ 30% 인지는 T307 이 본다. 이 입력에선 근거 없음 |
| top_p 1 | 받아들임 · 효과 불명 | 200. 기본값과 같은 값이라 의미 없음. 문서도 temperature 와 함께 바꾸지 말라 함 | 쓰지 않는다 |
| reasoning_effort low | **받아들임 · 효과 확인(지연·토큰)** | 200, 4회 모두 completion 288~400 토큰·5~11초. JSON 해석 4/4. 정확도는 미평가 | S8 은 T311 이 정한다. 그때 후보로 유력 |
| max_tokens 1024 / 4096 | 받아들임 · 효과 불명 | 둘 다 200·stop. 이번 호출에서 잘림 없음. 문서상 상한 4096 | 현재 코드 기본 2048 은 범위 안. **T308 이 허용하는 최대 32768 은 문서 상한 4096 을 넘으므로 검증 범위를 4096 으로 줄여야 한다**(계약 변경 아님, 값 검증 상수) |
| 거부(HTTP 4xx) | 없음 | 25회 전부 200 (429 없음) | — |
| 미확인 | seed·response_format 의 문서상 지원 여부, 서버 비결정의 원인, 정확도 영향 | 레퍼런스 스키마에 없음 | — |

## 8. T308 에 주는 메모
- `temperature` 허용 범위를 서버 문서(0~1)에 맞출지 검토. 현재 명세는 0..2.
- `max_tokens` 허용 범위 상한이 문서(4096)보다 큼.
- 한 번의 호출이 8~45초 걸렸다(추론 토큰 포함). 이 입력 하나로 §6.4 의 T_llm 을 정하지 말고 T307 의 p95 를 쓴다.

## 9. 호출 기록
- 총 실호출 **25회** (상한 30 미만): 파라미터별 8 + 결정성 10 + 기준 추가 2 + json_object 추가 2 + 합친 구성 3.
- 재시도·429·타임아웃 없음. 스크립트는 레포 밖 임시 디렉터리에 두었고 키 값은 어디에도 출력·저장하지 않았다.
