from pathlib import Path
from packaging import version
from packaging.version import Version
from src.build_classes import BuildFile, InstallEntry
from src.exceptions import NoInstallationError, VersionCheckerError
from src.component.checkers.version_checker import VersionChecker, VersionStatus
import shutil
from typing import Literal
import json
import logging
import subprocess
import os

logger = logging.getLogger(__file__)

# Canonical OS strings used throughout Origami.
# All OS values are normalized to one of these at the boundary (Component.__init__,
# OrigamiConfig._get_operating_system) and should never need re-normalization inside
# lower-level classes.
SUPPORTED_OS = frozenset({"linux", "darwin", "termux"})


class Installer:
    def __init__(
        self,
        build_config: BuildFile,
        origami_config: Path,
        operating_system: str,
        theme: str,
        var_substitutions: dict[str, str] | None = None,
    ) -> None:
        self.build_config = build_config
        self.operating_system = operating_system.lower()
        self.origami_config = origami_config
        self.theme = theme
        self.var_substitutions = var_substitutions

    def get_old_version(self, receipt_path: Path) -> str:
        try:
            with open(receipt_path, "r") as f:
                build_json = json.load(f)
        except json.JSONDecodeError:
            raise
        except KeyError:
            raise
        return build_json["version"]

    def get_install_objects(self) -> list[InstallEntry]:
        installations = []
        if self.build_config.install:
            install = self.build_config.install
            if install.linux and self.operating_system == "linux":
                installations.extend(install.linux)
            if install.macos and self.operating_system == "darwin":
                installations.extend(install.macos)
            if install.termux and self.operating_system == "termux":
                installations.extend(install.termux)
        if installations:
            return installations
        raise NoInstallationError(self.build_config.path)

    def install_target(self) -> str | None:
        install = getattr(self.build_config.install, self.operating_system, None)
        return install.target if install else None

    def create_install_receipt(self, receipt_path: Path, ver: Version) -> None:
        """Write the install receipt JSON to receipt_path directly.

        receipt_path is expected to be the full path to the .json file, e.g.:
            ~/.config/origami/installations/<theme>/<component>/install_receipt.json
        The version is stored inside the JSON payload, not as part of the path.
        """
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(self.build_config.raw_json)
        payload["version"] = str(ver)
        with open(receipt_path, "w") as f:
            json.dump(payload, f, indent=2)

    def backup_config(self, path: Path) -> None:
        backup_dir = (
            self.origami_config
            / "backups"
            / "themes"
            / self.theme
            / self.build_config.name
        )
        if path.is_dir():
            shutil.copytree(path, backup_dir, dirs_exist_ok=True)
        else:
            backup_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_dir)

    def _run_hook(self, hook_command: str, stage: str) -> None:
        if not hook_command:
            return
        logger.info(f"Running {stage} hook: {hook_command}")
        try:
            subprocess.run(hook_command, shell=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Hook '{stage}' failed with exit code {e.returncode}")

    def _hardlink_tree(self, source: Path, target: Path) -> None:
        """Recursively recreate source's directory tree at target,
        creating hard links for every file.

        Hard links cannot span directories, only files — so we walk the source
        tree, mirror each subdirectory at the target, and os.link() each file.
        """
        target.mkdir(parents=True, exist_ok=True)
        for item in source.rglob("*"):
            relative = item.relative_to(source)
            dest = target / relative
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            elif item.is_file():
                if dest.exists() or dest.is_symlink():
                    dest.unlink()
                os.link(item, dest)
                logger.debug(f"Hard linked {item} -> {dest}")

    def _install_symlink(self, source_path: Path, target_path: Path) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(source_path, target_is_directory=source_path.is_dir())
        logger.info(f"Symlinked {source_path} -> {target_path}")

    def _install_hardlink(self, source_path: Path, target_path: Path) -> None:
        if source_path.is_dir():
            self._hardlink_tree(source_path, target_path)
            logger.info(f"Hard linked tree {source_path} -> {target_path}")
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            os.link(source_path, target_path)
            logger.info(f"Hard linked {source_path} -> {target_path}")

    def _clear_target(self, target_path: Path) -> None:
        """Remove whatever is currently at target_path, backing up non-symlinks."""
        if target_path.is_symlink():
            target_path.unlink()
        elif target_path.exists():
            self.backup_config(target_path)
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()

    def apply_component(self, installation: InstallEntry) -> None:
        install_receipt_path = (
            self.origami_config
            / "installations"
            / self.theme
            / self.build_config.name
            / "install_receipt.json"
        )

        first_install = not install_receipt_path.exists()

        if not first_install:
            version_checker = VersionChecker(
                installation,
                version.parse(self.build_config.version),
                version.parse(self.get_old_version(install_receipt_path)),
            )
            status = version_checker.check_version()

            if status == "upgrade":
                logger.info(f"Upgrading {self.build_config.name}...")
            elif status == "downgrade":
                logger.info(f"Downgrading {self.build_config.name}...")
            elif status == "reinstall":
                logger.info(f"Reinstalling {self.build_config.name}...")
            else:
                raise VersionCheckerError(
                    f"Unexpected version status for {self.build_config.name}"
                )

        # PRE-INSTALL HOOK
        if self.build_config.hooks and self.build_config.hooks.pre_install:
            for hook in self.build_config.hooks.pre_install:
                self._run_hook(hook, "pre-install")

        source_path = Path(installation.source).expanduser()
        target_path = Path(installation.target).expanduser()

        if not source_path.exists():
            raise FileNotFoundError(f"Source {source_path} does not exist.")

        self._clear_target(target_path)

        try:
            install_type = installation.type.lower()
            if install_type == "hardlink":
                self._install_hardlink(source_path, target_path)
            else:
                # "symlink", "auto", or unrecognized — fall back to symlink
                self._install_symlink(source_path, target_path)

            self.create_install_receipt(
                install_receipt_path, version.parse(self.build_config.version)
            )
        except PermissionError:
            logger.error(
                f"Permission denied on {target_path}. Try running with higher "
                "privileges or check macOS Full Disk Access."
            )
            raise
        except OSError:
            raise
        except Exception as e:
            logger.error(f"Other Exception: {e}")
            raise

        # POST-INSTALL HOOK
        if self.build_config.hooks and self.build_config.hooks.post_install:
            for hook in self.build_config.hooks.post_install:
                self._run_hook(hook, "post-install")
