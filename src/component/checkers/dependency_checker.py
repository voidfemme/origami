import logging
from src.build_classes import DependencyList, FontDependency
from src.exceptions import MissingTermuxPrefixError
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

    def verify_programs(self):
        programs = self.dependencies.programs
        if programs:
            for program in programs:
                if not shutil.which(program.name):
                    return f"Program {program} does not exist."

    def verify_configs(self):
        configs = self.dependencies.configs
        if configs:
            for config in configs:
                if not os.path.exists(config.path):
                    return f"Config {config.name} does not exist at {config.path}"

    def verify_paths(self) -> str | None:
        # Do the source files exist in `$CORE`?
        paths = self.dependencies.paths
        if paths:
            for path in paths:
                if not os.path.exists(path):
                    return f"Path {path} does not exist."

    def _get_missing_fonts(
        self, fonts: list[FontDependency], font_dirs: list[Path]
    ) -> list[FontDependency]:
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
                return []
        return []

    def verify_env_vars(self):
        envs = self.dependencies.env
        if envs:
            for env in envs:
                env_var = env.name.replace("$", "").upper()
                if env.required == True:
                    # If the environment variable exists, return
                    if os.environ.get(env_var):
                        logger.info(f"Environment variable: ${env_var} exists...")
                    else:
                        logger.info(
                            f"Environment variable ${env_var} does not exist. Creating..."
                        )
                        if not env.value:
                            os.environ[env_var] = input(
                                f"Enter file path for {env_var}: "
                            )
                        else:
                            os.environ[env_var] = env.value
                elif env.required == False:
                    manually_define = input(
                        f"WARNING: envrionment variable ${env_var} is missing, but not required. Would you like to define it manually? (y/n): "
                    )
                    if manually_define:
                        os.environ[env_var] = input(
                            f"Enter a value for variable ${env_var}: "
                        )
