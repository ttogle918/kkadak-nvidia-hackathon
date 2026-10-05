"""LLM 설정 로드·검증 (D5). 표준 라이브러리만 쓴다.

설정에는 키 값이 아니라 env 변수 **이름**만 적는다. 에러 메시지에도 이름만 나온다.
설정 파일은 JSON 이거나 `deploy/llm.example.yaml` 모양의 YAML 부분집합(최상위 `providers:`·
`features:`, 항목은 한 줄짜리 `{...}` 흐름 매핑)이다. 외부 YAML 라이브러리는 쓰지 않는다.

가정(문서 미확인, CLAUDE.md 규칙 4): 게이트웨이의 다중 provider·모델 라우팅 지원은 확인 전이다.
그래서 provider 이름이 호출 대상을 가리키는 유일한 키이고, env 변수 이름 대신 게이트웨이
provider 이름으로 바꿔 끼울 수 있게 `api_key_envs` 해석을 `resolve_keys` 한 곳에 모았다.

백엔드 스위치: 키는 provider 단위로 고르고 env 로 바뀌는 것은 엔드포인트(api|local)뿐이다.
자동 폴백은 없다 — 로컬이 죽었다고 조용히 외부 API 로 요청(본문)이 나가면 안 되므로 사람이
환경변수로 명시한다. 로컬 백엔드는 호스트 경로 전용이다(샌드박스 안은 D1 에 따라 inference.local).
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "FeatureConfig",
    "LlmConfig",
    "LlmConfigError",
    "LlmError",
    "LlmUnavailable",
    "ProviderConfig",
    "UnknownFeature",
    "load_config",
    "parse_config",
    "resolve_backend",
    "resolve_keys",
]

DEFAULT_COOLDOWN_S = 30.0
DEFAULT_TIMEOUT_S = 60.0
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_FEATURE_NAME = re.compile(r"^[A-Za-z0-9_.\-]+$")
_PROVIDER_KEYS = {
    "api_key_envs",
    "base_url",
    "max_concurrency",
    "local_max_concurrency",
    "cooldown_s",
    "timeout_s",
    "local_base_url",
    "local_api_key_envs",
}
BACKENDS = ("api", "local")
BACKEND_ENV = "LLM_BACKEND"


class LlmError(Exception):
    pass


class LlmConfigError(LlmError, ValueError):
    pass


class UnknownFeature(LlmError, KeyError):
    pass


class LlmUnavailable(LlmError):
    pass


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key_envs: tuple[str, ...]
    base_url: str
    max_concurrency: int
    cooldown_s: float = DEFAULT_COOLDOWN_S
    timeout_s: float = DEFAULT_TIMEOUT_S
    local_base_url: str | None = None
    local_api_key_envs: tuple[str, ...] = ()
    local_max_concurrency: int | None = None  # None 이면 max_concurrency 와 같은 값(별도 세마포어)

    def concurrency_for(self, backend: str) -> int:
        if backend == "local" and self.local_max_concurrency is not None:
            return self.local_max_concurrency
        return self.max_concurrency

    def base_url_for(self, backend: str) -> str:
        if backend == "local":
            if not self.local_base_url:
                raise LlmConfigError(f"provider {self.name!r}: local_base_url 이 없다")
            return self.local_base_url
        return self.base_url

    def key_envs_for(self, backend: str) -> tuple[str, ...]:
        return self.local_api_key_envs if backend == "local" else self.api_key_envs


@dataclass(frozen=True)
class FeatureConfig:
    name: str
    provider: str
    model: str


@dataclass(frozen=True)
class LlmConfig:
    providers: Mapping[str, ProviderConfig] = field(default_factory=dict)
    features: Mapping[str, FeatureConfig] = field(default_factory=dict)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonempty(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _env_names(name: str, key: str, envs: Any, *, allow_empty: bool) -> tuple[str, ...]:
    if not isinstance(envs, (list, tuple)) or (not envs and not allow_empty):
        raise LlmConfigError(f"provider {name!r}: {key} 는 비어 있지 않은 목록이어야 한다")
    for i, e in enumerate(envs):
        # 값이 잘못 들어왔을 때 그 값을 에러에 싣지 않는다(키를 붙여 넣은 실수 대비). 위치만 보고.
        if not isinstance(e, str) or not _ENV_NAME.match(e):
            raise LlmConfigError(
                f"provider {name!r}: {key}[{i}] 는 env 변수 이름(영문·숫자·_)이어야 한다"
            )
    if len(set(envs)) != len(envs):
        raise LlmConfigError(f"provider {name!r}: {key} 에 중복이 있다")
    return tuple(envs)


def _parse_provider(name: str, raw: Any) -> ProviderConfig:
    if not isinstance(raw, Mapping):
        raise LlmConfigError(f"provider {name!r}: 매핑이어야 한다")
    extra = set(raw) - _PROVIDER_KEYS
    if extra:
        raise LlmConfigError(f"provider {name!r}: 알 수 없는 설정 키 {sorted(map(str, extra))}")
    for req in ("api_key_envs", "base_url", "max_concurrency"):
        if req not in raw:
            raise LlmConfigError(f"provider {name!r}: 필수 키 {req} 가 없다")
    envs = _env_names(name, "api_key_envs", raw["api_key_envs"], allow_empty=False)
    local_envs = _env_names(
        name, "local_api_key_envs", raw.get("local_api_key_envs", []), allow_empty=True
    )
    if not _nonempty(raw["base_url"]):
        raise LlmConfigError(f"provider {name!r}: base_url 이 비어 있다")
    local_url = raw.get("local_base_url")
    if "local_base_url" in raw and not _nonempty(local_url):
        raise LlmConfigError(f"provider {name!r}: local_base_url 이 비어 있다")
    mc = raw["max_concurrency"]
    if isinstance(mc, bool) or not isinstance(mc, int) or mc < 1:
        raise LlmConfigError(f"provider {name!r}: max_concurrency 는 1 이상의 정수여야 한다")
    lmc = raw.get("local_max_concurrency")
    if "local_max_concurrency" in raw and (
        isinstance(lmc, bool) or not isinstance(lmc, int) or lmc < 1
    ):
        raise LlmConfigError(
            f"provider {name!r}: local_max_concurrency 는 1 이상의 정수여야 한다"
        )
    nums = {"cooldown_s": DEFAULT_COOLDOWN_S, "timeout_s": DEFAULT_TIMEOUT_S}
    for k in nums:
        if k in raw:
            if not _is_num(raw[k]) or raw[k] <= 0:
                raise LlmConfigError(f"provider {name!r}: {k} 는 0 보다 큰 숫자여야 한다")
            nums[k] = float(raw[k])
    return ProviderConfig(
        name=name,
        api_key_envs=tuple(envs),
        base_url=raw["base_url"],
        max_concurrency=mc,
        cooldown_s=nums["cooldown_s"],
        timeout_s=nums["timeout_s"],
        local_base_url=local_url,
        local_api_key_envs=local_envs,
        local_max_concurrency=lmc,
    )


def backend_env_name(feature: str) -> str:
    return f"{BACKEND_ENV}_{re.sub(r'[^A-Z0-9_]', '_', feature.upper())}"


def resolve_backend(feature: str, env: Mapping[str, str]) -> str:
    """기능별 LLM_BACKEND_<FEATURE> > 전역 LLM_BACKEND > 기본 api. 잘못된 값은 이름만 보고한다.

    빈 문자열도 잘못된 값이다(fail-closed: 의도를 추측하지 않는다).
    """
    for var in (backend_env_name(feature), BACKEND_ENV):
        if var in env:
            if env[var] not in BACKENDS:  # 값은 에러에 싣지 않는다
                raise LlmConfigError(f"env 변수 {var} 는 {list(BACKENDS)} 중 하나여야 한다")
            return env[var]
    return "api"


def resolve_keys(
    provider: ProviderConfig, env: Mapping[str, str], backend: str = "api"
) -> list[tuple[str, str]]:
    """(env 변수 이름, 값) 목록. 누락·빈 값이면 **이름만** 밝혀 LlmConfigError.

    local 백엔드는 키가 없어도 되므로 `local_api_key_envs` 가 비면 빈 목록이다.
    게이트웨이 provider 로 바꿔 끼울 때 이 함수만 교체한다(가정, 문서 미확인).
    """
    provider.base_url_for(backend)  # local_base_url 없으면 fail-closed
    envs = provider.key_envs_for(backend)
    missing = [n for n in envs if not env.get(n, "").strip()]
    if missing:
        raise LlmConfigError(f"provider {provider.name!r}: env 변수가 없거나 비어 있다: {missing}")
    return [(n, env[n]) for n in envs]


def parse_config(data: Mapping[str, Any], env: Mapping[str, str] | None = None) -> LlmConfig:
    """매핑을 검증해 LlmConfig 로. env 를 주면 참조한 변수가 있는지도 시작 시점에 확인한다."""
    if not isinstance(data, Mapping):
        raise LlmConfigError("설정 최상위는 매핑이어야 한다")
    extra = set(data) - {"providers", "features"}
    if extra:
        raise LlmConfigError(f"알 수 없는 최상위 키 {sorted(map(str, extra))}")
    raw_p, raw_f = data.get("providers"), data.get("features")
    if not isinstance(raw_p, Mapping) or not raw_p:
        raise LlmConfigError("providers 가 비어 있다")
    if not isinstance(raw_f, Mapping) or not raw_f:
        raise LlmConfigError("features 가 비어 있다")
    providers = {str(n): _parse_provider(str(n), r) for n, r in raw_p.items()}
    # api 키 env 가 로컬 서버로 가면 안 된다 — local 목록은 어떤 provider 의 api 목록과도 겹치지 않는다.
    api_envs = {e for p in providers.values() for e in p.api_key_envs}
    for p in providers.values():
        overlap = sorted(set(p.local_api_key_envs) & api_envs)
        if overlap:
            raise LlmConfigError(
                f"provider {p.name!r}: local_api_key_envs 가 api_key_envs 와 겹친다: {overlap}"
            )
    features: dict[str, FeatureConfig] = {}
    norm_seen: dict[str, str] = {}
    for fname, r in raw_f.items():
        fname = str(fname)
        if not _FEATURE_NAME.match(fname):
            raise LlmConfigError(f"feature 이름이 올바르지 않다: {fname!r}")
        norm = backend_env_name(fname)
        if norm in norm_seen:
            raise LlmConfigError(
                f"feature {norm_seen[norm]!r}·{fname!r} 이 같은 env 변수 {norm} 로 정규화된다"
            )
        norm_seen[norm] = fname
        if not isinstance(r, Mapping) or set(r) != {"provider", "model"}:
            raise LlmConfigError(f"feature {fname!r}: provider·model 두 키만 있어야 한다")
        if not _nonempty(r["provider"]) or not _nonempty(r["model"]):
            raise LlmConfigError(f"feature {fname!r}: provider·model 이 비어 있다")
        if r["provider"] not in providers:
            raise LlmConfigError(f"feature {fname!r}: 없는 provider {r['provider']!r} 를 참조한다")
        features[fname] = FeatureConfig(fname, r["provider"], r["model"])
    cfg = LlmConfig(providers=providers, features=features)
    if env is not None:
        used: dict[str, set[str]] = {n: set() for n in providers}
        for f in features.values():
            used[f.provider].add(resolve_backend(f.name, env))
        for p in providers.values():
            for backend in used[p.name] or {"api"}:
                resolve_keys(p, env, backend)
    return cfg


# ---- 최소 YAML 부분집합 ----------------------------------------------------------------------


def _strip_comment(line: str) -> str:
    quote = ""
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            return line[:i]
    return line


def _split_top(s: str, sep: str) -> list[str]:
    parts, buf, depth, quote = [], [], 0, ""
    for ch in s:
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if quote or depth != 0:
        raise LlmConfigError("설정 파싱 실패: 따옴표나 괄호가 닫히지 않았다")
    parts.append("".join(buf))
    return parts


def _scalar(tok: str) -> Any:
    tok = tok.strip()
    if tok == "":
        raise LlmConfigError("설정 파싱 실패: 빈 값")
    if tok[0] in "\"'":
        if len(tok) < 2 or tok[-1] != tok[0]:
            raise LlmConfigError("설정 파싱 실패: 따옴표가 맞지 않는다")
        return tok[1:-1]
    if tok.startswith("["):
        if not tok.endswith("]"):
            raise LlmConfigError("설정 파싱 실패: 목록이 닫히지 않았다")
        inner = tok[1:-1].strip()
        return [_scalar(t) for t in _split_top(inner, ",")] if inner else []
    if tok.startswith("{"):
        if not tok.endswith("}"):
            raise LlmConfigError("설정 파싱 실패: 매핑이 닫히지 않았다")
        return _flow_map(tok[1:-1])
    for conv in (int, float):
        try:
            return conv(tok)
        except ValueError:
            pass
    return tok


def _flow_map(inner: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not inner.strip():
        return out
    for item in _split_top(inner, ","):
        kv = _split_top(item, ":")
        if len(kv) < 2:
            raise LlmConfigError("설정 파싱 실패: `키: 값` 모양이 아닌 항목이 있다")
        key = kv[0].strip()
        if not key:
            raise LlmConfigError("설정 파싱 실패: 빈 키")
        out[key] = _scalar(":".join(kv[1:]))
    return out


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    data: dict[str, dict[str, Any]] = {}
    section: str | None = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        try:
            if not line[0].isspace():
                if not line.endswith(":"):
                    raise LlmConfigError("최상위 줄은 `이름:` 모양이어야 한다")
                section = line[:-1].strip()
                data[section] = {}
                continue
            if section is None:
                raise LlmConfigError("최상위 섹션 밖의 들여쓴 줄")
            name, sep, rest = line.strip().partition(":")
            if not sep or not name.strip():
                raise LlmConfigError("`이름: {...}` 모양이어야 한다")
            val = _scalar(rest)
            if not isinstance(val, dict):
                raise LlmConfigError("항목 값은 `{...}` 이어야 한다")
            data[section][name.strip()] = val
        except LlmConfigError as exc:
            raise LlmConfigError(f"{lineno}번째 줄: {exc}") from None
    return data


def load_config(path: str | Path, env: Mapping[str, str] | None = None) -> LlmConfig:
    """파일(.json 또는 YAML 부분집합)을 읽어 검증한다. env 기본값은 os.environ."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise LlmConfigError(f"설정 파일을 읽을 수 없다: {p}") from exc
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise LlmConfigError(f"JSON 파싱 실패: {exc}") from None
    else:
        data = _parse_yaml_subset(text)
    return parse_config(data, os.environ if env is None else env)
