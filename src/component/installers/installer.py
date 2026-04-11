from pathlib import Path
from packaging import version
from packaging.version import Version
from src.build_classes import BuildFile, SymlinkOp
from src.exceptions import NoInstallationError
from src.component.checkers.version_checker import VersionChecker
import shutil
import json
import logging
import subprocess

logger = logging.getLogger(__file__)


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
        with open(receipt_path, "r") as f:
            build_json = json.load(f)
        return build_json["version"]

    def get_install_objects(self) -> list[SymlinkOp]:
        installations = []
        if self.build_config.install:
            install = self.build_config.install
            if install.linux:
                for item in install.linux:
                    installations.append(item)
            if install.macos:
                for item in install.macos:
                    installations.append(item)
            if install.termux:
                for item in install.termux:
                    installations.append(item)
        if len(installations) > 0:
            return installations
        else:
            raise NoInstallationError(self.build_config.path)

    def install_target(self) -> str | None:
        install = getattr(self.build_config.install, self.operating_system, None)
        return install.target if install else None

    def create_install_receipt(self, receipt_path: Path, version: Version) -> None:
        versioned_path = receipt_path / str(version)
        versioned_path.parent.mkdir(parents=True, exist_ok=True)
        with open(versioned_path, "w") as f:
            json.dump(self.build_config.raw_json, f)

    def backup_config(self, path: Path):
        backup_dir = (
            self.origami_config
            / "backups"
            / "themes"
            / self.theme
            / self.build_config.name
        )

        if path.is_dir():
            # dirs_exist_ok=True is useful in case a previous backup exists
            shutil.copytree(path, backup_dir, dirs_exist_ok=True)
        else:
            # Ensure the parent backup folder exists first
            backup_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_dir)

    def _run_hook(self, hook_command: str, stage: str) -> None:
        if not hook_command:
            return

        logger.info(f"Running {stage} hook: {hook_command}")
        try:
            # shell=True allows for pipes, redirects, and environment variables
            # check=True raises an exception if the command fails
            subprocess.run(hook_command, shell=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Hook '{stage}' failed with exit code {e.returncode}")

    def apply_component(self, installation: SymlinkOp) -> None:
        install_receipt_path = (
            self.origami_config
            / "installations"
            / self.theme
            / self.build_config.name
            / self.build_config.name
        )

        version_checker = VersionChecker(
            installation,
            version.parse(self.build_config.version),
            version.parse(self.get_old_version(install_receipt_path)),
        )

        if not version_checker.check_version():
            return

        # PRE-INSTALL HOOK
        if self.build_config.hooks:
            if self.build_config.hooks.pre_install:
                for hook in self.build_config.hooks.pre_install:
                    self._run_hook(hook, "pre-install")

        source_path = Path(installation.source)
        target_path = Path(installation.target)
        if not source_path.exists():
            raise FileNotFoundError(f"Source {source_path} does not exist.")

        if target_path.exists():
            if target_path.is_symlink():
                target_path.unlink()
            else:
                self.backup_config(target_path)
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()

        # 2. Create the Symlink
        try:
            # Ensure the parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # The actual link creation
            target_path.symlink_to(
                source_path, target_is_directory=source_path.is_dir()
            )

            # Create and store the installation receipt
            self.create_install_receipt(install_receipt_path, version_checker.v1)

            # POST-INSTALL HOOK
            if self.build_config.hooks:
                if self.build_config.hooks.post_install:
                    for hook in self.build_config.hooks.post_install:
                        self._run_hook(hook, "post-install")
            logger.info(f"Successfully linked {source_path} -> {target_path}")
        except PermissionError:
            logger.error(
                f"Permission denied on {target_path}. Try running with higher privileges or check macOS Full Disk Access."
            )
