from pathlib import Path

from app.config import Settings


def test_settings_come_from_the_environment(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("LIBRARY_DB", str(tmp_path / "lib.sqlite"))
    monkeypatch.setenv("READER_PASSWORD", "sesame")
    settings = Settings(_env_file=None)
    assert settings.env == "prod"
    assert settings.library_db == tmp_path / "lib.sqlite"
    assert settings.reader_password == "sesame"


def test_defaults_need_no_environment(monkeypatch):
    for name in ("ENV", "LIBRARY_DB", "READER_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)
    assert settings.env == "dev"
    assert settings.library_db.name == "library.sqlite"
    assert settings.reader_password is None
