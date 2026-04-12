from src.build_classes import InstallEntry
from typing import Literal
from packaging.version import Version
import logging

logger = logging.getLogger(__file__)
VersionStatus = Literal["upgrade", "downgrade", "reinstall", "error"]


class VersionChecker:
    def __init__(
        self, installation: InstallEntry, new_version: Version, old_version: Version
    ) -> None:
        self.installation = installation
        self.new_version = new_version
        self.old_version = old_version

    def check_version(self) -> VersionStatus:
        if self.new_version > self.old_version:
            # Upgrading
            logger.info(
                f"Upgrading: {self.installation.type} in {self.installation.target} from {self.installation.source}"
            )
            return "upgrade"
        elif self.old_version > self.new_version:
            # Downgrading
            logger.info(
                f"Downgrading: {self.installation.type} in {self.installation.target} from {self.installation.source}"
            )
            return "downgrade"
        elif self.new_version == self.old_version:
            return "reinstall"
        else:
            return "error"
