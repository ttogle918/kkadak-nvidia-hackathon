import json
from pathlib import Path

import pytest

from core.llm import LlmConfigError, load_config, parse_config

REPO = Path(__file__).resolve().parents[3]
FAKE = "nvapi-" + "x" * 24  # 런타임 조립 — 리터럴 키 모양 금지


def _data(**over):
    d = {
        "providers": {
            "pa": {"api_key_envs": ["K_A1", "K_A2"], "base_url": "http://a", "max_concurrency": 2},
            "pb": {"api_key_envs": ["K_B"], "base_url": "http://b", "max_concurrency": 1},
        },
        "features": {
            "feature1": {"provider": "pa", "model": "m1"},
            "feature2": {"provider": "pb", "model": "m2"},
        },
    }
    d.update(over)
    return d


ENV = {"K_A1": "v1", "K_A2": "v2", "K_B": "v3"}


def test_parse_ok_defaults():
    cfg = parse_config(_data(), ENV)
    assert cfg.features["feature2"].provider == "pb"
    assert cfg.providers["pa"].api_key_envs == ("K_A1", "K_A2")
    assert cfg.providers["pa"].cooldown_s > 0


def test_example_yaml_loads_and_has_todo():
    path = REPO / "deploy" / "llm.example.yaml"
    text = path.read_text(encoding="utf-8")
    assert "# TODO: feature1, feature2 채우기" in text
    cfg = load_config(path, {"NVIDIA_API_KEY_A": "a", "NVIDIA_API_KEY_B": "b"})
    assert set(cfg.features) == {"feature1", "feature2"}
    assert cfg.providers["nvidia_a"].max_concurrency == 4


def test_example_yaml_has_no_key_like_values():
    text = (REPO / "deploy" / "llm.example.yaml").read_text(encoding="utf-8")
    assert "nvapi-" not in text and "sk-" not in text


def test_missing_env_reports_names_only():
    env = {"K_A1": FAKE}  # K_A2·K_B 없음
    with pytest.raises(LlmConfigError) as ei:
        parse_config(_data(), env)
    msg = str(ei.value)
    assert "K_A2" in msg
    assert FAKE not in msg


def test_empty_env_value_counts_as_missing():
    with pytest.raises(LlmConfigError, match="K_B"):
        parse_config(_data(), {**ENV, "K_B": "  "})


def test_env_not_checked_when_env_none():
    assert parse_config(_data()).providers


def test_feature_refs_unknown_provider():
    d = _data(features={"feature1": {"provider": "nope", "model": "m"}})
    with pytest.raises(LlmConfigError, match="nope"):
        parse_config(d, ENV)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["providers"]["pa"].pop("base_url"),
        lambda d: d["providers"]["pa"].update(max_concurrency=0),
        lambda d: d["providers"]["pa"].update(max_concurrency=True),
        lambda d: d["providers"]["pa"].update(api_key_envs=[]),
        lambda d: d["providers"]["pa"].update(api_key_envs=["K_A1", "K_A1"]),
        lambda d: d["providers"]["pa"].update(cooldown_s=0),
        lambda d: d["providers"]["pa"].update(extra=1),
        lambda d: d["features"]["feature1"].pop("model"),
        lambda d: d["features"].update({"bad name": {"provider": "pa", "model": "m"}}),
        lambda d: d.update(unknown=1),
        lambda d: d.update(features={}),
    ],
)
def test_invalid_config_rejected(mutate):
    d = _data()
    mutate(d)
    with pytest.raises(LlmConfigError):
        parse_config(d, ENV)


def test_pasted_key_value_in_api_key_envs_not_echoed():
    d = _data()
    d["providers"]["pa"]["api_key_envs"] = [FAKE]
    with pytest.raises(LlmConfigError) as ei:
        parse_config(d, ENV)
    assert FAKE not in str(ei.value)


def test_load_json_and_missing_file(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps(_data()), encoding="utf-8")
    assert load_config(p, ENV).features["feature1"].model == "m1"
    with pytest.raises(LlmConfigError):
        load_config(tmp_path / "none.yaml", ENV)


def test_yaml_subset_errors_have_line_numbers(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("providers:\n  pa: {api_key_envs: [X\nfeatures:\n", encoding="utf-8")
    with pytest.raises(LlmConfigError, match="2번째 줄"):
        load_config(p, {})


def test_yaml_quoted_hash_and_colon_kept(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(
        "providers:\n"
        '  pa: {api_key_envs: [K_A1], base_url: "http://h:1/#x", max_concurrency: 2}  # c\n'
        "features:\n"
        "  feature1: {provider: pa, model: m}\n",
        encoding="utf-8",
    )
    cfg = load_config(p, ENV)
    assert cfg.providers["pa"].base_url == "http://h:1/#x"
