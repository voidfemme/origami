from pathlib import Path
from src.rice import Rice
from src.exceptions import RiceNotExistsError, MissingConfigKeyError
import logging
import platform
import tomllib
import os

logger = logging.getLogger(__name__)


def normalize_os(operating_system: str) -> str:
    """Canonical OS normalization for the top-level config layer.
    Returns: linux | darwin | termux
    """
    os_str = operating_system.lower()
    if os_str == "macos":
        return "darwin"
    return os_str


class OrigamiConfig:
    def __init__(
        self,
        origami_config_dir: Path,
        operating_system: str | None = None,
    ) -> None:
        self.origami_config_dir = origami_config_dir
        self.operating_system = self._get_operating_system(operating_system)
        self.global_config_file = origami_config_dir / "config.toml"
        self.user_preferences = self._get_prefs_from_toml(self.global_config_file)
        try:
            self.theme = self.user_preferences["theme"]
            self.default_os = self.user_preferences["defaults"]["os"]
            self.config_dir = self.user_preferences["config_dir"]
            self.scripts_dir = Path(self.user_preferences["scripts_dir"]).expanduser()
            self.themes_dir = Path(self.user_preferences["themes_dir"]).expanduser()
        except KeyError as e:
            logger.error(f"Could not retrieve key(s) from origami.toml: {e}")
            raise MissingConfigKeyError
        self.rices = self.get_available_rices()

    def _get_operating_system(self, operating_system: str | None) -> str:
        if not operating_system:
            return normalize_os(platform.system())
        return normalize_os(operating_system)

    def _get_prefs_from_toml(self, config_path: Path) -> dict:
        config: dict = {}
        try:
            with open(config_path, "rb") as f:
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

    def get_available_rices(self) -> dict[str, Rice]:
        available_rice_dirs = []
        try:
            available_rice_dirs = os.listdir(self.themes_dir)
        except FileNotFoundError:
            os.mkdir(self.themes_dir)

        rices: dict[str, Rice] = {}
        for dir in available_rice_dirs:
            theme_path = self.themes_dir / dir
            rice = Rice(dir, theme_path, self.origami_config_dir)
            rices[dir] = rice
        return rices

    def get_themes(self) -> list[str]:
        return list(self.rices.keys())

    @classmethod
    def from_default(cls) -> "OrigamiConfig":
        return OrigamiConfig(origami_config_dir=Path("~/.config/origami").expanduser())

    def apply_rice(self, rice_name: str) -> None:
        self.get_rice(rice_name).apply_rice()
        self.rices[rice_name].activate()

    def delete_rice(self, rice_name: str) -> None:
        self.rices[rice_name].delete_rice()
        self.rices = self.get_available_rices()

    def get_rice(self, rice_name: str) -> Rice:
        if rice_name not in self.rices:
            raise RiceNotExistsError(rice_name)
        return self.rices[rice_name]
