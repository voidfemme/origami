from pathlib import Path
from src.build_classes import BuildFile, FontDependency, InstallEntry
from src.component.checkers.dependency_checker import DependencyChecker
from src.component.installers.installer import Installer
from src.component.installers.font_installer import FontInstaller
import logging

logger = logging.getLogger(__name__)


def normalize_os(operating_system: str) -> str:
    """Normalize OS string to a canonical value: linux | darwin | termux.

    This is the single place OS normalization happens for the component layer.
    All classes below Component receive an already-normalized string and should
    not re-normalize.
    """
    os = operating_system.lower()
    if os == "macos":
        return "darwin"
    return os


class Component:
    def __init__(
        self,
        operating_system: str,
        theme: str,
        build_config: BuildFile,
        origami_config: Path | None,
        themes_dir: Path | str | None = None,
        scripts_dir: Path | str | None = None,
    ) -> None:
        self.operating_system = normalize_os(operating_system)

        if not origami_config:
            self.origami_config = Path.home() / ".config/origami"
        else:
            self.origami_config = origami_config

        self.theme = theme
        self.themes_dir = (
            Path(themes_dir) if themes_dir else self.origami_config / "themes"
        )
        self.scripts_dir = (
            Path(scripts_dir) if scripts_dir else self.origami_config / "scripts"
        )
        self.origami_theme_path = self.themes_dir / self.theme
        self.build_config = build_config
        self.build_config_path = self.build_config.path
        self.fonts_dir = self.themes_dir / self.theme / "fonts"
        self.installer = Installer(
            self.build_config,
            Path(self.origami_config),
            self.operating_system,
            self.theme,
        )
        if self.build_config.deps:
            self.dependency_checker = DependencyChecker(
                self.build_config.deps, self.operating_system
            )
            self.font_installer = FontInstaller(self.operating_system)
        self.installations: list[InstallEntry] = self.installer.get_install_objects()

    def apply_all_components(self) -> None:
        for component in self.installations:
            self.installer.apply_component(component)

    def get_required_paths(self) -> list[Path] | None:
        if self.build_config.deps:
            paths = self.build_config.deps.paths
        else:
            logger.log(logging.DEBUG, "Build file requires no paths to exist.")
            paths = []
        return paths

    def get_missing_fonts(self) -> list[FontDependency]:
        return self.dependency_checker.verify_fonts()

    def apply_fonts(self) -> None:
        if self.build_config.deps and self.build_config.deps.fonts:
            for font in self.get_missing_fonts():
                if font:
                    font_path = self.fonts_dir / font.name
                    self.font_installer.install_font(font_path)

    def check_upstream(self) -> None:
        if self.build_config.upstream:
            pass

    def check_health(self):
        pass
