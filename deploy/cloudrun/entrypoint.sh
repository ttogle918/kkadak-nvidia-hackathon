#!/bin/sh
# Cloud Run 컨테이너 시작 (D27). 읽기 데이터는 /app/var(이미지), 쓰기는 전부 /tmp/kc(메모리 파일시스템 — 휘발).
set -eu

export KC_PUBLIC_MODE="${KC_PUBLIC_MODE:-1}"
export KC_TARGET_REGION="${KC_TARGET_REGION:-all}"
# KC_TRUSTED_PROXY_HOPS 는 기본값을 넣지 않는다 — 배포 env 로만(T426 실측 뒤). 없으면 IP 제한이 꺼진다.

W=/tmp/kc
mkdir -p "$W/audit" "$W/output" "$W/var"
export KC_VAR_DIR="$W/var"            # 일정 캐시(var/cache/schedule)·var 아래 쓰기
export KC_HITL_DB="$W/hitl.db"
export KC_AUDIT_DIR="$W/audit"
export KC_OUTPUT_DIR="$W/output"

# 카탈로그는 읽기 전용으로 두되 잠금 파일(.lock)이 생기므로, 쓰기 폴더에 심볼릭 링크로 묶는다(복사하지 않아 메모리 0).
mkdir -p "$W/catalog"
for f in /app/var/catalog/*; do
  ln -sfn "$f" "$W/catalog/$(basename "$f")"
done
export KC_CATALOG_DIR="$W/catalog"
export KC_INDEX_DB="${KC_INDEX_DB:-/app/var/index/kcontext.db}"
export KC_AUTO_PLACES="${KC_AUTO_PLACES:-/app/var/places/auto_places.json}"

exec uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
