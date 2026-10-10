# Cloud Run 이미지 (D27)

공개 배포용 컨테이너. 제품은 호스트에서도 돌고, 이 폴더는 **선택 배포 경로**다.

## 빌드 순서
```
bash scripts/build_image_data.sh                      # image-data/ (커밋하지 않음)
docker build --platform linux/amd64 -t kc-api:local . # Cloud Run 은 amd64 (T402 §6)
bash scripts/build_image_data.sh                      # (선택) 이미지 크기 출력, 0.5GiB 넘으면 경고 — D28 ④
```

## 이미지에 담는 것 (`image-data/` → `/app/var/`)
| 경로 | 내용 |
|---|---|
| `index/kcontext.db` | 실록 색인(4개 구 키워드 그대로, D28) |
| `catalog/` | `var/catalog.all`(서울 25개 구)에서 `seoul_openapi` 유래만 다시 묶은 것(`snapshot_catalog.py --keep-ended`) + 검색 색인 |
| `places/auto_places.json` | 자동 좌표 중 `origin == ["seoul_openapi"]` 만 (D25 ⑤) |

넣지 않는 것: Tavily(web)·제보·TourAPI 유래(TourAPI 는 저장 자체가 없고 요청 시점에만 부른다, D29), `var/data/events`(웹 수집 원자료), `domains/kcontext/data/raw`, 비밀. 비밀(`NVIDIA_API_KEY`·`DATA_GO_KR_SERVICE_KEY`)은 Secret Manager → 런타임 env 로만 들어온다.

## 쓰기 경로 (전부 `/tmp/kc` — 인메모리, 휘발, 인스턴스 메모리에 합산)
`entrypoint.sh` 가 정한다: `KC_HITL_DB`·`KC_AUDIT_DIR`·`KC_OUTPUT_DIR`·`KC_VAR_DIR`(일정 캐시 `cache/schedule`)·`KC_CATALOG_DIR`.
카탈로그는 카탈로그 잠금 파일(`.lock`)을 쓰기 때문에 `/tmp/kc/catalog` 에 **심볼릭 링크**로 묶는다(복사하지 않아 메모리 0). 읽기 전용 데이터(`KC_INDEX_DB`·`KC_AUTO_PLACES`)는 `/app/var` 에서 그대로 읽는다.
**전제**: 공개 모드에서는 카탈로그 쓰기(제보·관리자 수집)가 닫혀 있다(D24). 쓰기가 생기면 저장(`mkstemp` + `os.replace`)이 링크를 `/tmp` 의 실파일로 바꾸고, 그 크기(카탈로그 약 100MB)가 컨테이너 메모리에 더해진다(D27 ⑦) — 쓰기를 여는 변경은 이 방식을 다시 본다.
`/tmp` 크기는 감사 JSONL 회전·일정 캐시 상한(D27 ⑦, T436)이 묶는다.

## 기본값
`KC_PUBLIC_MODE=1`, `KC_TARGET_REGION=all`, `--workers 1`. `KC_TRUSTED_PROXY_HOPS` 는 **기본값이 없다** — T426 실측 뒤 배포 env 로만 넣는다(없으면 IP 제한 꺼짐).

## 로컬 점검 (키 없이)
```
docker run --rm -p 8080:8080 kc-api:local   # curl localhost:8080/api/meta -> public:true
```
키가 없으면 LLM 호출 경로는 실패하므로 외부 호출 없는 엔드포인트(`/api/meta`·`/api/events/*`)만 확인한다.
