"""
Tests for src/build_loader.py

Covers:
  - Loading and validating valid JSON (minimal and full)
  - Schema validation errors (missing required fields, wrong types)
  - File errors (not found, malformed JSON, is a directory)
  - Dataclass construction (correct field mapping)
  - upstream.provider normalization (should be lowercased)
  - BuildLoader.supported_environments property
  - BuildLoader.get_version()
"""

import pytest
from packaging.version import Version

from src.build_loader import BuildLoader
from src.build_classes import InstallEntry
from jsonschema import ValidationError
import json


class TestBuildLoaderValidFiles:
    def test_loads_minimal_json(self, minimal_json_path):
        build = BuildLoader.from_path(minimal_json_path)
        assert build.name == "test-component"
        assert build.version == "1.0.0"

    def test_loads_full_json(self, full_json_path):
        build = BuildLoader.from_path(full_json_path)
        assert build.name == "test-component-full"
        assert build.description == "A fully-featured test component"
        assert build.upstream is not None
        assert build.hooks is not None
        assert build.deps is not None

    def test_install_entries_parsed(self, minimal_json_path):
        build = BuildLoader.from_path(minimal_json_path)
        assert build.install.linux is not None
        assert isinstance(build.install.linux[0], InstallEntry)

    def test_upstream_provider_normalized_to_lowercase(self, tmp_path):
        data = {
            "name": "x",
            "version": "1.0.0",
            "install": {"linux": [{"type": "symlink", "source": "s", "target": "t"}]},
            "upstream": {"repo": "a/b", "branch": "main", "provider": "GitHub"},
        }
        p = tmp_path / "origami.json"
        p.write_text(json.dumps(data))
        build = BuildLoader.from_path(p)
        assert build.upstream.provider == "github"

    def test_get_version_returns_version_object(self, minimal_json_path):
        loader = BuildLoader(minimal_json_path)
        assert loader.get_version() == Version("1.0.0")

    def test_supported_environments_linux_only(self, minimal_json_path):
        loader = BuildLoader(minimal_json_path)
        assert loader.supported_environments == ["linux"]

    def test_supported_environments_multi_os(self, full_json_path):
        loader = BuildLoader(full_json_path)
        assert set(loader.supported_environments) == {"linux", "macos"}


class TestBuildLoaderFileErrors:
    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            BuildLoader.from_path(tmp_path / "does_not_exist.json")

    def test_raises_on_malformed_json(self, malformed_json_path):
        import json

        with pytest.raises(json.JSONDecodeError):
            BuildLoader.from_path(malformed_json_path)

    def test_raises_on_directory_instead_of_file(self, tmp_path):
        with pytest.raises(IsADirectoryError):
            BuildLoader.from_path(tmp_path)


class TestBuildLoaderSchemaValidation:
    def test_raises_on_missing_required_fields(self, invalid_json_path):
        with pytest.raises(ValidationError):
            BuildLoader.from_path(invalid_json_path)

    def test_raises_on_invalid_version_format(self, tmp_path):
        data = {
            "name": "x",
            "version": "not-a-version",
            "install": {"linux": [{"type": "file", "source": "s", "target": "t"}]},
        }
        p = tmp_path / "origami.json"
        p.write_text(json.dumps(data))
        with pytest.raises(ValidationError):
            BuildLoader.from_path(p)

    def test_raises_on_invalid_provider_value(self, tmp_path):
        data = {
            "name": "x",
            "version": "1.0.0",
            "install": {"linux": [{"type": "file", "source": "s", "target": "t"}]},
            "upstream": {"repo": "a/b", "branch": "main", "provider": "bitbucket"},
        }
        p = tmp_path / "origami.json"
        p.write_text(json.dumps(data))
        with pytest.raises(ValidationError):
            BuildLoader.from_path(p)
