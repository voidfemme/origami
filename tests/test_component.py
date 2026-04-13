"""
Tests for src/component/component.py

Covers:
  - normalize_os: macos -> darwin, linux stays linux, case insensitive
  - Component.__init__: correct OS normalization at construction
  - Component.__init__: default paths derived from origami_config
  - Component.__init__: custom themes_dir / scripts_dir respected
  - Component.__init__: raises NoInstallationError when no OS match
  - Component.get_required_paths: returns paths from deps, empty list when no deps
  - Component.apply_all_components: delegates to installer for each entry
  - Component.apply_fonts: delegates to font_installer for missing fonts
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.component.component import Component, normalize_os
from src.exceptions import NoInstallationError
from tests.conftest import minimal_json_path


class TestNormalizeOs:
    def test_macos_becomes_darwin(self):
        assert normalize_os("macos") == "darwin"

    def test_linux_unchanged(self):
        assert normalize_os("linux") == "linux"

    def test_termux_unchanged(self):
        assert normalize_os("termux") == "termux"

    def test_darwin_unchanged(self):
        assert normalize_os("darwin") == "darwin"

    def test_case_insensitive(self):
        assert normalize_os("MacOS") == "darwin"
        assert normalize_os("LINUX") == "linux"
        assert normalize_os("Termux") == "termux"


class TestComponentInit:
    def test_os_normalized_at_construction(self, full_build_file, fake_origami_dir):
        if full_build_file.path.exists():
            print(f"Build File exists at: {full_build_file.path}")
        else:
            print(f"Build File {full_build_file.path} does not exist.")
        c = Component(
            operating_system="macos",
            theme="test-rice",
            build_config=full_build_file,
            origami_config=fake_origami_dir,
        )
        assert c.operating_system == "darwin"

    def test_default_paths_derived_from_origami_config(
        self, minimal_build_file, fake_origami_dir
    ):
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=fake_origami_dir,
        )
        assert c.themes_dir == fake_origami_dir / "themes"
        assert c.scripts_dir == fake_origami_dir / "scripts"

    def test_custom_themes_dir_respected(
        self, minimal_build_file, fake_origami_dir, tmp_path
    ):
        custom_themes = tmp_path / "custom_themes"
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=fake_origami_dir,
            themes_dir=custom_themes,
        )
        assert c.themes_dir == custom_themes

    def test_custom_scripts_dir_respected(
        self, minimal_build_file, fake_origami_dir, tmp_path
    ):
        custom_scripts = tmp_path / "custom_scripts"
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=fake_origami_dir,
            scripts_dir=custom_scripts,
        )
        assert c.scripts_dir == custom_scripts

    def test_raises_when_no_os_match(self, minimal_build_file, fake_origami_dir):
        # minimal_build_file only has linux entries
        with pytest.raises(NoInstallationError):
            Component(
                operating_system="darwin",
                theme="test-rice",
                build_config=minimal_build_file,
                origami_config=fake_origami_dir,
            )

    def test_dependency_checker_created_when_deps_present(
        self, full_build_file, fake_origami_dir
    ):
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=full_build_file,
            origami_config=fake_origami_dir,
        )
        assert hasattr(c, "dependency_checker")

    def test_dependency_checker_absent_when_no_deps(
        self, minimal_build_file, fake_origami_dir
    ):
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=fake_origami_dir,
        )
        assert not hasattr(c, "dependency_checker")

    def test_default_origami_config_when_none(self, minimal_build_file):
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=None,
        )
        assert c.origami_config == Path.home() / ".config/origami"


class TestGetRequiredPaths:
    def test_returns_paths_when_deps_defined(
        self, full_build_file, fake_origami_dir, tmp_path
    ):
        full_build_file.deps.paths = [tmp_path / "some_path"]
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=full_build_file,
            origami_config=fake_origami_dir,
        )
        result = c.get_required_paths()
        assert result == [tmp_path / "some_path"]

    def test_returns_empty_when_no_deps(self, minimal_build_file, fake_origami_dir):
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=fake_origami_dir,
        )
        result = c.get_required_paths()
        assert result == []


class TestApplyAllComponents:
    def test_calls_apply_component_for_each_entry(
        self, minimal_build_file, fake_origami_dir
    ):
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=fake_origami_dir,
        )
        c.installer = MagicMock()
        c.apply_all_components()
        assert c.installer.apply_component.call_count == len(c.installations)

    def test_passes_correct_entries_to_installer(
        self, minimal_build_file, fake_origami_dir
    ):
        c = Component(
            operating_system="linux",
            theme="test-rice",
            build_config=minimal_build_file,
            origami_config=fake_origami_dir,
        )
        c.installer = MagicMock()
        c.apply_all_components()
        called_with = [ca.args[0] for ca in c.installer.apply_component.call_args_list]
        assert called_with == c.installations
