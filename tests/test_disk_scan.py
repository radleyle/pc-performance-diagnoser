"""Tests for disk scan helpers."""

from pathlib import Path

from collector import disk_scan


def test_scan_home_folders_returns_sorted_results(tmp_path, monkeypatch):
    home = tmp_path / "home"
    downloads = home / "Downloads"
    documents = home / "Documents"
    downloads.mkdir(parents=True)
    documents.mkdir(parents=True)
    (downloads / "big.bin").write_bytes(b"x" * 5000)
    (documents / "small.txt").write_bytes(b"x" * 100)

    monkeypatch.setattr(disk_scan.Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr(disk_scan, "_scan_home_folders_du", lambda _limit: None)

    results = disk_scan.scan_home_folders(limit=5)

    assert len(results) == 2
    assert results[0]["name"] == "Downloads"
    assert results[0]["size_bytes"] >= results[1]["size_bytes"]


def test_find_large_files_respects_threshold(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    large = home / "movie.mp4"
    small = home / "note.txt"
    large.write_bytes(b"x" * (2 * 1024 * 1024))
    small.write_bytes(b"x" * 1024)

    monkeypatch.setattr(disk_scan.Path, "home", staticmethod(lambda: home))

    results = disk_scan.find_large_files(min_mb=1, limit=10, max_depth=2)

    assert len(results) == 1
    assert results[0]["name"] == "movie.mp4"
