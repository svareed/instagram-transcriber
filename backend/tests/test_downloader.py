"""Regression tests for how cookie settings reach yt-dlp.

These never touch the network: yt_dlp.YoutubeDL is replaced with a stub that
records the options it was constructed with.
"""

import threading
from pathlib import Path

import pytest

from backend.core import downloader

SHORTCODE = "AAAAAAAAAAA"
FAKE_URL = f"https://www.instagram.com/reel/{SHORTCODE}/"


@pytest.fixture
def captured_opts(monkeypatch, tmp_path: Path) -> dict:
    """Swap in a fake YoutubeDL and return the dict it was handed."""
    recorded: dict = {}

    class _FakeYoutubeDL:
        def __init__(self, opts: dict) -> None:
            recorded.update(opts)

        def __enter__(self) -> "_FakeYoutubeDL":
            return self

        def __exit__(self, *_exc: object) -> bool:
            return False

        def extract_info(self, url: str, download: bool = True) -> dict:
            # Stand in for the postprocessor writing the extracted audio.
            (tmp_path / f"{SHORTCODE}.wav").write_bytes(b"RIFF")
            return {
                "id": SHORTCODE,
                "title": "Example",
                "uploader": "example",
                "duration": 12.0,
            }

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _FakeYoutubeDL)
    return recorded


def test_no_cookiefile_option_when_cookies_are_unset(captured_opts, tmp_path: Path) -> None:
    downloader.download_media(FAKE_URL, tmp_path, None, threading.Event())

    assert "cookiefile" not in captured_opts


def test_cookiefile_option_is_passed_when_configured(captured_opts, tmp_path: Path) -> None:
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")

    downloader.download_media(FAKE_URL, tmp_path, cookies, threading.Event())

    assert captured_opts["cookiefile"] == str(cookies)


def test_download_result_points_at_the_extracted_audio(captured_opts, tmp_path: Path) -> None:
    result = downloader.download_media(FAKE_URL, tmp_path, None, threading.Event())

    assert result.audio_path == tmp_path / f"{SHORTCODE}.wav"
    assert result.title == "Example"
    assert result.source_duration == 12.0
