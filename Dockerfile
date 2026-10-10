# Cloud Run 이미지 (D27). 빌드 전에 `bash scripts/build_image_data.sh` 로 image-data/ 를 만든다.
# 빌드: docker build --platform linux/amd64 -t kc-api:local .
# 비밀은 이미지에 없다 — 키는 Secret Manager 에서 런타임 env 로만 들어온다.
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

RUN useradd --create-home --uid 10001 app
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-install-project

COPY core/ /app/core/
COPY backend/ /app/backend/
COPY domains/ /app/domains/
COPY deploy/llm.chat.yaml /app/deploy/llm.chat.yaml
COPY --chmod=a+rX image-data/ /app/var/
# 읽기 전용 데이터라 chown 하지 않는다(층이 두 배가 된다). 쓰기는 전부 /tmp/kc.
COPY --chmod=755 deploy/cloudrun/entrypoint.sh /app/entrypoint.sh

USER app

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
