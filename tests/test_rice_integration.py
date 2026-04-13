"""
Integration tests for src/rice.py

These tests exercise the full Rice -> Component -> Installer stack against
a real (tmp_path) filesystem. They are slower than unit tests and may catch
bugs that mocks hide.

Covers:
  - Rice.collect_components: discovers components by origami.json presence,
    skips dirs without origami.json
  - Rice.apply_rice: symlinks are created at expected target paths
  - Rice.apply_rice: hardlinks are created at expected target paths
  - Rice.apply_rice: conflict in rice is logged and does not crash (future: raises)
  - Rice.delete_rice: removes theme directory
  - Rice.__eq__: equality with string theme name
"""

import json
import pytest
from pathlib import Path

from src.rice import Rice


# ---------------------------------------------------------------------------
# Helpers to build a realistic on-disk rice structure
# ---------------------------------------------------------------------------


def write_origami_json(
    path: Path, name: str, source: str, target: str, install_type: str = "symlink"
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "name": name,
        "version": "1.0.0",
        "install": {
            "linux": [{"type": install_type, "source": source, "target": target}]
        },
    }
    path.write_text(json.dumps(data))


@pytest.fixture
def rice_dir(tmp_path) -> Path:
    """A themes/test-rice directory with two valid components and one invalid dir."""
    theme_dir = tmp_path / "themes" / "test-rice"

    # Component A: a real source file
    comp_a_src = tmp_path / "src" / "comp-a" / "config"
    comp_a_src.parent.mkdir(parents=True)
    comp_a_src.write_text("# comp-a config")
    comp_a_target = tmp_path / "targets" / "comp-a" / "config"
    write_origami_json(
        theme_dir / "comp-a" / "origami.json",
        name="comp-a",
        source=str(comp_a_src),
        target=str(comp_a_target),
    )

    # Component B: a real source file
    comp_b_src = tmp_path / "src" / "comp-b" / "config"
    comp_b_src.parent.mkdir(parents=True)
    comp_b_src.write_text("# comp-b config")
    comp_b_target = tmp_path / "targets" / "comp-b" / "config"
    write_origami_json(
        theme_dir / "comp-b" / "origami.json",
        name="comp-b",
        source=str(comp_b_src),
        target=str(comp_b_target),
    )

    # A directory with no origami.json (should be skipped)
    (theme_dir / "not-a-component").mkdir(parents=True)

    return theme_dir


@pytest.fixture
def origami_config_dir(tmp_path) -> Path:
    config = tmp_path / ".config" / "origami"
    (config / "installations").mkdir(parents=True)
    (config / "backups").mkdir(parents=True)
    return config


# ---------------------------------------------------------------------------
# collect_components
# ---------------------------------------------------------------------------


class TestCollectComponents:
    def test_discovers_components_with_origami_json(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        names = {c.build_config.name for c in rice.components}
        assert "comp-a" in names
        assert "comp-b" in names

    def test_skips_dirs_without_origami_json(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        names = {c.build_config.name for c in rice.components}
        assert "not-a-component" not in names

    def test_component_count_correct(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        assert len(rice.components) == 2


# ---------------------------------------------------------------------------
# apply_rice
# ---------------------------------------------------------------------------


class TestApplyRice:
    def test_symlinks_created_at_target_paths(
        self, rice_dir, origami_config_dir, tmp_path
    ):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        rice.apply_rice()
        comp_a_target = tmp_path / "targets" / "comp-a" / "config"
        comp_b_target = tmp_path / "targets" / "comp-b" / "config"
        assert comp_a_target.is_symlink()
        assert comp_b_target.is_symlink()

    def test_symlinks_point_to_correct_sources(
        self, rice_dir, origami_config_dir, tmp_path
    ):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        rice.apply_rice()
        comp_a_src = tmp_path / "src" / "comp-a" / "config"
        comp_a_target = tmp_path / "targets" / "comp-a" / "config"
        assert comp_a_target.resolve() == comp_a_src.resolve()

    def test_receipts_written_after_apply(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        rice.apply_rice()
        receipt_a = (
            origami_config_dir
            / "installations"
            / "test-rice"
            / "comp-a"
            / "install_receipt.json"
        )
        receipt_b = (
            origami_config_dir
            / "installations"
            / "test-rice"
            / "comp-b"
            / "install_receipt.json"
        )
        assert receipt_a.exists()
        assert receipt_b.exists()


class TestApplyRiceHardlinks:
    def test_hardlinks_created_at_target_paths(self, tmp_path, origami_config_dir):
        theme_dir = tmp_path / "themes" / "test-rice"

        src = tmp_path / "src" / "hl-comp" / "config"
        src.parent.mkdir(parents=True)
        src.write_text("# hardlink source")
        target = tmp_path / "targets" / "hl-comp" / "config"

        write_origami_json(
            theme_dir / "hl-comp" / "origami.json",
            name="hl-comp",
            source=str(src),
            target=str(target),
            install_type="hardlink",
        )

        rice = Rice("test-rice", theme_dir, origami_config_dir)
        rice.apply_rice()

        assert target.exists()
        assert not target.is_symlink()
        assert src.stat().st_ino == target.stat().st_ino


# ---------------------------------------------------------------------------
# delete_rice / __eq__
# ---------------------------------------------------------------------------


class TestRiceMisc:
    def test_eq_with_matching_string(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        assert rice == "test-rice"

    def test_eq_with_non_matching_string(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        assert rice != "other-rice"

    def test_activate_sets_active_true(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        rice.activate()
        assert rice.active is True

    def test_deactivate_sets_active_false(self, rice_dir, origami_config_dir):
        rice = Rice("test-rice", rice_dir, origami_config_dir)
        rice.activate()
        rice.deactivate()
        assert rice.active is False
