import pytest

from reviewdigest import config as config_mod
from reviewdigest.config import ConfigError


def _write(tmp_path, text):
    p = tmp_path / "reviewdigest.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_minimal_config(tmp_path):
    cfg = config_mod.load(_write(tmp_path, "apps: [324684580]\ncountries: [us]\n"))
    assert cfg.apps[0].id == "324684580"
    assert cfg.countries == ["us"]
    assert cfg.llm.provider == "anthropic"


def test_missing_apps_is_human_error(tmp_path):
    with pytest.raises(ConfigError, match="apps.apple.com"):
        config_mod.load(_write(tmp_path, "countries: [us]\n"))


def test_bad_country_named_in_error(tmp_path):
    with pytest.raises(ConfigError, match="zz"):
        config_mod.load(_write(tmp_path, "apps: [1]\ncountries: [zz]\n"))


def test_countries_major_expands(tmp_path):
    cfg = config_mod.load(_write(tmp_path, "apps: [1]\ncountries: major\n"))
    assert "us" in cfg.countries and len(cfg.countries) == 20


def test_app_dict_form_with_name(tmp_path):
    cfg = config_mod.load(_write(tmp_path, "apps:\n  - id: 99\n    name: Foo\ncountries: [us]\n"))
    assert cfg.apps[0].name == "Foo"


def test_unsupported_provider(tmp_path):
    with pytest.raises(ConfigError, match="provider"):
        config_mod.load(_write(tmp_path, "apps: [1]\ncountries: [us]\nllm:\n  provider: gemini\n"))


def test_non_numeric_app_id(tmp_path):
    with pytest.raises(ConfigError, match="numeric"):
        config_mod.load(_write(tmp_path, "apps: [myapp]\ncountries: [us]\n"))


def test_placeholder_app_id_exits_zero_not_error(tmp_path, capsys):
    from reviewdigest.main import main
    cfg = tmp_path / "reviewdigest.yaml"
    cfg.write_text("apps: [YOUR_APP_ID]\ncountries: [us]\n", encoding="utf-8")
    assert main(["--config", str(cfg), "--dry-run"]) == 0
    assert "isn't configured yet" in capsys.readouterr().out
