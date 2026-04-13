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
        """
        Params:
            operating_system: canonical OS string (linux | darwin | termux).
                              Normalization is handled upstream in Component.
        """
        self.dependencies = dependencies
        self.operating_system = operating_system

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
        Returns:
            list[FontDependency]: fonts from the input list not found in any font_dir
        """
        found_fonts: set[FontDependency] = set()
        for font in fonts:
            for dir in font_dirs:
                if dir.exists() and any(dir.glob(f"{font.name}*")):
                    logger.debug(f"Font {font.name} found in {dir}")
                    found_fonts.add(font)
        return [font for font in fonts if font not in found_fonts]

    def verify_fonts(self, termux_prefix: Path | None = None) -> list[FontDependency]:
        """
        Params:
            termux_prefix: optional prefix path for termux environments
        Returns:
            list[FontDependency]: missing fonts for the target OS
        Raises:
            MissingTermuxPrefixError
            UnsupportedOsError
        """
        fonts = self.dependencies.fonts
        if not fonts:
            return []

        if self.operating_system == "linux":
            font_dirs = [
                Path.home() / ".local/share/fonts",
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
            ]
            return self._get_missing_fonts(fonts, font_dirs)

        elif self.operating_system == "termux":
            if not termux_prefix:
                raise MissingTermuxPrefixError
            font_dirs = [
                Path.home() / ".local/share/fonts",
                termux_prefix / "usr/share/fonts",
                termux_prefix / "usr/local/share/fonts",
            ]
            return self._get_missing_fonts(fonts, font_dirs)

        elif self.operating_system == "darwin":
            font_dirs = [
                Path.home() / "Library/Fonts",
                Path("/Library/Fonts"),
                Path("/System/Library/Fonts"),
            ]
            return self._get_missing_fonts(fonts, font_dirs)

        else:
            raise UnsupportedOsError

    def verify_env_vars(self) -> None:
        """
        Raises:
            RequiredEnvNotFoundError
            OptionalEnvNotFoundError
        """
        envs = self.dependencies.env
        if envs:
            for env in envs:
                env_var = env.name.replace("$", "").upper()
                if env.required:
                    if os.environ.get(env_var):
                        logger.info(f"Environment variable: ${env_var} exists...")
                    else:
                        logger.error(f"Environment variable ${env_var} does not exist.")
                        raise RequiredEnvNotFoundError
                else:
                    if not os.environ.get(env_var):
                        logger.warning(
                            f"Optional environment variable ${env_var} does not exist. "
                            f"Consider defining it using 'export {env_var}=\"<value>\"'"
                        )
                        raise OptionalEnvNotFoundError
                    else:
                        logger.info(f"Optional environment variable ${env_var} exists!")
