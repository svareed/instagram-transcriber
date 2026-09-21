"""Regression tests for Settings env parsing.

An unset `COOKIES_FILE=` in .env used to arrive as "", which Path() resolves
to Path("."). yt-dlp was then handed the working directory as a cookie jar and
every download failed with `[Errno 13] Permission denied: '.'`.
"""

import pytest

from backend.config import Settings


@pytest.mark.parametrize("blank", ["", "   ", "\t", "\n"])
def test_blank_cookies_file_is_treated_as_unset(blank: str) -> None:
    assert Settings(_env_file=None, cookies_file=blank).cookies_file is None


def test_blank_cookies_file_in_env_file_is_treated_as_unset(tmp_path) -> None:
    """The exact shape .env.example ships, and setup.sh copies verbatim."""
    env_file = tmp_path / ".env"
    env_file.write_text("COOKIES_FILE=\nMODEL_SIZE=auto\n", encoding="utf-8")

    assert Settings(_env_file=env_file).cookies_file is None


def test_omitted_cookies_file_is_none() -> None:
    assert Settings(_env_file=None).cookies_file is None


def test_explicit_cookies_path_is_preserved(tmp_path) -> None:
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")

    settings = Settings(_env_file=None, cookies_file=str(cookies))

    assert settings.cookies_file == cookies


def test_cookies_path_from_env_file_is_preserved(tmp_path) -> None:
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text(f"COOKIES_FILE={cookies}\n", encoding="utf-8")

    assert Settings(_env_file=env_file).cookies_file == cookies
