"""Tests for reveal helper safety checks."""

from collector.reveal import reveal_in_file_manager


def test_reveal_rejects_outside_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("nope")

    monkeypatch.setattr("collector.reveal.Path.home", lambda: home)

    result = reveal_in_file_manager(str(outside))

    assert result["ok"] is False
    assert "home directory" in result["message"]


def test_reveal_rejects_missing_path(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    missing = home / "missing.txt"

    monkeypatch.setattr("collector.reveal.Path.home", lambda: home)

    result = reveal_in_file_manager(str(missing))

    assert result["ok"] is False
    assert "does not exist" in result["message"]
