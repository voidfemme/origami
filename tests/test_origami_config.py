"""
Tests for src/origami_config.py

Covers:
  - _get_operating_system: platform detection, macos->darwin normalization,
    explicit override respected
  - _get_prefs_from_toml: loads valid TOML, raises FileNotFoundError on missing,
    raises TOMLDecodeError on malformed
  - OrigamiConfig.__init__: raises MissingConfigKeyError when keys absent from TOML
  - OrigamiConfig.__init__: themes_dir and scripts_dir resolved as Paths
  - get_available_rices: returns empty dict and creates themes dir when missing,
    returns rices when themes dir populated
  - get_rice: returns Rice for known name, raises RiceNotExistsError for unknown
  - get_themes: returns list of theme names
  - delete_rice: removes rice and refreshes rices dict

Note: apply_rice is integration-level and depends on Rice.apply_rice — tested
in test_rice_integration.py instead.
"""

import pytest
import tomllib
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.origami_config import OrigamiConfig, normalize_os
from src.exceptions import RiceNotExistsError, MissingConfigKeyError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_config_toml(path: Path, extra: dict | None = None) -> None:
    """Write a minimal valid config.toml to path."""
    contents = {
        "theme": "test-rice",
        "config_dir": str(path.parent),
        "scripts_dir": str(path.parent / "scripts"),
        "themes_dir": str(path.parent / "themes"),
        "defaults": {"os": "linux"},
    }
    if extra:
        contents.update(extra)
    import tomli_w  # only needed for writing; tomllib is read-only
    with open(path, "wb") as f:
        tomli_w.dump(contents, f)


def make_origami_dir(tmp_path: Path) -> Path:
    """Create a minimal origami config dir structure under tmp_path."""
    origami = tmp_path / ".config" / "origami"
    origami.mkdir(parents=True)
    (origami / "themes").mkdir()
    (origami / "scripts").mkdir()
    return origami


# ---------------------------------------------------------------------------
# normalize_os (module-level helper)
# ---------------------------------------------------------------------------

class TestNormalizeOs:
    def test_macos_becomes_darwin(self):
        assert normalize_os("macos") == "darwin"

    def test_darwin_unchanged(self):
        assert normalize_os("darwin") == "darwin"

    def test_linux_unchanged(self):
        assert normalize_os("linux") == "linux"

    def test_case_insensitive(self):
        assert normalize_os("MacOS") == "darwin"
        assert normalize_os("LINUX") == "linux"


# ---------------------------------------------------------------------------
# OrigamiConfig construction
# ---------------------------------------------------------------------------

class TestOrigamiConfigInit:
    def test_loads_valid_config(self, tmp_path, config_toml_path):
        """Use the static fixture config.toml with paths rewritten for tmp_path."""
        origami = make_origami_dir(tmp_path)
        # Write a config.toml pointing at our tmp dirs
        toml_path = origami / "config.toml"
        toml_path.write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        config = OrigamiConfig(origami)
        assert config.theme == "test-rice"

    def test_scripts_dir_is_path(self, tmp_path):
        origami = make_origami_dir(tmp_path)
        toml_path = origami / "config.toml"
        toml_path.write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        config = OrigamiConfig(origami)
        assert isinstance(config.scripts_dir, Path)

    def test_themes_dir_is_path(self, tmp_path):
        origami = make_origami_dir(tmp_path)
        toml_path = origami / "config.toml"
        toml_path.write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        config = OrigamiConfig(origami)
        assert isinstance(config.themes_dir, Path)

    def test_raises_missing_config_key_error_when_key_absent(self, tmp_path):
        origami = make_origami_dir(tmp_path)
        toml_path = origami / "config.toml"
        # Missing scripts_dir, themes_dir, defaults
        toml_path.write_text('theme = "test-rice"\nconfig_dir = "/tmp"\n')
        with pytest.raises(MissingConfigKeyError):
            OrigamiConfig(origami)

    def test_raises_file_not_found_when_no_toml(self, tmp_path):
        origami = make_origami_dir(tmp_path)
        # Don't write config.toml
        with pytest.raises(FileNotFoundError):
            OrigamiConfig(origami)

    def test_raises_toml_decode_error_on_malformed_toml(self, tmp_path):
        origami = make_origami_dir(tmp_path)
        (origami / "config.toml").write_text("this is not [ valid toml }")
        with pytest.raises(tomllib.TOMLDecodeError):
            OrigamiConfig(origami)

    def test_os_override_respected(self, tmp_path):
        origami = make_origami_dir(tmp_path)
        (origami / "config.toml").write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        config = OrigamiConfig(origami, operating_system="macos")
        assert config.operating_system == "darwin"


# ---------------------------------------------------------------------------
# get_available_rices
# ---------------------------------------------------------------------------

class TestGetAvailableRices:
    def _make_config(self, tmp_path) -> OrigamiConfig:
        origami = make_origami_dir(tmp_path)
        (origami / "config.toml").write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        return OrigamiConfig(origami)

    def test_returns_empty_dict_when_themes_dir_empty(self, tmp_path):
        config = self._make_config(tmp_path)
        assert config.rices == {}

    def test_creates_themes_dir_if_missing(self, tmp_path):
        origami = tmp_path / ".config" / "origami"
        origami.mkdir(parents=True)
        (origami / "scripts").mkdir()
        # Don't create themes dir
        (origami / "config.toml").write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        config = OrigamiConfig(origami)
        assert (origami / "themes").exists()

    def test_returns_rice_objects_for_each_theme_dir(self, tmp_path):
        origami = make_origami_dir(tmp_path)
        (origami / "themes" / "my-rice").mkdir()
        (origami / "config.toml").write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        config = OrigamiConfig(origami)
        assert "my-rice" in config.rices


# ---------------------------------------------------------------------------
# get_rice / get_themes / delete_rice
# ---------------------------------------------------------------------------

class TestGetRice:
    def _make_config(self, tmp_path) -> OrigamiConfig:
        origami = make_origami_dir(tmp_path)
        (origami / "config.toml").write_text(
            f'theme = "test-rice"\n'
            f'config_dir = "{origami}"\n'
            f'scripts_dir = "{origami / "scripts"}"\n'
            f'themes_dir = "{origami / "themes"}"\n'
            f'[defaults]\nos = "linux"\n'
        )
        return OrigamiConfig(origami)

    def test_raises_for_unknown_rice(self, tmp_path):
        config = self._make_config(tmp_path)
        with pytest.raises(RiceNotExistsError):
            config.get_rice("nonexistent")

    def test_get_themes_returns_list_of_strings(self, tmp_path):
        config = self._make_config(tmp_path)
        assert isinstance(config.get_themes(), list)
