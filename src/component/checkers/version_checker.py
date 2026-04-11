from src.build_classes import SymlinkOp
from packaging.version import Version
import logging

logger = logging.getLogger(__file__)


class VersionChecker:
    def __init__(self, installation: SymlinkOp, v1: Version, v2: Version) -> None:
        self.installation = installation
        self.v1 = v1
        self.v2 = v2

    def check_version(self) -> bool:  # I'm not confident about this function name
        if self.v1 > self.v2:
            # Upgrading
            logger.info(
                f"Upgrading: {self.installation.type} in {self.installation.target} from {self.installation.source}"
            )
            return True
        elif self.v2 > self.v1:
            # Downgrading
            print(
                f"Downgrading: {self.installation.type} in {self.installation.target} from {self.installation.source}"
            )
            downgrade_response = print("Are you sure you want to downgrade? (y/n): ")
            if str(downgrade_response).lower() != "y":
                print("Aborting this installation...")
                return False
            else:
                return True
        elif self.v1 == self.v2:
            reinstall_response = print(
                f"{self.installation.source} v{self.v1} is already up-to-date. Are you sure you want to re-install? (y/n): "
            )
            if str(reinstall_response) != "y":
                print("Aborting this installation...")
                return False
            else:
                return True
        else:
            return False
