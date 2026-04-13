"""
Tests for src/component/installers/font_installer.py

Covers:
  - install_font: creates symlink in correct font dir for linux
  - install_font: creates symlink in correct font dir for darwin
  - install_font: raises UnsupportedOsError for unsupported OS
  - install_font: no-ops when font already correctly linked
  - install_font: replaces existing symlink pointing elsewhere
  - install_font: creates font_dir if it doesn't exist
  - install_font: runs fc-cache on linux
  - install_font: does NOT run fc-cache on darwin
"""

import pytest
from pathlib import Path
from unittest.mock import patch, call

from src.component.installers.font_installer import FontInstaller
from src.exceptions import UnsupportedOsError


@pytest.fixture
def font_file(tmp_path) -> Path:
    font = tmp_path / "source_fonts" / "JetBrainsMono-Regular.ttf"
    font.parent.mkdir(parents=True)
    font.write_bytes(b"\x00\x01\x00\x00")  # minimal fake font bytes
    return font


class TestFontInstallerLinux:
    def test_creates_symlink_in_linux_font_dir(self, font_file, tmp_path):
        installer = FontInstaller("linux")
        font_dir = tmp_path / ".local" / "share" / "fonts"
        with patch.object(Path, "home", return_value=tmp_path):
            with patch("subprocess.run"):
                installer.install_font(font_file)
        expected_link = font_dir / font_file.name
        assert expected_link.is_symlink()
        assert expected_link.resolve() == font_file.resolve()

    def test_runs_fc_cache_on_linux(self, font_file, tmp_path):
        installer = FontInstaller("linux")
        with patch.object(Path, "home", return_value=tmp_path):
            with patch("subprocess.run") as mock_run:
                installer.install_font(font_file)
        mock_run.assert_called_once_with(["fc-cache", "-f"], check=False)

    def test_creates_font_dir_if_missing(self, font_file, tmp_path):
        installer = FontInstaller("linux")
        font_dir = tmp_path / ".local" / "share" / "fonts"
        assert not font_dir.exists()
        with patch.object(Path, "home", return_value=tmp_path):
            with patch("subprocess.run"):
                installer.install_font(font_file)
        assert font_dir.exists()

    def test_no_op_when_already_correctly_linked(self, font_file, tmp_path):
        installer = FontInstaller("linux")
        font_dir = tmp_path / ".local" / "share" / "fonts"
        font_dir.mkdir(parents=True)
        existing_link = font_dir / font_file.name
        existing_link.symlink_to(font_file)
        with patch.object(Path, "home", return_value=tmp_path):
            with patch("subprocess.run") as mock_run:
                installer.install_font(font_file)
        # fc-cache should not be called if font already linked correctly
        mock_run.assert_not_called()

    def test_replaces_symlink_pointing_elsewhere(self, font_file, tmp_path):
        installer = FontInstaller("linux")
        font_dir = tmp_path / ".local" / "share" / "fonts"
        font_dir.mkdir(parents=True)
        other_file = tmp_path / "other.ttf"
        other_file.write_bytes(b"\xff")
        existing_link = font_dir / font_file.name
        existing_link.symlink_to(other_file)
        with patch.object(Path, "home", return_value=tmp_path):
            with patch("subprocess.run"):
                installer.install_font(font_file)
        assert existing_link.resolve() == font_file.resolve()


class TestFontInstallerDarwin:
    def test_creates_symlink_in_darwin_font_dir(self, font_file, tmp_path):
        installer = FontInstaller("darwin")
        font_dir = tmp_path / "Library" / "Fonts"
        with patch.object(Path, "home", return_value=tmp_path):
            installer.install_font(font_file)
        expected_link = font_dir / font_file.name
        assert expected_link.is_symlink()

    def test_does_not_run_fc_cache_on_darwin(self, font_file, tmp_path):
        installer = FontInstaller("darwin")
        with patch.object(Path, "home", return_value=tmp_path):
            with patch("subprocess.run") as mock_run:
                installer.install_font(font_file)
        mock_run.assert_not_called()


class TestFontInstallerUnsupportedOs:
    def test_raises_unsupported_os_error(self, font_file):
        installer = FontInstaller("windows")
        with pytest.raises(UnsupportedOsError):
            installer.install_font(font_file)
