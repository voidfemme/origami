from pathlib import Path
import shutil
from src.rice import Rice
from src.exceptions import RiceNotExistsError, MissingConfigKeyError
import logging
import platform
import tomllib
import os

logger = logging.getLogger(__name__)


class OrigamiConfig:
    def __init__(
        self, origami_config_dir: Path, operating_system: str | None = None
    ) -> None:
        self.origami_config_dir = origami_config_dir
        self.operating_system = self._get_operating_system(operating_system)
        self.global_config_file = origami_config_dir / "config.toml"
        self.user_preferences = self._get_prefs_from_toml(self.global_config_file)
        try:
            self.theme = self.user_preferences["theme"]
            self.default_os = self.user_preferences["defaults"]["os"]
            self.config_dir = self.user_preferences["config_dir"]
        except KeyError as e:
            logger.error(f"Could not retrieve key(s) from origami.toml: {e}")
            raise MissingConfigKeyError
        self.rices = self._get_available_rices()

    def _get_operating_system(self, operating_system: str | None) -> str:
        if not operating_system:
            if platform.system().lower() == "darwin":
                return "macos"
            else:
                return platform.system()
        else:
            return operating_system.lower()

    def _get_prefs_from_toml(self, config_path: Path) -> dict:
        config: dict[str, str] = {}
        try:
            with open(config_path, "rb") as f:  # note: binary mode required
                config = tomllib.load(f)
        except FileNotFoundError as e:
            logger.error(
                f"Could not locate Origami configuration file at {config_path}\n{e}"
            )
            raise
        except tomllib.TOMLDecodeError as e:
            logger.error(
                f"Could not decode TOML at {config_path}. Please check for errors.\n{e}"
            )
            raise

        return config

    def _get_available_rices(self) -> dict[str, Rice]:
        available_rice_dirs = []
        try:
            available_rice_dirs = os.listdir(self.origami_config_dir / "themes")
        except FileNotFoundError:
            os.mkdir(self.origami_config_dir / "themes")

        rices: dict[str, Rice] = {}
        for dir in available_rice_dirs:
            theme_path = self.origami_config_dir / "themes" / dir
            rice = Rice(dir, theme_path, self.origami_config_dir)
            rices[dir] = rice
        return rices

    def get_themes(self) -> list[str]:
        return list(self.rices.keys())

    @classmethod
    def from_default(cls) -> OrigamiConfig:
        return OrigamiConfig(origami_config_dir=Path("~/.config/origami"))

    def apply_rice(self, rice_name: str) -> None:
        self.get_rice(rice_name).apply_rice()

    def get_rice(self, rice_name: str) -> Rice:
        if rice_name not in self.rices:
            raise RiceNotExistsError(rice_name)
        return self.rices[rice_name]
