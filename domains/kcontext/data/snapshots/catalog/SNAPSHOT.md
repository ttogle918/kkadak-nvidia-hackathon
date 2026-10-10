# 행사 카탈로그 스냅샷

- 출처: 서울 열린데이터광장 문화행사 정보 (`seoul_openapi`)
- 이용 조건: 공공누리 제1유형(출처표시) — 출처: 서울특별시, 서울 열린데이터광장
- 수집일: 2026-10-10 (스냅샷 생성 2026-10-10)
- 건수: 관찰값 162건 · 행사 항목 162건
- 범위: 스냅샷 날짜에 끝나지 않은 행사만 (종료일 2026-10-10 이후이거나, 종료일이 없으면 시작한 지 1년 이내 — D23). 걸러낸 항목 8550건 (그중 종료일 없이 1년 넘은 항목 20건)
- 포함하지 않은 것: 검색(Tavily 등) 유래 자료, 제보, 원응답, 키 (D12 ⑦, D19)

스냅샷은 수집 시점 자료이며 이후 바뀌었을 수 있다.

생성 명령:

```
python scripts/snapshot_catalog.py --from var/catalog --to domains/kcontext/data/snapshots/catalog
```

되돌리기: `python scripts/snapshot_catalog.py --restore --from <이 폴더> --to var/catalog`
