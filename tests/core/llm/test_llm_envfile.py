from core.llm import load_allowed_keys, resolve_env

OTHER = "other-secret-" + "z" * 8


def _write(tmp_path, text):
    p = tmp_path / ".env"
    p.write_text(text, encoding="utf-8")
    return p


def test_parses_allowed_names_only(tmp_path):
    p = _write(
        tmp_path,
        "# 주석\n\nMAIL_PASSWORD=" + OTHER + "\nSECRET_KEY='" + OTHER + "'\n"
        "NVIDIA_API_KEY=\"nvapi-aaa\"\nexport NVIDIA_API_KEY_A=nvapi-bbb # 설명\n"
        "NVIDIA_API_KEY_B='nvapi-c d'\nNVIDIA_API_KEY_EXTRA=x\n",
    )
    got = load_allowed_keys(p)
    assert got == {"NVIDIA_API_KEY": "nvapi-aaa", "NVIDIA_API_KEY_A": "nvapi-bbb",
                   "NVIDIA_API_KEY_B": "nvapi-c d"}
    assert OTHER not in repr(got)


def test_empty_value_comment_line_and_missing_file(tmp_path):
    p = _write(tmp_path, "NVIDIA_API_KEY=\n#NVIDIA_API_KEY_A=x\nbroken line\n")
    assert load_allowed_keys(p) == {}
    assert load_allowed_keys(tmp_path / "nope") == {}


def test_shell_env_wins_and_other_names_not_exported(tmp_path):
    p = _write(tmp_path, "NVIDIA_API_KEY=from-file\nNVIDIA_API_KEY_A=file-a\nMAIL_PASSWORD=" + OTHER)
    env = resolve_env(p, environ={"NVIDIA_API_KEY": "from-shell", "PATH": "/bin",
                                  "LLM_BACKEND": "api"})
    assert env == {"NVIDIA_API_KEY": "from-shell", "NVIDIA_API_KEY_A": "file-a", "LLM_BACKEND": "api"}
    assert OTHER not in repr(env)


def test_blank_shell_value_falls_back_to_file(tmp_path):
    p = _write(tmp_path, "NVIDIA_API_KEY=from-file\n")
    assert resolve_env(p, environ={"NVIDIA_API_KEY": "  "}) == {"NVIDIA_API_KEY": "from-file"}


def test_does_not_touch_os_environ(tmp_path, monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    p = _write(tmp_path, "NVIDIA_API_KEY=from-file\n")
    import os

    resolve_env(p, environ={})
    assert "NVIDIA_API_KEY" not in os.environ
