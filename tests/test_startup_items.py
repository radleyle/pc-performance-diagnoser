"""Tests for startup item listing."""

from collector import startup_items


def test_read_plist_name_uses_label(tmp_path):
    plist = tmp_path / "com.example.helper.plist"
    plist.write_bytes(
        b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.example.helper</string>
</dict></plist>"""
    )

    assert startup_items._read_plist_name(plist) == "com.example.helper"


def test_list_startup_items_empty_on_non_macos(monkeypatch):
    monkeypatch.setattr(startup_items.sys, "platform", "linux")
    assert startup_items.list_startup_items() == []
