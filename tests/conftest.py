"""
Shared pytest fixtures for Origami tests.

Fixture strategy:
  - Static files in tests/fixtures/ are used for BuildLoader/schema validation
    tests, where realistic on-disk JSON/TOML matters.
  - tmp_path is used for anything that writes to the filesystem at runtime
    (symlinks, hardlinks, receipts, backups, font installation).
"""

import json
import pytest
from pathlib import Path

from src.build_classes import (
    BuildFile,
    InstallEntry,
    InstallList,
    DependencyList,
    ProgramDependency,
    FontDependency,
    ConfigDependency,
    EnvDependency,
    RepoUpstream,
    InstallHooks,
)

# ---------------------------------------------------------------------------
# Paths to static fixture files
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def minimal_json_path() -> Path:
    return FIXTURES_DIR / "origami_minimal.json"


@pytest.fixture
def full_json_path() -> Path:
    return FIXTURES_DIR / "origami_full.json"


@pytest.fixture
def hardlink_json_path() -> Path:
    return FIXTURES_DIR / "origami_hardlink.json"


@pytest.fixture
def invalid_json_path() -> Path:
    return FIXTURES_DIR / "origami_invalid_missing_required.json"


@pytest.fixture
def malformed_json_path() -> Path:
    return FIXTURES_DIR / "origami_malformed.json"


@pytest.fixture
def config_toml_path() -> Path:
    return FIXTURES_DIR / "config.toml"


# ---------------------------------------------------------------------------
# In-memory BuildFile factories
# These avoid hitting disk and are faster for unit tests.
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_install_entry() -> InstallEntry:
    return InstallEntry(type="symlink", source="/src/config", target="/target/config")


@pytest.fixture
def hardlink_install_entry() -> InstallEntry:
    return InstallEntry(type="hardlink", source="/src/config", target="/target/config")


@pytest.fixture
def minimal_build_file(tmp_path) -> BuildFile:
    fake_path = tmp_path / "origami.json"
    return BuildFile(
        path=fake_path,
        name="test-component",
        description=None,
        version="1.0.0",
        install=InstallList(
            linux=[
                InstallEntry(
                    type="hardlink", source="src/config", target="target/config"
                )
            ]
        ),
        deps=None,
        upstream=None,
        hooks=None,
        notes=None,
        raw_json={"name": "test-component", "version": "1.0.0"},
    )


@pytest.fixture
def full_build_file(tmp_path) -> BuildFile:
    fake_path = tmp_path / "origami.json"
    return BuildFile(
        path=fake_path,
        name="test-component-full",
        description="Full test component",
        version="2.1.0",
        install=InstallList(
            linux=[
                InstallEntry(
                    type="hardlink", source="src/config", target="target/config"
                )
            ],
            macos=[
                InstallEntry(
                    type="hardlink", source="src/config", target="target/config"
                )
            ],
        ),
        deps=DependencyList(
            programs=[
                ProgramDependency(name="git", version=">=2.0.0", required=True),
                ProgramDependency(name="fzf", version=None, required=False),
            ],
            fonts=[FontDependency(name="JetBrainsMono", required=True)],
            configs=[
                ConfigDependency(
                    name="nvim", path=Path("~/.config/nvim"), required=True
                )
            ],
            env=[
                EnvDependency(name="EDITOR", value="", required=True),
                EnvDependency(name="OPTIONAL_VAR", value="", required=False),
            ],
        ),
        upstream=RepoUpstream(
            repo="voidfemme/test-component-full",
            branch="main",
            commit=None,
            provider="github",
        ),
        hooks=InstallHooks(
            pre_install=["echo pre-install"],
            post_install=["echo post-install"],
        ),
        notes="Full test fixture",
        raw_json={"name": "test-component-full", "version": "2.1.0"},
    )


# ---------------------------------------------------------------------------
# Filesystem helpers (tmp_path-based)
# These set up realistic on-disk states for installer/symlink/hardlink tests.
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_origami_dir(tmp_path) -> Path:
    """A minimal origami config directory structure under tmp_path."""
    origami = tmp_path / ".config" / "origami"
    (origami / "themes").mkdir(parents=True)
    (origami / "installations").mkdir(parents=True)
    (origami / "backups").mkdir(parents=True)
    (origami / "scripts").mkdir(parents=True)
    return origami


@pytest.fixture
def fake_source_file(tmp_path) -> Path:
    """A real file to use as an install source."""
    src = tmp_path / "source" / "config"
    src.parent.mkdir(parents=True)
    src.write_text("# test config content")
    return src


@pytest.fixture
def fake_source_dir(tmp_path) -> Path:
    """A real directory tree to use as an install source."""
    src = tmp_path / "source" / "config_dir"
    src.mkdir(parents=True)
    (src / "init.lua").write_text("-- neovim config")
    (src / "subdir").mkdir()
    (src / "subdir" / "plugin.lua").write_text("-- plugin config")
    return src


@pytest.fixture
def fake_target_path(tmp_path) -> Path:
    """A target path that does not yet exist."""
    return tmp_path / "target" / "config"


@pytest.fixture
def fake_target_path_with_existing_file(tmp_path) -> Path:
    """A target path where a real (non-symlink) file already exists."""
    target = tmp_path / "target" / "config"
    target.parent.mkdir(parents=True)
    target.write_text("# existing config that should be backed up")
    return target


@pytest.fixture
def fake_target_path_with_existing_symlink(tmp_path, fake_source_file) -> Path:
    """A target path where a symlink already exists (pointing somewhere)."""
    target = tmp_path / "target" / "config"
    target.parent.mkdir(parents=True)
    target.symlink_to(fake_source_file)
    return target


@pytest.fixture
def fake_install_receipt(tmp_path) -> Path:
    """An existing install receipt JSON."""
    receipt = (
        tmp_path
        / "installations"
        / "test-rice"
        / "test-component"
        / "install_receipt.json"
    )
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({"name": "test-component", "version": "1.0.0"}))
    return receipt
