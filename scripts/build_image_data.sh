#!/usr/bin/env bash
# 배포 이미지에 넣을 데이터를 image-data/ 에 만든다 (D27 ④). 호스트에서, docker build 전에 실행.
#   image-data/index/kcontext.db           실록 색인 (var/index/kcontext.db 복사)
#   image-data/catalog/                    var/catalog.all 에서 서울 API(seoul_openapi) 유래만 다시 묶은 것 + 검색 색인
#   image-data/places/auto_places.json     origin == ["seoul_openapi"] 인 자동 좌표만
# Tavily(web)·TourAPI(D29)·제보 유래와 var/data/events 는 넣지 않는다. 키는 읽지도 쓰지도 않는다.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=${KC_IMAGE_OUT:-image-data}
CATALOG_SRC=${KC_IMAGE_CATALOG_SRC:-var/catalog.all}
INDEX_SRC=${KC_IMAGE_INDEX_SRC:-var/index/kcontext.db}
PLACES_SRC=${KC_IMAGE_PLACES_SRC:-var/places/auto_places.json}

for f in "$CATALOG_SRC/observations.json" "$INDEX_SRC" "$PLACES_SRC"; do
  [ -f "$f" ] || { echo "실패: $f 없음 — 4개 구 데이터로 조용히 넘어가지 않는다 (var/catalog.all 을 먼저 수집)" >&2; exit 1; }
done

rm -rf "$OUT"
mkdir -p "$OUT/index" "$OUT/places"
cp "$INDEX_SRC" "$OUT/index/kcontext.db"

uv run python scripts/snapshot_catalog.py --from "$CATALOG_SRC" --to "$OUT/catalog" --keep-ended
rm -f "$OUT/catalog/SNAPSHOT.md"
uv run python -m domains.kcontext.catalog --dir "$OUT/catalog" reindex >/dev/null

uv run python - "$PLACES_SRC" "$OUT/places/auto_places.json" <<'PY'
import json, sys
src, dst = sys.argv[1:]
items = json.load(open(src, encoding="utf-8"))
keep = [x for x in items if x.get("origin") == ["seoul_openapi"]]
json.dump(keep, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"자동 좌표: {len(keep)}/{len(items)}건 (origin == [seoul_openapi])")
PY

chmod -R a+rX "$OUT"  # 스냅샷은 0600 으로 쓰인다 — 비루트 사용자가 읽어야 한다

echo "--- image-data 크기"
for d in "$OUT"/*; do du -sh "$d"; done
du -sh "$OUT"

# 전체 이미지 크기(D28 ④): 이미 빌드된 이미지가 있으면 함께 보고, 0.5GiB(Artifact Registry 무료 저장)를 넘으면 경고한다.
TAG=${KC_IMAGE_TAG:-kc-api:local}
if command -v docker >/dev/null 2>&1 && bytes=$(docker image inspect "$TAG" --format '{{.Size}}' 2>/dev/null); then
  echo "이미지 $TAG: $((bytes / 1024 / 1024)) MiB (비압축 기준)"
  [ "$bytes" -le 536870912 ] || echo "경고: 0.5GiB 초과 — 키워드를 줄이거나 D27 (d) 예비안 검토 (D28 ④)" >&2
fi
