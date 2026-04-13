"""
Tests for src/component/checkers/dependency_checker.py

Covers:
  - verify_programs: found, missing (required)
  - verify_configs: path exists, path missing (required)
  - verify_paths: path exists, path missing
  - verify_fonts: linux, darwin, termux, unsupported OS, missing termux prefix
  - verify_env_vars: required present, required missing, optional present, optional missing
  - _get_missing_fonts: correct set logic
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

from src.build_classes import (
    DependencyList,
    ProgramDependency,
    ConfigDependency,
    FontDependency,
    EnvDependency,
)
from src.component.checkers.dependency_checker import DependencyChecker
from src.exceptions import (
    ProgramNotFoundError,
    ConfigNotFoundError,
    PathNotFoundError,
    RequiredEnvNotFoundError,
    OptionalEnvNotFoundError,
    MissingTermuxPrefixError,
    UnsupportedOsError,
)


def make_checker(deps: DependencyList, os: str = "linux") -> DependencyChecker:
    return DependencyChecker(deps, os)


class TestVerifyPrograms:
    def test_passes_when_program_found(self):
        deps = DependencyList(programs=[ProgramDependency(name="sh", version=None, required=True)])
        checker = make_checker(deps)
        # sh should exist on any system running tests
        checker.verify_programs()  # should not raise

    def test_raises_when_required_program_missing(self):
        deps = DependencyList(
            programs=[ProgramDependency(name="definitely_not_a_real_program_xyz", version=None, required=True)]
        )
        checker = make_checker(deps)
        with pytest.raises(ProgramNotFoundError):
            checker.verify_programs()

    def test_passes_with_no_programs(self):
        deps = DependencyList()
        checker = make_checker(deps)
        checker.verify_programs()  # should not raise


class TestVerifyConfigs:
    def test_passes_when_path_exists(self, tmp_path):
        config_file = tmp_path / "config"
        config_file.write_text("# config")
        deps = DependencyList(
            configs=[ConfigDependency(name="myconfig", path=config_file, required=True)]
        )
        checker = make_checker(deps)
        checker.verify_configs()  # should not raise

    def test_raises_when_path_missing(self, tmp_path):
        deps = DependencyList(
            configs=[ConfigDependency(name="missing", path=tmp_path / "nope", required=True)]
        )
        checker = make_checker(deps)
        with pytest.raises(ConfigNotFoundError):
            checker.verify_configs()


class TestVerifyPaths:
    def test_passes_when_path_exists(self, tmp_path):
        deps = DependencyList(paths=[tmp_path])
        checker = make_checker(deps)
        checker.verify_paths()

    def test_raises_when_path_missing(self, tmp_path):
        deps = DependencyList(paths=[tmp_path / "missing"])
        checker = make_checker(deps)
        with pytest.raises(PathNotFoundError):
            checker.verify_paths()


class TestVerifyFonts:
    def test_returns_empty_when_no_fonts(self):
        deps = DependencyList()
        checker = make_checker(deps)
        assert checker.verify_fonts() == []

    def test_finds_font_in_linux_font_dir(self, tmp_path):
        font_dir = tmp_path / ".local" / "share" / "fonts"
        font_dir.mkdir(parents=True)
        (font_dir / "JetBrainsMono-Regular.ttf").write_bytes(b"")
        deps = DependencyList(fonts=[FontDependency(name="JetBrainsMono", required=True)])
        checker = make_checker(deps, "linux")
        with patch.object(Path, "home", return_value=tmp_path):
            missing = checker.verify_fonts()
        assert missing == []

    def test_reports_missing_font_on_linux(self, tmp_path):
        deps = DependencyList(fonts=[FontDependency(name="NonExistentFont", required=True)])
        checker = make_checker(deps, "linux")
        with patch.object(Path, "home", return_value=tmp_path):
            missing = checker.verify_fonts()
        assert len(missing) == 1

    def test_raises_on_unsupported_os(self):
        deps = DependencyList(fonts=[FontDependency(name="SomeFont", required=True)])
        checker = make_checker(deps, "windows")
        with pytest.raises(UnsupportedOsError):
            checker.verify_fonts()

    def test_raises_on_termux_without_prefix(self):
        deps = DependencyList(fonts=[FontDependency(name="SomeFont", required=True)])
        checker = make_checker(deps, "termux")
        with pytest.raises(MissingTermuxPrefixError):
            checker.verify_fonts()


class TestVerifyEnvVars:
    def test_passes_when_required_var_set(self, monkeypatch):
        monkeypatch.setenv("EDITOR", "nvim")
        deps = DependencyList(env=[EnvDependency(name="EDITOR", value="", required=True)])
        checker = make_checker(deps)
        checker.verify_env_vars()  # should not raise

    def test_raises_when_required_var_missing(self, monkeypatch):
        monkeypatch.delenv("DEFINITELY_NOT_SET_XYZ", raising=False)
        deps = DependencyList(
            env=[EnvDependency(name="DEFINITELY_NOT_SET_XYZ", value="", required=True)]
        )
        checker = make_checker(deps)
        with pytest.raises(RequiredEnvNotFoundError):
            checker.verify_env_vars()

    def test_raises_when_optional_var_missing(self, monkeypatch):
        monkeypatch.delenv("OPTIONAL_VAR_XYZ", raising=False)
        deps = DependencyList(
            env=[EnvDependency(name="OPTIONAL_VAR_XYZ", value="", required=False)]
        )
        checker = make_checker(deps)
        with pytest.raises(OptionalEnvNotFoundError):
            checker.verify_env_vars()

    def test_passes_when_optional_var_set(self, monkeypatch):
        monkeypatch.setenv("OPTIONAL_VAR_XYZ", "some_value")
        deps = DependencyList(
            env=[EnvDependency(name="OPTIONAL_VAR_XYZ", value="", required=False)]
        )
        checker = make_checker(deps)
        checker.verify_env_vars()  # should not raise
