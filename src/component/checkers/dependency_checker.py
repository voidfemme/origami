import logging
from src.build_classes import DependencyList, FontDependency
from src.exceptions import (
    MissingTermuxPrefixError,
    ProgramNotFoundError,
    ConfigNotFoundError,
    PathNotFoundError,
    FontNotFoundError,
    RequiredEnvNotFoundError,
    OptionalEnvNotFoundError,
    UnsupportedOsError,
)
from pathlib import Path
import os
import shutil

logger = logging.getLogger(__name__)


class DependencyChecker:
    def __init__(self, dependencies: DependencyList, operating_system: str) -> None:
        self.dependencies = dependencies
        if operating_system == "macos":
            self.operating_system = "darwin"
        else:
            self.operating_system = operating_system.lower()

    def verify_programs(self) -> None:
        """
        Raises: ProgramNotFoundError
        """
        programs = self.dependencies.programs
        if programs:
            for program in programs:
                if not shutil.which(program.name):
                    raise ProgramNotFoundError

    def verify_configs(self) -> None:
        """
        Raises: ConfigNotFoundError
        """
        configs = self.dependencies.configs
        if configs:
            for config in configs:
                if not os.path.exists(config.path):
                    raise ConfigNotFoundError

    def verify_paths(self) -> None:
        """
        Raises: PathNotFoundError
        """
        # Do the source files exist in `$CORE`?
        paths = self.dependencies.paths
        if paths:
            for path in paths:
                if not os.path.exists(path):
                    raise PathNotFoundError

    def _get_missing_fonts(
        self, fonts: list[FontDependency], font_dirs: list[Path]
    ) -> list[FontDependency]:
        """
        Params:
            fonts: list[FontDependency] (list of fonts to check)
            font_dirs: list[Path] (font directories to check against)
        Returns: list[FontDependency] (a list of fonts from the `fonts` list that are not installed on the system)
        """
        missing_fonts = set()
        found_fonts = set()
        for font in fonts:
            for dir in font_dirs:
                if dir.exists():
                    if any(dir.glob(f"{font.name}*")):
                        print(f"Font {font.name} found in {dir}")
                        found_fonts.add(font)
        for font in fonts:
            if font not in found_fonts:
                missing_fonts.add(font)
        return list(missing_fonts)

    def verify_fonts(self, termux_prefix: Path | None = None) -> list[FontDependency]:
        """
        Params
            termux_prefix: Path or None: (Optional parameter for defining the directory prefix in termux environments)
        Returns
            list[FontDependency]: a list of missing fonts contingent on the target OS
        Raises
            FontNotFoundError
        """
        fonts = self.dependencies.fonts
        if fonts:
            if self.operating_system == "linux":
                linux_font_dirs = [
                    Path.home() / ".local/share/fonts",
                    Path("/usr/share/fonts"),
                    Path("/usr/local/share/fonts"),
                ]
                return self._get_missing_fonts(fonts, linux_font_dirs)
            elif self.operating_system == "termux" and termux_prefix:
                termux_font_dirs = [
                    Path.home() / ".local/share/fonts",
                    termux_prefix / "usr/share/fonts",
                    termux_prefix / "usr/local/share/fonts",
                ]
                return self._get_missing_fonts(fonts, termux_font_dirs)
            elif self.operating_system == "termux" and not termux_prefix:
                raise MissingTermuxPrefixError
            elif self.operating_system == "darwin":
                macos_font_dirs = [
                    Path.home() / "Library/Fonts",
                    Path("/Library/Fonts"),
                    Path("/System/Library/Fonts"),
                ]
                return self._get_missing_fonts(fonts, macos_font_dirs)
            else:
                raise UnsupportedOsError
        return []

    def verify_env_vars(self) -> None:
        """
        Raises
            OptionalEnvNotFoundError
            RequiredEnvNotFoundError
        """
        envs = self.dependencies.env
        if envs:
            for env in envs:
                env_var = env.name.replace("$", "").upper()
                if env.required == True:
                    # If the environment variable exists, return
                    if os.environ.get(env_var):
                        logger.info(f"Environment variable: ${env_var} exists...")
                    else:
                        logger.error(f"Environment variable ${env_var} does not exist.")
                        raise RequiredEnvNotFoundError
                elif env.required == False:
                    if not os.environ.get(env_var):
                        logger.warning(
                            f"Optional environment variable ${env_var} does not exist. "
                            f"Consider defining it using 'export {env_var}=\"<value>\"'"
                        )
                        raise OptionalEnvNotFoundError
                    else:
                        logger.info(f"Optional environment variable ${env_var} exists!")
