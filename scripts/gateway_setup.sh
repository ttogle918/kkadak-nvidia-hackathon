#!/bin/sh
# OpenShell 게이트웨이에 NVIDIA 추론 provider 를 등록한다 (호스트에서 1회).
# 키는 셸 env 의 NVIDIA_API_KEY 에서 읽히고 게이트웨이에만 저장된다 — 샌드박스에는 들어가지 않는다.
# 사용: export NVIDIA_API_KEY=...; scripts/gateway_setup.sh [model]
set -eu
MODEL="${1:-nvidia/nemotron-3-super-120b-a12b}"
: "${NVIDIA_API_KEY:?NVIDIA_API_KEY 를 셸에 export 하세요 (파일에 쓰지 않는다)}"

openshell status
openshell provider create --name nvidia-prod --type nvidia --from-existing
openshell inference set --provider nvidia-prod --model "$MODEL"
openshell provider list && openshell inference get
