from pathlib import Path

from warhammer_rag.config import Settings


def test_paths_follow_project_root_without_creating_directories(tmp_path):
    root = tmp_path / "another checkout"
    settings = Settings(project_root=root, raw_dir=Path("custom/raw"))
    assert settings.rulebook_path == root / "custom/raw/core_rules.pdf"
    assert settings.eval_dir == root / "evaluation/datasets"
    assert not root.exists()


def test_env_overrides_dotenv_and_secret_is_masked(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("GOOGLE_API_KEY=file-secret\nGOOGLE_MODEL=file-model\n")
    monkeypatch.setenv("GOOGLE_API_KEY", "environment-secret")
    settings = Settings()
    assert settings.google_api_key.get_secret_value() == "environment-secret"
    assert settings.google_model == "file-model"
    assert "environment-secret" not in repr(settings)
    assert "environment-secret" not in settings.model_dump_json()


def test_blank_values_are_not_configured(tmp_path):
    (tmp_path / ".env").write_text("GOOGLE_API_KEY=\nGOOGLE_MODEL=\n")
    settings = Settings()
    assert not settings.has_api_key
    assert settings.google_model is None


def test_absolute_directory_override_is_preserved(tmp_path):
    absolute_raw = tmp_path / "elsewhere"
    settings = Settings(project_root=tmp_path / "project", raw_dir=absolute_raw)
    assert settings.raw_dir == absolute_raw
