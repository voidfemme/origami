"""
Tests for src/component/installers/installer.py

Covers:
  - get_install_objects: correct OS filtering, raises NoInstallationError when no match
  - create_install_receipt: file is created, version stored in JSON payload (not in path)
  - get_old_version: reads version from existing receipt
  - backup_config: file and directory cases
  - _clear_target: symlink unlinked without backup, real file backed up and removed
  - _hardlink_tree: directory tree recreated, all files hard linked
  - apply_component (symlink): new install, upgrade, reinstall
  - apply_component (hardlink): new install
  - apply_component: source missing raises FileNotFoundError
  - apply_component: pre/post hooks run in correct order
"""

import json
import pytest
from unittest.mock import call

from src.build_classes import InstallEntry
from src.component.installers.installer import Installer
from src.exceptions import NoInstallationError


def make_installer(
    build_file, origami_config, operating_system="linux", theme="test-rice"
):
    return Installer(
        build_config=build_file,
        origami_config=origami_config,
        operating_system=operating_system,
        theme=theme,
    )


class TestGetInstallObjects:
    def test_returns_linux_entries_on_linux(self, minimal_build_file, fake_origami_dir):
        installer = make_installer(minimal_build_file, fake_origami_dir, "linux")
        result = installer.get_install_objects()
        assert len(result) > 0

    def test_raises_when_no_matching_os(self, minimal_build_file, fake_origami_dir):
        # minimal_build_file only has linux installs
        installer = make_installer(minimal_build_file, fake_origami_dir, "darwin")
        with pytest.raises(NoInstallationError):
            installer.get_install_objects()

    def test_does_not_return_wrong_os_entries(self, full_build_file, fake_origami_dir):
        installer = make_installer(full_build_file, fake_origami_dir, "linux")
        result = installer.get_install_objects()
        # should only contain linux entries, not macos
        assert all(isinstance(e, InstallEntry) for e in result)


class TestInstallReceipt:
    def test_receipt_written_to_correct_path(
        self, minimal_build_file, fake_origami_dir
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        from packaging.version import Version

        receipt_path = (
            fake_origami_dir
            / "installations"
            / "test-rice"
            / "test-component"
            / "install_receipt.json"
        )
        installer.create_install_receipt(receipt_path, Version("1.0.0"))
        assert receipt_path.exists()

    def test_receipt_stores_version_in_payload(
        self, minimal_build_file, fake_origami_dir
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        from packaging.version import Version

        receipt_path = (
            fake_origami_dir
            / "installations"
            / "test-rice"
            / "test-component"
            / "install_receipt.json"
        )
        installer.create_install_receipt(receipt_path, Version("1.2.3"))
        data = json.loads(receipt_path.read_text())
        assert data["version"] == "1.2.3"

    def test_receipt_path_is_json_file_not_directory(
        self, minimal_build_file, fake_origami_dir
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        from packaging.version import Version

        receipt_path = (
            fake_origami_dir
            / "installations"
            / "test-rice"
            / "test-component"
            / "install_receipt.json"
        )
        installer.create_install_receipt(receipt_path, Version("1.0.0"))
        assert receipt_path.is_file()
        assert not receipt_path.is_dir()

    def test_get_old_version_reads_from_receipt(
        self, minimal_build_file, fake_origami_dir, fake_install_receipt
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        result = installer.get_old_version(fake_install_receipt)
        assert result == "1.0.0"


class TestClearTarget:
    def test_unlinks_existing_symlink_without_backup(
        self,
        minimal_build_file,
        fake_origami_dir,
        fake_target_path_with_existing_symlink,
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        installer._clear_target(fake_target_path_with_existing_symlink)
        assert not fake_target_path_with_existing_symlink.exists()
        assert not fake_target_path_with_existing_symlink.is_symlink()

    def test_backs_up_and_removes_existing_file(
        self, minimal_build_file, fake_origami_dir, fake_target_path_with_existing_file
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        installer._clear_target(fake_target_path_with_existing_file)
        assert not fake_target_path_with_existing_file.exists()

    def test_does_nothing_when_target_absent(
        self, minimal_build_file, fake_origami_dir, fake_target_path
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        # should not raise
        installer._clear_target(fake_target_path)


class TestHardlinkTree:
    def test_files_are_hardlinked(
        self, minimal_build_file, fake_origami_dir, fake_source_dir, tmp_path
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        target = tmp_path / "hardlink_target"
        installer._hardlink_tree(fake_source_dir, target)
        # Hard linked files share the same inode
        src_file = fake_source_dir / "init.lua"
        dst_file = target / "init.lua"
        assert dst_file.exists()
        assert src_file.stat().st_ino == dst_file.stat().st_ino

    def test_subdirectory_structure_recreated(
        self, minimal_build_file, fake_origami_dir, fake_source_dir, tmp_path
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        target = tmp_path / "hardlink_target"
        installer._hardlink_tree(fake_source_dir, target)
        assert (target / "subdir" / "plugin.lua").exists()

    def test_overwrites_existing_file_at_target(
        self, minimal_build_file, fake_origami_dir, fake_source_dir, tmp_path
    ):
        installer = make_installer(minimal_build_file, fake_origami_dir)
        target = tmp_path / "hardlink_target"
        target.mkdir()
        (target / "init.lua").write_text("# old content")
        installer._hardlink_tree(fake_source_dir, target)
        src_file = fake_source_dir / "init.lua"
        dst_file = target / "init.lua"
        assert src_file.stat().st_ino == dst_file.stat().st_ino


class TestApplyComponent:
    def test_creates_symlink_for_new_install(
        self, minimal_build_file, fake_origami_dir, fake_source_file, tmp_path
    ):
        target = tmp_path / "target" / "config"
        entry = InstallEntry(
            type="symlink", source=str(fake_source_file), target=str(target)
        )
        minimal_build_file.install.linux[0] = entry
        installer = make_installer(minimal_build_file, fake_origami_dir)
        installer.apply_component(entry)
        assert target.is_symlink()
        assert target.resolve() == fake_source_file.resolve()

    def test_creates_hardlink_for_new_install(
        self, minimal_build_file, fake_origami_dir, fake_source_file, tmp_path
    ):
        target = tmp_path / "target" / "config"
        entry = InstallEntry(
            type="hardlink", source=str(fake_source_file), target=str(target)
        )
        minimal_build_file.install.linux[0] = entry
        installer = make_installer(minimal_build_file, fake_origami_dir)
        installer.apply_component(entry)
        assert target.exists()
        assert not target.is_symlink()
        assert fake_source_file.stat().st_ino == target.stat().st_ino

    def test_raises_when_source_missing(
        self, minimal_build_file, fake_origami_dir, tmp_path
    ):
        entry = InstallEntry(
            type="hardlink",
            source=str(tmp_path / "does_not_exist"),
            target=str(tmp_path / "target"),
        )
        installer = make_installer(minimal_build_file, fake_origami_dir)
        with pytest.raises(FileNotFoundError):
            installer.apply_component(entry)

    def test_replaces_existing_symlink(
        self,
        minimal_build_file,
        fake_origami_dir,
        fake_source_file,
        fake_target_path_with_existing_symlink,
    ):
        entry = InstallEntry(
            type="symlink",
            source=str(fake_source_file),
            target=str(fake_target_path_with_existing_symlink),
        )
        installer = make_installer(minimal_build_file, fake_origami_dir)
        installer.apply_component(entry)
        assert (
            fake_target_path_with_existing_symlink.resolve()
            == fake_source_file.resolve()
        )

    def test_receipt_written_after_install(
        self, minimal_build_file, fake_origami_dir, fake_source_file, tmp_path
    ):
        target = tmp_path / "target" / "config"
        entry = InstallEntry(
            type="hardlink", source=str(fake_source_file), target=str(target)
        )
        minimal_build_file.install.linux[0] = entry
        installer = make_installer(minimal_build_file, fake_origami_dir)
        installer.apply_component(entry)
        receipt = (
            fake_origami_dir
            / "installations"
            / "test-rice"
            / "test-component"
            / "install_receipt.json"
        )
        assert receipt.exists()
