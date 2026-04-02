from pathlib import Path

from sophion.config import BackendConfig, Config, StudyConfig


def test_config_defaults(tmp_base):
    config = Config.load(base_dir=tmp_base)
    assert config.base_dir == tmp_base
    assert config.backend.primary == "claude-code"
    assert config.backend.api_provider is None
    assert config.backend.api_key is None
    assert config.backend.model is None
    assert config.study.enabled is False
    assert config.study.socratic is False
    assert config.study.proof_verification is False


def test_config_defaults_without_base_dir():
    config = Config.load()
    assert config.base_dir == Path.home() / ".sophion"


def test_config_from_toml(tmp_base):
    tmp_base.mkdir(parents=True)
    config_file = tmp_base / "config.toml"
    config_file.write_text(
        '[backend]\n'
        'primary = "api"\n'
        'api_provider = "anthropic"\n'
        'model = "claude-sonnet-4-20250514"\n'
        "\n"
        "[study]\n"
        "enabled = true\n"
        "socratic = true\n"
    )
    config = Config.load(base_dir=tmp_base)
    assert config.backend.primary == "api"
    assert config.backend.api_provider == "anthropic"
    assert config.backend.model == "claude-sonnet-4-20250514"
    assert config.study.enabled is True
    assert config.study.socratic is True
    assert config.study.proof_verification is False


def test_config_toml_partial_override(tmp_base):
    tmp_base.mkdir(parents=True)
    config_file = tmp_base / "config.toml"
    config_file.write_text(
        "[study]\n"
        "enabled = true\n"
    )
    config = Config.load(base_dir=tmp_base)
    assert config.backend.primary == "claude-code"
    assert config.study.enabled is True
