#!/usr/bin/env bash
# Netlify 정적 빌드 (D27 ② 직접 CORS). 프론트 원본은 바꾸지 않고 출력 폴더에서만 바꾼다.
# 입력 env: KC_KAKAO_JS_KEY, KC_BACKEND_ORIGIN(https://호스트, 경로·포트·끝 슬래시 없음)
# 출력 폴더: 첫 번째 인자 또는 KC_DIST_DIR (기본 dist). 값은 로그에 길이만 남긴다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/frontend/k-context"
OUT="${1:-${KC_DIST_DIR:-$ROOT/dist}}"

fail() { echo "netlify_build: $1" >&2; exit 1; }

KEY="${KC_KAKAO_JS_KEY:-}"
ORIGIN="${KC_BACKEND_ORIGIN:-}"
[[ -n "$KEY" ]] || fail "KC_KAKAO_JS_KEY 가 비어 있다"
[[ ${#KEY} -le 128 ]] || fail "KC_KAKAO_JS_KEY 가 너무 길다 (길이 ${#KEY})"
[[ "$KEY" =~ ^[A-Za-z0-9._-]+$ ]] || fail "KC_KAKAO_JS_KEY 에 허용되지 않는 문자가 있다 (길이 ${#KEY})"
[[ -n "$ORIGIN" ]] || fail "KC_BACKEND_ORIGIN 이 비어 있다"
[[ "$ORIGIN" =~ ^https://[A-Za-z0-9.-]+$ ]] || fail "KC_BACKEND_ORIGIN 형식 오류 (길이 ${#ORIGIN})"

[[ -d "$SRC" ]] || fail "프론트 원본 폴더가 없다"
case "$OUT" in "$SRC"|"$SRC"/*|/) fail "출력 경로가 허용되지 않는다" ;; esac

rm -rf "$OUT"
mkdir -p "$OUT"
cp -R "$SRC"/. "$OUT"/
rm -rf "$OUT/tests" "$OUT/node_modules" "$OUT/admin.html" "$OUT/src/events/admin.js" "$OUT/config.local.js" \
  "$OUT/README.md"  # 관리자 화면은 공개 배포물에 없다(서버도 403, D24 ⑤)

printf "window.KC_KAKAO_JS_KEY = '%s';\nwindow.KC_API_BASE = '%s/api';\n" \
  "$KEY" "$ORIGIN" > "$OUT/config.local.js"

# events.html meta CSP connect-src 에 백엔드 원점 추가 (index.html 은 CSP 를 강제하지 않는다)
EV="$OUT/events.html"
grep -q "connect-src 'self'" "$EV" || fail "events.html 에서 connect-src 를 찾지 못했다"
sed -i "s|connect-src 'self'|connect-src 'self' $ORIGIN|" "$EV"

echo "netlify_build: ok (key ${#KEY}자, origin ${#ORIGIN}자) -> 출력 폴더 생성"
